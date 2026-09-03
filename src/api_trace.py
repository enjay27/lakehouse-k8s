"""
api_trace.py
============
Correlate one Polaris API call with the SQL it issues against PostgreSQL and
the objects it touches in MinIO.

Phase 1 of the API -> SQL -> MinIO profiling effort: answer "which API hits
which table, with which query, and which storage path", so that slow queries
and missing indexes can be found per API.

THREE STREAMS
-------------
    A. Polaris application log  (PRIMARY, for attribution)
       Polaris 1.3.0 logs every statement from
       `org.apache.polaris.persistence.relational.jdbc.DatasourceOperations`
       at DEBUG as `query: <sql> <params>`. Because it is emitted in-process,
       it sits between the request's own log lines -- which is why it beats
       the PostgreSQL log for working out WHICH API issued WHICH statement.

    B. PostgreSQL server log    (SECONDARY, for server-side timing)
       `log_statement=all` + `log_min_duration_statement=0`. Gives the real
       `duration: N ms` per statement and catches the pooler/driver chatter
       Polaris never logs (BEGIN/COMMIT/SET/DISCARD).

    C. MinIO trace              (for the storage side)
       `mc admin trace --json` -- one JSON object per request, with method,
       object key, status, duration and byte counts.

CORRELATION
-----------
Each API call is wrapped in a window: mark every stream, run the call, then
read back only what each stream appended. All three run on the same host
clock, so a window is sound; `Tracer` additionally records `requestId` /
`traceId` from the Polaris MDC when the log format exposes them, which gives
exact rather than windowed attribution.

If OpenTelemetry is enabled later (`quarkus.otel.sdk.disabled=false` plus
`quarkus.datasource.jdbc.telemetry=true`), the span tree supersedes this
windowing entirely and stream B can be switched off. This module is
deliberately structured so that swapping the source of `SqlStatement` records
is the only change that would require.

SECRET SAFETY  (this is a hard requirement, not a nicety)
---------------------------------------------------------
Statements against `principal_authentication_data` bind `main_secret_hash`,
`secondary_secret_hash` and `secret_salt`. Raw captures must never be
committed. `redact_params()` runs on EVERY parsed statement before it reaches
a record -- ALL parameters of any statement touching that table are replaced
with `<redacted>`, plus a value-shaped fallback for hash-like strings
anywhere else. There is no flag to turn this off, by design.

OFFLINE-TESTABLE
----------------
Every parser takes text and returns records, so the whole module is testable
against fixtures with no live cluster. See `test_api_trace.py`.

Usage:
    from api_trace import Tracer, FileStream

    tracer = Tracer(
        polaris_log=FileStream("/tmp/cap/polaris.log"),
        pg_log=FileStream("/tmp/cap/pg.log"),          # optional
        minio_trace=FileStream("/tmp/cap/minio.json"), # optional
        pg_conn=conn,                                  # optional, pg_stat_statements
    )

    with tracer.trace("iceberg.load_table", "GET", "/v1/cat/namespaces/ns/tables/t") as t:
        r = ic.load_table("cat", "ns", "t")
        t.status = r.status_code

    print(t.tables_touched, t.sql_count, t.minio_count, t.cache_shape)
"""

import json
import os
import pathlib
import re
import statistics
import time
from dataclasses import dataclass, field

# ----------------------------------------------------------------------
# constants
# ----------------------------------------------------------------------

#: Metastore tables in Polaris 1.3.0 (schema-v2).
POLARIS_TABLES_V2 = {
    "version",
    "entities",
    "grant_records",
    "principal_authentication_data",
    "policy_mapping_record",
}
#: `events` is NOT part of schema-v2, but Polaris 1.3.0 creates and writes it
#: when a persistence-backed event listener is configured
#: (`eventListener.type: persistence-in-memory-buffer`). So its presence here is
#: expected configuration, not schema drift.
POLARIS_TABLES_V3_ONLY = set()
EVENT_LISTENER_TABLES = {"events"}

#: Tables written by BACKGROUND work rather than by the request being traced.
#:
#: The persistence event listener buffers audit events in memory and flushes
#: them on a timer (`bufferTime: PT5S`, `maxBufferSize: 1000`). The resulting
#: INSERTs therefore land in whatever trace window happens to be open when the
#: flush fires — NOT in the window of the API call that generated them.
#: Counting them as part of an API's cost would inflate a random subset of
#: measurements and make the sweep non-reproducible, so they are reported
#: separately instead.
ASYNC_WRITE_TABLES = {"events"}

#: Any statement touching these tables has ALL of its parameters redacted.
SECRET_TABLES = {"principal_authentication_data"}

#: Fallback value-shaped redaction for hash/salt-like strings appearing
#: anywhere else (defence in depth -- the table check above is the real guard).
_HASHLIKE = re.compile(r"\b[A-Fa-f0-9]{32,}\b|\b[A-Za-z0-9+/]{40,}={0,2}\b")

REDACTED = "<redacted>"

# ----------------------------------------------------------------------
# line patterns
# ----------------------------------------------------------------------

#: Polaris DEBUG SQL line. Quarkus abbreviates the logger category by default
#: (`org.apa.pol.per.rel.jdb.DatasourceOperations`), so match on the class name
#: rather than the full package. The `query: ` marker comes from
#: DatasourceOperations.logQuery().
#: DOTALL matters: in the JSON format the whole message — SQL *and* the
#: newline-separated parameters — lives in one string, so `.` must span
#: newlines or nothing matches at all. The trailing `\s*$` also absorbs the
#: bare `"\n    "` that an empty parameter list leaves behind.
_POLARIS_QUERY = re.compile(r"query:\s*(?P<sql>.+?)\s*$", re.DOTALL)
_POLARIS_LOGGER_HINT = "DatasourceOperations"

#: MDC values. Polaris 1.3.0's shipped console/file format emits them
#: POSITIONALLY, not as key=value:
#:
#:   %d{...} %-5p [%c{3.}] [%X{requestId},%X{realmId}] \
#:       [%X{traceId},%X{parentId},%X{spanId},%X{sampled}] (%t) %s%e%n
#:
#: producing e.g.
#:   2026-08-18 10:00:00,100 DEBUG [org.apa.pol.per.rel.jdb.DatasourceOperations] \
#:       [req-abc,POLARIS] [4bf92f,00f067,a1b2c3,true] (executor-thread-1) query: ...
#:
#: so the two bracket groups AFTER the logger bracket carry the MDC. A
#: key=value matcher finds nothing against the real format — hence both forms
#: are supported, positional first.
_MDC_POSITIONAL = re.compile(
    r"\]\s*\[(?P<request_id>[^,\[\]]*),(?P<realm_id>[^\[\]]*)\]"
    r"\s*\[(?P<trace_id>[^,\[\]]*),(?P<parent_id>[^,\[\]]*),"
    r"(?P<span_id>[^,\[\]]*),(?P<sampled>[^\[\]]*)\]"
)
#: Fallback for a customised key=value format.
_MDC_REQUEST_ID = re.compile(r"requestId=(?P<v>[0-9a-zA-Z\-_]+)")
_MDC_TRACE_ID = re.compile(r"traceId=(?P<v>[0-9a-f]+)")


def parse_mdc(line):
    """Extract (request_id, trace_id) from a Polaris log line.

    Tries the shipped positional format first, then a key=value fallback.
    Returns (None, None) when neither matches — MDC is a bonus for exact
    attribution, never a requirement, since the trace window already works
    without it.
    """
    m = _MDC_POSITIONAL.search(line)
    if m:
        req = (m.group("request_id") or "").strip() or None
        trace = (m.group("trace_id") or "").strip() or None
        return req, trace
    rid = _MDC_REQUEST_ID.search(line)
    tid = _MDC_TRACE_ID.search(line)
    return (rid.group("v") if rid else None, tid.group("v") if tid else None)


#: PostgreSQL log lines. `execute <unnamed>:` is the extended-query-protocol
#: form the JDBC driver produces; `statement:` is the simple-protocol form.
#: Both appear in practice -- the driver switches after `prepareThreshold`
#: executions -- so both are matched.
_PG_STATEMENT = re.compile(
    r"(?P<pid>\[\d+\])?.*?\bLOG:\s+(?:execute\s+\S+:|statement:)\s*(?P<sql>.+?)\s*$"
)
#: CASE-INSENSITIVE, and that is not cosmetic. PostgreSQL emits
#: `DETAIL:  Parameters:` with a capital P on this cluster; the pattern
#: matched only lower-case, so **no PG-side bound parameter was ever
#: captured** (found 2026-09-02 while routing async event rows, which
#: cannot be attributed without the request_id their parameters carry).
_PG_DETAIL_PARAMS = re.compile(r"\bDETAIL:\s+parameters:\s*(?P<params>.+?)\s*$", re.I)
_PG_DURATION = re.compile(r"\bLOG:\s+duration:\s+(?P<ms>[\d.]+)\s+ms")
_PG_PID = re.compile(r"\[(?P<pid>\d+)\]")

#: Table extraction from the SQL shapes QueryGenerator emits. Schema-qualified
#: (`POLARIS_SCHEMA.entities`) or bare -- both are handled.
_SQL_TABLE = re.compile(
    r"\b(?:FROM|INTO|UPDATE|JOIN)\s+(?:(?P<schema>[A-Za-z_][\w]*)\.)?(?P<table>[A-Za-z_][\w]*)",
    re.IGNORECASE,
)
_SQL_VERB = re.compile(
    r"^\s*(?P<verb>SELECT|INSERT|UPDATE|DELETE|BEGIN|COMMIT|ROLLBACK|SET|SHOW)",
    re.IGNORECASE,
)

#: Version-only projection -- the cache-validation query. A SELECT whose
#: projection is limited to the two change-tracking columns means the resolver
#: found everything in the entity cache and is only validating it.
_VERSION_ONLY_SELECT = re.compile(
    r"^\s*SELECT\s+(?P<cols>.+?)\s+FROM\b", re.IGNORECASE | re.DOTALL
)
_VERSION_COLUMNS = {"entity_version", "grant_records_version"}


# ----------------------------------------------------------------------
# records
# ----------------------------------------------------------------------
@dataclass
class SqlStatement:
    """One SQL statement observed during a traced API call.

    Attributes:
        seq: 0-based position within the traced call, in observed order.
        sql: statement text. Parameter markers stay as `?` / `$N`.
        params: bound parameter values, ALREADY REDACTED. May be None when the
            source did not report them.
        table: primary table touched, lower-cased, or None if not identifiable.
        verb: SELECT / INSERT / UPDATE / DELETE / BEGIN / COMMIT / ...
        duration_ms: server-side duration, only available from the PG log.
        source: "polaris" or "postgres" -- which stream this came from.
        request_id / trace_id: Polaris MDC values when the log format has them.
    """

    seq: int
    sql: str
    params: str = None
    table: str = None
    verb: str = None
    duration_ms: float = None
    source: str = "polaris"
    request_id: str = None
    trace_id: str = None

    @property
    def is_version_check(self):
        """True when this is the entity-cache validation query.

        The resolver probes the cache optimistically and then validates
        everything it resolved with ONE batched
        `SELECT entity_version, grant_records_version ... WHERE (catalog_id, id) IN (...)`.
        Seeing only this and no full-column entity SELECT is the signature of a
        cache hit.
        """
        if not self.sql or (self.verb or "").upper() != "SELECT":
            return False
        m = _VERSION_ONLY_SELECT.match(self.sql)
        if not m:
            return False
        cols = {
            c.strip().split(".")[-1].lower()
            for c in m.group("cols").split(",")
            if c.strip()
        }
        return bool(cols) and cols.issubset(_VERSION_COLUMNS)


@dataclass
class MinioOp:
    """One MinIO/S3 request observed during a traced API call.

    Attributes:
        seq: 0-based position within the traced call.
        method: HTTP method (GET / PUT / HEAD / DELETE / POST).
        path: full request path as reported by the trace.
        bucket / key: path split at the first "/" for convenience.
        status: HTTP status code.
        duration_ms: server-reported duration.
        rx / tx: bytes in / out, when reported.
    """

    seq: int
    method: str
    path: str
    bucket: str = None
    key: str = None
    status: int = None
    duration_ms: float = None
    rx: int = None
    tx: int = None


@dataclass
class TraceRecord:
    """Everything observed for one API call.

    `status` is left for the caller to set inside the `with` block, since only
    the caller knows the HTTP response.
    """

    api: str
    method: str = None
    path: str = None
    status: int = None
    t0: float = None
    t1: float = None
    error: str = None
    sql: list = field(default_factory=list)
    minio: list = field(default_factory=list)
    pg_stat: list = field(default_factory=list)
    #: The RAW Polaris window, kept ONLY when parsing produced no statements.
    #: An empty statement list is ambiguous between three faults with three
    #: different fixes (see `diagnose_empty_window`), and the raw text settles
    #: it in a glance. Kept only on the empty path because a full drive's
    #: windows run to megabytes -- this is a diagnostic, not a second copy of
    #: the capture. Bounded in `_TraceContext.__exit__`.
    raw_log: str = None

    # -- derived -------------------------------------------------------
    @property
    def wall_ms(self):
        """End-to-end client-observed latency, in milliseconds."""
        if self.t0 is None or self.t1 is None:
            return None
        return (self.t1 - self.t0) * 1000.0

    @property
    def sql_count(self):
        return len(self.sql)

    @property
    def sql_total_ms(self):
        """Summed server-side SQL duration. None when no statement carried a
        duration (i.e. the PG log stream was not enabled)."""
        vals = [s.duration_ms for s in self.sql if s.duration_ms is not None]
        return sum(vals) if vals else None

    @property
    def tables_touched(self):
        """Sorted distinct table names -- the core Phase 1 answer.

        Excludes ASYNC_WRITE_TABLES: those are written by a background flush
        that merely happened to fire inside this window, so attributing them to
        this API would be wrong. See `async_tables`.
        """
        return sorted(
            {s.table for s in self.sql if s.table and s.table not in ASYNC_WRITE_TABLES}
        )

    @property
    def async_tables(self):
        """Background-written tables observed in this window (see ASYNC_WRITE_TABLES).

        Reported, not hidden: seeing `events` here is useful (it confirms the
        audit listener is active and shows its flush cadence), it just must not
        be counted as this API's own database work.
        """
        return sorted(
            {s.table for s in self.sql if s.table and s.table in ASYNC_WRITE_TABLES}
        )

    @property
    def sync_sql(self):
        """Statements attributable to this request, excluding background writes."""
        return [s for s in self.sql if s.table not in ASYNC_WRITE_TABLES]

    @property
    def minio_count(self):
        return len(self.minio)

    @property
    def minio_total_ms(self):
        vals = [m.duration_ms for m in self.minio if m.duration_ms is not None]
        return sum(vals) if vals else None

    @property
    def minio_paths(self):
        """Sorted distinct object paths touched -- "which directory in MinIO"."""
        return sorted({m.path for m in self.minio if m.path})

    @property
    def unaccounted_ms(self):
        """wall - SQL - MinIO: Polaris CPU, auth, serialization, transport.

        A large unaccounted share on a read API usually means serialization of
        a big response body rather than anything the database is doing.
        """
        if self.wall_ms is None:
            return None
        return self.wall_ms - (self.sql_total_ms or 0) - (self.minio_total_ms or 0)

    @property
    def entity_access(self):
        """Per-shape breakdown of this request's `entities` reads.

        See `entity_access_profile` for the shapes and for why this is a share
        rather than a verdict.
        """
        return entity_access_profile(self.sql)

    @property
    def cache_shape(self):
        """WARM / MIXED / COLD / N/A for this request.

        **Use this, not `cache_verdict`.** See `entity_access_shape` for why
        the older property cannot answer the question on Polaris 1.3.0.
        """
        return self.entity_access["verdict"]

    @property
    def batched_share(self):
        """Fraction of this request's entity reads served by batched validation.

        None when the request read no entities. This is the number that should
        move as a cache warms: a path-resolving API always loads its first
        entity BY NAME, because a name is all the caller supplied, so a warm
        request is not one with zero per-entity loads -- it is one where the
        proportion revalidated in a batch has risen.
        """
        return self.entity_access["batched_share"]

    @property
    def cache_verdict(self):
        """MISS / HIT / N/A, inferred from SQL shape. **Superseded.**

        Prefer `cache_shape`. Kept because removing it would silently change
        anything still reading it, but be aware of what it can actually return:

        MISS -- a full-column SELECT against `entities` was issued.
        HIT  -- only the batched version-check query appeared.
        N/A  -- no entity reads at all (e.g. `GET /v1/config`).

        **HIT is unreachable on Polaris 1.3.0.** It requires every entity read
        to satisfy `is_version_check`, which matches a projection of just
        `entity_version, grant_records_version`. Measured against a real 75.7 MB
        capture, this build never emits that: every `entities` SELECT --
        including the row-constructor cache-validation query, the highest-volume
        statement in the system -- projects the full column list. So this
        returns MISS or N/A and nothing else, which is why the Phase 1 matrix
        reported `cache: MISS` for all 43 APIs. That was not evidence about the
        cache; it was the classifier's only reachable answer.

        Note this is inference from observed statements, not introspection:
        Polaris exposes no cache metrics (neither cache calls Caffeine's
        `recordStats()`), so behaviour is the only available signal.
        """
        entity_reads = [
            s
            for s in self.sql
            if s.table == "entities" and (s.verb or "").upper() == "SELECT"
        ]
        if not entity_reads:
            return "N/A"
        if all(s.is_version_check for s in entity_reads):
            return "HIT"
        return "MISS"

    def to_row(self):
        """Flatten to a dict for a pandas DataFrame / report table."""
        return {
            "api": self.api,
            "http_method": self.method,
            "path": self.path,
            "status": self.status,
            "wall_ms": round(self.wall_ms, 2) if self.wall_ms is not None else None,
            "sql_count": self.sql_count,
            "sql_total_ms": (
                round(self.sql_total_ms, 2) if self.sql_total_ms is not None else None
            ),
            "tables_touched": ",".join(self.tables_touched),
            "async_tables": ",".join(self.async_tables),
            "minio_count": self.minio_count,
            "minio_total_ms": (
                round(self.minio_total_ms, 2)
                if self.minio_total_ms is not None
                else None
            ),
            "unaccounted_ms": (
                round(self.unaccounted_ms, 2)
                if self.unaccounted_ms is not None
                else None
            ),
            # `cache_shape` and `batched_share` REPLACE the old `cache_verdict`
            # column here. That column could only ever read MISS or N/A on this
            # build, so every report carrying it was stating the classifier's
            # limitation as a finding. The property is still on the record for
            # anything that asks for it by name.
            "cache_shape": self.cache_shape,
            "batched_share": (
                round(self.batched_share, 2) if self.batched_share is not None else None
            ),
            "error": self.error,
        }


# ----------------------------------------------------------------------
# redaction
# ----------------------------------------------------------------------
#: Columns whose bound value names the API call a row DESCRIBES rather than
#: the call that happened to be in flight when the row was written.
_REQUEST_ID_COLUMN = "request_id"
_PARAM_SLOT = r"\$%d\s*=\s*(?:'(?P<q>(?:[^']|'')*)'|(?P<b>[^,]+))"


def request_id_from_params(sql, raw_params):
    """The request_id an ASYNC row carries in its own bound parameters.

    WHY THIS EXISTS (measured 2026-09-02). Polaris's event listener writes
    `POLARIS_SCHEMA.EVENTS` asynchronously, and the row describes an API call
    that has already finished. One `AfterCreateTableEvent` for request `_046`
    fired at 08:26:26.027 and its INSERT executed at **08:26:31.056 -- a 5.03
    second lag** -- by which time the drive was on request `_062`. The trace
    window credited it to `mgmt.create_principal`, a **403 that wrote nothing**,
    and the report said so.

    A trace window cannot fix that: attribution by "which window was open" is
    exactly the assumption an async write breaks. Nor can post-hoc correlation
    on `mdc.requestId` -- this statement never reaches the Polaris log at all
    and is visible only in the PostgreSQL one, so it carries no MDC.

    The row carries the answer itself. `INSERT INTO ... (a, b, request_id, ...)
    VALUES ($1, $2, $3, ...)` maps `request_id` to a positional slot, and the
    `DETAIL: Parameters:` line binds it.

    Args:
        sql: the INSERT text, with its column list.
        raw_params: the raw `$1 = 'x', $2 = 'y'` string, BEFORE redaction --
            redaction can replace the value, and this needs the real one.

    Returns:
        The request id, or None when the statement has no such column or the
        parameter was not logged.
    """
    if not sql or not raw_params:
        return None
    cols = re.search(r"\(([^()]*)\)\s*VALUES", sql, re.I | re.S)
    if not cols:
        return None
    names = [c.strip().lower() for c in cols.group(1).split(",")]
    if _REQUEST_ID_COLUMN not in names:
        return None
    slot = names.index(_REQUEST_ID_COLUMN) + 1  # $N is 1-based
    m = re.search(_PARAM_SLOT % slot, raw_params)
    if not m:
        return None
    val = m.group("q") if m.group("q") is not None else (m.group("b") or "")
    val = val.replace("''", "'").strip()
    return val or None


def redact_params(sql, params):
    """Redact bound parameters that may carry secret material.

    Two layers, deliberately conservative:
      1. If the statement touches a table in SECRET_TABLES, EVERY parameter is
         replaced. Positional parameters cannot be reliably mapped back to
         columns, so redacting the whole set is the only safe choice.
      2. Otherwise, hash-like values (long hex or base64 runs) are replaced
         individually as defence in depth.

    Args:
        sql: the statement text.
        params: raw parameter string, or None.

    Returns:
        The redacted parameter string, or None if `params` was None.
    """
    if params is None:
        return None
    table = extract_table(sql)
    if table in SECRET_TABLES:
        return REDACTED
    return _HASHLIKE.sub(REDACTED, params)


def scrub_text(text):
    """Redact an arbitrary block of captured log text.

    Use before writing any raw capture to disk or into a document. Redacts
    whole `parameters:` payloads on lines mentioning a secret table, and
    hash-like values everywhere else.
    """
    out = []
    for line in text.splitlines():
        if any(t in line for t in SECRET_TABLES) and "parameters:" in line:
            line = re.sub(r"(parameters:).*$", r"\1 " + REDACTED, line)
        out.append(_HASHLIKE.sub(REDACTED, line))
    return "\n".join(out)


# ----------------------------------------------------------------------
# SQL helpers
# ----------------------------------------------------------------------
def extract_table(sql):
    """Best-effort primary table name from a statement, lower-cased.

    QueryGenerator emits only single-table statements (there are no JOINs
    anywhere in the Polaris relational-jdbc layer), so the first match is the
    answer. Returns None when nothing recognisable is present, e.g. for
    BEGIN / COMMIT.
    """
    if not sql:
        return None
    m = _SQL_TABLE.search(sql)
    if not m:
        return None
    return m.group("table").lower()


def extract_verb(sql):
    """Leading SQL verb, upper-cased, or None."""
    if not sql:
        return None
    m = _SQL_VERB.match(sql)
    return m.group("verb").upper() if m else None


# ----------------------------------------------------------------------
# entity-access shape (cache discrimination)
# ----------------------------------------------------------------------
#: WHERE-shape classes for a SELECT against `entities`.
ENTITY_BATCH_VALIDATE = "BATCH_VALIDATE"
ENTITY_BY_ID = "BY_ID"
ENTITY_BY_NAME = "BY_NAME"
ENTITY_LIST_CHILDREN = "LIST_CHILDREN"

_ENTITY_FROM = re.compile(r"\bFROM\s+[\w.]*\bentities\b", re.IGNORECASE)
#: The row-constructor cache-validation predicate. Matches the raw form
#: `(catalog_id, id) IN ((?,?),(?,?))` and the `normalize_sql` form
#: `(catalog_id, id) IN (<rows>)` alike.
_ENTITY_IN_ROWS = re.compile(r"\(\s*catalog_id\s*,\s*id\s*\)\s+IN\s*\(", re.IGNORECASE)
_WHERE_SPLIT = re.compile(r"\bWHERE\b", re.IGNORECASE)


def where_clause(sql):
    """Return everything after the first WHERE, or "" when there is none.

    **Why anything classifying a statement should use this.** Twice now a
    classifier here has read the whole statement and treated a column named in
    the SELECT list as though it were constrained:

      * `cache_verdict` matched on the projection, so it could never see a
        batched cache validation (see `entity_access_shape`);
      * `schema_audit.check_hypotheses` matched predicate columns anywhere in
        the text, so the SECURABLE lookup -- which merely *projects*
        `grantee_catalog_id, grantee_id` -- was admitted as evidence about the
        GRANTEE hypothesis, along with an INSERT that names every column.

    A projection says what you get back. Only the WHERE says what the planner
    has to find, which is the thing an index question is about.

    An INSERT has no WHERE and correctly yields "", excluding it from any
    predicate match.
    """
    if not sql:
        return ""
    parts = _WHERE_SPLIT.split(" ".join(str(sql).split()), 1)
    return parts[1] if len(parts) > 1 else ""


def entity_access_shape(sql):
    """Classify an `entities` SELECT by the shape of its WHERE clause.

    Returns one of ENTITY_BATCH_VALIDATE / ENTITY_BY_ID / ENTITY_BY_NAME /
    ENTITY_LIST_CHILDREN, or None when `sql` is not a SELECT against `entities`.

    **Why the WHERE clause and not the projection.** `SqlStatement.is_version_check`
    looks for a version-only projection (`entity_version, grant_records_version`),
    on the documented assumption that the entity cache validates with a narrow
    SELECT. Polaris 1.3.0 does not do that: measured against a real 75.7 MB
    capture, every `entities` SELECT it emits -- INCLUDING the row-constructor
    cache-validation query, the highest-volume statement in the system at 1,662
    calls -- projects the same full column list. So `is_version_check` is always
    False, and `TraceRecord.cache_verdict`, which needs it to be True, can only
    ever return MISS or N/A. That is why the Phase 1 matrix reported
    `cache: MISS` for all 43 APIs: not a sampling artifact, an unreachable branch.

    The WHERE clause does carry the signal. The resolver's deferred bulk
    validation asks for many entities at once by `(catalog_id, id)`; a genuine
    miss loads them one at a time, by id or by name.
    """
    if not sql:
        return None
    s = " ".join(str(sql).split())
    if not s[:6].upper().startswith("SELECT") or not _ENTITY_FROM.search(s):
        return None
    where = where_clause(s)
    if _ENTITY_IN_ROWS.search(where):
        return ENTITY_BATCH_VALIDATE
    if re.search(r"\bname\s*=", where, re.IGNORECASE):
        return ENTITY_BY_NAME
    if re.search(r"(?<!parent_)\bid\s*=", where, re.IGNORECASE):
        return ENTITY_BY_ID
    if re.search(r"\bparent_id\s*=", where, re.IGNORECASE):
        return ENTITY_LIST_CHILDREN
    return ENTITY_LIST_CHILDREN


def entity_access_profile(statements):
    """Break one request's `entities` reads down by access shape.

    Args:
        statements: iterable of SqlStatement (e.g. `TraceRecord.sql`).

    Returns:
        dict with per-shape counts, plus:
          per_entity     -- BY_ID + BY_NAME, i.e. loads the cache could not serve
          entity_reads   -- per_entity + batch_validate (list queries excluded;
                            the entity cache does not serve them)
          batched_share  -- batch_validate / entity_reads, or None when there
                            were no entity reads at all
          verdict        -- WARM / MIXED / COLD / N/A (see below)

    **Why a share and not a boolean.** The first shape-based classifier here
    scored a request MISS if it contained ANY per-entity load, and measured
    100% MISS across all 703 requests in the reference capture -- which looked
    like a confirmation of the old projection-based result but was the same
    mistake twice: an unreachable HIT branch. Any API that resolves a path
    (catalog -> namespace -> table) must look the first entity up BY NAME,
    because a name is all the caller supplied. So a warm request is not one
    with zero per-entity loads; it is one where the *proportion* served by
    batched validation has risen.

    Measured on that capture: 628 of 703 requests (89.3%) contain at least one
    batched validation, median batched share 0.33, modal shape 2 batched to 4
    per-entity. The cache is plainly working -- the binary verdict just could
    not see it.

    verdict:
        WARM  -- batched validation only, no per-entity load
        MIXED -- both (the normal steady state for path-resolving APIs)
        COLD  -- per-entity loads only, nothing revalidated
        N/A   -- no entity reads (e.g. `GET /v1/config`, or list-only requests)
    """
    counts = {
        ENTITY_BATCH_VALIDATE: 0,
        ENTITY_BY_ID: 0,
        ENTITY_BY_NAME: 0,
        ENTITY_LIST_CHILDREN: 0,
    }
    for st in statements or []:
        shape = entity_access_shape(getattr(st, "sql", st))
        if shape:
            counts[shape] += 1

    batch = counts[ENTITY_BATCH_VALIDATE]
    per_entity = counts[ENTITY_BY_ID] + counts[ENTITY_BY_NAME]
    reads = batch + per_entity

    if not reads:
        verdict = "N/A"
    elif not per_entity:
        verdict = "WARM"
    elif not batch:
        verdict = "COLD"
    else:
        verdict = "MIXED"

    return {
        "batch_validate": batch,
        "by_id": counts[ENTITY_BY_ID],
        "by_name": counts[ENTITY_BY_NAME],
        "list_children": counts[ENTITY_LIST_CHILDREN],
        "per_entity": per_entity,
        "entity_reads": reads,
        "batched_share": (batch / reads) if reads else None,
        "verdict": verdict,
    }


def cache_shape_verdict(statements):
    """WARM / MIXED / COLD / N/A for one request. See `entity_access_profile`.

    Replaces `TraceRecord.cache_verdict` for Polaris 1.3.0, which cannot return
    HIT at all -- see `entity_access_shape`. Kept separate rather than fixed in
    place so nothing already reading `cache_verdict` changes underneath it.
    """
    return entity_access_profile(statements)["verdict"]


def normalize_sql(sql):
    """Canonicalize a statement so the same query groups across sources/calls.

    Three normalizations, in order:

      1. **Placeholder style.** Polaris logs JDBC's `?` markers; PostgreSQL
         logs the driver's rewritten `$1`, `$2`. Without unifying these, the
         SAME statement looks different in stream A and stream B and the
         server-side durations never attach to the statements Polaris
         reported. Found by test, not by inspection — the failure is silent
         (durations simply come back None), which is exactly the kind of thing
         that would have quietly hollowed out the perf numbers.
      2. **Whitespace.**
      3. **IN-list cardinality.** The cache-validation query is a
         row-constructor `IN ((?,?),(?,?),...)` whose length varies with how
         many entities the resolver touched; collapsing it is what lets the
         report say "this one statement ran N times".
    """
    if not sql:
        return sql
    s = re.sub(r"\$\d+", "?", sql)
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(
        r"IN\s*\((?:\s*\([^)]*\)\s*,?)+\)", "IN (<rows>)", s, flags=re.IGNORECASE
    )
    s = re.sub(
        r"IN\s*\(\s*\?(?:\s*,\s*\?)+\s*\)", "IN (<list>)", s, flags=re.IGNORECASE
    )
    return s


# ----------------------------------------------------------------------
# parsers
# ----------------------------------------------------------------------
def diagnose_empty_window(text, marker="DatasourceOperations"):
    """Why did a trace window yield no statements? Three answers, three fixes.

    An operation whose statement list is empty is the single most expensive
    thing in this repo's history -- three drives and most of a session went
    into one, and every hour of it was spent deciding WHICH of these it was.
    The raw window answers it immediately, so the report carries the answer
    rather than the reader re-deriving it.

    Returns:
        (verdict, hint) -- a short label and the fix that goes with it.
    """
    if not text or not text.strip():
        return (
            "the capture recorded NOTHING in this window",
            "The stream is not recording, or the drive is reading a different "
            "directory than the one being written. Pass --capture explicitly "
            "(find_capture_dir needs a NON-EMPTY polaris.log and will otherwise "
            "pick a stale directory), then check the tails are alive: "
            "kill -0 $(awk '{print $1}' <capture>/.pids)",
        )
    if marker not in text:
        return (
            f"the window has output but no {marker} lines",
            "Either this operation genuinely issued no SQL -- a request refused "
            "at the HTTP layer before the metastore does -- or the SQL logger is "
            "above DEBUG. The access-log line below tells you which: a request "
            "that reached Polaris and returned a status issued no SQL; no "
            "request line at all means the window missed it. "
            "Logger check: ./capture.sh preflight",
        )
    return (
        f"{marker} lines ARE present and none parsed",
        "This is a PARSER fault, not a capture fault -- the rarest of the three "
        "and the only one where the raw text below is the bug report. Check "
        "parse_polaris_log's require_logger against the logger name in the "
        "lines below.",
    )


def parse_polaris_log(text, require_logger=True, start_seq=0):
    """Parse Polaris DEBUG output into SqlStatement records.

    Args:
        text: the captured chunk of Polaris log.
        require_logger: when True (default) only lines that also mention
            `DatasourceOperations` are accepted. Set False if the log format
            omits the logger name -- at the cost of matching any line that
            happens to contain "query:".
        start_seq: starting sequence number.

    Returns:
        list[SqlStatement], in log order, with parameters already redacted.
    """
    out = []
    seq = start_seq
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        parsed = _parse_json_log_line(line) if line.startswith("{") else None
        if parsed is not None:
            logger_name, message, rid, tid = parsed
            if require_logger and _POLARIS_LOGGER_HINT not in logger_name:
                continue
            body = message
        else:
            if require_logger and _POLARIS_LOGGER_HINT not in line:
                continue
            body = line
            rid, tid = parse_mdc(line)

        m = _POLARIS_QUERY.search(body)
        if not m:
            continue
        sql, params = split_query_message(m.group("sql"))
        out.append(
            SqlStatement(
                seq=seq,
                sql=sql,
                params=redact_params(sql, params),
                table=extract_table(sql),
                verb=extract_verb(sql),
                source="polaris",
                request_id=rid,
                trace_id=tid,
            )
        )
        seq += 1
    return out


def _parse_json_log_line(line):
    """Parse one Quarkus JSON-format log line.

    Enabled by `quarkus.log.console.json.enabled=true`, which is the format
    worth using here: `DatasourceOperations` renders parameters as *newline-
    separated* text, so in the plain-text formatter a single statement spans
    several physical lines and cannot be parsed line-by-line at all. JSON keeps
    the whole message in one string, and carries `mdc.requestId` as a first-
    class field for exact per-request attribution.

    Returns:
        (loggerName, message, requestId, traceId), or None if the line is not
        parseable JSON — `mc`-style banner text and partial writes are skipped
        rather than raising.
    """
    try:
        obj = json.loads(line)
    except (ValueError, TypeError):
        return None
    if not isinstance(obj, dict) or "message" not in obj:
        return None
    mdc = obj.get("mdc") or {}
    return (
        obj.get("loggerName") or "",
        obj.get("message") or "",
        mdc.get("requestId") or None,
        mdc.get("traceId") or None,
    )


def split_query_message(body):
    """Split a `query: ...` message body into (sql, params).

    `DatasourceOperations.logQuery` builds the message as:

        LOGGER.atDebug()
            .addArgument(query.sql())
            .addArgument(() -> query.parameters().stream()
                .map(...)
                .collect(Collectors.joining("\\n    ", "\\n    ", "")))
            .setMessage("query: {}{}")

    so parameters are appended **newline-separated and four-space indented**,
    not bracketed:

        query: SELECT ... WHERE realm_id = ?
            POLARIS
            0
            42

    An empty parameter list still emits the prefix, leaving a bare trailing
    `"\\n    "`, which is treated as no parameters rather than as one empty one.

    Returns:
        (sql, params) where params is a comma-joined string, or None.
    """
    if "\n" not in body:
        # Also accept a bracketed form, in case a future release changes the
        # joiner — cheap to support, and avoids a silent regression.
        pm = re.search(r"\s(\[.*\])\s*$", body)
        if pm:
            return body[: pm.start()].strip(), pm.group(1)
        return body.strip(), None

    # The SQL itself can be MULTI-LINE, and Polaris indents its continuation
    # lines by four spaces -- exactly like the parameter lines. Taking only the
    # first line as SQL (what this did) truncated the grant_records OR-delete to
    #     DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (
    # and fed that to EXPLAIN, which failed with "syntax error at end of input".
    # Indentation cannot separate the two blocks, but the PLACEHOLDER COUNT can:
    # the trailing k lines are the parameters exactly when the remaining SQL
    # contains k `?` placeholders. Self-checking, so a shape we have not seen
    # falls through rather than being mis-split.
    lines = body.split("\n")
    for k in range(len(lines)):
        sql = "\n".join(lines[: len(lines) - k]).strip()
        if not sql:
            continue
        if sql.count("?") == k:
            values = [v.strip() for v in lines[len(lines) - k :] if v.strip()]
            return sql, (", ".join(values) if values else None)

    # No split satisfies the placeholder count (a parameter value containing a
    # newline, say). Fall back to the original first-line rule, which is wrong
    # for multi-line SQL but no worse than before.
    first, _, rest = body.partition("\n")
    values = [v.strip() for v in rest.split("\n") if v.strip()]
    return first.strip(), (", ".join(values) if values else None)


def parse_pg_log(text, start_seq=0, carry=None):
    """Parse a PostgreSQL server-log chunk into SqlStatement records.

    Handles the three-line shape the JDBC driver produces:

        LOG:  execute <unnamed>: SELECT ... WHERE realm_id = $1
        DETAIL:  parameters: $1 = 'POLARIS'
        LOG:  duration: 1.234 ms

    A `DETAIL: parameters:` line is attached to the most recent statement from
    the SAME backend pid, and a bare `duration:` line likewise -- without the
    pid check, interleaved backends would cross-assign durations, which under
    PgBouncer is not a hypothetical.

    Returns:
        list[SqlStatement] with `source="postgres"` and `duration_ms` populated
        where a duration line followed.
    """
    out = []
    seq = start_seq
    #: STATE ACROSS CALLS, when the caller supplies it. A statement and its
    #: `DETAIL:  Parameters:` line are adjacent in the file but not necessarily
    #: in the same READ: `read_since_mark()` returns whatever has arrived
    #: through kubectl's pipe at that instant, so an `execute` line can end one
    #: trace window with its DETAIL arriving in the next. The statement then
    #: has no params -- and for `POLARIS_SCHEMA.EVENTS`, no `request_id`, so
    #: the async row cannot be routed to the request it names. Measured
    #: 2026-09-03: the admin drive's events row kept the wrong API for exactly
    #: this reason, while parsing the same log in ONE call extracts it fine.
    last_by_pid = carry if carry is not None else {}
    last_pid = "-"
    for line in text.splitlines():
        pidm = _PG_PID.search(line)
        if pidm:
            pid = last_pid = pidm.group("pid")
        else:
            # A continuation line carries no log prefix and therefore no pid.
            # Falling back to "-" would look up the wrong backend and silently
            # drop the rest of a wrapped statement.
            pid = last_pid

        dm = _PG_DURATION.search(line)
        if dm:
            stmt = last_by_pid.get(pid)
            if stmt is not None and stmt.duration_ms is None:
                stmt.duration_ms = float(dm.group("ms"))
            continue

        pm = _PG_DETAIL_PARAMS.search(line)
        if pm:
            stmt = last_by_pid.get(pid)
            if stmt is not None:
                raw = pm.group("params")
                #: BEFORE redaction: redact_params can replace the value, and
                #: the request id has to be read from the real one.
                stmt.request_id = request_id_from_params(stmt.sql, raw)
                stmt.params = redact_params(stmt.sql, raw)
            continue

        # A statement that wraps across lines is logged with the continuation
        # lines INDENTED and carrying no log prefix. Without this, a multi-line
        # statement is truncated at the first newline -- which is why the
        # grant_records OR-delete arrived as the unparseable fragment
        # "DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (" and then failed
        # EXPLAIN with "syntax error at end of input".
        if (
            line[:1] in ("\t", " ")
            and line.strip()
            and not _PG_PID.search(line)
            and last_by_pid.get(pid) is not None
        ):
            cont = last_by_pid[pid]
            cont.sql = cont.sql + " " + line.strip()
            cont.table = extract_table(cont.sql) or cont.table
            cont.verb = extract_verb(cont.sql) or cont.verb
            continue

        sm = _PG_STATEMENT.search(line)
        if sm:
            sql = sm.group("sql")
            #: `LOG:  statement: ` with NOTHING after it is Pgpool's health
            #: check, which probes a backend with an empty query string. It
            #: arrives on an exact 30-second cadence from the same two pids
            #: (measured 2026-09-02: 07:54:24, 07:54:54, 07:55:24) and made up
            #: **22.6% of every pg statement parsed** in that capture.
            #:
            #: It is not Polaris's, carries no table, no verb and nothing to
            #: EXPLAIN -- and because a blank never matches a Polaris statement
            #: it fell straight through `_merge_pg_durations` into the report as
            #: a leftover. **35-38% of the statement entries in the 2026-09-02
            #: reports were these**, rendering as `[8] — · — · 0.06 ms` above an
            #: empty code block and inflating every per-API statement count by
            #: more than a third.
            #:
            #: Dropped at the parse boundary rather than in the renderer: a
            #: statement with no text is not a measurement, and anything
            #: downstream that counts statements would otherwise have to know
            #: about it separately.
            if not sql.strip():
                continue
            stmt = SqlStatement(
                seq=seq,
                sql=sql,
                table=extract_table(sql),
                verb=extract_verb(sql),
                source="postgres",
            )
            out.append(stmt)
            last_by_pid[pid] = stmt
            seq += 1
    return out


def parse_minio_trace(text, start_seq=0):
    """Parse `mc admin trace --json` output into MinioOp records.

    One JSON object per line. Unparseable lines are skipped rather than
    raising, because `mc` interleaves banner text with the stream and a single
    stray line should not abort a whole sweep.

    Only S3 API calls are kept -- `mc admin trace` also reports internal
    healing and metrics traffic, which is not Polaris activity and would
    otherwise inflate the counts.

    Returns:
        list[MinioOp] in stream order.
    """
    out = []
    seq = start_seq
    for line in text.splitlines():
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except (ValueError, TypeError):
            continue
        req = obj.get("request") or {}
        resp = obj.get("response") or {}
        path = req.get("path") or obj.get("path") or ""
        if not path:
            continue
        fn = obj.get("api") or obj.get("funcName") or ""
        if fn and not str(fn).startswith(("s3.", "S3.")) and "." in str(fn):
            continue
        bucket, _, key = path.lstrip("/").partition("/")
        dur_ns = obj.get("callStats", {}).get("duration") or obj.get("duration")
        duration_ms = None
        if isinstance(dur_ns, (int, float)):
            # mc reports nanoseconds; anything smaller is already ms.
            duration_ms = dur_ns / 1e6 if dur_ns > 1e4 else float(dur_ns)
        stats = obj.get("callStats") or {}
        out.append(
            MinioOp(
                seq=seq,
                method=(req.get("method") or obj.get("method") or "").upper(),
                path=path,
                bucket=bucket or None,
                key=key or None,
                status=resp.get("statusCode") or obj.get("statusCode"),
                duration_ms=duration_ms,
                rx=stats.get("rx"),
                tx=stats.get("tx"),
            )
        )
        seq += 1
    return out


# ----------------------------------------------------------------------
# stream sources
# ----------------------------------------------------------------------
class FileStream:
    """Reads only what a log file appended since the last mark.

    Deliberately dependency-free: the notebook redirects `kubectl logs -f`,
    `docker logs -f` and `mc admin trace --json` into plain files, and this
    reads the delta. Handles truncation (file replaced or rotated) by
    restarting from position 0 rather than returning garbage.
    """

    def __init__(self, path, encoding="utf-8"):
        self.path = path
        self.encoding = encoding
        self._pos = 0

    def exists(self):
        return os.path.exists(self.path)

    def mark(self):
        """Record the current end-of-file. Call immediately before the API call."""
        try:
            self._pos = os.path.getsize(self.path)
        except OSError:
            self._pos = 0
        return self._pos

    def read_since_mark(self):
        """Return everything appended since `mark()`, and advance the mark."""
        try:
            size = os.path.getsize(self.path)
        except OSError:
            return ""
        if size < self._pos:  # truncated or rotated
            self._pos = 0
        with open(self.path, "r", encoding=self.encoding, errors="replace") as fh:
            fh.seek(self._pos)
            data = fh.read()
            self._pos = fh.tell()
        return data


class StringStream:
    """In-memory stand-in for FileStream, for tests and dry runs."""

    def __init__(self, text=""):
        self.text = text
        self._pos = 0

    def exists(self):
        return True

    def mark(self):
        self._pos = len(self.text)
        return self._pos

    def read_since_mark(self):
        data = self.text[self._pos :]
        self._pos = len(self.text)
        return data

    def append(self, more):
        """Test helper: simulate the server writing more log output."""
        self.text += more


# ----------------------------------------------------------------------
# locating a capture
# ----------------------------------------------------------------------
def find_capture_dir(roots=None, env_var="CAPTURE_DIR", verbose=True):
    """Locate the capture directory that actually holds a run's logs.

    Resolve by CONTENT, never by name. Three things have to line up, and each
    one has silently gone wrong here at least once:

      * a notebook's cwd is its OWN directory, so a relative `"capture"`
        resolves under `diagnostics/api-sql-profile/` while the log may sit at
        the repo root;
      * `capture.sh rotate <dir>` writes to a NEW directory (`capture-seeded`,
        say), which no hardcoded `"capture"` would ever find -- it would
        analyse the stale pre-rotation logs instead, which is worse than
        failing;
      * an explicit choice must beat both.

    **The failure this exists to prevent.** Notebook 02 once picked the first
    directory whose `polaris.log` merely `.exists()`, in a fixed order that put
    `capture/` ahead of `capture-seeded/`. `capture/polaris.log` was a 0-byte
    leftover, so 02 parsed 0 records, built an empty inventory and reported all
    three index hypotheses INCONCLUSIVE -- while 01, reading the same cluster,
    had already CONFIRMED two. Nothing raised. Hence: non-empty is part of the
    predicate, and ties are broken by mtime rather than by sort order.

    Args:
        roots: iterable of directories to search. Defaults to the current
            directory and the repo root two levels up, evaluated at CALL time
            because a notebook's cwd is what makes them meaningful.
        env_var: environment variable that overrides the search entirely.
        verbose: print a note when more than one candidate exists, so a run
            that silently had a choice to make says so.

    Returns:
        pathlib.Path, or **None** when no candidate holds a non-empty
        `polaris.log`. None rather than a plausible-looking default: a consumer
        should assert and stop, and a producer that intends to CREATE the
        directory can spell that fallback out at the call site.
    """
    env = os.environ.get(env_var)
    if env:
        return pathlib.Path(env)

    if roots is None:
        cwd = pathlib.Path.cwd()
        roots = [pathlib.Path("."), cwd.parents[1] if len(cwd.parents) > 1 else cwd]

    cands = []
    for root in roots:
        for d in sorted(pathlib.Path(root).glob("capture*")):
            log = d / "polaris.log"
            if d.is_dir() and log.exists() and log.stat().st_size > 0:
                cands.append((log.stat().st_mtime, d))
    if not cands:
        return None

    cands.sort(key=lambda t: t[0], reverse=True)
    chosen = cands[0][1]
    if verbose and len(cands) > 1:
        others = ", ".join(str(d) for _, d in cands[1:])
        print(
            f"note: several capture dirs hold logs; using the newest "
            f"({chosen}). Others: {others}"
        )
    return chosen


# ----------------------------------------------------------------------
# measurement helpers
# ----------------------------------------------------------------------
#: Prevents Pgpool from routing a statement to a replica. Every EXPLAIN must
#: carry it: a replica can hold different statistics and would silently plan
#: differently, so a measurement taken there describes a node nobody asked
#: about. Assert `pg_is_in_recovery() = False` as well -- this hint is a
#: request to the pooler, not a guarantee from the server.
NO_LOAD_BALANCE = "/*NO LOAD BALANCE*/ "

#: Default repeats for `explain_n`, one of which is discarded as warm-up.
#:
#: Across two full runs the SAME plan -- Total Cost 810.16, 285 shared hits, 0
#: disk reads, 29,003 rows discarded by filter -- measured 7.523 / 3.289 /
#: 4.571 / 1.622 ms. A 4.6x spread with nothing structural changing, which
#: moved a reported speedup 11.6x -> 6.3x on noise alone. Plan SHAPE is
#: deterministic here; execution time is not.
EXPLAIN_N = 11


def explain(conn, sql, params=None, analyze=True, no_lb=True):
    """Run one EXPLAIN and return the plan dict.

    Args:
        conn: a psycopg2 connection. Pass the PRIMARY, or rely on `no_lb`.
        analyze: False issues a plan-only EXPLAIN. **Use False for writes** --
            `EXPLAIN ANALYZE` on an INSERT/UPDATE/DELETE really performs it.
    """
    mode = "(ANALYZE, BUFFERS, FORMAT JSON)" if analyze else "(FORMAT JSON)"
    pre = (NO_LOAD_BALANCE if no_lb else "") + f"EXPLAIN {mode} "
    with conn.cursor() as cur:
        cur.execute(pre + sql, params)
        return cur.fetchone()[0][0]


def explain_n(conn, sql, params=None, k=None, analyze=True, no_lb=True):
    """EXPLAIN k times, drop the first, return (median, min, max, last_plan, times).

    The discarded first run absorbs backend warm-up, which is not a rounding
    error: the first EXPLAIN in a fresh kernel has measured **25.2 ms against a
    1.3 ms steady-state median here -- 19x**. Any n=1 timing from a cold kernel
    is worthless, and reporting one as a result is how a measurement becomes an
    argument about noise.
    """
    k = k or EXPLAIN_N
    plans = [explain(conn, sql, params, analyze, no_lb) for _ in range(k)]
    times = sorted(p.get("Execution Time") for p in plans[1:])
    mid = len(times) // 2
    med = times[mid] if len(times) % 2 else (times[mid - 1] + times[mid]) / 2
    return med, times[0], times[-1], plans[-1], times


def timeit(fn, k=15, warmup=2):
    """Median wall-clock ms over k calls, discarding the first `warmup`.

    Warm-up is discarded for the same reason EXPLAIN drops its first run, and
    then some: the first call pays Polaris's `InMemoryEntityCache` miss AND
    pgjdbc's `prepareThreshold=5` promotion to a server-side prepared
    statement. Those are two distinct knees in the warm curve, both inside the
    first few iterations, and neither is what a schema change is about.

    Returns:
        (median, min, max) in milliseconds, over the k measured calls only.
    """
    xs = []
    for i in range(k + warmup):
        t0 = time.perf_counter()
        fn()
        dt = (time.perf_counter() - t0) * 1000
        if i >= warmup:
            xs.append(dt)
    return statistics.median(xs), min(xs), max(xs)


# ----------------------------------------------------------------------
# pg_stat_statements
# ----------------------------------------------------------------------
PG_STAT_COLUMNS = (
    "queryid, calls, total_exec_time, mean_exec_time, rows, "
    "shared_blks_hit, shared_blks_read, query"
)


def pg_stat_reset(conn):
    """Reset pg_stat_statements. Call immediately before a measured operation.

    Requires the extension to be installed (`shared_preload_libraries` plus
    `CREATE EXTENSION pg_stat_statements`) and sufficient privilege. Raises on
    failure rather than silently producing empty deltas -- a silent no-op here
    would look like "this API issued no SQL", which is exactly the wrong
    conclusion.
    """
    with conn.cursor() as cur:
        cur.execute("SELECT pg_stat_statements_reset()")
    conn.commit()


def pg_stat_snapshot(conn, min_calls=1):
    """Read pg_stat_statements as a list of dicts, busiest first.

    Args:
        conn: a live psycopg2 connection.
        min_calls: skip entries below this call count.

    Returns:
        list[dict] with keys matching PG_STAT_COLUMNS. `query` text is scrubbed
        through `scrub_text` before being returned.
    """
    sql = (
        f"SELECT {PG_STAT_COLUMNS} FROM pg_stat_statements "
        "WHERE calls >= %s ORDER BY total_exec_time DESC"
    )
    with conn.cursor() as cur:
        cur.execute(sql, (min_calls,))
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    for r in rows:
        if r.get("query"):
            r["query"] = scrub_text(r["query"])
    return rows


# ----------------------------------------------------------------------
# tracer
# ----------------------------------------------------------------------
class MultiStream:
    """A `FileStream` over SEVERAL files, concatenating each one's new output.

    Pgpool load-balances reads, so a statement Polaris issues can execute on any
    replica and its `duration:` line lands in THAT node's log. Reading one file
    attributes timings to a fraction of the statements and silently leaves the
    rest blank -- which looks identical to "durations are off" and sends you to
    the wrong fix.

    Lived in a cell of `01_api_access_map.ipynb` until 2026-09-01, where no
    runner could reach it: `drive_api_surface.py` built a Tracer without it and
    read one replica. Same interface as FileStream -- exists / mark /
    read_since_mark -- so the two are interchangeable.
    """

    def __init__(self, paths):
        self.streams = [FileStream(str(x)) for x in paths]

    def exists(self):
        return any(st.exists() for st in self.streams)

    def mark(self):
        for st in self.streams:
            st.mark()

    def read_since_mark(self):
        return "".join(st.read_since_mark() for st in self.streams)


class Tracer:
    """Wrap API calls in a trace window across the configured streams.

    Every stream is optional. With none configured the tracer still produces
    wall-clock timings, so a notebook degrades gracefully rather than failing
    when, say, the MinIO trace is not running.
    """

    def __init__(
        self,
        polaris_log=None,
        pg_log=None,
        minio_trace=None,
        pg_conn=None,
        settle_s=0.25,
        require_logger=True,
    ):
        """
        Args:
            polaris_log: stream for the Polaris application log (stream A).
            pg_log: stream for the PostgreSQL server log (stream B).
            minio_trace: stream for `mc admin trace --json` (stream C).
            pg_conn: psycopg2 connection for pg_stat_statements deltas.
            settle_s: pause after the API call before reading the streams.
                Logs are flushed asynchronously; without this, the tail end of
                a call's output is routinely missed and statements go
                uncounted. 0.25 s is enough locally -- raise it if statement
                counts come back unstable across repeats.
            require_logger: passed to `parse_polaris_log`.
        """
        self.polaris_log = polaris_log
        self.pg_log = pg_log
        self.minio_trace = minio_trace
        self.pg_conn = pg_conn
        self.settle_s = settle_s
        self.require_logger = require_logger
        self.records = []
        #: Statements naming a request id that is not this window's. Placed by
        #: `reattribute_deferred` once every record exists -- an async write
        #: can only be routed after the record it belongs to has been created.
        self.deferred = []
        #: `parse_pg_log`'s last-statement-per-pid, threaded between windows so
        #: a DETAIL line that arrives in the next read still reaches its
        #: statement. See parse_pg_log's `carry`.
        self._pg_carry = {}

    def _streams(self):
        return [s for s in (self.polaris_log, self.pg_log, self.minio_trace) if s]

    def trace(self, api, method=None, path=None, reset_pg_stat=False):
        """Context manager yielding a TraceRecord that is filled in on exit.

        Args:
            api: label for this operation, e.g. "iceberg.load_table".
            method / path: HTTP method and path, for the report.
            reset_pg_stat: reset pg_stat_statements before the call so the
                snapshot afterwards is a clean per-call delta. Costs a
                round trip; only worth it when you actually want the stats.

        Yields:
            TraceRecord -- set `.status` on it inside the block.
        """
        return _TraceContext(self, api, method, path, reset_pg_stat)


class _TraceContext:
    """Internal context-manager implementation for `Tracer.trace`."""

    def __init__(self, tracer, api, method, path, reset_pg_stat):
        self.tracer = tracer
        self.record = TraceRecord(api=api, method=method, path=path)
        self.reset_pg_stat = reset_pg_stat

    def __enter__(self):
        t = self.tracer
        if self.reset_pg_stat and t.pg_conn is not None:
            pg_stat_reset(t.pg_conn)
        for s in t._streams():
            s.mark()
        self.record.t0 = time.time()
        return self.record

    def __exit__(self, exc_type, exc, tb):
        t = self.tracer
        self.record.t1 = time.time()
        if exc is not None:
            # Record the failure and still collect: a failed call's SQL is
            # often the most interesting SQL there is.
            self.record.error = f"{exc_type.__name__}: {exc}"
        if t.settle_s:
            time.sleep(t.settle_s)

        if t.polaris_log:
            window = t.polaris_log.read_since_mark()
            self.record.sql.extend(
                parse_polaris_log(window, require_logger=t.require_logger)
            )
            #: Keep the raw window only when nothing parsed. By LINES and with
            #: each line truncated: one `listCatalogs returning:` line has
            #: measured 1,292,023 bytes here, and a diagnostic that blows up
            #: the report it is meant to explain helps nobody.
            if not self.record.sql:
                kept = [ln[:600] for ln in (window or "").splitlines()[-40:]]
                self.record.raw_log = "\n".join(kept)
        if t.pg_log:
            pg_stmts = parse_pg_log(t.pg_log.read_since_mark(), carry=t._pg_carry)
            known = {s.request_id for s in self.record.sql if s.request_id}
            t.deferred.extend(
                _merge_pg_durations(self.record.sql, pg_stmts, known) or []
            )
        if t.minio_trace:
            self.record.minio.extend(parse_minio_trace(t.minio_trace.read_since_mark()))
        if self.reset_pg_stat and t.pg_conn is not None:
            self.record.pg_stat = pg_stat_snapshot(t.pg_conn)

        t.records.append(self.record)
        return False  # never swallow the caller's exception


def _merge_pg_durations(polaris_stmts, pg_stmts, known_request_ids=None):
    """Attach server-side durations from stream B onto stream A's statements.

    Matched by normalized SQL, in order, so repeats of the same statement pair
    up 1:1.

    STATEMENTS ONLY POSTGRES SAW ARE APPENDED ONLY IF THEY ARE POLARIS'S
    (changed 2026-09-02, and this reverses an earlier decision). They used to be
    appended unconditionally, on the argument that pooler chatter is part of the
    real cost even though Polaris never logs it. Measured against a real drive,
    that argument does not survive: **390 of 780 statements in
    `doc-api-sql-matrix-unauthorized-20260902-170341.md` -- 50% -- were repmgr,
    Pgpool and psql traffic sharing the same server log**, led by 87
    `pg_is_in_recovery()`, 61 `repmgr.nodes` reads and 36
    `SET synchronous_commit`.

    The fatal part is not the volume, it is that this traffic is TIMER-DRIVEN.
    How much of it lands in an operation's window is proportional to how long
    that operation took, not to what it did: `mgmt.grant_privilege` showed
    178 foreign statements of 242 (74%), `mgmt.list_catalogs` 58 of 65 (89%).
    A per-API statement count built that way is a proxy for wall time wearing
    the label of work, and it inverts the point of the matrix.

    `is_polaris_statement` identifies them positively -- a statement counts only
    if it names the Polaris schema or one of its tables -- and
    `statement_inventory` has always used it. The record path did not, so the
    inventory was clean while the per-API detail it is derived from was not.
    """
    if not polaris_stmts:
        polaris_stmts.extend(p for p in pg_stmts if is_polaris_statement(p.sql))
        return []
    buckets = {}
    for p in pg_stmts:
        buckets.setdefault(normalize_sql(p.sql), []).append(p)
    for stmt in polaris_stmts:
        key = normalize_sql(stmt.sql)
        queue = buckets.get(key)
        if queue:
            match = queue.pop(0)
            if stmt.duration_ms is None:
                stmt.duration_ms = match.duration_ms
            if stmt.params is None and match.params is not None:
                stmt.params = match.params
    leftovers = [p for q in buckets.values() for p in q if is_polaris_statement(p.sql)]
    #: A statement that NAMES a request id belongs to THAT request, not to
    #: whichever window it happened to land in. Held back rather than appended,
    #: and returned so the caller can place it once every record exists.
    strays = [
        s
        for s in leftovers
        if s.request_id and known_request_ids and s.request_id not in known_request_ids
    ]
    if strays:
        _stray = {id(s) for s in strays}
        leftovers = [s for s in leftovers if id(s) not in _stray]
    next_seq = max((s.seq for s in polaris_stmts), default=-1) + 1
    for p in sorted(leftovers, key=lambda x: x.seq):
        p.seq = next_seq
        next_seq += 1
        polaris_stmts.append(p)
    return strays


# ----------------------------------------------------------------------
# reporting
# ----------------------------------------------------------------------
def reattribute_deferred(records, deferred):
    """Place async statements on the record whose request they actually name.

    An async write cannot be attributed by trace window -- "which window was
    open" is precisely the assumption it breaks. Polaris's event listener
    writes `POLARIS_SCHEMA.EVENTS` up to seconds after the call it describes
    (5.03 s measured 2026-09-02), so the row lands in a later operation's
    window and the report credits the wrong API. One such row was credited to
    `mgmt.create_principal`, a 403 that wrote nothing.

    The row names its own request in a `request_id` COLUMN, so routing is
    exact rather than heuristic. Statements whose request is not among the
    records are returned rather than dropped silently: the usual reason is a
    call that finished after the last window closed, and a count of those is
    the honest measure of what the capture missed.

    TWO ROUTES IN, because there are two ways a row goes astray and only one
    of them can be caught while the window is open:

      1. the row arrived with its `request_id` already parsed, so the merge
         held it back as a stray -- `deferred`;
      2. the row's `DETAIL:  Parameters:` line arrived in the NEXT read, so it
         had no request_id when the merge saw it and was appended to the wrong
         record before its id was known. Only a post-pass over the finished
         records can see that one, which is why this is a post-pass.

    Route 2 is what actually bit on 2026-09-03: the mechanism for route 1 was
    correct and simply never fired.

    Args:
        records: every `TraceRecord` from the drive, in order.
        deferred: `Tracer.deferred` -- statements held back by the merge.

    Returns:
        (placed, unplaceable) -- how many were routed, and how many named a
        request that is not in this capture at all.
    """
    #: Ownership comes from the POLARIS-side statements, which carry
    #: `mdc.requestId` and are logged synchronously inside their own request.
    owner = {}
    for rec in records:
        for s in rec.sql:
            if s.request_id and s.source != "postgres":
                owner.setdefault(s.request_id, rec)

    placed = 0
    unplaceable = []

    #: PASS 1 -- statements ALREADY on a record but on the WRONG one. A pg
    #: statement whose DETAIL line arrived a window late gains its request_id
    #: only after it was appended (see parse_pg_log's `carry`), so holding
    #: strays back at merge time cannot catch it. Checking placement here
    #: catches both routes, and is the reason this runs as a post-pass at all.
    for rec in records:
        for s in list(rec.sql):
            if not s.request_id or s.source != "postgres":
                continue
            target = owner.get(s.request_id)
            if target is None or target is rec:
                continue
            rec.sql.remove(s)
            s.seq = max((x.seq for x in target.sql), default=-1) + 1
            target.sql.append(s)
            placed += 1

    #: PASS 2 -- statements held back by the merge because they named another
    #: window's request and were never appended anywhere.
    for stmt in deferred or []:
        rec = owner.get(stmt.request_id)
        if rec is None:
            unplaceable.append(stmt)
            continue
        stmt.seq = max((s.seq for s in rec.sql), default=-1) + 1
        rec.sql.append(stmt)
        placed += 1

    return placed, len(unplaceable)


def records_to_rows(records):
    """Flatten TraceRecords into row dicts for a summary DataFrame."""
    return [r.to_row() for r in records]


# Statements that are NOT Polaris's. `log_statement='all'` records every
# statement the server executes, so the pg log also carries repmgr's monitoring
# daemon (repmgr.nodes, repmgr.get_local_node_id()), Pgpool's health checks and
# connection handoff (SET, DISCARD ALL, pg_stat_replication), and psql's own
# chatter. None of it is issued by Polaris, none of it can be EXPLAINed as
# written, and including it produced 19 ERROR rows that buried the real
# verdicts.
_FOREIGN_SCHEMA = re.compile(
    r"\brepmgr\.|\bpg_catalog\.|\bpg_stat_|\binformation_schema\.", re.I
)
# Not EXPLAINable at all: session/transaction control, not queries.
_NON_QUERY = re.compile(
    r"^\s*(SET|SHOW|DISCARD|BEGIN|COMMIT|ROLLBACK|RESET|DEALLOCATE|LISTEN|"
    r"CHECKPOINT|VACUUM|ANALYZE|START\s+TRANSACTION)\b",
    re.I,
)


def is_polaris_statement(sql):
    """True if this statement is one Polaris issued against its own metastore.

    Positive identification, not exclusion: a statement counts only if it names
    the Polaris schema or one of its tables. Anything else -- another schema's
    query, a SET, a health check -- is someone else's traffic sharing the same
    server log.
    """
    if not sql or _NON_QUERY.match(sql):
        return False
    if _FOREIGN_SCHEMA.search(sql):
        return False
    low = sql.lower()
    if "polaris_schema" in low:
        return True
    known = POLARIS_TABLES_V2 | EVENT_LISTENER_TABLES
    return any(re.search(rf"\b{t}\b", low) for t in known)


def statement_inventory(records):
    """Group every statement seen across all records by normalized SQL.

    This is the artifact the index audit consumes: the distinct statement set,
    with how often each ran, which APIs issued it, and its observed timing.
    Ranked by `total_ms` where available, otherwise by call count -- because
    the statement worth fixing is the moderately slow one on the auth path,
    not the slowest single outlier.

    Returns:
        list[dict] with keys: sql, table, verb, calls, apis, total_ms, mean_ms,
        max_ms.
    """
    groups = {}
    skipped_foreign = 0
    for rec in records:
        for s in rec.sql:
            if not is_polaris_statement(s.sql):
                skipped_foreign += 1
                continue
            key = normalize_sql(s.sql)
            g = groups.setdefault(
                key,
                {
                    "sql": key,
                    "table": s.table,
                    "verb": s.verb,
                    "calls": 0,
                    "apis": set(),
                    "_durations": [],
                },
            )
            g["calls"] += 1
            g["apis"].add(rec.api)
            if s.duration_ms is not None:
                g["_durations"].append(s.duration_ms)
    out = []
    for g in groups.values():
        d = g.pop("_durations")
        g["apis"] = sorted(g["apis"])
        g["total_ms"] = round(sum(d), 3) if d else None
        g["mean_ms"] = round(sum(d) / len(d), 3) if d else None
        g["max_ms"] = round(max(d), 3) if d else None
        out.append(g)
    out.sort(key=lambda r: (r["total_ms"] is None, -(r["total_ms"] or 0), -r["calls"]))
    statement_inventory.skipped_foreign = skipped_foreign
    return out


def api_table_matrix(records):
    """Build the API -> table access matrix.

    Returns:
        dict: {api: {table: "R" | "W" | "RW"}}. SELECT counts as R; INSERT,
        UPDATE and DELETE count as W.
    """
    matrix = {}
    for rec in records:
        row = matrix.setdefault(rec.api, {})
        for s in rec.sql:
            if not s.table or s.table in ASYNC_WRITE_TABLES:
                continue
            verb = (s.verb or "").upper()
            if verb == "SELECT":
                mode = "R"
            elif verb in ("INSERT", "UPDATE", "DELETE"):
                mode = "W"
            else:
                continue
            prev = row.get(s.table)
            row[s.table] = "RW" if prev and prev != mode else mode
    return matrix


def api_minio_matrix(records):
    """Build the API -> MinIO access matrix.

    Returns:
        dict: {api: [{"method":..., "path":..., "count":...}, ...]}, so the
        report can answer "which API touches which directory in storage".
    """
    matrix = {}
    for rec in records:
        agg = {}
        for m in rec.minio:
            k = (m.method, m.path)
            agg[k] = agg.get(k, 0) + 1
        matrix.setdefault(rec.api, [])
        for (method, path), count in sorted(agg.items()):
            matrix[rec.api].append({"method": method, "path": path, "count": count})
    return matrix


def unknown_tables(records):
    """Tables observed that are NOT part of the expected 1.3.0 schema-v2 set.

    A non-empty result means either the parser mis-read something or the
    deployed schema is not the version assumed -- both worth knowing before
    trusting any of the mapping output.
    """
    seen = {s.table for rec in records for s in rec.sql if s.table}
    known = POLARIS_TABLES_V2 | EVENT_LISTENER_TABLES
    return sorted(seen - known - {None})
