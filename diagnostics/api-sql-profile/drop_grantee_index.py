"""Remove hand-added indexes so the audit runs on the PLAIN upstream schema.

    python3 drop_grantee_index.py              # the grantee index only
    python3 drop_grantee_index.py --all-custom # every index upstream does not create
    python3 drop_grantee_index.py --list       # report, change nothing

THE POLICY (Kade, 2026-09-03). Measurements are taken on the schema Polaris
ships -- `schema_v3.sql`, which creates `idx_entities`, `idx_locations` and
`idx_policy_mapping_record` and gives `grant_records` nothing but its primary
key. A custom index makes every plan a statement about a database nobody runs,
and the whole point of the API-SQL matrix is what a real deployment does.

WHY `--all-custom` EXISTS. This script knew exactly one index name, so "drop the
custom indexes" silently meant "drop that one" and left anything else from an
earlier experiment in place -- indistinguishable, from the outside, from a clean
schema. `schema_audit.STOCK_INDEX_NAMES` is the authority; anything live and
outside it was added by hand.

Safe to re-run: IF EXISTS, and it verifies the result rather than assuming it.
CONCURRENTLY cannot run inside a transaction, hence autocommit.
"""

import argparse
import os
import pathlib
import sys

import psycopg2

PG = dict(
    host=os.environ.get("PG_HOST", "192.168.139.2"),
    port=int(os.environ.get("PG_PORT", "5432")),
    dbname=os.environ.get("PG_DB", "polaris"),
    user=os.environ.get("PG_USER", "polaris"),
    password=os.environ.get("PG_PASSWORD", "polaris"),
)
SCHEMA, INDEX = "polaris_schema", "idx_grant_records_grantee"

REPO = pathlib.Path(__file__).resolve().parent
while not (REPO / "src").is_dir() and REPO != REPO.parent:
    REPO = REPO.parent
sys.path.insert(0, str(REPO / "src"))
from schema_audit import STOCK_INDEX_NAMES, custom_indexes  # noqa: E402

LIVE_INDEXES = """
SELECT c.relname
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
JOIN pg_index i ON i.indexrelid = c.oid
WHERE n.nspname = %s AND c.relkind = 'i'
ORDER BY c.relname
"""

STATE = """
SELECT c.relname, i.indisvalid, i.indisready
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
JOIN pg_index i ON i.indexrelid = c.oid
WHERE n.nspname = %s AND c.relname = %s
"""

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument(
    "--all-custom",
    action="store_true",
    help="drop EVERY index upstream does not create, not just the " "grantee one",
)
ap.add_argument(
    "--list", action="store_true", help="report what is custom and change nothing"
)
args = ap.parse_args()

conn = psycopg2.connect(**PG)
conn.autocommit = True  # DROP INDEX CONCURRENTLY refuses a transaction block
with conn.cursor() as cur:
    cur.execute("SELECT pg_is_in_recovery()")
    if cur.fetchone()[0]:
        raise SystemExit("connected to a REPLICA — refusing to DDL. Check Pgpool.")

    cur.execute(LIVE_INDEXES, (SCHEMA,))
    live = [r[0] for r in cur.fetchall()]
    custom = custom_indexes(live)
    print(f"live indexes in {SCHEMA}: {len(live)}")
    print(f"  upstream: {sorted(set(live) & set(STOCK_INDEX_NAMES))}")
    print(f"  CUSTOM  : {custom or '(none — schema is plain)'}")

    if args.list:
        raise SystemExit(0 if not custom else 1)

    targets = custom if args.all_custom else [INDEX]
    if args.all_custom and not custom:
        print("\nnothing to drop — already the plain upstream schema")
    for name in targets:
        if name not in live:
            print(f"\n{name}: absent already")
            continue
        print(f"\ndropping {name}")
        cur.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {SCHEMA}.{name}")
        cur.execute(STATE, (SCHEMA, name))
        row = cur.fetchone()
        #: An interrupted concurrent drop leaves an indisvalid=false row that a
        #: naive existence check passes but the planner never uses -- the audit
        #: would then measure unindexed behaviour while its guard still saw an
        #: index.
        if row:
            raise SystemExit(
                f"STILL PRESENT (valid={row[1]}, ready={row[2]}) — do not "
                "measure yet"
            )
        print(f"  {name}: gone")

    #: Re-read rather than assume. The whole point is a plain schema, and
    #: "I dropped what I meant to" is not the same claim.
    cur.execute(LIVE_INDEXES, (SCHEMA,))
    left = custom_indexes([r[0] for r in cur.fetchall()])
    print(f"\ncustom indexes remaining: {left or '(none — schema is plain)'}")
    if left and args.all_custom:
        raise SystemExit(f"REFUSING to report success — still custom: {left}")

    cur.execute(STATE, (SCHEMA, INDEX))
    print(f"\n{INDEX}:", cur.fetchone() or "absent")

    cur.execute("SELECT count(*) FROM polaris_schema.entities")
    e = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM polaris_schema.grant_records")
    g = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM polaris_schema.principal_authentication_data")
    p = cur.fetchone()[0]
    print(f"\nexact counts now — entities={e}  grant_records={g}  auth_rows={p}")
    print("(02 will write these into the fresh manifest)")
conn.close()
print("\nschema is plain. Restart the kernel before measuring.")
