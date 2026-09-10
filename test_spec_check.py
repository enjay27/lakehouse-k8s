"""Tests for `src/spec_check.py` -- request conformance through Prism.

**The real Prism has never run against this code, and that is stated rather
than hidden.** `npm` answers 403 through the org egress policy on every machine
a Cowork session can reach, so Prism could not be installed to build this
against. What runs here is a stub that speaks Prism's shape: a 422 carrying a
`validation` array for an invalid request, a 404 for an unrouted path, a 200
otherwise. The first real run is Kade's, and it is the one that confirms the
mount points.

So these tests establish that **the logic around Prism is right** -- the
two-sided expectation, the two controls, the mount derivation, the
not-routed/rejected split. They do not establish that Prism agrees with the
stub about what is invalid. Read them as exactly that much.
"""

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "src"))

import api_status_matrix as mx  # noqa: E402
import make_traffic as mt  # noqa: E402
import spec_check as sc  # noqa: E402

SPEC = pathlib.Path(__file__).resolve().parent / "log-coverage" / "spec"
PRISM = {
    "management": "http://prism-mgmt.invalid",
    "catalog": "http://prism-cat.invalid",
}

pytestmark = pytest.mark.skipif(
    not SPEC.is_dir() or not any(SPEC.iterdir()),
    reason="the vendored specs are not in this tree",
)


# ----------------------------------------------------------------------
# a stub that answers the way Prism does
# ----------------------------------------------------------------------
class FakeResponse:
    def __init__(self, status, payload):
        self.status_code = status
        self._payload = payload
        self.text = str(payload)

    def json(self):
        return self._payload


class FakePrism:
    """Prism's shape, and nothing of its judgement.

    `enforcing=False` reproduces `prism mock` WITHOUT `--errors`: it sees the
    violation and answers 200 anyway. That mode is the reason the controls
    exist, so the stub has to be able to be in it.
    """

    def __init__(self, enforcing=True, routed=True, invalid=None):
        self.enforcing = enforcing
        self.routed = routed
        #: predicate(url, req) -> True when the request violates the spec.
        self.invalid = invalid or (lambda url, req: _looks_malformed(req))
        self.seen = []

    def request(
        self, method, url, params=None, headers=None, json=None, data=None, timeout=None
    ):
        req = {
            "method": method,
            "params": params,
            "headers": headers,
            "json": json,
            "data": data,
        }
        self.seen.append((url, req))
        if not self.routed:
            return FakeResponse(
                404, {"type": "NOT_FOUND", "title": "Route not resolved"}
            )
        if self.invalid(url, req):
            if not self.enforcing:
                return FakeResponse(200, {"ok": True})
            return FakeResponse(
                422,
                {
                    "type": "https://stoplight.io/prism/errors#UNPROCESSABLE_ENTITY",
                    "title": "Invalid request",
                    "status": 422,
                    "validation": [
                        {
                            "location": ["body", "name"],
                            "severity": "Error",
                            "code": "required",
                            "message": "must have required property 'name'",
                        }
                    ],
                },
            )
        return FakeResponse(200, {"ok": True})


def _looks_malformed(req):
    """The marker `MALFORMED_BODY` puts in a body, in EITHER encoding.

    Reading only `json` made the stub call the one form-encoded operation
    valid, which is how the naive negative control looked like it passed.
    """
    for body in (req.get("json"), req.get("data")):
        if isinstance(body, dict) and "matrix" in body and len(body) == 1:
            return True
    return False


def _run(**kw):
    session = FakePrism(**kw)
    report = sc.check_requests(SPEC, PRISM, session=session, run="t")
    return report, session


# ----------------------------------------------------------------------
# mounting, derived from the documents themselves
# ----------------------------------------------------------------------
def test_the_two_specs_mount_at_different_paths():
    """The difference is invisible until every catalog request 404s: the
    management document carries its prefix in `servers`, the Iceberg one
    defaults `basePath` to empty and gets `/api/catalog` from POLARIS."""
    mounts = sc.prism_mounts(SPEC)
    assert mounts["management"] == "/api/management/v1"
    assert mounts["catalog"] == ""


def test_a_templated_server_url_resolves_to_its_defaults():
    assert (
        sc._server_path(
            {
                "url": "{scheme}://{host}/{basePath}",
                "variables": {
                    "scheme": {"default": "https"},
                    "host": {"default": "localhost"},
                    "basePath": {"default": ""},
                },
            }
        )
        == ""
    )
    assert (
        sc._server_path(
            {
                "url": "{scheme}://{host}/api/management/v1",
                "variables": {"scheme": {"default": "https"}, "host": {"default": "h"}},
            }
        )
        == "/api/management/v1"
    )


def test_the_polaris_base_is_stripped_and_the_spec_mount_prepended():
    ops = {o.api: o for o in mx.load_spec(SPEC)}
    mounts = sc.prism_mounts(SPEC)
    m, c = ops["management"], ops["catalog"]
    assert (
        sc.prism_path(m, m.base + "/catalogs", mounts) == "/api/management/v1/catalogs"
    )
    assert sc.prism_path(c, c.base + "/v1/config", mounts) == "/v1/config"


def test_a_path_that_does_not_carry_its_recorded_base_raises():
    """Quietly sending it anywhere produces a 404 that reads like a missing
    route, which is a different finding with a different remedy."""
    op = next(o for o in mx.load_spec(SPEC) if o.api == "catalog")
    with pytest.raises(ValueError, match="does not start with its recorded base"):
        sc.prism_path(op, "/somewhere/else", sc.prism_mounts(SPEC))


# ----------------------------------------------------------------------
# the two-sided expectation
# ----------------------------------------------------------------------
def test_only_a_body_carrying_400_cell_is_expected_to_be_rejected():
    grid = mx.cells(mx.load_spec(SPEC))
    for cell in grid:
        want = sc.expectation(cell)
        if cell.target == 400 and cell.op.has_body:
            assert want == sc.REJECTED, cell.op.op_id
        else:
            assert want == sc.ACCEPTED, f"{cell.op.op_id} target {cell.target}"


def test_get_config_without_warehouse_stays_spec_valid():
    """`warehouse` is `required: false` in the Iceberg document, so the bare
    call does NOT violate the spec -- even though this build answers 400."""
    grid = mx.cells(mx.load_spec(SPEC))
    cell = next(c for c in grid if c.op.op_id == "getConfig" and c.target == 400)
    assert not cell.op.has_body
    assert sc.expectation(cell) == sc.ACCEPTED


def test_both_sides_of_the_expectation_are_actually_present_in_the_grid():
    """An assertion that only ever sees one side is a one-sided check wearing
    a two-sided docstring."""
    wants = {sc.expectation(c) for c in mx.cells(mx.load_spec(SPEC))}
    assert wants == {sc.ACCEPTED, sc.REJECTED}


# ----------------------------------------------------------------------
# classification
# ----------------------------------------------------------------------
def test_a_404_without_violations_is_not_routed_not_rejected():
    """Folding them together reports a mounting mistake as 286 invalid
    requests, and the two have opposite remedies."""
    assert sc.classify(404, {"title": "Route not resolved"}) == sc.NOT_ROUTED
    assert sc.classify(422, {"validation": [{"message": "x"}]}) == sc.REJECTED
    assert sc.classify(200, {"ok": True}) == sc.ACCEPTED
    assert sc.classify(None, None) == sc.ERROR


def test_a_404_that_does_carry_violations_is_a_rejection():
    assert (
        sc.classify(404, {"validation": [{"message": "bad path param"}]}) == sc.REJECTED
    )


@pytest.mark.parametrize("key", ["validation", "violations", "errors"])
def test_violations_are_read_under_whichever_key_this_prism_uses(key):
    assert sc.classify(422, {key: [{"message": "m"}]}) == sc.REJECTED


def test_violation_summary_survives_a_shape_it_does_not_know():
    assert sc.violation_summary({"validation": ["just a string"]}) == "just a string"
    assert sc.violation_summary({}) == ""


# ----------------------------------------------------------------------
# THE CONTROLS -- the part that stops this passing without having looked
# ----------------------------------------------------------------------
def test_a_prism_that_is_not_enforcing_makes_the_pass_void_not_pass():
    """`prism mock` without `--errors` answers 200 to a violation. Every
    request then reads as valid, and the run would report a perfect grid."""
    report, _ = _run(enforcing=False)
    assert report["verdict"] == sc.VOID
    assert "--errors" in report["why"]
    assert report["verdict"] != sc.PASS


def test_a_void_report_says_plainly_that_nothing_was_measured():
    report, _ = _run(enforcing=False)
    text = sc.render_report(report)
    assert "VOID" in text and "nothing was measured" in text
    assert "not a pass" in text


def test_a_wrong_mount_makes_the_pass_void_rather_than_286_failures():
    """And it must SAY the mount is wrong. Diagnosing a 404 as "Prism is not
    enforcing" sends the reader to `--errors`, which is not the fix and which
    leaves the real cause in place."""
    report, _ = _run(routed=False)
    assert report["verdict"] == sc.VOID
    assert "NOT ROUTED" in report["why"]
    assert "--errors" not in report["why"]


def test_the_negative_control_is_never_the_form_encoded_operation():
    """`getToken` is the only one, the grid's sort order reaches it first, and
    whether Prism validates a form body against a schema is unsettled. Letting
    it vouch for the other 285 makes the least representative cell the
    control -- which is how this check first reported VOID on a healthy stub."""
    report, _ = _run()
    assert report["controls"]["negative"]["op_id"] not in mx.FORM_ENCODED


def test_the_controls_are_built_from_the_real_grid():
    """A control written by hand can pass while the thing it vouches for is
    built differently."""
    report, _ = _run()
    ops = {c.op.op_id for c in mx.cells(mx.load_spec(SPEC))}
    assert report["controls"]["negative"]["op_id"] in ops
    assert report["controls"]["positive"]["op_id"] in ops


def test_a_clean_run_passes_and_reports_both_controls_ok():
    report, _ = _run()
    assert report["verdict"] == sc.PASS
    assert report["controls"]["ok"] is True
    assert report["cells"] == len(mx.cells(mx.load_spec(SPEC)))


# ----------------------------------------------------------------------
# the pass itself
# ----------------------------------------------------------------------
def test_every_cell_is_sent_somewhere_and_nothing_touches_polaris():
    report, session = _run()
    assert len(session.seen) >= report["cells"]
    for url, _req in session.seen:
        assert url.startswith(("http://prism-mgmt.invalid", "http://prism-cat.invalid"))


def _except_controls(judgement):
    """A stub judgement that applies to the GRID only; the controls stay honest.

    Needed because a Prism that is globally wrong VOIDs the run -- correctly,
    and that is tested below. To see a FAIL you have to break something the
    controls do not vouch for, which is also the only realistic shape: a real
    Prism does not accept or reject everything.
    """

    def go(url, req):
        rid = (req.get("headers") or {}).get("Polaris-Request-Id", "")
        if rid in ("speccheck-negative", "speccheck-positive"):
            return _looks_malformed(req)
        return judgement(url, req)

    return go


def test_a_spec_valid_malformed_body_is_a_failure_not_a_pass():
    """A `400` cell whose body the spec ACCEPTS is a cell that is not testing
    what it claims to -- the harness believes it sent something broken and it
    did not."""
    report, _ = _run(invalid=_except_controls(lambda url, req: False))
    assert report["verdict"] == sc.FAIL
    bad = [r for r in report["unexpected"] if r["expected"] == sc.REJECTED]
    assert bad and all(r["verdict"] == sc.ACCEPTED for r in bad)


def test_a_well_formed_request_that_prism_rejects_is_a_failure():
    report, _ = _run(invalid=_except_controls(lambda url, req: True))
    assert report["verdict"] == sc.FAIL
    assert any(r["expected"] == sc.ACCEPTED for r in report["unexpected"])


def test_a_prism_that_accepts_everything_is_void_not_a_perfect_grid():
    """This is the failure the controls exist for, and it is worth its own
    test: a Prism that never rejects looks EXACTLY like a grid where every
    request is valid. 286 accepted cells and a green verdict would be the most
    convincing wrong answer this module could produce."""
    report, _ = _run(invalid=lambda url, req: False)
    assert report["verdict"] == sc.VOID
    assert report["accepted"] == report["cells"]


def test_a_prism_that_rejects_everything_is_void_not_286_findings():
    """The mirror. Something is wrong with Prism or the documents, and
    reporting it as 286 invalid requests would send the reader to the harness."""
    report, _ = _run(invalid=lambda url, req: True)
    assert report["verdict"] == sc.VOID


def test_the_report_counts_reconcile_with_the_rows():
    report, _ = _run()
    assert report["accepted"] + report["rejected"] + report["not_routed"] + report[
        "errors"
    ] == len(report["rows"])


def test_prism_being_down_is_raised_not_reported_as_invalid_requests():
    """Nothing was measured, so it must not render as a grid of failures."""

    class Dead(FakePrism):
        def request(self, *a, **k):
            raise ConnectionError("connection refused")

    with pytest.raises(sc.PrismUnavailable, match="control could not reach Prism"):
        sc.check_requests(SPEC, PRISM, session=Dead(), run="t")


# ----------------------------------------------------------------------
# build findings stay on Polaris's side of the line
# ----------------------------------------------------------------------
def test_get_config_accepted_by_the_spec_is_a_build_finding():
    report, _ = _run()
    titles = [f["title"] for f in report["build_findings"]]
    assert any("getConfig" in t for t in titles)
    assert all(f["about"] == "polaris" for f in report["build_findings"])


def test_a_build_finding_is_not_counted_as_an_unexpected_cell():
    """SCENARIO §6: the two report sections must never merge. A divergence
    between Polaris and its own spec is not a failure of this check."""
    report, _ = _run()
    assert report["build_findings"]
    assert report["verdict"] == sc.PASS
    assert not report["unexpected"]


# ----------------------------------------------------------------------
# the boundary still holds
# ----------------------------------------------------------------------
#: The same set `test_make_traffic` guards, restated rather than imported:
#: there is no `conftest.py`, so one test module cannot import another, and a
#: cross-file import that silently fails would take the guard with it.
LOGGING_MODULES = frozenset(
    {"log_coverage", "os_report", "vlogs", "opensearch_alert_provisioner"}
)


def _imports_of(path):
    import ast

    out = set()
    for node in ast.walk(ast.parse(pathlib.Path(path).read_text())):
        if isinstance(node, ast.Import):
            out.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            out.add(node.module.split(".")[0])
    return out


def _graph_from(start):
    src = pathlib.Path(__file__).resolve().parent / "src"
    seen, queue = set(), [start]
    while queue:
        name = queue.pop()
        if name in seen:
            continue
        seen.add(name)
        path = src / f"{name}.py"
        if path.exists():
            queue.extend(_imports_of(path))
    return seen


def test_spec_check_imports_no_logging_module():
    """It reaches `make_traffic` and the whole matrix, so if the boundary were
    going to leak through anything, it would be through here."""
    graph = _graph_from("spec_check")
    assert {
        "api_status_matrix",
        "make_traffic",
    } <= graph, "the walker is not following imports and would pass on anything"
    assert not (graph & LOGGING_MODULES)
