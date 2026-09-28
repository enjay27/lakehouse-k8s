"""Every notebook must be able to find `src/` from its own directory.

The 2026-09-21 merge moved notebooks to new depths and broke this silently: a
notebook whose bootstrap counts `.parent` levels keeps importing fine from the
repo root and fails only when Jupyter is launched in the notebook's own folder,
which is the normal case. Worse, the shift was NOT uniform -- 49 notebooks moved
one level, 3 moved two, and 5 did not move at all -- so any single blanket fix
would have left some broken while looking done.

The bootstraps now walk up for `src/` instead of counting levels. These tests
execute each notebook's real bootstrap text with the working directory set to
that notebook's folder, then import every `src` module the notebook imports by
bare name. Counting is what broke; executing is what proves it fixed.
"""

import json
import pathlib
import re
import subprocess
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
SRCMODS = {p.stem for p in (REPO / "src").glob("*.py")}

#: Deliberately self-contained: hardcoded endpoints, a different realm
#: (DATACORP-PROD), or localhost-by-design teardown. CLAUDE.md documents each.
#: They have no `src/` bootstrap and must not acquire one.
NO_BOOTSTRAP = {
    "diagnostics/ladders/api-sql-profile/06_explain_workbook.ipynb",
    "notebooks/admin/polaris_clean_all.ipynb",
    "notebooks/admin/polaris_rotate_credential.ipynb",
    "notebooks/rbac/polaris_rbac_graph.ipynb",
    "notebooks/scenario/polaris_production_scenario.ipynb",
}


def _notebooks():
    for f in sorted(REPO.rglob("*.ipynb")):
        s = str(f)
        if ".git" in s or "checkpoint" in s or ".venv" in s:
            continue
        yield f


def _code(nb):
    return [
        "".join(c["source"])
        for c in json.load(nb.open())["cells"]
        if c["cell_type"] == "code"
    ]


ALL = list(_notebooks())
WITH_BOOT = [f for f in ALL if any("sys.path.insert" in s for s in _code(f))]
IDS = [str(f.relative_to(REPO)) for f in WITH_BOOT]


def test_the_self_contained_set_has_not_grown():
    """A notebook losing its bootstrap should fail here, not at someone's desk."""
    found = {str(f.relative_to(REPO)) for f in ALL} - {
        str(f.relative_to(REPO)) for f in WITH_BOOT
    }
    assert found == NO_BOOTSTRAP, (
        f"notebooks without a src/ bootstrap changed.\n"
        f"  newly missing one: {sorted(found - NO_BOOTSTRAP)}\n"
        f"  newly having one : {sorted(NO_BOOTSTRAP - found)}"
    )


@pytest.mark.parametrize("nb", WITH_BOOT, ids=IDS)
def test_bootstrap_resolves_from_the_notebooks_own_directory(nb):
    code = _code(nb)
    cell = next(s for s in code if "sys.path.insert" in s)
    lines = cell.split("\n")
    last = max(i for i, l in enumerate(lines) if "sys.path.insert" in l)
    snippet = "\n".join(lines[: last + 1])  # whole prefix, so combined imports survive

    whole = "\n".join(code)
    mods = sorted(
        {
            m
            for m in SRCMODS
            if re.search(r"^\s*(?:import|from)\s+" + m + r"\b", whole, re.M)
        }
    )
    prog = (
        snippet
        + "\nimport importlib\nfor m in %r:\n    importlib.import_module(m)\n" % (mods,)
    )

    r = subprocess.run(
        [sys.executable, "-c", prog],
        cwd=nb.parent,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert r.returncode == 0, (
        f"{nb.relative_to(REPO)} cannot reach src/ when run from its own directory.\n"
        f"  imports: {mods}\n"
        f"  {(r.stderr.strip().splitlines() or ['?'])[-1]}"
    )
