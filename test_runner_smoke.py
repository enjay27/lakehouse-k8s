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

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
RUNNERS = ROOT / "diagnostics" / "api-sql-profile"


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
    ["seed_polaris", "scan_privileges", "profile_queries", "probe_api_surface"],
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
