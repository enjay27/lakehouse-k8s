#!/usr/bin/env python3
"""At what row count does the grantee lookup stop using an index?

    python3 find_scan_crossover.py            # measure, then clean up
    python3 find_scan_crossover.py --keep     # leave the filler in place

WHY THIS RUNS BEFORE THE NEXT SWEEP
-----------------------------------
The 2026-08-22 sweep spent six restarts and produced nothing, for one reason:
every cell -- index present AND absent -- planned an **Index Only Scan**. At
3,064 `grant_records` the primary key covers the grantee query, so dropping
`idx_grant_records_grantee` changed nothing the planner did. The Seq Scan the
whole audit is about never appeared.

Notebook 02 saw a Seq Scan at 30,009 rows. This run saw an index scan at 3,064.
The crossover is somewhere in between and **nobody has measured it**. Picking
sweep volumes without that number is guessing, and guessing costs six restarts
and forty minutes per attempt.

This costs neither. No API calls, no restarts, no Polaris involvement at all --
just `EXPLAIN` against progressively more rows.

WHY FILLER AND NOT CLONES
-------------------------
The crossover is a property of `grant_records` row count alone. Clones exist to
move `entities` as well, which matters for LIST endpoints and costs ~16 INSERT
round trips per clone. Filler is one bulk `INSERT ... SELECT generate_series`
and reaches 600,000 rows in seconds.

Filler lives in the NEGATIVE id space and is removed with `grantee_id < 0`,
disjoint from clones and from real data. `resolve_probes` deliberately excludes
it when choosing what to measure, so the probe is a REAL grantee throughout --
what changes between steps is only how much unrelated data it has to scan past.

WHAT IT CANNOT TELL YOU
-----------------------
Nothing about latency. Plan shape and buffer counts only. That is the point:
those were reproducible across every run of 02 while its timings moved 4.6x.
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

#: Geometric, because the crossover is a cost comparison and cost is roughly
#: linear in pages -- a linear ladder would spend most of its steps in the
#: region the last run already proved uninformative.
LADDER = (5_000, 10_000, 20_000, 40_000, 80_000, 160_000, 320_000, 640_000)


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


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--volumes", help="comma-separated row counts")
    ap.add_argument("--keep", action="store_true", help="leave the filler behind")
    args = ap.parse_args()
    ladder = [int(x) for x in args.volumes.split(",")] if args.volumes else list(LADDER)

    conn = connect()
    try:
        state = run_manifest.index_state(conn, SCHEMA, grant_scale.INDEX_NAME)
        if state["present"]:
            print(f"{grant_scale.INDEX_NAME} is PRESENT — dropping it.")
            print("  The question is what the planner does WITHOUT it; leaving it")
            print("  in place would measure the index, not the crossover.")
            grant_scale.set_index(conn, SCHEMA, False)

        grant_scale.assert_filler_range_is_safe(conn, SCHEMA)
        base = grant_scale.total_rows(conn, SCHEMA)
        print(f"baseline: {base:,} grant_records (real rows, kept throughout)\n")

        print(
            f"{'target':>9} {'actual':>9} {'pages':>8} {'cost':>10} "
            f"{'buffers':>8} {'filtered':>10}  plan"
        )
        rows = []
        for target in ladder:
            have = grant_scale.total_rows(conn, SCHEMA)
            need = target - have
            if need > 0:
                grant_scale.insert_filler(conn, SCHEMA, REALM, need)
            # VACUUM FULL, not ANALYZE: a Seq Scan reads PAGES, and top-ups
            # leave the relation larger than its row count implies. The
            # crossover is a page-count comparison, so the page count has to be
            # honest at every step.
            api_sweep.compact(conn, SCHEMA, "grant_records")

            probe = grant_scale.resolve_probes(conn, SCHEMA, REALM, targets=("max",))[0]
            assert not probe["synthetic"], (
                "resolve_probes returned a SYNTHETIC probe — it could not find a "
                "real grantee, so this row would describe the filler rather than "
                "a real identity's lookup"
            )
            m = grant_scale.measure(conn, SCHEMA, REALM, probe)
            bloat = api_sweep.table_bloat(conn, SCHEMA, "grant_records")
            actual = grant_scale.total_rows(conn, SCHEMA)
            rows.append({**m, "rows": actual, "pages": bloat["pages"]})
            print(
                f"{target:>9,} {actual:>9,} {bloat['pages']:>8,} "
                f"{m['total_cost']:>10,.1f} {m['shared_hit'] or 0:>8,} "
                f"{m['rows_filtered'] or 0:>10,}  {m['path']}"
            )

        print("\n" + "=" * 70)
        seq = next((r for r in rows if "Seq Scan" in (r["path"] or "")), None)
        par = next((r for r in rows if r["parallel"]), None)
        if seq:
            print(
                f"SEQ SCAN first appears at ~{seq['rows']:,} rows "
                f"({seq['pages']:,} pages)."
            )
            print("  Below this the primary key covers the query and the index")
            print("  toggle is a no-op — which is exactly what voided the last")
            print("  sweep. Every index-absent cell must sit ABOVE this line.")
        else:
            print("NO Seq Scan at any tested volume. The planner kept using an")
            print("index throughout, so the premise behind the whole index")
            print("contrast needs re-examining before another sweep is run.")
        if par:
            print(f"\nPARALLEL escalation begins at ~{par['rows']:,} rows.")
            print("  02b measured timings becoming unusable past this point —")
            print("  identical plan cost and buffers, 3-10x spread. Run the")
            print("  sweep with SWEEP_PIN_PARALLELISM=1 at or above it, and")
            print("  note the /dev/shm ceiling is 64M on every PostgreSQL pod.")
        else:
            print("\nNo parallel escalation at any tested volume.")

        print("\nPick sweep volumes from this table, not from round numbers:")
        print("  one comfortably BELOW the Seq Scan line (the index-is-moot")
        print("  control), and one or two comfortably above it.")
    finally:
        if not args.keep:
            removed = grant_scale.delete_filler(conn, SCHEMA)
            api_sweep.compact(conn, SCHEMA, "grant_records")
            print(
                f"\nremoved {removed:,} filler rows and compacted; "
                f"{grant_scale.total_rows(conn, SCHEMA):,} rows remain"
            )
        else:
            print(
                "\n--keep: filler left in place. Remove it with "
                "`python3 sql_fill.py --remove` before measuring anything else."
            )
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
