"""Tests for `src/make_traffic.py` -- the traffic side of the split.

Three kinds, and the first is the one this file exists for.

**The boundary.** `SCENARIO-logging-test.md` §3 asks that the traffic side hold
no logging concept, and says why it must be a test: *"the boundary should fail
at CI, not at review"*. `test_the_import_graph_carries_no_logging_module` walks
the graph rather than reading the docstring. It is the reason
`traffic_helpers.py` exists at all -- `log_coverage` held both halves, so
before the split this assertion could not have been written.

**The contract.** The row shape, the claim shape, and every refusal
`TrafficRun.from_dict` makes. `local-k8s` reads these; a change here that nobody
notices is a verifier reporting pipeline faults that are file faults.

**The twins.** `window_bounds` / `seconds_to_boundary` exist in two modules on
purpose -- importing `os_report` for twelve lines of `//` would put the whole
OpenSearch client in the traffic side's import graph. Two copies drift, so a
test compares them.

No test here touches the network, and none needs a cluster.
"""

import ast
import json
import pathlib
import sys

import pytest

import make_traffic as mt  # noqa: E402

SRC = pathlib.Path(__file__).resolve().parents[1] / "src"
SPEC = (
    pathlib.Path(__file__).resolve().parents[1]
    / "diagnostics"
    / "ladders"
    / "log-coverage"
    / "spec"
)

#: Modules that hold a concept of what a log pipeline did with a request. The
#: traffic side may not reach any of them, at module scope or inside a
#: function.
LOGGING_MODULES = frozenset(
    {"log_coverage", "os_report", "vlogs", "opensearch_alert_provisioner"}
)

#: `polaris_test_utils` is NOT on that list and the exemption is deliberate:
#: it is `init_env`, this repo's config loader, and SCENARIO §7.3 puts it on
#: this side on purpose so `local-k8s` never holds a Polaris credential. It
#: carries OpenSearch *connection settings* for other callers, which is not a
#: logging concept -- but it is the one edge worth naming, so that a future
#: reader who finds a logging import hiding behind it knows this test allowed
#: the door and not the room.
CONFIG_MODULE = "polaris_test_utils"


def _imports_of(path):
    """Every module `path` imports, module scope and function scope alike."""
    out = set()
    for node in ast.walk(ast.parse(pathlib.Path(path).read_text())):
        if isinstance(node, ast.Import):
            out.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            out.add(node.module.split(".")[0])
    return out


def _graph_from(start):
    """Transitive closure over the modules that live in `src/`."""
    seen, queue = set(), [start]
    while queue:
        name = queue.pop()
        if name in seen:
            continue
        seen.add(name)
        path = SRC / f"{name}.py"
        if path.exists():
            queue.extend(_imports_of(path))
    return seen


# ----------------------------------------------------------------------
# the boundary
# ----------------------------------------------------------------------
def test_the_import_graph_carries_no_logging_module():
    graph = _graph_from("make_traffic")
    assert "traffic_helpers" in graph, (
        "the walker found no traffic_helpers, so it is not following imports "
        "at all and would pass on anything"
    )
    assert not (graph & LOGGING_MODULES), (
        f"make_traffic reaches {sorted(graph & LOGGING_MODULES)}. The traffic "
        "side must not be able to form an opinion about what the pipeline "
        "stored -- see SCENARIO-logging-test.md §3."
    )


def test_the_guard_would_notice_a_logging_import():
    """The guard's own coverage. A walker that cannot see through
    `traffic_helpers` would pass this file whatever it imported."""
    assert LOGGING_MODULES & _graph_from("log_coverage"), (
        "log_coverage does not appear to be a logging module to this walker, "
        "so the walker is broken, not the boundary"
    )


def test_traffic_helpers_does_not_import_back():
    """One-way, or it is not a split. `log_coverage -> traffic_helpers` is the
    only direction that may exist."""
    assert not (_graph_from("traffic_helpers") & LOGGING_MODULES)


def test_log_coverage_still_re_exports_every_moved_name():
    """`polaris_log_coverage.ipynb` is the v1 RUN OF RECORD and must keep
    working unedited while the split happens around it."""
    import log_coverage as lc
    import traffic_helpers as th

    moved = [
        n
        for n in dir(th)
        if not n.startswith("__") and n not in th.__added_after_split__
    ]
    missing = [n for n in moved if not hasattr(lc, n)]
    assert not missing, f"log_coverage no longer re-exports {missing}"


# ----------------------------------------------------------------------
# the twins
# ----------------------------------------------------------------------
@pytest.mark.parametrize("when", [0, 1789008899, 1789008900, 1789008929.999])
@pytest.mark.parametrize("seconds", [10, 30, 60])
def test_window_bounds_agrees_with_the_copy_in_os_report(when, seconds):
    import os_report as osr

    assert mt.window_bounds(when, seconds) == osr.window_bounds(when, seconds)


@pytest.mark.parametrize("now", [0, 1789008899, 1789008900.5])
def test_seconds_to_boundary_agrees_with_the_copy_in_os_report(now):
    import os_report as osr

    assert mt.seconds_to_boundary(30, lag=0.5, now=now) == osr.seconds_to_boundary(
        30, lag=0.5, now=now
    )


def test_a_boundary_wait_lands_inside_the_next_window():
    now = 1789008899.0
    wait = mt.seconds_to_boundary(30, lag=0.5, now=now)
    assert mt.window_bounds(now + wait, 30)[0] != mt.window_bounds(now, 30)[0]


# ----------------------------------------------------------------------
# the contract: profiles and refusals
# ----------------------------------------------------------------------
def test_every_documented_profile_is_implemented():
    assert sorted(mt.PROFILES) == sorted(mt._PHASES), (
        "a profile documented in PROFILES with no entry in _PHASES is a "
        "profile the caller can ask for and that drives nothing"
    )
    for name, phases in mt._PHASES.items():
        assert phases, f"profile {name!r} drives no phase at all"


def test_drive_refuses_an_unknown_profile():
    with pytest.raises(mt.ContractError, match="unknown profile"):
        mt.drive({}, window_seconds=30, profile="everything")


@pytest.mark.parametrize("bad", [0, -30, None, "30", 30j])
def test_drive_refuses_a_window_that_is_not_a_positive_number(bad):
    with pytest.raises(mt.ContractError, match="window_seconds"):
        mt.drive({}, window_seconds=bad)


def test_drive_refuses_a_config_that_cannot_drive():
    with pytest.raises(mt.ContractError, match="missing"):
        mt.drive({"polaris_url": "http://x"}, window_seconds=30)


# ----------------------------------------------------------------------
# the lag: every phase starts clear of the report tick's blind spot
# ----------------------------------------------------------------------
_GOOD_CFG = {k: "x" for k in mt._REQUIRED_CONFIG}


def test_drive_refuses_to_drive_without_a_tick_interval():
    # Before 2026-09-16 there was no such argument and every wait used lag=0.5:
    # inside the tick's blind spot, so each phase was booked one row early.
    with pytest.raises(mt.ContractError, match="tick_interval_s is required"):
        mt.drive(dict(_GOOD_CFG), window_seconds=30)


def test_the_default_lag_clears_the_whole_tick_interval():
    assert mt.phase_lag_for(30, tick_interval_s=5) == 5 + mt.PHASE_LAG_MARGIN_S
    assert mt.phase_lag_for(1800, tick_interval_s=30) == 30 + mt.PHASE_LAG_MARGIN_S


def test_an_explicit_lag_inside_the_tick_is_refused():
    with pytest.raises(mt.ContractError, match="does not clear the tick"):
        mt.phase_lag_for(30, tick_interval_s=5, phase_lag=0.5)


def test_a_lag_that_eats_half_the_window_is_refused():
    with pytest.raises(mt.ContractError, match="less than half"):
        mt.phase_lag_for(10, tick_interval_s=5)


def test_a_wait_with_the_default_lag_starts_after_the_tick():
    # Tick phase anywhere in [0, 5): the call must land past boundary + 5.
    now = 1789008899.0
    lag = mt.phase_lag_for(30, tick_interval_s=5)
    start = now + mt.seconds_to_boundary(30, lag=lag, now=now)
    assert 5 < start % 30 < 15


def test_no_boundary_wait_in_make_traffic_uses_a_literal_lag():
    """The lag=0.5 bug was five literals. A literal lag can only come back by hand."""
    tree = ast.parse((SRC / "make_traffic.py").read_text())
    literal = [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and getattr(node.func, "id", None) == "seconds_to_boundary"
        and any(
            kw.arg == "lag" and isinstance(kw.value, ast.Constant)
            for kw in node.keywords
        )
    ]
    assert (
        not literal
    ), f"seconds_to_boundary called with a literal lag at lines {literal}"
    sleeps = [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and getattr(node.func, "attr", None) == "sleep"
        and any(
            isinstance(a, ast.Call)
            and getattr(a.func, "id", None) == "seconds_to_boundary"
            for a in node.args
        )
    ]
    assert len(sleeps) == 1, (
        f"boundary sleeps at lines {sleeps}: every phase must wait through "
        "_wait_for_window, the one place the validated lag is applied"
    )


def test_check_config_refuses_prod_whatever_else_is_right():
    cfg = {k: "x" for k in mt._REQUIRED_CONFIG}
    assert mt.check_config(dict(cfg)) is not None
    cfg["env"] = "PROD"
    with pytest.raises(mt.ContractError, match="PROD"):
        mt.check_config(cfg)


def test_check_config_refuses_something_that_is_not_a_dict():
    with pytest.raises(mt.ContractError, match="must be a dict"):
        mt.check_config("local")


# ----------------------------------------------------------------------
# the contract: the call row
# ----------------------------------------------------------------------
def _driven(**kw):
    row = {
        "request_id": "nb-1-001-x",
        "echoed_request_id": "nb-1-001-x",
        "op_id": "createNamespace",
        "method": "post",
        "path": "/v1/{prefix}/namespaces",
        "actual_path": "/api/catalog/v1/c/namespaces",
        "api": "catalog",
        "target": 2,
        "status": 200,
        "response_bytes": 41,
        "principal": "runner",
        "issued_at": 1789008899.0,
        "verdict": "covered",
    }
    row.update(kw)
    return row


def test_a_call_row_carries_exactly_the_contract_fields():
    row = mt.call_row(_driven(), 30, phase="B")
    assert tuple(row) == mt._CALL_FIELDS


def test_a_call_row_carries_no_expectation_about_storage():
    """PLAN §3.2: which calls are counted is a fact about the deployed Lua.
    A field here would let the two repos hold two answers about one policy."""
    row = mt.call_row(_driven(), 30)
    forbidden = {"kept", "counted", "expected", "disposition", "stored", "keep", "drop"}
    assert not (set(row) & forbidden)


def test_the_window_is_derived_from_when_the_call_went_out():
    row = mt.call_row(_driven(issued_at=1789008899.0), 30)
    assert row["window"] == "2026-09-10T02:54:30Z"
    assert mt.call_row(_driven(issued_at=None), 30)["window"] is None


def test_the_actual_path_wins_over_the_template():
    assert mt.call_row(_driven(), 30)["path"] == "/api/catalog/v1/c/namespaces"
    assert (
        mt.call_row(_driven(actual_path=None), 30)["path"] == "/v1/{prefix}/namespaces"
    )


def test_echo_ok_separates_absent_from_disagreed():
    """The two accuse different repos. Collapsing them loses exactly the
    distinction the check exists for."""
    assert mt.call_row(_driven(), 30)["echo_ok"] is True
    assert mt.call_row(_driven(echoed_request_id="nb-1-001-y"), 30)["echo_ok"] is False
    assert mt.call_row(_driven(echoed_request_id=None), 30)["echo_ok"] is None


def test_echo_failures_lists_only_the_ids_that_came_back_wrong():
    calls = [
        mt.call_row(_driven(), 30),
        mt.call_row(_driven(request_id="a", echoed_request_id="b"), 30),
        mt.call_row(_driven(request_id="c", echoed_request_id=None), 30),
    ]
    assert [c["request_id"] for c in mt.echo_failures(calls)] == ["a"]


# ----------------------------------------------------------------------
# the contract: claims
# ----------------------------------------------------------------------
def test_every_claim_is_keyed_by_request_id():
    """PLAN §3.1. A claim keyed by resource name is what made Gate 4
    unreadable in run 1789008899."""
    claims = [
        mt.claim_last_write_bytes("rid-1", "W", 1733),
        mt.claim_no_last_write_bytes("rid-2", "W"),
        mt.claim_role_writes(["rid-3", "rid-4", "rid-5"], "W", 3),
        mt.claim_auth_denied("rid-6", "W"),
    ]
    for c in claims:
        assert c["window"] == "W"
        assert c["because"]
        assert c.get("request_id") or c.get("request_ids")


def test_a_role_writes_claim_counts_the_ids_it_names():
    c = mt.claim_role_writes(["a", "b", "c"], "W", 3)
    assert c["equals"] == len(c["request_ids"]) == 3


# ----------------------------------------------------------------------
# the contract: the record on disk
# ----------------------------------------------------------------------
def _run_dict(**kw):
    d = {
        "contract_version": mt.CONTRACT_VERSION,
        "run": "1789008899",
        "driven_at": "2026-09-10T02:54:30Z",
        "profile": "full",
        "polaris": {"url": "http://x", "realm": "r", "version": "1.3.0"},
        "fixture": {"catalog": "c"},
        "identities": {"admin": "root"},
        "window_seconds": 30,
        "windows": {
            "first": "2026-09-10T02:54:30Z",
            "last": "2026-09-10T02:55:00Z",
            "distinct": ["2026-09-10T02:54:30Z", "2026-09-10T02:55:00Z"],
        },
        "phases": [],
        "calls": [mt.call_row(_driven(), 30, phase="B")],
        "claims": [],
        "coverage": {},
        "build_findings": [],
        "incomplete": None,
    }
    d.update(kw)
    return d


def test_a_run_round_trips_through_disk(tmp_path):
    written = mt.TrafficRun(**_run_dict()).write(tmp_path)
    assert written.name == "traffic-1789008899.json"
    back = mt.TrafficRun.read(written)
    assert back.to_dict() == _run_dict()


def test_a_run_refuses_a_field_it_does_not_know():
    with pytest.raises(mt.ContractError, match="unknown TrafficRun field"):
        mt.TrafficRun(**_run_dict(kept_calls=[]))


def test_a_run_from_a_different_contract_is_refused_not_coerced():
    with pytest.raises(mt.TrafficRunInvalid, match="contract_version"):
        mt.TrafficRun.from_dict(_run_dict(contract_version=2))


@pytest.mark.parametrize("field", ["run", "profile", "window_seconds"])
def test_a_run_missing_an_identifying_field_is_refused(field):
    with pytest.raises(mt.TrafficRunInvalid, match=field):
        mt.TrafficRun.from_dict(_run_dict(**{field: None}))


def test_a_run_with_no_calls_is_refused():
    """A run that drove nothing is not evidence that the pipeline stored
    nothing, and that is precisely how it would be read."""
    with pytest.raises(mt.TrafficRunInvalid, match="calls is empty"):
        mt.TrafficRun.from_dict(_run_dict(calls=[]))


def test_a_run_whose_windows_run_backwards_is_refused():
    with pytest.raises(mt.TrafficRunInvalid, match="is after"):
        mt.TrafficRun.from_dict(
            _run_dict(
                windows={
                    "first": "2026-09-10T02:55:00Z",
                    "last": "2026-09-10T02:54:30Z",
                    "distinct": [],
                }
            )
        )


def test_a_claim_naming_a_window_outside_the_run_is_refused():
    with pytest.raises(mt.TrafficRunInvalid, match="not.*one of the run"):
        mt.TrafficRun.from_dict(
            _run_dict(claims=[mt.claim_auth_denied("rid", "1999-01-01T00:00:00Z")])
        )


def test_a_run_that_is_not_an_object_is_refused():
    with pytest.raises(mt.TrafficRunInvalid, match="expected an object"):
        mt.TrafficRun.from_dict([])


def test_read_refuses_a_half_written_file(tmp_path):
    p = tmp_path / "traffic-x.json"
    p.write_text(json.dumps(_run_dict(calls=[])))
    with pytest.raises(mt.TrafficRunInvalid):
        mt.TrafficRun.read(p)


# ----------------------------------------------------------------------
# coverage and build findings
# ----------------------------------------------------------------------
def test_coverage_counts_a_call_that_never_completed_as_error_not_missed():
    calls = [
        mt.call_row(_driven(verdict="covered"), 30),
        mt.call_row(_driven(verdict="missed", status=404), 30),
        mt.call_row(_driven(verdict="covered", status=None), 30),
    ]
    cov = mt.coverage_of(calls)
    assert (cov["covered"], cov["missed"], cov["error"]) == (1, 1, 1)
    assert cov["by_target"]["2"]["covered"] == 1


def test_build_findings_are_empty_when_the_build_behaved():
    assert mt.build_findings([mt.call_row(_driven(), 30)]) == []


def test_build_findings_report_every_500_with_its_request_id():
    calls = [
        mt.call_row(_driven(request_id="r1", status=500, op_id="createNamespace"), 30),
        mt.call_row(_driven(request_id="r2", status=200), 30),
    ]
    found = [f for f in mt.build_findings(calls) if "500" in f["title"]]
    assert len(found) == 1
    assert found[0]["about"] == "polaris"
    assert found[0]["request_ids"] == ["r1"]


def test_an_endpoint_that_404s_every_cell_is_reported_as_unrouted():
    """404 to EVERY cell including the unauthenticated one is what separates
    'not routed on this build' from 'not found'."""
    calls = [
        mt.call_row(_driven(op_id="planTableScan", status=404, target=t), 30)
        for t in (2, 401, 403, 404)
    ]
    titles = [f["title"] for f in mt.build_findings(calls)]
    assert any("not routed" in t for t in titles)


def test_a_single_404_is_not_an_unrouted_endpoint():
    calls = [
        mt.call_row(_driven(op_id="loadTable", status=404, target=404), 30),
        mt.call_row(_driven(op_id="loadTable", status=200, target=2), 30),
    ]
    assert not any("not routed" in f["title"] for f in mt.build_findings(calls))


def test_a_2xx_to_an_identity_that_should_have_been_refused_is_a_build_finding():
    calls = [mt.call_row(_driven(op_id="getConfig", target=401, status=200), 30)]
    found = mt.build_findings(calls)
    assert found and found[0]["about"] == "polaris"


def test_build_findings_never_claim_to_be_pipeline_work():
    """SCENARIO §6: two report sections that must never merge. Today's
    REPORT-for-local-k8s.md mixes them and sends four Polaris facts to the
    wrong repo."""
    calls = [mt.call_row(_driven(status=500), 30)]
    assert all(f["about"] == "polaris" for f in mt.build_findings(calls))


# ----------------------------------------------------------------------
# incomplete, and cleanup that runs anyway
# ----------------------------------------------------------------------
class _Resp:
    def __init__(self, status=204, content=b""):
        self.status_code = status
        self.content = content
        self.headers = {}
        self.request = None


class _Boom:
    """A client whose every call raises. Cleanup must survive it."""

    def __init__(self):
        self.tried = []

    def __getattr__(self, name):
        def go(*a, **k):
            self.tried.append(name)
            raise RuntimeError(f"{name} exploded")

        return go


class _Quiet:
    def __init__(self):
        self.tried = []
        self.extra_headers = {}

    def __getattr__(self, name):
        def go(*a, **k):
            self.tried.append(name)
            return _Resp()

        return go


def _collector():
    calls, phases = [], []

    def record(rows, phase):
        out = [mt.call_row(r, 30, phase=phase) for r in rows]
        calls.extend(out)
        return out

    def phase_window(name, t0, t1, cells):
        entry = {
            "name": name,
            "start": mt.window_bounds(t0, 30)[0],
            "end": mt.window_bounds(t1, 30)[0],
            "straddled": False,
            "cells": cells,
            "seconds": 0.0,
        }
        phases.append(entry)
        return entry

    return calls, phases, record, phase_window


class _Fx:
    cat, ns, tbl, view = "c", "n", "t", "v"


def test_cleanup_records_its_deletes_as_phase_i():
    """The cleanup DELETEs are part of the test, not tidying: dropTable,
    dropView, dropNamespace, deleteCatalog and deletePrincipal are five of
    the 63 operations."""
    calls, phases, record, phase_window = _collector()
    adm, ic = _Quiet(), _Quiet()
    rows = mt._cleanup(
        {},
        "1",
        adm,
        ic,
        _Fx(),
        {"catalogRoleName": "cr"},
        "runner",
        "rrole",
        "denied",
        "drole",
        30,
        record,
        phase_window,
    )
    assert rows and [p["name"] for p in phases] == ["I"]
    assert {c["phase"] for c in calls} == {"I"}
    assert "dropTable" in {c["op_id"] for c in calls}


def test_cleanup_never_raises_when_every_delete_explodes():
    """A failure here must not lose the run's findings."""
    calls, phases, record, phase_window = _collector()
    rows = mt._cleanup(
        {},
        "1",
        _Boom(),
        _Boom(),
        _Fx(),
        {},
        "r",
        "rr",
        "d",
        "dr",
        30,
        record,
        phase_window,
    )
    assert rows and all(r["status"] is None for r in rows)
    assert all(c["verdict"] == "error" for c in calls)


def test_cleanup_skips_what_setup_never_built():
    """A drive that died before the fixture must not delete a catalog whose
    name it never learned."""
    calls, phases, record, phase_window = _collector()
    adm = _Quiet()
    mt._cleanup(
        {}, "1", adm, None, None, {}, "r", "rr", "d", "dr", 30, record, phase_window
    )
    assert "delete_catalog" not in adm.tried
    assert "drop_table" not in adm.tried


# ----------------------------------------------------------------------
# dry_run: it must contact NOTHING, and it must not return from inside the try
# ----------------------------------------------------------------------
def _unreachable_config():
    """A config whose URL cannot be dialled at all.

    `"x"` is not a URL -- `requests` raises MissingSchema on it before any
    socket is opened. So a dry run that completes against this config proves
    it made no request, without needing to intercept anything.
    """
    cfg = {k: "x" for k in mt._REQUIRED_CONFIG}
    cfg["realm"] = "POLARIS"
    return cfg


def test_dry_run_contacts_nothing(tmp_path):
    """The first version of this ran AFTER the fixture was built, so a "dry
    run" created a catalog, a namespace, a table, a view, two principals, two
    roles and the whole doomed family -- dozens of mutating calls against a
    docstring promising none. Nothing caught it, because there was no test."""
    run = mt.drive(
        _unreachable_config(),
        window_seconds=30,
        profile="full",
        run="dry1",
        dry_run=True,
        spec_dir=SPEC,
        runs_dir=tmp_path,
    )
    assert run.incomplete.startswith("dry_run:")
    assert run.calls == [] and run.claims == [] and run.phases == []
    assert run.identities == {}


def test_dry_run_still_builds_every_cell_in_the_grid():
    """Contacting nothing must not become checking nothing: the count is the
    evidence that all 286 requests were actually built."""
    import api_status_matrix as mx

    expected = len(mx.cells(mx.load_spec(SPEC)))
    run = mt.drive(
        _unreachable_config(),
        window_seconds=30,
        run="dry2",
        dry_run=True,
        spec_dir=SPEC,
        runs_dir=False,
    )
    assert f"{expected} requests were built" in run.incomplete
    assert expected > 200


def test_dry_run_writes_no_evidence_file(tmp_path):
    """It drove nothing, so it has no evidence to give. A `traffic-<run>.json`
    with no calls in it is a file a verifier could still be handed."""
    mt.drive(
        _unreachable_config(),
        window_seconds=30,
        run="dry3",
        dry_run=True,
        spec_dir=SPEC,
        runs_dir=tmp_path,
    )
    assert list(tmp_path.iterdir()) == []


def test_dry_run_says_it_proves_shape_and_not_validity():
    """A reader who takes "286 requests were built" for "286 requests are
    valid" would believe a claim nothing in this repo makes.

    It used to point at `spec_check`; that tier was removed on 2026-09-10, so
    the sentence must now say a real drive is the only answer -- an
    `incomplete` that names a module which no longer exists is worse than one
    that names nothing."""
    run = mt.drive(
        _unreachable_config(),
        window_seconds=30,
        run="dry4",
        dry_run=True,
        spec_dir=SPEC,
        runs_dir=False,
    )
    assert "only a real drive against Polaris" in run.incomplete
    assert "spec_check" not in run.incomplete


def test_drive_never_returns_from_inside_its_try_block():
    """The record must be assembled AFTER cleanup, not before it.

    The removed dry_run path returned from inside the `try`, so `_finish` ran
    while `finally` had not yet driven the phase-I deletes -- the returned
    TrafficRun was missing its own cleanup rows, and the evidence file was
    written before they happened. Asserted structurally because the shape is
    the bug: any `return` inside that `try` reintroduces it, whatever it
    returns.
    """
    import ast

    src = (pathlib.Path(mt.__file__)).read_text()
    fn = next(
        n
        for n in ast.walk(ast.parse(src))
        if isinstance(n, ast.FunctionDef) and n.name == "drive"
    )
    tries = [n for n in fn.body if isinstance(n, ast.Try)]
    assert tries, "drive no longer has a try/finally -- cleanup is not guaranteed"
    for t in tries:
        for node in ast.walk(ast.Module(body=t.body, type_ignores=[])):
            assert not isinstance(node, ast.Return), (
                "a `return` inside drive()'s try block builds the record before "
                "`finally` runs cleanup -- the phase-I rows would be missing"
            )


def test_finish_carries_incomplete_through_to_the_record(tmp_path):
    state = {
        "calls": [mt.call_row(_driven(), 30, phase="B")],
        "claims": [],
        "phases": [],
        "fixture": {},
        "identities": {},
        "incomplete": "RuntimeError: boom -- after 1 call(s).",
    }
    run = mt._finish(
        state, "1", "full", {k: "x" for k in mt._REQUIRED_CONFIG}, 30, tmp_path
    )
    assert run.incomplete.startswith("RuntimeError")
    assert run.windows["first"] == run.windows["last"] == "2026-09-10T02:54:30Z"
    assert (tmp_path / "traffic-1.json").exists()


def test_finish_writes_nothing_when_the_drive_produced_no_calls(tmp_path):
    state = {
        "calls": [],
        "claims": [],
        "phases": [],
        "fixture": {},
        "identities": {},
        "incomplete": "died in setup",
    }
    mt._finish(state, "1", "full", {k: "x" for k in mt._REQUIRED_CONFIG}, 30, tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_finish_can_be_told_to_write_nothing_at_all(tmp_path):
    state = {
        "calls": [mt.call_row(_driven(), 30)],
        "claims": [],
        "phases": [],
        "fixture": {},
        "identities": {},
        "incomplete": None,
    }
    mt._finish(state, "1", "full", {k: "x" for k in mt._REQUIRED_CONFIG}, 30, False)
    assert list(tmp_path.iterdir()) == []


# ----------------------------------------------------------------------
# phase J -- the two-level namespace (local-k8s TODO 1.5)
# ----------------------------------------------------------------------
class _FakeResp:
    def __init__(self, status, url, rid, body=b""):
        import requests

        self.status_code = status
        self.content = body
        self.headers = {"Polaris-Request-Id": rid}
        self.request = requests.Request("GET", url).prepare()


class _FakeIceberg:
    """Records every call and answers with a prepared URL built the real way."""

    def __init__(self, fail_on=None):
        from iceberg_rest import IcebergREST

        self.real = IcebergREST("http://polaris:8181", "POLARIS", token="t")
        self.calls, self.fail_on, self.extra_headers = [], fail_on, {}

    def _answer(self, op, status, path):
        rid = self.extra_headers.get("Polaris-Request-Id")
        self.calls.append((op, rid))
        if op == self.fail_on:
            raise RuntimeError(f"boom in {op}")
        return _FakeResp(status, f"http://polaris:8181{path}", rid, b"{}")

    def _ns(self, cat, ns):
        return f"/api/catalog/v1/{cat}/namespaces/{self.real._ns_path(ns)}"

    def create_namespace(self, cat, ns):
        assert isinstance(ns, list) and len(ns) == 2
        return self._answer("createNamespace", 200, f"/api/catalog/v1/{cat}/namespaces")

    def create_table(self, cat, ns, payload):
        return self._answer("createTable", 200, self._ns(cat, ns) + "/tables")

    def commit_table(self, cat, ns, table, updates):
        return self._answer("updateTable", 200, self._ns(cat, ns) + f"/tables/{table}")

    def load_table(self, cat, ns, table):
        return self._answer("loadTable", 200, self._ns(cat, ns) + f"/tables/{table}")

    def drop_table(self, cat, ns, table):
        return self._answer("dropTable", 204, self._ns(cat, ns) + f"/tables/{table}")

    def drop_namespace(self, cat, ns):
        return self._answer("dropNamespace", 204, self._ns(cat, ns))


def _nested(ic):
    import traffic_helpers as th

    return th.drive_nested_namespace(
        ic,
        "1789",
        "cat1",
        "probe_ns",
        schema=None,
        table_payload=lambda n, s: {"name": n},
    )


def test_names_added_after_the_split_exist():
    import traffic_helpers as th

    assert all(hasattr(th, n) for n in th.__added_after_split__)


def test_full_profile_drives_phase_j_last():
    assert mt._PHASES["full"][-1] == "J"


def test_a_unit_separator_goes_out_as_percent_1f():
    """The assumption the report key rests on, checked without a network."""
    import requests

    from iceberg_rest import IcebergREST

    seg = IcebergREST._ns_path(["probe_ns", "nested"])
    url = f"http://polaris:8181/api/catalog/v1/cat1/namespaces/{seg}/tables/t"
    assert "%1F" in requests.Request("GET", url).prepare().path_url


def test_phase_j_drives_six_tagged_calls_in_order():
    ic = _FakeIceberg()
    result = _nested(ic)
    assert [op for op, _ in ic.calls] == [
        "createNamespace",
        "createTable",
        "updateTable",
        "loadTable",
        "dropTable",
        "dropNamespace",
    ]
    assert all(rid and rid.startswith("nb-1789-34") for _, rid in ic.calls)
    assert len(set(result["request_ids"])) == 6
    assert ic.extra_headers.get("Polaris-Request-Id") is None, "tag left on the client"
    assert all(r["verdict"] == "covered" for r in result["rows"])


def test_phase_j_names_the_one_row_the_verifier_must_find():
    result = _nested(_FakeIceberg())
    assert result["resource_key"] == (
        "/api/catalog/v1/cat1/namespaces/probe_ns%1Fnested/tables/mx_1789_deep"
    )
    assert result["path_encoded"] is True
    table_paths = {
        r["actual_path"]
        for r in result["rows"]
        if r["op_id"] in ("updateTable", "loadTable")
    }
    assert table_paths == {result["resource_key"]}, "the issued path IS the report key"


def test_phase_j_still_drops_when_the_commit_fails():
    ic = _FakeIceberg(fail_on="updateTable")
    result = _nested(ic)
    ops = [op for op, _ in ic.calls]
    assert ops[-2:] == ["dropTable", "dropNamespace"]
    assert [r["verdict"] for r in result["rows"] if r["op_id"] == "updateTable"] == [
        "error"
    ]
