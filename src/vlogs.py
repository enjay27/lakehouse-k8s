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


def dedup_by_request_id(records):
    """Collapse records that share an `mdc.requestId`, keeping the first.

    NOT a tidy-up. The shipper's tail offset DB lives on an `emptyDir`
    (`local-k8s` roadmap step 2), so `helm upgrade` replaces the pod, the DB is
    empty, `Read_from_Head true` re-reads the whole file and VictoriaLogs does
    not deduplicate on ingest. **Records can legitimately appear twice**, and
    counting them twice would turn a shipper upgrade into a false finding about
    the retention policy.

    Records with no request id are all kept -- there is nothing to join on and
    dropping them would be guessing.
    """
    seen, out = set(), []
    for r in records:
        rid = r.get("mdc.requestId")
        if not rid:
            out.append(r)
            continue
        if rid in seen:
            continue
        seen.add(rid)
        out.append(r)
    return out


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


def status_field_is_numeric(record):
    """Is `http_status` stored as a number or a string in THIS deployment?

    Returns "number", "string" or None. Cell 0 reports it, and every LogsQL
    filter that compares a status is written against the answer.
    """
    v = record.get("http_status")
    if v is None:
        return None
    numeric = isinstance(v, (int, float)) and not isinstance(v, bool)
    return "number" if numeric else "string"


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
