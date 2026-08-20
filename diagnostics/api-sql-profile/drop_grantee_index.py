"""Drop idx_grant_records_grantee so notebook 02 can measure a clean baseline.

Exists because 02's own instructions are circular from a cold kernel: the DROP
lives in the final cell, but reaching that cell requires passing the section-5
guard, which is what refuses to run while the index exists.

Safe to re-run: IF EXISTS, and it verifies the result rather than assuming it.
CONCURRENTLY cannot run inside a transaction, hence autocommit.
"""
import os

import psycopg2

PG = dict(
    host=os.environ.get("PG_HOST", "192.168.139.2"),
    port=int(os.environ.get("PG_PORT", "5432")),
    dbname=os.environ.get("PG_DB", "polaris"),
    user=os.environ.get("PG_USER", "polaris"),
    password=os.environ.get("PG_PASSWORD", "polaris"),
)
SCHEMA, INDEX = "polaris_schema", "idx_grant_records_grantee"

STATE = """
SELECT c.relname, i.indisvalid, i.indisready
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
JOIN pg_index i ON i.indexrelid = c.oid
WHERE n.nspname = %s AND c.relname = %s
"""

conn = psycopg2.connect(**PG)
conn.autocommit = True  # DROP INDEX CONCURRENTLY refuses a transaction block
with conn.cursor() as cur:
    cur.execute("SELECT pg_is_in_recovery()")
    if cur.fetchone()[0]:
        raise SystemExit("connected to a REPLICA — refusing to DDL. Check Pgpool.")

    cur.execute(STATE, (SCHEMA, INDEX))
    print("before:", cur.fetchone() or "absent")

    cur.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {SCHEMA}.{INDEX}")

    cur.execute(STATE, (SCHEMA, INDEX))
    row = cur.fetchone()
    print("after :", row or "absent")

    # An interrupted concurrent drop leaves an indisvalid=false row that a
    # naive existence check passes but the planner never uses — 02 would then
    # measure unindexed behaviour while the guard still saw an index.
    if row:
        raise SystemExit(f"STILL PRESENT (valid={row[1]}, ready={row[2]}) — do not run 02 yet")

    cur.execute("SELECT count(*) FROM polaris_schema.entities")
    e = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM polaris_schema.grant_records")
    g = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM polaris_schema.principal_authentication_data")
    p = cur.fetchone()[0]
    print(f"\nexact counts now — entities={e}  grant_records={g}  auth_rows={p}")
    print("(02 will write these into the fresh manifest)")
conn.close()
print("\nindex dropped. Restart the kernel, then Restart & Run All on 02.")
