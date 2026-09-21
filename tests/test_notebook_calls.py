"""Bind every client call in `polaris_log_coverage_v2.ipynb` against the real
signature, without a cluster and without executing a cell.

WHY THIS EXISTS. Four helper signatures in the notebook were written from
memory and three were wrong: `create_catalog` takes (name, bucket,
minio_endpoint), not the keyword arguments I invented;
`assign_catalog_role_to_principal_role` takes the catalog FIRST. Two of those
surface as a TypeError forty seconds into a run, after the fixture has been
built -- and the third, the argument order, does not surface at all. It comes
back as a 404 that reads like a Polaris finding.

`inspect.Signature.bind` answers all of it in milliseconds, so it should never
have been a guess.

WHAT THIS CANNOT CATCH, stated so nobody trusts it further than it goes:
**argument ORDER between parameters of the same arity**. `f(catalog, role)` and
`f(role, catalog)` both bind. Only reading the signature, or running the call,
settles that one.
"""

import ast
import inspect
import json
import pathlib
import sys

import pytest

import api_status_matrix as mx  # noqa: E402
import iceberg_rest  # noqa: E402
import log_coverage as lc  # noqa: E402
import os_report as osr  # noqa: E402
import polaris_rest  # noqa: E402
import traffic_helpers as th  # noqa: E402

NOTEBOOK = (
    pathlib.Path(__file__).resolve().parents[1]
    / "diagnostics"
    / "ladders"
    / "log-coverage"
    / "polaris_log_coverage_v2.ipynb"
)

#: The name a cell uses -> what it actually holds.
OWNERS = {
    "adm_pc": polaris_rest.PolarisREST,
    "denied_pc": polaris_rest.PolarisREST,
    "adm_ic": iceberg_rest.IcebergREST,
    "run_ic": iceberg_rest.IcebergREST,
    "run_adm_ic": iceberg_rest.IcebergREST,
    # elect_drive_identity returns these two, by tuple unpacking
    "run_pc": polaris_rest.PolarisREST,
    "run_ic_elected": iceberg_rest.IcebergREST,
    "OS": osr.OSReports,
    "lc": lc,
    "mx": mx,
    "osr": osr,
    "th": th,
}

#: `src/make_traffic.py` is checked by the same walker for the same reason.
#: It IS the notebook's traffic cells, lifted -- so every signature the
#: notebook was checked for is a signature it now makes, and a module gets no
#: exemption a notebook does not.
MODULE = pathlib.Path(__file__).resolve().parents[1] / "src" / "make_traffic.py"


def _calls_in(src):
    for node in ast.walk(ast.parse(src)):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
            continue
        owner = node.func.value
        if isinstance(owner, ast.Name) and owner.id in OWNERS:
            yield owner.id, node.func.attr, node


def _notebook_source():
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    return "\n".join(
        "".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"
    )


def _bind_all(src, floor):
    """Bind every known client call in `src`. Returns the problems found."""
    checked, problems = 0, []
    for who, name, node in _calls_in(src):
        target = OWNERS[who]
        fn = getattr(target, name, None)
        if fn is None:
            problems.append(
                f"{who}.{name} does not exist on "
                f"{getattr(target, '__name__', target)}"
            )
            continue
        if not callable(fn):
            continue
        try:
            sig = inspect.signature(fn)
        except (TypeError, ValueError):
            continue
        if any(isinstance(a, ast.Starred) for a in node.args) or any(
            k.arg is None for k in node.keywords
        ):
            continue  # *args / **kwargs cannot be bound statically
        args = [None] * len(node.args)
        if inspect.isclass(target):
            args = [None] + args  # `self`, for an unbound method
        try:
            sig.bind(*args, **{k.arg: None for k in node.keywords})
            checked += 1
        except TypeError as exc:
            problems.append(f"{who}.{name}(): {exc}   [real signature {sig}]")
    assert (
        checked > floor
    ), f"only {checked} calls checked -- the walker stopped finding them"
    return problems


@pytest.mark.skipif(not MODULE.exists(), reason="make_traffic is not in this tree")
def test_every_client_call_in_make_traffic_binds_to_its_real_signature():
    """The module is the notebook's traffic cells, so it inherits the check.

    `make_traffic` calls `create_catalog`, `grant_privilege` and
    `assign_catalog_role_to_principal_role` -- the three signatures that were
    written from memory and wrong. Being a `.py` file rather than a cell does
    not make them right.
    """
    problems = _bind_all(MODULE.read_text(encoding="utf-8"), floor=15)
    assert not problems, "\n  ".join([""] + sorted(set(problems)))


@pytest.mark.skipif(not NOTEBOOK.exists(), reason="the v2 notebook is not in this tree")
def test_every_client_call_in_the_notebook_binds_to_its_real_signature():
    problems = _bind_all(_notebook_source(), floor=50)
    assert not problems, "\n  ".join([""] + sorted(set(problems)))


@pytest.mark.skipif(not NOTEBOOK.exists(), reason="the v2 notebook is not in this tree")
def test_every_code_cell_parses():
    """`Restart & Run All` fails on cell 1 for a syntax error in cell 30, after
    the fixture is built and the windows are spent."""
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    for i, cell in enumerate(nb["cells"]):
        if cell["cell_type"] == "code":
            ast.parse("".join(cell["source"]))


@pytest.mark.skipif(not NOTEBOOK.exists(), reason="the v2 notebook is not in this tree")
def test_the_notebook_never_reaches_for_a_client_this_check_does_not_know():
    """A new client name in a cell silently escapes the check above. Fail here
    instead, so the coverage of this test is itself covered."""
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    src = "\n".join(
        "".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"
    )
    assigned = set()
    for node in ast.walk(ast.parse(src)):
        if not isinstance(node, ast.Assign):
            continue
        for t in node.targets:
            # TUPLE TARGETS COUNT. `a, pc, ic, name, notes = elect_drive_identity(...)`
            # binds two clients and the first version of this walker saw neither,
            # so the check passed by being unable to look -- the same shape of
            # blind spot it exists to catch.
            for leaf in ast.walk(t):
                if isinstance(leaf, ast.Name):
                    assigned.add(leaf.id)
    clients = {n for n in assigned if n.endswith(("_pc", "_ic")) or n in ("OS",)}
    unknown = clients - set(OWNERS)
    assert (
        not unknown
    ), f"client(s) the signature check does not cover: {sorted(unknown)}"
