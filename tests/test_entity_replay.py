"""
Pytest suite for src/entity_replay.py — cloning a user-set in SQL.

No cluster required. The fake answers by inspecting the SQL, and models the two
things that actually bite: the primary key `(realm_id, id)`, and the unique
constraint `(realm_id, catalog_id, parent_id, type_code, name)`. A fake that
accepted anything would let a clone with a duplicate name pass here and fail on
the cluster, which is the wrong place to find out.

Run: pytest test_entity_replay.py
"""

import sys
from pathlib import Path

import pytest

import entity_replay as er  # noqa: E402

SCHEMA, REALM = "polaris_schema", "POLARIS"

#: Ids shaped like the real ones: snowflake-scale and scattered across the WHOLE
#: bigint range. `HIGH_REAL_ID` is the shape that broke the first design — 201
#: real entities were found living above the "reserved" 9e18 base, which made
#: `DELETE ... WHERE id >= BASE` a command that deleted real users.
CAT_ID = 7985247348701050877
PRINCIPAL_ID = 2490852191059560064
ROLE_ID = 77192520090151552
HIGH_REAL_ID = 9009225487382325435
SERVICE_ADMIN_ID = 2  # outside the user-set, and must stay that way


def _entity(eid, catalog_id, parent_id, type_code, name, **kw):
    row = {
        "id": eid,
        "catalog_id": catalog_id,
        "parent_id": parent_id,
        "type_code": type_code,
        "name": name,
        "entity_version": 1,
        "sub_type_code": 0,
        "create_timestamp": 1787214579791,
        "drop_timestamp": 0,
        "purge_timestamp": 0,
        "to_purge_timestamp": 0,
        "last_update_timestamp": 1787214579791,
        "properties": {},
        "internal_properties": {},
        "grant_records_version": 1,
        "location_without_scheme": None,
        "realm_id": REALM,
    }
    row.update(kw)
    return tuple(row[c] for c in er.ENTITY_COLUMNS)


def template_rows(catalog_self_id=0):
    """One complete user-set.

    `catalog_self_id` is what the CATALOG row carries in its own `catalog_id`
    column. The live cluster says it is NOT the catalog's own id -- an earlier
    version of this fake asserted that it was, so the suite confirmed the
    assumption and `read_template` silently returned a set with no catalog in
    it. Both shapes are exercised now; the code must not care.
    """
    cat = _entity(
        CAT_ID,
        catalog_self_id,
        0,
        er.TYPE_CATALOG,
        "user1_catalog",
        internal_properties={
            "default-base-location": "s3a://bkt/user1_catalog/",
            "catalogType": "INTERNAL",
        },
        location_without_scheme="bkt/user1_catalog",
    )
    return [
        _entity(PRINCIPAL_ID, 0, 0, er.TYPE_PRINCIPAL, "user1_principal"),
        _entity(ROLE_ID, 0, 0, er.TYPE_PRINCIPAL_ROLE, "user1_principal_role"),
        cat,
        _entity(CAT_ID + 1, CAT_ID, CAT_ID, 5, "catalog_admin"),
        _entity(CAT_ID + 2, CAT_ID, CAT_ID, 5, "owner_principal"),
        _entity(CAT_ID + 3, CAT_ID, CAT_ID, 6, "ns1"),
        _entity(CAT_ID + 4, CAT_ID, CAT_ID, 6, "ns2"),
    ]


def template_grants():
    return [
        (0, ROLE_ID, 0, PRINCIPAL_ID, 1, REALM),  # principal -> role
        (CAT_ID, CAT_ID + 2, 0, ROLE_ID, 1, REALM),  # role -> catalog-role
        (CAT_ID, CAT_ID, CAT_ID, CAT_ID + 1, 2, REALM),  # catalog_admin
        (CAT_ID, CAT_ID, 0, SERVICE_ADMIN_ID, 3, REALM),  # service_admin
        (CAT_ID, CAT_ID, CAT_ID, CAT_ID + 2, 7, REALM),  # owner_principal grant
    ]


class FakeCursor:
    def __init__(self, db):
        self.db = db
        self._result = None
        self.rowcount = -1

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        s = " ".join(sql.split())
        self.db.log.append(s)
        if "INSERT INTO polaris_schema.principal_authentication_data" in s:
            # insert_identities writes the credential row via cur.execute, not
            # execute_values. params is the 6-tuple in AUTH_COLUMNS order.
            self.db.auth.append(tuple(params))
            self.rowcount = 1
        elif s.startswith("DELETE FROM") and "principal_authentication_data" in s:
            ids = set(params[1])
            keep = [a for a in self.db.auth if a[1] not in ids]
            self.rowcount = len(self.db.auth) - len(keep)
            self.db.auth = keep
        elif "FROM polaris_schema.principal_authentication_data" in s:
            # read_identity_source: WHERE realm_id = %s AND principal_id = %s
            pid = params[1]
            self._result = [a for a in self.db.auth if a[1] == pid]
        elif s.startswith("DELETE FROM") and ".grant_records" in s:
            ids = set(params[1])
            keep = [g for g in self.db.grants if not (g[1] in ids or g[3] in ids)]
            self.rowcount = len(self.db.grants) - len(keep)
            self.db.grants = keep
        elif s.startswith("DELETE FROM") and ".entities" in s:
            ids = set(params[1])
            keep = [e for e in self.db.entities if e[0] not in ids]
            self.rowcount = len(self.db.entities) - len(keep)
            self.db.entities = keep
        elif "id >= %s AND id < %s" in s:  # the band emptiness check
            lo, hi = params[1], params[2]
            self._result = [(len([e for e in self.db.entities if lo <= e[0] < hi]),)]
        elif "count(*) FROM polaris_schema.entities" in s and "name LIKE" in s:
            # prefix-is-free check. NO id bound in this predicate, deliberately:
            # the earlier `AND id < CLONE_ID_SEARCH_START` excluded the exact
            # region where 201 real entities were found. If that bound ever
            # comes back, this branch stops matching and the suite says so.
            pre = params[1].rstrip("%")
            self._result = [
                (len([e for e in self.db.entities if str(e[4]).startswith(pre)]),)
            ]
        elif "SELECT id, type_code" in s:
            pre = params[1].rstrip("%")
            self._result = [
                (e[0], e[3]) for e in self.db.entities if str(e[4]).startswith(pre)
            ]
        elif "SELECT id FROM polaris_schema.entities" in s and "catalog_id = ANY" in s:
            cats = set(params[1])
            self._result = [(e[0],) for e in self.db.entities if e[1] in cats]
        elif "count(*) FROM polaris_schema.grant_records" in s:
            ids = set(params[1])
            self._result = [
                (len([g for g in self.db.grants if g[1] in ids or g[3] in ids]),)
            ]
        elif "FROM polaris_schema.entities" in s and "name = %s" in s:
            self._result = [
                e for e in self.db.entities if e[4] == params[1] and e[3] == params[2]
            ]
        elif "FROM polaris_schema.entities" in s:
            # (realm, catalog_id, catalog_id, names) — the query selects the
            # catalog by `id` as well as its children by `catalog_id`, because a
            # catalog's own catalog_id is not its own id.
            cat, names = params[1], params[3]
            self._result = [
                e
                for e in self.db.entities
                if e[0] == cat or e[1] == cat or e[4] in names
            ]
        elif "FROM polaris_schema.grant_records" in s:
            cat, ids = params[1], set(params[2])
            self._result = [
                g for g in self.db.grants if g[0] == cat or g[3] in ids or g[1] in ids
            ]
        else:  # pragma: no cover
            raise AssertionError(f"no branch for: {s[:110]}")

    def fetchone(self):
        return self._result[0] if self._result else None

    def fetchall(self):
        return list(self._result or [])


class FakeDB:
    """entities and grant_records, with the constraints Polaris actually has."""

    def __init__(self, entities=(), grants=(), auth=()):
        self.entities = list(entities)
        self.grants = list(grants)
        self.auth = list(auth)
        self.log = []

    def cursor(self):
        return FakeCursor(self)

    # `execute_values` is patched onto this in the fixture below.
    def insert_entities(self, rows):
        pk = {(e[16], e[0]) for e in self.entities}
        uniq = {(e[16], e[1], e[2], e[3], e[4]) for e in self.entities}
        added = 0
        for r in rows:
            r = tuple(getattr(v, "adapted", v) for v in r)
            if (r[16], r[0]) in pk:
                raise AssertionError(f"PRIMARY KEY collision on id {r[0]}")
            key = (r[16], r[1], r[2], r[3], r[4])
            if key in uniq:
                raise AssertionError(f"UNIQUE constraint collision on {key}")
            pk.add((r[16], r[0]))
            uniq.add(key)
            self.entities.append(r)
            added += 1
        return added

    def insert_grants(self, rows):
        for r in rows:
            self.grants.append(tuple(getattr(v, "adapted", v) for v in r))
        return len(rows)


#: The source principal's credential row: (realm, principal_id, client_id,
#: main_hash, secondary_hash, salt). secondary == main, as the bootstrap writes.
SOURCE_AUTH = (REALM, PRINCIPAL_ID, "user1-client", "HASH", "HASH", "SALT")


@pytest.fixture
def db(monkeypatch):
    d = FakeDB(template_rows(), template_grants(), [SOURCE_AUTH])

    class _Json:
        def __init__(self, v):
            self.adapted = v

    def _execute_values(cur, sql, rows, *a, **kw):
        n = (
            cur.db.insert_entities(rows)
            if ".entities" in sql
            else cur.db.insert_grants(rows)
        )
        cur.rowcount = n

    fake = type(sys)("psycopg2.extras")
    fake.execute_values = _execute_values
    fake.Json = _Json
    monkeypatch.setitem(sys.modules, "psycopg2", type(sys)("psycopg2"))
    monkeypatch.setitem(sys.modules, "psycopg2.extras", fake)
    return d


# ----------------------------------------------------------------------
# the id band — chosen against live data, never declared
# ----------------------------------------------------------------------
def test_band_search_skips_a_region_that_holds_real_rows(db):
    """The design this replaces hardcoded a base "above every live id" from
    three sampled ids. Polaris ids are scattered: 201 real entities were found
    above 9e18. A band is now searched for and proven empty."""
    db.entities.append(_entity(HIGH_REAL_ID, 0, 0, 2, "user975_principal"))
    base, width = er.find_clone_band(db, SCHEMA, REALM, 10)
    assert width == 10 * er.IDS_PER_CLONE
    assert not any(base <= e[0] < base + width for e in db.entities)


def test_band_search_gives_up_rather_than_overflowing(db):
    with pytest.raises((RuntimeError, ValueError)):
        er.find_clone_band(db, SCHEMA, REALM, 10**17)


def test_prefix_must_be_free_before_anything_is_written(db):
    """Deletion keys on the name prefix, so a real entity wearing it would be
    swept by --remove. That is the failure this module was one command from."""
    assert er.assert_prefix_is_free(db, SCHEMA, REALM)
    db.entities.append(_entity(12345, 0, 0, 2, "sqlclone_lookalike"))
    with pytest.raises(AssertionError, match="already carry"):
        er.assert_prefix_is_free(db, SCHEMA, REALM)


def test_prefix_guard_looks_above_the_search_start_too(db):
    """The guard once read `AND id < CLONE_ID_SEARCH_START`, which excluded the
    one region where the 201 real entities actually were. A high-id lookalike
    must still trip it."""
    db.entities.append(
        _entity(er.CLONE_ID_SEARCH_START + 77, 0, 0, 2, "sqlclone_lookalike")
    )
    with pytest.raises(AssertionError, match="already carry"):
        er.assert_prefix_is_free(db, SCHEMA, REALM)


# ----------------------------------------------------------------------
# the template
# ----------------------------------------------------------------------
def test_template_gathers_the_whole_user_set(db):
    t = er.read_template(db, SCHEMA, REALM, "user1")
    assert t["catalog_id"] == CAT_ID
    assert len(t["entities"]) == 7
    assert {e[4] for e in t["entities"]} == {
        "user1_principal",
        "user1_principal_role",
        "user1_catalog",
        "catalog_admin",
        "owner_principal",
        "ns1",
        "ns2",
    }
    assert len(t["grants"]) == 5


@pytest.mark.parametrize("catalog_self_id", [0, CAT_ID])
def test_template_finds_the_catalog_whatever_its_catalog_id_holds(catalog_self_id):
    """The live failure: `WHERE catalog_id = <cat id>` returned the catalog's
    CHILDREN and not the catalog, because a catalog's own catalog_id is not its
    own id. The fake had asserted the opposite, so the suite confirmed the
    assumption instead of testing it."""
    d = FakeDB(template_rows(catalog_self_id), template_grants())
    t = er.read_template(d, SCHEMA, REALM, "user1")
    assert len(t["entities"]) == 7
    assert er.TYPE_CATALOG in {e[3] for e in t["entities"]}


def test_template_refuses_an_incomplete_user(db):
    db.entities = [e for e in db.entities if e[3] != er.TYPE_PRINCIPAL]
    with pytest.raises(LookupError, match="no principal"):
        er.read_template(db, SCHEMA, REALM, "user1")


def test_template_refuses_a_missing_catalog(db):
    with pytest.raises(LookupError, match="no catalog named"):
        er.read_template(db, SCHEMA, REALM, "nope")


# ----------------------------------------------------------------------
# stamping
# ----------------------------------------------------------------------
BASE = 9_100_000_000_000_000_000


def test_clone_rewrites_only_what_must_change(db):
    t = er.read_template(db, SCHEMA, REALM, "user1")
    entities, _ = er.clone_rows(t, 0, REALM, BASE)
    by_name = {e[4]: e for e in entities}
    cat = by_name["sqlclone0_catalog"]
    src = [e for e in t["entities"] if e[4] == "user1_catalog"][0]
    for idx in (3, 5, 6, 7, 8, 9, 10, 11, 14):
        assert cat[idx] == src[idx], f"column {er.ENTITY_COLUMNS[idx]} was altered"
    assert "catalog_admin" in by_name and "ns1" in by_name


def test_clone_children_point_at_the_new_catalog(db):
    """Whatever a catalog's own catalog_id is, its CHILDREN carry the catalog's
    id — those must be remapped or the clone's namespaces still belong to the
    template."""
    t = er.read_template(db, SCHEMA, REALM, "user1")
    entities, _ = er.clone_rows(t, 0, REALM, BASE)
    by_name = {e[4]: e for e in entities}
    new_cat = by_name["sqlclone0_catalog"][0]
    for child in ("catalog_admin", "owner_principal", "ns1", "ns2"):
        assert by_name[child][1] == new_cat, f"{child} still points at user1"
        assert by_name[child][2] == new_cat, f"{child} parent still user1"


def test_clone_rewrites_the_storage_location(db):
    t = er.read_template(db, SCHEMA, REALM, "user1")
    entities, _ = er.clone_rows(t, 3, REALM, BASE)
    cat = [e for e in entities if e[4] == "sqlclone3_catalog"][0]
    assert cat[13]["default-base-location"] == "s3a://bkt/sqlclone3_catalog/"
    assert cat[13]["catalogType"] == "INTERNAL", "other keys untouched"
    assert cat[15] == "bkt/sqlclone3_catalog"


def test_service_admin_is_not_remapped(db):
    """The template's grants include a row whose grantee is service_admin — an
    id OUTSIDE the user-set. Remapping it would invent a grantee that does not
    exist."""
    t = er.read_template(db, SCHEMA, REALM, "user1")
    _, grants = er.clone_rows(t, 0, REALM, BASE)
    assert len([g for g in grants if g[3] == SERVICE_ADMIN_ID]) == 1


def test_clone_blocks_do_not_overlap(db):
    t = er.read_template(db, SCHEMA, REALM, "user1")
    a, _ = er.clone_rows(t, 0, REALM, BASE)
    b, _ = er.clone_rows(t, 1, REALM, BASE)
    assert max(e[0] for e in a) < min(e[0] for e in b)
    assert len(t["entities"]) <= er.IDS_PER_CLONE


def test_clones_do_not_collide_with_each_other(db):
    t = er.read_template(db, SCHEMA, REALM, "user1")
    res = er.insert_clones(db, SCHEMA, REALM, t, 25, BASE)
    assert res["entities"] == 25 * 7
    assert res["grants"] == 25 * 5
    assert er.clone_counts(db, SCHEMA, REALM) == {"entities": 175, "grants": 125}


def test_a_colliding_clone_raises_rather_than_being_skipped(db):
    """`ON CONFLICT DO NOTHING` would turn a primary-key collision into a
    silently smaller realm."""
    t = er.read_template(db, SCHEMA, REALM, "user1")
    er.insert_clones(db, SCHEMA, REALM, t, 1, BASE)
    with pytest.raises(AssertionError, match="PRIMARY KEY collision"):
        er.insert_clones(db, SCHEMA, REALM, t, 1, BASE)


# ----------------------------------------------------------------------
# removal — the part that nearly went very wrong
# ----------------------------------------------------------------------
def test_delete_never_touches_a_real_entity_with_a_high_id(db):
    """THE regression. `DELETE ... WHERE id >= BASE` matched 201 real rows on
    the live cluster — `user975_principal`, `user888_catalog` and friends —
    because Polaris ids are scattered, not capped. Deletion keys on names now.
    """
    db.entities.append(_entity(HIGH_REAL_ID, 0, 0, 2, "user975_principal"))
    db.entities.append(_entity(BASE + 5, 0, 0, 2, "user888_principal"))
    t = er.read_template(db, SCHEMA, REALM, "user1")
    er.insert_clones(db, SCHEMA, REALM, t, 3, BASE + 1_000_000)

    removed = er.delete_clones(db, SCHEMA, REALM)

    assert removed["entities"] == 21
    survivors = {e[4] for e in db.entities}
    assert "user975_principal" in survivors, "a REAL high-id entity was deleted"
    assert "user888_principal" in survivors, "a REAL in-band entity was deleted"
    assert not any(str(n).startswith("sqlclone") for n in survivors)


def test_delete_removes_only_clones(db):
    t = er.read_template(db, SCHEMA, REALM, "user1")
    er.insert_clones(db, SCHEMA, REALM, t, 10, BASE)
    real_e, real_g = len(template_rows()), len(template_grants())
    removed = er.delete_clones(db, SCHEMA, REALM)
    assert removed == {"entities": 70, "grants": 50}
    assert len(db.entities) == real_e and len(db.grants) == real_g


def test_clone_ids_are_found_by_name_and_parentage(db):
    """Namespaces and the two catalog-roles keep ordinary names; they are only
    reachable through their catalog. A name-only sweep would strand them."""
    t = er.read_template(db, SCHEMA, REALM, "user1")
    er.insert_clones(db, SCHEMA, REALM, t, 2, BASE)
    ids = er.clone_ids(db, SCHEMA, REALM)
    names = {e[4] for e in db.entities if e[0] in ids}
    assert "ns1" in names and "catalog_admin" in names
    assert len(ids) == 14


# ----------------------------------------------------------------------
# authenticable identities at a chosen grant-set size
# ----------------------------------------------------------------------
def _template_with_privileges(n_priv):
    """A source user-set whose owner_principal holds n_priv privilege grants,
    each a distinct privilege_code, so size-capping has something to cap."""
    ents = template_rows()
    grants = [
        (0, ROLE_ID, 0, PRINCIPAL_ID, 1, REALM),  # principal -> role
        (CAT_ID, CAT_ID + 2, 0, ROLE_ID, 1, REALM),  # role -> owner_principal
        (CAT_ID, CAT_ID, CAT_ID, CAT_ID + 1, 2, REALM),  # catalog_admin
        (CAT_ID, CAT_ID, 0, SERVICE_ADMIN_ID, 3, REALM),  # service_admin
    ]
    # owner_principal (CAT_ID+2) privilege grants, codes 10..10+n
    for code in range(10, 10 + n_priv):
        grants.append((CAT_ID, CAT_ID, CAT_ID, CAT_ID + 2, code, REALM))
    return {
        "prefix": "user1",
        "catalog_id": CAT_ID,
        "ids": {e[0] for e in ents},
        "entities": ents,
        "grants": grants,
        "source_principal_id": PRINCIPAL_ID,
        "auth": SOURCE_AUTH,
    }


def test_read_identity_source_attaches_the_credential_row(db):
    t = er.read_identity_source(db, SCHEMA, REALM, "user1")
    assert t["auth"] == SOURCE_AUTH
    assert t["source_principal_id"] == PRINCIPAL_ID


def test_read_identity_source_refuses_a_principal_with_no_credentials(db):
    """A clone with no hash to copy could never authenticate — the whole point.
    Fail loudly at read, not silently at login."""
    db.auth = []
    with pytest.raises(LookupError, match="no credential row"):
        er.read_identity_source(db, SCHEMA, REALM, "user1")


def test_auth_chain_finds_the_leaf_catalog_role_from_the_grant_graph():
    """Which catalog-role the principal holds is computed from the grants, never
    assumed — the repeated failure mode in this repo."""
    t = _template_with_privileges(3)
    chain, leaves = er._principal_auth_chain(t)
    assert PRINCIPAL_ID in chain and ROLE_ID in chain
    assert leaves == {CAT_ID + 2}  # owner_principal, not catalog_admin


def test_size_cap_trims_privilege_grants_but_keeps_structural_ones():
    t = _template_with_privileges(10)
    _, leaves = er._principal_auth_chain(t)
    kept = er._size_capped_grants(t, leaves, size=3)
    priv = [g for g in kept if g[3] in leaves]
    structural = [g for g in kept if g[3] not in leaves]
    assert len(priv) == 3
    assert len(structural) == 4  # role assignments + catalog_admin + service_admin


def test_size_cap_is_a_prefix_so_sizes_are_monotone():
    """Size K for one identity must be a subset of size K'>K for another, or the
    axis is a random scatter instead of a curve."""
    t = _template_with_privileges(10)
    _, leaves = er._principal_auth_chain(t)
    small = {g[4] for g in er._size_capped_grants(t, leaves, 3) if g[3] in leaves}
    big = {g[4] for g in er._size_capped_grants(t, leaves, 6) if g[3] in leaves}
    assert small < big


def test_size_none_keeps_every_grant():
    t = _template_with_privileges(10)
    assert (
        er._size_capped_grants(t, er._principal_auth_chain(t)[1], None) == t["grants"]
    )


def test_clone_identity_copies_hash_and_salt_verbatim_under_a_new_id():
    t = _template_with_privileges(5)
    ents, grants, auth, client_id = er.clone_identity(t, 0, REALM, 9 * 10**18, size=2)
    realm, pid, cid, mainh, sech, salt = auth
    assert (mainh, sech, salt) == ("HASH", "HASH", "SALT")  # verbatim
    assert pid != PRINCIPAL_ID and cid == client_id  # new identity
    assert client_id == "idclone0-client"


def test_insert_identities_writes_one_authenticable_principal_per_size(db):
    t = er.read_identity_source(db, SCHEMA, REALM, "user1")
    # give the source several privilege grants so sizes differ
    t = _template_with_privileges(50)
    base, _ = er.find_clone_band(db, SCHEMA, REALM, 4)
    out = er.insert_identities(db, SCHEMA, REALM, t, [2, 25, 50], base)
    assert [o["size_requested"] for o in out] == [2, 25, 50]
    assert len({o["client_id"] for o in out}) == 3  # distinct client_ids
    # one credential row per identity
    assert len(db.auth) == 1 + 3  # source + three clones
    # bigger size => more grant rows written
    assert out[0]["grants_written"] < out[2]["grants_written"]


def test_delete_identities_clears_credentials_too(db):
    t = _template_with_privileges(50)
    base, _ = er.find_clone_band(db, SCHEMA, REALM, 3)
    er.insert_identities(db, SCHEMA, REALM, t, [2, 25], base)
    assert len(db.auth) == 3  # source + 2
    removed = er.delete_identities(db, SCHEMA, REALM)
    assert removed["auth"] == 2  # both clone credentials gone
    assert len(db.auth) == 1  # source survives — it is real, not prefixed
    assert er.clone_counts(db, SCHEMA, REALM, er.IDENTITY_NAME_PREFIX) == {
        "entities": 0,
        "grants": 0,
    }
