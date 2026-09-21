"""Static verification for 02b: exec every code cell against a mocked backend.

The repo's established harness. It proves the notebook runs top to bottom with
no NameError, no kwarg mismatch and no shape bug — everything that would
otherwise be discovered 40 minutes into a live sweep.

It does NOT prove anything about volume or timing. `SIZES` is shrunk so the fake
does not materialise 500,000 tuples in Python; the arithmetic that computes it
from the live row count is still exercised.

`api_trace`, `grant_scale`, `run_manifest` and `matplotlib` are REAL. Only
psycopg2 is faked.
"""

import json
import os
import pathlib
import re
import shutil
import sys
import tempfile
import types

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE
while not (REPO / "src").is_dir() and REPO != REPO.parent:
    REPO = REPO.parent
sys.path.insert(0, str(REPO))  # test_grant_scale lives at the repo root
sys.path.insert(0, str(REPO / "src"))

from test_grant_scale import REAL_IDS, FakeCursor, FakeDB, real_rows  # noqa: E402

SCHEMA, REALM = "polaris_schema", "POLARIS"


class HarnessCursor(FakeCursor):
    """FakeCursor plus the statements only the notebook issues."""

    def execute(self, sql, params=None):
        s = " ".join(sql.split())
        if "version()" in s:
            self._result = [("PostgreSQL 16.4, compiled", False, "10.0.0.5")]
        elif "percentile_disc" in s:
            per = {}
            for r in self.db.rows:
                if r[4] >= 0:
                    per[r[4]] = per.get(r[4], 0) + 1
            vals = sorted(per.values()) or [0]
            self._result = [(len(per), vals[len(vals) // 2], vals[-1], max(vals))]
        elif "pg_constraint" in s:
            self._result = []
        else:
            return super().execute(sql, params)


class HarnessDB(FakeDB):
    def cursor(self):
        return HarnessCursor(self)

    def close(self):
        self.closed = True


def main():
    root = pathlib.Path(tempfile.mkdtemp(prefix="fakerepo-"))
    (root / "src").mkdir()
    for m in ("api_trace.py", "grant_scale.py", "run_manifest.py"):
        shutil.copy(REPO / "src" / m, root / "src" / m)
    nb_dir = root / "diagnostics" / "api-sql-profile"
    nb_dir.mkdir(parents=True)

    db = HarnessDB(real_rows(n_grantees=3, per=2))
    fake_pg = types.ModuleType("psycopg2")
    fake_pg.connect = lambda **kw: db
    sys.modules["psycopg2"] = fake_pg

    nb = json.loads((HERE / "02b_grant_scale_sweep.ipynb").read_text())
    cells = [c for c in nb["cells"] if c["cell_type"] == "code"]

    cwd = os.getcwd()
    os.chdir(nb_dir)
    ns = {"__name__": "__main__"}
    try:
        for i, c in enumerate(cells):
            src = "".join(c["source"])
            # Volume is not what this harness checks; see the module docstring.
            if "SIMULATED_USERS = [" in src:
                # Volume is not what this harness checks; see the module
                # docstring. ASSERTED, because a replacement that silently
                # stops matching leaves the harness measuring the wrong thing
                # while every line still reads green -- which is how a broken
                # patch got past this once already.
                patched = re.sub(
                    r"SIMULATED_USERS = \[[^\]]*\]",
                    "SIMULATED_USERS = [2, 4, 6]",
                    src,
                )
                assert patched != src, "the SIMULATED_USERS patch stopped matching"
                src = patched
            try:
                exec(compile(src, f"<cell {i}>", "exec"), ns)
            except Exception as e:
                print(f"\n!! CELL {i} FAILED: {type(e).__name__}: {e}")
                print("---- source ----")
                print(src)
                raise
        print("\nall %d code cells executed cleanly" % len(cells))
    finally:
        os.chdir(cwd)

    runs = sorted((nb_dir / "runs").glob("*.json"))
    reports = sorted((nb_dir / "reports").glob("*"))
    print("manifest :", [p.name for p in runs])
    print("reports  :", [p.name for p in reports])
    assert runs, "no manifest was written"
    assert any(p.suffix == ".md" for p in reports), "no report was written"
    assert any(p.suffix == ".png" for p in reports), "no plot was written"

    m = json.loads(runs[0].read_text())
    for key in ("index", "fixture", "schema"):
        assert key in m, f"manifest is missing {key!r}, which 03 re-checks"
    # Self-consistency, not a fixed value: whichever way LEAVE_INDEX_FOR_03 is
    # set, the recorded flag must agree with the state actually left behind.
    # A manifest claiming an index the notebook dropped is the precise failure
    # 02's teardown comment warns about in prose.
    assert m["index"]["left_in_place"] == m["index"]["state_at_write"]["present"], (
        f"manifest claims left_in_place={m['index']['left_in_place']} but the "
        f"state it recorded is {m['index']['state_at_write']}"
    )
    assert m["fixture"]["exact_counts"], "03 diffs these against the live cluster"
    print("manifest carries the keys 03 re-checks")
    shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    main()
