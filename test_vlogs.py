"""Offline tests for `src/vlogs.py` — no cluster, no network.

Every parser here takes text and returns records, so the whole module is
testable against fixtures. Only `VLogs.query` and `fluentbit_metrics` touch a
socket and neither is exercised here.
"""

import sys
import pathlib

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "src"))

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
def test_dedup_by_request_id_keeps_the_first_of_each():
    recs = [
        {"mdc.requestId": "a", "n": 1},
        {"mdc.requestId": "a", "n": 2},
        {"mdc.requestId": "b", "n": 3},
    ]
    assert [r["n"] for r in vlogs.dedup_by_request_id(recs)] == [1, 3]


def test_dedup_keeps_every_record_that_has_no_request_id():
    recs = [{"n": 1}, {"n": 2}]
    assert len(vlogs.dedup_by_request_id(recs)) == 2


def test_status_of_reads_both_the_number_and_the_string_form():
    #: fb-values.yaml sets `type_int_key http_status`, but the source plan's
    #: [verified] sample record carries a string. Both cannot be true of one
    #: deployment; nothing here should fall over while that is open.
    assert vlogs.status_of({"http_status": 404}) == 404
    assert vlogs.status_of({"http_status": "404"}) == 404
    assert vlogs.status_of({"http_status": "404.0"}) == 404
    assert vlogs.status_of({}) is None


def test_status_field_is_numeric_reports_which_form_this_deployment_stores():
    assert vlogs.status_field_is_numeric({"http_status": 200}) == "number"
    assert vlogs.status_field_is_numeric({"http_status": "200"}) == "string"
    assert vlogs.status_field_is_numeric({}) is None


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
