#!/usr/bin/env python3
"""Give `grant_records` a production-shaped volume, in SQL, in seconds.

WHY THIS IS SEPARATE FROM seed_polaris.py
-----------------------------------------
`seed_polaris.py` creates REAL entities over REST: principals, catalogs, roles,
grants that Polaris resolves and serves. This creates SYNTHETIC rows in
`grant_records` and nothing else. Keeping them in two files keeps the two ideas
apart, because conflating them is how a synthetic number ends up quoted as a
measured one.

WHAT IT IS FOR, AND WHAT IT IS NOT
----------------------------------
A Seq Scan cannot tell a row inserted here from one created over REST -- same
plan, same buffers, same timing. That is precisely why this is sufficient for
the grant_records index question, and precisely why every number derived from it
must be disclosed as synthetic.

It is NOT a substitute for the REST fixture. These rows match no entity, so
Polaris never resolves, serves or caches them. Anything that reads through the
API -- 03's read-cache profile, the privilege suites -- needs real entities.

    10,000 users over REST : ~610,000 API calls, ~8.5 hours, ~250 half-created
                             catalogs to repair, and a teardown later that
                             leaves ~70,000 unreaped TASK rows
    10,000 users here      : one INSERT per band, seconds

SAFETY
------
Filler lives in the NEGATIVE id space. `PLAN-grant-scale-sweep.md` reserved
`>= 1_000_000_000`, which sits BELOW every real Polaris id (they are
snowflake-style, ~10^18) -- the documented cleanup would have deleted the whole
fixture. `--status` and every write path assert the disjointness against live
data before touching anything.

USAGE
-----
    python3 sql_fill.py --status                  # what is there now
    python3 sql_fill.py --users 10000 --dry-run   # print the SQL, write nothing
    python3 sql_fill.py --users 10000             # add a 10,000-user shape
    python3 sql_fill.py --probe 10006             # one grantee holding N rows
    python3 sql_fill.py --remove                  # delete every synthetic row

`ANALYZE grant_records` runs automatically after any change: without it the
planner works from a `reltuples` the data no longer supports and may choose a
plan the table no longer justifies, which looks exactly like a finding.
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

import grant_scale  # noqa: E402

PG = dict(
    host=os.environ.get("PG_HOST", "192.168.139.2"),
    port=int(os.environ.get("PG_PORT", "5432")),
    dbname=os.environ.get("PG_DB", "polaris"),
    user=os.environ.get("PG_USER", "polaris"),
    password=os.environ.get("PG_PASSWORD", "polaris"),
)
SCHEMA = os.environ.get("PG_SCHEMA", "polaris_schema")
REALM = os.environ.get("POLARIS_REALM", "POLARIS")


def connect():
    import psycopg2

    if not any(h in PG["host"] for h in ("localhost", "127.0.0.1", "192.168.")):
        sys.exit(f"refusing to write to a non-local PostgreSQL: {PG['host']}")
    conn = psycopg2.connect(**PG)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("/*NO LOAD BALANCE*/ SELECT pg_is_in_recovery()")
        standby = cur.fetchone()[0]
    if standby:
        sys.exit(
            "the pooler routed this session to a STANDBY, which is read-only "
            "and would report counts that lag the primary. Connect to the "
            "primary directly: PG_HOST=<primary-pod-ip>"
        )
    return conn


def status(conn):
    """Counts and the grantee histogram, real and synthetic side by side."""
    safety = grant_scale.assert_filler_range_is_safe(conn, SCHEMA)
    total = grant_scale.total_rows(conn, SCHEMA)
    filler = grant_scale.filler_count(conn, SCHEMA)
    print(f"grant_records : {total:>10,} rows")
    print(f"  real        : {total - filler:>10,}")
    print(f"  synthetic   : {filler:>10,}")
    print(
        f"  reltuples   : {grant_scale.reltuples(conn, SCHEMA):>10,}  "
        "(planner's estimate; drifts until ANALYZE)"
    )
    print(f"\nsmallest real ids: {safety['real_minimums']}")
    print("  all >= 0, so `WHERE grantee_id < 0` touches only synthetic rows")

    with conn.cursor() as cur:
        cur.execute(
            f"""/*NO LOAD BALANCE*/
            WITH g AS (SELECT grantee_id, count(*) n FROM {SCHEMA}.grant_records
                       WHERE realm_id = %s GROUP BY 1)
            SELECT n, count(*) FILTER (WHERE grantee_id >= 0),
                      count(*) FILTER (WHERE grantee_id <  0)
            FROM g GROUP BY n ORDER BY count(*) DESC LIMIT 12""",  # noqa: S608
            (REALM,),
        )
        rows = cur.fetchall()
    print(f"\n{'rows held':>10} {'real grantees':>14} {'synthetic':>11}")
    for n, real, synth in rows:
        print(f"{n:>10,} {real:>14,} {synth:>11,}")
    return 0


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--status", action="store_true")
    ap.add_argument(
        "--users",
        type=int,
        help="add the grant_records shape of an N-user realm "
        "(2N+2 grantees holding 1 row, N holding 2, N holding --grants-per-role)",
    )
    ap.add_argument("--grants-per-role", type=int, default=50)
    ap.add_argument(
        "--probe",
        type=int,
        help="create ONE synthetic grantee holding exactly N rows, for probing "
        "a point on the rows-returned axis the real fixture does not occupy",
    )
    ap.add_argument("--remove", action="store_true", help="delete every synthetic row")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not any((args.status, args.users, args.probe, args.remove)):
        ap.error("nothing to do — pass --status, --users, --probe or --remove")

    if args.dry_run and args.users:
        shape = grant_scale.production_shape(args.users, args.grants_per_role)
        print(
            f"-- {args.users:,} simulated users = "
            f"{grant_scale.shape_rows(shape):,} rows, one statement per band"
        )
        print(f"-- bands (grantees x rows each): {shape}\n")
        print(grant_scale.shaped_insert_sql(SCHEMA))
        print("\n-- then, always:")
        print(f"ANALYZE {SCHEMA}.grant_records;")
        print("\n-- and to undo, the ONLY predicate needed:")
        print(f"DELETE FROM {SCHEMA}.grant_records WHERE grantee_id < 0;")
        return 0

    conn = connect()
    try:
        if args.status:
            return status(conn)

        # Every write path proves the sentinel range is disjoint from real data
        # first. The cost of being wrong is deleting the fixture.
        grant_scale.assert_filler_range_is_safe(conn, SCHEMA)
        before = grant_scale.total_rows(conn, SCHEMA)

        if args.remove:
            removed = grant_scale.delete_filler(conn, SCHEMA)
            print(f"removed {removed:,} synthetic rows")
        if args.users:
            shape = grant_scale.production_shape(args.users, args.grants_per_role)
            print(
                f"{args.users:,} simulated users -> "
                f"{grant_scale.shape_rows(shape):,} rows"
            )
            res = grant_scale.insert_shaped_filler(
                conn, SCHEMA, REALM, shape, on_progress=lambda ln: print(ln, flush=True)
            )
            print(f"inserted {res['total']:,}")
        if args.probe:
            grant_scale.ensure_probe_grantee(conn, SCHEMA, REALM, args.probe)
            print(f"probe grantee holds {args.probe:,} rows")

        grant_scale.analyze(conn, SCHEMA)
        after = grant_scale.total_rows(conn, SCHEMA)
        print(f"\ngrant_records {before:,} -> {after:,} ({after - before:+,})")
        print(f"reltuples now {grant_scale.reltuples(conn, SCHEMA):,} (ANALYZE ran)")
        print("\nThese rows are SYNTHETIC. Disclose that beside every number")
        print("derived from them, not once in a preamble.")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
