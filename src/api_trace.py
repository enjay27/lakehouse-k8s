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

    print(t.tables_touched, t.sql_count, t.minio_count, t.cache_verdict)
"""

import json
import os
import re
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
_PG_DETAIL_PARAMS = re.compile(r"\bDETAIL:\s+parameters:\s*(?P<params>.+?)\s*$")
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
    def cache_verdict(self):
        """MISS / HIT / N/A, inferred from SQL shape.

        MISS -- a full-column SELECT against `entities` was issued, so the
                resolver had to load entities from the metastore.
        HIT  -- only the batched version-check query appeared; everything else
                came from the entity cache.
        N/A  -- no entity reads at all (e.g. `GET /v1/config`), so the question
                does not apply.

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
            "cache_verdict": self.cache_verdict,
            "error": self.error,
        }


# ----------------------------------------------------------------------
# redaction
# ----------------------------------------------------------------------
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
    parts = _WHERE_SPLIT.split(s, 1)
    where = parts[1] if len(parts) > 1 else ""
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


def parse_pg_log(text, start_seq=0):
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
    last_by_pid = {}
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
                stmt.params = redact_params(stmt.sql, pm.group("params"))
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
            self.record.sql.extend(
                parse_polaris_log(
                    t.polaris_log.read_since_mark(), require_logger=t.require_logger
                )
            )
        if t.pg_log:
            pg_stmts = parse_pg_log(t.pg_log.read_since_mark())
            _merge_pg_durations(self.record.sql, pg_stmts)
        if t.minio_trace:
            self.record.minio.extend(parse_minio_trace(t.minio_trace.read_since_mark()))
        if self.reset_pg_stat and t.pg_conn is not None:
            self.record.pg_stat = pg_stat_snapshot(t.pg_conn)

        t.records.append(self.record)
        return False  # never swallow the caller's exception


def _merge_pg_durations(polaris_stmts, pg_stmts):
    """Attach server-side durations from stream B onto stream A's statements.

    Matched by normalized SQL, in order, so repeats of the same statement pair
    up 1:1. Statements seen only by Postgres (BEGIN/COMMIT/SET, pooler
    chatter) are appended rather than dropped -- they are part of the real
    cost even though Polaris never logs them.
    """
    if not polaris_stmts:
        polaris_stmts.extend(pg_stmts)
        return
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
    leftovers = [p for q in buckets.values() for p in q]
    next_seq = max((s.seq for s in polaris_stmts), default=-1) + 1
    for p in sorted(leftovers, key=lambda x: x.seq):
        p.seq = next_seq
        next_seq += 1
        polaris_stmts.append(p)


# ----------------------------------------------------------------------
# reporting
# ----------------------------------------------------------------------
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
