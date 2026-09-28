"""Every URL PolarisREST builds must exist in the vendored OpenAPI documents.

A wrong path is indistinguishable from a missing entity: both answer 404. That
ambiguity already cost a live run -- `polaris_availability_test` asked port 8181
for `/q/health` and read the 404 as a health failure, when `/q/health` is the
Quarkus management interface on 8182 and is not a Polaris API at all.

This checks the client against `log-coverage/spec/`, the same documents that are
the denominator for the 297-cell status matrix, so the client and the matrix can
never disagree about what a path is.

The documents are gitignored downloads (`fetch_specs.sh`). When they are absent
these tests skip -- loudly, and naming the fix.
"""

import inspect
import re

import pytest

pytest.importorskip("yaml")
import yaml  # noqa: E402

import polaris_rest  # noqa: E402

SPEC_DIR = __import__("pathlib").Path(__file__).resolve().parents[1] / (
    "diagnostics/ladders/log-coverage/spec"
)
MGMT = SPEC_DIR / "polaris-management-service.yml"
CAT = SPEC_DIR / "rest-catalog-open-api.yaml"

needs_specs = pytest.mark.skipif(
    not (MGMT.exists() and CAT.exists()),
    reason=f"OpenAPI documents absent from {SPEC_DIR} -- run log-coverage/fetch_specs.sh",
)


def _placeholders(path):
    """Collapse every {named} segment so {name} and {catalogName} compare equal."""
    return re.sub(r"\{[^}]+\}", "{X}", path)


def _built_urls():
    """(which_base, normalized_path) for every f-string URL in polaris_rest."""
    src = inspect.getsource(polaris_rest)
    out = set()
    for which, tail in re.findall(r'f"\{self\.base_(mgmt|cat)\}([^"]*)"', src):
        t = re.sub(r"\{self\._ns_path\([^)]*\)\}", "{namespace}", tail)
        out.add((which, _placeholders(t).split("?")[0].rstrip("/")))
    return sorted(out)


@needs_specs
def test_every_management_path_exists_in_the_spec():
    spec = {_placeholders(p) for p in yaml.safe_load(MGMT.read_text())["paths"]}
    built = [p for w, p in _built_urls() if w == "mgmt"]
    assert (
        built
    ), "found no management URLs in polaris_rest -- the extractor regex broke"
    assert not [p for p in built if p not in spec], (
        f"PolarisREST builds management paths the 1.6.0 document does not define: "
        f"{[p for p in built if p not in spec]}"
    )


@needs_specs
def test_every_catalog_path_exists_in_the_spec():
    # base_cat already carries /v1, so a spec path /v1/{prefix}/x is /{X}/x here.
    spec = {
        _placeholders(p[3:])
        for p in yaml.safe_load(CAT.read_text())["paths"]
        if p.startswith("/v1/")
    }
    built = [p for w, p in _built_urls() if w == "cat"]
    assert built, "found no catalog URLs in polaris_rest -- the extractor regex broke"
    assert not [p for p in built if p not in spec], (
        f"PolarisREST builds catalog paths the 1.6.0 document does not define: "
        f"{[p for p in built if p not in spec]}"
    )


def test_the_quarkus_management_interface_is_not_a_polaris_api():
    """/q/health belongs to POLARIS_MGMT_URL, never POLARIS_URL."""
    import nb_support

    assert nb_support.QUARKUS_MGMT_PORT == 8182
    src = inspect.getsource(polaris_rest)
    assert "/q/health" not in src, (
        "polaris_rest must not reach the Quarkus interface -- it derives both of its "
        "bases from the Polaris API port, so a /q/ path there would 404"
    )
