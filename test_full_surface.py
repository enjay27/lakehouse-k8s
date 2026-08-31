"""Tests for the FULL GET/HEAD surface and the two identity profiles.

Written after the privilege scan was found to cover 13 of 29 operations with
nothing in the harness saying so. The gap was not a bug anyone introduced — the
op list was its own authority, so there was no place for a disagreement to
show up. These tests are that place.

A new FILE rather than additions to `test_api_sweep.py` / `test_privilege_scan.py`
on purpose: the catalog-scoped path is the denominator of an already-correlated
capture, so the strongest thing these tests can assert is that it did not move.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
import api_sweep as sweep  # noqa: E402
import privilege_scan as ps  # noqa: E402
import query_profile as qp  # noqa: E402

FULL_FIXTURE = {
    "catalog": "authz1_catalog",
    "namespace": "ns1",
    "principal": "authz1_principal",
    "principal_role": "authz1_principal_role",
    "catalog_role": "owner_principal",
    "table": "t1",
    "view": "v1",
    "generic_table": "gt1",
    "policy": "p1",
}
THIN_FIXTURE = {k: FULL_FIXTURE[k] for k in list(FULL_FIXTURE)[:5]}


class Resp:
    def __init__(self, status=200):
        self.status_code = status
        self.text = "" if status < 300 else "error"


class Client:
    """Answers every method. `rule` maps a method name to a status code."""

    def __init__(self, rule=None):
        self.rule = rule or (lambda name: 200)
        self.called = []

    def __getattr__(self, name):
        def go(*a, **kw):
            self.called.append(name)
            return Resp(self.rule(name))

        return go


def verdicts(statuses):
    out = {}
    for s in statuses:
        out[s.verdict] = out.get(s.verdict, 0) + 1
    return out


# ----------------------------------------------------------------------
# the surface itself
# ----------------------------------------------------------------------
def test_full_surface_is_29_operations():
    ops = sweep.full_read_operations(FULL_FIXTURE)
    assert len(ops) == 29
    by_surface = {}
    for _label, surface, _fn in ops:
        by_surface[surface] = by_surface.get(surface, 0) + 1
    assert by_surface == {"mgmt": 13, "iceberg": 11, "polaris": 5}


def test_labels_are_unique():
    labels = [l for l, _s, _f in sweep.full_read_operations(FULL_FIXTURE)]
    assert len(set(labels)) == len(labels)


def test_read_operations_is_frozen_at_13():
    """The catalog-scoped denominator must not move.

    `privscan-20260824-123408` is already correlated against these 13 labels.
    Adding an operation here would not enrich that report — it would make its
    per-API table describe a surface the drive never issued.
    """
    assert len(sweep.read_operations(FULL_FIXTURE)) == 13


def test_full_surface_is_a_strict_superset_by_label():
    """Shared labels are what let the two suites' reports diff directly."""
    thirteen = {l for l, _s, _f in sweep.read_operations(FULL_FIXTURE)}
    twentynine = {l for l, _s, _f in sweep.full_read_operations(FULL_FIXTURE)}
    assert thirteen < twentynine
    assert len(twentynine - thirteen) == 16


def test_the_four_missing_management_reads_are_the_role_graph():
    """Named explicitly, because they are the ones that mattered most.

    principal -> principal-role -> catalog-role IS the authorization model, so
    these are the reads most likely to touch `grant_records` more than once.
    """
    thirteen = {l for l, _s, _f in sweep.read_operations(FULL_FIXTURE)}
    mgmt = {l for l, s, _f in sweep.full_read_operations(FULL_FIXTURE) if s == "mgmt"}
    assert mgmt - thirteen == {
        "GET  /principals/{p}/principal-roles",
        "GET  /principal-roles/{n}/catalog-roles/{c}",
        "GET  /catalogs/{c}/catalog-roles/{r}",
        "GET  /catalog-roles/{r}/principal-roles",
    }


# ----------------------------------------------------------------------
# the third outcome: undriveable
# ----------------------------------------------------------------------
def test_missing_entities_make_ops_undriveable_not_failed():
    """A `--no-tables` fixture is a fixture gap, not a Polaris 404.

    This is the exact state of the 1,000-principal fixture
    (`create_tables: False` in the seed ledger), so it is not a hypothetical
    branch: seven operations have nothing to point at.
    """
    statuses = ps.probe_surface(
        Client(), None, sweep.full_read_operations(THIN_FIXTURE)
    )
    assert verdicts(statuses) == {"authorized": 22, "undriveable": 7}
    undriveable = [s for s in statuses if s.undriveable]
    assert all("fixture has no" in s.detail for s in undriveable)
    assert not any(
        s.unavailable for s in undriveable
    ), "an undriveable op must never also read as feature-unavailable"


def test_a_full_fixture_leaves_nothing_undriveable():
    statuses = ps.probe_surface(
        Client(), None, sweep.full_read_operations(FULL_FIXTURE)
    )
    assert verdicts(statuses) == {"authorized": 29}


def test_undriveable_ops_never_reach_the_client():
    """The refusal happens before the request, so no 404 is provoked."""
    c = Client()
    ps.probe_surface(c, None, sweep.full_read_operations(THIN_FIXTURE))
    assert "load_table" not in c.called
    assert "load_credentials" not in c.called
    assert "list_tables" in c.called, "the COLLECTION read is still driveable"


# ----------------------------------------------------------------------
# feature flags, refusals, and keeping the three apart
# ----------------------------------------------------------------------
def test_feature_flagged_extensions_are_unavailable_not_refused():
    """404/501 from generic-tables or policies is a fact about the deployment."""
    off = Client(lambda n: 404 if ("generic" in n or "polic" in n) else 200)
    statuses = ps.probe_surface(off, None, sweep.full_read_operations(FULL_FIXTURE))
    assert verdicts(statuses) == {"authorized": 24, "unavailable": 5}


def test_service_level_refusals_read_as_refused():
    denied = Client(
        lambda n: 403 if ("principal" in n or n == "list_catalogs") else 200
    )
    statuses = ps.probe_surface(denied, None, sweep.full_read_operations(FULL_FIXTURE))
    counts = verdicts(statuses)
    assert counts["refused"] == 9 and counts["authorized"] == 20


def test_probe_table_explains_undriveable_rather_than_implying_a_server_fault():
    statuses = ps.probe_surface(
        Client(), None, sweep.full_read_operations(THIN_FIXTURE)
    )
    table = ps.render_probe_table(statuses)
    assert "undriveable" in table
    assert "the FIXTURE has no such entity" in table


# ----------------------------------------------------------------------
# profiles
# ----------------------------------------------------------------------
def test_the_two_profiles_bind_different_prefixes_and_op_counts():
    assert len(ps.PROFILES["catalog-scoped"].ops(FULL_FIXTURE)) == 13
    assert len(ps.PROFILES["catalog-scoped-full"].ops(FULL_FIXTURE)) == 29
    assert ps.PROFILES["catalog-scoped"].prefix == "user"
    assert ps.PROFILES["catalog-scoped-full"].prefix == "authz"


def test_default_profile_reproduces_the_completed_pass():
    assert ps.DEFAULT_PROFILE == "catalog-scoped"
    p = ps.PROFILES[ps.DEFAULT_PROFILE]
    assert p.operations == "read_operations" and p.prefix == "user"


def test_catalog_scoped_full_declares_the_footprint_it_must_match():
    """The plan's central constraint, encoded rather than left to a docstring.

    Seq Scan cost is flat in rows-owned; index-scan cost tracks rows returned.
    So a service-scoped principal with a different grant footprint sits at a
    different point on the curve, and diffing the two suites would compare two
    volumes while appearing to compare two privilege levels.
    """
    assert ps.PROFILES["catalog-scoped-full"].footprint_must_match == "catalog-scoped"
    #: service-admin deliberately declares NO match: `service_admin` gains one
    #: grant per catalog, so there is nothing to match and claiming otherwise
    #: would invite exactly the diff this separation prevents.
    assert ps.PROFILES["service-admin"].footprint_must_match is None
    assert ps.PROFILES["service-admin"].prefix == "admin"


# ----------------------------------------------------------------------
# templates and coverage
# ----------------------------------------------------------------------
def test_every_one_of_the_29_gets_a_template():
    templates = qp.operation_templates(read_operations=sweep.full_read_operations)
    labels = {t.label for t in templates}
    for label, _s, _f in sweep.full_read_operations(qp._SENTINELS):
        assert label in labels, f"{label} has no URL template"


def test_head_and_get_on_one_path_do_not_collide():
    """Three pairs share a path and differ only by method."""
    templates = qp.operation_templates(read_operations=sweep.full_read_operations)
    path = "/api/catalog/v1/c1/namespaces/ns1"
    assert qp.classify("GET", path, templates)[0] == "GET  /namespaces/{ns}"
    assert qp.classify("HEAD", path, templates)[0] == "HEAD /namespaces/{ns}"


def test_polaris_extension_paths_carry_their_own_prefix():
    templates = qp.operation_templates(read_operations=sweep.full_read_operations)
    label, _s, ents = qp.classify(
        "GET",
        "/api/catalog/polaris/v1/c1/namespaces/ns1/generic-tables/gt1",
        templates,
    )
    assert label == "GET  /generic-tables/{gt}"
    assert ents["generic_table"] == "gt1"


def test_every_full_surface_label_round_trips():
    templates = qp.operation_templates(read_operations=sweep.full_read_operations)
    real = dict(FULL_FIXTURE)
    for t in templates:
        concrete = t.template
        for name, value in real.items():
            concrete = concrete.replace("{" + name + "}", str(value))
        assert qp.classify(t.method, concrete, templates)[0] == t.label


def test_canonical_path_ignores_parameter_names():
    """The server calls it {prefix}; the harness calls it {catalog}."""
    assert qp.canonical_path("/v1/{prefix}/namespaces/{namespace}") == (
        qp.canonical_path("/v1/{catalog}/namespaces/{ns}")
    )


def test_coverage_gap_reports_the_13_of_29_that_started_this():
    server = [
        ("GET", "/api/management/v1/catalogs"),
        ("GET", "/api/management/v1/principals/{principalName}/principal-roles"),
        ("GET", "/api/catalog/v1/config"),
        ("HEAD", "/api/catalog/v1/{prefix}/namespaces/{namespace}"),
    ]
    thirteen = qp.operation_templates()
    gap = qp.coverage_gap(thirteen, server)
    assert not gap["clean"]
    assert len(gap["missing"]) == 3
    assert "GET  /catalogs" in gap["covered"]


def test_coverage_gap_is_clean_for_the_full_surface():
    server = [
        ("GET", "/api/management/v1/catalogs"),
        ("GET", "/api/management/v1/principals/{principalName}/principal-roles"),
        ("GET", "/api/catalog/v1/config"),
        ("HEAD", "/api/catalog/v1/{prefix}/namespaces/{namespace}"),
        ("GET", "/api/catalog/polaris/v1/{prefix}/applicable-policies"),
    ]
    gap = qp.coverage_gap(
        qp.operation_templates(read_operations=sweep.full_read_operations), server
    )
    assert gap["clean"] and gap["missing"] == []


def test_the_token_post_is_not_reported_as_an_uncovered_path():
    """A permanent false positive in the one number whose value is being zero."""
    gap = qp.coverage_gap(
        qp.operation_templates(read_operations=sweep.full_read_operations),
        [("GET", "/api/catalog/v1/config")],
    )
    assert "POST /oauth/tokens" not in gap["extra"]
    #: The other 28 ARE legitimately extra against a one-item server list —
    #: the point is only that the control call is not among them.
    assert len(gap["extra"]) == 28
    assert not any("oauth" in e for e in gap["extra"])


def test_render_coverage_states_the_fraction_plainly():
    gap = qp.coverage_gap(
        qp.operation_templates(),
        [("GET", "/api/catalog/v1/config"), ("GET", "/api/management/v1/catalogs")],
    )
    out = qp.render_coverage(gap, total_server=2)
    assert "1 of 2" in out
    assert "NOT driven" in out


# ----------------------------------------------------------------------
# the captured inventory — evidence, and its limit
# ----------------------------------------------------------------------
MATRIX = """# API → SQL → MinIO Access Matrix

## Per-API detail

### `preflight`

- `GET /v1/catalogs` → **200**

### `mgmt.list_catalogs`

- `GET /v1/catalogs` → **200**
- wall 3 ms

### `mgmt.get_catalog`

- `GET /v1/catalogs/{cat}` → **200**

### `iceberg.load_table`

- `GET /v1/{cat}/namespaces/{ns}/tables/{tbl}` → **200**

### `iceberg.load_table[missing]`

- `GET /v1/{cat}/.../tables/{missing}` → **404**

### `iceberg.load_table[snapshots=refs]`

- `GET /v1/{cat}/namespaces/{ns}/tables/{tbl}?snapshots=refs` → **200**

### `iceberg.head_namespace`

- `HEAD /v1/{cat}/namespaces/{ns}` → **204**

### `mgmt.create_principal`

- `POST /v1/principals` → **201**
"""


def test_matrix_paths_get_the_right_service_base():
    """`/v1/catalogs` and `/v1/{cat}/namespaces` both start `/v1/`.

    Only the label prefix says which service answered. Without it the
    management and catalog surfaces collapse onto each other.
    """
    ops = qp.parse_api_matrix(MATRIX)
    paths = {api: path for _m, path, api, _s in ops}
    assert paths["mgmt.list_catalogs"] == "/api/management/v1/catalogs"
    assert paths["iceberg.head_namespace"] == ("/api/catalog/v1/{cat}/namespaces/{ns}")


def test_matrix_keeps_head_and_its_status():
    ops = qp.parse_api_matrix(MATRIX)
    head = [o for o in ops if o[0] == "HEAD"]
    assert len(head) == 1 and head[0][3] == 204


def test_matrix_folds_variants_into_the_base_operation():
    """`load_table[missing]` and `[snapshots=refs]` are one operation.

    Counting them separately would inflate the inventory and make the
    harness's coverage look worse than it is.
    """
    ops = qp.parse_api_matrix(MATRIX)
    assert not any("[" in api for _m, _p, api, _s in ops)
    loads = [o for o in ops if o[2] == "iceberg.load_table"]
    assert len(loads) == 1


def test_matrix_drops_abbreviated_paths_rather_than_guessing():
    """A `...` in a variant heading stands for text the report elided."""
    assert not any("..." in p for _m, p, _a, _s in qp.parse_api_matrix(MATRIX))


def test_matrix_excludes_writes_and_the_preflight_pseudo_api():
    ops = qp.parse_api_matrix(MATRIX)
    assert all(m in ("GET", "HEAD") for m, _p, _a, _s in ops)
    assert not any(a == "preflight" for _m, _p, a, _s in ops)


def test_matrix_query_string_is_not_part_of_the_operation():
    ops = qp.parse_api_matrix(MATRIX)
    assert not any("?" in p for _m, p, _a, _s in ops)


# ----------------------------------------------------------------------
# three-way coverage
# ----------------------------------------------------------------------
def test_an_observed_operation_the_suite_misses_is_a_CONFIRMED_gap():
    """The cluster answered it, so it exists. No asterisk needed."""
    observed = qp.parse_api_matrix(MATRIX)
    cov = qp.coverage_from_evidence(qp.operation_templates(), observed)
    assert not cov["clean"]
    assert any("tables/{tbl}" in o for o in cov["observed_not_driven"])
    assert "GET  /catalogs" in cov["driven_verified"]


def test_the_full_surface_closes_every_confirmed_gap():
    observed = qp.parse_api_matrix(MATRIX)
    cov = qp.coverage_from_evidence(
        qp.operation_templates(read_operations=sweep.full_read_operations), observed
    )
    assert cov["clean"] and cov["observed_not_driven"] == []


def test_spec_candidates_never_become_a_confirmed_gap():
    """A transcribed endpoint this build may not serve is a question, not a fault.

    Merging candidates into the gap count would let a feature-flagged endpoint
    read as a coverage failure — and let a genuinely missing one hide behind
    the same asterisk.
    """
    observed = qp.parse_api_matrix(MATRIX)
    candidates = [("GET", "/api/catalog/polaris/v1/{prefix}/applicable-policies")]
    cov = qp.coverage_from_evidence(
        qp.operation_templates(read_operations=sweep.read_operations),
        observed,
        candidates,
    )
    assert not any("applicable-policies" in o for o in cov["observed_not_driven"])
    assert any("applicable-policies" in c for c in cov["candidate_not_driven"])


def test_driven_but_never_called_is_unverified_not_verified():
    """The 10 new ops have no prior observation; saying otherwise would be a claim."""
    observed = qp.parse_api_matrix(MATRIX)
    cov = qp.coverage_from_evidence(
        qp.operation_templates(read_operations=sweep.full_read_operations), observed
    )
    assert "GET  /policies" in cov["driven_unverified"]
    assert "GET  /policies" not in cov["driven_verified"]


def test_render_states_that_a_call_log_cannot_prove_absence():
    observed = qp.parse_api_matrix(MATRIX)
    cov = qp.coverage_from_evidence(qp.operation_templates(), observed)
    out = qp.render_evidence_coverage(cov)
    assert "cannot prove one is absent" in out
    assert "floor on what is missing, never a ceiling" in out


# ----------------------------------------------------------------------
# entity targets — asked for, never constructed
# ----------------------------------------------------------------------
class EntityClient(Client):
    """Lists tables/views; `ext_status` controls the feature-flagged pair."""

    def __init__(self, ext_status=200, tables=("tbl1",), views=("vw1",)):
        super().__init__()
        self.ext_status = ext_status
        self._tables = tables
        self._views = views

    def _ids(self, ns, names):
        return _Body(
            200, {"identifiers": [{"namespace": [ns], "name": n} for n in names]}
        )

    def list_tables(self, c, ns):
        return self._ids(ns, self._tables)

    def list_views(self, c, ns):
        return self._ids(ns, self._views)

    def list_generic_tables(self, c, ns):
        return _Body(self.ext_status, {"identifiers": [{"name": "gt1"}]})

    def list_policies(self, c, ns):
        return _Body(self.ext_status, {"policies": [{"name": "pol1"}]})


class _Body(Resp):
    def __init__(self, status, body):
        super().__init__(status)
        self._body = body

    def json(self):
        return self._body


def _identity(**kw):
    base = dict(
        index=1,
        principal="authz1_principal",
        principal_role="authz1_principal_role",
        client_id="authz1_client",
        catalog="authz1_catalog",
        namespace="ns1",
    )
    base.update(kw)
    return ps.Identity(**base)


def test_entity_targets_come_from_the_api_not_a_format_string():
    """The seeder names them tbl1/vw1/pol1/gt1 — which is a fact about the
    seeder, not about the fixture in front of us."""
    i = _identity()
    missing = ps.resolve_entities(EntityClient(), i)
    assert (i.table, i.view, i.generic_table, i.policy) == (
        "tbl1",
        "vw1",
        "gt1",
        "pol1",
    )
    assert missing == {}


def test_a_feature_flagged_extension_leaves_its_target_unresolved():
    i = _identity()
    missing = ps.resolve_entities(EntityClient(ext_status=404), i)
    assert i.table == "tbl1" and i.view == "vw1"
    assert i.generic_table is None and i.policy is None
    assert missing == {"generic_table": "list [404]", "policy": "list [404]"}


def test_an_empty_namespace_is_reported_as_holding_none():
    i = _identity()
    missing = ps.resolve_entities(EntityClient(tables=(), views=()), i)
    assert missing["table"] == "namespace holds none"
    assert i.table is None


def test_no_namespace_means_nothing_can_resolve():
    missing = ps.resolve_entities(EntityClient(), _identity(namespace=None))
    assert set(missing) == {"table", "view", "policy", "generic_table"}
    assert all(v == "no namespace resolved" for v in missing.values())


def test_unavailable_and_undriveable_stay_apart_on_the_same_feature():
    """With extensions off: the COLLECTION read 404s (feature off) while the
    ITEM read has no target (fixture). Same feature, two different facts."""
    i = _identity()
    ps.resolve_entities(EntityClient(ext_status=404), i)
    st = {
        s.label.strip(): s
        for s in ps.probe_surface(
            EntityClient(ext_status=404), i, sweep.full_read_operations(i.fixture())
        )
    }
    assert st["GET  /policies"].verdict == "unavailable"
    assert st["GET  /policies/{p}"].verdict == "undriveable"


def test_only_the_full_profiles_ask_for_entity_targets():
    assert ps.PROFILES["catalog-scoped"].resolve_entities is False
    assert ps.PROFILES["catalog-scoped-full"].resolve_entities is True
    assert ps.PROFILES["service-admin"].resolve_entities is True


# ----------------------------------------------------------------------
# scope — the bug that made two privilege tiers produce identical output
# ----------------------------------------------------------------------
def test_service_admin_names_its_scope_explicitly():
    """A principal holding two principal-roles gets a token scoped to ONE.

    The `admin{N}` principals hold their own role plus `service_admin`. Probed
    at `PRINCIPAL_ROLE:admin1_principal_role`, service_admin's grants were
    never in scope and the "fully authorized" profile refused exactly the same
    nine operations as the catalog-scoped one — identical output from two
    privilege tiers, which is the shape of a scope bug and not a finding.
    """
    assert ps.PROFILES["service-admin"].scope == "PRINCIPAL_ROLE:service_admin"


def test_the_catalog_tiers_use_their_own_principal_role():
    """NOT `PRINCIPAL_ROLE:ALL` — that is root's scope, and a non-root
    principal asking for it is handed a token with no effective role."""
    assert ps.PROFILES["catalog-scoped"].scope is None
    assert ps.PROFILES["catalog-scoped-full"].scope is None


# ----------------------------------------------------------------------
# malformed — a harness fault must not be filed as an authorization outcome
# ----------------------------------------------------------------------
def test_a_400_is_malformed_not_refused():
    s = ps.OpStatus("GET  /config", "iceberg", 400, "warehouse not specified")
    assert s.verdict == "malformed"
    assert not s.ok and not s.unavailable and not s.undriveable


def test_403_is_still_refused_and_404_still_unavailable():
    assert ps.OpStatus("x", "mgmt", 403, "").verdict == "refused"
    assert ps.OpStatus("x", "polaris", 404, "").verdict == "unavailable"


def test_probe_table_shows_the_body_and_flags_a_harness_fault():
    out = ps.render_probe_table(
        [ps.OpStatus("GET  /config", "iceberg", 400, "warehouse not specified")]
    )
    assert "warehouse not specified" in out, "the body is what says WHY"
    assert "harness fault until proven otherwise" in out


def test_get_config_sends_a_warehouse():
    """Optional in the Iceberg spec; required in practice for a non-root
    principal, which answered 400 without it."""
    calls = []

    class Recorder(Client):
        def get_config(self, warehouse=None, token=None):
            calls.append(warehouse)
            return Resp(200 if warehouse else 400)

    ops = {l.strip(): f for l, _s, f in sweep.full_read_operations(FULL_FIXTURE)}
    ops["GET  /config"](Recorder())
    assert calls == [FULL_FIXTURE["catalog"]]
