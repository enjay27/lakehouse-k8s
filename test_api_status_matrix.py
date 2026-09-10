"""Tests for `src/api_status_matrix.py` -- the operation x status grid.

The grid is derived from the vendored specs, so these tests read the real
`log-coverage/spec/` documents rather than a fixture. That is deliberate: the
denominator of the whole run is those two files, and a test against a hand-made
copy would keep passing after `fetch_specs.sh` vendored a new version.

Nothing here touches the network.
"""

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "src"))

import api_status_matrix as m  # noqa: E402

SPEC_DIR = pathlib.Path(__file__).parent / "log-coverage" / "spec"


@pytest.fixture(scope="module")
def ops():
    return m.load_spec(SPEC_DIR)


@pytest.fixture
def binding():
    """Everything `bind_path` and `payload_for` need, with no cluster."""
    return {
        "catalog": "cat",
        "namespace": "ns",
        "table": "tbl",
        "view": "vw",
        "principalName": "prin",
        "principalRoleName": "prole",
        "catalogRoleName": "crole",
        "plan-id": "plan-1",
        "new_catalog": "cat2",
        "new_namespace": "ns2",
        "new_table": "tbl2",
        "new_view": "vw2",
        "new_principal": "prin2",
        "new_principal_role": "prole2",
        "new_catalog_role": "crole2",
        "renamed_table": "tbl_r",
        "renamed_view": "vw_r",
        "doomed_catalog": "cat_doomed",
        "doomed_namespace": "ns_doomed",
        "doomed_table": "tbl_doomed",
        "doomed_view": "vw_doomed",
        "doomed_principal": "prin_doomed",
        "doomed_principal_role": "prole_doomed",
        "doomed_catalog_role": "crole_doomed",
        "entity_version": 1,
        "run": "1789000000",
        "base_location": "s3a://bucket/cat2/",
        "allowed_location": "s3a://bucket/",
        "s3_endpoint": "http://minio:9000",
        "s3_endpoint_internal": "http://minio.svc:9000",
        "metadata_location": "s3://bucket/cat2/meta.json",
        "client_id": "id",
        "client_secret": "secret",
    }


# ----------------------------------------------------------------------
# the denominator
# ----------------------------------------------------------------------
def test_the_spec_yields_the_operations_the_plan_counted(ops):
    """63, split 33 management / 30 catalog. If this changes, `fetch_specs.sh`
    vendored a new version -- read the diff before touching the number."""
    assert len(ops) == 63
    assert sum(1 for o in ops if o.api == "management") == 33
    assert sum(1 for o in ops if o.api == "catalog") == 30


def test_an_empty_spec_directory_is_an_error_not_an_empty_grid(tmp_path):
    """A missing spec must not read as "nothing to cover"."""
    with pytest.raises(m.SpecUnavailable):
        m.load_spec(tmp_path)


def test_the_base_path_comes_from_the_document_not_from_the_template(ops):
    by_id = {o.op_id: o for o in ops}
    assert by_id["createCatalog"].full_template == "/api/management/v1/catalogs"
    assert by_id["loadTable"].full_template == (
        "/api/catalog/v1/{prefix}/namespaces/{namespace}/tables/{table}"
    )


def test_declared_codes_are_read_off_the_document(ops):
    by_id = {o.op_id: o for o in ops}
    assert "201" in by_id["createCatalog"].declared
    assert "409" in by_id["createNamespace"].declared
    assert by_id["listCatalogRoles"].declared == ("200",)


# ----------------------------------------------------------------------
# binding
# ----------------------------------------------------------------------
def test_every_operation_binds_with_no_brace_left_behind(ops, binding):
    """A literal `{table}` in a URL is a 404 that looks like a finding."""
    for op in ops:
        path = m.bind_path(op, binding)
        assert "{" not in path and "}" not in path, op.op_id


def test_prefix_and_catalogName_are_the_same_value(ops, binding):
    by_id = {o.op_id: o for o in ops}
    assert m.bind_path(by_id["loadTable"], binding).startswith("/api/catalog/v1/cat/")
    assert (
        m.bind_path(by_id["getCatalog"], binding) == "/api/management/v1/catalogs/cat"
    )


def test_the_404_rule_breaks_the_LAST_parameter(ops, binding):
    """Breaking an earlier one 404s on a different endpoint: a bad catalog in
    `/catalogs/{c}/catalog-roles/{cr}` never reaches the role handler."""
    op = {o.op_id: o for o in ops}["getCatalogRole"]
    broken = m.bind_path(op, binding, break_param=True)
    assert broken == f"/api/management/v1/catalogs/cat/catalog-roles/{m.MISSING}"


def test_a_missing_fixture_value_raises_rather_than_guessing(ops):
    op = {o.op_id: o for o in ops}["loadTable"]
    with pytest.raises(KeyError):
        m.bind_path(op, {"catalog": "cat"})


# ----------------------------------------------------------------------
# payloads
# ----------------------------------------------------------------------
def test_every_body_carrying_operation_has_a_payload(ops):
    """THE COMPLETENESS TEST. A new endpoint in a re-vendored spec must not be
    drivable with an empty body and recorded as covered at 400."""
    missing = sorted(o.op_id for o in ops if o.has_body and o.op_id not in m.PAYLOADS)
    assert not missing, f"operations with a requestBody and no payload: {missing}"


def test_every_payload_builds_against_the_binding(ops, binding):
    for op in ops:
        body = m.payload_for(op, binding)
        if op.has_body:
            assert isinstance(body, dict) and body, op.op_id
        else:
            assert body is None, op.op_id


def test_a_body_carrying_operation_with_no_payload_raises(binding):
    fake = m.Operation(
        "newEndpoint",
        "post",
        "/x",
        "catalog",
        "/api/catalog",
        ["200"],
        [],
        True,
        "spec.yaml",
    )
    with pytest.raises(KeyError, match="no PAYLOADS entry"):
        m.payload_for(fake, binding)


def test_payloads_are_copies_so_a_driver_cannot_mutate_the_registry(ops, binding):
    op = {o.op_id: o for o in ops}["createNamespace"]
    first = m.payload_for(op, binding)
    first["properties"]["scribbled"] = True
    assert "scribbled" not in m.payload_for(op, binding)["properties"]


def test_the_token_endpoint_is_form_encoded(ops, binding):
    """Sending it as JSON returns a 400 that reads as a malformed-body finding
    and is a harness bug."""
    assert "getToken" in m.FORM_ENCODED
    body = m.payload_for({o.op_id: o for o in ops}["getToken"], binding)
    assert body["grant_type"] == "client_credentials"


def test_the_malformed_body_is_not_an_empty_object():
    """Several Polaris endpoints accept `{}` and answer 2xx, which would make
    the 400 cell a miss for a reason unrelated to validation."""
    assert m.MALFORMED_BODY and m.MALFORMED_BODY != {}


# ----------------------------------------------------------------------
# the grid
# ----------------------------------------------------------------------
def test_every_operation_gets_a_happy_cell(ops):
    grid = m.cells(ops)
    covered = {c.op.op_id for c in grid if c.target == 2}
    assert covered == {o.op_id for o in ops}


def test_the_grid_is_unique_on_operation_and_target(ops):
    grid = m.cells(ops)
    keys = [c.key for c in grid]
    assert len(keys) == len(set(keys))


def test_the_token_endpoint_gets_no_403_cell(ops):
    """It is the endpoint that issues authorization; there is no identity that
    can be refused by it in the way a catalog call is."""
    grid = [c for c in m.cells(ops) if c.op.op_id == "getToken"]
    assert 403 not in {c.target for c in grid}
    assert 401 in {c.target for c in grid}


def test_only_operations_with_a_path_parameter_get_a_404_cell(ops):
    for c in m.cells(ops):
        if c.target == 404:
            assert c.op.params, f"{c.op.op_id} has no path parameter to break"


def test_409_cells_follow_the_spec_rather_than_a_typed_list(ops):
    with_409 = {c.op.op_id for c in m.cells(ops) if c.target == 409}
    assert with_409 == {o.op_id for o in ops if "409" in o.declared}


def test_every_cell_names_a_driver_and_a_phase(ops):
    for c in m.cells(ops):
        assert c.driver and c.phase, c.label


def test_the_grid_is_the_size_the_plan_committed_to(ops):
    """~293 cells. A characterization test: it is expected to move when the
    spec is re-vendored or a rule changes, and the diff is the thing to read."""
    grid = m.cells(ops)
    by_target = {}
    for c in grid:
        by_target[c.target] = by_target.get(c.target, 0) + 1
    assert by_target[2] == 63
    assert by_target[401] == 63
    assert by_target[403] == 62
    assert by_target[404] == 55
    assert by_target[409] == 15
    assert 285 <= len(grid) <= 305, by_target


# ----------------------------------------------------------------------
# adjudication -- the rule that keeps the number a measurement
# ----------------------------------------------------------------------
def _cell(ops, op_id, target):
    op = {o.op_id: o for o in ops}[op_id]
    return m.Cell(op, target, "test", "B")


def test_a_cell_that_hits_its_target_is_covered(ops):
    assert m.adjudicate(_cell(ops, "loadTable", 404), 404)["verdict"] == m.COVERED


def test_a_cell_that_misses_is_NOT_relabelled_as_coverage_of_what_it_hit(ops):
    """The rule the whole figure rests on. A 404 cell that returns 403 leaves
    the 404 uncovered; the 403 cell is driven separately by an identity that
    makes the 403 mean something."""
    got = m.adjudicate(_cell(ops, "loadTable", 404), 403)
    assert got["verdict"] == m.MISSED and got["actual"] == 403
    assert "expected 404" in got["why"]


def test_the_happy_cell_is_adjudicated_against_the_declared_2xx(ops):
    """createCatalog answers 201 and dropNamespace 204; a matrix expecting 200
    would call both a miss."""
    assert m.adjudicate(_cell(ops, "createCatalog", 2), 201)["verdict"] == m.COVERED
    assert m.adjudicate(_cell(ops, "dropNamespace", 2), 204)["verdict"] == m.COVERED
    assert m.adjudicate(_cell(ops, "createCatalog", 2), 200)["verdict"] == m.MISSED


def test_a_transport_failure_is_an_error_not_a_miss(ops):
    """A connection reset says nothing about the endpoint's status coverage."""
    got = m.adjudicate(_cell(ops, "loadTable", 404), None, error=OSError("reset"))
    assert got["verdict"] == m.ERROR and "reset" in got["why"]


def test_coverage_by_operation_separates_not_driven_from_missed(ops):
    """An undriven cell is not a failure and must never be counted as one."""
    op = {o.op_id: o for o in ops}["loadTable"]
    results = {
        ("loadTable", 2): {"verdict": m.COVERED, "actual": 200, "why": ""},
        ("loadTable", 404): {"verdict": m.MISSED, "actual": 403, "why": "x"},
    }
    row = m.coverage_by_operation([op], results)[0]
    assert row["covered"] == [2] and row["missed"] == [404]
    assert 401 in row["not_driven"] and 403 in row["not_driven"]


# ----------------------------------------------------------------------
# the not-reachable ledger
# ----------------------------------------------------------------------
def test_every_ledger_entry_carries_a_reason_and_a_state():
    for row in m.ledger():
        assert row["why"], row["status"]
        assert row["state"] in ("settled", "probe")


def test_the_codes_that_must_still_be_probed_are_marked_as_such():
    """ "Unreachable" written from a spec is an assumption. 304, 406 and 419 get
    one call each and the result is recorded either way."""
    probes = {r["status"] for r in m.ledger() if r["state"] == "probe"}
    assert probes == {304, 406, 419}


def test_405_and_500_are_extras_the_spec_never_declares():
    """Both appear in polaris-logs-* -- measured 2026-09-10, 405 x7, 500 x21."""
    assert m.UNDECLARED_EXTRAS == (405, 500)


# ----------------------------------------------------------------------
# the executor -- every transform in the status axis, without a network
# ----------------------------------------------------------------------
TOKENS = {m.ADMIN: "root-token", m.RUNNER: "run-token", m.DENIED: "denied-token"}
REALM = "POLARIS"


def _req(ops, op_id, target, binding, driver="test", phase="B"):
    op = {o.op_id: o for o in ops}[op_id]
    cell = m.Cell(op, target, driver, phase)
    return cell, m.request_for(cell, binding, TOKENS, "nb-1-001-x", REALM)


def test_a_management_cell_goes_out_as_admin(ops, binding):
    """Management endpoints refuse the run principal. A happy management cell
    driven as the runner is a 403 recorded as a missed 2xx -- a harness gap
    wearing a finding's clothes, which is exactly what run 1 produced."""
    _, req = _req(ops, "listPrincipals", 2, binding)
    assert req["identity"] == m.ADMIN
    assert req["headers"]["Authorization"] == "Bearer root-token"


def test_a_catalog_cell_goes_out_as_the_run_principal(ops, binding):
    _, req = _req(ops, "loadTable", 2, binding)
    assert req["identity"] == m.RUNNER


def test_the_401_cell_carries_a_bad_token_not_a_missing_header(ops, binding):
    """An absent Authorization header and a bad one are different code paths,
    and only the second is what a client with a stale token looks like."""
    _, req = _req(ops, "loadTable", 401, binding)
    assert req["headers"]["Authorization"] == f"Bearer {m.GARBAGE_TOKEN}"
    assert req["identity"] == m.NOBODY


def test_the_403_cell_goes_out_as_the_denied_principal(ops, binding):
    _, req = _req(ops, "loadTable", 403, binding)
    assert req["headers"]["Authorization"] == "Bearer denied-token"


def test_the_404_cell_breaks_the_path_and_nothing_else(ops, binding):
    cell, req = _req(ops, "loadTable", 404, binding)
    happy = m.request_for(m.Cell(cell.op, 2, "t", "B"), binding, TOKENS, "r", REALM)
    assert m.MISSING in req["path"] and m.MISSING not in happy["path"]
    assert req["headers"]["Authorization"] == happy["headers"]["Authorization"]


def test_the_400_cell_sends_a_body_that_is_incomplete_not_absent(ops, binding):
    _, req = _req(ops, "createNamespace", 400, binding)
    assert req["json"] == m.MALFORMED_BODY
    assert req["headers"]["Content-Type"] == "application/json"


def test_the_409_cell_on_a_management_put_sends_a_stale_entity_version(ops, binding):
    _, req = _req(ops, "updateCatalog", 409, binding)
    assert req["json"]["currentEntityVersion"] == m.STALE_ENTITY_VERSION


def test_the_409_cell_on_a_create_is_the_same_request_issued_again(ops, binding):
    """The conflict comes from ORDER, not from the body: phase D re-creates
    what phase B created. If the body differed, the cell would be testing
    validation instead."""
    cell, req = _req(ops, "createNamespace", 409, binding)
    happy = m.request_for(m.Cell(cell.op, 2, "t", "B"), binding, TOKENS, "r", REALM)
    assert req["json"] == happy["json"] and req["path"] == happy["path"]


def test_getConfig_carries_a_warehouse_except_on_its_400_cell(ops, binding):
    """Without a warehouse this build answers 400, so the bare call tests rule
    3 and not the counted-2xx path -- run 1 recorded three 400s under a label
    promising a successful GET."""
    _, happy = _req(ops, "getConfig", 2, binding)
    _, bad = _req(ops, "getConfig", 400, binding)
    assert happy["params"] == {"warehouse": "cat"}
    assert bad["params"] is None


def test_the_token_endpoint_is_sent_as_a_form_with_no_bearer(ops, binding):
    _, req = _req(ops, "getToken", 2, binding)
    assert req["data"]["grant_type"] == "client_credentials" and req["json"] is None
    assert "Authorization" not in req["headers"]
    assert req["headers"]["Content-Type"] == "application/x-www-form-urlencoded"


def test_the_token_endpoints_401_is_a_wrong_secret_not_a_bad_bearer(ops, binding):
    """A real client id with the wrong secret. That is the case that makes
    "who failed to authenticate" answerable while "who authenticated" is not."""
    _, req = _req(ops, "getToken", 401, binding)
    assert req["data"]["client_id"] == "id"
    assert req["data"]["client_secret"] == "not-the-secret"


def test_every_request_carries_the_realm_and_the_request_id(ops, binding):
    """An untagged call cannot be found afterwards, and the matrix then reports
    EXPECTED STORED, ABSENT for a record that was almost certainly there."""
    for cell in m.cells(ops):
        req = m.request_for(cell, binding, TOKENS, "nb-1-001-x", REALM)
        assert req["headers"]["Polaris-Realm"] == REALM
        assert req["headers"]["Polaris-Request-Id"] == "nb-1-001-x"


def test_every_cell_in_the_whole_grid_builds_a_request(ops, binding):
    """286 requests, none of them raising. This is the test that would have
    caught a missing payload or an unbindable path before a run, not during."""
    built = [m.request_for(c, binding, TOKENS, "r", REALM) for c in m.cells(ops)]
    assert len(built) == len(m.cells(ops))
    assert all(r["path"].startswith("/api/") for r in built)


def test_the_request_id_format_matches_the_v1_harness_exactly(ops):
    """The v1 pull filters on `"mdc.requestId":"nb-<run>-"*`. A second format
    would simply go unfound, and read as a correlation failure."""
    assert m.request_id("1789", 7, "loadTable@404") == "nb-1789-007-loadTable-404"
    assert m.request_id("1789", 7, "a.b[c]") == "nb-1789-007-a-b-c"


# ----------------------------------------------------------------------
# the harness must not eat itself
# ----------------------------------------------------------------------
FIXTURE_VALUES = {"cat", "ns", "tbl", "vw", "prin", "prole", "crole"}

DESTRUCTIVE = {
    "deleteCatalog",
    "deleteCatalogRole",
    "deletePrincipal",
    "deletePrincipalRole",
    "revokePrincipalRole",
    "revokeCatalogRoleFromPrincipalRole",
    "dropNamespace",
    "dropTable",
    "dropView",
}


def test_no_destructive_operation_is_pointed_at_the_fixture(ops, binding):
    """FOUND 2026-09-10 WHILE WIRING THE NOTEBOOK, and it would have wasted a
    whole run: bound naively, `deleteCatalog` takes `{catalogName}` from the
    fixture and deletes the run's catalog at call ~30 of 63. `dropTable`,
    `dropView` and `dropNamespace` finish the job, `deletePrincipal` removes
    the run principal, and every later cell 404s -- a matrix reporting a
    pipeline with no coverage, when what happened is the harness ate itself.
    """
    by_id = {o.op_id: o for o in ops}
    for op_id in DESTRUCTIVE:
        op = by_id.get(op_id)
        if op is None:
            continue
        # Only the LAST segment is the thing being deleted. The catalog and the
        # namespace appear earlier as containers, and a table dropped inside the
        # fixture namespace does not harm the namespace.
        target = m.bind_path(op, binding).rstrip("/").split("/")[-1]
        assert (
            target not in FIXTURE_VALUES
        ), f"{op_id} would destroy the fixture entity `{target}`"


def test_delete_catalog_is_pointed_at_the_doomed_catalog(ops, binding):
    op = {o.op_id: o for o in ops}["deleteCatalog"]
    assert m.bind_path(op, binding).endswith("/cat_doomed")


def test_credential_rotation_never_touches_an_identity_the_run_authenticates_as(
    ops, binding
):
    """resetCredentials / rotateCredentials on the run principal replace the
    secret its token was minted from. Every later call then carries a token for
    a credential that no longer exists, and the rest of the run reports 401 --
    which the matrix would record as this build refusing every endpoint."""
    for op_id in ("resetCredentials", "rotateCredentials"):
        op = {o.op_id: o for o in ops}[op_id]
        path = m.bind_path(op, binding)
        assert "prin2" in path and "/prin/" not in path, f"{op_id} -> {path}"


def test_a_rename_moves_the_disposable_table_not_the_fixture(ops, binding):
    """A rename is a destructive operation wearing a POST."""
    body = m.payload_for({o.op_id: o for o in ops}["renameTable"], binding)
    assert body["source"]["name"] == "tbl2"
    assert body["destination"]["name"] == "tbl_r"


def test_the_409_family_still_has_something_to_conflict_with(ops, binding):
    """The deletes target `doomed_*` and the creates target `new_*` precisely so
    phase D can re-create a `new_*` entity that phase B has NOT deleted."""
    for op_id in ("updateCatalog", "updateCatalogRole", "updatePrincipal"):
        op = {o.op_id: o for o in ops}[op_id]
        assert "doomed" not in m.bind_path(op, binding), op_id


def test_the_catalog_payload_matches_the_shape_that_works_on_this_build(ops, binding):
    """PolarisREST.create_catalog is the reference: s3a:// rather than s3://,
    allowedLocations at the BUCKET root rather than at the catalog prefix, and
    drop-with-purge on so the cleanup cell can remove what this creates.
    Guessing the shape is how a create cell returns 400 and gets read as a
    validation finding about Polaris."""
    body = m.payload_for({o.op_id: o for o in ops}["createCatalog"], binding)["catalog"]
    assert body["properties"]["default-base-location"].startswith("s3a://")
    assert body["storageConfigInfo"]["allowedLocations"] == ["s3a://bucket/"]
    assert body["properties"]["polaris.config.drop-with-purge.enabled"] == "true"
