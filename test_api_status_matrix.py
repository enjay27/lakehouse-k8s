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
        "rename_table": "tbl_rn",
        "rename_view": "vw_rn",
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
    """65, split 33 management / 32 catalog. If this changes, `fetch_specs.sh`
    vendored a new version -- read the diff before touching the number.

    The documents moved on 2026-09-21: `fetch_specs.sh` was run at
    `apache-polaris-1.6.0` (catalog document = Iceberg 1.11.0), which added
    `registerView` and `signRequest` and nothing else. The diff was read, the
    cluster is on 1.6.0, and `log-coverage/spec/inventory.json` records both
    fingerprints -- the superseded 1.3.0 one is in its `history`.
    """
    assert len(ops) == 65
    assert sum(1 for o in ops if o.api == "management") == 33
    assert sum(1 for o in ops if o.api == "catalog") == 32
    assert {"registerView", "signRequest"} <= {o.op_id for o in ops}


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
    """297 cells. A characterization test: it is expected to move when the
    spec is re-vendored or a rule changes, and the diff is the thing to read.
    It was 286 until the 1.6.0 documents were vendored on 2026-09-21; the +11
    is `registerView` (6 cells) and `signRequest` (5)."""
    grid = m.cells(ops)
    by_target = {}
    for c in grid:
        by_target[c.target] = by_target.get(c.target, 0) + 1
    assert by_target[2] == 65
    assert by_target[400] == 30
    assert by_target[401] == 65
    assert by_target[403] == 64
    assert by_target[404] == 57
    assert by_target[409] == 16
    assert len(grid) == 297, by_target
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
    assert body["source"]["name"] == "tbl_rn"
    assert body["destination"]["name"] == "tbl_r"
    assert body["source"]["name"] != binding["table"], "never the fixture"


def test_a_rename_does_not_consume_what_the_409_cells_conflict_with(ops, binding):
    """Phase B's renameTable / renameView used to move `new_table` and
    `new_view` away, so phase D's createTable and createView 409 cells had
    nothing left to collide with. Run 1789950539 recorded that as
    `createTable missed [409] got {409: 403}` and `createView missed [409] got
    {409: 200}` -- two cells that could not pass, printed as Polaris.
    """
    by_id = {o.op_id: o for o in ops}
    for rename_op, create_op, new_key in (
        ("renameTable", "createTable", "new_table"),
        ("renameView", "createView", "new_view"),
    ):
        moved = m.payload_for(by_id[rename_op], binding)["source"]["name"]
        conflicts_with = m.payload_for(by_id[create_op], binding)["name"]
        assert conflicts_with == binding[new_key]
        assert moved != conflicts_with, f"{rename_op} consumes {create_op}'s 409 target"


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


# ----------------------------------------------------------------------
# what the documents say about the 400 cells
#
# Ported from `test_spec_check.py` when Prism was removed (2026-09-10). These
# six never needed Prism -- they read the vendored documents and nothing else --
# and they are the ONLY coverage of the malform hybrid, so deleting that file
# without moving them first would have left the hybrid untested.
# ----------------------------------------------------------------------
def _docs():
    import yaml

    return {
        f.name: yaml.safe_load(f.read_text())
        for f in list(SPEC_DIR.glob("*.yml")) + list(SPEC_DIR.glob("*.yaml"))
    }


def _json_type(value):
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    return "object"


#: A body-carrying operation whose schema declares no `required` and no
#: property whose type can be violated. Nothing the grid can build will be
#: rejected by it, which is exactly what `unmalformable_cells` exists to name.
_UNBREAKABLE_SPEC = """
openapi: 3.0.3
info: {title: Unbreakable, version: 0.0.1}
servers: [{url: "http://localhost/api/management/v1"}]
paths:
  /widgets:
    post:
      operationId: createWidget
      requestBody:
        content:
          application/json:
            schema: {$ref: '#/components/schemas/WidgetRequest'}
      responses: {'201': {description: ok}, '400': {description: bad}}
components:
  schemas:
    WidgetRequest:
      description: no required, and no property with a violable type
      properties:
        anything: {}
"""


def test_every_400_cell_now_has_a_way_to_break_its_body():
    """The eleven that could not are fixed, not suppressed.

    On its own this assertion is worthless: a function that always returns
    `[]` passes it, which a mutant proved. The test below is what gives it
    meaning -- it feeds the finder a document it MUST report on."""
    assert m.unmalformable_cells(SPEC_DIR) == []


def test_the_finder_reports_a_cell_that_really_cannot_be_broken(tmp_path):
    """The empty result above must be empty because the documents are clean,
    not because the finder cannot find. Without this, `return []` passes."""
    (tmp_path / "unbreakable-management.yml").write_text(_UNBREAKABLE_SPEC)
    rows = m.unmalformable_cells(tmp_path)
    assert [r["op_id"] for r in rows] == ["createWidget"]

    counts = m.malform_strategies(tmp_path)
    assert counts["none"] == 1 and counts["omit"] == 0 and counts["wrong_type"] == 0


def test_the_finder_does_not_flag_an_operation_it_can_break(tmp_path):
    """The other half: give the same document a violable property and the
    finding disappears. A finder that reported everything would also pass the
    test above."""
    (tmp_path / "breakable-management.yml").write_text(
        _UNBREAKABLE_SPEC.replace("anything: {}", "anything: {type: integer}")
    )
    assert m.unmalformable_cells(tmp_path) == []
    assert m.malform_strategies(tmp_path)["wrong_type"] == 1


def test_the_hybrid_splits_exactly_eighteen_and_eleven():
    """18 keep omission, 11 switch to a wrong-typed value, none is left with
    no way to break. A count that drifts means a document changed, and the
    right response is to read the diff rather than to adjust the number.

    It was 16/11/0 against the 1.3.0 documents. `registerView` and
    `signRequest` both declare `required` properties, so both take omission,
    and the eleven wrong-type cells are untouched -- which is what keeps every
    previous run's 400 column comparable with this one.
    """
    counts = m.malform_strategies(SPEC_DIR)
    assert counts == {"omit": 18, "wrong_type": 11, "none": 0}
    assert sum(counts.values()) == len(
        [c for c in m.cells(m.load_spec(SPEC_DIR)) if c.target == 400 and c.op.has_body]
    )


def test_the_omission_cells_send_a_byte_identical_body_to_before_the_hybrid(binding):
    """**This is the comparability guarantee, and it is the whole reason the
    hybrid was chosen over one rule for all 27.** Sixteen 400 cells must send
    exactly the body they have always sent, or every past run's 400 column
    stops being comparable with every future one."""
    checked = 0
    for cell in m.cells(m.load_spec(SPEC_DIR)):
        if cell.target != 400 or not cell.op.has_body:
            continue
        if cell.op.malform != m.MALFORM_OMIT:
            continue
        req = m.request_for(cell, binding, TOKENS, "nb-1-001-x", REALM)
        body = req["json"] if req["json"] is not None else req["data"]
        assert body == m.MALFORMED_BODY, cell.op.op_id
        checked += 1
    assert checked == 18


def test_the_wrong_type_cells_send_something_their_schema_must_reject(binding):
    """A value of a type the property does not declare. Not a guess: the
    declared type is read from the document and the value is of another one."""
    docs = _docs()
    checked = 0
    for cell in m.cells(m.load_spec(SPEC_DIR)):
        if cell.target != 400 or not isinstance(cell.op.malform, dict):
            continue
        req = m.request_for(cell, binding, TOKENS, "nb-1-001-x", REALM)
        body = req["json"] if req["json"] is not None else req["data"]
        name = cell.op.malform["property"]
        assert set(body) == {name}, cell.op.op_id
        doc = docs[cell.op.source]
        comps = (doc.get("components") or {}).get("schemas") or {}
        prop = m.request_schema(doc, cell.op.op_id) or {}
        declared = m._typed_properties(prop, comps).get(name)
        assert declared == cell.op.malform["type"], cell.op.op_id
        assert _json_type(body[name]) != declared, cell.op.op_id
        checked += 1
    assert checked == 11


# ----------------------------------------------------------------------
# the combinator walk
#
# RECOVERED FROM `7cb12c2` on 2026-09-10. These tests existed when
# `has_required_fields` was fixed; the working copy that moved the walker into
# this module replaced them with the hybrid tests above and left the walker
# with NO coverage -- and because the file's test COUNT was 58 on both sides,
# the suite stayed green and the deletion was committed unnoticed. The repo's
# own rule, written after `_epoch_of`, is *diff the NAMES, not the line count*;
# it had been applied to source and not to tests.
# ----------------------------------------------------------------------
def test_get_token_is_malformable_through_its_anyOf_and_was_once_counted_wrong():
    """THE BUG THESE TESTS ONCE ENSHRINED. `getToken` `$ref`s
    `OAuthTokenRequest`, which carries no `required` of its own -- only an
    `anyOf` over two branches that each require three fields. A resolver that
    stopped at the first `$ref` read "no required", called the operation
    unmalformable, and **the count 12 was published in a commit message, two
    memory files, and an assertion in a test. The real count is 11.**

    Prism never contradicted it: `getToken` came back 401 on a security
    scheme, so the one run that could have caught it was looking elsewhere.
    """
    doc = _docs()["rest-catalog-open-api.yaml"]
    comps = (doc.get("components") or {}).get("schemas") or {}
    sch = m.request_schema(doc, "getToken")
    assert not sch.get("required"), "no top-level required -- that is the trap"
    assert sch.get("anyOf"), "and the constraints live in an anyOf"
    assert m.has_required_fields(sch, comps) is True


def test_anyOf_is_malformable_only_when_EVERY_branch_is():
    """The body need satisfy only ONE branch, so a single unconstrained branch
    accepts `{"matrix": ...}` and the whole schema accepts it with it."""
    comps = {
        "Strict": {"required": ["a"], "properties": {"a": {"type": "string"}}},
        "Loose": {"properties": {"b": {"type": "string"}}},
    }
    assert (
        m.has_required_fields(
            {"anyOf": [{"$ref": "#/c/Strict"}, {"$ref": "#/c/Strict"}]}, comps
        )
        is True
    )
    assert (
        m.has_required_fields(
            {"anyOf": [{"$ref": "#/c/Strict"}, {"$ref": "#/c/Loose"}]}, comps
        )
        is False
    )


def test_allOf_is_malformable_when_ANY_branch_is():
    """The body must satisfy EVERY branch, so one constrained branch suffices.
    The opposite rule to anyOf, and getting them the same way round would flip
    roughly half the answers."""
    comps = {"Strict": {"required": ["a"]}, "Loose": {"properties": {"b": {}}}}
    assert (
        m.has_required_fields(
            {"allOf": [{"$ref": "#/c/Loose"}, {"$ref": "#/c/Strict"}]}, comps
        )
        is True
    )
    assert (
        m.has_required_fields(
            {"allOf": [{"$ref": "#/c/Loose"}, {"$ref": "#/c/Loose"}]}, comps
        )
        is False
    )


def test_a_cyclic_document_does_not_hang_the_walker():
    """A document that refs itself is the document's problem; hanging on it
    would be ours."""
    assert (
        m.has_required_fields({"$ref": "#/c/Loop"}, {"Loop": {"$ref": "#/c/Loop"}})
        is False
    )


def test_the_combinator_blind_spot_was_never_going_to_stay_one_wrong_answer():
    """Schemas across BOTH documents hide their constraints in a combinator."""
    total = 0
    for doc in _docs().values():
        comps = (doc.get("components") or {}).get("schemas") or {}
        total += sum(
            1
            for v in comps.values()
            if isinstance(v, dict)
            and not v.get("required")
            and any(k in v for k in ("anyOf", "oneOf", "allOf"))
        )
    assert total > 20, f"only {total} -- the walker or the documents changed"


def test_a_malformable_op_resolves_its_required_fields_through_the_ref():
    """One `$ref` hop is all these documents use -- and a helper that failed to
    follow it would call every operation unmalformable and the finding would
    quietly become "all 27"."""
    import yaml

    doc = yaml.safe_load((SPEC_DIR / "polaris-management-service.yml").read_text())
    sch = m.request_schema(doc, "createCatalog")
    assert sch and sch.get("required") == ["catalog"]


def test_typed_properties_reads_through_a_combinator_branch():
    """**The wrong-type half needs the same walk the required-field half needed,
    and nothing was testing it.** A mutant that dropped the combinator loop from
    `_typed_properties` passed the entire suite, because no operation in today's
    two documents happens to need it -- so the blind spot that produced the 12
    was still open on the other side of the same function."""
    comps = {
        "Base": {"properties": {"count": {"type": "integer"}}},
        "More": {"properties": {"flag": {"type": "boolean"}}},
    }
    got = m._typed_properties(
        {"allOf": [{"$ref": "#/c/Base"}, {"$ref": "#/c/More"}]}, comps
    )
    assert got == {"count": "integer", "flag": "boolean"}
    assert m.malform_strategy({"allOf": [{"$ref": "#/c/Base"}]}, comps) == {
        "property": "count",
        "value": "not-an-integer",
        "type": "integer",
    }


# ----------------------------------------------------------------------
# the denominator is recorded, not assumed
# ----------------------------------------------------------------------
#
# These exist because of run 1789950539: the grid was 63 operations / 286
# cells, `log-coverage/spec/` was re-fetched at a different tag 19 minutes
# later, and nothing on disk recorded either number. The run's coverage
# figure survived only as printed output inside a committed notebook.


def _twin(
    tmp_path,
    a="paths:\n  /x:\n    get:\n      operationId: getX\n      responses:\n        200:\n          description: ok\n",
):
    """A minimal two-document spec directory, the shape `load_spec` expects."""
    (tmp_path / "polaris-management-service.yml").write_text(a, encoding="utf-8")
    (tmp_path / "rest-catalog-open-api.yaml").write_text(a, encoding="utf-8")
    return tmp_path


def test_the_fingerprint_carries_bytes_and_counts_together():
    """A sha says the file moved; the counts say what the move did to the grid.
    Either alone leaves a reader guessing."""
    fp = m.spec_fingerprint(SPEC_DIR)
    assert fp["operations"] == len(m.load_spec(SPEC_DIR))
    assert fp["cells"] == len(m.cells(m.load_spec(SPEC_DIR)))
    assert sorted(f["name"] for f in fp["files"]) == [
        "polaris-management-service.yml",
        "rest-catalog-open-api.yaml",
    ]
    for f in fp["files"]:
        assert len(f["sha256"]) == 64
        assert f["bytes"] > 0
    assert sum(fp["by_target"].values()) == fp["cells"]


def test_the_vendored_spec_matches_its_own_inventory():
    """The tracked record and the documents on disk agree. When this fails,
    someone re-fetched without re-recording -- which is the whole failure this
    module was added to catch."""
    assert m.inventory_drift(SPEC_DIR) == []


def test_a_directory_with_no_inventory_reports_that_as_the_drift(tmp_path):
    """Absent is a finding, not a pass. An unrecorded denominator is exactly
    the state run 1789950539 was measured in."""
    d = _twin(tmp_path)
    drift = m.inventory_drift(d)
    assert len(drift) == 1 and "no inventory.json" in drift[0]
    with pytest.raises(m.SpecUnavailable, match="THE DENOMINATOR MOVED"):
        m.assert_denominator(d)


def test_a_changed_document_is_named_with_both_shas(tmp_path):
    d = _twin(tmp_path)
    m.write_inventory(d, tag="t1")
    assert m.inventory_drift(d) == []
    (d / "rest-catalog-open-api.yaml").write_text(
        "paths:\n  /x:\n    get:\n      operationId: getX\n      responses:\n"
        "        200:\n          description: ok\n"
        "  /z:\n    get:\n      operationId: getZ\n      responses:\n"
        "        200:\n          description: ok\n",
        encoding="utf-8",
    )
    drift = m.inventory_drift(d)
    assert any("rest-catalog-open-api.yaml" in line for line in drift), drift
    assert any(line.startswith("operations:") for line in drift), drift
    assert any(line.startswith("cells:") for line in drift), drift
    assert any(
        "operations added since the record: ['getZ']" in line for line in drift
    ), drift


def test_a_re_record_keeps_the_fingerprint_it_superseded(tmp_path):
    """The previous denominator must survive the overwrite. Losing it is what
    made run 1789950539 unreproducible."""
    d = _twin(tmp_path)
    first = m.write_inventory(d, tag="apache-polaris-1.3.0-incubating")
    (d / "rest-catalog-open-api.yaml").write_text(
        "paths:\n  /y:\n    get:\n      operationId: getY\n      responses:\n"
        "        200:\n          description: ok\n",
        encoding="utf-8",
    )
    second = m.write_inventory(d, tag="apache-polaris-1.6.0")
    assert second["tag"] == "apache-polaris-1.6.0"
    assert len(second["history"]) == 1
    assert second["history"][0]["tag"] == "apache-polaris-1.3.0-incubating"
    assert second["history"][0]["files"] == first["files"]
    assert "history" not in second["history"][0]


def test_re_recording_an_unchanged_spec_does_not_grow_the_history(tmp_path):
    d = _twin(tmp_path)
    m.write_inventory(d, tag="t1")
    again = m.write_inventory(d, tag="t1")
    assert again["history"] == []


def test_the_inventory_names_the_operations_that_appeared(tmp_path):
    """`registerView` and `signRequest` are the entire 63->65 difference, and a
    reader must be able to see that without re-fetching anything."""
    rec = m.read_inventory(SPEC_DIR)
    assert rec["history"], "the 1.3.0 fingerprint must still be on record"
    was = set(rec["history"][0]["operation_ids"])
    now = set(rec["operation_ids"])
    assert now - was == {"registerView", "signRequest"}
    assert was - now == set()
    assert rec["history"][0]["cells"] == 286 and rec["cells"] == 297
