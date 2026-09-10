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

    `mounts` says WHERE this stub serves each document; anything else 404s.
    The default reproduces what the first real run measured -- Prism mounts at
    the document's path ROOT and ignores a templated server base path -- so a
    module that goes back to deriving the mount fails here rather than in a
    report.

    `bad_response` holds URL FRAGMENTS whose generated example does not satisfy
    the document -- fragments rather than operation ids because that is all a
    server can see. It produces a violation about the RESPONSE, raised
    identically whatever the request was: the `SPEC_EXAMPLE` case, and 36 rows
    of it were read as invalid requests on the first real run.
    """

    def __init__(
        self,
        enforcing=True,
        routed=True,
        invalid=None,
        mounts=None,
        bad_response=(),
        auth_required=(),
    ):
        self.enforcing = enforcing
        self.routed = routed
        self.mounts = {"management": "", "catalog": ""} if mounts is None else mounts
        self.bad_response = set(bad_response)
        #: URL fragments Prism refuses on a SECURITY scheme -- a bare 401.
        self.auth_required = set(auth_required)
        #: predicate(url, req) -> True when the request violates the spec.
        self.invalid = invalid or (lambda url, req: _looks_malformed(req))
        self.seen = []

    def _path_of(self, url):
        return url.split(".invalid", 1)[-1] or "/"

    def _routed(self, url):
        if not self.routed:
            return False
        api = "management" if "prism-mgmt" in url else "catalog"
        mount = self.mounts.get(api)
        if mount is None:
            return False
        path = self._path_of(url)
        return path.startswith(mount) if mount else not path.startswith("/api/")

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
        if not self._routed(url):
            return FakeResponse(
                404, {"type": "NOT_FOUND", "title": "Route not resolved"}
            )
        if self.auth_required and any(m in url for m in self.auth_required):
            # Prism enforcing a security scheme: no violations, just a 401.
            return FakeResponse(
                401, {"type": "UNAUTHORIZED", "title": "Invalid security"}
            )
        # VALIDATE THE REQUEST FIRST, THEN GENERATE THE RESPONSE. That is the
        # real ordering, and the whole reason a negative control can never
        # legitimately come back SPEC_EXAMPLE: a request Prism rejects never
        # reaches response generation. Written the other way round, this stub
        # let a rejected request come back as a document problem, and the
        # reasoning in `controls` could not have been tested at all.
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
                            "location": ["request", "body", "name"],
                            "severity": "Error",
                            "code": "required",
                            "message": "must have required property 'name'",
                        }
                    ],
                },
            )
        if any(marker in url for marker in self.bad_response):
            return FakeResponse(
                500,
                {
                    "type": "https://stoplight.io/prism/errors#VIOLATIONS",
                    "validation": [
                        {
                            "location": [
                                "response",
                                "body",
                                "metadata",
                                "schemas",
                                "0",
                            ],
                            "severity": "Error",
                            "message": "Response body property "
                            "metadata.schemas.0.fields.0.type must be equal to constant",
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
def test_the_declared_server_path_is_a_candidate_and_not_the_answer():
    """It USED to be the answer, derived from `servers`, and it was wrong for
    the management document: Prism mounts at the path root and ignores a
    templated base path, so all 144 management cells 404'd on the first real
    run. The empty mount is first because that is what was measured."""
    cands = sc.candidate_mounts(SPEC)
    assert cands["management"][0] == ""
    assert "/api/management/v1" in cands["management"]
    assert cands["catalog"] == [""]


def test_the_mount_is_probed_against_the_running_prism():
    """Measured, not derived -- and the report says which candidate won, or
    the next reader re-derives it and gets the same wrong answer."""
    report, _ = _run()
    for api in ("management", "catalog"):
        assert report["mounts"][api]["resolved"] is True
        assert report["mounts"][api]["mount"] == ""
        assert report["mounts"][api]["tried"]


def test_a_prism_serving_the_declared_path_is_found_there_too():
    """The probe must not hardcode the answer that happens to be right today:
    a server that DOES mount at the declared path resolves to it."""
    report, _ = _run(mounts={"management": "/api/management/v1", "catalog": ""})
    assert report["mounts"]["management"]["mount"] == "/api/management/v1"
    assert report["mounts"]["catalog"]["mount"] == ""
    assert report["verdict"] == sc.PASS


def test_an_api_that_routes_nowhere_is_void_not_144_bad_requests():
    """The first real run's shape exactly: every management cell 404. Reported
    as 144 invalid requests it points at the harness; the true answer is that
    Prism is not serving that document there."""
    report, _ = _run(mounts={"management": "/nowhere", "catalog": ""})
    assert report["verdict"] == sc.VOID
    assert report["mounts"]["management"]["resolved"] is False
    assert "NOT ROUTED at any candidate mount" in report["why"]
    assert report["mounts"]["catalog"]["resolved"] is True


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


def test_the_polaris_base_is_stripped_and_the_resolved_mount_prepended():
    ops = {o.api: o for o in mx.load_spec(SPEC)}
    m, c = ops["management"], ops["catalog"]
    declared = {"management": {"mount": "/api/management/v1"}, "catalog": {"mount": ""}}
    assert (
        sc.prism_path(m, m.base + "/catalogs", declared)
        == "/api/management/v1/catalogs"
    )
    assert sc.prism_path(c, c.base + "/v1/config", declared) == "/v1/config"
    # and at the root mount, which is where Prism was measured serving both
    root = {"management": {"mount": ""}, "catalog": {"mount": ""}}
    assert sc.prism_path(m, m.base + "/catalogs", root) == "/catalogs"


def test_a_path_that_does_not_carry_its_recorded_base_raises():
    """Quietly sending it anywhere produces a 404 that reads like a missing
    route, which is a different finding with a different remedy."""
    op = next(o for o in mx.load_spec(SPEC) if o.api == "catalog")
    with pytest.raises(ValueError, match="does not start with its recorded base"):
        sc.prism_path(op, "/somewhere/else", {"catalog": {"mount": ""}})


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


def test_the_controls_are_built_from_the_real_grid():
    """A control written by hand can pass while the thing it vouches for is
    built differently."""
    report, _ = _run()
    ops = {c.op.op_id for c in mx.cells(mx.load_spec(SPEC))}
    for api, pair in report["controls"].items():
        if not isinstance(pair, dict):
            continue
        for name in ("negative", "positive"):
            if pair.get(name):
                assert pair[name]["op_id"] in ops


def test_a_clean_run_passes_and_reports_both_controls_ok():
    report, _ = _run()
    assert report["verdict"] == sc.PASS
    assert report["controls"]["ok"] is True
    assert report["cells"] == len(mx.cells(mx.load_spec(SPEC)))
    assert report["not_routed"] == 0


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

    with pytest.raises(sc.PrismUnavailable, match="could not reach Prism"):
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


# ----------------------------------------------------------------------
# request violations are not response violations
# ----------------------------------------------------------------------
def test_a_response_violation_is_not_a_verdict_on_the_request():
    """The first real run returned 36 of these and every one was counted as an
    invalid request. The giveaway that they cannot be: the SAME violation
    appears for targets 2, 401, 403, 404 and 409 of one operation -- identical
    whatever was sent."""
    body = {
        "validation": [
            {
                "location": ["response", "body", "metadata"],
                "message": "Response body property x must be equal to constant",
            }
        ]
    }
    assert sc.classify(500, body) == sc.SPEC_EXAMPLE
    assert sc.classify(500, body) != sc.REJECTED


@pytest.mark.parametrize(
    "violation",
    [
        {"location": ["response", "body"], "message": "bad"},
        {"location": "response.body.x", "message": "bad"},
        {"location": [], "message": "Response body property x must be a string"},
    ],
)
def test_a_response_violation_is_recognised_in_every_shape_prism_writes_it(violation):
    assert sc.classify(500, {"validation": [violation]}) == sc.SPEC_EXAMPLE


def test_a_request_violation_still_rejects():
    body = {
        "validation": [
            {
                "location": ["request", "body", "name"],
                "message": "must have required property 'name'",
            }
        ]
    }
    assert sc.classify(422, body) == sc.REJECTED


def test_a_body_carrying_both_kinds_is_a_rejection():
    """The request half decides, because that is the half being asked about."""
    body = {
        "validation": [
            {"location": ["response", "body"], "message": "Response body property x"},
            {"location": ["request", "body"], "message": "must have required property"},
        ]
    }
    assert sc.classify(422, body) == sc.REJECTED


def test_spec_example_rows_are_not_counted_as_failures():
    """They are not this repo's to fix and not Polaris's either. Counted as
    unexpected cells they would fail a run whose requests were all correct."""
    report, _ = _run(bad_response=["/tables", "/register"])
    assert report["spec_examples"] > 0
    assert not [r for r in report["unexpected"] if r["verdict"] == sc.SPEC_EXAMPLE]
    assert report["verdict"] == sc.PASS


def test_spec_findings_group_by_property_rather_than_listing_every_cell():
    """One property accounted for 23 rows across six operations on the first
    real run. Thirty-six repetitions of one sentence is not six findings."""
    report, _ = _run(bad_response=["/tables", "/register"])
    findings = report["spec_findings"]
    assert findings and all(f["about"] == "spec" for f in findings)
    assert len(findings) < report["spec_examples"]
    assert sum(f["cells"] for f in findings) == report["spec_examples"]


def test_the_report_keeps_spec_build_and_request_findings_in_three_sections():
    report, _ = _run(bad_response=["/register"])
    text = sc.render_report(report)
    assert "Spec findings -- about the DOCUMENT" in text
    assert "Build findings -- about Polaris" in text
    # and the spec section says, in words, that it is not about any request --
    # a reader who takes these for harness failures fixes the wrong thing.
    assert "Nothing here is a statement about a request" in text
    assert "Where Prism is serving each document" in text


# ----------------------------------------------------------------------
# one control per api
# ----------------------------------------------------------------------
def test_there_is_a_control_pair_for_every_api_the_grid_drives():
    """Both controls landed on CATALOG operations on the first real run, so
    they reported green while all 144 management cells 404'd. A control that
    cannot fail for the thing it vouches for is the failure this module exists
    to prevent, and it was inside the module."""
    report, _ = _run()
    apis = {c.op.api for c in mx.cells(mx.load_spec(SPEC))}
    for api in apis:
        pair = report["controls"][api]
        assert pair["negative"] and pair["positive"], api
        assert pair["negative"]["api"] == api
        assert pair["positive"]["api"] == api


def test_a_management_only_failure_is_caught_by_the_management_control():
    """The exact first-run shape: catalog healthy, management not."""
    report, _ = _run(mounts={"management": "/nowhere", "catalog": ""})
    assert report["verdict"] == sc.VOID
    assert "management" in report["why"]


def test_neither_apis_negative_control_is_the_form_encoded_operation():
    report, _ = _run()
    for api, pair in report["controls"].items():
        if isinstance(pair, dict) and pair.get("negative"):
            assert pair["negative"]["op_id"] not in mx.FORM_ENCODED


def test_the_report_prints_a_status_for_every_control_and_odd_cell():
    """An ERROR row with no status is undiagnosable -- three `getToken` rows
    came back that way on the first real run and could not be read at all."""
    report, _ = _run()
    text = sc.render_report(report)
    assert "| status |" in text or "status |" in text
    for api, pair in report["controls"].items():
        if isinstance(pair, dict) and pair.get("negative"):
            assert pair["negative"]["status"] is not None


# ----------------------------------------------------------------------
# a security 401 is not a verdict on the request
# ----------------------------------------------------------------------
def test_a_bare_401_is_a_security_refusal_not_a_malformed_request():
    """`getToken` declares no `security` of its own, inherits the document's
    global requirement, and Prism then demands a bearer token in order to
    obtain a bearer token. The request is right: an OAuth token endpoint
    carries credentials in the form body. Three unreadable `error` rows on the
    second real run."""
    assert sc.classify(401, {}) == sc.AUTH_REQUIRED
    assert sc.classify(401, {"title": "Unauthorized"}) == sc.AUTH_REQUIRED


def test_a_401_that_carries_request_violations_is_still_a_rejection():
    """Security is checked before the 400/422 rule, but never before the
    violations themselves -- a malformed request must not hide behind a 401."""
    body = {"validation": [{"location": ["request", "body"], "message": "required"}]}
    assert sc.classify(401, body) == sc.REJECTED


def test_neither_kind_of_document_verdict_counts_as_a_failure():
    assert sc.SPEC_EXAMPLE in sc.NOT_ABOUT_THE_REQUEST
    assert sc.AUTH_REQUIRED in sc.NOT_ABOUT_THE_REQUEST
    assert sc.REJECTED not in sc.NOT_ABOUT_THE_REQUEST
    assert sc.ERROR not in sc.NOT_ABOUT_THE_REQUEST


def test_auth_required_rows_are_reported_as_a_spec_finding():
    findings = sc.auth_findings(
        [{"op_id": "getToken", "target": 2}, {"op_id": "getToken", "target": 401}],
        SPEC,
    )
    assert findings and findings[0]["about"] == "spec"
    assert "getToken" in findings[0]["title"]
    assert findings == [] or "security scheme" in findings[0]["title"]


def test_a_security_401_reaches_the_report_without_failing_the_run():
    """Three `getToken` rows came back `error` on the second real run and could
    not be read. They must be visible, explained, and not counted against the
    requests."""
    report, _ = _run(auth_required=["/oauth/tokens"])
    assert report["auth_required"] > 0
    assert not [r for r in report["unexpected"] if r["verdict"] == sc.AUTH_REQUIRED]
    assert report["verdict"] != sc.VOID
    assert any("security scheme" in f["title"] for f in report["spec_findings"])


def test_no_auth_rows_means_no_auth_finding():
    assert sc.auth_findings([], SPEC) == []


# ----------------------------------------------------------------------
# the positive control asks whether a valid request GOT THROUGH
# ----------------------------------------------------------------------
def test_the_positive_control_passes_when_only_the_response_was_invalid():
    """The second real run VOIDed over `listCatalogs`, whose response the
    document cannot describe, while the check was working perfectly. The
    request got through; Prism failed to build its own example."""
    report, _ = _run(bad_response=["/catalogs"])
    assert report["verdict"] != sc.VOID, report["why"]
    mgmt = report["controls"]["management"]["positive"]
    assert mgmt["verdict"] == sc.SPEC_EXAMPLE and mgmt["ok"] is True


def test_the_negative_control_is_not_loosened_the_same_way():
    """A request Prism REJECTS never reaches response generation, so a
    negative control can never legitimately come back SPEC_EXAMPLE. Loosening
    it would let a non-enforcing Prism through, which is the one thing the
    controls exist for."""
    import inspect

    src = inspect.getsource(sc.controls)
    assert 'if name == "positive"' in src
    report, _ = _run(enforcing=False)
    assert report["verdict"] == sc.VOID


# ----------------------------------------------------------------------
# the 400 cells the documents say cannot be malformed by omission
# ----------------------------------------------------------------------
def test_the_unmalformable_cells_are_computed_from_the_documents_alone():
    """No Prism and no cluster. Prism's second run surfaced 9 of them; the
    other three were masked behind other verdicts, which is the whole argument
    for computing this statically rather than waiting for a run."""
    rows = sc.unmalformable_cells(SPEC)
    ops = {r["op_id"] for r in rows}
    assert {"updateProperties", "createPrincipal", "getToken", "updateCatalog"} <= ops
    assert (
        "createCatalog" not in ops
    ), "createCatalog requires `catalog` and IS malformable"
    assert "createTable" not in ops, "createTable requires name and schema"


def test_every_unmalformable_op_really_has_no_required_fields():
    """The claim is checkable against the document, so check it rather than
    trusting the helper that made it."""
    import yaml

    docs = {
        f.name: yaml.safe_load(f.read_text())
        for f in list(SPEC.glob("*.yml")) + list(SPEC.glob("*.yaml"))
    }
    ops = {o.op_id: o for o in mx.load_spec(SPEC)}
    for row in sc.unmalformable_cells(SPEC):
        op = ops[row["op_id"]]
        sch = sc.request_schema(docs[op.source], op.op_id)
        assert not (sch or {}).get("required"), row["op_id"]


def test_a_malformable_op_resolves_its_required_fields_through_the_ref():
    """One `$ref` hop is all these documents use -- and a helper that failed to
    follow it would call every operation unmalformable and the finding would
    quietly become "all 27"."""
    import yaml

    doc = yaml.safe_load((SPEC / "polaris-management-service.yml").read_text())
    sch = sc.request_schema(doc, "createCatalog")
    assert sch and sch.get("required") == ["catalog"]


def test_the_unmalformable_cells_are_one_harness_finding_not_twelve():
    findings = sc.harness_findings(SPEC)
    assert len(findings) == 1
    f = findings[0]
    assert f["about"] == "harness"
    assert len(f["operations"]) == len(sc.unmalformable_cells(SPEC))
    assert f["remedy"]


def test_a_harness_finding_is_not_a_polaris_or_pipeline_finding():
    """Four audiences, four sections. A cell this repo drives wrongly must not
    be sent to `local-k8s` as work or read as a fact about Polaris."""
    report, _ = _run()
    assert all(f["about"] == "harness" for f in report["harness_findings"])
    assert all(f["about"] == "polaris" for f in report["build_findings"])
    assert all(f["about"] == "spec" for f in report["spec_findings"])
    text = sc.render_report(report)
    assert "Harness findings -- THIS repo's" in text


def test_spec_check_imports_no_logging_module():
    """It reaches `make_traffic` and the whole matrix, so if the boundary were
    going to leak through anything, it would be through here."""
    graph = _graph_from("spec_check")
    assert {
        "api_status_matrix",
        "make_traffic",
    } <= graph, "the walker is not following imports and would pass on anything"
    assert not (graph & LOGGING_MODULES)
