#!/usr/bin/env python3
"""Static verification for 02c: exec every code cell against a mocked cluster.

The repo's established harness, and the reason it exists: a 02c cell that calls
a module function with the wrong kwarg, or unpacks a return value that is an int
where the cell assumed a dict, fails **six restarts and forty minutes** into a
live sweep. That exact class of bug was already caught once here — the first
draft of the notebook read `grant_scale.total_rows()` as a dict when it returns
an int.

WHAT IS REAL AND WHAT IS FAKE
-----------------------------
`api_sweep` is REAL — the grid ordering, the cold/warm split, the refusal to
time a non-2xx, and the report are what this is verifying.

Faked: psycopg2, kubectl, HTTP. Every faked module function is wrapped by
`guard()`, which binds the call against the **real** function's signature before
answering. So a renamed parameter or a dropped positional still fails here, even
though nothing touches a database. What guard cannot check is the return SHAPE;
those are pinned by hand below and each one carries the real function's
docstring claim beside it.
"""

import inspect
import json
import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE
while not (REPO / "src").is_dir() and REPO != REPO.parent:
    REPO = REPO.parent
sys.path.insert(0, str(REPO / "src"))

NB = HERE / "02c_api_latency_sweep.ipynb"
SCHEMA, REALM = "polaris_schema", "POLARIS"


def guard(real, fake):
    """Answer with `fake`, but bind the call against `real`'s signature first.

    This is what keeps the harness from certifying a notebook that calls a
    function the module no longer has in that shape.
    """
    sig = inspect.signature(real)

    def wrapper(*a, **kw):
        sig.bind(*a, **kw)  # raises TypeError on any mismatch
        return fake(*a, **kw)

    wrapper.__name__ = getattr(real, "__name__", "guarded")
    return wrapper


# ----------------------------------------------------------------------
# fake psycopg2
# ----------------------------------------------------------------------
class FakeCursor:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        s = " ".join(sql.split())
        if "version()" in s:
            self._r = ("PostgreSQL 16.4, compiled by gcc", False)
        elif "count(*)" in s:
            self._r = (7319,)
        else:
            self._r = (0,)

    def fetchone(self):
        return self._r

    def fetchall(self):
        return []


class FakeConn:
    autocommit = False

    def cursor(self):
        return FakeCursor()

    def close(self):
        pass


def install_fakes(ns_env):
    import api_sweep
    import entity_replay
    import grant_scale
    import run_manifest

    psycopg2 = types.ModuleType("psycopg2")
    psycopg2.connect = lambda **kw: FakeConn()
    psycopg2.extras = types.ModuleType("psycopg2.extras")
    sys.modules["psycopg2"] = psycopg2

    requests = types.ModuleType("requests")

    class R:
        status_code = 200

        def json(self):
            return {"access_token": "fake"}

        text = ""

    requests.get = lambda *a, **kw: R()
    sys.modules["requests"] = requests

    # --- kubectl ---
    api_sweep._run = guard(
        api_sweep._run, lambda cmd, timeout: "deployment restarted\n"
    )
    api_sweep.restart_polaris = guard(
        api_sweep.restart_polaris,
        lambda **kw: {"seconds": 3.0, "restart": "restarted", "status": "complete"},
    )
    api_sweep.wait_until_serving = guard(
        api_sweep.wait_until_serving,
        lambda *a, **kw: {"seconds": 1.0, "attempts": True},
    )

    # --- entity_replay. Shapes taken from the module's own returns. ---
    template = {
        "prefix": "user1",
        "catalog_id": 4436362907216553159,
        "ids": set(),
        "entities": [(i,) * 17 for i in range(7)],
        "grants": [(0,) * 6 for _ in range(55)],
    }
    entity_replay.read_template = guard(
        entity_replay.read_template, lambda *a, **kw: dict(template)
    )
    entity_replay.assert_prefix_is_free = guard(
        entity_replay.assert_prefix_is_free, lambda *a, **kw: True
    )
    entity_replay.find_clone_band = guard(
        entity_replay.find_clone_band, lambda *a, **kw: (9 * 10**18, 1600)
    )
    entity_replay.insert_clones = guard(
        entity_replay.insert_clones,
        lambda *a, **kw: {"entities": 7, "grants": 55},
    )
    entity_replay.delete_clones = guard(
        entity_replay.delete_clones, lambda *a, **kw: {"entities": 0, "grants": 0}
    )
    entity_replay.clone_ids = guard(entity_replay.clone_ids, lambda *a, **kw: [])
    api_sweep.wait_for_replicas = guard(
        api_sweep.wait_for_replicas,
        lambda *a, **kw: {"standbys": 1, "seconds": 0.4, "lag": []},
    )

    # --- grant_scale ---
    grant_scale.set_index = guard(
        grant_scale.set_index,
        lambda *a, **kw: {
            "seconds": 0.1,
            "state": {"present": True, "valid": True, "ready": True},
        },
    )
    grant_scale.resolve_probes = guard(
        grant_scale.resolve_probes,
        lambda *a, **kw: [
            {
                "label": "fattest (1006 rows)",
                "grantee_id": 1,
                "grantee_catalog_id": 0,
                "rows": 1006,
                "synthetic": False,
            }
        ],
    )
    grant_scale.measure = guard(
        grant_scale.measure,
        lambda *a, **kw: {
            "label": "fattest (1006 rows)",
            "synthetic": False,
            "rows_returned": 1006,
            "rows_filtered": 29003,
            "path": "Gather > Parallel Seq Scan",
            "node": "Gather",
            "scan_node": "Parallel Seq Scan",
            "parallel": True,
            "total_cost": 810.16,
            "shared_hit": 285,
            "shared_read": 0,
            "ms": 1.4,
            "min": 1.2,
            "max": 2.7,
        },
    )
    run_manifest.table_counts = guard(
        run_manifest.table_counts,
        lambda conn, schema, tables: {t: 7319 for t in tables},
    )

    # --- PolarisREST ---
    class FakePolarisREST:
        def __init__(self, base_url, realm, token=None):
            self.token = token

        def get_token(self, client_id, client_secret, scope="PRINCIPAL_ROLE:ALL"):
            return R()

        def __getattr__(self, _name):
            return lambda *a, **kw: R()

    mod = types.ModuleType("polaris_rest")
    mod.PolarisREST = FakePolarisREST
    sys.modules["polaris_rest"] = mod

    ns_env["__fakes__"] = True


def main():
    if not NB.exists():
        sys.exit(f"{NB.name} not found — run build_02c.py first")

    import os

    # Shrink the grid. The arithmetic that scales it is still exercised; what is
    # skipped is materialising 550,000 tuples in a fake.
    os.environ["SWEEP_VOLUMES"] = "0,10"
    os.environ["SWEEP_K"] = "2"
    os.environ["SWEEP_WARMUP"] = "1"
    os.environ.setdefault("SWEEP_FIXTURE", "user1")
    os.environ.setdefault("SWEEP_DECOY", "user2")

    ns = {"__name__": "__nb__"}
    install_fakes(ns)

    nb = json.loads(NB.read_text())
    cells = [c for c in nb["cells"] if c["cell_type"] == "code"]
    cwd = os.getcwd()
    os.chdir(HERE)
    try:
        for i, cell in enumerate(cells, 1):
            src = "".join(cell["source"])
            try:
                exec(compile(src, f"<cell {i}>", "exec"), ns)  # noqa: S102
            except Exception as exc:
                print(f"\nCELL {i} FAILED: {type(exc).__name__}: {exc}")
                print("-" * 60)
                print(src[:1200])
                return 1
            print(f"  cell {i:>2} ok")
    finally:
        os.chdir(cwd)

    cells_out = ns.get("cells")
    assert cells_out, "the sweep produced no cells"
    expected = len(ns["VOLUMES"]) * len(ns["INDEX_STATES"])
    assert len(cells_out) == expected, f"{len(cells_out)} cells, expected {expected}"

    import api_sweep

    for c in cells_out:
        assert api_sweep.CONTROL in c["warm"], "a cell has no control"
        assert c["cold"], "a cell has no cold sample"
        assert "scan" in c, "a cell has no plan-shape evidence"

    report = ns.get("report", "")
    assert "## Control" in report, "the report does not lead with the control"
    assert "synthetic" in report, "the report does not disclose synthetic volume"

    print(
        f"\nOK — {len(cells)} code cells, {len(cells_out)} grid cells, report rendered"
    )
    print("This proves the notebook RUNS. It proves nothing about latency.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
