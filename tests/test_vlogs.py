"""Offline tests for `src/vlogs.py` — no cluster, no network.

Every parser here takes text and returns records, so the whole module is
testable against fixtures. Only `VLogs.query` and `fluentbit_metrics` touch a
socket and neither is exercised here.
"""

import pathlib
import sys

import pytest

import vlogs  # noqa: E402


# ---------------------------------------------------------------- LogsQL
def test_quote_escapes_the_characters_that_would_reparse():
    assert vlogs.quote("plain") == '"plain"'
    assert vlogs.quote('say "hi"') == '"say \\"hi\\""'


def test_field_eq_quotes_the_field_name_too():
    #: `mdc.requestId` contains a dot, which LogsQL reads as a field path.
    got = vlogs.field_eq("mdc.requestId", "nb-1-002-x")
    assert got == '"mdc.requestId":"nb-1-002-x"'


def test_and_skips_empty_terms():
    assert vlogs.and_("a:1", None, "", "b:2") == "(a:1) AND (b:2)"


def test_a_path_with_a_query_string_survives_quoting():
    #: An unquoted `?` is a LogsQL wildcard. A filter that quietly became a
    #: prefix match would return the wrong count, and the wrong count here
    #: reads as "the pipeline dropped it" -- the one wrong answer this suite
    #: must not produce.
    path = "/api/catalog/v1/c/namespaces/ns/tables/t?snapshots=all"
    q = vlogs.field_eq("api_path", path)
    assert q.endswith('tables/t?snapshots=all"')


# ---------------------------------------------------------------- ndjson
def test_parse_ndjson_skips_blank_lines():
    assert vlogs.parse_ndjson('{"a":1}\n\n{"a":2}\n') == [{"a": 1}, {"a": 2}]


def test_parse_ndjson_raises_on_garbage_rather_than_reporting_zero_records():
    #: A dead port-forward answers with HTML. Swallowing it would report "0
    #: records stored" for a query that never ran.
    with pytest.raises(ValueError, match="not JSON"):
        vlogs.parse_ndjson("<html>502 Bad Gateway</html>")


# ------------------------------------------------------------ dedup/read
def test_dedup_replayed_keys_on_the_record_not_the_request():
    #: THE REGRESSION. One API call emits many records sharing a request id --
    #: its access-log line plus every application line it produced. Keying on
    #: the request id collapsed 2,049 records to 122 on 2026-09-04, capped every
    #: "stored" count at 1 and reported 1,927 phantom duplicates.
    recs = [
        {"mdc.requestId": "a", "sequence": "1", "hostName": "p", "loggerName": "sql"},
        {"mdc.requestId": "a", "sequence": "2", "hostName": "p", "loggerName": "sql"},
        {
            "mdc.requestId": "a",
            "sequence": "3",
            "hostName": "p",
            "loggerName": vlogs.ACCESS_LOGGER,
        },
    ]
    assert len(vlogs.dedup_replayed(recs)) == 3


def test_dedup_replayed_collapses_a_shipper_replay():
    #: A replayed record is the SAME record posted twice -- same sequence, same
    #: host. That is what `Read_from_Head true` on a fresh tail DB produces.
    one = {"sequence": "4168", "hostName": "polaris-0", "_msg": "x"}
    assert len(vlogs.dedup_replayed([one, dict(one), dict(one)])) == 1


def test_dedup_replayed_falls_back_to_time_and_message():
    a = {"_time": "2026-09-04T01:00:00Z", "_msg": "same"}
    b = {"_time": "2026-09-04T01:00:00Z", "_msg": "different"}
    assert len(vlogs.dedup_replayed([a, dict(a), b])) == 2


def test_dedup_replayed_keeps_what_it_cannot_key():
    assert len(vlogs.dedup_replayed([{"n": 1}, {"n": 2}])) == 2


def test_status_of_reads_both_the_number_and_the_string_form():
    #: fb-values.yaml sets `type_int_key http_status`, but the source plan's
    #: [verified] sample record carries a string. Both cannot be true of one
    #: deployment; nothing here should fall over while that is open.
    assert vlogs.status_of({"http_status": 404}) == 404
    assert vlogs.status_of({"http_status": "404"}) == 404
    assert vlogs.status_of({"http_status": "404.0"}) == 404
    assert vlogs.status_of({}) is None


def test_numeric_status_filters_are_tested_by_QUERY_not_by_json_type():
    #: VictoriaLogs hands every field back as a JSON string whatever it indexed,
    #: so a type check on a returned record always says "string" and answers
    #: nothing -- the 2026-09-04 run reported exactly that and it meant nothing.
    #: Ask the operational question instead: does the range filter match?
    class C:
        def __init__(self, ranged, exact):
            self.ranged, self.exact = ranged, exact

        def count(self, q, **kw):
            return self.ranged if ">=400" in q else self.exact

    assert vlogs.numeric_status_filters_work(C(7, 3))[0] is True
    assert vlogs.numeric_status_filters_work(C(0, 3))[0] is False
    assert vlogs.numeric_status_filters_work(C(0, 0))[0] is None


def test_is_access_log_discriminates_on_the_logger():
    assert vlogs.is_access_log({"loggerName": vlogs.ACCESS_LOGGER})
    assert not vlogs.is_access_log({"loggerName": "org.apache.polaris.x"})


# ------------------------------------------------------- fluent-bit metrics
PROM = """\
# HELP fluentbit_filter_drop_records_total Fluentbit metrics.
fluentbit_filter_add_records_total{name="lua.1"} 0
fluentbit_filter_drop_records_total{name="lua.1"} 0
fluentbit_filter_drop_records_total{name="lua.2"} 1417
fluentbit_output_proc_records_total{name="http.0"} 88
"""

JSON_DOC = (
    '{"input":{"tail.0":{"records":100}},'
    '"filter":{"lua.1":{"drop_records":0,"add_records":0},'
    '"lua.2":{"drop_records":1417,"add_records":0}}}'
)


def test_prometheus_and_json_shapes_agree():
    a = vlogs.parse_fluentbit_metrics(PROM)
    b = vlogs.parse_fluentbit_metrics(JSON_DOC)
    assert vlogs.drop_records_total(a) == vlogs.drop_records_total(b) == 1417


def test_drop_total_sums_across_plugins_because_names_are_positional():
    #: `lua.1` / `lua.2` are positions, not identities: adding a filter
    #: renumbers them. The total is the number that keeps meaning something.
    m = vlogs.parse_fluentbit_metrics(PROM)
    assert set(m) == {"lua.1", "lua.2"}
    assert vlogs.drop_records_total(m) == 1417


def test_empty_metrics_are_empty_not_an_exception():
    assert vlogs.parse_fluentbit_metrics("") == {}


# ---------------------------------------------------------------- polling
class _FakeVLogs(vlogs.VLogs):
    def __init__(self, pages):
        super().__init__("http://unused")
        self._pages = list(pages)

    def query(self, logsql, **kw):
        return self._pages.pop(0) if self._pages else []


def test_poll_until_returns_as_soon_as_the_records_arrive():
    v = _FakeVLogs([[], [{"a": 1}]])
    r = v.poll_until("q", expect_at_least=1, timeout=5, interval=0)
    assert r.satisfied and len(r) == 1


def test_poll_until_returns_a_timeout_rather_than_raising():
    #: Half the assertions in the notebook expect ZERO records. For those the
    #: timeout is the measurement, not a failure.
    v = _FakeVLogs([[], [], []])
    r = v.poll_until("q", expect_at_least=1, timeout=0, interval=0)
    assert not r.satisfied and len(r) == 0


def test_settle_waits_out_a_late_arriving_second_record():
    #: "expect exactly 1 stored" cannot be answered by an early return: a
    #: second record arriving a moment later is the failure being tested for.
    v = _FakeVLogs([[{"a": 1}], [{"a": 1}, {"a": 2}], [{"a": 1}, {"a": 2}]])
    r = v.settle("q", quiet_for=0, timeout=5, interval=0)
    assert len(r) == 2


# ---------------------------------------------------- the flush report stream
class _RecordingVLogs(vlogs.VLogs):
    """Captures the LogsQL it would have sent, and replays canned rows."""

    def __init__(self, rows=()):
        super().__init__("http://vlogs.invalid")
        self.rows = list(rows)
        self.queries = []

    def query(self, logsql, **kw):
        self.queries.append((logsql, kw))
        return list(self.rows)


def _report_row(kind, window="2026-09-04T07:30:00Z", **kw):
    row = {
        "app": vlogs.REPORT_APP,
        "level": "REPORT",
        "report_type": kind,
        "window_start": window,
        "window_end": "2026-09-04T08:00:00Z",
        "window_seconds": "1800",
    }
    row.update(kw)
    return row


def test_the_report_lives_on_its_own_stream_so_app_polaris_is_unaffected():
    #: `_stream_fields=app,level`. If these two selectors overlapped, every
    #: existing `app:polaris` count in the notebook would silently gain the
    #: report rows.
    assert vlogs.app_report() != vlogs.app_polaris()
    assert "polaris-shipper-report" in vlogs.app_report()


def test_tick_leak_asks_for_the_raw_tick_and_must_return_nothing():
    #: 2,880 ticks a day reach the filter. If they were reaching VictoriaLogs
    #: instead of being swallowed, this query would be how you found out.
    assert vlogs.tick_leak() == '"tick":"polaris.report"'


def test_reports_narrows_by_type_and_window():
    V = _RecordingVLogs()
    V.reports(report_type="resource", window_start="2026-09-04T07:30:00Z")
    logsql, _ = V.queries[-1]
    assert "polaris-shipper-report" in logsql
    assert '"report_type":"resource"' in logsql
    assert '"window_start":"2026-09-04T07:30:00Z"' in logsql


def test_report_types_counts_the_split_which_is_the_whole_gate():
    #: Three types back means Fluent Bit split the filter's array return. One
    #: type back means it did not, the record carries numeric-keyed fields, and
    #: the schema the tests target does not exist.
    V = _RecordingVLogs(
        [
            _report_row("summary"),
            _report_row("resource"),
            _report_row("resource"),
            _report_row("principal"),
        ]
    )
    assert V.report_types() == {"summary": 1, "resource": 2, "principal": 1}


def test_latest_summary_can_insist_on_a_window_that_saw_traffic():
    #: A window with `access_seen: 0` has no resource or principal rows to
    #: split into, so it cannot answer the gate. Asking for one with traffic is
    #: the difference between inconclusive and answered -- exactly what the
    #: first live probe on 2026-09-04 ran into.
    quiet = _report_row("summary", window="2026-09-04T07:00:00Z", access_seen="0")
    busy = _report_row("summary", window="2026-09-04T06:30:00Z", access_seen="12")
    V = _RecordingVLogs([quiet, busy])
    assert V.latest_summary()["window_start"] == "2026-09-04T07:00:00Z"
    assert V.latest_summary(with_traffic=True)["window_start"] == "2026-09-04T06:30:00Z"


def test_latest_summary_with_traffic_returns_none_rather_than_a_quiet_window():
    V = _RecordingVLogs([_report_row("summary", access_seen="0")])
    assert V.latest_summary(with_traffic=True) is None


def test_seconds_to_boundary_is_derived_never_hardcoded():
    V = _RecordingVLogs()
    #: 07:33:45 with 1800s windows -> 08:00:00 is 1575s away.
    assert V.seconds_to_boundary(1800, now=1788507225) == 1575.0
    #: the same instant at 30s windows -> 15s. The notebook must work at both.
    assert V.seconds_to_boundary(30, now=1788507225) == 15.0
    assert V.seconds_to_boundary(30, lag=2.5, now=1788507225) == 17.5


def test_wait_for_boundary_names_the_window_it_closed_not_the_one_it_opened():
    #: Off by one here would assert against an empty window and report the run
    #: as missing.
    V = _RecordingVLogs()
    assert V.wait_for_boundary(1800, lag=0, now=1788507225, sleep=False) == (
        "2026-09-04T07:30:00Z"
    )
    assert V.wait_for_boundary(30, lag=0, now=1788507225, sleep=False) == (
        "2026-09-04T07:33:30Z"
    )


def test_a_drop_counter_that_cannot_be_a_record_count_is_refused():
    #: The first time this counter was ever read (run 1788745242 -- the metrics
    #: port-forward was down for both earlier runs) it returned
    #: 7,154,980,971,680, almost exactly four times the epoch in MILLISECONDS,
    #: so the field being summed was a timestamp in four plugins. The delta
    #: computed from two such readings was 52,000 and was printed as
    #: suppression. A number that reconciles with nothing on the page borrows
    #: the credibility of the ones that do.
    stamp = 1788745242920
    before = {"lua.0": {"drop_records": stamp}, "lua.1": {"drop_records": stamp}}
    later = stamp + 6000
    after = {"lua.0": {"drop_records": later}, "lua.1": {"drop_records": later}}
    delta, note = vlogs.drop_records_delta(before, after)
    assert delta is None
    assert "UNREADABLE" in note and "record count" in note

    #: and a plausible pair still measures
    delta, note = vlogs.drop_records_delta(
        {"lua.0": {"drop_records": 10}}, {"lua.0": {"drop_records": 99}}
    )
    assert (delta, note) == (89, None)


def test_the_drop_breakdown_names_the_plugin():
    #: A wrong sum is silent; a breakdown naming the plugin is not.
    m = {"lua.0": {"drop_records": 7}, "record_modifier.0": {"drop_records": 0}}
    assert vlogs.drop_records_by_plugin(m) == {"lua.0": 7, "record_modifier.0": 0}
    assert vlogs.drop_records_by_plugin(None) == {}


PROM_SAMPLE = (
    "# HELP fluentbit_filter_drop_records_total drops\n"
    "# TYPE fluentbit_filter_drop_records_total counter\n"
    'fluentbit_filter_drop_records_total{name="polaris_noise_filter"} 1943 1788745242920\n'
    'fluentbit_filter_add_records_total{name="polaris_noise_filter"} 534 1788745242920\n'
    'fluentbit_output_retries_failed_total{name="http.0"} 0 1788745242920\n'
    'fluentbit_output_dropped_records_total{name="http.0"} 0 1788745242920\n'
)


def test_the_prometheus_value_is_not_the_trailing_timestamp():
    #: Fluent Bit's Prometheus encoder appends an optional MILLISECOND
    #: timestamp after the sample value. Reading the line with rpartition(" ")
    #: takes that timestamp, and since fluentbit_metrics tries the prometheus
    #: path FIRST, every filter reported the epoch in ms as its drop_records:
    #: run 1788745242 printed the sum of four of them, 7,154,980,971,680, as a
    #: record count. It also broke the plugin name, which came back as
    #: 'polaris_noise_filter"} 1943'.
    m = vlogs.parse_fluentbit_metrics(PROM_SAMPLE)
    assert set(m) == {"polaris_noise_filter"}
    assert m["polaris_noise_filter"] == {"drop_records": 1943.0, "add_records": 534.0}
    assert vlogs.drop_records_total(m) == 1943.0
    #: and the same reading now passes the plausibility guard it used to fail
    delta, note = vlogs.drop_records_delta({}, m)
    assert (delta, note) == (1943.0, None)


def test_the_output_section_is_readable_and_names_transit_loss():
    #: The counters that separate "the filter never emitted it" from "it was
    #: emitted and the HTTP output dropped it" -- the two candidates for the
    #: missing report windows of 2026-09-07.
    out = vlogs.parse_fluentbit_metrics(PROM_SAMPLE, section="output")
    assert vlogs.output_health(out)["lost"] is False
    doc = (
        '{"output": {"http.0": {"errors": 0, "retries_failed": 2,'
        ' "dropped_records": 0, "proc_records": 20408}}}'
    )
    health = vlogs.output_health(vlogs.parse_fluentbit_metrics(doc, section="output"))
    assert health["lost"] is True and health["retries_failed"] == 2
    assert health["proc_records"] == 20408
