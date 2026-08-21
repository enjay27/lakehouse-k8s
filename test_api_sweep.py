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
def test_restart_issues_rollout_then_waits_for_status():
    seen = []

    def runner(cmd, timeout):
        seen.append(cmd)
        return "ok"

    out = sweep.restart_polaris(runner=runner)
    assert seen[0][:3] == ["kubectl", "rollout", "restart"]
    assert seen[1][:3] == ["kubectl", "rollout", "status"]
    assert "deploy/benchmarks-polaris" in seen[0]
    assert "-n" in seen[0] and "datahub-hynix" in seen[0]
    # The status call must carry a timeout, or a stuck rollout hangs the sweep
    # instead of failing it.
    assert any(a.startswith("--timeout=") for a in seen[1])
    assert out["seconds"] >= 0


def test_restart_raises_rather_than_measuring_a_half_restarted_deployment():
    def runner(cmd, timeout):
        raise RuntimeError("rollout status: timed out waiting")

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
