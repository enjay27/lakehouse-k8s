"""Tests for `src/os_report.py` -- the OpenSearch query layer.

Two kinds, as `log-coverage/README.md` insists.

**Invariants.** These must hold under any query this module ever builds, and
each one is a bug that has already been paid for somewhere in this pipeline:
the schema filter that gets forgotten at one call site, the `sum` with no
`value_count`, the term filter on an analysed field that matches nothing. They
are asserted structurally -- over the built query body -- so they hold without
a cluster, a drive, or a window boundary to wait for.

**Characterization.** The shape of a response as OpenSearch returns it today.
Expected to fail if the report schema changes, which is the signal to read the
diff rather than to "fix" the test.

No test here touches the network. Every one runs in under a millisecond, which
is the point: the expensive checks need a cluster and these do not, so these
are the ones that run on every commit.
"""

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "src"))

import os_report as osr  # noqa: E402


# ----------------------------------------------------------------------
# invariant: v3 is filtered on EVERY report query
# ----------------------------------------------------------------------
def _filters_of(body):
    return ((body.get("query") or {}).get("bool") or {}).get("filter") or []


REPORT_BUILDERS = [
    ("q_reports", lambda: osr.q_reports()),
    ("q_report_types", lambda: osr.q_report_types()),
    (
        "q_margins",
        lambda: osr.q_margins(("2026-09-10T01:00:00Z", "2026-09-10T02:00:00Z")),
    ),
    ("q_last_write", lambda: osr.q_last_write()),
    ("q_absent_last_write", lambda: osr.q_absent_last_write("t", None)),
    ("q_classification", lambda: osr.q_classification()),
    ("q_role_rows", lambda: osr.q_role_rows()),
    ("q_synthetic_split", lambda: osr.q_synthetic_split()),
    ("q_unclassified", lambda: osr.q_unclassified()),
]


@pytest.mark.parametrize(
    "name,build", REPORT_BUILDERS, ids=[n for n, _ in REPORT_BUILDERS]
)
def test_every_report_query_filters_the_schema_version(name, build):
    """v1, v2 and v3 rows share the index -- measured 2026-09-10, 1465 v2 rows
    against 63 v3 rows in one pattern. A query that forgets the filter mixes
    them and reports a number nobody can interpret."""
    assert {"term": {"schema_version": osr.SCHEMA_VERSION}} in _filters_of(
        build()
    ), f"{name} built a report query with no schema_version filter"


def test_the_schema_version_is_not_hardcoded_past_the_argument():
    """A caller measuring the v2 shipper must be able to say so. The two
    Fluent Bits run different versions as of 2026-09-10, so a module constant
    baked into the query would hand a v3 oracle to a v2 pipeline."""
    body = osr.q_reports(schema_version=2)
    assert {"term": {"schema_version": 2}} in _filters_of(body)


def test_the_access_log_builder_takes_no_schema_version():
    """Access-log records carry no schema_version. A builder that accepted one
    would let a caller believe they had filtered when they had not."""
    with pytest.raises(TypeError):
        osr.q_access_records(schema_version=3)


# ----------------------------------------------------------------------
# invariant: every sum is paired with a value_count
# ----------------------------------------------------------------------
def _agg_names(node, out=None):
    out = [] if out is None else out
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "aggs" and isinstance(v, dict):
                out.extend(v.keys())
            _agg_names(v, out)
    elif isinstance(node, list):
        for v in node:
            _agg_names(v, out)
    return out


def _sum_fields(node, out=None):
    out = set() if out is None else out
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "sum" and isinstance(v, dict) and "field" in v:
                out.add(v["field"])
            _sum_fields(v, out)
    elif isinstance(node, list):
        for v in node:
            _sum_fields(v, out)
    return out


def _count_fields(node, out=None):
    out = set() if out is None else out
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "value_count" and isinstance(v, dict) and "field" in v:
                out.add(v["field"])
            _count_fields(v, out)
    elif isinstance(node, list):
        for v in node:
            _count_fields(v, out)
    return out


@pytest.mark.parametrize(
    "name,build", REPORT_BUILDERS, ids=[n for n, _ in REPORT_BUILDERS]
)
def test_every_sum_has_a_paired_value_count(name, build):
    """`sum` over a field no document carries returns 0.0. A window with no v3
    rows then reports a tidy `0 == 0` and the gate passes without looking --
    the guide flags this and it is the single easiest way to fake a green run."""
    body = build()
    sums, counts = _sum_fields(body), _count_fields(body)
    assert sums <= counts, f"{name}: sum with no value_count on {sorted(sums - counts)}"


# ----------------------------------------------------------------------
# invariant: exact-match terms on string fields use .keyword
# ----------------------------------------------------------------------
def _terms_of(node, out=None):
    out = [] if out is None else out
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "term" and isinstance(v, dict):
                out.extend(v.keys())
            if k == "terms" and isinstance(v, dict) and "field" in v:
                out.append(v["field"])
            _terms_of(v, out)
    elif isinstance(node, list):
        for v in node:
            _terms_of(v, out)
    return out


@pytest.mark.parametrize(
    "name,build", REPORT_BUILDERS, ids=[n for n, _ in REPORT_BUILDERS]
)
def test_string_fields_are_matched_on_the_keyword_subfield(name, build):
    """THE GUIDE'S GATE 5 IS WRITTEN WITH THIS BUG.

    `{"term": {"resource": "__errors__"}}` runs against the analysed text
    field, where the standard analyser has already turned `__errors__` into the
    token `errors`. It matches nothing, the aggregation reports zero, and the
    gate passes forever without having looked at anything.
    """
    for field in _terms_of(build()):
        base = field[: -len(".keyword")] if field.endswith(".keyword") else field
        if base in osr.STRING_FIELDS:
            assert field.endswith(".keyword"), (
                f"{name}: term/terms on the analysed field `{field}` -- "
                "it will silently match nothing"
            )


def test_kw_leaves_numeric_fields_alone():
    """A `.keyword` suffix on a numeric field produces a clean 'no such field',
    but only if we never add one."""
    assert osr.kw("requests") == "requests"
    assert osr.kw("http_status") == "http_status"
    assert osr.kw("resource") == "resource.keyword"
    assert osr.kw("resource.keyword") == "resource.keyword"


def test_gate5_asks_for_both_synthetic_keys_by_their_exact_names():
    body = osr.q_synthetic_split()
    filters = body["aggs"]["synthetic"]["filters"]["filters"]
    assert filters["errors"] == {"term": {"resource.keyword": "__errors__"}}
    assert filters["other"] == {"term": {"resource.keyword": "__other__"}}


# ----------------------------------------------------------------------
# invariant: absence is not zero
# ----------------------------------------------------------------------
def test_a_metric_no_document_carried_is_absent_not_zero():
    m = osr.Metric("requests", 0.0, 0)
    assert m.absent and m.value is None
    assert m.as_int() is None and m.as_int(0) == 0


def test_a_real_zero_is_a_zero():
    m = osr.Metric("requests", 0.0, 4)
    assert not m.absent and m.value == 0.0 and m.as_int() == 0


def test_a_metric_compares_to_a_plain_number():
    assert osr.Metric("errors_4xx", 26.0, 2) == 26
    assert not (
        osr.Metric("errors_4xx", 0.0, 0) == 0
    ), "an absent field must not compare equal to zero -- that is the whole bug"


def test_gate2_negative_half_asks_for_ABSENT_not_for_zero():
    """`last_write_bytes` must be absent, never 0, when a window's only write
    was a DELETE (204, empty body). A query looking for `: 0` would pass
    against a schema doing the thing the schema forbids."""
    body = osr.q_absent_last_write("tbl", None)
    assert body["query"]["bool"]["must_not"] == [
        {"exists": {"field": "last_write_bytes"}}
    ]
    assert "0" not in str(body["query"]["bool"].get("filter"))


# ----------------------------------------------------------------------
# invariant: counts are scoped to the run's windows
# ----------------------------------------------------------------------
def test_a_window_range_is_lexical_over_window_start_keyword():
    f = osr.window_filter("2026-09-10T01:00:00Z", "2026-09-10T01:30:00Z")
    assert f == {
        "range": {
            "window_start.keyword": {
                "gte": "2026-09-10T01:00:00Z",
                "lte": "2026-09-10T01:30:00Z",
            }
        }
    }


def test_margins_carries_the_window_range_into_the_query():
    """The report index is written continuously -- 1 row per window, 2/min at
    WINDOW_SECONDS=30. An unscoped count is a statement about how long the
    query took to reach the server."""
    win = ("2026-09-10T01:00:00Z", "2026-09-10T01:30:00Z")
    assert osr.window_filter(*win) in _filters_of(osr.q_margins(win))


def test_no_window_means_no_range_rather_than_a_silent_default():
    assert osr.window_filter(None, None) is None
    assert len(_filters_of(osr.q_reports())) == 1  # the schema term, nothing invented


# ----------------------------------------------------------------------
# parsers
# ----------------------------------------------------------------------
def _win_bucket(ws, res_req, pri_req, seen, parse=0, doc_count=6):
    def m(field, total, n):
        return {f"{field}__sum": {"value": float(total)}, f"{field}__n": {"value": n}}

    res, pri = {}, {}
    res.update(m("requests", res_req, 3))
    pri.update(m("requests", pri_req, 2))
    for f in ("errors_4xx", "errors_5xx", "auth_denied", "response_bytes", "errors"):
        res.update(m(f, 0, 3))
        pri.update(m(f, 0, 2))
    b = {
        "key": ws,
        "doc_count": doc_count,
        "by_type": {
            "buckets": [{"key": "resource", **res}, {"key": "principal", **pri}]
        },
    }
    b.update(m("access_seen", seen, 1))
    b.update(m("parse_errors", parse, 1))
    for f in (
        "carried_rows",
        "distinct_resources",
        "distinct_principals",
        "role_keys_forced",
        "resources_other",
    ):
        b.update(m(f, 0, 1))
    return b


def test_the_margin_holds_when_the_three_figures_agree():
    resp = {
        "aggregations": {"by_win": {"buckets": [_win_bucket("W", 40, 40, 41, parse=1)]}}
    }
    row = osr.parse_margins(resp)[0]
    assert row["ok"] is True and row["expected"] == 40


def test_the_margin_fails_loudly_and_names_all_three_numbers():
    resp = {
        "aggregations": {"by_win": {"buckets": [_win_bucket("W", 39, 40, 41, parse=1)]}}
    }
    row = osr.parse_margins(resp)[0]
    assert row["ok"] is False
    assert "39" in row["why"] and "40" in row["why"]


def test_a_window_with_no_v3_rows_is_UNPROVEN_not_failed():
    """The distinction the whole harness rests on. A quiet window has nothing
    to say; reporting it as a failure invents a pipeline fault, and reporting
    it as a pass invents a measurement."""
    empty = {"key": "W", "doc_count": 0, "by_type": {"buckets": []}}
    row = osr.parse_margins({"aggregations": {"by_win": {"buckets": [empty]}}})[0]
    assert row["ok"] is None and "no v3 resource/principal rows" in row["why"]


def test_synthetic_split_passes_when_errors_holds_nothing_but_errors():
    resp = {
        "aggregations": {
            "synthetic": {
                "buckets": {
                    "errors": {
                        "doc_count": 2,
                        "requests__sum": {"value": 38.0},
                        "requests__n": {"value": 2},
                        "errors__sum": {"value": 38.0},
                        "errors__n": {"value": 2},
                    },
                    "other": {
                        "doc_count": 0,
                        "requests__sum": {"value": 0.0},
                        "requests__n": {"value": 0},
                        "errors__sum": {"value": 0.0},
                        "errors__n": {"value": 0},
                    },
                }
            }
        }
    }
    out = osr.parse_synthetic(resp)
    assert out["verdict"] is True
    assert out["other"][
        "requests"
    ].absent, "an absent __other__ must not read as zero traffic"


def test_synthetic_split_fails_when_errors_carries_non_error_traffic():
    resp = {
        "aggregations": {
            "synthetic": {
                "buckets": {
                    "errors": {
                        "doc_count": 1,
                        "requests__sum": {"value": 10.0},
                        "requests__n": {"value": 1},
                        "errors__sum": {"value": 4.0},
                        "errors__n": {"value": 1},
                    },
                    "other": {"doc_count": 0},
                }
            }
        }
    }
    out = osr.parse_synthetic(resp)
    assert out["verdict"] is False and "non-error traffic" in out["why"]


def test_synthetic_split_is_unproven_when_nothing_landed_there():
    resp = {
        "aggregations": {
            "synthetic": {
                "buckets": {"errors": {"doc_count": 0}, "other": {"doc_count": 0}}
            }
        }
    }
    assert osr.parse_synthetic(resp)["verdict"] is None


def test_gate6_reports_real_paths_and_drops_the_two_synthetic_keys():
    resp = {
        "aggregations": {
            "by_api": {
                "buckets": [
                    {
                        "key": "catalog",
                        "paths": {
                            "buckets": [
                                {"key": "__errors__", "doc_count": 9},
                                {"key": "__other__", "doc_count": 1},
                                {
                                    "key": "/api/catalog/v1/c/namespaces/ns/tables/t/credentials",
                                    "doc_count": 3,
                                },
                            ]
                        },
                    }
                ]
            }
        }
    }
    out = osr.unclassified_paths(resp)
    assert [r["resource"] for r in out] == [
        "/api/catalog/v1/c/namespaces/ns/tables/t/credentials"
    ]
    assert out[0]["api_kind"] == "catalog"


def test_report_types_parses_the_array_split():
    resp = {
        "aggregations": {
            "by_type": {
                "buckets": [
                    {"key": "summary", "doc_count": 1},
                    {"key": "resource", "doc_count": 3},
                    {"key": "principal", "doc_count": 2},
                ]
            }
        }
    }
    assert osr.parse_types(resp) == {"summary": 1, "resource": 3, "principal": 2}


# ----------------------------------------------------------------------
# mapping helpers -- the min_record_time trap
# ----------------------------------------------------------------------
def test_first_type_walks_a_real_mapping_response():
    resp = {
        "polaris-report-2026.09.10": {
            "mappings": {
                "min_record_time": {
                    "full_name": "min_record_time",
                    "mapping": {"min_record_time": {"type": "text"}},
                }
            }
        }
    }
    assert osr._first_type(resp) == "text"


def test_a_field_nothing_has_carried_has_no_type():
    assert osr._first_type({"idx": {"mappings": {}}}) is None


def test_window_bounds_aligns_to_the_wall_clock_grid():
    # 2026-09-10T01:26:17Z, 30s windows -> 01:26:00 .. 01:26:30
    t = 1789003577
    assert osr.window_bounds(t, 30) == ("2026-09-10T01:26:00Z", "2026-09-10T01:26:30Z")


def test_seconds_to_boundary_never_returns_a_full_window():
    for now in (0.0, 1.0, 29.9, 30.0, 45.5):
        s = osr.seconds_to_boundary(30, now=now)
        assert 0 < s <= 30


def test_partial_window_is_a_string_and_the_constants_say_so():
    """Review #1: `counts.partial and "true" or "false"`. Every other flag-like
    value in the schema is an int, so this one reads as a boolean and is not."""
    assert osr.PARTIAL_TRUE == "true" and isinstance(osr.PARTIAL_TRUE, str)


def test_the_correlation_field_is_matched_on_its_keyword_subfield():
    """A request id is `nb-<run>-<seq>-<label>` and the standard analyser splits
    it on every hyphen, so a term or prefix query against the analysed field
    matches NOTHING -- every call reports unrecovered and the per-call half of
    the matrix reads as a total pipeline failure rather than as a query bug.

    Found on 2026-09-10 in THIS module, while wiring the v2 notebook, three
    commits after the same defect was written up as a finding against the
    guide's Gate 5."""
    assert osr.kw("mdc.requestId") == "mdc.requestId.keyword"
    body = {
        "query": {
            "bool": {
                "filter": [
                    {"term": {osr.kw("mdc.requestId"): "nb-1789-007-loadTable-404"}}
                ]
            }
        }
    }
    assert _terms_of(body) == ["mdc.requestId.keyword"]


# ----------------------------------------------------------------------
# field names are READ from the mapping, never assumed
# ----------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _forget_the_mapping():
    """Every test starts from the STRING_FIELDS default, not from whatever the
    previous test taught the module."""
    osr.use_mapping({})
    yield
    osr.use_mapping({})


def test_a_date_mapped_field_is_matched_WITHOUT_the_keyword_suffix():
    """MEASURED, run 1789007773: `window_start` is an RFC3339 string and
    OpenSearch date-detects it, so `window_start.keyword` does not exist. Every
    window-scoped report query matched nothing and eight gates went VOID on an
    empty result -- the same defect as the guide's Gate 5, in the opposite
    direction."""
    osr.use_mapping({"window_start": "date"})
    assert osr.kw("window_start") == "window_start"
    assert osr.window_filter("A", "B") == {
        "range": {"window_start": {"gte": "A", "lte": "B"}}
    }


def test_a_text_mapped_field_still_gets_the_suffix():
    osr.use_mapping({"resource": "text", "min_record_time": "text"})
    assert osr.kw("resource") == "resource.keyword"
    assert osr.kw("min_record_time") == "min_record_time.keyword"


def test_two_fields_of_the_same_shape_can_be_mapped_differently():
    """`window_start` and `min_record_time` are both RFC3339 strings in the same
    index, and are mapped date and text respectively -- because the Lua writes
    "" on idle windows and the index typed min_record_time from the first one.
    Nothing about a field's VALUES predicts its mapping."""
    osr.use_mapping({"window_start": "date", "min_record_time": "text"})
    assert osr.kw("window_start") == "window_start"
    assert osr.kw("min_record_time") == "min_record_time.keyword"


def test_an_unmapped_field_falls_back_rather_than_guessing():
    """None means nothing has carried it yet. Absence is not evidence, so the
    STRING_FIELDS default stands."""
    osr.use_mapping({"resource": None})
    assert osr.kw("resource") == "resource.keyword"


def test_a_keyword_mapped_field_is_left_alone():
    osr.use_mapping({"report_type": "keyword"})
    assert osr.kw("report_type") == "report_type"


def test_the_margins_query_follows_the_resolved_names():
    """The whole point: the builders are pure, and they still pick up what the
    mapping said."""
    osr.use_mapping({"window_start": "date", "report_type": "text"})
    body = osr.q_margins(("A", "B"))
    assert body["aggs"]["by_win"]["terms"]["field"] == "window_start"
    assert (
        body["aggs"]["by_win"]["aggs"]["by_type"]["terms"]["field"]
        == "report_type.keyword"
    )


def test_types_of_reads_every_field_not_just_the_first():
    """`_first_type` walks the document and returns the first type it meets --
    correct for one field, silently wrong for many, which would make every
    field report as whichever OpenSearch serialised first."""
    resp = {
        "polaris-report-2026.09.10": {
            "mappings": {
                "window_start": {
                    "full_name": "window_start",
                    "mapping": {"window_start": {"type": "date"}},
                },
                "min_record_time": {
                    "full_name": "min_record_time",
                    "mapping": {"min_record_time": {"type": "text"}},
                },
                "requests": {
                    "full_name": "requests",
                    "mapping": {"requests": {"type": "long"}},
                },
            }
        }
    }
    assert osr._types_of(resp) == {
        "window_start": "date",
        "min_record_time": "text",
        "requests": "long",
    }


# ----------------------------------------------------------------------
# the shape at the boundary: OpenSearch nests, VictoriaLogs flattens
# ----------------------------------------------------------------------
def test_a_nested_source_is_flattened_to_dotted_keys():
    """Run 1789008899 reported all eight 500s as `absent` -- no application
    line, which rule 2 forbids and which would be a SERIOUS pipeline finding.
    It is a dict access: lc.error_record_pair filters on
    `r.get("mdc.requestId")`, and OpenSearch keeps that nested in _source while
    VictoriaLogs flattens it on ingest. The QUERY works either way, which is
    why correlation reported 286/286 and hid it."""
    nested = {
        "mdc": {"requestId": "nb-1-001-x", "principal": "runner"},
        "exception": {"frames": [{"class": "X"}], "message": "boom"},
        "level": "ERROR",
    }
    flat = osr.flatten(nested)
    assert flat["mdc.requestId"] == "nb-1-001-x"
    assert flat["exception.frames"] == [{"class": "X"}]
    assert flat["level"] == "ERROR"


def test_an_already_flat_record_is_unchanged():
    flat = {"mdc.requestId": "nb-1-001-x", "http_status": 500}
    assert osr.flatten(flat) == flat


def test_a_list_value_is_left_alone_not_walked():
    """`exception.frames` is a list of dicts and must stay one -- flattening it
    into frames.0.class would break exception_fields, which looks for the
    field NAME."""
    out = osr.flatten({"exception": {"frames": [{"class": "A"}, {"class": "B"}]}})
    assert out["exception.frames"] == [{"class": "A"}, {"class": "B"}]


def test_sources_flattens_and_raw_sources_does_not():
    body = {"hits": {"hits": [{"_source": {"mdc": {"requestId": "r1"}}}]}}
    res = osr.Result(body, "polaris-logs-*")
    assert res.sources == [{"mdc.requestId": "r1"}]
    assert res.raw_sources == [{"mdc": {"requestId": "r1"}}]
