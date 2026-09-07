"""
vlogs.py
========
VictoriaLogs query client, for the Polaris API -> log-coverage notebook.

WHY A NEW MODULE AND NOT A FUNCTION IN polaris_test_utils
---------------------------------------------------------
`polaris_test_utils` already has `search_logs`, `search_404_errors`,
`search_all_errors` and a dozen siblings. **Every one of them talks to
OpenSearch**, which is the OTHER pipeline: a Fluent Bit DaemonSet shipping
container stdout to an OpenSearch running in Docker outside the cluster.

This module talks to VictoriaLogs, which is fed by a SECOND, independent Fluent
Bit -- the `fb-polaris-shipper` Deployment tailing the Polaris log PVC, with the
access-log field extraction and the retention policy that `log-coverage/`
exists to test. The two sinks hold different records under different rules. A
line present in OpenSearch and absent from VictoriaLogs is the DaemonSet, not a
finding.

    Polaris (Quarkus JSON) -> /deployments/logs/polaris.log  (PVC)
      -> fb-polaris-shipper -> [access-log parse] -> [polaris_noise_filter]
      -> VictoriaLogs /insert/jsonline   <- THIS MODULE READS THAT

OFFLINE-TESTABLE
----------------
Every parser takes text and returns records, so `test_vlogs.py` runs with no
cluster, matching `api_trace.py`'s design. Only `VLogs.query` and
`fluentbit_metrics` touch the network.

NO AUTH, DELIBERATELY NOT WORKED AROUND
---------------------------------------
VictoriaLogs single has no authentication and 9428 is a `LoadBalancer`
(`local-k8s` `.memory/active-issues.md` #7 -- unauthenticated ingest AND
query). There is no credential to configure here. That is a finding the
notebook reports, not a gap this module papers over.
"""

import json
import time as _time
from datetime import datetime, timedelta, timezone

import requests

#: The logger every access-log record carries. Anything else is an application
#: log line, which `polaris_noise_filter` rule 2 passes through untouched.
ACCESS_LOGGER = "io.quarkus.http.access-log"

DEFAULT_TIMEOUT = 15


# ----------------------------------------------------------------------
# LogsQL construction
# ----------------------------------------------------------------------
def quote(value):
    """A LogsQL double-quoted string literal.

    Values here are principal names, request ids and API paths -- a path
    carries `/` and may carry `?`, both of which are LogsQL operators unquoted.
    Quote everything rather than deciding per value; a filter that silently
    parses as something else returns 0 records and reads as "the pipeline
    dropped it", which is the one wrong answer this whole notebook must not
    produce.
    """
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'


def field_eq(field, value):
    """`"mdc.requestId":"nb-1788-3"` -- an exact-phrase filter on one field.

    The field name is quoted too: `mdc.requestId` and `mdc.realmId` contain a
    dot, which LogsQL reads as part of a field path.
    """
    return f"{quote(field)}:{quote(value)}"


def and_(*terms):
    """Join non-empty filters with AND, parenthesised."""
    parts = [t for t in terms if t]
    return " AND ".join(f"({t})" for t in parts)


def app_polaris():
    """The stream selector. `_stream_fields=app,level`, so this is the only
    real stream narrowing available -- every other field is searchable but not
    a stream selector (`local-k8s` source plan section 6)."""
    return 'app:"polaris"'


#: The scheduled flush report lands on its OWN stream. `_stream_fields=app,level`
#: and the filter sets `app=polaris-shipper-report`, `level=REPORT`, so
#: `app:polaris` queries are unaffected by it and vice versa.
REPORT_APP = "polaris-shipper-report"
REPORT_TAG = "polaris.report"


def app_report():
    """The report stream selector."""
    return f'app:{quote(REPORT_APP)}'


def tick_leak():
    """Records still carrying the raw tick.

    Must be ZERO. The `dummy` INPUT ticks every 30s and the filter is supposed
    to swallow every tick inside the current window (`return -1`) and replace
    the boundary one with the report array. A non-zero count here means raw
    ticks are reaching VictoriaLogs, which would be 2,880 junk records a day.
    """
    return f'{quote("tick")}:{quote(REPORT_TAG)}'


# ----------------------------------------------------------------------
# parsing
# ----------------------------------------------------------------------
def parse_ndjson(text):
    """Newline-delimited JSON -> list of dicts, skipping blank lines.

    A malformed line is RAISED, not skipped. VictoriaLogs does not emit
    half-written JSON; a parse failure means the response is something else
    (an HTML error page from a port-forward that died is the usual one), and
    swallowing it would report "0 records stored" for a query that never ran.
    """
    out = []
    for i, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"VictoriaLogs response line {i} is not JSON: {line[:200]!r}"
            ) from exc
    return out


def dedup_replayed(records):
    """Collapse records the shipper posted twice, keeping the first of each.

    NOT a tidy-up. The shipper's tail offset DB lives on an `emptyDir`
    (`local-k8s` roadmap step 2), so `helm upgrade` replaces the pod, the DB is
    empty, `Read_from_Head true` re-reads the whole file and VictoriaLogs does
    not deduplicate on ingest. **Records can legitimately appear twice**, and
    counting them twice would turn a shipper upgrade into a false finding about
    the retention policy.

    THE KEY IS THE RECORD, NOT THE REQUEST. An earlier version of this keyed on
    `mdc.requestId` and was badly wrong: one API call produces MANY records that
    share a request id -- its access-log line plus every application log line
    the request emitted (measured 2026-09-04: 15 records for a single
    `list_catalogs`). Keying on the request id collapsed 2,049 records to 122,
    capped every "stored" count at 1, reported 1,927 phantom duplicates, and
    made `app_lines` zero for every row. `sequence` is the JBoss log sequence
    number and is unique per record -- it is kept in the pipeline precisely so a
    gap in ingestion is visible -- and `hostName` disambiguates it if Polaris
    ever runs more than one replica.

    Records with neither `sequence` nor a usable `_time`/`_msg` pair are all
    kept: there is nothing to key on, and dropping them would be guessing.
    """
    seen, out = set(), []
    for r in records:
        seq, host = r.get("sequence"), r.get("hostName")
        if seq not in (None, ""):
            key = ("seq", host, seq)
        elif r.get("_time") and r.get("_msg"):
            key = ("msg", r.get("_time"), r.get("_msg"))
        else:
            out.append(r)
            continue
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


#: Kept so an older notebook or script does not fail on import; the name is a
#: trap and nothing new should use it.
dedup_by_request_id = dedup_replayed


def is_access_log(record):
    return record.get("loggerName") == ACCESS_LOGGER


def status_of(record):
    """`http_status` as an int, or None.

    Tolerates both types ON PURPOSE. `fb-values.yaml` sets `type_int_key
    http_status response_size` so VictoriaLogs stores numbers, but the sample
    record in the source plan -- marked [verified] -- carries strings. Both
    cannot be true of one deployment and cell 0 of the notebook settles which,
    but nothing in this module should fall over while that is open.
    """
    v = record.get("http_status")
    if v is None or v == "":
        return None
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def numeric_status_filters_work(client, since="24h", end=None, scope=None):
    """Does `http_status:>=400` actually match anything? Returns (bool, detail).

    THE JSON TYPE CANNOT ANSWER THIS, and an earlier version of this module
    tried. VictoriaLogs returns every field value as a JSON string on
    `/select/logsql/query` regardless of how it indexed it, so a type check on a
    returned record always says "string" and says nothing at all about whether
    `type_int_key` took effect. The 2026-09-04 run reported `http_status stored
    as string` on that basis and it was meaningless.

    The question that matters is the operational one -- do numeric LogsQL
    filters find the errors -- so ask it directly: compare a numeric range
    filter against an exact-match filter over the same window. If the range
    finds nothing where the exact match finds plenty, `type_int_key` is not in
    effect and every status-range query in the spec's recipes is silently empty.

    SAY WHAT WAS COUNTED. The default window is the retention slice this
    instrument check needs in order to find any 4xx at all, and it is NOT the
    run: run 1 of v3 printed `http_status:"404" -> 138` in a *Validity* block
    beside a run that made 23 of them, and the number reconciled with nothing
    on the page. `scope` names the window inside the returned detail so the
    instrument check and the run's own count cannot be read as each other.
    Pass the run's `start`/`end` and `scope="this run"` for the second.
    """
    scope = scope or (
        f"cluster-wide, last {since}" if isinstance(since, str) else "as given"
    )
    kw = {"start": since, "limit": 1000}
    if end is not None:
        kw["end"] = end
    exact = client.count(and_(app_polaris(), field_eq("http_status", "404")), **kw)
    ranged = client.count(and_(app_polaris(), "http_status:>=400"), **kw)
    if exact == 0 and ranged == 0:
        return None, f"no 4xx to test with [{scope}]"
    ok = ranged > 0
    detail = f'http_status:>=400 -> {ranged};  http_status:"404" -> {exact}'
    return ok, f"{detail}  [{scope}]"


def parse_fluentbit_metrics(text):
    """Fluent Bit `/api/v1/metrics` -> {plugin_name: {metric: value}}.

    Accepts BOTH shapes the HTTP server serves: the native JSON document, and
    the Prometheus exposition text at `/api/v1/metrics/prometheus`. Which one a
    build serves at which path has moved between Fluent Bit versions, and the
    number wanted here -- `fluentbit_filter_drop_records_total`, the source
    plan's only measure of total suppression -- is in both.
    """
    text = (text or "").strip()
    if not text:
        return {}
    if text.startswith("{"):
        doc = json.loads(text)
        out = {}
        for name, metrics in (doc.get("filter") or {}).items():
            out[name] = dict(metrics)
        return out
    out = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        head, _, value = line.rpartition(" ")
        if not head:
            continue
        metric, _, labels = head.partition("{")
        if not metric.startswith("fluentbit_filter_"):
            continue
        name = "unknown"
        for kv in labels.rstrip("}").split(","):
            k, _, v = kv.partition("=")
            if k.strip() == "name":
                name = v.strip().strip('"')
        short = metric[len("fluentbit_filter_") :].removesuffix("_total")
        try:
            out.setdefault(name, {})[short] = float(value)
        except ValueError:
            continue
    return out


def drop_records_total(metrics):
    """Sum `drop_records` across every filter plugin.

    Summed, not per-plugin, because the number that answers "how much is the
    policy suppressing" is the total -- and because plugin names (`lua.1`,
    `lua.2`) are positional and change when a filter is added.
    """
    return sum(m.get("drop_records", 0) for m in metrics.values())


def drop_records_by_plugin(metrics):
    """`{plugin: drop_records}` -- which filter, not just how many.

    The total is the number the source plan asks for; the breakdown is what
    tells you whether it can be believed. A sum that is wrong is silent; a
    breakdown naming `lua.0: 7154980971680` is not.
    """
    return {name: m.get("drop_records", 0) for name, m in (metrics or {}).items()}


#: No filter on a laptop has dropped a billion records. The first time this
#: counter was ever read (run `1788745242`, the metrics port-forward having been
#: down for both earlier runs) it returned **7,154,980,971,680** -- almost
#: exactly four times the epoch in MILLISECONDS, so the field being summed was a
#: timestamp and not a counter, in four plugins. The "delta" computed from two
#: such readings was 52,000 and was reported as suppression.
IMPLAUSIBLE_DROP_TOTAL = 10**9


def drop_records_delta(before, after, cap=IMPLAUSIBLE_DROP_TOTAL):
    """`(delta, note)` for `fluentbit_filter_drop_records_total` across a run.

    Returns `delta=None` and a note naming the readings when either side cannot
    be a record count. **A number that reconciles with nothing on the page is
    worse than a missing one**: this notebook's whole subject is a report whose
    figures can be checked against each other, and an unchecked counter printed
    beside them borrows their credibility.

    The cap is deliberately crude. It is not trying to validate the metric; it
    is trying to make an unparseable one impossible to quote.
    """
    lo, hi = drop_records_total(before or {}), drop_records_total(after or {})
    for label, value in (("before", lo), ("after", hi)):
        if abs(value) >= cap:
            return None, (
                f"UNREADABLE: the {label} reading is {value:,.0f} across "
                f"{len(after or before or {})} filter(s), which cannot be a record "
                "count -- the metrics document's shape is not the one "
                "parse_fluentbit_metrics expects. Do not quote a delta from it."
            )
    return hi - lo, None


# ----------------------------------------------------------------------
# client
# ----------------------------------------------------------------------
class PollResult:
    """What a poll saw, and how long it waited to see it.

    `waited_s` is reported rather than discarded: ingest is asynchronous, and
    "0 records after 30s" and "0 records after 0.4s" are different claims.
    """

    def __init__(self, records, waited_s, satisfied, expected):
        self.records = records
        self.waited_s = waited_s
        self.satisfied = satisfied
        self.expected = expected

    def __len__(self):
        return len(self.records)

    def __repr__(self):
        mark = "ok" if self.satisfied else "TIMEOUT"
        return (
            f"<PollResult {mark} {len(self.records)}/{self.expected} records "
            f"after {self.waited_s:.1f}s>"
        )


class VLogs:
    """Query one VictoriaLogs instance.

    Args:
        base_url: e.g. http://localhost:9428 (a port-forward, or the
            LoadBalancer directly -- it has no auth either way).
    """

    def __init__(self, base_url, timeout=DEFAULT_TIMEOUT, session=None):
        self.base_url = (base_url or "").rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()

    # -- low level -----------------------------------------------------
    def query(self, logsql, start=None, end=None, limit=1000):
        """POST /select/logsql/query -> list of record dicts.

        `start`/`end` accept a datetime, a LogsQL duration string ("5m") or
        None. A run's window should always be passed: without it the query
        scans the full 30-day retention, which on this laptop is slow enough to
        read as a hang.
        """
        data = {"query": logsql, "limit": str(limit)}
        if start is not None:
            data["start"] = _as_time(start)
        if end is not None:
            data["end"] = _as_time(end)
        r = self.session.post(
            f"{self.base_url}/select/logsql/query", data=data, timeout=self.timeout
        )
        r.raise_for_status()
        return parse_ndjson(r.text)

    def count(self, logsql, **kw):
        return len(self.query(logsql, **kw))

    def ping(self):
        """Is VictoriaLogs answering? Returns (ok, detail).

        Never raises: cell 0 wants to print a diagnosis and abort with a
        message, not a traceback with a port number buried in it.
        """
        try:
            r = self.session.get(f"{self.base_url}/select/vmui", timeout=5)
            return (r.status_code < 500, f"HTTP {r.status_code}")
        except Exception as exc:  # noqa: BLE001
            return (False, f"{type(exc).__name__}: {exc}")

    # -- polling -------------------------------------------------------
    def poll_until(
        self, logsql, expect_at_least=1, timeout=30.0, interval=1.0, **kw
    ):
        """Poll until `expect_at_least` records match, or the timeout expires.

        Ingest is asynchronous. The source plan's rule is **poll, do not
        sleep-and-hope**: a fixed `sleep(5)` either wastes four seconds or
        reports a drop that was merely late, and there is no way afterwards to
        tell which happened.

        Returns a `PollResult` either way -- a timeout is DATA here. Half the
        assertions in this notebook expect zero records, and for those the
        timeout IS the measurement.
        """
        deadline = _time.monotonic() + timeout
        started = _time.monotonic()
        records = []
        while True:
            records = self.query(logsql, **kw)
            if len(records) >= expect_at_least:
                return PollResult(
                    records, _time.monotonic() - started, True, expect_at_least
                )
            if _time.monotonic() >= deadline:
                return PollResult(
                    records, _time.monotonic() - started, False, expect_at_least
                )
            _time.sleep(interval)

    def settle(self, logsql, quiet_for=3.0, timeout=30.0, interval=1.0, **kw):
        """Poll until the match count stops changing for `quiet_for` seconds.

        The companion to `poll_until` for the assertions that expect a SMALL
        number rather than at least one: "expect exactly 1 stored" cannot be
        satisfied by an early return, because a second record arriving a moment
        later is exactly the failure being tested for.
        """
        deadline = _time.monotonic() + timeout
        started = _time.monotonic()
        last, stable_since, records = None, None, []
        while True:
            records = self.query(logsql, **kw)
            now = _time.monotonic()
            if len(records) != last:
                last, stable_since = len(records), now
            elif now - stable_since >= quiet_for:
                return PollResult(records, now - started, True, last)
            if now >= deadline:
                return PollResult(records, now - started, False, last)
            _time.sleep(interval)

    # -- the queries this notebook actually asks ------------------------
    def for_request_id(self, request_id, **kw):
        """Every record -- access-log AND application -- for one API call.

        This is the join the whole correlation design rests on, and whether it
        works is cell 1's question, not an assumption.
        """
        return self.query(
            and_(app_polaris(), field_eq("mdc.requestId", request_id)), **kw
        )

    def for_principal(self, principal, **kw):
        """Every record for one run, via `%u` in the access log.

        The FALLBACK correlation key. Coarser than the request id -- per run,
        not per call -- but it survives Polaris ignoring a client-supplied id,
        and it needs no code change to use.
        """
        return self.query(
            and_(app_polaris(), field_eq("user_principal_name", principal)), **kw
        )

    def for_path(self, api_path, method=None, **kw):
        terms = [app_polaris(), field_eq("api_path", api_path)]
        if method:
            terms.append(field_eq("http_method", method))
        return self.query(and_(*terms), **kw)

    def levels(self, level, since="10m", **kw):
        """Every WARN or ERROR in the window.

        Source plan section 8.1: the exact WARN messages are what lets the
        "Deprecated Config" exclusion be written NARROWLY. A broad pattern
        there silently discards real errors, which is the failure mode the
        whole exercise is against.
        """
        kw.setdefault("start", since)
        return self.query(and_(app_polaris(), field_eq("level", level)), **kw)

    def with_exception(self, since="10m", **kw):
        """Records carrying a Quarkus `exception` object.

        Source plan section 5 rule 1: no filter touches it, but no record with
        one has ever been observed. If stack traces are being dropped or
        truncated, that is the single most valuable thing this notebook finds.
        """
        kw.setdefault("start", since)
        return self.query(and_(app_polaris(), "_msg:*exception* OR exception:*"), **kw)

    # -- the scheduled flush report ------------------------------------
    def reports(self, report_type=None, window_start=None, since="2h", **kw):
        """Report rows, optionally narrowed to one type and/or one window.

        Report records carry NO `mdc.requestId` -- they are per-window
        aggregates, so the correlation machinery the rest of this module is
        built on does not apply to them and must not be forced onto them. They
        join on `window_start` (or on `report_seq`, which is unique per
        `hostname`).
        """
        terms = [app_report()]
        if report_type:
            terms.append(field_eq("report_type", report_type))
        if window_start:
            terms.append(field_eq("window_start", window_start))
        kw.setdefault("start", since)
        return self.query(and_(*terms), **kw)

    def report_window(self, window_start, **kw):
        """Every row of ONE window, ready for `log_coverage.check_invariants`."""
        return self.reports(window_start=window_start, **kw)

    def report_types(self, window_start=None, **kw):
        """`{report_type: count}` -- THE GATE.

        The filter returns an ARRAY of records for one tick. If Fluent Bit
        splits it, three types come back. If it does not, one record comes back
        carrying numeric-keyed fields, the schema is not what the tests target,
        and the fix is in `local-k8s/logging/fb-values.yaml` rather than here.
        """
        rows = self.reports(window_start=window_start, **kw)
        out = {}
        for r in rows:
            key = r.get("report_type", "(none)")
            out[key] = out.get(key, 0) + 1
        return out

    def latest_summary(self, with_traffic=False, since="2h", **kw):
        """The newest summary row, or the newest that saw traffic.

        `with_traffic` exists because a window with `access_seen: 0` proves
        nothing about the array split -- there are no resource or principal
        rows to split INTO. Asking for a window with traffic is the difference
        between an inconclusive gate and an answered one.
        """
        rows = self.reports(report_type="summary", since=since, **kw)
        rows.sort(key=lambda r: str(r.get("window_start", "")), reverse=True)
        empty = ("0", "", "None")
        for r in rows:
            if not with_traffic or str(r.get("access_seen", "0")) not in empty:
                return r
        return None

    def seconds_to_boundary(self, window_seconds, lag=0.0, now=None):
        """How long until the next window boundary, plus ingest lag.

        Never sleeps -- the caller decides whether to wait, print, or come back
        later. `window_seconds` must come from a report record or the running
        ConfigMap, NEVER a literal: the whole point is that the same notebook
        works at 1800 and at 30.
        """
        window_seconds = int(window_seconds)
        now = _time.time() if now is None else float(now)
        return (window_seconds - (now % window_seconds)) + float(lag)

    def wait_for_boundary(self, window_seconds, lag=5.0, now=None, sleep=True):
        """Wait for the next boundary. Returns the window_start it just closed.

        At small `window_seconds` this is seconds; at the deployed 1800 it is
        up to half an hour, so callers that cannot block should use
        `seconds_to_boundary` and come back instead.
        """
        window_seconds = int(window_seconds)
        now = _time.time() if now is None else float(now)
        wait = self.seconds_to_boundary(window_seconds, lag, now)
        if sleep:
            _time.sleep(max(0.0, wait))
        closed = int((now + wait) // window_seconds) * window_seconds - window_seconds
        return _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime(closed))


def fluentbit_metrics(base_url, timeout=10, session=None):
    """Read the shipper's metrics. Returns (metrics, error_or_None).

    NEVER raises. The metrics port needs its own port-forward and is the most
    likely thing to be missing on a given day; the source plan wants the
    `fluentbit_filter_drop_records_total` delta, but a missing delta must
    degrade to a reported gap, not an aborted run that already drove 43 APIs.
    """
    sess = session or requests
    for path in ("/api/v1/metrics/prometheus", "/api/v1/metrics"):
        try:
            r = sess.get(f"{base_url.rstrip('/')}{path}", timeout=timeout)
            if r.status_code == 200 and r.text.strip():
                parsed = parse_fluentbit_metrics(r.text)
                if parsed:
                    return parsed, None
        except Exception as exc:  # noqa: BLE001
            last = f"{type(exc).__name__}: {exc}"
            continue
        last = f"HTTP {r.status_code}"
    return {}, f"fluent-bit metrics unreachable at {base_url} ({last})"


def _as_time(v):
    if isinstance(v, datetime):
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    if isinstance(v, timedelta):
        return f"-{int(v.total_seconds())}s"
    return str(v)
