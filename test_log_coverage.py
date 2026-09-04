"""Tests for `src/log_coverage.py`.

Two kinds, and the difference matters.

**Invariants** hold under any sane retention policy: an error is always kept, a
DELETE is always kept, a repeated read of one table collapses. If one of these
fails, the policy has a hole.

**Characterization** records what the policy deployed TODAY does. It is
expected to fail when the policy changes -- that is what it is for. When it
does, the fix is to read the diff it prints, decide the change was intended,
and update both this test and `log-coverage/doc-log-coverage-results.md`, which
otherwise silently describes a pipeline that no longer exists.

Both need a Lua interpreter and the `local-k8s` checkout. Missing either is a
SKIP with the reason, never a silent pass: `log_coverage` deliberately has no
Python re-implementation to fall back on, because a port that agrees with
itself is not evidence.
"""

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "src"))

import log_coverage as lc  # noqa: E402

CAT = "/api/catalog/v1"
MGMT = "/api/management/v1"


# ------------------------------------------------------------ pure python
def test_canonical_makes_the_prefix_and_the_param_names_irrelevant():
    #: `{prefix}` in the Iceberg spec and `{cat}` in the harness are the same
    #: slot. probe_api_surface.py learned that the hard way.
    assert lc.canonical("/v1/{cat}/namespaces/{ns}") == "/{}/namespaces/{}"
    spec_path = f"{CAT}/{{prefix}}/namespaces/{{namespace}}"
    assert lc.canonical(spec_path) == "/{}/namespaces/{}"
    assert lc.canonical(f"{MGMT}/catalogs/{{catalogName}}") == "/catalogs/{}"


def test_canonical_drops_the_query_string():
    got = lc.canonical("/v1/c/namespaces/n/tables/t?snapshots=all")
    assert got == "/c/namespaces/n/tables/t"


def test_api_of_splits_management_from_catalog():
    assert lc.api_of("mgmt.create_principal") == "management"
    assert lc.api_of("iceberg.load_table") == "catalog"
    assert lc.api_of(f"{MGMT}/principals") == "management"


def test_request_id_survives_an_mdc_value():
    #: api_trace._MDC_REQUEST_ID accepts [0-9a-zA-Z-_] only. The dots and the
    #: `[snapshots=refs]` brackets in an operation label do not.
    rid = lc.request_id("1788", 7, "iceberg.load_table[snapshots=refs]")
    assert rid == "nb-1788-007-iceberg-load_table-snapshots-refs"
    assert all(c.isalnum() or c in "-_" for c in rid)


def test_driven_inventory_prefers_the_issued_url_over_the_template():
    rows = [
        {
            "label": "iceberg.load_table",
            "method": "GET",
            "path": "/v1/{cat}/.../tables/{tbl}",
            "actual_path": f"{CAT}/c1/namespaces/ns1/tables/t1",
        }
    ]
    inv = lc.driven_inventory(rows)
    assert list(inv) == [("catalog", "GET", "/c1/namespaces/ns1/tables/t1")]


def test_driven_inventory_drops_an_abbreviated_template_rather_than_guessing():
    class Op:
        label, method, path = "iceberg.load_table", "GET", "/v1/{cat}/.../tables/{tbl}"

    assert lc.driven_inventory([Op()]) == {}


def test_coverage_rows_keeps_the_three_verdicts_apart():
    k_gap = ("catalog", "GET", "/served/but/undriven")
    k_unv = ("catalog", "GET", "/driven/never/seen")
    k_can = ("catalog", "GET", "/spec/only")
    k_ok = ("catalog", "GET", "/both")
    spec = {k_can: {}, k_ok: {}}
    captured = {k_gap: {}, k_ok: {}}
    driven = {k_unv: {"labels": ["x"]}, k_ok: {"labels": ["y"]}}
    verdicts = {
        (r["method"], r["path"]): r["verdict"]
        for r in lc.coverage_rows(spec, captured, driven)
    }
    assert verdicts[("GET", "/served/but/undriven")] == "confirmed gap"
    assert verdicts[("GET", "/driven/never/seen")] == "unverified"
    assert verdicts[("GET", "/spec/only")] == "candidate"
    assert verdicts[("GET", "/both")] == "driven"


def test_access_log_line_matches_the_quarkus_pattern():
    line = lc.access_log_line(
        "GET", "/api/x", 200, size=113, user="root", ip="10.0.0.1"
    )
    assert line.startswith("10.0.0.1 - root [")
    assert line.endswith('"GET /api/x HTTP/1.1" 200 113')


def test_a_zero_byte_body_is_written_as_a_dash():
    #: %b writes "-" for a zero-byte body -- CLF for 0, not for unknown -- and
    #: the deployed parser normalises it back to 0. A 204 writes the dash form.
    assert lc.access_log_line("DELETE", "/api/x", 204, size=0).endswith('" 204 -')


def test_deployed_policy_status_catches_a_policy_that_was_never_installed():
    #: THE 2026-09-04 FINDING, as a regression. fb-values.yaml gained
    #: polaris_noise_filter at 08:26:18Z; the shipper pod had been up since
    #: 08:04:06Z. Parser live, policy absent, nothing dropped -- and the run
    #: could only work that out from the shape of its own results.
    class P:
        script = "function polaris_noise_filter(t, ts, r) return 0 end"

    cm = "data:\n  polaris_access_log.lua: |\n    function polaris_access_log() end\n"
    verdict, detail = lc.deployed_policy_status(cm, P())
    assert verdict is False and "never been applied" in detail


def test_deployed_policy_status_accepts_a_reindented_configmap():
    #: Helm re-emits the block with its own indentation; a byte comparison would
    #: cry wolf on every run.
    class P:
        script = "function polaris_noise_filter(t, ts, r)\n  return 0\nend"

    cm = ("data:\n  x.lua: |\n      function polaris_noise_filter(t, ts, r)\n"
          "        return 0\n      end\n")
    assert lc.deployed_policy_status(cm, P())[0] is True


def test_deployed_policy_status_says_unknown_when_kubectl_is_absent():
    class P:
        script = "x"

    assert lc.deployed_policy_status(None, P())[0] is None


def test_a_configmap_carrying_a_stale_filter_is_not_a_match():
    class P:
        script = "function polaris_noise_filter() return -1 end"

    verdict, detail = lc.deployed_policy_status(
        "polaris_noise_filter -- but an older one, returning 0", P()
    )
    assert verdict is False and "edited since the last helm upgrade" in detail


# ------------------------------------------------------------- the oracle
def _policy():
    if lc.resolve_fb_values() is None:
        pytest.skip("local-k8s/logging/fb-values.yaml not reachable from here")
    try:
        lc.lua_binary()
    except lc.PolicyUnavailable as exc:
        pytest.skip(str(exc))
    return lc.load_policy()


@pytest.fixture(scope="module")
def policy():
    return _policy()


def _rec(method, path, status, **kw):
    return lc.access_log_record(method, path, status, **kw)


def _verdicts(policy, calls):
    return policy.verdicts([_rec(m, p, s) for m, p, s in calls])


T = f"{CAT}/c1/namespaces/ns1/tables/t1"


# -- invariants: these must hold under ANY retention policy worth shipping --
def test_an_error_is_never_deduplicated_away(policy):
    #: Rule 3 outranks rule 6 deliberately: a 404 on a table GET is both "a
    #: table read" and "an error", and errors win, so a client hammering a
    #: missing table stays visible instead of deduplicating into silence.
    assert _verdicts(policy, [("GET", T, 404)] * 20).count("keep") == 20


def test_a_server_error_on_a_deduplicated_path_is_always_kept(policy):
    assert _verdicts(policy, [("GET", T, 500)] * 5).count("keep") == 5


def test_every_delete_is_kept(policy):
    calls = [
        ("DELETE", f"{MGMT}/principals/p1", 204),
        ("DELETE", f"{MGMT}/catalogs/c1", 204),
        ("DELETE", T, 204),
    ]
    assert _verdicts(policy, calls) == ["keep"] * 3


def test_warn_and_error_records_survive_whatever_they_are(policy):
    #: Rule 1. Not the safety net it looks like -- a failed request is usually
    #: an access-log line with a 4xx and no ERROR line at all -- but it must
    #: hold.
    recs = [
        lc.app_log_record("Deprecated Config: quarkus.x", level="WARN"),
        lc.app_log_record("boom", level="ERROR"),
    ]
    assert policy.verdicts(recs) == ["keep", "keep"]


def test_application_logs_pass_through_untouched(policy):
    recs = [lc.app_log_record("query: SELECT 1", level="DEBUG")]
    assert policy.verdicts(recs) == ["keep"]


def test_a_line_that_does_not_parse_is_kept_never_dropped(policy):
    #: Rule 3's null branch: never drop what you could not read. A pattern
    #: change must show up as noise, not as silence.
    bad = {
        "app": "polaris",
        "level": "INFO",
        "loggerName": lc.ACCESS_LOGGER,
        "_time": "2026-09-04T01:00:00.000000000Z",
        "_msg": "the format changed",
    }
    out = policy.predict([bad])
    assert out[0]["verdict"] == "keep" and out[0]["parse_error"]


def test_a_repeated_read_of_one_table_collapses_to_one_a_day(policy):
    assert _verdicts(policy, [("GET", T, 200)] * 20).count("keep") == 1


def test_the_kst_day_comes_from_the_records_own_time_not_the_clock(policy):
    #: A KST day starts at 15:00 UTC, and the day is taken from `_time` so a
    #: shipper REPLAY re-evaluates historical records against their own day.
    before = _rec("GET", T, 200, time_rfc3339="2026-09-04T14:59:00.000000000Z")
    after = _rec("GET", T, 200, time_rfc3339="2026-09-04T15:00:00.000000000Z")
    same_day = _rec("GET", T, 200, time_rfc3339="2026-09-04T15:30:00.000000000Z")
    assert policy.verdicts([before, after]) == ["keep", "keep"]
    assert policy.verdicts([after, same_day]) == ["keep", "drop"]


# -- characterization: EXPECTED TO FAIL when the policy changes -------------
#: Each entry is (method, path, status, expected). Update this list and
#: log-coverage/doc-log-coverage-results.md together, or the report describes a
#: pipeline that no longer exists.
CHARACTERIZED = [
    ("POST", f"{CAT}/oauth/tokens", 200, "drop"),
    ("POST", f"{MGMT}/catalogs", 201, "drop"),
    ("POST", f"{MGMT}/principals", 201, "drop"),
    ("POST", f"{MGMT}/principal-roles", 201, "drop"),
    ("POST", f"{MGMT}/catalogs/c1/catalog-roles", 201, "drop"),
    ("POST", f"{MGMT}/principals/p1/reset", 200, "drop"),
    ("POST", f"{CAT}/c1/tables/rename", 204, "drop"),
    ("POST", f"{CAT}/c1/views/rename", 204, "drop"),
    ("POST", f"{CAT}/c1/namespaces", 200, "drop"),
    ("POST", f"{CAT}/c1/namespaces/ns1/properties", 200, "drop"),
    ("POST", f"{CAT}/c1/namespaces/ns1/tables", 200, "keep"),
    ("POST", T, 200, "keep"),
    ("POST", f"{T}/metrics", 204, "keep"),
    ("POST", f"{CAT}/c1/namespaces/ns1/views", 200, "keep"),
    ("PUT", f"{MGMT}/catalogs/c1/catalog-roles/cr1/grants", 201, "keep"),
    ("GET", f"{CAT}/config", 200, "keep"),
    ("GET", f"{CAT}/c1/namespaces/ns1/tables", 200, "keep"),
]


def test_the_deployed_policy_still_drops_exactly_what_the_report_says(policy):
    got = [
        policy.predict([_rec(m, p, s)])[0]["verdict"]
        for m, p, s, _ in CHARACTERIZED
    ]
    changed = [
        f"  {m:6} {p} ({s}) -- report says {want}, policy says {is_}"
        for (m, p, s, want), is_ in zip(CHARACTERIZED, got)
        if want != is_
    ]
    assert not changed, (
        "the deployed retention policy no longer matches what "
        "log-coverage/doc-log-coverage-results.md describes:\n"
        + "\n".join(changed)
        + "\n\nIf the change was intended, update this list AND the report. "
        "A report nobody updated is worse than no report."
    )


def test_the_dropped_mutations_are_still_ten_and_still_these(policy):
    #: The notebook's headline number. Measured against the deployed Lua on
    #: 2026-09-04: eight of the 43 driven operations, plus the fixture's
    #: catalog create and the token exchange.
    dropped = {
        f"{m} {p}"
        for (m, p, s, _), v in zip(
            CHARACTERIZED,
            [
                policy.predict([_rec(m, p, s)])[0]["verdict"]
                for m, p, s, _ in CHARACTERIZED
            ],
        )
        if v == "drop"
    }
    assert len(dropped) == 10, sorted(dropped)
