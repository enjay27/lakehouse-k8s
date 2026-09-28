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

from polaris_seed import COARSE_CATALOG_PRIVILEGES  # noqa: E402
from polaris_seed import (
    CATALOG_PRIVILEGES,
    CORE_CATALOG_PRIVILEGES,
    FULL_CATALOG_PRIVILEGES,
    OWNER_ROLE_NAME,
    Ledger,
    SeedResult,
    SeedSpec,
    catalog_privileges,
    delete_catalog_fully,
    empty_catalog,
    find_strays,
    ledger_shortfall,
    require_local,
    revert_grants,
)
from polaris_seed import seed as _seed  # noqa: E402
from polaris_seed import (
    teardown,
    upgrade_grants,
    verify_counts,
)

#: Storage config for the fake cluster. `seed()` requires a bucket and a MinIO
#: endpoint even when `create_tables` is False, because every catalog carries a
#: storage config regardless -- see the guard at the top of `seed()`. The fakes
#: never dereference these, so any well-formed values do.
FAKE_BUCKET = "test-bucket"
FAKE_MINIO_ENDPOINT = "http://minio.local:9000"


def seed(pc, ic, spec=None, ledger_path="seed_ledger.json", **kw):
    """Call the real `seed()` with this suite's fake storage config.

    A thin shim, not a reimplementation: it defaults `bucket` and
    `minio_endpoint` and forwards everything else untouched, so a test can
    still override either one, and any argument the real `seed()` grows in
    future passes straight through.

    It exists because the storage config is uninteresting to all but one of
    these tests, and threading two identical literals through eighteen call
    sites would bury what each test is actually asserting.
    """
    kw.setdefault("bucket", FAKE_BUCKET)
    kw.setdefault("minio_endpoint", FAKE_MINIO_ENDPOINT)
    return _seed(pc, ic, spec, ledger_path, **kw)


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

    def __init__(
        self,
        base_url="http://localhost:8181",
        reject_privs=(),
        fail_on=None,
        half_create=(),
        unreadable_roles=(),
    ):
        self.base_url = base_url
        self.principals, self.principal_roles, self.catalogs = set(), set(), set()
        self.catalog_roles, self.grants = set(), set()
        #: Namespaces and tables live HERE, not on the Iceberg fake, so
        #: `delete_catalog` can refuse a non-empty catalog the way Polaris does.
        self.namespaces, self.tables = set(), set()
        self.assignments = []
        self.reject_privs = set(reject_privs)
        self.fail_on = fail_on or {}
        #: Every call, in order, so a test can assert HOW something was done --
        #: one GET per role rather than one per privilege is the whole point of
        #: `upgrade_grants`, and only a call log can show it.
        self.log = []
        #: (catalog, role) pairs whose `list_grants` 403s, so the "could not
        #: read the role" branch can be exercised. That branch matters: reading
        #: a failure as "holds nothing" would issue 50 duplicate writes per
        #: role, each paying the measured ~5 s duplicate-key retry.
        self.unreadable_roles = set(unreadable_roles)
        #: Catalog names whose `catalog_admin` bootstrap is skipped on the FIRST
        #: create, reproducing the non-atomic catalog creation seen live (25 of
        #: 1,000 under load): the entity commits, its admin role does not. The
        #: recreate then succeeds, so `_ensure_catalog` can actually repair it.
        self.half_create = set(half_create)

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
        # Real Polaris bootstraps `catalog_admin` as part of catalog creation.
        # It is a SECOND write, and under load it can fail to commit while the
        # entity write succeeds -- which is exactly what `half_create` models.
        if name in self.half_create:
            self.half_create.discard(name)  # only the first attempt is broken
        else:
            self.catalog_roles.add((name, "catalog_admin"))
        return Resp(200)

    def get_catalog(self, name):
        if name not in self.catalogs:
            return Resp(404)
        return Resp(200, {"name": name})

    def list_catalog_roles(self, catalog):
        if catalog not in self.catalogs:
            return Resp(404)
        roles = sorted(n for (c, n) in self.catalog_roles if c == catalog)
        if "catalog_admin" not in roles:
            # The live signature of a half-created catalog: the entity answers
            # GET 200, but the caller holds no grant on it, so this 403s.
            return Resp(403, {"error": "not authorized"})
        return Resp(200, {"roles": [{"name": n} for n in roles]})

    def create_catalog_role(self, catalog, name):
        if catalog not in self.catalogs:
            return Resp(404)
        key = (catalog, name)
        if key in self.catalog_roles:
            return Resp(409)
        self.catalog_roles.add(key)
        return Resp(200)

    def delete_catalog_role(self, catalog, name):
        key = (catalog, name)
        if key not in self.catalog_roles:
            return Resp(404)
        self.catalog_roles.discard(key)
        self.grants = {g for g in self.grants if g[:2] != key}
        return Resp(204)

    def assign_catalog_role_to_principal_role(self, catalog, prole, crole):
        self.assignments.append(("cr->pr", catalog, crole, prole))
        return Resp(200)

    def grant_privilege(self, catalog, crole, priv, skip_if_present=True, **kw):
        # `skip_if_present` is accepted and ignored: the real client's flag
        # controls a GET-before-PUT optimisation, not the outcome. What the
        # tests care about is that `upgrade_grants` passes False -- asserted
        # via `self.log`, not by making the fake behave differently.
        self.log.append(("grant", catalog, crole, priv, skip_if_present))
        if priv in self.reject_privs:
            return Resp(400, {"error": f"unknown privilege {priv}"})
        self.grants.add((catalog, crole, priv))
        return Resp(200)

    def list_grants(self, catalog, crole):
        self.log.append(("list_grants", catalog, crole))
        if (catalog, crole) in self.unreadable_roles:
            return Resp(403, {"error": "not authorized"})
        held = sorted(p for (c, r, p) in self.grants if c == catalog and r == crole)
        return Resp(
            200, {"grants": [{"type": "catalog", "privilege": p} for p in held]}
        )

    def revoke_privilege(self, catalog, crole, priv, cascade=False, **kw):
        self.log.append(("revoke", catalog, crole, priv, cascade))
        key = (catalog, crole, priv)
        if key not in self.grants:
            return Resp(404, {"error": "grant not found"})
        self.grants.discard(key)
        return Resp(200)

    def calls_of(self, kind):
        return [e for e in self.log if e[0] == kind]

    def list_namespaces(self, catalog, parent=None):
        if catalog not in self.catalogs:
            return Resp(404)
        # `empty_catalog` passes the namespace back as a LIST (that is what
        # the response carries), so normalise both forms — wrapping a list in a
        # tuple silently matched nothing and hid a nested namespace.
        if parent is None:
            want = ()
        elif isinstance(parent, (list, tuple)):
            want = tuple(parent)
        else:
            want = (parent,)
        out = [ns for (c, ns) in self.namespaces if c == catalog and ns[:-1] == want]
        return Resp(200, {"namespaces": [list(ns) for ns in out]})

    def delete_namespace(self, catalog, ns):
        key = (catalog, tuple(ns) if isinstance(ns, (list, tuple)) else (ns,))
        if key not in self.namespaces:
            return Resp(404)
        if [t for t in self.tables if t[:2] == key]:
            return Resp(400, {"error": "Namespace is not empty"})
        self.namespaces.discard(key)
        return Resp(204)

    def list_tables(self, catalog, ns):
        key = (catalog, tuple(ns) if isinstance(ns, (list, tuple)) else (ns,))
        names = sorted(t[2] for t in self.tables if t[:2] == key and t[3] == "table")
        return Resp(200, {"identifiers": [{"name": n} for n in names]})

    def list_views(self, catalog, ns):
        key = (catalog, tuple(ns) if isinstance(ns, (list, tuple)) else (ns,))
        names = sorted(t[2] for t in self.tables if t[:2] == key and t[3] == "view")
        return Resp(200, {"identifiers": [{"name": n} for n in names]})

    def delete_table(self, catalog, ns, name, purge=False):
        key = (
            catalog,
            tuple(ns) if isinstance(ns, (list, tuple)) else (ns,),
            name,
            "table",
        )
        if key not in self.tables:
            return Resp(404)
        self.tables.discard(key)
        return Resp(204)

    def delete_view(self, catalog, ns, name, purge=False):
        key = (
            catalog,
            tuple(ns) if isinstance(ns, (list, tuple)) else (ns,),
            name,
            "view",
        )
        if key not in self.tables:
            return Resp(404)
        self.tables.discard(key)
        return Resp(204)

    def delete_catalog(self, name, purge=False):
        if name not in self.catalogs:
            return Resp(404)
        # The measured refusal. purgeRequested=true does NOT cascade — it was
        # set on both live calls that produced this 400.
        children = [k for k in self.namespaces if k[0] == name] + [
            r for r in self.catalog_roles if r[0] == name and r[1] != "catalog_admin"
        ]
        if children:
            return Resp(
                400,
                {
                    "error": {
                        "message": f"Catalog '{name}' cannot be dropped, it is "
                        "not empty",
                        "type": "BadRequestException",
                        "code": 400,
                    }
                },
            )
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
    """Writes into the Polaris fake's state, so a catalog delete can see it."""

    def __init__(self, polaris):
        self.p = polaris

    @property
    def namespaces(self):
        return self.p.namespaces

    @property
    def tables(self):
        return self.p.tables

    def create_namespace(self, catalog, ns, **kw):
        key = (catalog, (ns,) if isinstance(ns, str) else tuple(ns))
        if key in self.p.namespaces:
            return Resp(409)
        self.p.namespaces.add(key)
        return Resp(200)

    def create_table(self, catalog, ns, payload, **kw):
        key = (
            catalog,
            (ns,) if isinstance(ns, str) else tuple(ns),
            payload["name"],
            "table",
        )
        if key in self.p.tables:
            return Resp(409)
        self.p.tables.add(key)
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


def test_remote_guard_beats_argument_validation(small_spec, ledger_path):
    """A remote host is reported as such even when the call is ALSO malformed.

    Both checks raise before any work, so ordering cannot change what gets
    written -- but it decides which mistake the caller hears about, and the
    wrong host is the more dangerous one. When the argument check ran first,
    this call raised ValueError about the missing bucket and said nothing about
    pointing at a company cluster.
    """
    p = FakePolaris(base_url="http://polaris.prod.company:8181")
    with pytest.raises(AssertionError):
        _seed(p, FakeIceberg(p), small_spec, ledger_path)  # no storage config


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
    # entities is projected in two parts for the same reason grant_records is:
    # Polaris bootstraps a `catalog_admin` role with every catalog, so there are
    # TWO catalog-roles per catalog, not one. Pinned against the measured census
    # of the metadata-only fixture — ROOT 2, PRINCIPAL 1002, PRINCIPAL_ROLE 1002,
    # CATALOG 1000, CATALOG_ROLE 2000, NAMESPACE 2000 = 7,006.
    assert exp["entities_seeded"] == 1000 * 4 + 2000 + 10000
    assert exp["entities_bootstrap"] == 1000 + 3
    # grant_records is now projected in two parts, because it is two things:
    # what the seeder grants, and what Polaris writes on its own (the role
    # assignments and the catalog_admin bootstrap). The observed constant is
    # pinned here against the measured fixture -- 25,000 granted + 5,009
    # Polaris-written = the 30,009 counted on the live cluster.
    assert exp["grant_records_granted"] == 1000 * len(CORE_CATALOG_PRIVILEGES)
    assert exp["grant_records_overhead"] == 1000 * 5 + 2


def test_the_2026_07_census_still_reproduces_under_its_own_bootstrap():
    """7,006 entities and 30,009 grant_records were REAL, counted on the live
    cluster in July. They are not wrong -- they are conditional on a realm
    bootstrapped by Polaris's admin tool, which wrote 6 realm entities and 9
    realm grants. That realm was dropped on 2026-08-21 and replaced by a
    hand-written bootstrap writing 3 and 2.

    Pinning the census against its own constants keeps the measurement instead
    of deleting it, and makes the dependency explicit: if these two lines ever
    have to change, the census was never about the bootstrap at all."""
    july = SeedSpec(
        create_tables=False, entity_overhead_realm=6, grant_overhead_realm=9
    )
    assert july.expected_counts()["entities_total"] == 7006
    assert july.expected_counts()["grant_records"] == 30009


def test_coarse_privileges_produce_far_fewer_grant_rows():
    """Compared on the GRANTED part, not the total.

    The total also carries the rows Polaris writes itself (role assignments,
    the catalog_admin bootstrap), and those do not shrink when the privilege
    list does — with 1,000 users they are 5,009 rows either way, enough to
    swamp the ratio this test is about.
    """
    full = SeedSpec().expected_counts()["grant_records_granted"]
    coarse = SeedSpec(privileges=list(COARSE_CATALOG_PRIVILEGES)).expected_counts()[
        "grant_records_granted"
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
    # Each catalog carries exactly the role the seeder makes plus the
    # `catalog_admin` Polaris bootstraps itself. This once asserted that every
    # role was the owner role, which only held because the fake did not model
    # the bootstrap at all.
    assert p.catalog_roles == {
        (f"user{i}_catalog", name)
        for i in (1, 2, 3)
        for name in (OWNER_ROLE_NAME, "catalog_admin")
    }
    assert len(ic.namespaces) == 6
    assert len(ic.tables) == 12
    assert len(p.grants) == 3 * len(FULL_CATALOG_PRIVILEGES)


def test_half_created_catalog_is_detected_and_rebuilt(small_spec, ledger_path):
    """`_ensure_catalog`'s reason for existing, exercised end to end.

    A catalog whose entity committed but whose `catalog_admin` bootstrap did
    not answers GET 200 while `list_catalog_roles` 403s. Checking existence --
    what this module did before -- records it as a success, and it is then
    permanently unusable: nothing can be created inside it and no retry helps.
    The only remedy is delete and recreate, which is what should happen here.
    """
    p = FakePolaris(half_create={"user2_catalog"})
    res = seed(p, FakeIceberg(p), small_spec, ledger_path)

    assert res.completed_users == 3
    assert not res.failed_users
    assert res.repaired_catalogs == ["user2_catalog"]
    # Repaired means usable, not merely present.
    assert ("user2_catalog", "catalog_admin") in p.catalog_roles
    assert ("user2_catalog", OWNER_ROLE_NAME) in p.catalog_roles


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
# ledger_shortfall -- the seed path's version of "a changed target
# invalidates the record". A resumed seed skips finished users, so a ledger
# written at 25 grants silently under-delivers a 50-grant run.
# ----------------------------------------------------------------------
def test_shortfall_absent_ledger_is_safe(tmp_path):
    assert ledger_shortfall(str(tmp_path / "nope.json"), 50) is None


def test_shortfall_empty_ledger_is_safe(ledger_path):
    Ledger(ledger_path).set_spec(SeedSpec(n_users=3))
    assert ledger_shortfall(ledger_path, 50) is None


def test_shortfall_detects_a_ledger_that_cannot_deliver(small_spec, ledger_path):
    p = FakePolaris()
    seed(p, FakeIceberg(p), small_spec, ledger_path)  # 3 users at 25 grants

    n_short, recorded, n_done = ledger_shortfall(ledger_path, 50)
    assert (n_short, recorded, n_done) == (3, len(CORE_CATALOG_PRIVILEGES), 3)


def test_shortfall_is_none_when_the_ledger_already_meets_the_target(tmp_path):
    lp = str(tmp_path / "fifty.json")
    spec = SeedSpec(n_users=3, create_tables=False, privileges=catalog_privileges(50))
    p = FakePolaris()
    seed(p, FakeIceberg(p), spec, lp)

    assert ledger_shortfall(lp, 50) is None
    # A LARGER recorded set is fine too -- the run asks for less than it has.
    assert ledger_shortfall(lp, 25) is None


def test_shortfall_counts_a_completed_upgrade(small_spec, ledger_path):
    """An upgraded user holds the target however few grants the seed wrote.

    Refusing a fixture that `upgrade_grants` has already raised is the failure
    mode that gets a guard deleted, so it is pinned here.
    """
    p = FakePolaris()
    seed(p, FakeIceberg(p), small_spec, ledger_path)
    assert ledger_shortfall(ledger_path, 50) is not None

    upgrade_grants(p, small_spec, grants_per_role=50, ledger_path=ledger_path)
    assert ledger_shortfall(ledger_path, 50) is None

    # ...but only for THAT target. A 50-grant upgrade does not cover 51.
    assert ledger_shortfall(ledger_path, 51) is not None


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
    assert v["grant_residual"] == 0
    assert any("grant_records exact" in n for n in v["notes"])


def test_verify_counts_names_an_unexplained_surplus_instead_of_absorbing_it():
    """The `>=` bug, pinned.

    This printed "Row counts match the spec" for 30,009 actual against a
    25,000 projection: 5,009 unexplained rows in the table under audit,
    reported as agreement. A surplus must now be named and quantified.
    """
    spec = SeedSpec(n_users=10, namespaces_per_catalog=2, tables_per_namespace=5)
    exp = spec.expected_counts()
    v = verify_counts(FakePg(exp["entities_total"], exp["grant_records"] + 40), spec)
    assert v["grants_ok"], "a surplus is not a shortfall"
    assert v["grant_residual"] == 40
    assert any("UNEXPLAINED" in n for n in v["notes"])
    assert not any("exact" in n for n in v["notes"])


def test_verify_counts_accounts_for_task_rows_rather_than_ignoring_them():
    """The entity surplus has a known name, and must still be named.

    Every drop-with-purge leaves a TASK row in `entities` (measured: 279, none
    soft-deleted, none ever attempted). So a surplus is expected — but reporting
    it as "fine" would hide anything ELSE that started accumulating, which would
    look identical from the count alone.
    """
    spec = SeedSpec(n_users=10, create_tables=False)
    exp = spec.expected_counts()
    v = verify_counts(FakePg(exp["entities_total"] + 12, exp["grant_records"]), spec)
    assert v["entities_ok"]
    assert v["entity_residual"] == 12
    assert any("TASK rows" in n for n in v["notes"])


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


# ----------------------------------------------------------------------
# grant volume — upgrading an existing fixture to production shape
# ----------------------------------------------------------------------
@pytest.fixture
def no_sleep(monkeypatch):
    """Collapse `_attempt`'s backoff. Its ~8 s ladder is correct against a
    lagging replica and pointless against an in-memory fake."""
    monkeypatch.setattr("polaris_seed.time.sleep", lambda *_: None)


@pytest.fixture
def seeded(small_spec, ledger_path):
    """A 3-user fixture at the 25-grant baseline — the state to upgrade FROM."""
    p = FakePolaris()
    seed(p, FakeIceberg(p), small_spec, ledger_path)
    p.log.clear()  # the seed's own calls are not what these tests measure
    return p


def test_the_first_25_catalog_privileges_are_exactly_the_core_set():
    """What makes 25 -> 50 additive rather than a rewrite.

    `catalog_privileges(n)` slices the spec-ordered enum, so every larger n is
    a superset of every smaller one. If the order in `CATALOG_PRIVILEGES` is
    ever reshuffled, this fails — and it should, because an upgrade that no
    longer contains what the roles already hold would leave the fixture
    holding some grants it was never asked for and missing some it was.
    """
    assert set(CATALOG_PRIVILEGES[:25]) == set(CORE_CATALOG_PRIVILEGES)
    assert set(catalog_privileges(25)) <= set(catalog_privileges(50))
    assert len(CATALOG_PRIVILEGES) == len(set(CATALOG_PRIVILEGES)), "no duplicates"


def test_catalog_privileges_refuses_more_than_the_enum_supplies():
    """Better than silently returning a short list and a thin fixture."""
    with pytest.raises(ValueError, match="1.3.0 enum"):
        catalog_privileges(len(CATALOG_PRIVILEGES) + 1)


def test_upgrade_issues_one_get_per_role_and_puts_only_what_is_missing(
    seeded, small_spec, ledger_path
):
    """The optimisation, asserted as behaviour rather than as intent.

    The naive pass costs one GET per privilege (25,000 across the real
    fixture), none of which can hit, because the grants are new. Turning
    `skip_if_present` off wholesale removes that cost and idempotence with it.
    Diffing once per role gets both.
    """
    res = upgrade_grants(
        seeded, small_spec, grants_per_role=30, ledger_path=ledger_path
    )

    assert len(seeded.calls_of("list_grants")) == 3, "one GET per ROLE"
    puts = seeded.calls_of("grant")
    assert len(puts) == 15, "5 missing privileges x 3 roles, and nothing else"
    assert all(e[4] is False for e in puts), (
        "the diff already established absence, so skip_if_present must be off "
        "— leaving it on pays a GET per privilege for a lookup that cannot hit"
    )
    assert res.grants_added == 15
    assert res.completed_users == 3
    for i in (1, 2, 3):
        held = {p for (c, r, p) in seeded.grants if c == f"user{i}_catalog"}
        assert held == set(catalog_privileges(30))


def test_upgrade_is_idempotent_and_writes_nothing_on_a_second_pass(
    seeded, small_spec, ledger_path, tmp_path
):
    upgrade_grants(seeded, small_spec, grants_per_role=30, ledger_path=ledger_path)
    seeded.log.clear()

    # Same ledger: skipped without even reading the roles.
    again = upgrade_grants(
        seeded, small_spec, grants_per_role=30, ledger_path=ledger_path
    )
    assert again.skipped_users == 3
    assert not seeded.calls_of("grant")
    assert not seeded.calls_of("list_grants")

    # Fresh ledger: it must re-read, and still write nothing.
    fresh = upgrade_grants(
        seeded, small_spec, grants_per_role=30, ledger_path=str(tmp_path / "new.json")
    )
    assert len(seeded.calls_of("list_grants")) == 3
    assert not seeded.calls_of("grant")
    assert fresh.grants_added == 0


def test_a_changed_target_invalidates_the_recorded_upgrade(
    seeded, small_spec, ledger_path
):
    """Resuming a 35-grant pass from a 30-grant ledger must not skip.

    Those users are done for 30 and five short of 35. Skipping them would
    leave every role under target, and a fixture that is quietly 15 rows light
    reads as a Polaris behaviour rather than a resume bug.
    """
    upgrade_grants(seeded, small_spec, grants_per_role=30, ledger_path=ledger_path)
    seeded.log.clear()

    res = upgrade_grants(
        seeded, small_spec, grants_per_role=35, ledger_path=ledger_path
    )
    assert res.skipped_users == 0
    assert len(seeded.calls_of("list_grants")) == 3
    assert res.grants_added == 15


def test_upgrade_records_a_rejected_privilege_name_and_keeps_going(
    seeded, small_spec, ledger_path
):
    """A name this build does not have is data, not a fault.

    It is also the reason the pass must shout: fewer rows than projected in
    the table under audit is exactly the shape of a false finding.
    """
    seeded.reject_privs = {CATALOG_PRIVILEGES[26]}
    res = upgrade_grants(
        seeded, small_spec, grants_per_role=30, ledger_path=ledger_path
    )
    assert set(res.invalid_privileges) == {CATALOG_PRIVILEGES[26]}
    assert res.completed_users == 3, "one bad name must not abort the pass"
    assert res.grants_added == 12, "4 written per role, not 5"


def test_upgrade_does_not_mark_a_role_done_when_a_write_never_landed(
    seeded, small_spec, ledger_path, no_sleep
):
    """The distinction that keeps the pass resumable.

    `_attempt` returns immediately on a 4xx that is not 403/404 (a bad name)
    and only exhausts its retries on 5xx/403/404 (lag). The first is data; the
    second is a hole in the fixture. Recording both as "invalid privilege" and
    marking the role done would leave that hole permanently, since a re-run
    skips what the ledger calls finished.
    """
    seeded.fail_on = {}
    doomed = CATALOG_PRIVILEGES[27]
    original = seeded.grant_privilege

    def flaky(catalog, crole, priv, skip_if_present=True, **kw):
        if priv == doomed:
            seeded.log.append(("grant", catalog, crole, priv, skip_if_present))
            return Resp(503, {"error": "replica lag"})
        return original(catalog, crole, priv, skip_if_present, **kw)

    seeded.grant_privilege = flaky
    res = upgrade_grants(
        seeded, small_spec, grants_per_role=30, ledger_path=ledger_path
    )

    assert res.completed_users == 0
    assert len(res.failed_users) == 3
    assert not res.invalid_privileges, "a 503 is lag, not a bad name"
    assert Ledger(ledger_path).upgraded_users(30) == set(), "must be retried"


def test_upgrade_skips_a_role_it_cannot_read_rather_than_granting_blind(
    seeded, small_spec, ledger_path
):
    """ "Could not read" must never be read as "holds nothing".

    Granting the full target to a role that already has most of it means ~50
    duplicate writes, each paying the measured ~5 s duplicate-key retry, on a
    role whose state is unknown.
    """
    seeded.unreadable_roles = {("user2_catalog", OWNER_ROLE_NAME)}
    res = upgrade_grants(
        seeded, small_spec, grants_per_role=30, ledger_path=ledger_path
    )
    assert [f["index"] for f in res.failed_users] == [2]
    assert not [e for e in seeded.calls_of("grant") if e[1] == "user2_catalog"]
    assert res.grants_added == 10, "the other two roles still upgraded"


def test_upgrade_refuses_a_remote_host_before_validating_its_arguments(small_spec):
    """Same ordering as `seed()`: both raise, but the host is the dangerous
    mistake and must be the one reported."""
    remote = FakePolaris(base_url="http://polaris.company.com:8181")
    with pytest.raises(AssertionError, match="refuses to run against host"):
        upgrade_grants(remote, small_spec, grants_per_role=9999)


def test_upgrade_refuses_to_reduce():
    """It is additive by construction; asking it to shrink is a caller error,
    not a silent no-op."""
    p = FakePolaris()
    with pytest.raises(ValueError, match="additive"):
        upgrade_grants(p, SeedSpec(n_users=1), grants_per_role=10)


def test_revert_removes_only_what_is_above_the_baseline(
    seeded, small_spec, ledger_path
):
    upgrade_grants(seeded, small_spec, grants_per_role=30, ledger_path=ledger_path)
    seeded.log.clear()

    res = revert_grants(seeded, small_spec, ledger_path=ledger_path)

    assert res.grants_revoked == 15
    for i in (1, 2, 3):
        held = {p for (c, r, p) in seeded.grants if c == f"user{i}_catalog"}
        assert held == set(CORE_CATALOG_PRIVILEGES)
    # catalog_admin's own bootstrap grants are never touched.
    assert not [e for e in seeded.calls_of("revoke") if e[2] == "catalog_admin"]


def test_revert_clears_the_upgrade_record(seeded, small_spec, ledger_path):
    """Otherwise a later upgrade skips every role as done, against a cluster
    that was just reverted."""
    upgrade_grants(seeded, small_spec, grants_per_role=30, ledger_path=ledger_path)
    assert Ledger(ledger_path).upgraded_users(30) == {1, 2, 3}

    revert_grants(seeded, small_spec, ledger_path=ledger_path)
    assert Ledger(ledger_path).upgraded_users(30) == set()

    res = upgrade_grants(
        seeded, small_spec, grants_per_role=30, ledger_path=ledger_path
    )
    assert res.grants_added == 15, "the revert must be re-doable"


def test_ledger_spec_survives_an_unknown_key(ledger_path):
    """Forward compatibility, in the one place it is unaffordable.

    A ledger written after `SeedSpec` grows a field, read by code that
    predates it, used to raise `TypeError` inside `teardown()` — the moment
    when the ledger is the only record of what needs deleting.
    """
    with open(ledger_path, "w", encoding="utf-8") as fh:
        json.dump({"spec": {"n_users": 4, "invented_later": True}, "users": [1]}, fh)
    spec = Ledger(ledger_path).spec()
    assert spec.n_users == 4


def test_delete_catalog_fully_clears_blocking_roles_first(small_spec, ledger_path):
    """The probe teardown bug, pinned.

    A bare `delete_catalog(purge=True)` on a catalog carrying a non-default
    catalog-role came back 400 live, stranding the catalog, its role and 51
    grant_records rows. `catalog_admin` must survive the sweep — deleting it is
    what produces the unusable, unrepairable catalog `_ensure_catalog` exists to
    repair.
    """
    p = FakePolaris()
    p.catalogs.add("probe_cat")
    p.catalog_roles.update(
        {("probe_cat", "catalog_admin"), ("probe_cat", "probe_role")}
    )
    p.grants.add(("probe_cat", "probe_role", "TABLE_DROP"))

    ok, resp = delete_catalog_fully(p, "probe_cat", SeedResult())

    assert ok and resp.status_code < 300
    assert "probe_cat" not in p.catalogs
    assert not [r for r in p.catalog_roles if r[0] == "probe_cat"]
    assert not [g for g in p.grants if g[0] == "probe_cat"]


def test_delete_catalog_fully_is_idempotent_on_an_absent_catalog():
    ok, _ = delete_catalog_fully(FakePolaris(), "never_existed", SeedResult())
    assert ok, "already gone is the desired end state, not a failure"


def test_delete_catalog_fully_returns_the_failing_response(small_spec):
    """The actual defect was throwing the body away.

    The first version printed a bare status code, so the reason the delete was
    refused went unrecorded and the same failure had to be provoked again to
    learn anything. Whatever refuses, the caller gets the response.
    """
    p = FakePolaris()
    p.catalogs.add("stuck")
    p.catalog_roles.add(("stuck", "catalog_admin"))
    p.delete_catalog = lambda name, purge=False: Resp(400, {"error": "why it refused"})

    ok, resp = delete_catalog_fully(p, "stuck", SeedResult())
    assert not ok
    assert resp.status_code == 400
    assert "why it refused" in resp.text


def test_teardown_drops_a_catalog_that_holds_namespaces(small_spec, ledger_path):
    """The bug the live 400 exposed.

    `teardown_user` used a bare `delete_catalog(purge=True)` from the day it was
    written. Every seeded catalog holds ns1 and ns2, and Polaris refuses:
    "Catalog 'x' cannot be dropped, it is not empty" — purgeRequested does not
    cascade. It went unnoticed because `_ensure_catalog`'s repair path only ever
    deletes half-created catalogs, which have no children yet.
    """
    p = FakePolaris()
    ic = FakeIceberg(p)
    seed(p, ic, small_spec, ledger_path)
    assert p.namespaces and p.tables, "the fixture must actually hold children"

    res = teardown(p, ledger_path=ledger_path, spec=small_spec)

    assert not res.failed_users, f"teardown refused: {res.failed_users}"
    assert not p.catalogs
    assert not p.namespaces and not p.tables


def test_empty_catalog_removes_children_deepest_first():
    """Namespaces cannot be dropped while they hold tables, and nested
    namespaces cannot be dropped before their children — so the order is
    forced, not a preference."""
    p = FakePolaris()
    p.catalogs.add("c")
    p.catalog_roles.add(("c", "catalog_admin"))
    p.namespaces.update({("c", ("a",)), ("c", ("a", "b"))})
    p.tables.update({("c", ("a", "b"), "t1", "table"), ("c", ("a",), "v1", "view")})

    ok, removed = empty_catalog(p, "c", SeedResult())

    assert ok, removed
    assert removed == {
        "tables": 1,
        "views": 1,
        "namespaces": 2,
        "catalog_roles": 0,
    }
    assert not p.namespaces and not p.tables
    assert ("c", "catalog_admin") in p.catalog_roles, "never delete catalog_admin"


def test_delete_catalog_fully_reports_the_real_refusal():
    """Two teardowns discarded this body before it was ever read, and a wrong
    cause got asserted in the meantime. The response comes back now."""
    p = FakePolaris()
    p.catalogs.add("c")
    p.namespaces.add(("c", ("stuck",)))
    p.delete_namespace = lambda catalog, ns: Resp(403, {"error": "nope"})

    ok, resp = delete_catalog_fully(p, "c", SeedResult())
    assert not ok
    assert resp.status_code == 403
    assert "c" in p.catalogs, "the catalog must survive a failed empty pass"


def test_tables_are_dropped_without_purge_by_default():
    """`DROP_TABLE_WITH_PURGE` is a distinct op that root does NOT bypass —
    measured 2026-07-06 in purge/table_purge_privilege_test.ipynb, and hit again
    live on 2026-08-21 when this teardown sent purgeRequested=true:

        "Principal 'root' ... is not authorized for op DROP_TABLE_WITH_PURGE"

    Purge buys nothing here anyway — on this build it does not delete MinIO
    files (#379) — and the table entity goes either way.
    """
    p = FakePolaris()
    p.catalogs.add("c")
    p.catalog_roles.add(("c", "catalog_admin"))
    p.namespaces.add(("c", ("ns",)))
    p.tables.add(("c", ("ns",), "t", "table"))
    seen = []
    original = p.delete_table
    p.delete_table = lambda cat, ns, name, purge=False: (
        seen.append(purge) or original(cat, ns, name, purge)
    )

    ok, removed = empty_catalog(p, "c", SeedResult())
    assert ok and removed["tables"] == 1
    assert seen == [False], "purge must be opt-in, not the default"


def test_table_purge_can_be_opted_into():
    p = FakePolaris()
    p.catalogs.add("c")
    p.namespaces.add(("c", ("ns",)))
    p.tables.add(("c", ("ns",), "t", "table"))
    seen = []
    original = p.delete_table
    p.delete_table = lambda cat, ns, name, purge=False: (
        seen.append(purge) or original(cat, ns, name, purge)
    )
    empty_catalog(p, "c", SeedResult(), purge_tables=True)
    assert seen == [True]
