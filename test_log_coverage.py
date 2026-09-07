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

    cm = (
        "data:\n  x.lua: |\n      function polaris_noise_filter(t, ts, r)\n"
        "        return 0\n      end\n"
    )
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


def test_nothing_vanishes_silently(policy):
    #: The one invariant that outlives any policy: a request either leaves an
    #: individual record or is counted into the window's aggregate. v2 could
    #: satisfy this by keeping; v3 satisfies it by counting. A policy that
    #: satisfies NEITHER has a hole, and this is the test that finds it.
    W = policy.window_seconds
    calls = [("GET", T, 200), ("POST", f"{CAT}/oauth/tokens", 200), ("DELETE", T, 204)]
    recs = [_rec(m, p, s) for m, p, s in calls]
    verdicts, reports = policy.report_windows(recs, base=0, silent_windows=0)
    kept = sum(1 for v in verdicts if v["verdict"] == "keep")
    summary = [r for r in reports["w1"] if r["report_type"] == "summary"][0]
    assert summary["access_seen"] == len(calls)
    assert summary["access_kept"] == kept
    assert summary["access_kept"] + summary["access_counted"] == summary["access_seen"]


# -- the scheduled flush report: invariants ---------------------------------
def _window(policy, calls, base=0, silent=0, users=None):
    users = users or ["reader"] * len(calls)
    recs = [
        _rec(m, p, s, user=u, when=base + 10 + i)
        for i, ((m, p, s), u) in enumerate(zip(calls, users))
    ]
    return policy.report_windows(recs, base=base, silent_windows=silent)


def test_a_report_window_satisfies_every_schema_invariant(policy):
    _, reports = _window(
        policy,
        [
            ("GET", T, 200),
            ("PUT", T, 200),
            ("GET", T, 403),
            ("GET", f"{CAT}/c1/namespaces/ns1/tables/gone", 404),
            ("HEAD", f"{CAT}/c1/namespaces/ns1/views/v1", 200),
            ("POST", f"{MGMT}/principals", 201),
        ],
        users=["reader", "writer", "reader", "reader", "reader", "writer"],
    )
    assert lc.check_invariants(reports["w1"]) == []


def test_the_margins_are_the_only_real_self_check_and_they_catch_a_miscount(policy):
    #: `errors` overlaps `reads`/`writes` by design, so the resource margin and
    #: the principal margin agreeing is the schema's only cross-check. Move one
    #: count by one and it must fail -- otherwise the invariant is decorative.
    _, reports = _window(policy, [("GET", T, 200), ("PUT", T, 200)])
    rows = [dict(r) for r in reports["w1"]]
    assert lc.check_invariants(rows) == []
    for r in rows:
        if r["report_type"] == "resource" and r.get("requests"):
            r["requests"] += 1
            break
    bad = lc.check_invariants(rows)
    assert any("MARGINS DISAGREE" in b for b in bad), bad


def test_an_error_increments_an_existing_key_but_never_creates_one(policy):
    #: A GET 404 on a table that was never read successfully lands in
    #: `__other__`. Its count is NOT lost -- that is what keeps the margins
    #: exact -- and the request itself is stored in full by rule 3. Without
    #: this, a client walking invented table names could fill the key space.
    _, reports = _window(
        policy,
        [("GET", f"{CAT}/c1/namespaces/ns1/tables/never", 404)] * 3,
    )
    keys = {r["resource"] for r in reports["w1"] if r["report_type"] == "resource"}
    assert keys == {lc.REPORT_OTHER}
    other = [r for r in reports["w1"] if r.get("resource") == lc.REPORT_OTHER][0]
    assert other["requests"] == 3 and other["errors"] == 3


def test_an_error_on_a_known_resource_increments_that_resource(policy):
    _, reports = _window(policy, [("GET", T, 200), ("GET", T, 403)])
    rows = [r for r in reports["w1"] if r["report_type"] == "resource"]
    assert [r["resource"] for r in rows] == [T]
    assert rows[0]["requests"] == 2 and rows[0]["errors"] == 1


def test_a_sub_resource_counts_under_its_table_not_as_its_own_row(policy):
    #: v2 emitted two rows for one table. The resource key is the RESOURCE, not
    #: the URL.
    _, reports = _window(policy, [("GET", T, 200), ("POST", f"{T}/metrics", 204)])
    rows = [r for r in reports["w1"] if r["report_type"] == "resource"]
    assert [r["resource"] for r in rows] == [T]
    assert rows[0]["requests"] == 2
    assert not any("/metrics" in r["resource"] for r in rows)


def test_all_six_resource_kinds_are_reachable(policy):
    got = policy.classify_paths(
        [
            T,
            f"{CAT}/c1/namespaces/ns1/views/v1",
            f"{CAT}/c1/namespaces/ns1/tables",
            f"{CAT}/c1/namespaces/ns1",
            f"{MGMT}/principals",
            f"{CAT}/config",
        ]
    )
    assert sorted({kind for _, kind in got.values()}) == sorted(lc.RESOURCE_KINDS)


def test_response_bytes_is_zero_for_a_body_less_response(policy):
    #: `%b` writes `-` for a zero-byte body and the parser normalises it to 0.
    _, reports = _window(policy, [("HEAD", T, 200), ("DELETE", T, 204)])
    row = [r for r in reports["w1"] if r["report_type"] == "resource"][0]
    assert row["response_bytes"] == 0 and row["requests"] == 2


def test_the_tick_rate_is_not_the_report_period(policy):
    #: THE scheduled-job property. The dummy INPUT ticks every 30s; a tick
    #: inside the current window is dropped and only the boundary emits. Sixty
    #: ticks inside one window must produce exactly ONE report, not sixty.
    W = policy.window_seconds
    tick = policy.tick_seconds or 30
    events = [lc.Tick(1, "open"), _rec("GET", T, 200, when=2)]
    #: every tick STRICTLY inside the window -- one more than this and the last
    #: one lands on the boundary itself, which is a bug in the test and was one
    #: on 2026-09-04 (it reported `mid58` and read as a filter fault). The
    #: spacing is the DEPLOYED tick interval, not a literal: this test broke
    #: correctly when WINDOW_SECONDS went 1800 -> 30 and the interval 30 -> 5.
    events += [lc.Tick(tick * i, f"mid{i}") for i in range(1, max(2, W // tick))]
    events.append(lc.Tick(W + 1, "boundary"))
    _, reports = policy.run(events)
    assert list(reports) == ["boundary"], list(reports)
    assert len(events) > 3, (
        f"no mid-window ticks at WINDOW_SECONDS={W}, Interval_Sec={tick} -- "
        "this test proves nothing until the tick is smaller than the window"
    )


def test_the_tick_interval_stays_well_under_the_window(policy):
    #: A CONFIGURATION invariant, not a schema one, and it earns its place: at
    #: tick >= window a tick that arrives late moves the window index by TWO.
    #: The filter reports the window it was holding and the one in between
    #: never existed -- its records were attributed to the previous window and
    #: no report for it is ever emitted. Nothing in the schema can detect that
    #: from a single record; only a gap between consecutive `window_start`s
    #: shows it. Cell 14 looks for exactly that gap.
    W, tick = policy.window_seconds, policy.tick_seconds
    assert tick is not None, "the dummy INPUT's Interval_Sec could not be read"
    assert (
        tick < W
    ), f"Interval_Sec {tick} >= WINDOW_SECONDS {W}: a late tick skips a window"
    assert W / tick >= 4, (
        f"only {W / tick:.0f} ticks per window (Interval_Sec {tick}, "
        f"WINDOW_SECONDS {W}) -- too little margin for scheduling jitter"
    )


def test_a_window_start_is_always_aligned_to_window_seconds(policy):
    #: The filter derives both bounds from `floor(now / WINDOW_SECONDS)`, so an
    #: unaligned `window_start` in VictoriaLogs did not come from this filter.
    W = policy.window_seconds
    _, reports = _window(policy, [("GET", T, 200)], base=0)
    s = [r for r in reports["w1"] if r["report_type"] == "summary"][0]
    start = lc._epoch_of(s["window_start"])
    assert start % W == 0
    assert lc._epoch_of(s["window_end"]) - start == W
    assert s["_time"] == s["window_end"]


def test_a_resource_active_in_one_window_reports_an_explicit_zero_in_the_next(policy):
    #: ZERO-CARRY. A dashboard that drops a series the moment it goes quiet
    #: cannot tell "no traffic" from "no shipper".
    _, reports = _window(policy, [("GET", T, 200)], silent=1)
    w1 = {r["resource"] for r in reports["w1"] if r["report_type"] == "resource"}
    w2 = {r["resource"]: r for r in reports["w2"] if r["report_type"] == "resource"}
    assert w1 and w1 <= set(w2)
    assert all(w2[k]["requests"] == 0 for k in w1)


def test_a_carried_row_that_stayed_zero_is_not_carried_again(policy):
    #: CARRY DECAY, the other half. Without it every key ever seen is reported
    #: forever.
    _, reports = _window(policy, [("GET", T, 200)], silent=2)
    w2 = {r["resource"] for r in reports["w2"] if r["report_type"] == "resource"}
    w3 = {r["resource"] for r in reports["w3"] if r["report_type"] == "resource"}
    assert w2 and not (w2 & w3)


def test_report_seq_increments_by_one_per_report(policy):
    _, reports = _window(policy, [("GET", T, 200)], silent=2)
    seqs = [
        [r for r in reports[w] if r["report_type"] == "summary"][0]["report_seq"]
        for w in ("w1", "w2", "w3")
    ]
    assert seqs == [seqs[0], seqs[0] + 1, seqs[0] + 2]


def test_counters_reset_between_windows(policy):
    _, reports = _window(policy, [("GET", T, 200), ("GET", T, 200)], silent=1)
    w2 = [r for r in reports["w2"] if r["report_type"] == "summary"][0]
    assert w2["access_seen"] == 0 and w2["access_counted"] == 0


def test_the_first_window_after_a_start_is_flagged_partial(policy):
    #: `partial_window` is the string "true", not a boolean -- it is written
    #: with `and "true" or "false"`. The first tick after start OPENS a window
    #: rather than reporting one, and flags it, because the shipper missed the
    #: beginning of it.
    _, reports = _window(policy, [("GET", T, 200)], silent=1)
    w1 = [r for r in reports["w1"] if r["report_type"] == "summary"][0]
    w2 = [r for r in reports["w2"] if r["report_type"] == "summary"][0]
    assert w1["partial_window"] == "true"
    assert w2["partial_window"] == "false"


def test_records_before_the_first_tick_are_counted_into_no_window(policy):
    #: A REAL PROPERTY OF THE DEPLOYED FILTER, not a bug in the harness -- and
    #: the reason `Policy.run` takes an ordered event list rather than records
    #: plus a time. `count_record()` returns immediately while `counts` is nil,
    #: so records processed between shipper start and the first tick are routed
    #: correctly but appear in no report. Bounded by the tick period (30s
    #: deployed). Found on 2026-09-04 by a driver that ticked only at the end.
    W = policy.window_seconds
    events = [
        _rec("GET", T, 200, when=5),
        _rec("PUT", T, 200, when=6),
        lc.Tick(10, "open"),
        _rec("GET", T, 200, when=20),
        lc.Tick(W + 1, "w1"),
    ]
    verdicts, reports = policy.run(events)
    assert len(verdicts) == 3
    summary = [r for r in reports["w1"] if r["report_type"] == "summary"][0]
    assert summary["access_seen"] == 1, (
        "the two records before the first tick should be invisible to the "
        "report -- if this now counts 3, the filter gained a startup buffer "
        "and the results doc's blind-spot note is stale"
    )


def test_the_oracle_diff_is_empty_against_itself_and_names_a_single_field(policy):
    #: `diff_reports` is what makes schema coverage a DIFF instead of a set of
    #: hand-written expectations, so its own failure mode has to be exact.
    _, reports = _window(policy, [("GET", T, 200), ("PUT", T, 200)])
    rows = reports["w1"]
    assert lc.report_mismatches(lc.diff_reports(rows, rows)) == []
    tampered = [dict(r) for r in rows]
    for r in tampered:
        if r["report_type"] == "resource":
            r["reads"] = r["reads"] + 7
            break
    mm = lc.report_mismatches(lc.diff_reports(rows, tampered))
    assert len(mm) == 1 and mm[0]["field"] == "reads"


def test_the_diff_ignores_fields_that_describe_the_emitting_process(policy):
    #: `hostname` is `os.getenv("HOSTNAME") or "unknown"` and `report_seq` is a
    #: per-process counter. The oracle does not run in the shipper pod, so
    #: comparing them would fail on every row and hide the real diffs.
    _, reports = _window(policy, [("GET", T, 200)])
    rows = reports["w1"]
    shifted = [dict(r, hostname="some-pod-xyz", report_seq=99) for r in rows]
    assert lc.report_mismatches(lc.diff_reports(rows, shifted)) == []


# -- characterization: EXPECTED TO FAIL when the policy changes -------------
#: v3, measured against the deployed Lua on 2026-09-04 (fb-values.yaml sha256
#: 89aa2624f1f5...). Update this list and log-coverage/doc-log-coverage-results.md
#: together, or the report describes a pipeline that no longer exists.
#:
#: The v2 list this replaces said `drop` for every management POST. That was
#: the audit hole the notebook's first run measured: principals created
#: invisibly, deleted visibly, and a credential reset leaving no trace at all.
#: v3 closes it and pays for it by counting successful reads instead.
CHARACTERIZED = [
    # rule 5a -- POST under /api/management/ is KEPT. The v2 audit hole, closed.
    ("POST", f"{MGMT}/catalogs", 201, "keep"),
    ("POST", f"{MGMT}/principals", 201, "keep"),
    ("POST", f"{MGMT}/principal-roles", 201, "keep"),
    ("POST", f"{MGMT}/catalogs/c1/catalog-roles", 201, "keep"),
    ("POST", f"{MGMT}/principals/p1/reset", 200, "keep"),
    # rule 5b -- every other successful POST is counted only
    ("POST", f"{CAT}/oauth/tokens", 200, "drop"),
    ("POST", f"{CAT}/c1/tables/rename", 204, "drop"),
    ("POST", f"{CAT}/c1/views/rename", 204, "drop"),
    ("POST", f"{CAT}/c1/namespaces", 200, "drop"),
    ("POST", f"{CAT}/c1/namespaces/ns1/properties", 200, "drop"),
    ("POST", f"{CAT}/c1/namespaces/ns1/tables", 200, "drop"),
    ("POST", T, 200, "drop"),
    ("POST", f"{T}/metrics", 204, "drop"),
    ("POST", f"{CAT}/c1/namespaces/ns1/views", 200, "drop"),
    # rule 6 -- successful GET/HEAD counted only, INCLUDING lists and /config
    ("GET", T, 200, "drop"),
    ("HEAD", T, 200, "drop"),
    ("GET", f"{CAT}/config", 200, "drop"),
    ("GET", f"{CAT}/c1/namespaces/ns1/tables", 200, "drop"),
    ("GET", f"{MGMT}/principals", 200, "drop"),
    # rules 3 and 4 -- unchanged from v2, and the reason the pipeline is worth
    # having at all
    ("GET", T, 404, "keep"),
    ("GET", T, 500, "keep"),
    ("PUT", f"{MGMT}/catalogs/c1/catalog-roles/cr1/grants", 201, "keep"),
    ("DELETE", T, 204, "keep"),
]


def test_the_deployed_policy_still_does_exactly_what_the_report_says(policy):
    got = [
        policy.predict([_rec(m, p, s)])[0]["verdict"] for m, p, s, _ in CHARACTERIZED
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


def test_every_management_mutation_is_now_stored(policy):
    #: The headline of the v2 run was that TEN mutations produced no record at
    #: all, five of them management POSTs -- a principal created invisibly and
    #: deleted visibly, a credential reset leaving nothing. This is the test
    #: that says v3 closed it, and it is the one to read first if v4 ever
    #: reopens it.
    mutations = [
        ("POST", f"{MGMT}/principals", 201),
        ("POST", f"{MGMT}/principal-roles", 201),
        ("POST", f"{MGMT}/catalogs", 201),
        ("POST", f"{MGMT}/catalogs/c1/catalog-roles", 201),
        ("POST", f"{MGMT}/principals/p1/reset", 200),
        ("PUT", f"{MGMT}/principal-roles/pr1/catalog-roles/c1", 201),
        ("DELETE", f"{MGMT}/principals/p1", 204),
    ]
    assert _verdicts(policy, mutations) == ["keep"] * len(mutations)


def test_what_v3_gave_up_to_get_it(policy):
    #: The honest other half: successful reads and non-management creates now
    #: leave no individual record. They are COUNTED, not lost -- but access
    #: frequency per call is gone, and so is the timestamp of any single read.
    counted = [
        ("GET", T, 200),
        ("HEAD", T, 200),
        ("GET", f"{CAT}/c1/namespaces/ns1/tables", 200),
        ("GET", f"{CAT}/config", 200),
        ("POST", f"{CAT}/c1/namespaces/ns1/tables", 200),
        ("POST", f"{CAT}/oauth/tokens", 200),
    ]
    assert _verdicts(policy, counted) == ["drop"] * len(counted)


def test_victorialogs_metadata_is_not_read_as_schema_drift(policy):
    #: VictoriaLogs stamps `_stream` and `_stream_id` onto every record it
    #: returns. They are not fields the filter emitted. The 2026-09-04 verify
    #: run reported all six stored rows as carrying "unexpected fields" because
    #: of them -- a harness bug that would have fired on EVERY window of the
    #: real run and read as the report drifting from its own schema.
    _, reports = _window(policy, [("GET", T, 200), ("PUT", T, 200)])
    stored = [
        dict(
            r,
            _stream='{app="polaris-shipper-report",level="REPORT"}',
            _stream_id="0000000000000000d2093bd84cc34837",
        )
        for r in reports["w1"]
    ]
    assert lc.check_invariants(stored) == []
    #: but a field that is NOT VictoriaLogs metadata still fails
    tampered = [dict(r, surprise=1) for r in stored]
    assert any("unexpected fields" in b for b in lc.check_invariants(tampered))


def test_a_quiet_window_may_arrive_without_its_time_fields(policy):
    #: The filter writes min/max_record_time as "" when a window saw nothing,
    #: and VictoriaLogs does not store empty values -- so they are simply absent
    #: from every stored quiet window. Absent and empty are the same statement
    #: here. Measured 2026-09-04, when every silent window in the run reported
    #: "summary row is missing fields: ['max_record_time', 'min_record_time']".
    _, reports = _window(policy, [("GET", T, 200)], silent=1)
    quiet = [dict(r) for r in reports["w2"]]
    for r in quiet:
        r.pop("min_record_time", None)
        r.pop("max_record_time", None)
    assert lc.check_invariants(quiet) == []
    #: any OTHER missing field is still schema drift
    broken = [dict(r) for r in quiet]
    broken[0].pop("counted_read", None)
    assert any("missing fields" in b for b in lc.check_invariants(broken))


def test_a_run_spanning_several_windows_merges_into_one_comparable_set(policy):
    #: At WINDOW_SECONDS 30 every run spans many windows, so reading ONE window
    #: reports whatever landed in the last 30 seconds. On 2026-09-04 that was
    #: the cleanup DELETEs alone: 8 records, all errors, a single __other__ row,
    #: and a report that looked like the pipeline had lost the whole run.
    W = policy.window_seconds
    base = 0
    events = [lc.Tick(base + 1, "open")]
    events += [_rec("GET", T, 200, when=base + 5), _rec("PUT", T, 200, when=base + 6)]
    events.append(lc.Tick(base + W + 1, "w1"))
    events += [
        _rec("GET", f"{CAT}/c1/namespaces/ns1/views/v1", 200, when=base + W + 5),
        _rec("DELETE", T, 204, when=base + W + 6),
    ]
    events.append(lc.Tick(base + 2 * W + 1, "w2"))
    _, reports = policy.run(events)

    merged = lc.merge_windows([reports["w1"], reports["w2"]])
    assert lc.check_invariants(merged, merged=True) == []
    s = [r for r in merged if r["report_type"] == "summary"][0]
    assert s["access_seen"] == 4
    #: the table was touched in BOTH windows -- its counts add up, and it is one
    #: row, not two
    tbl = [r for r in merged if r.get("resource") == T]
    assert len(tbl) == 1 and tbl[0]["requests"] == 3
    #: distinct_resources is a cardinality and must NOT be the sum of the two
    #: windows' values (which would double-count the table)
    assert s["distinct_resources"] == 2


def test_merging_does_not_invent_a_key_from_a_carried_zero(policy):
    #: A resource active BEFORE the merged range is echoed at 0 inside it by
    #: zero-carry. It is not a resource this range saw, and counting it would
    #: inflate distinct_resources and put an all-zero row in the diff.
    _, reports = _window(policy, [("GET", T, 200)], silent=2)
    merged = lc.merge_windows([reports["w2"], reports["w3"]])
    assert [r for r in merged if r["report_type"] == "resource"] == []
    assert lc.check_invariants(merged, merged=True) == []


# ---------------------------------------------------------------- reading a run back
#: These cover the harness rather than the filter, and they exist because run 1
#: of v3 shipped a results document whose numbers could not be checked against
#: each other: a management-POST count taken from a truncated display column, a
#: principal column that was a constant, an oracle diff reported as a scalar,
#: and a merged row count nothing reconciled.
def _call(label, method, path, status, principal=None, rid=None):
    return {
        "label": label,
        "method": method,
        "path": path,
        "actual_path": path,
        "api": lc.api_of(path),
        "status": status,
        "principal": principal,
        "request_id": rid,
        "issued_at": 1788511328.0,
    }


LONG_MGMT = f"{MGMT}/catalogs/apiprofile1788511328_cat/catalog-roles"


def test_the_management_post_count_is_not_taken_from_a_truncated_path():
    #: Run 1 reported "Management POSTs kept: 5 of 5". Six were driven and six
    #: were kept: the matrix truncates `path` to its last 58 characters for
    #: printing and the count filtered THAT column, so the cut removed
    #: `/api/management` from this path and dropped the call out of the
    #: numerator and the denominator together -- a fraction that agreed with
    #: itself and was wrong.
    calls = [
        _call("mgmt.create_principal", "POST", f"{MGMT}/principals", 201),
        _call("mgmt.create_catalog_role", "POST", LONG_MGMT, 201),
    ]
    expected = [{"verdict": lc.KEEP}, {"verdict": lc.KEEP}]
    assert len(LONG_MGMT) > 58 and not LONG_MGMT[-58:].startswith(lc.MGMT_PREFIX)
    stats = lc.mgmt_post_stats(calls, expected)
    assert (stats["driven"], stats["kept"]) == (2, 2)
    assert [r[0] for r in stats["rows"]] == [c["label"] for c in calls]


def test_a_management_post_that_errored_is_not_evidence_for_the_management_rule():
    #: First match wins and the error rule is matched first, so a 403 on
    #: `reset` is kept whatever rule 5 does. Counting it as proof that
    #: management POSTs are kept overstates what the run drove.
    calls = [
        _call("mgmt.create_principal", "POST", f"{MGMT}/principals", 201),
        _call("mgmt.reset", "POST", f"{MGMT}/principals/p/reset", 403),
    ]
    stats = lc.mgmt_post_stats(calls, [{"verdict": lc.KEEP}] * 2)
    assert stats["kept"] == 2
    assert (stats["kept_2xx"], stats["kept_error"]) == (1, 1)


def test_the_principal_is_read_off_the_request_and_not_assumed():
    #: The matrix's `principal_row` was a single constant for all 132 calls of
    #: run 1, while the management block went out as root and the 403 as
    #: nb_<run>_denied. A column that cannot disagree with the run cannot catch
    #: a mis-attribution, and the per-principal margin is the only self-check
    #: the report schema has.
    class _Client:
        def __init__(self, token):
            self.token = token

    class _Resp:
        def __init__(self, token):
            hdr = {"Authorization": f"Bearer {token}"}
            self.request = type("R", (), {"headers": hdr})()

    reg = lc.principal_registry(
        [(_Client("tok-root"), "root"), ("tok-nb", "nb_principal")]
    )
    assert lc.principal_of(_Resp("tok-root"), reg) == "root"
    assert lc.principal_of(_Resp("tok-nb"), reg) == "nb_principal"
    #: an unknown token is not silently attributed to anyone
    assert lc.principal_of(_Resp("tok-other"), reg, default="-") == "-"
    #: and the registry never carries the credential itself
    assert not any("tok-" in k for k in reg)


def test_counted_where_names_the_row_that_actually_moved():
    #: `resource_row` is where a call lands IF IT SUCCEEDS. An error on a
    #: resource nobody read successfully passes create=false and increments
    #: __other__ instead, so for a 4xx the classified key is a counterfactual.
    keys = {T: (T, "table"), f"{CAT}/c1/namespaces/ns1/tables/gone": (None, None)}
    rows = [
        {"report_type": "summary"},
        {"report_type": "resource", "resource": T, "requests": 3},
        {"report_type": "resource", "resource": lc.REPORT_OTHER, "requests": 1},
    ]
    calls = [
        _call("ok", "GET", T, 200),
        _call("missing", "GET", f"{CAT}/c1/namespaces/ns1/tables/gone", 404),
        _call("never issued", "GET", T, None),
    ]
    assert lc.counted_where(calls, keys, rows) == [T, lc.REPORT_OTHER, ""]
    #: with no __other__ row in the report there is nowhere for the error to
    #: have gone, and that is worth saying rather than guessing
    assert lc.counted_where(calls[1:2], keys, rows[:2]) == ["ABSENT"]


def test_the_merged_row_count_is_reconciled_against_the_calls_that_explain_it():
    #: Run 1 reported `merged rows: 49` for a run with 30 distinct resource
    #: keys and 4 error-only ones -- about fifteen rows unaccounted for -- and
    #: nothing in the document compared the two numbers.
    keys = {T: (T, "table")}
    rows = [
        {"report_type": "summary"},
        {"report_type": "resource", "resource": T, "requests": 2},
        {
            "report_type": "resource",
            "resource": "/api/catalog/v1/someone_else",
            "requests": 9,
        },
        {"report_type": "resource", "resource": lc.REPORT_OTHER, "requests": 1},
        {"report_type": "principal", "user_principal_name": "nb_p", "requests": 3},
    ]
    r = lc.reconcile_merged_rows(
        rows, [_call("ok", "GET", T, 200), _call("bad", "GET", T, 404)], keys
    )
    assert r["unexplained"] == ["/api/catalog/v1/someone_else"]
    assert r["missing"] == []
    assert r["counts"] == {
        "summary": 1,
        "resource": 3,
        "principal": 1,
        "total": 5,
        "resource_expected": 2,
    }


def test_volume_reconciles_to_the_records_actually_pulled():
    #: 2,117 records reported, 2,109 attributable in the matrix, and eight
    #: records that belonged to neither column. `app_lines` is
    #: len(found) - len(access) from the same pull, so the two figures agree by
    #: construction unless something is unattributed -- name it instead.
    calls = [_call("a", "GET", T, 200, rid="nb-7-001-a")]
    stored = [
        {"mdc.requestId": "nb-7-001-a"},
        {"mdc.requestId": "nb-7-999-setup"},
        {"loggerName": "org.apache.iceberg"},
    ]
    v = lc.reconcile_volume(stored, calls, run="7")
    assert (v["attributed"], v["run_other"], v["untagged"]) == (1, 1, 1)
    assert v["reconciles"] and v["total"] == 3


def test_two_principals_make_the_margin_something_other_than_a_tautology(policy):
    #: `sum(principal.requests) == access_seen - parse_errors` is the schema's
    #: only real self-check, and with ONE principal it is satisfied identically
    #: by a global counter: the single row IS the run total, so a filter that
    #: attributed nothing would still pass. PLAN 6.2 asks for two principals
    #: with different mixes for exactly this reason; run 1 drove one.
    recs = [_rec("GET", T, 200, user="reader") for _ in range(4)]
    recs += [_rec("POST", T, 200, user="writer") for _ in range(2)]
    _, reports = policy.report_windows(recs, silent_windows=0)
    rows = reports["w1"]
    mix = lc.principal_mix(rows)
    assert set(mix) == {"reader", "writer"}
    summary = [r for r in rows if r["report_type"] == "summary"][0]
    total = sum(v["requests"] for v in mix.values())
    net = lc._as_int(summary["access_seen"]) - lc._as_int(summary["parse_errors"])
    assert total == net
    #: the point: neither row equals the total, so the equality has content
    assert all(0 < v["requests"] < total for v in mix.values())
    assert mix["reader"]["reads"] == 4 and mix["writer"]["writes"] == 2


def test_the_named_assertions_state_what_run_one_left_implied(policy):
    #: `/metrics` folding onto its table is the v2 two-rows-per-table bug
    #: staying fixed, and no results document has ever said so. Same for
    #: resources_other and for response_bytes taking both values.
    recs = [
        _rec("GET", T, 200, size=1200),
        _rec("POST", f"{T}/metrics", 204),
        _rec("GET", f"{CAT}/c1/namespaces/ns1/tables/never_read", 404),
    ]
    _, reports = policy.report_windows(recs, silent_windows=0)
    rows = reports["w1"]
    named = dict((n, ok) for n, ok, _ in lc.named_assertions(rows))
    assert named["no /metrics row (it folds onto its table; v2 emitted two)"] is True
    assert named["resources_other > 0 (an error never creates a resource key)"] is True
    assert named["response_bytes takes both a zero and a non-zero value"] is True


def test_a_named_assertion_fails_loudly_rather_than_reading_as_absent():
    #: A row for the /metrics PATH is the v2 bug returning, and it has to come
    #: back as FAIL rather than as a missing line nobody notices.
    rows = [
        {"report_type": "summary", "resources_other": 0},
        {
            "report_type": "resource",
            "resource": f"{T}/metrics",
            "requests": 1,
            "response_bytes": 0,
        },
    ]
    named = dict((n, ok) for n, ok, _ in lc.named_assertions(rows))
    assert named["no /metrics row (it folds onto its table; v2 emitted two)"] is False
    assert named["resources_other > 0 (an error never creates a resource key)"] is False


def test_victorialogs_own_fields_are_not_counted_as_diff_mismatches():
    #: `_stream` and `_stream_id` are added by VictoriaLogs on the way out. The
    #: filter never emitted them, so the oracle cannot have them, and every
    #: stored row was contributing two guaranteed mismatches -- 34 of the 60
    #: fixture mismatches listed for run 1788744260, which is most of why that
    #: number looked like a pipeline disagreement. `check_invariants` was fixed
    #: for exactly this on 2026-09-04 and `diff_reports` was not.
    exp = [{"report_type": "resource", "resource": T, "requests": 3}]
    act = [
        {
            "report_type": "resource",
            "resource": T,
            "requests": 3,
            "_stream": '{app="polaris-shipper-report"}',
            "_stream_id": "0000000000000000d209",
        }
    ]
    assert lc.report_mismatches(lc.diff_reports(exp, act)) == []
    #: and the exclusion must not swallow a real difference on the same row
    act[0]["requests"] = 4
    fields = {m["field"] for m in lc.report_mismatches(lc.diff_reports(exp, act))}
    assert fields == {"requests"}


def test_the_record_time_bracket_is_the_window_range_not_the_wall_clock():
    #: `min`/`max_record_time` are the timestamps of the records the WINDOWS
    #: saw. The merged range runs to the last window's boundary, which is
    #: always after the notebook captured RUN_END, and opens before STARTED --
    #: so bracketing them against the run's own clock asserts when a human
    #: pressed run. Run 1788744260 failed it that way: max 01:25:18Z against a
    #: RUN_END seconds earlier, inside a window closing at 01:25:30Z.
    summary = {
        "report_type": "summary",
        "window_start": "2026-09-07T01:24:00Z",
        "window_end": "2026-09-07T01:25:30Z",
        "min_record_time": "2026-09-07T01:24:02.771243337Z",
        "max_record_time": "2026-09-07T01:25:18.079449696Z",
        "resources_other": 1,
    }
    label = "min/max_record_time fall inside the merged window range"
    named = dict((n, ok) for n, ok, _ in lc.named_assertions([summary], summary))
    assert named[label] is True
    #: a record stamped outside the windows it is summarised in IS drift
    late = dict(summary, max_record_time="2026-09-07T01:25:41Z")
    named = dict((n, ok) for n, ok, _ in lc.named_assertions([late], late))
    assert named[label] is False
    #: and a quiet window, which VictoriaLogs stores without the fields at all,
    #: is neither
    quiet = dict(summary, min_record_time="", max_record_time="")
    named = dict((n, ok) for n, ok, _ in lc.named_assertions([quiet], quiet))
    assert named[label] is None


def test_correlation_counts_only_the_calls_it_claims_to():
    #: Run 1788745242 reported "147 distinct ids recovered from 146 calls" --
    #: more ids than calls. The numerator counted every run-minted id in the
    #: pull, including cell 1's correlation probe, which is deliberately not in
    #: ALL_CALLS; the denominator counted the calls. A ratio whose halves come
    #: from different populations cannot be read literally, and correlation is
    #: what the whole per-call matrix rests on.
    calls = [
        _call("a", "GET", T, 200, rid="nb-9-001-a"),
        _call("b", "GET", T, 200, rid="nb-9-002-b"),
        _call("timed out", "GET", T, None),
    ]
    stored = [
        {"mdc.requestId": "nb-9-001-a"},
        {"mdc.requestId": "nb-9-000-probe"},
        {"loggerName": "x"},
    ]
    c = lc.correlation_stats(stored, calls)
    assert c["calls"] == 3 and c["with_id"] == 2
    assert c["recovered"] == 1
    assert c["missing"] == ["nb-9-002-b"]
    #: the probe's id is counted apart rather than inflating the numerator
    assert c["other_ids"] == 1


def test_a_structured_exception_is_found_whatever_the_store_called_it():
    #: THE MISTAKE THIS EXISTS FOR. On 2026-09-07 the run reported "0 of 5
    #: WARN/ERROR records carried an exception object" and `grep -c stackTrace`
    #: on the source log returned 0, and the two were read as corroborating
    #: each other. They were the same error twice: this build emits Quarkus's
    #: STRUCTURED exception output -- an object with a `frames` array of
    #: {class, method, line} -- so there is no `stackTrace` string to grep for,
    #: and `"exception" in record` fails once a store flattens the object.
    nested = {
        "level": "ERROR",
        "exception": {
            "exceptionType": "java.lang.NullPointerException",
            "frames": [{"class": "C", "method": "m", "line": 1}],
        },
    }
    flattened = {
        "level": "ERROR",
        "exception.exceptionType": "java.lang.NullPointerException",
        "exception.frames": '[{"class": "C"}]',
    }
    assert lc.exception_fields(nested) == ["exception"]
    assert lc.exception_fields(flattened) == [
        "exception.exceptionType",
        "exception.frames",
    ]
    #: the `formatted` output type puts the trace in a value, not a named field
    formatted = {
        "level": "ERROR",
        "_msg": "boom\n\tat org.apache.polaris.C.m(C.java:1)",
    }
    assert lc.exception_fields(formatted) == ["_msg (formatted trace in the value)"]
    #: and a message that merely mentions one is not a trace
    assert lc.exception_fields({"_msg": "Unhandled exception returning 500"}) == []
    assert lc.exception_fields(None) == []


# ---------------------------------------------------------------- coverage: 500 error
#: The ERROR path had never been driven on purpose: `neg.500_null_pointer`
#: returned 200 for three runs running, and the only 500s ever stored came from
#: the PG-HA read-after-write failures -- writes that COMMITTED, and therefore
#: no evidence at all about unhandled exceptions. These tests are deliberately
#: split: the two oracle ones need Lua, and the rest are pure Python so the
#: honest-failure contract can be checked without a cluster, a drive, or a
#: window boundary to wait for.
def test_a_500_is_kept_and_also_counted(policy):
    #: BOTH, and the "and" is the point. Rule 3 keeps it; every access-log
    #: record is COUNTED before any keep/drop decision is taken, so the same
    #: record moves `access_seen` and the row's `errors`. `access_counted` is
    #: the notebook's other sense of the word -- records that left no
    #: individual trace -- and a kept 500 is not one of those.
    verdicts, reports = _window(policy, [("POST", T, 500)] * 3)
    assert [v["verdict"] for v in verdicts].count("keep") == 3
    summary = [r for r in reports["w1"] if r["report_type"] == "summary"][0]
    assert summary["access_seen"] == 3
    assert summary["access_kept"] == 3
    assert summary["access_counted"] == 0
    assert summary["errors_kept"] == 3


def test_an_application_error_line_is_kept_and_counted_into_no_window(policy):
    #: The other half of a 500. It is not an access-log record, so rule 2 hands
    #: it to rule 1: kept, and invisible to every counter -- which is why a
    #: check that reads only the summary can pass while the half carrying the
    #: stack trace is missing.
    err = lc.app_log_record(
        "Unhandled exception returning INTERNAL_SERVER_ERROR",
        level="ERROR",
        logger="org.apache.polaris.service.catalog.iceberg.IcebergCatalogHandler",
    )
    verdicts, reports = policy.report_windows([err])
    #: `report_windows` returns predict()-shaped dicts, not bare verdicts --
    #: `Policy.verdicts` is the one that flattens them.
    assert [v["verdict"] for v in verdicts] == ["keep"]
    summary = [r for r in reports["w1"] if r["report_type"] == "summary"][0]
    assert summary["access_seen"] == 0
    assert not [r for r in reports["w1"] if r["report_type"] == "resource"]


def test_a_500_on_an_unread_resource_never_creates_a_key(policy):
    #: The 404 case is already covered; this is the 5xx one, and it matters
    #: more here because section 5c's provoker fails on CREATE -- so the table
    #: it names has never been read successfully and must not become a key.
    _, reports = _window(
        policy, [("POST", f"{CAT}/c1/namespaces/ns1/tables/bh_tbl_0", 500)] * 3
    )
    keys = {r["resource"] for r in reports["w1"] if r["report_type"] == "resource"}
    assert keys == {lc.REPORT_OTHER}


def test_classify_500_never_folds_an_accident_into_coverage():
    #: THE SUBSTITUTION THIS EXISTS TO STOP. The PG-HA read-after-write 500s
    #: are writes that committed -- on 2026-09-01 `load_view`, `head_view` and
    #: `drop_view` all answered 2xx after one -- so counting them as ERROR-path
    #: coverage claims a measurement nobody took. Anything unrecognised is
    #: `unknown`, not folded into either bucket: an unexplained 500 is a
    #: finding.
    calls = [
        _call(
            f"{lc.DELIBERATE_500_PREFIX}black_hole_endpoint.create_table_0",
            "POST",
            T,
            500,
        ),
        _call("iceberg.create_namespace", "POST", f"{CAT}/c1/namespaces", 500),
        _call("iceberg.create_view", "POST", f"{CAT}/c1/namespaces/ns1/views", 500),
        _call("mgmt.something_new", "POST", f"{MGMT}/principals", 500),
        _call("iceberg.load_table", "GET", T, 200),
        _call("neg.404", "GET", T, 404),
    ]
    got = lc.classify_500s(calls)
    assert [c["label"] for c in got["deliberate"]] == [
        f"{lc.DELIBERATE_500_PREFIX}black_hole_endpoint.create_table_0"
    ]
    assert len(got["read_after_write"]) == 2
    assert [c["label"] for c in got["unknown"]] == ["mgmt.something_new"]
    #: a 2xx and a 4xx are not 500s and appear in none of the three
    assert sum(len(v) for v in got.values()) == 4


def test_error_record_pair_splits_the_two_halves_and_finds_a_flattened_trace():
    stored = [
        {
            "mdc.requestId": "nb-1-001-x",
            "loggerName": lc.ACCESS_LOGGER,
            "http_status": "500",
        },
        {
            "mdc.requestId": "nb-1-001-x",
            "level": "ERROR",
            "loggerName": "o.a.p.IcebergCatalogHandler",
            "exception.frames": '[{"class": "C"}]',
        },
        {"mdc.requestId": "nb-1-002-y", "loggerName": lc.ACCESS_LOGGER},
    ]
    pair = lc.error_record_pair(stored, "nb-1-001-x")
    assert pair["access_records"] == 1 and pair["app_records"] == 1
    assert pair["levels"] == ["ERROR"]
    #: FLATTENED. `exception` alone matches nothing here, and asking only for
    #: it is what produced "no stack traces" twice, in agreement with itself.
    assert pair["exception_fields"] == {
        "o.a.p.IcebergCatalogHandler": ["exception.frames"]
    }
    #: the other call's records are not swept in
    assert lc.error_record_pair(stored, "nb-1-002-y")["app_records"] == 0


class _FakeProv:
    """A rung with no cluster behind it: statuses are handed in."""

    def __init__(self, name, statuses, fail_setup=False):
        self.name = name
        self.why = "test"
        self.assumed = True
        self.statuses = statuses
        self.prepared = self.cleaned = 0
        self._fail = fail_setup

    def prepare(self):
        self.prepared += 1
        if self._fail:
            raise RuntimeError("no catalog for you")

    def calls(self):
        return [
            (f"c{i}", (lambda: None), "POST", "/p") for i in range(len(self.statuses))
        ]

    def cleanup(self):
        self.cleaned += 1


def _fake_call(statuses):
    it = iter(statuses)

    def call(clients, run, seq, label, fn, method="", path="", principals=None):
        return {
            "label": label,
            "method": method,
            "path": path,
            "seq": seq,
            "status": next(it),
            "request_id": f"nb-{run}-{seq:03d}",
        }

    return call


def test_drive_500_reports_not_provoked_rather_than_inventing_coverage():
    #: THE HONEST-FAILURE CONTRACT. A ladder that fires on nothing must say so.
    #: The alternative is what shipped for three runs: a probe returning 200,
    #: a report reading "0 of 0 records carried an exception object", and a
    #: reader taking that for a statement about the pipeline.
    rungs = [_FakeProv("a", [200, 200]), _FakeProv("b", [201, 200])]
    out = lc.drive_500([], "9", 0, rungs, call=_fake_call([200, 200, 201, 200]))
    assert out["winner"] is None
    assert [e["provoked"] for e in out["ladder"]] == [0, 0]
    assert all(r.cleaned == 1 for r in rungs)
    assert not lc.classify_500s(out["rows"])["deliberate"]


def test_drive_500_stops_at_the_first_rung_that_actually_fires():
    rungs = [_FakeProv("a", [200]), _FakeProv("b", [500, 500]), _FakeProv("c", [500])]
    out = lc.drive_500([], "9", 10, rungs, call=_fake_call([200, 500, 500]))
    assert out["winner"] == "b"
    #: the third rung is never prepared -- a rung that did not run left nothing
    #: behind to clean up, and cleanup on a rung that did run always happens
    assert (rungs[2].prepared, rungs[2].cleaned) == (0, 0)
    assert rungs[1].cleaned == 1
    assert out["seq"] == 13
    assert len(lc.classify_500s(out["rows"])["deliberate"]) == 2


def test_drive_500_survives_a_rung_whose_setup_fails():
    #: A rung whose catalog cannot be created is a rung that did not get to
    #: answer, not a rung that answered "no". It is recorded and the ladder
    #: continues.
    rungs = [_FakeProv("a", [500], fail_setup=True), _FakeProv("b", [500])]
    out = lc.drive_500([], "9", 0, rungs, call=_fake_call([500]))
    assert out["ladder"][0]["calls"] == 0
    assert out["ladder"][0]["note"].startswith("setup: RuntimeError")
    assert out["winner"] == "b"


def _sum_row(**kw):
    row = {
        "report_type": "summary",
        "errors": 0,
        "errors_4xx": 0,
        "errors_5xx": 0,
        "auth_denied": 0,
    }
    row.update(kw)
    return row


def test_check_500_window_is_void_not_green_on_a_schema_v1_window():
    #: ABSENT IS NOT ZERO. A v1 window carries no error split at all, and a
    #: check that reads a missing field as 0 reports PASS for a measurement
    #: nobody took -- the same shape as "0 of 0 carried an exception object".
    v1 = [{"report_type": "summary", "access_seen": 5, "errors_kept": 1}]
    got = lc.check_500_window(v1, driven_500=3)
    assert [ok for _, ok, _ in got] == [None]
    assert "VOID" in got[0][2]


def test_check_500_window_catches_a_500_charged_to_the_4xx_counter():
    #: The negative case, and the reason the 4xx check is an EQUALITY. A filter
    #: that put the 500 in `errors_4xx` would still satisfy `errors_5xx >= 0`
    #: and every total in the report.
    rows = [_sum_row(errors=3, errors_4xx=3, errors_5xx=0)]
    named = {n: ok for n, ok, _ in lc.check_500_window(rows, driven_500=3)}
    assert named["a 500 does not increment errors_4xx"] is False
    assert named["errors_5xx >= the 3 driven 500(s)"] is False


def test_check_500_window_passes_a_clean_pure_500_burst():
    rows = [
        _sum_row(errors=3, errors_4xx=0, errors_5xx=3, auth_denied=0),
        {
            "report_type": "resource",
            "resource": lc.REPORT_OTHER,
            "errors": 3,
            "errors_5xx": 3,
        },
        {
            "report_type": "principal",
            "user_principal_name": "nb_p",
            "errors": 3,
            "errors_5xx": 3,
        },
    ]
    got = lc.check_500_window(rows, driven_500=3)
    assert all(ok for _, ok, _ in got), [c for c in got if not c[1]]


def test_check_500_window_allows_a_neighbours_500_but_not_a_neighbours_4xx():
    #: The asymmetry, stated as a test. Neighbour traffic and an accidental
    #: PG-HA 500 land in the same window and can only ADD to `errors_5xx`;
    #: nothing this notebook drove can add a 4xx to a pure-500 burst, so an
    #: inequality there would pass a filter charging the 500 to the wrong
    #: counter.
    rows = [_sum_row(errors=5, errors_4xx=0, errors_5xx=5)]
    named = {n: ok for n, ok, _ in lc.check_500_window(rows, driven_500=3)}
    assert named["errors_5xx >= the 3 driven 500(s)"] is True
    assert named["a 500 does not increment errors_4xx"] is True

    rows = [_sum_row(errors=5, errors_4xx=2, errors_5xx=3)]
    named = {n: ok for n, ok, _ in lc.check_500_window(rows, driven_500=3)}
    assert named["a 500 does not increment errors_4xx"] is False


def test_check_500_window_margin_is_void_when_no_row_carries_the_field():
    #: A margin computed over rows that do not carry the counter is `0 == 0`,
    #: which is a pass nobody earned.
    rows = [
        _sum_row(errors=1, errors_5xx=1),
        {"report_type": "resource", "resource": "r", "errors": 1},
        {"report_type": "principal", "user_principal_name": "p", "errors": 1},
    ]
    named = {n: (ok, d) for n, ok, d in lc.check_500_window(rows, driven_500=1)}
    assert (
        named["margin: sum(resource.errors_5xx) == sum(principal.errors_5xx)"][0]
        is None
    )
    assert named["margin: sum(resource.errors) == sum(principal.errors)"][0] is True


def test_provokers_500_refuses_to_guess_a_table_payload():
    with pytest.raises(ValueError, match="table_payload"):
        lc.provokers_500(None, None, "9", bucket="b", endpoint="e")


def test_the_ladder_points_both_storage_endpoints_at_the_black_hole():
    #: WHY `error-cases/09` STOPPED WORKING, encoded so it cannot regress:
    #: it omitted `endpointInternal` only, and this build falls back to
    #: `endpoint`. A rung that leaves a working endpoint in place is a rung
    #: that provokes nothing and reports 200 forever.
    seen = {}

    class _PC:
        def create_catalog(self, name, bucket, endpoint, minio_endpoint_internal=None):
            seen.update(
                name=name,
                endpoint=endpoint,
                internal=minio_endpoint_internal,
                bucket=bucket,
            )
            return type("R", (), {"status_code": 201, "text": ""})()

        def delete_catalog(self, name, purge=False):
            seen["purge"] = purge
            return type("R", (), {"status_code": 204})()

    class _IC:
        def create_namespace(self, catalog, ns):
            return type("R", (), {"status_code": 200})()

    rungs = lc.provokers_500(
        _PC(),
        _IC(),
        "9",
        bucket="b",
        endpoint="http://real:9000",
        table_payload=lambda n: {"name": n},
        repeat=3,
    )
    assert rungs[0].name == "black_hole_endpoint"
    rungs[0].prepare()
    assert seen["endpoint"] == seen["internal"] != "http://real:9000"
    assert len(rungs[0].calls()) == 3
    rungs[0].cleanup()
    #: purge=False deliberately: purging talks to the endpoint this rung just
    #: pointed at a dead port, so it hangs or provokes a second untagged 500.
    assert seen["purge"] is False


# ---------------------------------------------------------------- report schema v2
#: PLAN-log-coverage-schema-v2 sections 1.1-1.4. These are the NEGATIVES: v1 could
#: produce the right total while attributing it to the wrong bucket, and only a
#: test that asks where a count landed catches that.
def test_no_row_carries_a_field_called_counted_get(policy):
    #: THE RENAME, not the value. `counted_get` counted GET *and* HEAD, so it
    #: undercounted by its own definition; v2 renames it to `counted_read`. A
    #: harness that still reads `counted_get` gets 0 or a KeyError, and 0 is the
    #: dangerous one.
    _, reports = _window(policy, [("GET", T, 200), ("HEAD", T, 200)])
    assert not [r for r in reports["w1"] if "counted_get" in r]
    s = [r for r in reports["w1"] if r["report_type"] == "summary"][0]
    assert s["counted_read"] == 2


def test_counted_read_counts_head_as_well_as_get(policy):
    _, reports = _window(
        policy,
        [("GET", T, 200), ("GET", T, 200), ("HEAD", T, 200), ("POST", T, 200)],
    )
    s = [r for r in reports["w1"] if r["report_type"] == "summary"][0]
    assert (s["counted_read"], s["counted_post"]) == (3, 1)


def test_the_error_split_charges_each_status_to_exactly_one_half(policy):
    #: 401 and 403 increment auth_denied AND errors_4xx -- denial is a KIND of
    #: client error, not an alternative to it. A 5xx increments neither.
    _, reports = _window(
        policy,
        [
            ("GET", T, 200),  # read it first, so the key exists
            ("GET", T, 401),
            ("GET", T, 403),
            ("GET", T, 404),
            ("GET", T, 500),
        ],
    )
    s = [r for r in reports["w1"] if r["report_type"] == "summary"][0]
    assert s["errors_4xx"] == 3
    assert s["errors_5xx"] == 1
    assert s["auth_denied"] == 2
    row = [r for r in reports["w1"] if r.get("resource") == T][0]
    assert (row["errors"], row["errors_4xx"], row["errors_5xx"]) == (4, 3, 1)
    assert row["auth_denied"] == 2
    assert lc.check_invariants(reports["w1"]) == []


def test_an_unparsed_status_is_an_error_charged_to_neither_half(policy):
    #: `count_record` increments `errors` and returns. Charging it to
    #: `errors_4xx` would make "client errors" absorb the pipeline's own
    #: failures, which is why the invariant is an INEQUALITY.
    W = policy.window_seconds
    broken = lc.app_log_record("x")
    broken["loggerName"] = lc.ACCESS_LOGGER
    broken["_msg"] = "this line does not match the access-log pattern at all"
    events = [lc.Tick(1, "open"), broken, lc.Tick(W + 1, "w1")]
    _, reports = policy.run(events)
    s = [r for r in reports["w1"] if r["report_type"] == "summary"][0]
    assert s["parse_errors"] >= 1
    assert s["errors_4xx"] == 0 and s["errors_5xx"] == 0
    assert lc.check_invariants(reports["w1"]) == []


def test_an_idle_window_reports_zero_distinct_resources_and_says_what_it_carried(
    policy,
):
    #: THE v1 DEFECT, and the single most important assertion in schema v2.
    #: v1's `distinct_resources` was the number of rows EMITTED, which includes
    #: zero-carry rows -- so a window with no traffic at all reported two
    #: distinct resources and a dashboard built on it showed steady activity
    #: through a total outage.
    _, reports = _window(policy, [("GET", T, 200)], silent=1)
    idle = reports["w2"]
    s = [r for r in idle if r["report_type"] == "summary"][0]
    assert s["access_seen"] == 0
    assert s["distinct_resources"] == 0
    assert s["distinct_principals"] == 0
    #: the rows are still emitted -- that is zero-carry -- and now they are
    #: counted under a name that says so
    assert s["carried_rows"] == len([r for r in idle if r["report_type"] != "summary"])
    assert lc.check_invariants(idle) == []


def test_the_cardinality_rule_closes_against_the_row_count(policy):
    _, reports = _window(policy, [("GET", T, 200), ("GET", T, 403)])
    rows = reports["w1"]
    s = [r for r in rows if r["report_type"] == "summary"][0]
    assert (
        s["distinct_resources"] + s["distinct_principals"] + s["carried_rows"]
        == len(rows) - 1
    )


def test_every_v2_margin_counter_is_reconciled_across_both_row_sets(policy):
    #: NEW CAPABILITY, not more fields. Under v1 only `requests` was reconciled
    #: across two independently built row sets, so an error attributed to the
    #: wrong principal, or bytes charged to the wrong resource, had nowhere to
    #: show up. Two principals with different mixes, because with one identity
    #: every margin is satisfied by a global counter.
    _, reports = _window(
        policy,
        [("GET", T, 200), ("PUT", T, 200), ("GET", T, 403), ("GET", T, 500)],
        users=["writer", "writer", "reader", "reader"],
    )
    rows = reports["w1"]
    res = [r for r in rows if r["report_type"] == "resource"]
    pri = [r for r in rows if r["report_type"] == "principal"]
    assert len(pri) == 2
    for field in lc.MARGIN_FIELDS:
        assert sum(r[field] for r in res) == sum(r[field] for r in pri), field
    #: and no single principal carries the whole total, or the equality is empty
    assert all(r["requests"] < 4 for r in pri)
    assert lc.check_invariants(rows) == []


def test_the_merge_sums_a_field_this_module_was_never_told_about():
    #: PLAN section 1.1's acceptance test, and the bug it is written against:
    #: `merge_windows` summed a HARDCODED list, so when the filter shipped v2 it
    #: added `errors` and silently did not add `errors_4xx` -- in the same row,
    #: with no exception and a plausible number out. The list is gone; the merge
    #: reads the row. `invented_total` stands for the v3 field nobody has written
    #: yet, and it must merge correctly the day it appears.
    def win(start, end, e4, invented):
        return [
            {
                "report_type": "summary",
                "app": "polaris-shipper-report",
                "level": "REPORT",
                "schema_version": 2,
                "report_seq": 1,
                "hostname": "h",
                "window_start": start,
                "window_end": end,
                "window_seconds": 30,
                "_time": end,
                "_msg": "m",
                "access_seen": 1,
                "access_kept": 1,
                "access_counted": 0,
                "errors": 1,
                "errors_4xx": e4,
                "invented_total": invented,
                "distinct_resources": 1,
                "distinct_principals": 1,
                "carried_rows": 0,
            },
            {
                "report_type": "resource",
                "app": "polaris-shipper-report",
                "level": "REPORT",
                "schema_version": 2,
                "report_seq": 1,
                "hostname": "h",
                "window_start": start,
                "window_end": end,
                "window_seconds": 30,
                "_time": end,
                "_msg": "m",
                "resource": T,
                "resource_kind": "table",
                "requests": 1,
                "reads": 1,
                "writes": 0,
                "errors": e4,
                "errors_4xx": e4,
                "response_bytes": 10,
            },
        ]

    merged = lc.merge_windows(
        [
            win("2026-09-07T00:00:00Z", "2026-09-07T00:00:30Z", 1, 7),
            win("2026-09-07T00:00:30Z", "2026-09-07T00:01:00Z", 25, 11),
        ]
    )
    s = [r for r in merged if r["report_type"] == "summary"][0]
    row = [r for r in merged if r["report_type"] == "resource"][0]
    assert s["errors_4xx"] == 26, "the v2 field that used to be dropped"
    assert row["errors"] == 26 and row["errors_4xx"] == 26, (
        "`errors` merged under the old hardcoded list and `errors_4xx` did not -- "
        "IN THE SAME ROW. Both, or the bug is still here."
    )
    assert s["invented_total"] == 18, "a field this module has never heard of"
    #: and the things that must NOT be added
    assert s["window_seconds"] == 30
    assert s["schema_version"] == 2
    assert s["distinct_resources"] == 1
    assert s["carried_rows"] == 0


def test_the_merge_does_not_add_up_a_principal_whose_name_looks_like_a_number():
    #: `summable_fields` decides on the VALUE, because VictoriaLogs hands every
    #: field back as a string -- so the row's own identity has to be excluded by
    #: NAME or a principal called "42" becomes an addend.
    def win(start, end):
        return [
            {
                "report_type": "principal",
                "app": "polaris-shipper-report",
                "level": "REPORT",
                "schema_version": 2,
                "report_seq": 1,
                "hostname": "h",
                "window_start": start,
                "window_end": end,
                "window_seconds": 30,
                "_time": end,
                "_msg": "m",
                "user_principal_name": "42",
                "requests": "1",
                "reads": "1",
                "writes": "0",
                "errors": "0",
                "response_bytes": "5",
            }
        ]

    rows = win("2026-09-07T00:00:00Z", "2026-09-07T00:00:30Z") + [
        {
            "report_type": "summary",
            "app": "polaris-shipper-report",
            "level": "REPORT",
            "schema_version": 2,
            "report_seq": 1,
            "hostname": "h",
            "window_start": "2026-09-07T00:00:00Z",
            "window_end": "2026-09-07T00:00:30Z",
            "window_seconds": 30,
            "_time": "2026-09-07T00:00:30Z",
            "_msg": "m",
            "access_seen": 1,
        }
    ]
    merged = lc.merge_windows([rows, rows])
    pri = [r for r in merged if r["report_type"] == "principal"][0]
    assert pri["user_principal_name"] == "42"
    assert pri["requests"] == 2
    assert "user_principal_name" not in lc.summable_fields(pri)


def test_windows_skipped_is_never_diffed_against_the_oracle():
    #: It counts boundaries the tick never noticed, which on this cluster means
    #: the OrbStack VM was suspended with the MacBook. No oracle running under
    #: `_now_override` can predict a laptop lid.
    assert "windows_skipped" in lc.VOLATILE_FIELDS
    base = {
        "report_type": "summary",
        "window_start": "2026-09-07T00:00:00Z",
        "access_seen": 1,
    }
    diff = lc.diff_reports(
        [dict(base, windows_skipped=0)], [dict(base, windows_skipped=118)]
    )
    assert not lc.report_mismatches(diff)


def test_the_deployed_schema_version_is_read_and_not_assumed(policy):
    #: The constant drifted once already: the filter shipped v2 while this
    #: module said 1, and the gate's report was eight "unexpected fields" per
    #: row with nothing naming the cause. Cell 0b compares these two.
    assert policy.schema_version == lc.SCHEMA_VERSION


def test_a_handled_500_is_not_reported_as_a_lost_stack_trace():
    #: THE COLLAPSE THIS PREVENTS. Polaris can CATCH a storage failure, map it
    #: to a 500 and log it without attaching the throwable. A check that asks
    #: only "did a trace arrive?" reports that identically to a pipeline that
    #: dropped one -- and the remedies are opposite: change the probe, or fix
    #: the shipper. Three verdicts, and only `absent` accuses the pipeline.
    unhandled = {
        "app_records": 2,
        "exception_fields": {"o.a.p.Handler": ["exception.frames"]},
    }
    handled = {"app_records": 3, "exception_fields": {}}
    absent = {"app_records": 0, "exception_fields": {}}
    assert lc.trace_verdict(unhandled) == lc.TRACE_UNHANDLED
    assert lc.trace_verdict(handled) == lc.TRACE_HANDLED
    assert lc.trace_verdict(absent) == lc.TRACE_ABSENT
    #: a WARN-only line with a throwable is still `unhandled` -- the level is not
    #: the question, the payload is. Rule 2 keeps the line whatever its level.
    warned = {
        "app_records": 1,
        "levels": ["WARN"],
        "exception_fields": {"x": ["exception.exceptionType"]},
    }
    assert lc.trace_verdict(warned) == lc.TRACE_UNHANDLED
    got = lc.trace_verdicts([unhandled, handled, handled, absent])
    assert [
        len(got[k]) for k in (lc.TRACE_UNHANDLED, lc.TRACE_HANDLED, lc.TRACE_ABSENT)
    ] == [1, 2, 1]
    assert lc.trace_verdict(None) == lc.TRACE_ABSENT


def test_the_dns_rung_fails_at_a_different_layer_than_the_black_hole():
    #: Kade's case: a typo in the in-cluster MinIO service name. It is a
    #: SEPARATE rung rather than a different constant for rung 1, because DNS
    #: resolution and TCP connect are different failure layers and the S3
    #: client may handle them in different code paths -- so one can 500 where
    #: the other does not, and a ladder that tried only one would report NOT
    #: PROVOKED while the other rung was sitting there.
    seen = []

    class _PC:
        def create_catalog(self, name, bucket, endpoint, minio_endpoint_internal=None):
            seen.append((name, endpoint, minio_endpoint_internal))
            return type("R", (), {"status_code": 201, "text": ""})()

        def delete_catalog(self, name, purge=False):
            return type("R", (), {"status_code": 204})()

    class _IC:
        def create_namespace(self, catalog, ns):
            return type("R", (), {"status_code": 200})()

    rungs = lc.provokers_500(
        _PC(),
        _IC(),
        "9",
        bucket="b",
        endpoint="http://real:9000",
        endpoint_internal="http://real-internal:9000",
        table_payload=lambda n: {"name": n},
    )
    assert [r.name for r in rungs] == [
        "black_hole_endpoint",
        "unresolvable_host",
        "nonexistent_bucket",
        "stale_entity_version",
    ]
    rungs[1].prepare()
    _, endpoint, internal = seen[-1]
    assert endpoint == internal
    #: RFC 2606 reserves `.invalid`, so the lookup is guaranteed to fail. A
    #: plausible-but-wrong name risks resolving to something real.
    assert ".invalid" in endpoint and "real" not in endpoint
    #: and it is not rung 1's constant wearing a second name
    assert endpoint != "http://127.0.0.1:1"


def test_the_window_negatives_compare_against_what_was_actually_driven():
    #: RUN 1788759324. No rung fired, so the ladder's twelve calls came back
    #: 422/422/400/409 and landed in the very window the checks call a
    #: "pure-500 burst". Against a hardcoded `driven_4xx=0` that printed
    #: `a 500 does not increment errors_4xx: errors_4xx=13, driven 4xx=0` --
    #: the harness's own traffic reported as a fault in the filter.
    ladder = (
        [_call(f"{lc.DELIBERATE_500_PREFIX}bh.t{i}", "POST", T, 422) for i in range(3)]
        + [
            _call(f"{lc.DELIBERATE_500_PREFIX}dns.t{i}", "POST", T, 422)
            for i in range(3)
        ]
        + [
            _call(f"{lc.DELIBERATE_500_PREFIX}bkt.t{i}", "POST", T, 400)
            for i in range(3)
        ]
        + [_call(f"{lc.DELIBERATE_500_PREFIX}sv.p{i}", "PUT", T, 409) for i in range(3)]
        + [_call(f"{lc.DELIBERATE_500_PREFIX}x.denied", "GET", T, 403)]
    )
    mix = lc.driven_status_mix(ladder)
    assert (mix["n_5xx"], mix["n_4xx"], mix["n_auth_denied"]) == (0, 13, 1)

    rows = [
        _sum_row(errors_4xx=13, errors_5xx=1, auth_denied=1),
        {
            "report_type": "resource",
            "resource": lc.REPORT_OTHER,
            "errors": 14,
            "errors_4xx": 13,
            "errors_5xx": 1,
        },
        {
            "report_type": "principal",
            "user_principal_name": "nb_p",
            "errors": 14,
            "errors_4xx": 13,
            "errors_5xx": 1,
        },
    ]
    named = {
        n: ok
        for n, ok, _ in lc.check_500_window(
            rows,
            driven_500=0,
            driven_4xx=mix["n_4xx"],
            driven_auth_denied=mix["n_auth_denied"],
        )
    }
    assert named["a 500 does not increment errors_4xx"] is True
    assert named["a 500 does not increment auth_denied"] is True
    #: and the split check reads the RESOURCE margin, because the summary has no
    #: `errors` field at all -- it has `errors_kept`. Reading the missing name
    #: gave 0 and printed `13 + 1 <= 0  FAIL` for a consistent window.
    assert named["errors_4xx + errors_5xx <= errors"] is True
    #: an extra 4xx that nothing drove is still caught
    named = {
        n: ok for n, ok, _ in lc.check_500_window(rows, driven_500=0, driven_4xx=12)
    }
    assert named["a 500 does not increment errors_4xx"] is False
