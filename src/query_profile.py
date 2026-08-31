"""Post-hoc correlation of a privilege-scan capture: which SQL each API issued.

`api_trace.Tracer` is a LIVE instrument -- it marks a stream, makes one call,
reads the delta. This module is its post-hoc counterpart, for the case the
privilege scan produces: 15,000 requests that have already happened, written
into a 264 MB capture, correlated afterwards on `mdc.requestId`.

That is not a downgrade. `requestId` is a first-class MDC field on every Polaris
log line, so attribution here is EXACT, where a live tracer's is a time window
around one call.

WHAT IT JOINS
-------------
Two loggers in the same `polaris.log`, keyed on the same requestId:

    io.quarkus.http.access-log     -> principal, method, concrete path, STATUS
    ...DatasourceOperations        -> the SQL statements that request issued

`api_trace.parse_polaris_log` already yields the second with `request_id`
populated. The first has no parser anywhere in the repo, and without it a
statement cannot be attributed to an API at all -- only to a request id. So
`parse_access_log` is the piece that turns 109,010 statements into a per-API,
per-outcome distribution.

THE OP LABEL IS NOT RE-DERIVED BY HAND
--------------------------------------
A concrete path (`/api/catalog/v1/user1000_catalog/namespaces/ns1/views`) has to
become the op label the run JSON uses (`GET  /namespaces/{ns}/views`), or the
report and the run disagree about what was measured. `operation_templates()`
gets those templates by driving `api_sweep.read_operations` -- the single
definition of the surface -- against a real `PolarisREST` whose `requests`
module is swapped for a recorder. The URLs therefore come from `polaris_rest`
itself. Writing a second method->path table here is how the two drift apart.

WHAT IT DELIBERATELY DOES NOT DO
--------------------------------
It does not time anything. This capture was taken with statement logging ON,
which inflates the clock 4.6x (measured, MEMORY.md). `duration_ms` from the
PostgreSQL log is carried through and rendered, but every renderer labels it
inflated, because a millisecond column that does not say so will be quoted.

The durable evidence is plan shape, buffers and rows-filtered -- and those come
from EXPLAIN, in the runner, not from here.
"""

import json
import re
from dataclasses import dataclass, field

from api_trace import REDACTED, normalize_sql, parse_polaris_log

#: How much of a log file to hold in memory at once. The captures this reads
#: are 60-120 MB each and the parsers take text, so a whole-file read would
#: cost the file size twice over (raw + parsed) at peak.
CHUNK_BYTES = 8 << 20

#: `DatasourceOperations` renders parameters as newline-separated text, so a
#: single statement can span physical lines -- but only inside a JSON log line's
#: `message` string, which is itself one physical line. Chunking on line
#: boundaries is therefore safe for the JSON format, and this module requires
#: it (`quarkus.log.console.json.enabled=true`, as the capture already uses).
ACCESS_LOGGER = "io.quarkus.http.access-log"

#: Sentinel entity names for template extraction. Distinct enough not to occur
#: in a real path, and chosen so no sentinel is a substring of another --
#: "QPCATALOGQP" is not a prefix of "QPCATALOGROLEQP".
_SENTINELS = {
    "catalog": "QPCATALOGQP",
    "namespace": "QPNSQP",
    "principal": "QPPRINCIPALQP",
    "principal_role": "QPPRINCIPALROLEQP",
    "catalog_role": "QPCATALOGROLEQP",
    #: The entity-level keys `full_read_operations` needs. Present here even
    #: though the 13-op surface never reads them: `_require` raises
    #: `UndriveableOp` on a None, so a sentinel fixture missing these cannot
    #: build templates for the ops that most need them.
    "table": "QPTABLEQP",
    "view": "QPVIEWQP",
    "generic_table": "QPGENERICTABLEQP",
    "policy": "QPPOLICYQP",
}
_SENTINEL_BASE = "http://qp-template"

_ACCESS_LINE = re.compile(
    r"^(?P<ip>\S+)\s+\S+\s+(?P<principal>\S+)\s+"
    r"\[(?P<clf>[^\]]*)\]\s+"
    r'"(?P<method>[A-Z]+)\s+(?P<target>\S+)(?:\s+HTTP/[\d.]+)?"\s+'
    r"(?P<status>\d{3})\s+(?P<bytes>\S+)"
)

#: `2026-08-24 03:31:27.597 GMT [258] LOG:  ...`
_PG_LINE_TS = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?)\s*(?P<tz>[A-Z]{2,5})?\s"
)


# ----------------------------------------------------------------------
# records
# ----------------------------------------------------------------------
@dataclass
class AccessRecord:
    """One HTTP request as the access log saw it.

    `status` is the whole reason this parser exists: the statement stream says
    nothing about whether the request it belongs to was permitted, and the
    200-vs-403 split is what settles whether a refused request pays the
    authorization prelude.
    """

    request_id: str
    principal: str
    method: str
    path: str
    query: str
    status: int
    bytes: int
    timestamp: str = None

    @property
    def ok(self):
        return 200 <= self.status < 300


@dataclass
class OpTemplate:
    """An op label plus the URL shape that produces it.

    `pattern` is anchored and full-match, so `/catalogs` cannot be mistaken for
    `/catalogs/{name}` and no most-specific-first ordering is needed.
    """

    label: str
    surface: str
    method: str
    template: str
    pattern: object


@dataclass
class RequestProfile:
    """One request, its op label, its outcome, and every statement it issued."""

    request_id: str
    label: str
    surface: str
    method: str
    path: str
    principal: str
    status: int
    timestamp: str = None
    statements: list = field(default_factory=list)

    @property
    def ok(self):
        return 200 <= self.status < 300

    @property
    def n_statements(self):
        return len(self.statements)

    def touching(self, table):
        return [s for s in self.statements if (s.table or "").lower() == table]


@dataclass
class Correlation:
    """The join, plus everything about it that did not line up.

    The unmatched counts are not diagnostics to be logged and forgotten. A
    statement whose request has no access-log line is a statement missing from
    the distribution, and a report that silently drops it is describing a
    subset as if it were the whole.
    """

    profiles: list = field(default_factory=list)
    orphan_statements: int = 0
    orphan_request_ids: list = field(default_factory=list)
    unclassified_paths: dict = field(default_factory=dict)
    access_records: int = 0
    statements: int = 0

    def by_label(self):
        out = {}
        for p in self.profiles:
            out.setdefault(p.label, []).append(p)
        return out


# ----------------------------------------------------------------------
# streaming
# ----------------------------------------------------------------------
def iter_log_chunks(path, chunk_bytes=CHUNK_BYTES, encoding="utf-8"):
    """Yield a large log file as line-aligned text chunks.

    Line-aligned matters: both parsers are line-oriented, and a chunk that ends
    mid-line would drop that line from one chunk and produce an unparseable
    fragment in the next -- silently, since both parsers skip what they cannot
    parse.
    """
    with open(path, "r", encoding=encoding, errors="replace") as fh:
        buf = ""
        while True:
            block = fh.read(chunk_bytes)
            if not block:
                break
            buf += block
            cut = buf.rfind("\n")
            if cut == -1:
                continue
            yield buf[: cut + 1]
            buf = buf[cut + 1 :]
        if buf:
            yield buf


# ----------------------------------------------------------------------
# the access log (GAP 2)
# ----------------------------------------------------------------------
def parse_access_log(text, logger=ACCESS_LOGGER):
    """Parse Quarkus access-log lines into `AccessRecord`s.

    Only the JSON console format is supported, deliberately: it carries
    `mdc.requestId` as a field, and the requestId is the entire join key. A
    plain-text access log has no request id in it at all, so accepting one
    would produce records that can never be correlated -- better to return
    nothing and have the caller notice.
    """
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("{") or logger not in line:
            continue
        try:
            obj = json.loads(line)
        except (ValueError, TypeError):
            continue
        if not isinstance(obj, dict) or (obj.get("loggerName") or "") != logger:
            continue
        m = _ACCESS_LINE.match(obj.get("message") or "")
        if not m:
            continue
        rid = (obj.get("mdc") or {}).get("requestId")
        if not rid:
            continue
        target = m.group("target")
        path, _, query = target.partition("?")
        try:
            nbytes = int(m.group("bytes"))
        except ValueError:  # "-" for an empty body
            nbytes = 0
        out.append(
            AccessRecord(
                request_id=rid,
                principal=m.group("principal"),
                method=m.group("method"),
                path=path,
                query=query,
                status=int(m.group("status")),
                bytes=nbytes,
                timestamp=obj.get("timestamp"),
            )
        )
    return out


# ----------------------------------------------------------------------
# op labels, derived rather than transcribed
# ----------------------------------------------------------------------
class _RecordingRequests:
    """Stand-in for the `requests` module that records URLs instead of calling.

    Swapped into `polaris_rest` for the length of `operation_templates()` so a
    real client builds real URLs with no network and no cluster.
    """

    def __init__(self):
        self.calls = []

    def _record(self, method):
        def go(url, **kw):
            params = kw.get("params") or {}
            self.calls.append((method, url, params))
            return _StubResponse()

        return go

    def __getattr__(self, name):
        if name in ("get", "post", "put", "delete", "head", "patch"):
            return self._record(name.upper())
        raise AttributeError(name)


class _StubResponse:
    status_code = 200
    text = ""

    def json(self):
        return {}


def operation_templates(read_operations=None, include_token=True):
    """The op surface as (label, method, URL template, matcher).

    Built by DRIVING `api_sweep.read_operations` against a real `PolarisREST`
    whose `requests` module is a recorder. So the labels and their order come
    from `api_sweep` -- the single definition of the surface -- and the paths
    come from `polaris_rest`. Neither is restated here, which is the point:
    a hand-written method-to-path table in this module would drift from the
    client the scan actually used, and the drift would show up as
    "unclassified path", i.e. as a fixture fault rather than as the bug it is.
    """
    import api_sweep
    import polaris_rest

    read_operations = read_operations or api_sweep.read_operations
    fixture = dict(_SENTINELS)
    recorder = _RecordingRequests()
    real = polaris_rest.requests
    polaris_rest.requests = recorder
    try:
        pc = polaris_rest.PolarisREST(_SENTINEL_BASE, "POLARIS")
        #: `_h()` refuses to build headers without one. Nothing is sent --
        #: `requests` is the recorder -- but the client does not know that.
        pc.token = "template"
        ops = read_operations(fixture)
        templates = []
        for label, surface, fn in ops:
            before = len(recorder.calls)
            fn(pc)
            if len(recorder.calls) != before + 1:
                # An op that issued no request, or more than one, cannot be
                # mapped to a single path. Say so rather than guessing.
                raise RuntimeError(
                    f"{label!r} issued {len(recorder.calls) - before} HTTP calls "
                    "while building templates; expected exactly 1"
                )
            method, url, _params = recorder.calls[-1]
            templates.append(_template_from(label, surface, method, url))
        if include_token:
            before = len(recorder.calls)
            pc.get_token("client", "secret")
            method, url, _params = recorder.calls[-1]
            templates.append(_template_from("POST /oauth/tokens", "auth", method, url))
    finally:
        polaris_rest.requests = real
    return templates


def _template_from(label, surface, method, url):
    path = url[len(_SENTINEL_BASE) :] if url.startswith(_SENTINEL_BASE) else url
    path = path.partition("?")[0]
    template = path
    regex = re.escape(path)
    #: Longest sentinel first so no substitution can eat a prefix of another.
    for name, token in sorted(_SENTINELS.items(), key=lambda kv: -len(kv[1])):
        template = template.replace(token, "{" + name + "}")
        regex = regex.replace(re.escape(token), f"(?P<{name}>[^/]+)")
    return OpTemplate(
        label=label,
        surface=surface,
        method=method,
        template=template,
        pattern=re.compile("^" + regex + "$"),
    )


def classify(method, path, templates):
    """(label, surface, {entity: value}) for a concrete request, or (None, None, {})."""
    for t in templates:
        if t.method != method:
            continue
        m = t.pattern.match(path)
        if m:
            return t.label, t.surface, m.groupdict()
    return None, None, {}


# ----------------------------------------------------------------------
# the join
# ----------------------------------------------------------------------
def correlate(polaris_log_path, templates=None, chunk_bytes=CHUNK_BYTES):
    """Join every request's access-log line to the statements it issued.

    Streams the file once per chunk through both parsers, so peak memory is a
    chunk plus the parsed records rather than the whole 120 MB file.
    """
    templates = templates if templates is not None else operation_templates()
    access = {}
    stmts_by_rid = {}
    seq = 0
    n_stmts = 0

    for chunk in iter_log_chunks(polaris_log_path, chunk_bytes):
        for rec in parse_access_log(chunk):
            access[rec.request_id] = rec
        got = parse_polaris_log(chunk, start_seq=seq)
        seq += len(got)
        n_stmts += len(got)
        for st in got:
            if st.request_id:
                stmts_by_rid.setdefault(st.request_id, []).append(st)

    corr = Correlation(access_records=len(access), statements=n_stmts)
    for rid, rec in access.items():
        label, surface, _ents = classify(rec.method, rec.path, templates)
        if label is None:
            corr.unclassified_paths[f"{rec.method} {rec.path}"] = (
                corr.unclassified_paths.get(f"{rec.method} {rec.path}", 0) + 1
            )
            label, surface = f"{rec.method} {rec.path}", "unclassified"
        corr.profiles.append(
            RequestProfile(
                request_id=rid,
                label=label,
                surface=surface,
                method=rec.method,
                path=rec.path,
                principal=rec.principal,
                status=rec.status,
                timestamp=rec.timestamp,
                statements=stmts_by_rid.get(rid, []),
            )
        )

    for rid, sts in stmts_by_rid.items():
        if rid not in access:
            corr.orphan_statements += len(sts)
            if len(corr.orphan_request_ids) < 20:
                corr.orphan_request_ids.append(rid)

    corr.profiles.sort(key=lambda p: (p.timestamp or "", p.request_id))
    return corr


# ----------------------------------------------------------------------
# windowing (GAP 3)
# ----------------------------------------------------------------------
def profile_window(profiles):
    """(first, last) timestamp across correlated requests, as ISO strings."""
    stamps = sorted(p.timestamp for p in profiles if p.timestamp)
    return (stamps[0], stamps[-1]) if stamps else (None, None)


def _iso_key(ts):
    """A sortable key from either log format, without a datetime dependency.

    Polaris writes `2026-08-24T03:31:47.981196241Z` (9 fractional digits, which
    `datetime.fromisoformat` rejects) and PostgreSQL writes
    `2026-08-24 03:31:27.597 GMT`. Both are fixed-width UTC, so normalising the
    separator and padding the fraction makes plain string comparison correct
    and total -- and correctness here is worth more than a datetime object
    nothing else needs.
    """
    if not ts:
        return ""
    s = ts.strip().rstrip("Z").replace("T", " ")
    s = re.sub(r"\s*(GMT|UTC)$", "", s)
    date, _, rest = s.partition(" ")
    clock, dot, frac = rest.partition(".")
    frac = (frac + "000000000")[:9] if dot else "000000000"
    return f"{date} {clock}.{frac}"


def window_pg_text(text, start, end):
    """Clip raw PostgreSQL log text to [start, end], keeping continuation lines.

    The captures this reads keep growing after the drive ends -- statement
    logging stays enabled until `capture.sh pgoff` -- so `pg-*.log` holds
    (in the 2026-08-24 pass) 101 minutes of unrelated traffic past the last
    request. Merged in, that traffic contributes durations for statements no
    API in this run issued.

    A continuation line carries no timestamp prefix; it inherits the verdict of
    the last timestamped line, or the multi-line statements `parse_pg_log` was
    fixed to reassemble get truncated again.
    """
    lo, hi = _iso_key(start), _iso_key(end)
    keep = []
    inside = False
    for line in text.splitlines(True):
        m = _PG_LINE_TS.match(line)
        if m:
            inside = lo <= _iso_key(m.group("ts")) <= hi
        if inside:
            keep.append(line)
    return "".join(keep)


# ----------------------------------------------------------------------
# profiling
# ----------------------------------------------------------------------
@dataclass
class StatementProfile:
    """One distinct statement shape, as seen across a set of requests.

    TWO SQL FIELDS, AND THEY ARE NOT INTERCHANGEABLE
    ------------------------------------------------
    `sql` is `normalize_sql` output: the GROUPING KEY. It is what the report
    prints, and it is deliberately not executable -- `normalize_sql` collapses
    a row-constructor `IN ((?,?),(?,?),...)` to `IN (<rows>)` so one statement
    can be counted across calls whose IN-list length varies.

    `sample_sql` is one occurrence's RAW text, kept together with the
    parameters from that same occurrence. It is what EXPLAIN must replay.

    Sending `sql` to EXPLAIN fails with `syntax error at or near "<"`, which is
    how this was found (2026-08-31, first `--explain` run: 7 of 8 statements
    errored). Keeping the pair atomic matters for the same reason: parameters
    taken from a different occurrence than the SQL can disagree on placeholder
    count, and a mismatched replay is worse than a refused one.
    """

    sql: str
    table: str
    verb: str
    occurrences: int
    requests: int
    labels: dict = field(default_factory=dict)
    sample_sql: str = None
    sample_params: str = None
    durations_ms: list = field(default_factory=list)

    @property
    def per_request(self):
        return self.occurrences / self.requests if self.requests else 0.0

    @property
    def params_observed(self):
        return bool(self.sample_params) and REDACTED not in self.sample_params

    @property
    def replayable(self):
        """Whether this statement can be EXPLAINed exactly as it was issued.

        Not just "are the parameters unredacted" -- the placeholder count has
        to match too. `split_query_message` splits SQL from parameters BY that
        count, so a mismatch here means the fallback path was taken and the
        split is not trustworthy. Refusing is the honest answer; a replay with
        the wrong number of bound values would either error or, worse, succeed
        against a different statement than the one being reported.
        """
        if not (self.sample_sql and self.params_observed):
            return False
        return self.sample_sql.count("?") == len(param_tuple(self.sample_params))

    def replay(self):
        """(sql, params) ready for psycopg2, or (None, None) if not replayable."""
        if not self.replayable:
            return None, None
        return to_psycopg(self.sample_sql), param_tuple(self.sample_params)


def param_tuple(sample_params):
    """The logged parameter string back into a tuple, in issue order.

    `split_query_message` joins the bound values with ", " after validating
    that their count matches the statement's placeholder count, so splitting on
    the same separator round-trips. Values stay STRINGS: PostgreSQL resolves an
    unknown-typed literal against the column it is compared to, so `id = '1002'`
    plans as bigint. Guessing types here is how a bigint predicate silently
    becomes a text one and the plan changes underneath the measurement.
    """
    if not sample_params:
        return ()
    return tuple(p.strip() for p in sample_params.split(", ") if p.strip())


def to_psycopg(sql):
    """JDBC `?` placeholders into psycopg2 `%s`.

    NOT cosmetic. `?` is a valid operator character in PostgreSQL -- jsonb uses
    `?`, `?|`, `?&` -- so a statement sent with `?` intact does not fail at the
    placeholder. The parser reads `= ?` as an operator expression and then
    chokes on the next token, reporting `syntax error at or near "AND"`: an
    error that points at a keyword several tokens away from the actual cause.
    That misdirection cost the first `--explain` run (2026-08-31).

    Any literal `%` is escaped first, since psycopg2 treats `%` as its own
    placeholder introducer once parameters are passed.
    """
    return sql.replace("%", "%%").replace("?", "%s")


def statement_profile(profiles):
    """Distinct statements across `profiles`, keyed by normalised SQL."""
    out = {}
    for p in profiles:
        seen_here = set()
        for st in p.statements:
            key = normalize_sql(st.sql)
            sp = out.get(key)
            if sp is None:
                sp = out[key] = StatementProfile(
                    sql=key,
                    table=st.table,
                    verb=st.verb,
                    occurrences=0,
                    requests=0,
                )
            sp.occurrences += 1
            sp.labels[p.label] = sp.labels.get(p.label, 0) + 1
            #: Prefer a representative whose parameters were actually observed.
            #: `redact_params` blanks the whole set for a SECRET_TABLES
            #: statement, and an EXPLAIN replayed with "<redacted>" is not a
            #: replay of anything. SQL and parameters are taken from the SAME
            #: occurrence, always, so their placeholder counts agree.
            if st.params and (
                sp.sample_params is None
                or (not sp.params_observed and REDACTED not in st.params)
            ):
                sp.sample_params = st.params
                sp.sample_sql = st.sql
            if st.duration_ms is not None:
                sp.durations_ms.append(st.duration_ms)
            if key not in seen_here:
                sp.requests += 1
                seen_here.add(key)
    return out


def per_label_summary(corr, table="grant_records"):
    """Per op label: requests, statuses, statements/request, `table` hits/request."""
    rows = []
    for label, ps in corr.by_label().items():
        n = len(ps)
        stmts = sum(p.n_statements for p in ps)
        hits = sum(len(p.touching(table)) for p in ps)
        statuses = {}
        for p in ps:
            statuses[p.status] = statuses.get(p.status, 0) + 1
        rows.append(
            {
                "label": label,
                "surface": ps[0].surface,
                "requests": n,
                "statuses": statuses,
                "statements": stmts,
                "per_request": stmts / n if n else 0.0,
                "table_hits": hits,
                "table_per_request": hits / n if n else 0.0,
            }
        )
    rows.sort(key=lambda r: (-r["per_request"], r["label"]))
    return rows


def prelude_by_outcome(corr, table="grant_records"):
    """The 200-vs-403 question, answered from the capture rather than the source.

    `scan_privileges.py` asserts that "a refused request still pays the full
    7-statement authorization prelude ... so the grantee lookup fires on the
    denial path too", and its own docstring names asserting-from-source as the
    mistake `cache_verdict` was. This is the measurement: same fixture, same
    index state, same clock, 8,000 permitted requests and 6,000 refused.

    Returns per outcome class the statement counts, and the statement shapes
    that appear in one class and not the other -- the difference, if any, IS
    the short-circuit.
    """
    classes = {}
    for p in corr.profiles:
        if p.surface == "unclassified":
            #: Its own class, never folded into "permitted". A Kubernetes
            #: readiness probe answers 200 and issues no SQL, so counting one
            #: as a permitted API call drags the permitted mean toward zero --
            #: in exactly the direction that would make a prelude look
            #: cheaper than it is.
            key = "unclassified (not an op)"
        elif p.surface == "auth":
            key = "auth (token)"
        elif p.ok:
            key = "permitted (2xx)"
        elif p.status == 403:
            key = "refused (403)"
        else:
            key = f"other ({p.status})"
        classes.setdefault(key, []).append(p)

    out = {}
    for key, ps in classes.items():
        counts = sorted(p.n_statements for p in ps)
        shapes = statement_profile(ps)
        out[key] = {
            "requests": len(ps),
            "statements": sum(counts),
            "per_request": (sum(counts) / len(counts)) if counts else 0.0,
            "min": counts[0] if counts else 0,
            "median": counts[len(counts) // 2] if counts else 0,
            "max": counts[-1] if counts else 0,
            "table_per_request": (
                sum(len(p.touching(table)) for p in ps) / len(ps) if ps else 0.0
            ),
            "shapes": set(shapes),
            "labels": sorted({p.label for p in ps}),
        }

    permitted = out.get("permitted (2xx)", {}).get("shapes", set())
    refused = out.get("refused (403)", {}).get("shapes", set())
    return out, {
        "only_permitted": sorted(permitted - refused),
        "only_refused": sorted(refused - permitted),
        "shared": sorted(permitted & refused),
    }


def explain_worklist(shapes, table=None, limit=None):
    """Distinct statements worth an EXPLAIN, most-frequent first.

    Only statements whose parameters were actually observed can be replayed
    verbatim; the rest are returned too, flagged, because the report must say
    a parameter was reconstructed rather than quietly substitute one.
    """
    items = sorted(shapes.values(), key=lambda s: -s.occurrences)
    if table:
        items = [s for s in items if (s.table or "").lower() == table]
    return items[:limit] if limit else items


# ----------------------------------------------------------------------
# reconciliation against the drive's own record
# ----------------------------------------------------------------------
#: A label the harness records for a call it made to PREPARE a drive, not an
#: operation the drive measured: `GET  /namespaces [ns-resolve]`,
#: `GET  /namespaces/{ns}/tables [entity-resolve]`. The bracketed suffix is the
#: marker, so a new preparation call needs no change here.
_HARNESS_SUFFIX = re.compile(r"\s*\[[a-z-]+\]\s*$")


def base_label(label):
    """The operation a harness-preparation label shares its path with.

    These are REAL requests on real op paths -- `GET /namespaces/{ns}/tables` is
    issued both to resolve a table target and as the operation itself -- so the
    capture holds them and the reconciliation must expect them. Folding on the
    bracketed suffix generalises what was a special case for ns-resolve;
    without it, entity resolution makes four ops per identity read as an
    unexplained 2x.
    """
    return _HARNESS_SUFFIX.sub("", label or "")


def reconcile(corr, run_json, ns_resolve_label=None):
    """Compare the capture's request counts against the run JSON's.

    A capture holding materially fewer requests than the drive reported is a
    tail that missed part of the pass, and its distribution is a subset
    presented as a whole. This is `assert_capture_live`'s discipline applied at
    the reading end: the drive proved the capture was recording when it
    STARTED; this proves it was still recording when it finished.

    `GET  /namespaces` and the namespace-resolution probe are the SAME HTTP
    request and cannot be told apart from the access log. `privilege_scan`
    records them under separate labels precisely so the run JSON accounts for
    the 2x; here they are folded back together and the fold is reported, not
    hidden.
    """
    expected = {}
    folded = set()
    for label, buckets in (run_json.get("status_counts") or {}).items():
        target = base_label(label)
        if target != label:
            folded.add(target)
        expected[target] = expected.get(target, 0) + sum(buckets.values())
    #: The drive counts one token call per identity; the run JSON's
    #: `requests` total includes them but `status_counts` does not.
    token_calls = run_json.get("authenticated", 0)
    if token_calls:
        expected["POST /oauth/tokens"] = token_calls

    observed = {label: len(ps) for label, ps in corr.by_label().items()}
    rows = []
    for label in sorted(set(expected) | set(observed)):
        exp, obs = expected.get(label, 0), observed.get(label, 0)
        rows.append(
            {
                "label": label,
                "expected": exp,
                "observed": obs,
                "delta": obs - exp,
                "folded": label in folded,
            }
        )
    total_exp = sum(expected.values())
    total_obs = sum(observed.values())
    return {
        "rows": rows,
        "expected_total": total_exp,
        "observed_total": total_obs,
        "delta_total": total_obs - total_exp,
        "clean": all(r["delta"] == 0 for r in rows),
        "folded_labels": sorted(folded),
    }


# ----------------------------------------------------------------------
# rendering
# ----------------------------------------------------------------------
def _fmt(n, places=2):
    return f"{n:.{places}f}"


def render_reconciliation(rec):
    lines = [
        "| op | run JSON | capture | delta |",
        "|---|---:|---:|---:|",
    ]
    for r in rec["rows"]:
        note = "  *(incl. harness resolve calls)*" if r["folded"] else ""
        lines.append(
            f"| `{r['label'].strip()}`{note} | {r['expected']} | {r['observed']} "
            f"| {r['delta']:+d} |"
        )
    lines.append(
        f"| **total** | **{rec['expected_total']}** | **{rec['observed_total']}** "
        f"| **{rec['delta_total']:+d}** |"
    )
    return "\n".join(lines)


def render_per_label(rows, table="grant_records"):
    lines = [
        f"| op | surface | requests | statuses | stmts | stmts/req | " f"{table}/req |",
        "|---|---|---:|---|---:|---:|---:|",
    ]
    for r in rows:
        statuses = " ".join(f"{k}×{v}" for k, v in sorted(r["statuses"].items()))
        lines.append(
            f"| `{r['label'].strip()}` | {r['surface']} | {r['requests']} | "
            f"{statuses} | {r['statements']} | {_fmt(r['per_request'])} | "
            f"{_fmt(r['table_per_request'])} |"
        )
    return "\n".join(lines)


def render_outcome_split(classes, diff, table="grant_records"):
    lines = [
        f"| request class | requests | stmts/req | min | median | max | "
        f"{table}/req |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for key in sorted(classes):
        c = classes[key]
        lines.append(
            f"| {key} | {c['requests']} | {_fmt(c['per_request'])} | {c['min']} "
            f"| {c['median']} | {c['max']} | {_fmt(c['table_per_request'])} |"
        )
    out = ["\n".join(lines), ""]
    if diff["only_permitted"]:
        out.append(
            f"Statement shapes on the permitted path only "
            f"({len(diff['only_permitted'])}):"
        )
        out += [f"  - `{s[:150]}`" for s in diff["only_permitted"][:10]]
    if diff["only_refused"]:
        out.append(
            f"Statement shapes on the refused path only "
            f"({len(diff['only_refused'])}):"
        )
        out += [f"  - `{s[:150]}`" for s in diff["only_refused"][:10]]
    if not diff["only_permitted"] and not diff["only_refused"]:
        out.append(
            "Both classes issue the SAME set of statement shapes: the "
            "authorization prelude does not short-circuit on refusal."
        )
    return "\n".join(out)


def render_statements(shapes, limit=40, width=160):
    items = sorted(shapes.values(), key=lambda s: -s.occurrences)[:limit]
    lines = [
        "| n | reqs | /req | table | verb | params | statement |",
        "|---:|---:|---:|---|---|---|---|",
    ]
    for s in items:
        params = "observed" if s.params_observed else "redacted"
        sql = s.sql if len(s.sql) <= width else s.sql[: width - 1] + "…"
        lines.append(
            f"| {s.occurrences} | {s.requests} | {_fmt(s.per_request)} | "
            f"{s.table or '—'} | {s.verb or '—'} | {params} | `{sql}` |"
        )
    return "\n".join(lines)


def render_integrity(corr):
    lines = [
        f"- access-log requests correlated: **{corr.access_records}**",
        f"- statements parsed: **{corr.statements}**",
    ]
    if corr.orphan_statements:
        lines.append(
            f"- **{corr.orphan_statements} statements had no access-log line** "
            f"(e.g. `{corr.orphan_request_ids[0] if corr.orphan_request_ids else '—'}`)"
            " — startup, health probes, or a request whose access-log line fell "
            "outside the capture. Excluded from every per-API figure below."
        )
    else:
        lines.append("- every parsed statement mapped to a request. No orphans.")
    if corr.unclassified_paths:
        lines.append(
            f"- **{len(corr.unclassified_paths)} path shapes did not match the "
            "op surface** — reported under their raw path, never silently "
            "dropped:"
        )
        for path, n in sorted(corr.unclassified_paths.items(), key=lambda kv: -kv[1])[
            :10
        ]:
            lines.append(f"  - `{path}` ×{n}")
    else:
        lines.append("- every request matched a known op template.")
    return "\n".join(lines)


# ----------------------------------------------------------------------
# coverage — the question "does this cover everything?" answered by the runner
# ----------------------------------------------------------------------
def canonical_path(path):
    """A path with every template parameter erased, for cross-spec comparison.

    `/api/catalog/v1/{catalog}/namespaces/{namespace}` and the spec's
    `/v1/{prefix}/namespaces/{namespace}` name the same operation and disagree
    on every parameter name. Comparing the raw strings would report the entire
    surface as uncovered; comparing shapes reports what is actually missing.
    """
    return re.sub(r"\{[^}]*\}", "{}", (path or "").rstrip("/")) or "/"


#: The diff is about the READ surface. `POST /oauth/tokens` is driven by every
#: profile and is not a GET, so comparing it against a GET/HEAD inventory would
#: report the harness's own control call as an unmatched path -- a permanent
#: false positive in the one number whose value is being zero.
READ_METHODS = ("GET", "HEAD")


def coverage_gap(templates, server_ops, methods=READ_METHODS):
    """Operations the server exposes that the harness does not drive.

    THE POINT OF THIS FUNCTION. Until now "does the suite cover all the GET
    APIs?" was a question someone had to think to ask -- and when it was asked,
    the answer was 13 of 29. Rendered in every report, it stops being a question
    and becomes a number that is either zero or visibly not.

    `server_ops` must come from the RUNNING server's own document. A list
    transcribed from a spec file is a hypothesis about the deployment, which is
    the mistake the 25-privilege retraction is a monument to -- and it cannot
    see a feature-flagged endpoint that is compiled in but disabled.

    Args:
        templates: `OpTemplate`s the harness drives.
        server_ops: iterable of (method, full_path) the server exposes.
        methods: which HTTP methods to compare. Defaults to the read surface;
            pass None to compare every method.

    Returns:
        {"missing": [...], "extra": [...], "covered": [...], "clean": bool}
    """
    allowed = {m.upper() for m in methods} if methods else None
    ours = {}
    for t in templates:
        m = t.method.upper()
        if allowed and m not in allowed:
            continue
        ours[(m, canonical_path(t.template))] = t.label
    theirs = {}
    for method, path in server_ops:
        m = method.upper()
        if allowed and m not in allowed:
            continue
        theirs[(m, canonical_path(path))] = path

    missing = sorted(f"{m} {p}" for (m, p) in set(theirs) - set(ours))
    extra = sorted(f"{ours[(m, p)].strip()}" for (m, p) in set(ours) - set(theirs))
    covered = sorted(f"{ours[(m, p)].strip()}" for (m, p) in set(ours) & set(theirs))
    return {
        "missing": missing,
        "extra": extra,
        "covered": covered,
        "clean": not missing,
    }


def render_coverage(gap, total_server=None):
    if gap["clean"] and not gap["extra"]:
        return (
            f"- **coverage: complete** — every GET/HEAD the server exposes "
            f"({len(gap['covered'])}) is driven by this suite."
        )
    lines = []
    n_server = (
        total_server
        if total_server is not None
        else (len(gap["covered"]) + len(gap["missing"]))
    )
    lines.append(
        f"- **coverage: {len(gap['covered'])} of {n_server}** GET/HEAD "
        f"operations the server exposes are driven by this suite."
    )
    if gap["missing"]:
        lines.append(
            f"- **{len(gap['missing'])} operations exist on the server and are "
            "NOT driven.** They are absent from every figure in this report:"
        )
        lines += [f"  - `{m}`" for m in gap["missing"]]
    if gap["extra"]:
        lines.append(
            f"- **{len(gap['extra'])} operations are driven but not found in "
            "the server's document** — a harness path that no longer matches "
            "the deployment, or a document that does not list everything:"
        )
        lines += [f"  - `{e}`" for e in gap["extra"]]
    return "\n".join(lines)


# ----------------------------------------------------------------------
# the captured API inventory — evidence, where the spec is only a claim
# ----------------------------------------------------------------------
#: Which service base a `doc-api-sql-matrix` label belongs to. The report
#: records paths RELATIVE to the service (`/v1/catalogs` and
#: `/v1/{cat}/namespaces` both start `/v1/`), so the label prefix is the only
#: thing that says which service answered -- and without it the two collapse
#: onto each other.
MATRIX_BASES = {
    "mgmt": "/api/management",
    "iceberg": "/api/catalog",
    "polaris": "/api/catalog",
}

_MATRIX_BLOCK = re.compile(
    r"^### `(?P<api>[^`]+)`\n\n- `(?P<method>[A-Z]+) (?P<path>[^`]+)` "
    r"→ \*\*(?P<status>\d+)\*\*",
    re.M,
)


def parse_api_matrix(text, read_only=True):
    """Operations a previous run actually ISSUED, from a `doc-api-sql-matrix`.

    THIS IS EVIDENCE, AND IT IS THE STRONGEST KIND AVAILABLE HERE. Every entry
    is an operation that was called against THIS cluster and answered. A spec
    file cannot say that -- it describes a version, and the endpoints it
    describes may be feature-flagged off in the running build.

    AND IT IS A LOWER BOUND, WHICH MATTERS MORE THAN THE STRENGTH DOES. A
    call log proves existence for what was called and says NOTHING about what
    was not. It can never answer "is anything missing", because an operation
    nobody invoked leaves no trace to find. So a coverage claim built only on
    this is circular: the harness is judged complete against a record of what
    a harness once did.

    Hence `coverage_from_evidence`, which keeps the two apart: observed
    operations the suite does not drive are a CONFIRMED gap; spec operations
    neither observed nor driven are UNVERIFIED and stay that way until
    something calls them.

    Args:
        text: the Markdown of a `doc-api-sql-matrix-*.md` report.
        read_only: keep only GET and HEAD.

    Returns:
        list of (method, full_path, api_label, status), variants like
        `load_table[missing]` folded into their base operation.
    """
    out = []
    seen = set()
    for m in _MATRIX_BLOCK.finditer(text):
        api = m.group("api")
        if api == "preflight":
            continue
        #: `load_table[missing]` and `load_table[snapshots=refs]` are the SAME
        #: operation exercised differently. Counting them as separate entries
        #: would inflate the inventory and make coverage look worse than it is.
        base_api = api.split("[", 1)[0]
        method = m.group("method").upper()
        if read_only and method not in READ_METHODS:
            continue
        path = m.group("path").split("?", 1)[0]
        if "..." in path:
            #: The report abbreviates a long path in a variant heading. The
            #: base operation is present separately, so drop it rather than
            #: guess what the ellipsis stood for.
            continue
        prefix = base_api.split(".", 1)[0]
        full = MATRIX_BASES.get(prefix, "") + path
        key = (method, canonical_path(full))
        if key in seen:
            continue
        seen.add(key)
        out.append((method, full, base_api, int(m.group("status"))))
    return out


def coverage_from_evidence(templates, observed, candidates=(), methods=READ_METHODS):
    """Three-way coverage: confirmed gaps, unverified candidates, and the rest.

    `observed` comes from a real capture and carries the weight. `candidates`
    come from a spec and carry a question mark. Merging them into one number
    would let a transcribed endpoint that this build does not serve be counted
    as a coverage failure -- and let a genuinely missing one hide behind the
    same asterisk.

    Returns:
        driven_verified   -- harness ops a previous run confirmed exist here
        driven_unverified -- harness ops nothing has ever called; may or may
                             not exist on this build
        observed_not_driven -- CONFIRMED gap: the cluster served it, the
                             harness does not drive it
        candidate_not_driven -- spec says it exists, nothing confirms it, the
                             harness does not drive it
    """
    allowed = {m.upper() for m in methods} if methods else None

    def keyset(pairs):
        out = {}
        for entry in pairs:
            method, path = entry[0], entry[1]
            m = method.upper()
            if allowed and m not in allowed:
                continue
            out[(m, canonical_path(path))] = path
        return out

    ours = {}
    for t in templates:
        m = t.method.upper()
        if allowed and m not in allowed:
            continue
        ours[(m, canonical_path(t.template))] = t.label

    obs = keyset(observed)
    cand = keyset(candidates)

    driven_verified = sorted(ours[k].strip() for k in set(ours) & set(obs))
    driven_unverified = sorted(ours[k].strip() for k in set(ours) - set(obs))
    observed_not_driven = sorted(
        f"{m} {obs[(m, p)]}" for (m, p) in set(obs) - set(ours)
    )
    candidate_not_driven = sorted(
        f"{m} {cand[(m, p)]}" for (m, p) in (set(cand) - set(ours) - set(obs))
    )
    return {
        "driven_verified": driven_verified,
        "driven_unverified": driven_unverified,
        "observed_not_driven": observed_not_driven,
        "candidate_not_driven": candidate_not_driven,
        "observed_total": len(obs),
        "driven_total": len(ours),
        #: Clean means no CONFIRMED gap. It deliberately does not require the
        #: candidate list to be empty: an unverified spec endpoint is a thing
        #: to go and check, not a defect in the suite.
        "clean": not observed_not_driven,
    }


def render_evidence_coverage(cov, source=""):
    L = []
    a = L.append
    a(
        f"- driven: **{cov['driven_total']}** operations — "
        f"**{len(cov['driven_verified'])} confirmed** against a previous live "
        f"run{f' ({source})' if source else ''}, "
        f"{len(cov['driven_unverified'])} never yet called on this cluster."
    )
    if cov["observed_not_driven"]:
        a(
            f"- **{len(cov['observed_not_driven'])} operations this cluster has "
            "SERVED are not driven by this suite.** A confirmed gap — the "
            "cluster answered them, so they exist:"
        )
        L += [f"  - `{o}`" for o in cov["observed_not_driven"]]
    else:
        a(
            f"- **no confirmed gap**: every one of the {cov['observed_total']} "
            "GET/HEAD operations a previous run observed is driven here."
        )
    if cov["driven_unverified"]:
        a(
            f"- {len(cov['driven_unverified'])} driven operations are "
            "**unverified** — no prior run has called them, so whether this "
            "build serves them is open until the probe answers:"
        )
        L += [f"  - `{u}`" for u in cov["driven_unverified"]]
    if cov["candidate_not_driven"]:
        a(
            f"- {len(cov['candidate_not_driven'])} spec operations are neither "
            "observed nor driven:"
        )
        L += [f"  - `{c}`" for c in cov["candidate_not_driven"]]
    a("")
    a(
        "A captured inventory proves an operation EXISTS; it cannot prove one "
        "is absent, because an operation nobody called leaves no trace. "
        '"Confirmed gap" is therefore a floor on what is missing, never a '
        "ceiling."
    )
    return "\n".join(L)
