"""Tests for `src/api_status_matrix.py` -- the operation x status grid.

The grid is derived from the vendored specs, so these tests read the real
`log-coverage/spec/` documents rather than a fixture. That is deliberate: the
denominator of the whole run is those two files, and a test against a hand-made
copy would keep passing after `fetch_specs.sh` vendored a new version.

Nothing here touches the network.
"""

import pathlib

import pytest

import api_status_matrix as m

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
        "entity_version": 1,
        "run": "1789000000",
        "base_location": "s3://bucket/cat2",
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
