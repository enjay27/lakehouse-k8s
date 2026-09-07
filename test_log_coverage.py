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
    assert tick < W, (
        f"Interval_Sec {tick} >= WINDOW_SECONDS {W}: a late tick skips a window"
    )
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
    w2 = {
        r["resource"]: r for r in reports["w2"] if r["report_type"] == "resource"
    }
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
        dict(r, _stream='{app="polaris-shipper-report",level="REPORT"}',
             _stream_id="0000000000000000d2093bd84cc34837")
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
    broken[0].pop("counted_get", None)
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
        {"report_type": "resource", "resource": "/api/catalog/v1/someone_else",
         "requests": 9},
        {"report_type": "resource", "resource": lc.REPORT_OTHER, "requests": 1},
        {"report_type": "principal", "user_principal_name": "nb_p", "requests": 3},
    ]
    r = lc.reconcile_merged_rows(rows, [_call("ok", "GET", T, 200),
                                        _call("bad", "GET", T, 404)], keys)
    assert r["unexplained"] == ["/api/catalog/v1/someone_else"]
    assert r["missing"] == []
    assert r["counts"] == {"summary": 1, "resource": 3, "principal": 1,
                           "total": 5, "resource_expected": 2}


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
        {"report_type": "resource", "resource": f"{T}/metrics", "requests": 1,
         "response_bytes": 0},
    ]
    named = dict((n, ok) for n, ok, _ in lc.named_assertions(rows))
    assert named["no /metrics row (it folds onto its table; v2 emitted two)"] is False
    assert named["resources_other > 0 (an error never creates a resource key)"] is False
