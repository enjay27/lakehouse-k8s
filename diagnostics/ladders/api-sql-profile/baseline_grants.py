"""The before/after baseline for the grant-volume upgrade. Read-only.

WHY THIS EXISTS
---------------
`--upgrade-grants` moves `grant_records` from ~30,009 to ~55,009. Every claim
made afterwards -- about the index, about the scaling sweep, about production
shape -- rests on knowing precisely what the table looked like first. Taking
that by hand, twice, in a hurry, is how a number gets misremembered.

Run it BEFORE the upgrade and AFTER it, and diff the two JSON snapshots.

    python3 baseline_grants.py                 # print + write baselines/<ts>.json
    python3 baseline_grants.py --no-write      # print only

It also carries the Phase B pre-flight gate: whether `grant_records` has a
foreign key to `entities`. Polaris emits no JOINs anywhere, which suggests none
exists -- but that is an inference from query shape, and if one DOES exist the
sweep's filler-row design is dead. It costs one query, so it is asked here
rather than discovered later.

EVERYTHING RUNS ON THE PRIMARY. Pgpool load-balances reads across replicas and a
standby can lag, so a count taken there can disagree with the primary for
reasons that have nothing to do with the fixture. `/*NO LOAD BALANCE*/` pins
each statement, and `pg_is_in_recovery()` is asserted False rather than trusted.
"""

import argparse
import datetime
import json
import os
import pathlib

import psycopg2

HERE = pathlib.Path(__file__).resolve().parent

PG = dict(
    host=os.environ.get("PG_HOST", "192.168.139.2"),
    port=int(os.environ.get("PG_PORT", "5432")),
    dbname=os.environ.get("PG_DB", "polaris"),
    user=os.environ.get("PG_USER", "polaris"),
    password=os.environ.get("PG_PASSWORD", "polaris"),
)
SCHEMA = os.environ.get("PG_SCHEMA", "polaris_schema")
REALM = os.environ.get("POLARIS_REALM", "POLARIS")
INDEX = "idx_grant_records_grantee"

# Pgpool routes on the leading comment, so it must come first in the statement.
NLB = "/*NO LOAD BALANCE*/ "


def q(cur, sql, args=None):
    cur.execute(NLB + sql, args)
    return cur.fetchall()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--no-write", action="store_true", help="print only")
    args = ap.parse_args()

    snap = {
        "taken_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "realm": REALM,
        "schema": SCHEMA,
    }
    conn = psycopg2.connect(**PG)
    conn.autocommit = True
    with conn.cursor() as cur:
        standby, addr = q(cur, "SELECT pg_is_in_recovery(), inet_server_addr()")[0]
        snap["node"] = str(addr)
        snap["is_standby"] = bool(standby)
        print(f"node: {addr}  {'STANDBY' if standby else 'primary'}")
        assert not standby, (
            "this read landed on a STANDBY despite /*NO LOAD BALANCE*/. A "
            "lagging replica will produce counts that disagree with the primary "
            "for reasons unrelated to the fixture. Fix the routing before "
            "recording a baseline from it."
        )

        # --- exact counts. Never n_live_tup: it is an estimate that drifts
        # after bulk changes until the next ANALYZE, which is exactly the state
        # this table will be in right after the upgrade.
        counts = {}
        for t in ("entities", "grant_records", "principal_authentication_data"):
            counts[t] = q(cur, f"SELECT count(*) FROM {SCHEMA}.{t}")[0][0]  # noqa: S608
        snap["exact_counts"] = counts
        print("\nexact counts:")
        for t, n in counts.items():
            print(f"  {t:<32} {n:>10,}")

        # --- and the planner's view of the same table, so the drift between
        # them is visible rather than assumed. A large gap here means ANALYZE
        # has not run and any plan measured now is being chosen from stale
        # statistics -- which looks exactly like a finding.
        rows = q(
            cur,
            """SELECT c.relname, c.reltuples::bigint, s.last_analyze, s.last_autoanalyze
               FROM pg_class c
               JOIN pg_namespace n ON n.oid = c.relnamespace
               LEFT JOIN pg_stat_user_tables s ON s.relid = c.oid
               WHERE n.nspname = %s AND c.relname IN ('entities','grant_records')""",
            (SCHEMA,),
        )
        snap["reltuples"] = {r[0]: r[1] for r in rows}
        print("\nplanner statistics (reltuples vs exact):")
        for name, reltup, la, laa in rows:
            exact = counts.get(name, 0)
            drift = reltup - exact
            when = la or laa
            print(
                f"  {name:<20} reltuples {reltup:>10,}  exact {exact:>10,}  "
                f"drift {drift:>+8,}   last analyze: {when or 'never'}"
            )

        # --- the grantee distribution. THIS is the number the whole index
        # argument turns on: the Seq Scan cost is constant in grantee size while
        # the index scan tracks rows returned, so the speedup varies across this
        # distribution rather than being a single ratio.
        dist = q(
            cur,
            f"""WITH g AS (
                    SELECT grantee_catalog_id, grantee_id, count(*) AS n
                    FROM {SCHEMA}.grant_records WHERE realm_id = %s
                    GROUP BY 1, 2)
                SELECT count(*), min(n),
                       percentile_disc(0.5)  WITHIN GROUP (ORDER BY n),
                       percentile_disc(0.95) WITHIN GROUP (ORDER BY n),
                       max(n), sum(n)
                FROM g""",  # noqa: S608
            (REALM,),
        )[0]
        keys = ("grantees", "min", "p50", "p95", "max", "total_rows")
        snap["grantee_distribution"] = dict(zip(keys, [int(x or 0) for x in dist]))
        print("\ngrantee distribution:")
        for k, v in snap["grantee_distribution"].items():
            print(f"  {k:<12} {v:>10,}")

        # --- the histogram is what CONFIRMS the overhead model rather than
        # assuming it. `SeedSpec` projects 5 non-privilege rows per user; the
        # hypothesis is 1 principal role-assignment + 1 principal-role ->
        # catalog-role assignment + 3 catalog_admin bootstrap grants. If that is
        # right, this shows ~2,000 grantees holding 1 row, ~1,000 holding 3, and
        # ~1,000 holding len(privileges). If it is not, the shape says so.
        hist = q(
            cur,
            f"""WITH g AS (
                    SELECT grantee_catalog_id, grantee_id, count(*) AS n
                    FROM {SCHEMA}.grant_records WHERE realm_id = %s
                    GROUP BY 1, 2)
                SELECT n, count(*) FROM g GROUP BY n ORDER BY count(*) DESC
                LIMIT 15""",  # noqa: S608
            (REALM,),
        )
        snap["grantee_histogram"] = {int(n): int(c) for n, c in hist}
        print("\ngrants-per-grantee histogram (top 15 by frequency):")
        print(f"  {'rows held':>10} {'grantees':>10} {'= rows':>12}")
        for n, c in hist:
            print(f"  {n:>10,} {c:>10,} {n * c:>12,}")

        # --- relation sizes. The index's size relative to the PK is part of the
        # cost being proposed upstream, and it changes when the table grows.
        sizes = q(
            cur,
            """SELECT c.relname, pg_relation_size(c.oid)
               FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
               WHERE n.nspname = %s
                 AND c.relname IN ('grant_records','grant_records_pkey', %s)""",
            (SCHEMA, INDEX),
        )
        snap["relation_bytes"] = {r[0]: int(r[1]) for r in sizes}
        print("\nrelation sizes:")
        for name, b in sizes:
            print(f"  {name:<32} {b/1024:>10,.0f} kB")

        # --- index state. Presence alone is not enough: an interrupted
        # CREATE/DROP INDEX CONCURRENTLY leaves indisvalid = false, which passes
        # a naive existence check while the planner ignores it.
        st = q(
            cur,
            """SELECT i.indisvalid, i.indisready
               FROM pg_class c
               JOIN pg_index i ON i.indexrelid = c.oid
               JOIN pg_namespace n ON n.oid = c.relnamespace
               WHERE n.nspname = %s AND c.relname = %s""",
            (SCHEMA, INDEX),
        )
        snap["index"] = (
            {"name": INDEX, "present": False, "valid": False, "ready": False}
            if not st
            else {
                "name": INDEX,
                "present": True,
                "valid": bool(st[0][0]),
                "ready": bool(st[0][1]),
            }
        )
        print(f"\n{INDEX}: {snap['index']}")

        # --- THE PHASE B GATE. If a foreign key to `entities` exists, filler
        # rows with synthetic grantee ids cannot be inserted and the sweep's
        # ceiling drops to what REST can create (~110k rows).
        fks = q(
            cur,
            """SELECT conname, confrelid::regclass::text, pg_get_constraintdef(oid)
               FROM pg_constraint
               WHERE conrelid = %s::regclass AND contype = 'f'""",
            (f"{SCHEMA}.grant_records",),
        )
        snap["foreign_keys"] = [
            {"name": a, "references": b, "definition": c} for a, b, c in fks
        ]
        print("\nPhase B gate — foreign keys on grant_records:")
        if not fks:
            print("  NONE. Filler rows with synthetic grantee ids are viable.")
        else:
            for a, b, c in fks:
                print(f"  {a} -> {b}: {c}")
            print("  A FK EXISTS. The sweep's filler-row design does not survive")
            print("  this; fall back to pure-REST volume and say so in the report.")
    conn.close()

    if not args.no_write:
        d = HERE / "baselines"
        d.mkdir(parents=True, exist_ok=True)
        # Deliberately NOT runs/: `run_manifest.list_runs` globs runs/*.json and
        # treats every stem as a run id, so a snapshot dropped in there would be
        # picked up by `load_run(..., None)` as the newest manifest and fail in
        # a confusing place.
        path = d / f"{snap['taken_at'].replace(':', '').replace('-', '')}.json"
        path.write_text(json.dumps(snap, indent=2), encoding="utf-8")
        print(f"\nwrote {path}")
        print("Take this again after the upgrade and diff the two.")


if __name__ == "__main__":
    main()
