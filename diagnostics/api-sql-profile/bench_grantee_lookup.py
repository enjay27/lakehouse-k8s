#!/usr/bin/env python3
"""50 rows out of 500K, index OFF vs ON. The core query, at production volume.

    python3 bench_grantee_lookup.py                    # default 500,000 rows
    python3 bench_grantee_lookup.py --rows 500000
    python3 bench_grantee_lookup.py --rows 500000 --keep-filler

THE QUERY UNDER TEST
--------------------
Every authenticated Polaris request runs the grantee lookup in its authorization
prelude: "give me the grants held by THIS principal". A principal owns ~50 grants
-- but they sit in a `grant_records` table that, at production scale, holds
~500,000 rows. So the shape is: return 50 rows, from 500,000, on every call.

    SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id,
           privilege_code
    FROM grant_records
    WHERE grantee_id = %s AND realm_id = %s AND grantee_catalog_id = %s

`grant_records`' only index is its composite PRIMARY KEY, and a lookup by
grantee constrains PK positions 1,4,5 -- leaving 2,3 free, so only `realm_id` is
a usable prefix = the whole table in a single-realm deployment. Without
`idx_grant_records_grantee` the planner has no covering path and must Seq Scan.

WHAT THIS MEASURES, AND WHAT IT DOES NOT
----------------------------------------
It measures the SAME query, returning the SAME ~50 rows, at the SAME volume,
with the index absent and present. The difference is purely the access path:

  * ABSENT: Seq Scan -- reads every one of the 500,000 rows (every PAGE), throws
    away all but ~50. Cost is CONSTANT in the 50; it is dominated by the table.
  * PRESENT: Index Scan -- reads ~50 rows. Cost tracks rows RETURNED.

That contrast is the whole argument for the index, and it is carried by
plan-shape, buffer counts and rows-filtered -- numbers identical across every
run. Timings are reported too, but as illustration: this repo has watched the
same plan measure a 4.6x spread on clock alone.

PARALLELISM IS PINNED FOR THE COMPARISON, AND THE ESCALATION IS NOTED SEPARATELY
-------------------------------------------------------------------------------
At 500K an unindexed Seq Scan escalates to a PARALLEL Gather, and 02b measured
those timings as unusable -- identical plan cost and buffers, 3-10x spread. So
for an apples-to-apples index-vs-no-index number this pins
`max_parallel_workers_per_gather = 0` (session-scoped, reversible, NOT an ALTER
SYSTEM). The fact that the unindexed path WOULD go parallel on every
authenticated request -- burning worker slots, and this cluster's 64MB /dev/shm
is where that has bitten before -- is a worse operational story than latency and
is reported on its own.
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

import api_sweep  # noqa: E402
import grant_scale  # noqa: E402
import run_manifest  # noqa: E402

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
        if cur.fetchone()[0]:
            sys.exit("routed to a STANDBY; EXPLAIN must run on the primary")
    return conn


def _describe(m):
    return (
        f"{m['path']}\n"
        f"       rows returned {m['rows_returned']}, "
        f"filtered {m['rows_filtered'] or 0:,}\n"
        f"       total cost {m['total_cost']:,.1f}, "
        f"buffers hit {m['shared_hit'] or 0:,} read {m['shared_read'] or 0:,}\n"
        f"       explain-analyze ms: median {m['ms']:.3f} "
        f"({m['min']:.3f}..{m['max']:.3f})"
    )


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--rows",
        type=int,
        default=500_000,
        help="target grant_records row count (default 500,000)",
    )
    ap.add_argument(
        "--keep-filler",
        action="store_true",
        help="leave the filler in place after measuring",
    )
    args = ap.parse_args()

    conn = connect()
    try:
        grant_scale.assert_filler_range_is_safe(conn, SCHEMA)
        base = grant_scale.total_rows(conn, SCHEMA)
        print(f"baseline: {base:,} real grant_records")

        # Pick the probe FIRST, on the real data, and require it real. "50 rows"
        # must be a real principal's grant set, not filler -- resolve_probes
        # excludes filler (grantee_id >= 0) exactly so this cannot silently
        # measure a synthetic grantee.
        probe = grant_scale.resolve_probes(conn, SCHEMA, REALM, targets=(50,))[0]
        if probe.get("synthetic"):
            print("\nNo real grantee near 50 grants exists yet. Seed the fixture")
            print("(50 users, 50 grants/role) before running this -- otherwise")
            print("the '50 rows' half of '50 from 500K' is fabricated.")
            return 2
        print(
            f"probe   : {probe['label']} — a REAL grantee holding "
            f"{probe['rows']} grants"
        )

        need = args.rows - grant_scale.total_rows(conn, SCHEMA)
        if need > 0:
            print(f"\nfilling to {args.rows:,} rows (+{need:,} filler)...")
            grant_scale.insert_filler(conn, SCHEMA, REALM, need)
        api_sweep.compact(conn, SCHEMA, "grant_records")
        bloat = api_sweep.table_bloat(conn, SCHEMA, "grant_records")
        print(
            f"at volume: {grant_scale.total_rows(conn, SCHEMA):,} rows, "
            f"{bloat['pages']:,} pages "
            f"({bloat['total_bytes'] / 1e6:.0f} MB)"
        )

        # Pin parallelism for the comparison so both sides are serial and the
        # only difference is the access path.
        grant_scale.set_parallelism(conn, 0)
        print("max_parallel_workers_per_gather pinned to 0 for the comparison\n")

        results = {}
        for present in (False, True):
            label = "WITH index" if present else "WITHOUT index"
            grant_scale.set_index(conn, SCHEMA, present)
            api_sweep.compact(conn, SCHEMA, "grant_records")
            m = grant_scale.measure(conn, SCHEMA, REALM, probe)
            results[present] = m
            print(f"{label}:\n       {_describe(m)}\n")

        off, on = results[False], results[True]
        print("=" * 64)
        print("THE INDEX EFFECT ON THIS QUERY, AT THIS VOLUME")
        print("=" * 64)
        print(f"  plan shape   : {off['path']}")
        print(f"              -> {on['path']}")
        buf_off = (off["shared_hit"] or 0) + (off["shared_read"] or 0)
        buf_on = (on["shared_hit"] or 0) + (on["shared_read"] or 0)
        print(
            f"  buffers read : {buf_off:,} -> {buf_on:,} "
            f"({buf_off / max(buf_on, 1):.0f}x fewer pages touched)"
        )
        print(
            f"  rows scanned : filters {off['rows_filtered'] or 0:,} away to "
            f"return {off['rows_returned']}  ->  reads ~{on['rows_returned']}"
        )
        if on["ms"]:
            print(
                f"  explain time : {off['ms']:.3f} ms -> {on['ms']:.3f} ms "
                f"({off['ms'] / on['ms']:.0f}x) -- illustration, not the "
                f"headline; see buffers"
            )
        print()
        print("  The buffer and rows-filtered numbers are the argument: the")
        print("  unindexed lookup reads the WHOLE table to return ~50 rows, on")
        print("  every authenticated request. They are identical across runs;")
        print("  the millisecond ratio is not, which is why it is the footnote.")

        # Escalation note: what the unindexed path does WITHOUT the pin.
        print("\n" + "=" * 64)
        print("SEPARATELY — what the unindexed path does in PRODUCTION")
        print("=" * 64)
        grant_scale.set_index(conn, SCHEMA, False)
        grant_scale.set_parallelism(conn, 4)  # a realistic default
        api_sweep.compact(conn, SCHEMA, "grant_records")
        esc = grant_scale.measure(conn, SCHEMA, REALM, probe)
        grant_scale.set_parallelism(conn, 0)
        if esc["parallel"]:
            print(f"  Unpinned, the Seq Scan ESCALATES to parallel: {esc['path']}")
            print("  So the grantee lookup consumes worker slots on every")
            print("  authenticated request. On this cluster /dev/shm is 64MB and")
            print("  parallel DSM exhaustion there is already documented -- that")
            print("  is a worse story than latency and belongs upstream on its")
            print("  own, independent of the index.")
        else:
            print(f"  Did not escalate at {args.rows:,} rows: {esc['path']}")
            print("  (02b saw escalation from ~160-233k; row width and stats")
            print("   move the point, so quote it with this fixture.)")
    finally:
        print()
        # Leave the index PRESENT -- the remediated state the rest of the
        # directory assumes.
        grant_scale.set_index(conn, SCHEMA, True)
        if not args.keep_filler:
            removed = grant_scale.delete_filler(conn, SCHEMA)
            api_sweep.compact(conn, SCHEMA, "grant_records")
            print(
                f"removed {removed:,} filler rows; "
                f"{grant_scale.total_rows(conn, SCHEMA):,} real rows remain, "
                f"index left present"
            )
        else:
            print(
                f"--keep-filler: {grant_scale.total_rows(conn, SCHEMA):,} rows "
                "remain (filler included), index left present. "
                "Remove with sql_fill.py --remove."
            )
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
