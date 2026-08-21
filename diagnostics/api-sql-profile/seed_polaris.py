#!/usr/bin/env python3
"""Seed the Polaris metastore with the index-audit fixture, from a terminal.

WHY A CLI AND NOT JUST THE NOTEBOOK
-----------------------------------
Notebook 01 can run this (cells 10-12, RUN_SEED = True). But the seed is
~17,000 API calls over 10-30 minutes, and a notebook cell that long is exposed
to kernel restarts, browser sleep, and losing the output buffer. Running it here
keeps the notebook for the part that actually needs to be interactive -- the
trace and the EXPLAIN work -- and lets the seed survive a closed laptop under
`nohup`.

It writes the SAME ledger file the notebooks use, so the three are
interchangeable and resumable across each other: start here, finish in 01,
re-run either, nothing is created twice.

FIXTURE (project decision #9)
-----------------------------
1,000 principals, each with a principal-role, a catalog, a catalog-role, and an
`owner_principal` role holding all catalog privileges. Two namespaces per
catalog, five tables per namespace.

    --no-tables   (DEFAULT) metadata only: ~10x faster, skips 10,000 Iceberg
                  tables and their MinIO objects, but STILL fully populates
                  grant_records (~25,000 rows) -- which is the table the
                  grantee-index hypothesis is actually about.
    --tables      the full fixture. Slower, and heavier on connections:
                  PostgreSQL max_connections is 100 against a JDBC pool of 300.

USAGE
-----
    python3 seed_polaris.py                 # default 1000 users, no tables
    python3 seed_polaris.py --users 200     # a smaller trial run first
    python3 seed_polaris.py --tables        # full fixture
    python3 seed_polaris.py --teardown      # remove everything it created
    python3 seed_polaris.py --verify        # count what is actually there
    nohup python3 seed_polaris.py > seed.log 2>&1 &

Interrupt it with Ctrl-C at any time; re-run to continue from the ledger.

PRODUCTION GRANT VOLUME
-----------------------
25 grants per role is not a production shape; a real catalog role holds ~50.
These raise an EXISTING fixture rather than rebuilding it (a rebuild costs far
more and re-triggers the non-atomic catalog bug), and touch grant_records only:

    python3 seed_polaris.py --probe-privileges          # FIRST: what does this
                                                        # build actually accept?
    python3 seed_polaris.py --upgrade-grants --dry-run  # the per-role diff
    python3 seed_polaris.py --upgrade-grants            # ~26,000 calls, ~20 min
    python3 seed_polaris.py --verify --grants-per-role 50
    python3 seed_polaris.py --revert-grants             # back to the baseline

Run `ANALYZE grant_records` after any of these. Without it the planner works
from stale reltuples and may pick a plan the data no longer justifies — which
looks exactly like a finding.
"""

import argparse
import os
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE
while not (REPO / "src").is_dir() and REPO != REPO.parent:
    REPO = REPO.parent
sys.path.insert(0, str(REPO / "src"))

from iceberg_rest import IcebergREST  # noqa: E402
from polaris_rest import PolarisREST  # noqa: E402

# noqa: E402 applies to this block too; it is attached to the two imports above
# rather than inside the parentheses because isort relocates an inline comment
# on the first name and black then re-wraps it onto that name, which reads as a
# noqa for CATALOG_PRIVILEGES alone. Neither tool converges on the other's form
# (no [tool.isort] profile is set), so this block is written for black, which
# runs last.
from polaris_seed import (
    CATALOG_PRIVILEGES,
    CORE_CATALOG_PRIVILEGES,
    SeedResult,
    SeedSpec,
    call_with_lag_retry,
    catalog_privileges,
    ensure_catalog,
    find_strays,
    probe_privileges,
    revert_grants,
    seed,
    teardown,
    upgrade_grants,
    verify_counts,
)

# --- local cluster; secrets from env with visible defaults -------------------
POLARIS_URL = os.environ.get("POLARIS_URL", "http://192.168.139.2:8181")
REALM = os.environ.get("POLARIS_REALM", "POLARIS")
ROOT_CLIENT = os.environ.get("POLARIS_ROOT_CLIENT", "root")
ROOT_SECRET = os.environ.get("POLARIS_ROOT_SECRET", "polaris-secret")
MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "http://192.168.139.2:9000")
BUCKET = os.environ.get("MINIO_BUCKET", "data-catalog-bucket")


def ledger_path():
    """The same file the notebooks use, wherever their capture dir landed."""
    for c in (
        HERE / "capture" / "seed_ledger.json",
        REPO / "capture" / "seed_ledger.json",
    ):
        if c.exists():
            return c
    d = HERE / "capture"
    d.mkdir(parents=True, exist_ok=True)
    return d / "seed_ledger.json"


def connect():
    if not any(h in POLARIS_URL for h in ("localhost", "127.0.0.1", "192.168.")):
        sys.exit(f"refusing to seed a non-local Polaris: {POLARIS_URL}")
    pc = PolarisREST(POLARIS_URL, REALM)
    r = pc.get_token(ROOT_CLIENT, ROOT_SECRET)
    if r.status_code >= 300:
        sys.exit(f"auth failed [{r.status_code}]: {r.text[:200]}")
    pc.token = r.json()["access_token"]
    return pc, IcebergREST(POLARIS_URL, REALM, token=pc.token)


def make_progress(total):
    t0 = time.time()
    state = {"last": 0}

    def on_progress(done, _total, result):
        if done - state["last"] < 25 and done != total:
            return
        state["last"] = done
        el = time.time() - t0
        rate = done / el if el else 0
        eta = (total - done) / rate if rate else 0
        print(
            f"  {done:>5}/{total}  {el:6.0f}s elapsed  ~{eta:5.0f}s left  "
            f"{result.calls / max(el, 0.001):5.0f} calls/s",
            flush=True,
        )

    return on_progress


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--users", type=int, default=1000)
    ap.add_argument(
        "--tables",
        dest="tables",
        action="store_true",
        help="also create 10,000 Iceberg tables (slow)",
    )
    ap.add_argument("--no-tables", dest="tables", action="store_false")
    ap.set_defaults(tables=False)
    ap.add_argument("--prefix", default="user")
    ap.add_argument("--teardown", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument(
        "--upgrade-grants",
        action="store_true",
        help="additively raise every owner_principal role to --grants-per-role "
        "(default 50). ~26,000 calls, ~15-25 min, writes grant_records only.",
    )
    ap.add_argument(
        "--revert-grants",
        action="store_true",
        help=f"revoke everything above the {len(CORE_CATALOG_PRIVILEGES)}-name "
        "baseline, undoing --upgrade-grants.",
    )
    ap.add_argument(
        "--probe-privileges",
        action="store_true",
        help="find out which privilege names THIS build accepts, on one "
        "throwaway catalog. Run before any bulk grant pass.",
    )
    ap.add_argument(
        "--grants-per-role",
        type=int,
        default=None,
        help="target grants per owner_principal role. Defaults to 50 for "
        f"--upgrade-grants and to the {len(CORE_CATALOG_PRIVILEGES)}-name "
        "baseline everywhere else. Pass it with --verify to check counts "
        "against an upgraded fixture.",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="with --upgrade-grants: report the per-role diff, write nothing.",
    )
    args = ap.parse_args()

    # One flag, two defaults: the spec keeps today's 25-grant shape unless
    # asked otherwise, while the upgrade pass targets 50. Resolving both from
    # `None` here means --verify --grants-per-role 50 checks the upgraded
    # fixture, instead of reporting a 25,000-row shortfall that is not real.
    spec_privileges = (
        catalog_privileges(args.grants_per_role)
        if args.grants_per_role
        else list(CORE_CATALOG_PRIVILEGES)
    )
    upgrade_target = args.grants_per_role or 50

    spec = SeedSpec(
        n_users=args.users,
        namespaces_per_catalog=2,
        tables_per_namespace=5,
        create_tables=args.tables,
        prefix=args.prefix,
        privileges=spec_privileges,
    )
    lp = ledger_path()
    pc, ic = connect()

    print(f"polaris : {POLARIS_URL}  realm={REALM}")
    print(f"ledger  : {lp}")
    print(
        f"fixture : {args.users} users, tables={args.tables}, "
        f"{len(spec_privileges)} grants/role"
    )
    print(f"expected: {spec.expected_counts()}")
    print()

    if args.probe_privileges:
        sys.exit(probe(pc))

    if args.upgrade_grants:
        sys.exit(upgrade(pc, spec, lp, upgrade_target, args))

    if args.revert_grants:
        sys.exit(revert(pc, spec, lp, args))

    if args.verify:
        sys.exit(verify(pc, spec, args))

    if args.teardown:
        res = teardown(
            pc,
            ledger_path=str(lp),
            spec=spec,
            progress_every=25,
            on_progress=make_progress(args.users),
        )
        print(res.summary())
        return

    t0 = time.time()
    # bucket/minio_endpoint are ALWAYS required, regardless of --tables.
    # create_catalog takes them as positional arguments because every catalog
    # needs a storage config (default-base-location + allowedLocations) whether
    # or not any table is ever created inside it. Passing None when --no-tables
    # was my error and produced 50 identical TypeErrors.
    res = seed(
        pc,
        ic,
        spec,
        ledger_path=str(lp),
        bucket=BUCKET,
        minio_endpoint=MINIO_ENDPOINT,
        progress_every=25,
        on_progress=make_progress(args.users),
    )
    print()
    print(res.summary())
    print(f"wall: {time.time() - t0:.0f}s")

    if res.lag_recovered:
        # Polaris rejected a call whose prerequisite was written milliseconds
        # earlier -- read-after-write lag on PG-HA, surfacing as 500/403/404.
        # Report it by OPERATION, not as a share of all calls: "4.1% of calls"
        # buried the fact that two thirds of namespace creates were affected,
        # because 25 privilege grants per user diluted the denominator.
        from collections import Counter

        per_op = Counter(e["what"].split()[0] for e in res.lag_recovered)
        per_status = Counter(e["status"] for e in res.lag_recovered)
        attempted = {
            "create_namespace": args.users * 2,
            "create_catalog": args.users,
            "create_catalog_role": args.users,
            "create_principal": args.users,
            "create_principal_role": args.users,
            "assign_principal_role": args.users,
            "assign_catalog_role": args.users,
        }
        print(
            f"\nrecovered from {len(res.lag_recovered)} lag failures "
            f"(entity was there, or the retry succeeded):"
        )
        for op, k in per_op.most_common():
            tot = attempted.get(op)
            rate = f"{100.0 * k / tot:5.1f}% of {tot}" if tot else ""
            print(f"    {k:>6}x  {op:<24} {rate}")
        print("    by status:", dict(sorted(per_status.items())))
        dups = sum(1 for e in res.lag_recovered if e.get("reason") == "duplicate")
        if dups:
            # These are writes that had ALREADY landed -- usually on an earlier
            # attempt of this same script. Counted as success, not failure.
            print(f"    of which {dups} were duplicate-key (already written,")
            print("      treated as done rather than retried into the PK)")
        worst = max(
            (100.0 * k / attempted[o] for o, k in per_op.items() if o in attempted),
            default=0,
        )
        if worst > 25:
            print(f"    NOTE: {worst:.0f}% on the worst operation is high enough")
            print("    to distort timing measurements. Consider routing reads to")
            print("    the primary (Pgpool) before trusting per-API latency.")

    if res.repaired_catalogs:
        # Catalogs that existed but had no catalog_admin -- the entity write
        # committed while the grant bootstrap did not. Deleted and recreated,
        # because there is no endpoint that can add the missing role.
        print(
            f"\nrepaired {len(res.repaired_catalogs)} half-created catalogs "
            "(deleted + recreated):"
        )
        for c in res.repaired_catalogs[:10]:
            print(f"    {c}")
        if len(res.repaired_catalogs) > 10:
            print(f"    ... and {len(res.repaired_catalogs) - 10} more")

    if res.invalid_privileges:
        # Fewer grants than projected means grant_records is smaller than the
        # audit assumes -- say so rather than letting a thin fixture quietly
        # produce a TOO_SMALL verdict that reads like a pass.
        print("\nWARNING: this Polaris build rejected these privilege names:")
        print("  ", sorted(set(res.invalid_privileges)))
        print("  grant_records volume is LOWER than projected.")
    if res.failed_users:
        print(f"\n{len(res.failed_users)} users failed; re-run to retry them.")
        print("  first 10:", res.failed_users[:10])

    if res.failed_users:
        print("\nNOT seeded — fix the errors above and re-run (the ledger will")
        print("skip whatever did succeed). Check for partial residue with:")
        print("      python3 seed_polaris.py --verify")
    else:
        print("\nNext: in notebook 01 leave RUN_SEED = False (this already seeded),")
        print("      then run it to trace the API surface at real volume.")


# ---------------------------------------------------------------------------
# grant volume
# ---------------------------------------------------------------------------
def probe(pc):
    """Ask the DEPLOYED build which privilege names it accepts.

    `CATALOG_PRIVILEGES` is transcribed from the 1.3.0 spec, and a spec is not
    a running server. Granting an unknown name 1,000 times and inferring it
    from the shortfall is the expensive way to find out; this costs one
    throwaway catalog and ~51 calls.

    Returns a process exit code: 0 = every candidate accepted.
    """
    result = SeedResult()
    name = f"privprobe-{int(time.time())}"
    print(f"probing {len(CATALOG_PRIVILEGES)} candidate names on {name}\n")
    try:
        ensure_catalog(pc, name, BUCKET, MINIO_ENDPOINT, result)
        ok, r = call_with_lag_retry(
            lambda: pc.create_catalog_role(name, "probe_role"),
            "create_catalog_role",
            result,
        )
        if not ok:
            print(f"could not create the probe role: {r.status_code} {r.text[:160]}")
            return 1
        res = probe_privileges(pc, name, "probe_role")
    finally:
        # Always: a leftover probe catalog is exactly the residue the entities
        # count is being watched for.
        d = pc.delete_catalog(name, purge=True)
        if d.status_code >= 300 and d.status_code != 404:
            print(f"WARNING: probe catalog {name} not deleted ({d.status_code}).")

    print(f"accepted: {len(res['accepted'])}/{len(CATALOG_PRIVILEGES)}")
    if res["rejected"]:
        print(f"\nREJECTED by this build ({len(res['rejected'])}):")
        for k, v in res["rejected"].items():
            print(f"    {k:<32} {v}")
        print("\nThe measured list is the authority, not the spec. Trim")
        print("CATALOG_PRIVILEGES to the accepted names, or the upgrade pass")
        print("will fall short by (rejected x 1,000) rows and the shortfall")
        print("will look like a Polaris behaviour.")
        return 1
    print("every candidate accepted; CATALOG_PRIVILEGES is safe to use in full.")
    return 0


def upgrade(pc, spec, lp, target, args):
    """Additively raise every owner_principal role to `target` grants."""
    t0 = time.time()
    if args.dry_run:
        print("DRY RUN — reading the per-role diff, writing nothing.\n")
    res = upgrade_grants(
        pc,
        spec,
        grants_per_role=target,
        ledger_path=str(lp),
        progress_every=25,
        on_progress=make_progress(args.users),
        dry_run=args.dry_run,
    )
    print()
    print(res.summary())
    print(f"wall: {time.time() - t0:.0f}s")

    if args.dry_run:
        print(f"\nwould add {res.grants_added} grant_records rows across")
        print(f"{res.completed_users} roles ({res.skipped_users} already at target).")
        print("Re-run without --dry-run to write them.")
        return 0

    if res.invalid_privileges:
        # Fewer rows than projected, with a stated cause. Say it loudly: a
        # quiet shortfall in the table under audit reads as a finding.
        print("\nWARNING: this build rejected these privilege names:")
        print("  ", sorted(set(res.invalid_privileges)))
        print("  grant_records volume is LOWER than projected. Run")
        print("  --probe-privileges and trim CATALOG_PRIVILEGES before")
        print("  quoting any count from this fixture.")
    if res.failed_users:
        print(f"\n{len(res.failed_users)} roles incomplete; re-run to retry them")
        print("(the ledger skips the ones that finished).")
        print("  first 5:", res.failed_users[:5])
        return 1

    print(f"\nadded {res.grants_added} rows to grant_records.")
    print("Next: ANALYZE grant_records (the planner is working from stale")
    print("reltuples until you do), then --verify --grants-per-role", target)
    return 0


def revert(pc, spec, lp, args):
    """Undo the upgrade: revoke everything above the baseline."""
    t0 = time.time()
    res = revert_grants(
        pc,
        spec,
        ledger_path=str(lp),
        progress_every=25,
        on_progress=make_progress(args.users),
    )
    print()
    print(res.summary())
    print(f"wall: {time.time() - t0:.0f}s")
    if res.failed_users:
        print(f"\n{len(res.failed_users)} roles incomplete; re-run to retry them.")
        print("  first 5:", res.failed_users[:5])
        return 1
    print(f"\nrevoked {res.grants_revoked} rows. Run ANALYZE grant_records.")
    return 0


# ---------------------------------------------------------------------------
# verification
# ---------------------------------------------------------------------------
# The Pgpool service is a LoadBalancer, so PostgreSQL is reachable directly --
# no port-forward. Note this is the POOLER, not a node: it load-balances reads
# across replicas, so a count taken here can lag the primary by a moment. Fine
# for verification (a real gap does not heal itself); NOT fine for EXPLAIN,
# which must run on the primary -- see notebook 02.
PG = dict(
    host=os.environ.get("PG_HOST", "192.168.139.2"),
    port=int(os.environ.get("PG_PORT", "5432")),
    dbname=os.environ.get("PG_DB", "polaris"),
    user=os.environ.get("PG_USER", "polaris"),
    password=os.environ.get("PG_PASSWORD", "polaris"),
)
SCHEMA = os.environ.get("PG_SCHEMA", "polaris_schema")


def _load_metastore(realm):
    """Every seeded entity + per-catalog grant counts, in two queries.

    Straight from PostgreSQL rather than 6,000 REST calls: the fixture exists
    to create metastore rows, so the metastore is the authority, and this
    finishes in under a second instead of several minutes.
    """
    import psycopg2

    conn = psycopg2.connect(**PG)
    conn.autocommit = True
    with conn.cursor() as cur:
        # Which node did the pooler actually give us? A standby read can lag,
        # so say so rather than letting a stale count read as a missing entity.
        cur.execute("SELECT pg_is_in_recovery(), inet_server_addr()")
        standby, addr = cur.fetchone()
        _load_metastore.node = f"{addr}{' (standby)' if standby else ' (primary)'}"
        cur.execute(
            f"SELECT id, catalog_id, parent_id, type_code, name "  # noqa: S608
            f"FROM {SCHEMA}.entities WHERE realm_id = %s",
            (realm,),
        )
        ents = cur.fetchall()
        cur.execute(
            f"SELECT securable_catalog_id, count(*) FROM {SCHEMA}.grant_records "  # noqa: S608
            f"WHERE realm_id = %s GROUP BY 1",
            (realm,),
        )
        grants = dict(cur.fetchall())
    conn.close()
    return ents, grants


def verify(pc, spec, args):
    """Check that EVERY expected entity exists, per user, not just totals.

    Totals hide the failure mode this fixture actually hits: a catalog whose
    entity committed while its catalog_admin role did not. The counts look
    close to right, and the catalog is permanently unusable. So this checks
    each user's full set and reports which indices are incomplete and how.

    Returns a process exit code: 0 = complete, 1 = gaps found.
    """
    realm = REALM
    try:
        ents, grants = _load_metastore(realm)
        source = (
            f"PostgreSQL {PG['host']}:{PG['port']} -> "
            f"{getattr(_load_metastore, 'node', '?')}"
        )
    except Exception as e:  # noqa: BLE001
        print(f"cannot reach PostgreSQL ({str(e).splitlines()[0][:90]})")
        print(f"  expected the Pgpool LoadBalancer at {PG['host']}:{PG['port']}")
        print("  override with PG_HOST / PG_PORT / PG_USER / PG_PASSWORD")
        print("\nfalling back to REST stray listing only:")
        print(
            "strays by prefix:",
            {k: len(v) for k, v in find_strays(pc, prefix=args.prefix).items()},
        )
        return 1

    # Index by PARENT, not just by catalog. Every descendant of a catalog
    # carries the same catalog_id -- roles, namespaces and tables alike -- so a
    # single per-catalog name set cannot tell ns1/tbl1 from ns2/tbl1. Table
    # names repeat in every namespace, so parent_id is the only thing that
    # distinguishes them.
    by_name = {}  # top-level entities, keyed by name
    by_parent = {}  # parent_id -> {name: id}
    for _id, cat_id, parent, _tc, name in ents:
        by_name.setdefault(name, []).append((_id, cat_id))
        by_parent.setdefault(parent, {})[name] = _id

    cat_ids = {}
    for i in range(spec.start_index, spec.start_index + spec.n_users):
        hit = by_name.get(spec.names(i)["catalog"])
        if hit:
            cat_ids[i] = hit[0][0]

    missing = {
        k: []
        for k in (
            "principal",
            "principal_role",
            "catalog",
            "catalog_admin",
            "owner_role",
            "namespaces",
            "tables",
            "grants",
        )
    }
    tables_found = 0

    for i in range(spec.start_index, spec.start_index + spec.n_users):
        n = spec.names(i)
        if n["principal"] not in by_name:
            missing["principal"].append(i)
        if n["principal_role"] not in by_name:
            missing["principal_role"].append(i)

        cid = cat_ids.get(i)
        if cid is None:
            missing["catalog"].append(i)
            continue

        kids = by_parent.get(cid, {})
        # catalog_admin is the one that silently goes missing when the entity
        # write commits but the grant bootstrap does not.
        if "catalog_admin" not in kids:
            missing["catalog_admin"].append(i)
        if n["catalog_role"] not in kids:
            missing["owner_role"].append(i)

        for ns in n["namespaces"]:
            ns_id = kids.get(ns)
            if ns_id is None:
                missing["namespaces"].append(f"{i}/{ns}")
                if spec.create_tables:
                    # No namespace means none of its tables can exist either;
                    # count them so the table total is not quietly optimistic.
                    missing["tables"] += [f"{i}/{ns}/{t}" for t in n["tables"]]
                continue
            # Tables hang off the NAMESPACE, not the catalog.
            tkids = by_parent.get(ns_id, {})
            tables_found += len(tkids)
            if spec.create_tables:
                for tbl in n["tables"]:
                    if tbl not in tkids:
                        missing["tables"].append(f"{i}/{ns}/{tbl}")

        if grants.get(cid, 0) == 0:
            missing["grants"].append(i)

    total_users = spec.n_users
    exp = spec.expected_counts()
    print(f"source  : {source}")
    print(
        f"realm   : {realm}   users {spec.start_index}.."
        f"{spec.start_index + total_users - 1}"
    )
    print(
        f"entities: {len(ents)} rows   grant_records: {sum(grants.values())} "
        f"(expected ~{exp['entities_total']} / ~{exp['grant_records']})"
    )
    exp_tables = (
        (total_users * spec.namespaces_per_catalog * spec.tables_per_namespace)
        if spec.create_tables
        else 0
    )
    print(
        f"tables  : {tables_found} found under seeded namespaces "
        f"(expected {exp_tables})"
    )
    if not spec.create_tables:
        # State it rather than showing a silent zero: a metadata-only fixture is
        # a deliberate choice, and "0 tables" should not read as a failure.
        print("          fixture is metadata-only (--no-tables); tables are not")
        print("          expected. Re-run with --tables to build and check them.")
        if tables_found:
            print(
                f"          NOTE: {tables_found} table(s) present anyway — "
                "left over from an earlier --tables run or the probe fixture."
            )
    print()
    print(f"  {'check':<16} {'ok':>6} {'missing':>8}")
    ok_all = True
    for key, bad in missing.items():
        denom = total_users
        if key == "namespaces":
            denom = total_users * spec.namespaces_per_catalog
        elif key == "tables":
            denom = exp_tables
        if denom == 0:
            continue
        good = denom - len(bad)
        flag = "" if not bad else "  <-- INCOMPLETE"
        print(f"  {key:<16} {good:>6} {len(bad):>8}{flag}")
        if bad:
            ok_all = False
            print(f"      {bad[:15]}{' ...' if len(bad) > 15 else ''}")

    print()
    if ok_all:
        print("COMPLETE — every expected entity is present.")
        print("The fixture is sound; proceed to notebook 01 (RUN_SEED = False).")
        return 0

    if "standby" in getattr(_load_metastore, "node", ""):
        print("NOTE: this read came from a STANDBY via the pooler. A handful of")
        print("      very recent entities could still be replicating. Re-run to")
        print("      confirm before treating a small gap as real.")
        print()
    print("INCOMPLETE — re-run the seeder to fill the gaps:")
    print("    python3 seed_polaris.py")
    print("Half-created catalogs (catalog_admin missing) are deleted and")
    print("recreated automatically on that run.")
    return 1


if __name__ == "__main__":
    main()
