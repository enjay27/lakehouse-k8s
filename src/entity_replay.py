"""
entity_replay.py
================
Create N user-sets in the metastore by SQL, by cloning one real one.

WHY
---
A 10,000-user realm over REST is ~610,000 API calls and ~8.5 hours. The same
realm as rows is seconds. What stood in the way was knowing exactly what a
create writes -- and notebook 01 already captured that from Polaris's own log:

    INSERT INTO POLARIS_SCHEMA.ENTITIES
        (id, catalog_id, parent_id, type_code, name, entity_version,
         sub_type_code, create_timestamp, drop_timestamp, purge_timestamp,
         to_purge_timestamp, last_update_timestamp, properties,
         internal_properties, grant_records_version, location_without_scheme,
         realm_id)
    INSERT INTO POLARIS_SCHEMA.GRANT_RECORDS
        (securable_catalog_id, securable_id, grantee_catalog_id, grantee_id,
         privilege_code, realm_id)

Those are the only two tables a create touches. There is no INSERT into
`policy_mapping_record` (it appears only in teardown DELETEs) and zero `events`
traffic on any traced path. `principal_authentication_data` is skipped
deliberately -- the clones are never authenticated, which is the one thing that
would need it.

CLONE A PATTERN, NOT A SCHEMA
-----------------------------
`entities` has seventeen columns including two JSONB blobs, and a catalog's
`internal_properties` carries its storage config. Constructing that by hand is
the kind of guess this repo keeps getting burned by. So every clone is copied
from a live user-set: only `id`, `name`, `parent_id`, `catalog_id` and the
location strings are rewritten. Everything else -- type codes, versions,
timestamps, both blobs -- is whatever Polaris itself wrote.

The same applies to `grant_records`, and it is why the role graph comes along
for free: nothing here needs to know what `privilege_code` encodes for a
role assignment, or to remember that `service_admin` holds one grant per
catalog. Both are simply in the template.

TWO SENTINEL SPACES, AND WHY THEY DIFFER
----------------------------------------
`grant_scale` filler lives in the NEGATIVE id space and is removed with
`WHERE grantee_id < 0`. Clones therefore CANNOT be negative: their grant rows
would carry negative grantee ids and `delete_filler` would take them out. So
clones use a reserved HIGH range instead, asserted above every live id, removed
with its own predicate. Two spaces, two predicates, provably disjoint from each
other and from real data.

WHAT THESE CLONES ARE NOT
-------------------------
Read-only fixtures. They have no MinIO objects, so anything vending credentials
or touching storage fails against them. They share their template's storage
location unless rewritten (this module rewrites it). They are synthetic rows and
every number derived from them is disclosed as such.

And they are written behind Polaris's back: `InMemoryEntityCache` holds an
entity together with its grant_records, so **restart Polaris after cloning**, or
clone while it is down.
"""

import json

import api_trace

#: Starting point for the id search, NOT a reserved region.
#:
#: This was a hardcoded "above every live id" constant, on the strength of three
#: sampled ids (~7.99e18, ~2.49e18, ~7.7e16). It was wrong: Polaris ids are
#: scattered across the whole bigint range, and 201 real entities were found
#: sitting above 9e18 -- `user975_principal`, `user888_catalog` and friends.
#:
#: Two consequences, the second serious. There is no such thing as a "high
#: reserved range" to claim; and any predicate of the form `id >= BASE` selects
#: REAL ROWS. `delete_clones` used exactly that, so `--remove` would have
#: deleted 201 real entities. Deletion is now scoped by NAME, never by an id
#: range, and the band below is only ever used to avoid a primary-key collision
#: at insert time -- bounded at both ends, and verified empty before use.
CLONE_ID_SEARCH_START = 9_000_000_000_000_000_000

#: Ids used per clone. Seven entities today (principal, principal-role, catalog,
#: catalog_admin, owner_principal, ns1, ns2); the slack absorbs a template with a
#: few more without renumbering anything.
IDS_PER_CLONE = 16

#: Name prefix every clone carries. Deletion keys on this, so it must not match
#: anything real -- `assert_prefix_is_free` checks before a single insert.
#: Deliberately NOT "clone": short, generic prefixes are how a sweep predicate
#: eventually eats something it should not.
CLONE_NAME_PREFIX = "sqlclone"

BIGINT_MAX = 9_223_372_036_854_775_807

#: Column order taken from 01's captured INSERT, not from the schema. They agree
#: today; if a future Polaris reorders them, the capture is the thing that will
#: say so.
ENTITY_COLUMNS = (
    "id",
    "catalog_id",
    "parent_id",
    "type_code",
    "name",
    "entity_version",
    "sub_type_code",
    "create_timestamp",
    "drop_timestamp",
    "purge_timestamp",
    "to_purge_timestamp",
    "last_update_timestamp",
    "properties",
    "internal_properties",
    "grant_records_version",
    "location_without_scheme",
    "realm_id",
)

GRANT_COLUMNS = (
    "securable_catalog_id",
    "securable_id",
    "grantee_catalog_id",
    "grantee_id",
    "privilege_code",
    "realm_id",
)

TYPE_PRINCIPAL, TYPE_PRINCIPAL_ROLE, TYPE_CATALOG = 2, 3, 4


# ----------------------------------------------------------------------
# safety
# ----------------------------------------------------------------------
def find_clone_band(conn, schema, realm, n_clones, start=CLONE_ID_SEARCH_START):
    """A contiguous id band of the required width holding NO live rows.

    Not a reserved constant -- Polaris ids are scattered across the bigint
    range, so a band has to be found and checked rather than declared. The
    search is cheap: with a few thousand entities spread over ~9.2e18, almost
    any specific band of a few hundred thousand ids is empty, and the check
    proves it rather than assuming it.

    Returns:
        (base, width). Raises RuntimeError if no empty band is found.
    """
    width = n_clones * IDS_PER_CLONE
    if width <= 0:
        raise ValueError("n_clones must be positive")
    for attempt in range(64):
        base = start + attempt * width * 8
        if base + width >= BIGINT_MAX:
            break
        with conn.cursor() as cur:
            cur.execute(
                api_trace.NO_LOAD_BALANCE
                + f"SELECT count(*) FROM {schema}.entities "  # noqa: S608
                "WHERE realm_id = %s AND id >= %s AND id < %s",
                (realm, base, base + width),
            )
            if cur.fetchone()[0] == 0:
                return base, width
    raise RuntimeError(
        f"no empty id band of width {width} found from {start}. The realm is "
        "denser than expected; widen the search or lower the clone count."
    )


def assert_prefix_is_free(conn, schema, realm, prefix=CLONE_NAME_PREFIX):
    """Nothing may already carry the clone name prefix. Call BEFORE inserting.

    Deletion keys on this prefix, so a real entity wearing it would be removed
    by `--remove`. That is the failure mode this whole module was one command
    away from: the previous version deleted on `id >= BASE`, and 201 real
    entities were sitting above the base.

    There is deliberately **no id filter** here. An earlier draft narrowed the
    check to `id < CLONE_ID_SEARCH_START`, which excludes precisely the region
    where the real entities that started all this were found -- a guard that
    looks everywhere except at the crime scene. Any prefixed row at all makes
    this refuse.

    Because it refuses on ANY match, it is an insert-time precondition only:
    once clones exist it will (correctly) fail, so the removal path renders the
    inventory instead of re-asserting.
    """
    with conn.cursor() as cur:
        cur.execute(
            api_trace.NO_LOAD_BALANCE
            + f"SELECT count(*) FROM {schema}.entities "  # noqa: S608
            "WHERE realm_id = %s AND name LIKE %s",
            (realm, f"{prefix}%"),
        )
        n = cur.fetchone()[0]
    assert n == 0, (
        f"{n} entities already carry the {prefix!r} prefix. Either a previous "
        "run left clones behind (--remove them first) or something real wears "
        "the prefix, in which case picking a different one is the only safe "
        "move: deletion keys on that prefix and would take the real rows too."
    )
    return True


# ----------------------------------------------------------------------
# template
# ----------------------------------------------------------------------
def read_template(conn, schema, realm, prefix="user1"):
    """Every row of one real user-set: its entities and their grant_records.

    Returns:
        dict with `entities` (list of column-ordered tuples), `grants`, `ids`
        (the id set belonging to this user) and `catalog_id`.

    Raises:
        LookupError: if the template is incomplete. A partial template would
            produce partial clones, and a realm of subtly broken users is worse
            than no realm at all.
    """
    cols = ", ".join(ENTITY_COLUMNS)
    with conn.cursor() as cur:
        cur.execute(
            api_trace.NO_LOAD_BALANCE
            + f"SELECT {cols} FROM {schema}.entities "  # noqa: S608
            "WHERE realm_id = %s AND name = %s AND type_code = %s",
            (realm, f"{prefix}_catalog", TYPE_CATALOG),
        )
        catalog = cur.fetchone()
        if not catalog:
            raise LookupError(f"no catalog named {prefix}_catalog in realm {realm}")
        catalog_id = catalog[0]

        # `id = %s` is NOT redundant with `catalog_id = %s`.
        #
        # A catalog's own `catalog_id` is not its own id -- measured on the live
        # cluster 2026-08-21, when this query returned the catalog's children
        # and not the catalog. The test fake had asserted the opposite
        # ("a catalog's catalog_id is its own id"), so the suite confirmed the
        # assumption instead of testing it and the shape was only discovered
        # against real rows. Selecting the catalog by id makes the query
        # correct whatever that column holds.
        cur.execute(
            api_trace.NO_LOAD_BALANCE
            + f"SELECT {cols} FROM {schema}.entities "  # noqa: S608
            "WHERE realm_id = %s AND (id = %s OR catalog_id = %s "
            "  OR name = ANY(%s)) ORDER BY type_code, name",
            (
                realm,
                catalog_id,
                catalog_id,
                [f"{prefix}_principal", f"{prefix}_principal_role"],
            ),
        )
        entities = cur.fetchall()

    ids = {row[0] for row in entities}
    types = {row[3] for row in entities}
    for need, label in (
        (TYPE_PRINCIPAL, "principal"),
        (TYPE_PRINCIPAL_ROLE, "principal-role"),
        (TYPE_CATALOG, "catalog"),
    ):
        if need not in types:
            raise LookupError(
                f"template {prefix} has no {label} (type_code {need}). Clones "
                "built from it would be incomplete; pick a complete user."
            )

    gcols = ", ".join(GRANT_COLUMNS)
    with conn.cursor() as cur:
        cur.execute(
            api_trace.NO_LOAD_BALANCE
            + f"SELECT {gcols} FROM {schema}.grant_records "  # noqa: S608
            "WHERE realm_id = %s AND (securable_catalog_id = %s "
            "  OR grantee_id = ANY(%s) OR securable_id = ANY(%s))",
            (realm, catalog_id, list(ids), list(ids)),
        )
        grants = cur.fetchall()

    return {
        "prefix": prefix,
        "catalog_id": catalog_id,
        "ids": ids,
        "entities": entities,
        "grants": grants,
    }


# ----------------------------------------------------------------------
# stamping
# ----------------------------------------------------------------------
def _remap(value, id_map):
    """Ids inside the template are rewritten; ids outside it are left alone.

    That distinction is load-bearing. `service_admin` holds one grant per
    catalog, so the template's grant set includes a row whose grantee is
    service_admin -- an id OUTSIDE the user-set. Remapping it would invent a
    grantee that does not exist; leaving it gives every clone catalog the same
    service_admin grant a real one gets.
    """
    return id_map.get(value, value)


def clone_rows(template, k, realm, base, name_prefix=CLONE_NAME_PREFIX):
    """The entity and grant rows for clone `k`, as column-ordered tuples."""
    base = base + k * IDS_PER_CLONE
    ordered = sorted(template["entities"], key=lambda r: r[0])
    id_map = {row[0]: base + slot for slot, row in enumerate(ordered)}

    old_catalog_name = f"{template['prefix']}_catalog"
    new_catalog_name = f"{name_prefix}{k}_catalog"

    entities = []
    for row in ordered:
        r = list(row)
        r[0] = id_map[row[0]]
        r[1] = _remap(row[1], id_map)  # catalog_id
        r[2] = _remap(row[2], id_map)  # parent_id
        # Only realm-level entities need a new name: the catalog's children are
        # unique under the new catalog_id by the table's own constraint
        # (realm_id, catalog_id, parent_id, type_code, name).
        if row[3] in (TYPE_PRINCIPAL, TYPE_PRINCIPAL_ROLE, TYPE_CATALOG):
            r[4] = str(row[4]).replace(template["prefix"], f"{name_prefix}{k}", 1)
        # Storage strings carry the template catalog's name. Left alone, every
        # clone would claim the same location -- harmless for the read-only
        # probes this exists for, and a collision the moment anything writes.
        for idx in (12, 13):  # properties, internal_properties
            r[idx] = _rewrite_json(r[idx], old_catalog_name, new_catalog_name)
        if r[15]:
            r[15] = str(r[15]).replace(old_catalog_name, new_catalog_name)
        entities.append(tuple(r))

    grants = []
    for row in template["grants"]:
        g = list(row)
        g[0] = _remap(row[0], id_map)
        g[1] = _remap(row[1], id_map)
        g[2] = _remap(row[2], id_map)
        g[3] = _remap(row[3], id_map)
        grants.append(tuple(g))

    return entities, grants


def _rewrite_json(value, old, new):
    """Swap a catalog name inside a JSONB column, preserving its type.

    psycopg2 hands JSONB back as a dict; a plain `str.replace` on that would
    stringify it and the insert would write a quoted blob instead of an object.
    """
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return json.loads(json.dumps(value).replace(old, new))
    return str(value).replace(old, new)


def insert_clones(
    conn,
    schema,
    realm,
    template,
    n_clones,
    base,
    name_prefix=CLONE_NAME_PREFIX,
    on_progress=None,
):
    """Stamp out `n_clones` copies of the template.

    NOT idempotent, on purpose: call `delete_clones()` first to re-run. A
    conflict here means an id collision, and that should raise rather than
    quietly produce a smaller realm than requested.

    Uses `execute_values` rather than a server-side `generate_series`: 10,000
    clones is ~70,000 entity rows and ~550,000 grant rows, which is small enough
    that being able to build and TEST the id mapping in Python is worth more
    than the round trips saved.
    """
    from psycopg2.extras import Json, execute_values

    ecols = ", ".join(ENTITY_COLUMNS)
    gcols = ", ".join(GRANT_COLUMNS)
    total_e = total_g = 0

    for k in range(n_clones):
        entities, grants = clone_rows(template, k, realm, base, name_prefix)
        entities = [
            tuple(
                Json(v) if i in (12, 13) and v is not None else v
                for i, v in enumerate(row)
            )
            for row in entities
        ]
        with conn.cursor() as cur:
            execute_values(
                cur,
                # NO `ON CONFLICT DO NOTHING` here, deliberately. It would make
                # a primary-key collision with a real entity a silent no-op, and
                # the run would report fewer clones than asked for with no
                # indication why. Re-running is handled by delete_clones().
                f"INSERT INTO {schema}.entities ({ecols}) VALUES %s",  # noqa: S608
                entities,
            )
            total_e += cur.rowcount if cur.rowcount and cur.rowcount > 0 else 0
            if grants:
                execute_values(
                    cur,
                    f"INSERT INTO {schema}.grant_records ({gcols}) "  # noqa: S608
                    "VALUES %s",
                    grants,
                )
                total_g += cur.rowcount if cur.rowcount and cur.rowcount > 0 else 0
        if on_progress and (k + 1) % 250 == 0:
            on_progress(f"  {k + 1:,}/{n_clones:,} clones")
    return {"entities": total_e, "grants": total_g}


# ----------------------------------------------------------------------
# accounting and removal
# ----------------------------------------------------------------------
def clone_ids(conn, schema, realm, prefix=CLONE_NAME_PREFIX):
    """Every id belonging to a clone, found by NAME and by parentage.

    Two hops, because only realm-level entities carry the prefix:

      1. catalogs, principals and principal-roles named `<prefix>...`;
      2. everything whose `catalog_id` is one of those catalogs -- the
         catalog_admin and owner_principal roles, and the namespaces, which keep
         their ordinary names and are identifiable only by parentage.

    This replaces an `id >= BASE` predicate that would have matched 201 real
    entities. Ids are scattered; names are ours.
    """
    with conn.cursor() as cur:
        cur.execute(
            api_trace.NO_LOAD_BALANCE
            + f"SELECT id, type_code FROM {schema}.entities "  # noqa: S608
            "WHERE realm_id = %s AND name LIKE %s",
            (realm, f"{prefix}%"),
        )
        top = cur.fetchall()
        catalog_ids = [i for i, tc in top if tc == TYPE_CATALOG]
        ids = {i for i, _ in top}
        if catalog_ids:
            cur.execute(
                api_trace.NO_LOAD_BALANCE
                + f"SELECT id FROM {schema}.entities "  # noqa: S608
                "WHERE realm_id = %s AND catalog_id = ANY(%s)",
                (realm, catalog_ids),
            )
            ids.update(r[0] for r in cur.fetchall())
    return sorted(ids)


def clone_counts(conn, schema, realm, prefix=CLONE_NAME_PREFIX):
    """Rows belonging to clones, by name and parentage -- never by id range."""
    ids = clone_ids(conn, schema, realm, prefix)
    if not ids:
        return {"entities": 0, "grants": 0}
    with conn.cursor() as cur:
        cur.execute(
            api_trace.NO_LOAD_BALANCE
            + f"SELECT count(*) FROM {schema}.grant_records "  # noqa: S608
            "WHERE realm_id = %s AND (securable_id = ANY(%s) "
            "  OR grantee_id = ANY(%s))",
            (realm, ids, ids),
        )
        grants = cur.fetchone()[0]
    return {"entities": len(ids), "grants": grants}


def clone_inventory(conn, schema, realm, prefix=CLONE_NAME_PREFIX, limit=20):
    """What is actually there, by type and name.

    A count alone cannot say whether 201 rows are 28 clones plus a partial one
    or something else entirely -- and guessing at that is how this directory
    keeps producing confident wrong answers. Render it instead.
    """
    ids = clone_ids(conn, schema, realm, prefix)
    if not ids:
        return {"by_type": [], "sample": []}
    with conn.cursor() as cur:
        cur.execute(
            api_trace.NO_LOAD_BALANCE
            + f"""SELECT type_code, count(*), min(name), max(name)
                  FROM {schema}.entities
                  WHERE realm_id = %s AND id = ANY(%s)
                  GROUP BY type_code ORDER BY type_code""",  # noqa: S608
            (realm, ids),
        )
        by_type = cur.fetchall()
        cur.execute(
            api_trace.NO_LOAD_BALANCE
            + f"""SELECT id, catalog_id, parent_id, type_code, name
                  FROM {schema}.entities
                  WHERE realm_id = %s AND id = ANY(%s)
                  ORDER BY id LIMIT %s""",  # noqa: S608
            (realm, ids, limit),
        )
        sample = cur.fetchall()
    return {"by_type": by_type, "sample": sample}


def delete_clones(conn, schema, realm, prefix=CLONE_NAME_PREFIX):
    """Remove every cloned row, scoped by the id set `clone_ids` resolved.

    Grants first: a grant whose securable is gone is an orphan, and orphans in
    `grant_records` are what the audit is trying to measure the absence of.

    The predicate is an explicit id list derived from names, NOT `id >= BASE`.
    The previous version used the range, and 201 real entities were living
    inside it.
    """
    ids = clone_ids(conn, schema, realm, prefix)
    if not ids:
        return {"entities": 0, "grants": 0}
    with conn.cursor() as cur:
        cur.execute(
            f"DELETE FROM {schema}.grant_records "  # noqa: S608
            "WHERE realm_id = %s AND (securable_id = ANY(%s) "
            "  OR grantee_id = ANY(%s))",
            (realm, ids, ids),
        )
        g = cur.rowcount
        cur.execute(
            f"DELETE FROM {schema}.entities "  # noqa: S608
            "WHERE realm_id = %s AND id = ANY(%s)",
            (realm, ids),
        )
        e = cur.rowcount
    left = clone_counts(conn, schema, realm, prefix)
    assert left == {"entities": 0, "grants": 0}, f"clones survived deletion: {left}"
    return {"entities": e, "grants": g}


# ----------------------------------------------------------------------
# authenticable identities, at a chosen grant-set SIZE
# ----------------------------------------------------------------------
# Everything above clones USER-SETS to move row volume. This section clones
# PRINCIPALS that can AUTHENTICATE, to move a different axis: grant-set size.
#
# Confirmed live (Kade, 2026-08-24): a principal_authentication_data row copied
# with the source's main_secret_hash + secret_salt under a new client_id
# authenticates with the source's plaintext secret. So one API-minted principal
# seeds a whole fleet, and the plaintext never has to be stored -- the caller
# holds it from the mint, this code only copies the hash.
#
# The point of the fleet is a CURVE. An unindexed grantee lookup's cost is
# constant in the grantee's grant count; an indexed one tracks rows returned. So
# the index benefit is large for a 2-grant principal and small for a 200-grant
# one. Cloning principals at chosen sizes turns that into a measured line.

#: Its own prefix, distinct from CLONE_NAME_PREFIX, so identity cleanup and
#: volume-clone cleanup never touch each other's rows.
IDENTITY_NAME_PREFIX = "idclone"

TYPE_CATALOG_ROLE = 5

#: One extra column set beyond ENTITY_COLUMNS/GRANT_COLUMNS: the credential row.
#: Column order from the captured bootstrap INSERT, not the schema.
AUTH_COLUMNS = (
    "realm_id",
    "principal_id",
    "principal_client_id",
    "main_secret_hash",
    "secondary_secret_hash",
    "secret_salt",
)


def read_identity_source(conn, schema, realm, source_prefix="user1"):
    """A source user-set PLUS its principal's credential row.

    Builds on `read_template` (entities + grants) and adds the one thing an
    authenticable clone needs that a volume clone does not: the source
    principal's `principal_authentication_data` row. Only the HASH and SALT are
    read; the plaintext secret is the caller's, from when it minted the source.

    Raises LookupError if the source principal has no credential row -- an
    identity cloned from it could never authenticate, which is the whole point.
    """
    template = read_template(conn, schema, realm, source_prefix)
    principal = next((e for e in template["entities"] if e[3] == TYPE_PRINCIPAL), None)
    # read_template already guarantees a principal exists, but be explicit.
    if principal is None:  # pragma: no cover
        raise LookupError(f"source {source_prefix} has no principal")
    principal_id = principal[0]

    acols = ", ".join(AUTH_COLUMNS)
    with conn.cursor() as cur:
        cur.execute(
            api_trace.NO_LOAD_BALANCE
            + f"SELECT {acols} FROM {schema}.principal_authentication_data "  # noqa: S608
            "WHERE realm_id = %s AND principal_id = %s",
            (realm, principal_id),
        )
        auth = cur.fetchone()
    if not auth:
        raise LookupError(
            f"source principal {source_prefix} has no credential row. Mint one "
            "over the API first (reset_principal_credentials), then re-read: a "
            "clone with no hash to copy cannot authenticate."
        )

    template["source_principal_id"] = principal_id
    template["auth"] = auth  # (realm, principal_id, client_id, mainh, sech, salt)
    return template


def _principal_auth_chain(template):
    """The grantee ids the source principal's authorization actually walks.

    principal -> its principal-roles -> their catalog-roles. Computed from the
    template's own grant chain, never assumed: which catalog-role a principal
    holds is a fact about how the fixture was seeded, and this repo has been
    burned three times by assuming such facts.

    Returns (chain_ids, leaf_catalog_role_ids). The leaves are the catalog-roles
    whose privilege grants SCALE the footprint -- the ones a size cap trims.
    """
    by_type = {e[0]: e[3] for e in template["entities"]}
    principal_ids = {e[0] for e in template["entities"] if e[3] == TYPE_PRINCIPAL}
    # grants are (securable_catalog_id, securable_id, grantee_catalog_id,
    #             grantee_id, privilege_code, realm_id)
    role_ids = {
        g[1]
        for g in template["grants"]
        if g[3] in principal_ids and by_type.get(g[1]) == TYPE_PRINCIPAL_ROLE
    }
    catalog_role_ids = {
        g[1]
        for g in template["grants"]
        if g[3] in role_ids and by_type.get(g[1]) == TYPE_CATALOG_ROLE
    }
    chain = principal_ids | role_ids | catalog_role_ids
    return chain, catalog_role_ids


def _size_capped_grants(template, leaf_role_ids, size):
    """The template's grants, keeping only `size` privilege grants on the leaves.

    A privilege grant is one whose GRANTEE is a leaf catalog-role -- those are
    what scale a principal's footprint. Structural grants (role assignments,
    service_admin, catalog_admin) are always kept, so the identity stays
    authorizable at every size. `size=None` keeps everything.

    Trimming is deterministic (sorted by privilege_code) so size K for one
    identity is a prefix of size K'>K for another -- a monotone axis, not a
    random subset.
    """
    if size is None:
        return list(template["grants"])
    structural = [g for g in template["grants"] if g[3] not in leaf_role_ids]
    privilege = sorted(
        (g for g in template["grants"] if g[3] in leaf_role_ids),
        key=lambda g: g[4],  # privilege_code
    )
    return structural + privilege[:size]


def clone_identity(
    template, k, realm, base, size=None, name_prefix=IDENTITY_NAME_PREFIX
):
    """Entity rows, size-capped grant rows, and ONE credential row for clone k.

    The entity and grant remapping is `clone_rows`'; the additions are the size
    cap and the credential tuple. The credential carries the source's hash and
    salt verbatim under this clone's new principal_id and client_id.

    Returns (entities, grants, auth_tuple, client_id).
    """
    # `clone_rows` applies the per-clone shift itself, so it must receive the
    # ORIGINAL base. Build the local id_map from the SAME shift clone_rows will
    # use, or the credential and grant rows land at a different base than the
    # entities -- a double-shift that put idclone1's auth row on a principal id
    # no entity had. Caught by test_delete_identities_clears_credentials_too.
    shifted = base + k * IDS_PER_CLONE
    ordered = sorted(template["entities"], key=lambda r: r[0])
    id_map = {row[0]: shifted + slot for slot, row in enumerate(ordered)}

    entities, _ = clone_rows(template, k, realm, base, name_prefix)

    _, leaf_role_ids = _principal_auth_chain(template)
    kept = _size_capped_grants(template, leaf_role_ids, size)
    grants = []
    for row in kept:
        g = list(row)
        g[0] = _remap(row[0], id_map)
        g[1] = _remap(row[1], id_map)
        g[2] = _remap(row[2], id_map)
        g[3] = _remap(row[3], id_map)
        grants.append(tuple(g))

    new_principal_id = id_map[template["source_principal_id"]]
    client_id = f"{name_prefix}{k}-client"
    src_auth = template["auth"]
    auth = (
        realm,
        new_principal_id,
        client_id,
        src_auth[3],  # main_secret_hash, verbatim
        src_auth[4],  # secondary_secret_hash, verbatim
        src_auth[5],  # secret_salt, verbatim
    )
    return entities, grants, auth, client_id


def insert_identities(
    conn,
    schema,
    realm,
    template,
    sizes,
    base,
    name_prefix=IDENTITY_NAME_PREFIX,
    on_progress=None,
):
    """One authenticable principal per requested size.

    `sizes` is a list of grant-set sizes, e.g. [2, 25, 50, 200]. Each becomes
    one clone whose principal walks approximately that many privilege grants
    (approximate because structural grants are always present -- the caller
    should MEASURE the footprint, never trust the requested number).

    Returns a list of {client_id, principal_id, size_requested, grants_written}
    -- the caller authenticates each as (client_id, SOURCE_PLAINTEXT_SECRET).

    NOT idempotent, like insert_clones: delete first to re-run. No ON CONFLICT,
    so an id or client_id collision raises rather than silently under-producing.
    """
    from psycopg2.extras import Json, execute_values

    ecols = ", ".join(ENTITY_COLUMNS)
    gcols = ", ".join(GRANT_COLUMNS)
    acols = ", ".join(AUTH_COLUMNS)
    out = []

    for k, size in enumerate(sizes):
        entities, grants, auth, client_id = clone_identity(
            template, k, realm, base, size, name_prefix
        )
        entities = [
            tuple(
                Json(v) if i in (12, 13) and v is not None else v
                for i, v in enumerate(row)
            )
            for row in entities
        ]
        with conn.cursor() as cur:
            execute_values(
                cur,
                f"INSERT INTO {schema}.entities ({ecols}) VALUES %s",  # noqa: S608
                entities,
            )
            if grants:
                execute_values(
                    cur,
                    f"INSERT INTO {schema}.grant_records ({gcols}) "  # noqa: S608
                    "VALUES %s",
                    grants,
                )
            cur.execute(
                f"INSERT INTO {schema}.principal_authentication_data ({acols}) "  # noqa: S608
                "VALUES (%s, %s, %s, %s, %s, %s)",
                auth,
            )
        out.append(
            {
                "client_id": client_id,
                "principal_id": auth[1],
                "size_requested": size,
                "grants_written": len(grants),
            }
        )
        if on_progress:
            on_progress(
                f"  identity {k}: size~{size}, {len(grants)} grants, "
                f"client_id={client_id}"
            )
    return out


def delete_identities(conn, schema, realm, prefix=IDENTITY_NAME_PREFIX):
    """Remove cloned identities INCLUDING their credential rows.

    `delete_clones` does not touch `principal_authentication_data` -- volume
    clones have none. Identities do, so deletion here clears three tables. The
    credential rows are keyed by principal_id, resolved from the same name-scoped
    id set, never an id range.
    """
    ids = clone_ids(conn, schema, realm, prefix)
    if not ids:
        return {"entities": 0, "grants": 0, "auth": 0}
    with conn.cursor() as cur:
        cur.execute(
            f"DELETE FROM {schema}.principal_authentication_data "  # noqa: S608
            "WHERE realm_id = %s AND principal_id = ANY(%s)",
            (realm, ids),
        )
        a = cur.rowcount
        cur.execute(
            f"DELETE FROM {schema}.grant_records "  # noqa: S608
            "WHERE realm_id = %s AND (securable_id = ANY(%s) "
            "  OR grantee_id = ANY(%s))",
            (realm, ids, ids),
        )
        g = cur.rowcount
        cur.execute(
            f"DELETE FROM {schema}.entities "  # noqa: S608
            "WHERE realm_id = %s AND id = ANY(%s)",
            (realm, ids),
        )
        e = cur.rowcount
    left = clone_counts(conn, schema, realm, prefix)
    assert left == {"entities": 0, "grants": 0}, f"identities survived: {left}"
    return {"entities": e, "grants": g, "auth": a}
