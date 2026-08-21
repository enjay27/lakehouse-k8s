"""Tests for `api_sweep` — the per-API latency grid.

The fakes here are deliberately hostile in two places: `FakeResp` can carry any
status code, and `FakeClock` makes "time" a list the test controls. Both exist
because the failure this module is most likely to have is reporting an error
path or a startup artifact as if it were latency, and a fake that always
returns 200 in zero time cannot catch either.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import api_sweep as sweep  # noqa: E402

FIXTURE = {
    "catalog": "user1_catalog",
    "namespace": "ns1",
    "principal": "user1_principal",
    "principal_role": "user1_principal_role",
    "catalog_role": "owner_principal",
}


class FakeResp:
    def __init__(self, status_code=200, text=""):
        self.status_code = status_code
        self.text = text


class FakePolaris:
    """Answers every read op. `fail` forces one label's call to a status code."""

    def __init__(self, fail=None, code=403):
        self.calls = []
        self.fail = fail
        self.code = code

    def _r(self, what):
        self.calls.append(what)
        if self.fail and what == self.fail:
            return FakeResp(self.code, "not authorized")
        return FakeResp(200)

    def list_principals(self):
        return self._r("list_principals")

    def get_principal(self, n):
        return self._r(f"get_principal:{n}")

    def list_principal_roles(self):
        return self._r("list_principal_roles")

    def get_principal_role(self, n):
        return self._r(f"get_principal_role:{n}")

    def list_principals_for_principal_role(self, n):
        return self._r(f"pr_principals:{n}")

    def list_catalogs(self):
        return self._r("list_catalogs")

    def get_catalog(self, n):
        return self._r(f"get_catalog:{n}")

    def list_catalog_roles(self, c):
        return self._r(f"list_catalog_roles:{c}")

    def list_grants(self, c, r):
        return self._r(f"list_grants:{c}/{r}")

    def list_namespaces(self, c):
        return self._r(f"list_namespaces:{c}")

    def get_namespace(self, c, ns):
        return self._r(f"get_namespace:{c}/{ns}")

    def list_tables(self, c, ns):
        return self._r(f"list_tables:{c}/{ns}")

    def list_views(self, c, ns):
        return self._r(f"list_views:{c}/{ns}")

    def get_token(self, cid, secret):
        return self._r("get_token")


# ----------------------------------------------------------------------
# restart
# ----------------------------------------------------------------------
def _gen_runner(seen, gen=3):
    """A kubectl that answers the generation probes, so tests exercise the
    real ordering instead of dying in int('ok')."""
    state = {"gen": gen, "observed": gen}

    def runner(cmd, timeout):
        seen.append(cmd)
        joined = " ".join(cmd)
        if "observedGeneration" in joined:
            return f"{state['gen']} {state['observed']}"
        if "{.metadata.generation}" in joined:
            return str(state["gen"])
        if "restart" in cmd:
            state["gen"] += 1
            state["observed"] = state["gen"]
            return "restarted"
        return "ok"

    return runner


def test_restart_issues_rollout_then_waits_for_status():
    seen = []
    out = sweep.restart_polaris(runner=_gen_runner(seen))
    kinds = [" ".join(c) for c in seen]
    restart = next(i for i, k in enumerate(kinds) if "rollout restart" in k)
    status = next(i for i, k in enumerate(kinds) if "rollout status" in k)
    assert restart < status
    assert "deploy/benchmarks-polaris" in seen[restart]
    assert "-n" in seen[restart] and "datahub-hynix" in seen[restart]
    assert any(a.startswith("--timeout=") for a in seen[status])
    assert out["seconds"] >= 0


def test_restart_raises_rather_than_measuring_a_half_restarted_deployment():
    inner = _gen_runner([])

    def runner(cmd, timeout):
        if "status" in cmd:
            raise RuntimeError("rollout status: timed out waiting")
        return inner(cmd, timeout)

    with pytest.raises(RuntimeError, match="timed out"):
        sweep.restart_polaris(runner=runner)


def test_missing_kubectl_says_so_plainly():
    def runner(cmd, timeout):
        return sweep._run(["definitely-not-a-real-binary-xyz"], timeout=1)

    with pytest.raises(RuntimeError, match="not found"):
        sweep.restart_polaris(runner=runner)


def test_wait_until_serving_returns_once_polaris_answers():
    answers = [False, False, True]
    out = sweep.wait_until_serving(lambda: answers.pop(0), sleep=lambda _: None)
    assert out["seconds"] >= 0
    assert answers == []


def test_wait_until_serving_tolerates_connection_refused_during_startup():
    state = {"n": 0}

    def probe():
        state["n"] += 1
        if state["n"] < 3:
            raise ConnectionError("connection refused")
        return True

    sweep.wait_until_serving(probe, sleep=lambda _: None)
    assert state["n"] == 3


def test_wait_until_serving_times_out_rather_than_measuring_a_dead_polaris():
    with pytest.raises(TimeoutError):
        sweep.wait_until_serving(
            lambda: False, timeout=0.01, interval=0, sleep=lambda _: None
        )


# ----------------------------------------------------------------------
# the surface
# ----------------------------------------------------------------------
def test_every_operation_targets_the_real_fixture_never_a_clone():
    """The clones are load, not targets. A read op aimed at one would be timing
    a row with no storage behind it."""
    pc = FakePolaris()
    for label, surface, fn in sweep.read_operations(FIXTURE):
        fn(pc)
    joined = " ".join(pc.calls)
    assert "sqlclone" not in joined
    assert "user1_catalog" in joined


def test_the_surface_covers_both_rest_surfaces():
    surfaces = {s for _, s, _ in sweep.read_operations(FIXTURE)}
    assert surfaces == {"mgmt", "iceberg"}


def test_no_write_operation_is_in_the_measured_set():
    """A write mutates the tables whose row counts define the cell — it would
    move the independent variable mid-measurement."""
    for label, _, _ in sweep.read_operations(FIXTURE):
        assert label.startswith("GET"), label


# ----------------------------------------------------------------------
# refusing to time an error path
# ----------------------------------------------------------------------
@pytest.mark.parametrize("code", [400, 401, 403, 404, 500, 503])
def test_a_non_2xx_is_never_recorded_as_latency(code):
    with pytest.raises(AssertionError, match="error path"):
        sweep.assert_ok("GET /catalogs", FakeResp(code, "boom"))


def test_2xx_passes_through():
    assert sweep.assert_ok("GET /catalogs", FakeResp(204)) == 204


def test_cold_measurement_refuses_a_failing_api():
    pc = FakePolaris(fail="get_catalog:user1_catalog")
    ops = sweep.read_operations(FIXTURE)
    with pytest.raises(AssertionError, match="error path"):
        sweep.measure_cold(pc, ops)


def test_warm_measurement_checks_before_it_times():
    """The check must come BEFORE timeit, so a 403 costs one call, not 17."""
    pc = FakePolaris(fail="list_principals")
    with pytest.raises(AssertionError):
        sweep.measure_warm(pc, sweep.read_operations(FIXTURE), k=2, warmup=1)
    assert pc.calls.count("list_principals") == 1


# ----------------------------------------------------------------------
# measurement shape
# ----------------------------------------------------------------------
def test_cold_is_one_call_per_api_and_says_so():
    pc = FakePolaris()
    out = sweep.measure_cold(pc, sweep.read_operations(FIXTURE))
    assert len(out) == len(sweep.read_operations(FIXTURE))
    for label, rec in out.items():
        assert rec["n"] == 1, f"{label} claims a sample size cold cannot have"
        assert rec["cold"] is True
        assert "min" not in rec and "max" not in rec  # no spread on n=1


def test_warm_carries_a_spread_and_a_real_sample_size():
    pc = FakePolaris()
    out = sweep.measure_warm(pc, sweep.read_operations(FIXTURE), k=3, warmup=1)
    for rec in out.values():
        assert rec["n"] == 3 and rec["cold"] is False
        assert rec["min"] <= rec["ms"] <= rec["max"]


def test_warm_up_targets_the_decoy_and_never_the_measured_catalog():
    pc = FakePolaris()
    sweep.warm_up(pc, "decoy_catalog", rounds=3)
    assert "get_catalog:decoy_catalog" in pc.calls
    assert "get_catalog:user1_catalog" not in pc.calls


def test_warm_up_survives_a_broken_decoy():
    """A decoy failure must not abort a sweep — it is scaffolding, not data."""

    class Broken(FakePolaris):
        def get_catalog(self, n):
            raise ConnectionError("decoy is gone")

    sweep.warm_up(Broken(), "decoy", rounds=2)


# ----------------------------------------------------------------------
# the grid
# ----------------------------------------------------------------------
def _grid(volumes=(0, 100), index_states=(False, True), **kw):
    log = []

    def ops_for(pc):
        return sweep.read_operations(FIXTURE), "decoy_catalog", ("root", "secret")

    cells = sweep.run_sweep(
        volumes=list(volumes),
        index_states=list(index_states),
        apply_volume=lambda n: (log.append(("volume", n)), {"clones": n})[1],
        apply_index=lambda p: (log.append(("index", p)), {"present": p})[1],
        restart=lambda: (log.append(("restart",)), {"seconds": 1.0})[1],
        connect=lambda: FakePolaris(),
        ops_for=ops_for,
        k=2,
        warmup=1,
        **kw,
    )
    return cells, log


def test_grid_covers_every_combination():
    cells, _ = _grid()
    assert {(c["clones"], c["index"]) for c in cells} == {
        (0, False),
        (0, True),
        (100, False),
        (100, True),
    }


def test_volume_is_the_outer_loop_because_it_is_the_expensive_one():
    _, log = _grid()
    volume_changes = [e for e in log if e[0] == "volume"]
    assert len(volume_changes) == 2, "volume must not be re-applied per index cell"


def test_one_restart_per_cell_is_what_makes_cold_cold():
    cells, log = _grid()
    assert len([e for e in log if e[0] == "restart"]) == len(cells)


def test_index_is_toggled_before_the_restart_not_after():
    """Toggling after the restart would warm the cache the cold sample needs."""
    _, log = _grid(volumes=(0,), index_states=(True,))
    kinds = [e[0] for e in log]
    assert kinds.index("index") < kinds.index("restart")


def test_every_cell_carries_the_control():
    cells, _ = _grid()
    for c in cells:
        assert sweep.CONTROL in c["warm"]
        assert sweep.CONTROL not in c["cold"]


# ----------------------------------------------------------------------
# reading the result
# ----------------------------------------------------------------------
def _cell(clones, index, ms, control=1.0, cold=None):
    api = "GET  /catalogs/{name}"
    return {
        "clones": clones,
        "index": index,
        "volume": {},
        "index_state": {},
        "restart": {},
        "cold": {api: {"surface": "mgmt", "ms": cold or ms * 3, "n": 1, "cold": True}},
        "warm": {
            api: {"surface": "mgmt", "ms": ms, "min": ms, "max": ms, "n": 15},
            sweep.CONTROL: {
                "surface": "auth",
                "ms": control,
                "min": control,
                "max": control,
                "n": 15,
            },
        },
    }


API = "GET  /catalogs/{name}"


def test_index_effect_is_a_within_volume_contrast():
    cells = [
        _cell(0, False, 5.0),
        _cell(0, True, 3.0),
        _cell(100, False, 40.0),
        _cell(100, True, 3.5),
    ]
    rows = sweep.index_effect(cells, API)
    assert [r["clones"] for r in rows] == [0, 100]
    assert rows[0]["delta_ms"] == pytest.approx(2.0)
    assert rows[1]["delta_ms"] == pytest.approx(36.5)


def test_index_effect_skips_a_volume_measured_only_one_way():
    """Half a contrast is not a contrast; emitting it would invent a baseline."""
    cells = [_cell(0, False, 5.0), _cell(0, True, 3.0), _cell(100, False, 40.0)]
    assert [r["clones"] for r in sweep.index_effect(cells, API)] == [0]


def test_volume_effect_holds_the_index_fixed():
    cells = [
        _cell(0, False, 5.0),
        _cell(0, True, 3.0),
        _cell(100, False, 40.0),
        _cell(100, True, 3.5),
    ]
    rows = sweep.volume_effect(cells, API, index=True)
    assert [(r["clones"], r["ms"]) for r in rows] == [(0, 3.0), (100, 3.5)]


def test_control_drift_reports_the_spread_that_bounds_every_claim():
    cells = [_cell(0, False, 5.0, control=1.0), _cell(100, True, 3.5, control=1.6)]
    d = sweep.control_drift(cells)
    assert d["spread_ms"] == pytest.approx(0.6)


def test_control_drift_needs_more_than_one_cell():
    assert sweep.control_drift([_cell(0, False, 5.0)]) is None


def test_cold_penalty_is_a_ratio_over_an_n_of_one():
    cells = [_cell(0, True, 2.0, cold=50.0)]
    rows = sweep.cold_penalty(cells, API)
    assert rows[0]["ratio"] == pytest.approx(25.0)


# ----------------------------------------------------------------------
# the report
# ----------------------------------------------------------------------
def test_report_leads_with_the_control():
    cells = [_cell(0, False, 5.0), _cell(0, True, 3.0)]
    md = sweep.render_report(cells, {"run_id": "x"})
    assert md.index("## Control") < md.index("## Index effect")
    assert md.index("## Control") < md.index("## Volume effect")


def test_report_says_so_when_the_control_is_missing():
    cells = [_cell(0, False, 5.0), _cell(0, True, 3.0)]
    for c in cells:
        c["warm"].pop(sweep.CONTROL)
    md = sweep.render_report(cells, {})
    assert "unverified" in md


def test_report_labels_cold_as_n_equals_one():
    md = sweep.render_report([_cell(0, True, 2.0)], {})
    assert "n=1" in md
    assert "first touch after restart" in md


def test_report_discloses_that_volume_is_synthetic():
    md = sweep.render_report([_cell(0, True, 2.0)], {})
    assert "synthetic" in md


def test_empty_grid_reports_nothing_rather_than_an_empty_table():
    assert "Nothing to report" in sweep.render_report([], {})


def test_control_is_checked_before_it_is_timed():
    """A 401 control would otherwise be published as the floor every other
    number is compared against."""
    pc = FakePolaris(fail="get_token", code=401)
    with pytest.raises(AssertionError, match="error path"):
        sweep.measure_control(pc, "root", "wrong-secret", k=2, warmup=1)
    assert pc.calls.count("get_token") == 1


# ----------------------------------------------------------------------
# replication
# ----------------------------------------------------------------------
class FakeReplCursor:
    def __init__(self, db):
        self.db = db

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        self.db["calls"] += 1
        # The last step REPEATS rather than falling off to empty. An earlier
        # version returned [] once exhausted, which `wait_for_replicas` reads as
        # "no standby" -- so a test meaning "stays behind forever" silently
        # became "the standby disappeared" and passed for the wrong reason.
        if self.db["steps"]:
            self.db["last"] = self.db["steps"].pop(0)
        self._r = self.db.get("last", [])

    def fetchall(self):
        return self._r


class FakeReplConn:
    def __init__(self, steps):
        self.db = {"steps": list(steps), "calls": 0}

    def cursor(self):
        return FakeReplCursor(self.db)


def test_replication_lag_reports_bytes_behind_per_standby():
    conn = FakeReplConn([[("standby1", "streaming", 4096)]])
    assert sweep.replication_lag(conn) == [
        {"standby": "standby1", "state": "streaming", "behind_bytes": 4096}
    ]


def test_wait_for_replicas_blocks_until_caught_up():
    conn = FakeReplConn(
        [
            [("standby1", "streaming", 8192)],
            [("standby1", "streaming", 512)],
            [("standby1", "streaming", 0)],
        ]
    )
    out = sweep.wait_for_replicas(conn, interval=0, sleep=lambda _: None)
    assert out["standbys"] == 1
    assert conn.db["calls"] == 3


def test_a_standby_that_vanishes_mid_wait_is_an_error_not_a_pass():
    """It dropped its connection part-way through the insert, so it is an
    unknown number of rows behind — not caught up."""
    conn = FakeReplConn([[("standby1", "streaming", 8192)], []])
    with pytest.raises(RuntimeError, match="now none are"):
        sweep.wait_for_replicas(conn, interval=0, sleep=lambda _: None)


def test_no_standby_connected_is_reported_not_treated_as_caught_up():
    """An empty pg_stat_replication means nothing is streaming — worth seeing
    on a cluster that is supposed to have a standby, not silently passing."""
    out = sweep.wait_for_replicas(FakeReplConn([[]]), sleep=lambda _: None)
    assert out["standbys"] == 0


def test_wait_for_replicas_raises_rather_than_measuring_at_unknown_volume():
    """A cell labelled '10,000 clones' measured against a standby that has only
    replicated half of them is a wrong number, not a slow one."""
    conn = FakeReplConn([[("standby1", "streaming", 99999)]] * 50)
    with pytest.raises(TimeoutError, match="finished replicating"):
        sweep.wait_for_replicas(conn, timeout=0.05, interval=0, sleep=lambda _: None)


def test_restart_waits_for_the_controller_to_observe_the_patch():
    """`rollout restart` only patches the template. Running `rollout status`
    before the controller observes it reports the PREVIOUS rollout complete —
    which is how a sweep concludes Polaris is up and then hits a closed socket
    on the terminating pod. Errno 61, 2026-08-21."""
    seen, state = [], {"gen": 7, "observed": 7}

    def runner(cmd, timeout):
        seen.append(cmd)
        joined = " ".join(cmd)
        if "{.metadata.generation} {.status.observedGeneration}" in joined:
            # controller lags one poll behind the patch
            if state["observed"] < state["gen"]:
                out = f"{state['gen']} {state['observed']}"
                state["observed"] = state["gen"]
                return out
            return f"{state['gen']} {state['observed']}"
        if "{.metadata.generation}" in joined:
            return str(state["gen"])
        if "restart" in cmd:
            state["gen"] += 1
            state["observed"] = state["gen"] - 1
            return "restarted"
        return "complete"

    sweep.restart_polaris(runner=runner)
    kinds = [" ".join(c) for c in seen]
    gen_read = next(i for i, k in enumerate(kinds) if "{.metadata.generation}" in k)
    restarted = next(i for i, k in enumerate(kinds) if "rollout restart" in k)
    status = next(i for i, k in enumerate(kinds) if "rollout status" in k)
    observed = next(
        i for i, k in enumerate(kinds) if "observedGeneration" in k and i > restarted
    )
    assert gen_read < restarted < observed < status, kinds


def test_restart_refuses_if_the_controller_never_observes_it():
    def runner(cmd, timeout):
        joined = " ".join(cmd)
        if "observedGeneration" in joined:
            return "9 8"  # stuck: patched but never observed
        if "{.metadata.generation}" in joined:
            return "9"
        return "ok"

    with pytest.raises(TimeoutError, match="never observed"):
        sweep.restart_polaris(runner=runner, timeout=0.05)


# ----------------------------------------------------------------------
# noise floor and cell integrity
# ----------------------------------------------------------------------
def _cell_ns(clones, index, ms, lo, hi, scan=None, rows=64):
    return {
        "clones": clones,
        "index": index,
        "volume": {"rows": {"entities": 20, "grant_records": rows}},
        "scan": scan or {"plan": "Index Only Scan", "probe_is_clone": False},
        "restart": {},
        "cold": {},
        "warm": {
            API: {"surface": "mgmt", "ms": ms, "min": lo, "max": hi, "n": 15},
            sweep.CONTROL: {
                "surface": "auth",
                "ms": 6.8,
                "min": 6.7,
                "max": 7.3,
                "n": 15,
            },
        },
    }


def test_noise_floor_is_within_cell_spread_not_between_medians():
    """Measured 2026-08-22: control spread between medians was 0.60 ms while
    within-cell spreads were 35-60 ms. Bounding a 2 ms claim with 0.6 ms was
    two orders of magnitude wrong."""
    cells = [_cell_ns(0, False, 7.0, 6.5, 66.9), _cell_ns(0, True, 7.2, 6.6, 40.0)]
    assert sweep.noise_floor(cells, API) == pytest.approx(60.4)
    assert sweep.control_drift(cells)["spread_ms"] < 1.0  # the misleading number


def test_a_delta_below_the_floor_is_labelled_noise():
    cells = [_cell_ns(0, False, 7.0, 6.5, 66.9), _cell_ns(0, True, 9.5, 6.6, 40.0)]
    md = sweep.render_report(cells, {})
    assert "NOISE" in md
    assert "noise" in md


def test_an_index_absent_cell_that_planned_an_index_scan_is_flagged():
    """The whole contrast is void if the planner never stopped using an index."""
    problems = sweep.cell_integrity(_cell_ns(0, False, 7.0, 6.5, 8.0))
    assert any("did NOT measure the unindexed path" in p for p in problems)


def test_a_real_seq_scan_cell_at_volume_is_not_flagged_for_the_plan():
    cell = _cell_ns(
        10000,
        False,
        40.0,
        38.0,
        42.0,
        scan={"plan": "Gather > Parallel Seq Scan", "probe_is_clone": False},
        rows=580_000,
    )
    assert sweep.cell_integrity(cell) == []


def test_too_few_rows_to_be_informative_is_stated_not_left_implicit():
    problems = sweep.cell_integrity(_cell_ns(100, True, 7.0, 6.5, 8.0, rows=3064))
    assert any("uninformative" in p for p in problems)


def test_the_report_leads_with_the_integrity_warning():
    cells = [_cell_ns(0, False, 7.0, 6.5, 66.9), _cell_ns(0, True, 7.2, 6.6, 40.0)]
    md = sweep.render_report(cells, {})
    assert "DOES NOT MEASURE WHAT THE TABLES SAY" in md
    assert md.index("DOES NOT MEASURE") < md.index("## Index effect")
