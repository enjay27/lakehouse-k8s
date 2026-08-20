"""
Pytest suite for src/polaris_seed.py.

Runs the seeder end-to-end against a stateful in-memory fake Polaris — so
creation ordering, idempotency, resumability, ledger integrity, teardown and
the local-host guard are all verified without a live cluster.

The tests that matter most here are the destructive-safety ones: the host
guard, and the rule that teardown works from the ledger rather than by name.

Run: pytest test_polaris_seed.py
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent / "src"))
from polaris_seed import (COARSE_CATALOG_PRIVILEGES,  # noqa: E402
                          FULL_CATALOG_PRIVILEGES, OWNER_ROLE_NAME, Ledger,
                          SeedResult, SeedSpec, find_strays, require_local,
                          seed, teardown, verify_counts)


# ----------------------------------------------------------------------
# fakes
# ----------------------------------------------------------------------
class Resp:
    def __init__(self, status=200, body=None):
        self.status_code = status
        self._body = body or {}
        self.text = json.dumps(self._body)

    def json(self):
        return self._body


class FakePolaris:
    """Stateful fake of the PolarisREST surface the seeder uses."""

    def __init__(self, base_url="http://localhost:8181", reject_privs=(), fail_on=None):
        self.base_url = base_url
        self.principals, self.principal_roles, self.catalogs = set(), set(), set()
        self.catalog_roles, self.grants = set(), set()
        self.assignments = []
        self.reject_privs = set(reject_privs)
        self.fail_on = fail_on or {}

    def _maybe_fail(self, op, name):
        if self.fail_on.get(op) == name:
            return Resp(500, {"error": "induced"})
        return None

    def create_principal(self, name):
        f = self._maybe_fail("create_principal", name)
        if f:
            return f
        if name in self.principals:
            return Resp(409)
        self.principals.add(name)
        return Resp(200)

    def create_principal_role(self, name):
        if name in self.principal_roles:
            return Resp(409)
        self.principal_roles.add(name)
        return Resp(200)

    def assign_principal_role_to_principal(self, principal, role):
        self.assignments.append(("pr->p", role, principal))
        return Resp(200)

    def create_catalog(self, name, **kw):
        f = self._maybe_fail("create_catalog", name)
        if f:
            return f
        if name in self.catalogs:
            return Resp(409)
        self.catalogs.add(name)
        return Resp(200)

    def create_catalog_role(self, catalog, name):
        if catalog not in self.catalogs:
            return Resp(404)
        key = (catalog, name)
        if key in self.catalog_roles:
            return Resp(409)
        self.catalog_roles.add(key)
        return Resp(200)

    def assign_catalog_role_to_principal_role(self, catalog, prole, crole):
        self.assignments.append(("cr->pr", catalog, crole, prole))
        return Resp(200)

    def grant_privilege(self, catalog, crole, priv):
        if priv in self.reject_privs:
            return Resp(400, {"error": f"unknown privilege {priv}"})
        self.grants.add((catalog, crole, priv))
        return Resp(200)

    def delete_catalog(self, name, purge=False):
        if name not in self.catalogs:
            return Resp(404)
        self.catalogs.discard(name)
        self.catalog_roles = {k for k in self.catalog_roles if k[0] != name}
        self.grants = {g for g in self.grants if g[0] != name}
        return Resp(204)

    def delete_principal_role(self, name):
        if name not in self.principal_roles:
            return Resp(404)
        self.principal_roles.discard(name)
        return Resp(204)

    def delete_principal(self, name):
        if name not in self.principals:
            return Resp(404)
        self.principals.discard(name)
        return Resp(204)

    def list_principals(self):
        return Resp(200, {"principals": [{"name": n} for n in sorted(self.principals)]})

    def list_principal_roles(self):
        return Resp(200, {"roles": [{"name": n} for n in sorted(self.principal_roles)]})

    def list_catalogs(self):
        return Resp(200, {"catalogs": [{"name": n} for n in sorted(self.catalogs)]})


class FakeIceberg:
    def __init__(self, polaris):
        self.p = polaris
        self.namespaces, self.tables = set(), set()

    def create_namespace(self, catalog, ns, **kw):
        key = (catalog, ns)
        if key in self.namespaces:
            return Resp(409)
        self.namespaces.add(key)
        return Resp(200)

    def create_table(self, catalog, ns, payload, **kw):
        key = (catalog, ns, payload["name"])
        if key in self.tables:
            return Resp(409)
        self.tables.add(key)
        return Resp(200)


class FakePgCursor:
    def __init__(self, conn):
        self.conn = conn
        self._r = None

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, args=None):
        self._r = [
            self.conn.counts["grant_records" if "grant_records" in sql else "entities"]
        ]

    def fetchone(self):
        return self._r


class FakePg:
    def __init__(self, entities=0, grants=0):
        self.counts = {"entities": entities, "grant_records": grants}

    def cursor(self):
        return FakePgCursor(self)


@pytest.fixture
def small_spec():
    return SeedSpec(n_users=3, namespaces_per_catalog=2, tables_per_namespace=2)


@pytest.fixture
def ledger_path(tmp_path):
    return str(tmp_path / "ledger.json")


# ----------------------------------------------------------------------
# host guard — destructive safety
# ----------------------------------------------------------------------
def test_require_local_accepts_localhost_and_orbstack_range():
    assert require_local("http://localhost:8181")
    assert require_local("http://127.0.0.1:8181")
    assert require_local("http://192.168.139.2:8181")


def test_require_local_rejects_remote_hosts():
    for url in (
        "http://polaris.dev.company.internal:8181",
        "https://polaris-prod.example.com",
        "http://10.0.0.5:8181",
    ):
        with pytest.raises(AssertionError):
            require_local(url)


def test_seed_refuses_to_run_against_remote(small_spec, ledger_path):
    p = FakePolaris(base_url="http://polaris.prod.company:8181")
    with pytest.raises(AssertionError):
        seed(p, FakeIceberg(p), small_spec, ledger_path)


def test_teardown_refuses_to_run_against_remote(ledger_path):
    p = FakePolaris(base_url="http://polaris.prod.company:8181")
    with pytest.raises(AssertionError):
        teardown(p, ledger_path)


# ----------------------------------------------------------------------
# spec
# ----------------------------------------------------------------------
def test_expected_counts_match_the_specified_fixture():
    exp = SeedSpec().expected_counts()
    assert exp["principals"] == 1000
    assert exp["catalogs"] == 1000
    assert exp["namespaces"] == 2000
    assert exp["tables"] == 10000
    assert exp["entities_total"] == 1000 * 4 + 2000 + 10000
    assert exp["grant_records"] == 1000 * len(FULL_CATALOG_PRIVILEGES)


def test_coarse_privileges_produce_far_fewer_grant_rows():
    full = SeedSpec().expected_counts()["grant_records"]
    coarse = SeedSpec(privileges=list(COARSE_CATALOG_PRIVILEGES)).expected_counts()[
        "grant_records"
    ]
    assert coarse * 10 < full


def test_names_follow_the_specified_convention():
    n = SeedSpec().names(7)
    assert n["principal"] == "user7_principal"
    assert n["principal_role"] == "user7_principal_role"
    assert n["catalog"] == "user7_catalog"
    assert n["catalog_role"] == OWNER_ROLE_NAME


def test_metadata_only_spec_skips_tables():
    assert SeedSpec(create_tables=False).expected_counts()["tables"] == 0


# ----------------------------------------------------------------------
# seeding
# ----------------------------------------------------------------------
def test_seed_creates_the_full_shape(small_spec, ledger_path):
    p = FakePolaris()
    ic = FakeIceberg(p)
    res = seed(p, ic, small_spec, ledger_path)

    assert res.completed_users == 3
    assert not res.failed_users
    assert p.principals == {f"user{i}_principal" for i in (1, 2, 3)}
    assert p.principal_roles == {f"user{i}_principal_role" for i in (1, 2, 3)}
    assert p.catalogs == {f"user{i}_catalog" for i in (1, 2, 3)}
    assert all(r[1] == OWNER_ROLE_NAME for r in p.catalog_roles)
    assert len(ic.namespaces) == 6
    assert len(ic.tables) == 12
    assert len(p.grants) == 3 * len(FULL_CATALOG_PRIVILEGES)


def test_owner_role_is_wired_to_the_users_principal_role(small_spec, ledger_path):
    p = FakePolaris()
    seed(p, FakeIceberg(p), small_spec, ledger_path)
    cr = [a for a in p.assignments if a[0] == "cr->pr"]
    assert ("cr->pr", "user1_catalog", OWNER_ROLE_NAME, "user1_principal_role") in cr


def test_seed_is_idempotent_on_rerun_with_fresh_ledger(small_spec, tmp_path):
    p = FakePolaris()
    ic = FakeIceberg(p)
    seed(p, ic, small_spec, str(tmp_path / "a.json"))
    res2 = seed(p, ic, small_spec, str(tmp_path / "b.json"))
    assert not res2.failed_users, "409s must be tolerated, not fatal"
    assert len(p.principals) == 3, "no duplicates created"


def test_seed_resumes_from_ledger(small_spec, ledger_path):
    p = FakePolaris()
    ic = FakeIceberg(p)
    seed(p, ic, small_spec, ledger_path)
    res = seed(p, ic, small_spec, ledger_path)
    assert res.skipped_users == 3
    assert res.completed_users == 0
    assert res.calls == 0, "a fully-seeded fixture costs no API calls to re-run"


def test_rejected_privilege_names_are_recorded_not_fatal(small_spec, ledger_path):
    p = FakePolaris(reject_privs={"VIEW_FULL_METADATA"})
    res = seed(p, FakeIceberg(p), small_spec, ledger_path)
    assert res.completed_users == 3, "a bad privilege name must not abort the seed"
    assert "VIEW_FULL_METADATA" in res.invalid_privileges


def test_failed_user_is_recorded_and_not_marked_done(small_spec, ledger_path):
    p = FakePolaris(fail_on={"create_catalog": "user2_catalog"})
    res = seed(p, FakeIceberg(p), small_spec, ledger_path)
    assert res.completed_users == 2
    assert [f["index"] for f in res.failed_users] == [2]
    assert 2 not in Ledger(ledger_path).done_users, "failed users must be retryable"


def test_failed_user_is_retried_on_the_next_run(small_spec, ledger_path):
    p = FakePolaris(fail_on={"create_catalog": "user2_catalog"})
    ic = FakeIceberg(p)
    seed(p, ic, small_spec, ledger_path)
    p.fail_on = {}
    res = seed(p, ic, small_spec, ledger_path)
    assert res.completed_users == 1 and res.skipped_users == 2
    assert "user2_catalog" in p.catalogs


# ----------------------------------------------------------------------
# ledger
# ----------------------------------------------------------------------
def test_ledger_persists_and_reloads(small_spec, ledger_path):
    p = FakePolaris()
    seed(p, FakeIceberg(p), small_spec, ledger_path)
    assert Ledger(ledger_path).done_users == {1, 2, 3}
    assert Ledger(ledger_path).spec().n_users == 3


def test_corrupt_ledger_raises_rather_than_looking_empty(ledger_path):
    Path(ledger_path).write_text("{not json", encoding="utf-8")
    with pytest.raises(RuntimeError, match="could not be read"):
        Ledger(ledger_path)


def test_ledger_write_is_atomic(small_spec, ledger_path):
    p = FakePolaris()
    seed(p, FakeIceberg(p), small_spec, ledger_path)
    assert not Path(ledger_path + ".tmp").exists()
    json.loads(Path(ledger_path).read_text(encoding="utf-8"))


# ----------------------------------------------------------------------
# teardown
# ----------------------------------------------------------------------
def test_teardown_removes_everything_and_clears_the_ledger(small_spec, ledger_path):
    p = FakePolaris()
    seed(p, FakeIceberg(p), small_spec, ledger_path)
    res = teardown(p, ledger_path)

    assert res.completed_users == 3
    assert p.principals == set() and p.principal_roles == set()
    assert p.catalogs == set() and p.catalog_roles == set() and p.grants == set()
    assert not Path(ledger_path).exists()


def test_teardown_is_idempotent(small_spec, ledger_path):
    p = FakePolaris()
    seed(p, FakeIceberg(p), small_spec, ledger_path)
    teardown(p, ledger_path, keep_ledger=True)
    res = teardown(p, ledger_path, spec=small_spec)
    assert not res.failed_users, "404s on a second teardown must be tolerated"


def test_teardown_only_touches_ledger_recorded_entities(small_spec, ledger_path):
    """A name sweep would also delete this bystander; the ledger must not."""
    p = FakePolaris()
    seed(p, FakeIceberg(p), small_spec, ledger_path)
    p.principals.add("user999_principal")  # same prefix, not in the ledger
    p.catalogs.add("user999_catalog")

    teardown(p, ledger_path)
    assert p.principals == {"user999_principal"}
    assert p.catalogs == {"user999_catalog"}


# ----------------------------------------------------------------------
# verification / strays
# ----------------------------------------------------------------------
def test_verify_counts_passes_when_rows_match():
    spec = SeedSpec(n_users=10, namespaces_per_catalog=2, tables_per_namespace=5)
    exp = spec.expected_counts()
    v = verify_counts(FakePg(exp["entities_total"], exp["grant_records"]), spec)
    assert v["entities_ok"] and v["grants_ok"]
    assert "audit-ready" in v["notes"][0]


def test_verify_counts_flags_an_incomplete_seed():
    spec = SeedSpec(n_users=1000)
    v = verify_counts(FakePg(100, 50), spec)
    assert not v["entities_ok"] and not v["grants_ok"]
    assert any("did not complete" in n for n in v["notes"])
    assert any("invalid_privileges" in n for n in v["notes"])


def test_find_strays_reports_without_deleting(small_spec, ledger_path):
    p = FakePolaris()
    seed(p, FakeIceberg(p), small_spec, ledger_path)
    strays = find_strays(p, prefix="user")
    assert len(strays["principals"]) == 3
    assert len(p.principals) == 3, "find_strays must be read-only"


def test_seed_result_summary_is_readable():
    r = SeedResult(completed_users=5, skipped_users=1, elapsed_s=2.5, calls=100)
    s = r.summary()
    assert "seeded=5" in s and "skipped=1" in s and "calls=100" in s
