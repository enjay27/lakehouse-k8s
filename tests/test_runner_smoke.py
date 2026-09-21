"""Smoke tests for the runner entry points in `diagnostics/api-sql-profile/`.

WHY THIS FILE EXISTS. The runners had zero coverage, and it cost three bugs in
one session — every one of them trivially catchable, and every one found on the
only machine that can reach the cluster:

  * `probe_policy` reached for `args.user`; this runner's flag is `--users`, a
    COUNT. An index flag only `scan_privileges.py` has.
  * the seed command omitted `--tables`, which defaults to False, so the first
    authz fixture would have had no tables at all.
  * `ledger_path()` ignored the prefix, so seeding a second fixture skipped
    every user and reported success.

`--help` does not catch these: argparse parses the flags without ever executing
the branch, and the branches themselves want a live Polaris. So these tests
call the functions DIRECTLY with stubs. They assert plumbing — that the right
arguments reach the right places — not behaviour, which belongs with the
modules in `src/`.
"""

import importlib.util
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNNERS = ROOT / "diagnostics" / "ladders" / "api-sql-profile"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, RUNNERS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def seeder():
    return _load("seed_polaris")


@pytest.fixture(scope="module")
def scanner():
    return _load("scan_privileges")


class Resp:
    def __init__(self, status=200, text=""):
        self.status_code = status
        self.text = text

    def json(self):
        return {}


class PolicyClient:
    """Accepts exactly one policy type; records everything it was asked."""

    def __init__(self, accepts="system.data_compaction"):
        self.accepts = accepts
        self.seen = []

    def create_policy(self, catalog, ns, payload):
        self.seen.append((catalog, ns, payload["type"]))
        ok = payload["type"] == self.accepts
        return Resp(200 if ok else 400, "" if ok else '{"error":"unknown type"}')


# ----------------------------------------------------------------------
# every runner still imports
# ----------------------------------------------------------------------
@pytest.mark.parametrize(
    "name",
    [
        "seed_polaris",
        "scan_privileges",
        "profile_queries",
        "probe_api_surface",
        "explain_api_matrix",
        "drive_api_surface",
    ],
)
def test_runner_imports(name):
    """Catches a bad import or a NameError at module scope before the cluster does."""
    assert _load(name) is not None


# ----------------------------------------------------------------------
# probe_policy — the AttributeError this file was written for
# ----------------------------------------------------------------------
def test_probe_policy_takes_its_target_from_the_spec(seeder):
    """No `args` at all: the index comes from `spec.start_index`.

    The first version read `args.user`, which does not exist on this runner's
    parser, so the function raised the moment it was reached.
    """
    from polaris_seed import SeedSpec

    pc = PolicyClient()
    rc = seeder.probe_policy(pc, SeedSpec(n_users=100, prefix="authz"))
    assert rc == 0
    assert {c for c, _ns, _t in pc.seen} == {"authz1_catalog"}
    assert {ns for _c, ns, _t in pc.seen} == {"ns1"}


def test_probe_policy_honours_start_index(seeder):
    from polaris_seed import SeedSpec

    pc = PolicyClient()
    seeder.probe_policy(pc, SeedSpec(n_users=5, prefix="admin", start_index=3))
    assert pc.seen[0][0] == "admin3_catalog"


def test_probe_policy_tries_every_candidate_and_fails_when_none_work(seeder):
    from polaris_seed import POLICY_TYPE_CANDIDATES, SeedSpec

    pc = PolicyClient(accepts="nothing-matches")
    rc = seeder.probe_policy(pc, SeedSpec(prefix="authz"))
    assert rc == 1, "no accepted type must be a non-zero exit"
    assert [t for _c, _ns, t in pc.seen] == list(POLICY_TYPE_CANDIDATES)


def test_probe_policy_reports_the_accepted_type(seeder, capsys):
    from polaris_seed import SeedSpec

    seeder.probe_policy(PolicyClient(), SeedSpec(prefix="authz"))
    out = capsys.readouterr().out
    assert "ACCEPTED  system.data_compaction" in out
    assert "--policy-type system.data_compaction" in out


# ----------------------------------------------------------------------
# ledger paths and profiles — the other two bugs
# ----------------------------------------------------------------------
def test_ledger_path_is_per_prefix(seeder):
    """One shared ledger made every fixture after the first a silent no-op."""
    assert seeder.ledger_path("user").name == "seed_ledger.json"
    assert seeder.ledger_path("authz").name == "seed_ledger-authz.json"
    assert seeder.ledger_path("admin").name == "seed_ledger-admin.json"


def test_a_fixture_without_tables_leaves_the_entity_reads_undriveable(seeder):
    """`--tables` defaults to False on this runner (`set_defaults(tables=False)`).

    Asserted on `SeedSpec`, which is what actually governs the seed — the
    parser is built inside `main()` and extracting it to test one default would
    mean refactoring a working runner for no behavioural gain.

    The cost of forgetting the flag is not abstract: the 1,000-user fixture was
    seeded that way, and loadTable / headTable / loadCredentials had nothing to
    point at.
    """
    from polaris_seed import SeedSpec

    thin = SeedSpec(n_users=100, prefix="authz", create_tables=False)
    assert thin.expected_counts()["tables"] == 0
    full = SeedSpec(n_users=100, prefix="authz", create_tables=True)
    assert full.expected_counts()["tables"] == 1000


def test_scan_runner_resolves_every_profile(scanner):
    import privilege_scan as ps

    for name, profile in ps.PROFILES.items():
        scanner.PROFILE = profile
        assert scanner.prefix() == profile.prefix
        assert scanner.probe_path().name.endswith(".json")
    scanner.PROFILE = ps.PROFILES[ps.DEFAULT_PROFILE]


def test_default_profile_keeps_the_original_probe_filename(scanner):
    """`privscan-20260824-123408` must still resolve against its own probe."""
    import privilege_scan as ps

    scanner.PROFILE = ps.PROFILES[ps.DEFAULT_PROFILE]
    assert scanner.probe_path().name == "privscan_probe.json"


# ----------------------------------------------------------------------
# _try_extension — lag is not a disabled feature
# ----------------------------------------------------------------------
class Sequence:
    """Returns the given responses in order, then REPEATS the last one.

    Repeating rather than falling back to 200 matters: `_attempt` retries the
    transient class, so a stub that succeeds once the queue drains tests the
    retry rather than the refusal, and a "persistent 501" case would quietly
    assert nothing.
    """

    def __init__(self, *responses):
        self.queue = list(responses)
        self.calls = 0

    def __call__(self, catalog, ns, payload):
        self.calls += 1
        return self.queue.pop(0) if len(self.queue) > 1 else self.queue[0]


def test_lag_is_retried_and_does_not_disable_the_feature():
    """403/404/5xx are PG-HA read-after-write lag, not a missing feature.

    Creating a policy into a namespace written milliseconds earlier is exactly
    that race. The first version of `_try_extension` made ONE attempt and
    marked the kind off on any non-2xx, so one unlucky user disabled policies
    for a whole 100-user run — silently, with no failed user and no error.
    """
    import polaris_seed as seed

    result = seed.SeedResult()
    call = Sequence(Resp(404, "not visible yet"), Resp(200))
    assert seed._try_extension(call, "c", "ns", {}, "policies", result) is True
    assert result.features_off == set()
    assert call.calls == 2, "the lagging attempt must be retried"


def test_a_400_disables_the_kind_and_blames_the_payload():
    """Re-issuing a payload the build will never accept 200 more times only
    makes the same discovery slower."""
    import polaris_seed as seed

    result = seed.SeedResult()
    call = Sequence(Resp(400, '{"error":"Unknown policy type"}'))
    assert seed._try_extension(call, "c", "ns", {}, "policies", result) is False
    assert result.features_off == {"policies"}
    assert "seeder's fault" in result.feature_errors["policies"]
    assert "Unknown policy type" in result.feature_errors["policies"]


def test_a_501_is_reported_as_the_build_not_the_payload():
    import polaris_seed as seed

    result = seed.SeedResult()
    call = Sequence(Resp(501))
    assert seed._try_extension(call, "c", "ns", {}, "generic_tables", result) is False
    assert "not available on this build" in result.feature_errors["generic_tables"]
    assert call.calls > 1, "a 5xx is retried before being called definitive"


def test_the_accepted_policy_type_is_the_default():
    """`--probe-policy` measured system.data-compaction accepted on 2026-08-31,
    and system.data_compaction rejected. The default must be the accepted one."""
    import polaris_seed as seed

    assert seed.DEFAULT_POLICY_TYPE == "system.data-compaction"
    assert seed._policy_payload("p1")["type"] == "system.data-compaction"


# ----------------------------------------------------------------------
# _summarise_plan — the index question, asked of every relation
#
# The single-node summary was built to answer one question about
# `grant_records`. "Does this API use an index" is asked of every relation a
# statement touches, and reading only the chosen node reports the first scan's
# verdict as the whole statement's.
# ----------------------------------------------------------------------
@pytest.fixture(scope="module")
def profiler():
    return _load("profile_queries")


def _plan(*nodes):
    return {"Plan": {"Node Type": "Nested Loop", "Plans": list(nodes)}}


def test_every_scan_node_is_reported_not_only_the_chosen_one(profiler):
    r = profiler._summarise_plan(
        _plan(
            {"Node Type": "Seq Scan", "Relation Name": "grant_records"},
            {
                "Node Type": "Index Scan",
                "Relation Name": "entities",
                "Index Name": "idx_entities",
            },
        ),
        "grant_records",
    )
    assert len(r["scans"]) == 2
    assert r["seq_scanned"] == ["grant_records"]
    assert r["indexes_used"] == ["idx_entities"]
    #: the original single-node fields still answer about the focus table
    assert r["scan"] == "Seq Scan" and r["relation"] == "grant_records"


def test_a_bitmap_heap_read_is_index_access_not_a_sequential_scan(profiler):
    """The classification that a substring search gets wrong.

    A Bitmap Heap Scan reaches its rows through the child Bitmap Index Scan, so
    the relation is index-accessed. Calling it a sequential scan because the
    node type ends in "Scan" would report a missing index that is present and
    working.
    """
    r = profiler._summarise_plan(
        _plan(
            {
                "Node Type": "Bitmap Heap Scan",
                "Relation Name": "entities",
                "Plans": [
                    {"Node Type": "Bitmap Index Scan", "Index Name": "idx_entities"}
                ],
            },
        )
    )
    assert r["seq_scanned"] == [], "a bitmap heap read is not a Seq Scan"
    assert r["indexes_used"] == ["idx_entities"]


def test_a_parallel_seq_scan_still_counts_as_sequential(profiler):
    r = profiler._summarise_plan(
        _plan({"Node Type": "Parallel Seq Scan", "Relation Name": "grant_records"})
    )
    assert r["seq_scanned"] == ["grant_records"]


def test_a_plan_with_no_scan_at_all_reports_neither(profiler):
    """`INSERT ... VALUES` plans to a Result node. There is no index to detect,
    and reporting "no index used" there would read as a finding rather than a
    category error."""
    r = profiler._summarise_plan({"Plan": {"Node Type": "Result"}})
    assert r["scans"] == []
    assert r["seq_scanned"] == [] and r["indexes_used"] == []


def test_explain_statements_without_analyze_plans_once_and_reports_no_timing(
    profiler, monkeypatch
):
    """Plain EXPLAIN is what makes a write safe to ask about.

    `EXPLAIN ANALYZE` on an INSERT/UPDATE/DELETE really performs it. This path
    must therefore call `explain`, never `explain_n` — which additionally would
    raise, since it medians an `Execution Time` that a plan-only EXPLAIN does
    not emit.
    """
    import api_trace

    calls = {"explain": 0, "explain_n": 0}

    def fake_explain(conn, sql, params=None, analyze=True, no_lb=True):
        calls["explain"] += 1
        assert analyze is False, "a write must not be ANALYZEd"
        return _plan({"Node Type": "Seq Scan", "Relation Name": "entities"})

    def fake_explain_n(*a, **k):  # pragma: no cover - must never run
        calls["explain_n"] += 1
        raise AssertionError("explain_n has no Execution Time to median here")

    monkeypatch.setattr(api_trace, "explain", fake_explain)
    monkeypatch.setattr(api_trace, "explain_n", fake_explain_n)

    import query_profile as qp

    doc = (
        "### `iceberg.create_table`\n\n- `POST /v1/x` → **200**\n\n"
        "**[0]** `entities` · INSERT · no timing\n\n"
        "```sql\nINSERT INTO POLARIS_SCHEMA.ENTITIES (id) VALUES (?)\n```\n"
        "params: `7`\n"
    )
    (pair,) = qp.parse_api_statements(doc).pairs

    class _Cur:
        def execute(self, *a):
            pass

        def close(self):
            pass

    class _Conn:
        def cursor(self):
            return _Cur()

    (entry,) = profiler.explain_statements(_Conn(), [pair], analyze=False)
    assert calls == {"explain": 1, "explain_n": 0}, "exactly one plan, no timing runs"
    assert entry["analyze"] is False
    assert "explain_ms" not in entry
    assert entry["seq_scanned"] == ["entities"]
    assert entry["apis"] == ["iceberg.create_table"], "the pair carries its APIs"


# ----------------------------------------------------------------------
# explain_api_matrix — the per-API rollup, and the refusal to sweep a bad parse
# ----------------------------------------------------------------------
@pytest.fixture(scope="module")
def explainer():
    return _load("explain_api_matrix")


def test_a_report_that_did_not_fully_parse_is_refused_before_any_sweep(
    explainer, tmp_path
):
    """A short worklist looks exactly like a complete one downstream, so the
    refusal has to come before the database is touched, not after."""
    doc = tmp_path / "bad.md"
    doc.write_text(
        "### `mgmt.get_principal`\n\n- `GET /v1/x` → **200**\n\n"
        "**[0]** `entities` · SELECT · no timing\n\nno sql fence here\n"
    )
    with pytest.raises(SystemExit) as e:
        explainer.load_matrix(doc)
    assert "did not parse" in str(e.value)


def _pair(sql, params, apis, table="entities", verb="SELECT"):
    import query_profile as qp

    p = qp.ApiStatement(sql=sql, params=params, table=table, verb=verb)
    for api, idxs in apis.items():
        p.apis[api] = idxs
    return p


def test_a_statement_shared_by_two_apis_rolls_up_to_both(explainer):
    """Statements are shared, so the rollup is a fan-out of the pair results —
    not a second measurement that could disagree with the first."""
    import query_profile as qp

    ms = qp.MatrixStatements()
    ms.pairs = [
        _pair(
            "SELECT 1", "a", {"mgmt.get_principal": [0], "mgmt.list_principals": [3, 4]}
        )
    ]
    explains = [
        {
            "seq_scanned": ["entities"],
            "indexes_used": [],
            "scans": [{"relation": "entities"}],
        }
    ]
    r = explainer.per_api_rollup(explains, ms)
    assert set(r) == {"mgmt.get_principal", "mgmt.list_principals"}
    assert r["mgmt.get_principal"]["statements"] == 1
    assert r["mgmt.list_principals"]["statements"] == 2, "both instances counted"
    assert r["mgmt.get_principal"]["seq_scanned"] == ["entities"]


def test_a_skipped_statement_is_counted_as_skipped_not_as_index_using(explainer):
    """The three redacted secret-table statements can never be planned. Letting
    them fall through as 'no seq scan' would read as a clean result."""
    import query_profile as qp

    ms = qp.MatrixStatements()
    ms.pairs = [_pair("SELECT 1", "", {"mgmt.create_principal": [0]})]
    r = explainer.per_api_rollup([{"skipped": "params redacted"}], ms)
    row = r["mgmt.create_principal"]
    assert row["planned"] == 0 and row["skipped"] == 1
    assert row["seq_scanned"] == [] and row["indexes_used"] == []
    assert row["uses_index_only"] is False, "unplanned is not index-clean"


def test_an_api_whose_statements_all_use_indexes_is_marked_as_such(explainer):
    import query_profile as qp

    ms = qp.MatrixStatements()
    ms.pairs = [_pair("SELECT 1", "a", {"mgmt.get_catalog": [0]})]
    explains = [
        {
            "seq_scanned": [],
            "indexes_used": ["idx_entities"],
            "scans": [{"relation": "entities"}],
        }
    ]
    r = explainer.per_api_rollup(explains, ms)
    assert r["mgmt.get_catalog"]["uses_index_only"] is True
    assert r["mgmt.get_catalog"]["relations"] == ["entities"]


# ----------------------------------------------------------------------
# drive_api_surface — the fixture must survive between five processes
# ----------------------------------------------------------------------
@pytest.fixture(scope="module")
def driver():
    return _load("drive_api_surface")


def test_the_fixture_is_persisted_and_reloaded_identically(
    driver, tmp_path, monkeypatch
):
    """Setup, three drives and teardown are five separate processes. A fixture
    whose name is recomputed from a timestamp in each of them is five different
    fixtures, and the three cases would then differ by more than the identity."""
    import api_surface as surf

    monkeypatch.setattr(driver, "STATE", tmp_path / "fx.json")
    monkeypatch.setattr(driver, "RUNS_DIR", tmp_path)
    fx = surf.ProbeFixture.stamped()
    driver.save_fixture(fx)
    back = driver.load_fixture()
    assert back.cat == fx.cat and back.prole == fx.prole
    assert back.prefix == fx.prefix


def test_driving_without_a_recorded_fixture_refuses_with_the_reason(
    driver, tmp_path, monkeypatch
):
    monkeypatch.setattr(driver, "STATE", tmp_path / "absent.json")
    with pytest.raises(SystemExit) as e:
        driver.load_fixture()
    assert "--setup first" in str(e.value)


def test_admin_maps_to_a_seeded_principal_not_to_root(driver):
    """root's authorization resolves TWO grant rows and is the least
    representative identity in the realm; a seeded service_admin resolves
    ~1,100 and an authz principal 52. That spread is the point of the cases."""
    assert driver.CASE_PREFIX["admin"] == "admin"
    assert driver.CASE_PREFIX["authorized"] == "authz"
    assert driver.CASE_PREFIX["unauthorized"] == "zerograve"
    assert "root" not in driver.CASE_PREFIX.values()


def test_resolve_identity_accepts_a_named_principal_for_the_zero_grant_case(driver):
    """`load_identities` requires a principal to own a {prefix}N_catalog and
    reports anything else as no_catalog. Correct for the seeded tiers, fatal for
    the unauthorized case, whose whole definition is a principal holding
    nothing — so it is named outright rather than discovered."""
    ident, problems = driver.resolve_identity(
        "unauthorized",
        client_id="zerograve_client",
        principal_role="zerograve_principal_role",
    )
    assert ident.client_id == "zerograve_client"
    assert ident.principal_role == "zerograve_principal_role"
    assert ident.catalog is None, "it owns no catalog — that is the point"
    assert problems == {}


def test_a_named_principal_without_a_role_is_refused_not_scoped_to_all(driver):
    """The scope must be the principal's OWN role. Falling back to
    PRINCIPAL_ROLE:ALL would hand a non-root principal a token with no effective
    role, and every 403 would then be about the scope string."""
    with pytest.raises(SystemExit, match="principal-role"):
        driver.resolve_identity("unauthorized", client_id="zerograve_client")


def test_resolve_identity_matches_load_identities_arity(driver, monkeypatch):
    """This test exists because the first version of build_clients called
    load_identities(prefix=...) and authenticate(identity, secret). Both are
    wrong — load_identities takes (conn, schema, realm, ...) and returns a PAIR,
    and authenticate returns a TRIPLE. Nothing caught it until the contracts
    were read, and it would have failed on the first real drive."""
    import privilege_scan as ps

    seen = {}

    def fake(conn, schema, realm, prefix="user", limit=None):
        seen.update(conn=conn, schema=schema, realm=realm, prefix=prefix, limit=limit)
        return [
            ps.Identity(
                index=1,
                principal="authz1_principal",
                principal_role="authz1_principal_role",
                client_id="cid",
                catalog="authz1_catalog",
            )
        ], {}

    monkeypatch.setattr(ps, "load_identities", fake)
    ident, _ = driver.resolve_identity(
        "authorized", conn="CONN", schema="polaris_schema", realm="POLARIS"
    )
    assert seen == {
        "conn": "CONN",
        "schema": "polaris_schema",
        "realm": "POLARIS",
        "prefix": "authz",
        "limit": 1,
    }
    assert ident.client_id == "cid"


def test_no_drivable_principal_names_the_no_catalog_reason(driver, monkeypatch):
    import privilege_scan as ps

    monkeypatch.setattr(
        ps,
        "load_identities",
        lambda *a, **k: ([], {"no_catalog": ["zerograve_principal"]}),
    )
    with pytest.raises(SystemExit) as e:
        driver.resolve_identity("authorized", conn="C", schema="s", realm="R")
    assert "no_catalog" in str(e.value)
    assert "--client-id" in str(e.value)


def test_capture_streams_hands_tracer_streams_not_a_directory(driver, tmp_path):
    """The bug that turned 43 operations into 43 errors.

    Tracer takes stream OBJECTS — polaris_log, pg_log, minio_trace — not a path.
    Passing the capture directory raised IsADirectoryError on every operation.
    Nothing caught it because nothing had ever called this path with a real
    directory; the tests drove the catalogue with a stub tracer.
    """
    from api_trace import FileStream, MultiStream

    for n in ("polaris.log", "pg-0.log", "pg-1.log", "pg-2.log", "minio.json"):
        (tmp_path / n).write_text("x")
    st = driver.capture_streams(tmp_path)
    assert set(st) == {"polaris_log", "pg_log", "minio_trace"}
    assert isinstance(st["polaris_log"], FileStream)
    assert isinstance(st["minio_trace"], FileStream)
    #: every replica, because pgpool routes reads across them and a statement's
    #: duration line lands in whichever node ran it
    assert isinstance(st["pg_log"], MultiStream)
    assert len(st["pg_log"].streams) == 3
    for s in st["pg_log"].streams:
        assert not s.path.endswith(("polaris.log", "minio.json"))


def test_capture_streams_accepts_an_older_single_pg_log(driver, tmp_path):
    (tmp_path / "pg.log").write_text("x")
    st = driver.capture_streams(tmp_path)
    assert [s.path.split("/")[-1] for s in st["pg_log"].streams] == ["pg.log"]


def test_multistream_concatenates_every_replica(tmp_path):
    """Reading one file attributes timings to a fraction of the statements and
    leaves the rest blank — indistinguishable from durations being off."""
    from api_trace import MultiStream

    a, b = tmp_path / "pg-0.log", tmp_path / "pg-1.log"
    a.write_text("one\n")
    b.write_text("two\n")
    ms = MultiStream([a, b])
    ms.mark()
    a.write_text("one\nAAA\n")
    b.write_text("two\nBBB\n")
    got = ms.read_since_mark()
    assert "AAA" in got and "BBB" in got


def test_the_admin_case_scopes_its_token_to_service_admin_not_its_own_role(
    driver, monkeypatch
):
    """The trap privilege_scan names: a token is scoped to ONE principal-role.

    admin{N}_principal holds two — its own (catalog-scoped on admin{N}_catalog)
    and service_admin, which is the entire reason the tier exists.
    load_identities builds the name from the seeder's convention and hands back
    the own-role, so a token scoped to it carries no service-level authority and
    the drive is refused on all 43 operations — a distribution byte-identical to
    the zero-grant case.
    """
    import privilege_scan as ps

    monkeypatch.setattr(
        ps,
        "load_identities",
        lambda *a, **k: (
            [
                ps.Identity(
                    index=1,
                    principal="admin1_principal",
                    principal_role="admin1_principal_role",
                    client_id="cid",
                    catalog="admin1_catalog",
                )
            ],
            {},
        ),
    )
    ident, _ = driver.resolve_identity("admin", conn="C", schema="s", realm="R")
    assert ident.principal_role == ps.SERVICE_ADMIN_ROLE
    assert ident.principal == "admin1_principal", "same identity, different role"


def test_the_authorized_case_keeps_its_own_principal_role(driver, monkeypatch):
    """Only admin holds a second role. Rewriting the scope for every tier would
    hand a catalog-scoped principal a role it is not a member of."""
    import privilege_scan as ps

    monkeypatch.setattr(
        ps,
        "load_identities",
        lambda *a, **k: (
            [
                ps.Identity(
                    index=1,
                    principal="authz1_principal",
                    principal_role="authz1_principal_role",
                    client_id="cid",
                    catalog="authz1_catalog",
                )
            ],
            {},
        ),
    )
    ident, _ = driver.resolve_identity("authorized", conn="C", schema="s", realm="R")
    assert ident.principal_role == "authz1_principal_role"


# ----------------------------------------------------------------------
# the index-state guard that could never fail in one direction
# ----------------------------------------------------------------------
class _FakeIndexConn:
    """A connection whose grant_records carries only the named indexes."""

    def __init__(self, names):
        self._names = list(names)

    def cursor(self):
        return self

    def execute(self, *a, **k):
        pass

    def fetchall(self):
        return [(n, f"CREATE INDEX {n} ...") for n in self._names]

    def close(self):
        pass


def test_has_index_is_not_a_truthiness_test_on_every_index():
    """`bool(index_state(conn))` was the test, and grant_records ALWAYS has a
    primary key -- so `explain_api_matrix`'s --index-state guard answered
    "present" in both halves of every sweep. It could not detect the state it
    exists to guard against, and it blocked the index-absent pass outright
    (notebook 04's first run, 2026-09-03). A guard that cannot fail in one
    direction is not a guard."""
    pq = _load("profile_queries")
    only_pkey = _FakeIndexConn(["grant_records_pkey"])
    assert pq.index_state(only_pkey), "the table does have indexes"
    assert not pq.has_index(only_pkey), "but not THE one"

    with_it = _FakeIndexConn(["grant_records_pkey", pq.FOCUS_INDEX])
    assert pq.has_index(with_it)


def test_the_focus_index_is_named_once():
    """A second spelling would be a second thing to keep in agreement."""
    pq = _load("profile_queries")
    assert pq.FOCUS_INDEX == "idx_grant_records_grantee"


# ----------------------------------------------------------------------
# the EXPLAIN workbook
# ----------------------------------------------------------------------
def test_predicate_columns_collapses_the_three_orderings_to_one_shape():
    """The predicate column ORDER varies between runs: the same grantee lookup
    appeared as three different texts across the three identities. Comparing
    text reports differences that do not exist, which is the entire reason the
    Shapes sheet canonicalises by column SET."""
    w = _load("render_explain_workbook")
    a = "SELECT x FROM g WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?"
    b = "SELECT x FROM g WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?"
    c = "SELECT x FROM g WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?"
    assert w.predicate_columns(a) == w.predicate_columns(b) == w.predicate_columns(c)
    assert w.predicate_columns(a) == ("grantee_catalog_id", "grantee_id", "realm_id")


def test_predicate_columns_reads_both_placeholder_dialects():
    """Polaris logs `?`; PostgreSQL logs `$1`. Statements arrive from both."""
    w = _load("render_explain_workbook")
    assert w.predicate_columns("... WHERE a = $1 AND b = $2") == ("a", "b")


def test_a_statement_with_no_predicate_yields_an_empty_shape_not_a_crash():
    w = _load("render_explain_workbook")
    assert w.predicate_columns("INSERT INTO t (a, b) VALUES (?, ?)") == ()
    assert w.predicate_columns(None) == ()


def test_an_oversized_cell_is_truncated_visibly():
    """Excel's limit is 32,767 characters. A SILENTLY truncated cell is worse
    than a short one -- the marker names the real length so the reader knows to
    go to the run file."""
    w = _load("render_explain_workbook")
    out = w.truncate("x" * 40_000)
    assert len(out) < 40_000
    assert "truncated" in out and "40000 chars" in out


def test_a_short_cell_is_untouched():
    w = _load("render_explain_workbook")
    assert w.truncate("SELECT 1") == "SELECT 1"
    assert w.truncate(None) == ""


def test_scan_summary_collapses_a_bitmapor_rather_than_listing_it_five_times():
    """A Bitmap Index Scan node has no Relation Name, and a BitmapOr repeats the
    same index once per branch -- five sub-scans meaning two indexes."""
    w = _load("render_explain_workbook")
    e = {
        "scans": [
            {"node": "Bitmap Heap Scan", "relation": "entities", "index": None},
            {"node": "Bitmap Index Scan", "relation": None, "index": "entities_pkey"},
            {"node": "Bitmap Index Scan", "relation": None, "index": "idx_entities"},
            {"node": "Bitmap Index Scan", "relation": None, "index": "entities_pkey"},
        ],
        "node_types": ["Bitmap Heap Scan", "BitmapOr"],
    }
    got = w.scan_summary(e)
    assert got == "Bitmap Heap Scan on entities using entities_pkey ×2, idx_entities"
    assert "None" not in got


def test_index_cond_and_filter_separate_a_served_lookup_from_an_unserved_one():
    """The pair IS the finding, at row level. Index Cond is what the planner
    pushed into the index; Filter is what it tested on every row it read. A
    served lookup has the first and not the second; the grantee lookup is the
    reverse, which is what "no usable index" means concretely."""
    w = _load("render_explain_workbook")
    served = {
        "plan": {
            "Plan": {
                "Node Type": "Index Only Scan",
                "Index Cond": "((realm_id = 'X') AND (securable_id = 1))",
            }
        }
    }
    unserved = {
        "plan": {
            "Plan": {
                "Node Type": "Seq Scan",
                "Filter": "((grantee_id = 1) AND (realm_id = 'X'))",
            }
        }
    }
    assert w.cond_and_filter(served) == (
        "((realm_id = 'X') AND (securable_id = 1))",
        "",
    )
    assert w.cond_and_filter(unserved) == (
        "",
        "((grantee_id = 1) AND (realm_id = 'X'))",
    )


def test_a_bitmap_plans_condition_is_found_on_the_child_not_the_heap_node():
    """On a Bitmap plan the condition sits on the Bitmap Index Scan child. Only
    reading the top node would report no condition at all."""
    w = _load("render_explain_workbook")
    e = {
        "plan": {
            "Plan": {
                "Node Type": "Bitmap Heap Scan",
                "Relation Name": "entities",
                "Plans": [
                    {"Node Type": "Bitmap Index Scan", "Index Cond": "(realm_id = 'X')"}
                ],
            }
        }
    }
    cond, filt = w.cond_and_filter(e)
    assert cond == "(realm_id = 'X')" and filt == ""


def test_a_statement_with_no_plan_yields_empty_strings_not_a_crash():
    w = _load("render_explain_workbook")
    assert w.cond_and_filter({}) == ("", "")
    assert w.plan_node({}) == {}
