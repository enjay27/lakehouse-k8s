#!/usr/bin/env python3
"""Create N user-sets by SQL, by cloning one real one. Steps 1, 2 and 6.

Steps 3-5 are yours: restart Polaris, smoke-test, measure.

    python3 sql_seed_entities.py --status
    python3 sql_seed_entities.py --count 100 --dry-run
    python3 sql_seed_entities.py --count 100
    #   -> restart Polaris (the cache holds entities WITH their grants)
    #   -> python3 sql_seed_entities.py --smoke      (needs Polaris up)
    python3 sql_seed_entities.py --remove

WHAT THIS IS FOR
----------------
610,000 REST calls and ~8.5 hours, or a few seconds of INSERTs. It works because
notebook 01 already captured exactly what a create writes: `entities` and
`grant_records`, and nothing else.

WHAT IT IS NOT
--------------
The clones are READ-ONLY fixtures with no MinIO objects behind them. Anything
that vends credentials or writes storage will fail against one. They are
synthetic rows: disclose that beside every number derived from them.

SAFETY -- READ THIS BEFORE CHANGING THE PREDICATES
--------------------------------------------------
An earlier version of this script claimed a "reserved HIGH id range" and deleted
with `WHERE id >= BASE`. That was wrong, and dangerously so: Polaris ids are
scattered across the whole bigint range, and `--status` found **201 real
entities above the base** (`user975_principal`, `user888_catalog`, and a pile of
`entityCleanup_*` tasks). One `--remove` would have deleted them.

So: clones are identified by NAME (`sqlclone*`) plus parentage, never by an id
range. The only thing an id band is used for now is picking primary keys that do
not collide -- it is searched for, checked empty at both ends, and never used as
a deletion predicate. Before a single insert, `assert_prefix_is_free` refuses if
anything at all already wears the prefix, at any id; and `--remove` prints what
it matched, by type and name range, before deleting it.

`grant_scale`'s filler is a separate sentinel space (NEGATIVE ids, removed with
`WHERE grantee_id < 0`). Clones must stay positive so `sql_fill.py --remove`
cannot sweep them. Two spaces, two predicates, no overlap.
"""

import argparse
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE
while not (REPO / "src").is_dir() and REPO != REPO.parent:
    REPO = REPO.parent
sys.path.insert(0, str(REPO / "src"))

import entity_replay as er  # noqa: E402

PG = dict(
    host=os.environ.get("PG_HOST", "192.168.139.2"),
    port=int(os.environ.get("PG_PORT", "5432")),
    dbname=os.environ.get("PG_DB", "polaris"),
    user=os.environ.get("PG_USER", "polaris"),
    password=os.environ.get("PG_PASSWORD", "polaris"),
)
SCHEMA = os.environ.get("PG_SCHEMA", "polaris_schema")
REALM = os.environ.get("POLARIS_REALM", "POLARIS")
POLARIS_URL = os.environ.get("POLARIS_URL", "http://192.168.139.2:8181")
ROOT_CLIENT = os.environ.get("POLARIS_ROOT_CLIENT", "root")
ROOT_SECRET = os.environ.get("POLARIS_ROOT_SECRET", "polaris-secret")


def connect():
    import psycopg2

    if not any(h in PG["host"] for h in ("localhost", "127.0.0.1", "192.168.")):
        sys.exit(f"refusing to write to a non-local PostgreSQL: {PG['host']}")
    conn = psycopg2.connect(**PG)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("/*NO LOAD BALANCE*/ SELECT pg_is_in_recovery()")
        if cur.fetchone()[0]:
            sys.exit("routed to a STANDBY; connect to the primary directly")
    return conn


def smoke(prefix, n_check=3):
    """Step 4 -- do the clones actually SERVE? Read-only, needs Polaris up.

    A clone that inserts cleanly but 500s on read is worse than none: the sweep
    would time an error path and report it as latency. So this runs before any
    measurement and fails loudly.
    """
    from polaris_rest import PolarisREST

    pc = PolarisREST(POLARIS_URL, REALM)
    r = pc.get_token(ROOT_CLIENT, ROOT_SECRET)
    if r.status_code >= 300:
        sys.exit(f"auth failed [{r.status_code}]: {r.text[:200]}")
    pc.token = r.json()["access_token"]

    bad = 0
    for k in range(n_check):
        cat = f"{prefix}{k}_catalog"
        checks = [
            ("GET  /catalogs/{name}", lambda: pc.get_catalog(cat)),
            ("GET  catalog-roles", lambda: pc.list_catalog_roles(cat)),
            ("GET  namespaces", lambda: pc.list_namespaces(cat)),
        ]
        print(f"\n{cat}")
        for label, call in checks:
            resp = call()
            ok = resp.status_code < 300
            bad += 0 if ok else 1
            print(f"   {label:<24} {resp.status_code}")
            if not ok:
                print(f"      {(resp.text or '')[:200]}")
    if bad:
        print(f"\n{bad} check(s) FAILED. The clones are malformed -- do not")
        print("measure against them. If Polaris was not restarted after the")
        print("insert, its entity cache may simply not know about them yet.")
        return 1
    print("\nall clones serve. Safe to measure.")
    return 0


def show_status(conn, prefix, template):
    """What the clone predicate currently matches, rendered rather than counted.

    The header deliberately does NOT say "clones present". It says what the
    predicate matched, because that is the only thing a count can honestly
    claim -- and the last time this script conflated the two it was one command
    away from deleting real user data.
    """
    counts = er.clone_counts(conn, SCHEMA, REALM, prefix)
    print(
        f"rows matching prefix {prefix!r}: {counts['entities']:,} entities, "
        f"{counts['grants']:,} grant_records"
    )

    with conn.cursor() as cur:
        cur.execute(
            f"SELECT count(*) FROM {SCHEMA}.entities WHERE realm_id = %s",  # noqa: S608
            (REALM,),
        )
        print(f"entities in realm      : {cur.fetchone()[0]:,}")
    print(f"id search starts at    : {er.CLONE_ID_SEARCH_START:,}")
    print("   (a search START, not a reserved range -- real ids live above it)")

    if counts["entities"] or counts["grants"]:
        inv = er.clone_inventory(conn, SCHEMA, REALM, prefix)
        print(f"\nwhat carries the {prefix!r} prefix right now:")
        print(f"   {'type':>6} {'count':>7}  name range")
        for tc, n, lo, hi in inv["by_type"]:
            print(f"   {tc:>6} {n:>7}  {lo} .. {hi}")
        print("\n   sample:")
        for row in inv["sample"][:8]:
            print(
                f"     id={row[0]} catalog_id={row[1]} "
                f"parent_id={row[2]} type={row[3]} {row[4]}"
            )
        print("\n   --remove clears exactly these rows and nothing else.")
    else:
        print("\nnothing carries the clone prefix. --remove would be a no-op.")

    t = er.read_template(conn, SCHEMA, REALM, template)
    print(
        f"\ntemplate {template!r}: {len(t['entities'])} entities, "
        f"{len(t['grants'])} grants"
    )
    print(f"   {'id':>21} {'catalog_id':>21} {'parent_id':>21} type  name")
    for e in sorted(t["entities"], key=lambda r: (r[3], r[4])):
        print(f"   {e[0]:>21} {e[1]:>21} {e[2]:>21} {e[3]:>4}  {e[4]}")
    return 0


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--count", type=int, help="how many user-sets to create")
    ap.add_argument("--template", default="user1", help="user-set to clone")
    ap.add_argument(
        "--name-prefix",
        default=er.CLONE_NAME_PREFIX,
        help=(
            "name every clone carries; deletion keys on it, so it must not "
            f"match anything real (default: {er.CLONE_NAME_PREFIX})"
        ),
    )
    ap.add_argument("--remove", action="store_true")
    ap.add_argument("--smoke", action="store_true", help="step 4; needs Polaris up")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not any((args.status, args.count, args.remove, args.smoke)):
        ap.error("nothing to do -- pass --status, --count, --smoke or --remove")

    if args.smoke and not (args.count or args.remove):
        return smoke(args.name_prefix)

    conn = connect()
    try:
        if args.status:
            return show_status(conn, args.name_prefix, args.template)

        if args.remove:
            # `assert_prefix_is_free` cannot run here -- it refuses on ANY
            # prefixed row, and by now the clones are prefixed rows. So render
            # what is about to go instead. A human reading `sqlclone7_catalog`
            # and namespaces beneath it can tell at a glance that these are not
            # `user888_catalog`; a bare "removed 201 rows" could not, and that
            # is how the previous version nearly took real data.
            inv = er.clone_inventory(conn, SCHEMA, REALM, args.name_prefix)
            if not inv["by_type"]:
                print(f"nothing carries the {args.name_prefix!r} prefix; nothing to do")
                return 0
            print(f"about to delete, matched by name prefix {args.name_prefix!r}:")
            for tc, n, lo, hi in inv["by_type"]:
                print(f"   type {tc:>3}  {n:>7} rows   {lo} .. {hi}")
            removed = er.delete_clones(conn, SCHEMA, REALM, args.name_prefix)
            print(
                f"removed {removed['entities']:,} entities and "
                f"{removed['grants']:,} grant_records"
            )
            return 0

        # --- step 1: read the template ---
        t = er.read_template(conn, SCHEMA, REALM, args.template)
        per_user = len(t["entities"])
        print(
            f"\ntemplate {args.template!r}: {per_user} entities, "
            f"{len(t['grants'])} grants"
        )
        print(
            f"projected: {args.count * per_user:,} entities, "
            f"{args.count * len(t['grants']):,} grant_records"
        )

        # Both guards run before the dry-run too, so --dry-run reports the same
        # refusals a real run would hit instead of printing a plan that cannot
        # execute.
        er.assert_prefix_is_free(conn, SCHEMA, REALM, args.name_prefix)
        base, width = er.find_clone_band(conn, SCHEMA, REALM, args.count)
        print(
            f"\nid band  : {base:,} .. {base + width:,} ({width:,} ids, verified empty)"
        )

        if args.dry_run:
            e, g = er.clone_rows(t, 0, REALM, base, args.name_prefix)
            print("\nclone 0 would be:")
            for row in sorted(e, key=lambda r: (r[3], r[4])):
                print(f"   id={row[0]}  catalog_id={row[1]}  type={row[3]:<3} {row[4]}")
            print(f"\n   and {len(g)} grant rows, ids remapped through the same map")
            print("\nNothing written. Re-run without --dry-run.")
            return 0

        # --- step 2: stamp them out ---
        res = er.insert_clones(
            conn,
            SCHEMA,
            REALM,
            t,
            args.count,
            base,
            name_prefix=args.name_prefix,
            on_progress=lambda line: print(line, flush=True),
        )
        print(f"\ninserted {res['entities']:,} entities, {res['grants']:,} grants")

        with conn.cursor() as cur:
            cur.execute(f"ANALYZE {SCHEMA}.entities")  # noqa: S608
            cur.execute(f"ANALYZE {SCHEMA}.grant_records")  # noqa: S608
        print("ANALYZE done")

        print("\nNEXT -- steps 3 and 4, in this order:")
        print("  1. RESTART POLARIS. Its cache holds an entity together with its")
        print("     grants, so a running instance may not see these at all.")
        print("  2. python3 sql_seed_entities.py --smoke")
        print("     A clone that inserts cleanly but 500s on read would be timed")
        print("     as latency. Do not measure until this passes.")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
