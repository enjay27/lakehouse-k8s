#!/usr/bin/env python3
"""Seed the Polaris metastore with the index-audit fixture, from a terminal.

WHY A CLI AND NOT JUST THE NOTEBOOK
-----------------------------------
Notebook 01 can run this (cells 10-12, RUN_SEED = True). But the seed is
~42,000 API calls over 30-60 minutes at the default 50 grants per role, and a
notebook cell that long is exposed
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
`owner_principal` role holding **50 catalog-scoped privileges** -- the
production shape. Two namespaces per catalog, five tables per namespace.

    --grants-per-role N   defaults to 50 everywhere. Pass a smaller n for a
                          thin fixture; `catalog_privileges` slices the
                          spec-ordered enum, so any larger n is a strict
                          superset of any smaller one.

    --no-tables   (DEFAULT) metadata only: ~10x faster, skips 10,000 Iceberg
                  tables and their MinIO objects, but STILL fully populates
                  grant_records (~50,000 granted rows at the default 50
                  grants/role) -- which is the table the grantee-index
                  hypothesis is actually about.
    --tables      the full fixture. Slower, and heavier on connections:
                  PostgreSQL max_connections is 100 against a JDBC pool of 300.

USAGE
-----
    python3 seed_polaris.py                 # 1000 users x 50 grants, no tables
    python3 seed_polaris.py --users 200     # a smaller trial run first
    python3 seed_polaris.py --tables        # full fixture
    python3 seed_polaris.py --teardown      # remove everything it created
    python3 seed_polaris.py --verify        # count what is actually there
    nohup python3 seed_polaris.py > seed.log 2>&1 &

Interrupt it with Ctrl-C at any time; re-run to continue from the ledger.

PRODUCTION GRANT VOLUME
-----------------------
25 grants per role is not a production shape; a real catalog role holds ~50, so
50 is what a fresh seed writes -- in ONE pass, not a 25-grant seed followed by
25,000 more PUTs into the same table.

The upgrade path is for a fixture that ALREADY EXISTS: it raises it in place
rather than rebuilding (a rebuild costs far more and re-triggers the non-atomic
catalog bug), and touches grant_records only:

    python3 seed_polaris.py --probe-privileges          # FIRST: what does this
                                                        # build actually accept?
    python3 seed_polaris.py --upgrade-grants --dry-run  # the per-role diff
    python3 seed_polaris.py --upgrade-grants            # ~26,000 calls, ~20 min
    python3 seed_polaris.py --verify --grants-per-role 50
    python3 seed_polaris.py --revert-grants             # back to the 25 baseline

Run `ANALYZE grant_records` after ANY of these, the seed included. Without it
the planner works from stale reltuples and may pick a plan the data no longer
justifies — which looks exactly like a finding.

A LEDGER CAN OUTRANK THE TARGET
-------------------------------
`seed()` skips every user the ledger marks done, and the ledger records only
THAT a user was built, not how many grants it got. A 50-grant seed resumed
against a 25-grant ledger therefore writes nothing and reports "1,000 skipped"
— a fixture 25,000 rows short, in the table under audit, that reads as success.
This refuses instead, and prints the two ways out. See
`polaris_seed.ledger_shortfall`.
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
    delete_catalog_fully,
    ensure_catalog,
    find_strays,
    ledger_shortfall,
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

#: Grants per `owner_principal` role, for EVERY path this CLI offers.
#: 50 is the production shape (a real catalog role holds roughly that many);
#: `CORE_CATALOG_PRIVILEGES`' 25 remain the revert target and the meaning of
#: "baseline" in every ledger and report written before this default changed.
GRANTS_PER_ROLE_DEFAULT = 50


def ledger_path(prefix="user"):
    """The ledger for THIS fixture. Per-prefix, and it has to be.

    `Ledger.done_users` is a set of bare user INDEXES -- it records that user 7
    was built, never which fixture user 7 belonged to. One shared file
    therefore makes every fixture after the first a no-op: seeding 100 `authz`
    principals against a ledger holding `user` 1..1000 skips all 100 and
    reports

        seeded=0 skipped=100 failed=0

    which is indistinguishable from "already done" and was followed, before
    this fix, by a cheerful "Next: ..." (measured 2026-08-24 -- it cost two
    seeding runs that created nothing).

    `user` keeps the original unsuffixed filename so the existing 1,000-user
    fixture, its `grant_upgrades` record and every report that references it
    still resolve.
    """
    name = "seed_ledger.json" if prefix == "user" else f"seed_ledger-{prefix}.json"
    for c in (HERE / "capture" / name, REPO / "capture" / name):
        if c.exists():
            return c
    d = HERE / "capture"
    d.mkdir(parents=True, exist_ok=True)
    return d / name


def refuse_on_foreign_ledger(lp, prefix):
    """Refuse a ledger that belongs to a DIFFERENT fixture.

    Belt and braces beside the per-prefix path: the path can still be pointed
    somewhere by hand, and the failure mode is silent. A ledger whose spec
    names another prefix cannot say anything about this one's users.
    """
    import json as _json

    if not lp.exists():
        return
    try:
        spec = (_json.loads(lp.read_text(encoding="utf-8")) or {}).get("spec") or {}
    except (ValueError, OSError):
        return
    recorded = spec.get("prefix")
    if recorded and recorded != prefix:
        sys.exit(
            f"ledger at {lp} was written for prefix {recorded!r}, but this run\n"
            f"targets {prefix!r}. Its user indexes describe {recorded!r} users, so every\n"
            f"{prefix!r} user would be SKIPPED and the run would report success\n"
            "having created nothing.\n"
            f"    use this fixture's own ledger:  capture/seed_ledger-{prefix}.json\n"
            f"    or move the foreign one aside:  mv {lp.name} {lp.stem}-{recorded}.json"
        )


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


def refuse_on_short_ledger(lp, target):
    """Exit rather than run a seed the ledger will silently under-deliver.

    `seed()` skips every user the ledger marks done and the ledger does not
    record how many grants each got, so a 50-grant seed resumed against a
    25-grant ledger writes NOTHING, reports "1,000 skipped", and leaves the
    table under audit 25,000 rows short. Printing the two ways out is the
    whole point -- a bare refusal would just get worked around.
    """
    short = ledger_shortfall(str(lp), target)
    if not short:
        return
    n_short, recorded, n_done = short
    print(f"REFUSING to seed: the ledger cannot deliver {target} grants/role.")
    print()
    print(f"  {lp}")
    print(f"  records {n_done} finished user(s) at {recorded} grants per role,")
    print(f"  {n_short} of which have not been upgraded to {target}.")
    print()
    print("  seed() SKIPS every user the ledger marks done, so this run would")
    print(f"  write nothing and report {n_done} skipped, leaving the fixture")
    print(f"  ~{n_short * (target - recorded):,} grant_records rows short — short in")
    print("  the one table the audit is about, and looking like success.")
    print()
    print("  raise the existing fixture:")
    print(f"      python3 seed_polaris.py --upgrade-grants --grants-per-role {target}")
    print("  or build a new one from scratch:")
    print(f"      mv {lp} {lp}.{recorded}grants")
    sys.exit(2)


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
    #: The full-surface fixture (2026-08-24). All default to the existing
    #: fixture's shape, so a bare `seed_polaris.py` still seeds exactly what it
    #: seeded before.
    ap.add_argument(
        "--views-per-namespace",
        type=int,
        default=0,
        help="create N views per namespace. Without them loadView/headView "
        "have no target and are UNDRIVEABLE — a fixture gap, not a 404.",
    )
    ap.add_argument(
        "--policies-per-namespace",
        type=int,
        default=0,
        help="create N policies per namespace. Feature-flagged in 1.3; a "
        "refusal is recorded once as a disabled feature, not retried per user.",
    )
    ap.add_argument(
        "--generic-tables-per-namespace",
        type=int,
        default=0,
        help="create N generic tables per namespace. Feature-flagged in 1.3.",
    )
    ap.add_argument(
        "--service-admin",
        action="store_true",
        help="assign the bootstrapped `service_admin` principal-role to every "
        "seeded principal. THE ONLY route to service-level authorization — the "
        "1.3.0 management API has no service-level grant type. Note it makes "
        "each principal resolve ~1 grant per catalog in the realm (~1,100 "
        "here) instead of ~50, so such a fixture is NOT footprint-comparable "
        "with a catalog-scoped one. Seed it separately.",
    )
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
        "--cleanup-probes",
        nargs="?",
        const="privprobe-",
        default=None,
        metavar="PREFIX",
        help="delete catalogs left behind by a failed teardown. Defaults to "
        "the privprobe- prefix; pass another (e.g. --cleanup-probes wtc) to "
        "clean a different one. Run before taking a baseline.",
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
        default=GRANTS_PER_ROLE_DEFAULT,
        help=f"target grants per owner_principal role (default "
        f"{GRANTS_PER_ROLE_DEFAULT}, the production shape). Applies to every "
        f"path — seed, --upgrade-grants and --verify alike. Pass a smaller n "
        f"for a thin fixture; --revert-grants always returns to the "
        f"{len(CORE_CATALOG_PRIVILEGES)}-name baseline.",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="with --upgrade-grants: report the per-role diff, write nothing.",
    )
    args = ap.parse_args()

    # ONE default for every path. The old split -- 25 for a seed, 50 for the
    # upgrade -- made the documented flow permanently two passes: write 25,000
    # grant_records rows, then PUT 25,000 more into the same table. It also
    # meant `--verify` and the seed disagreed about what the fixture was
    # supposed to be unless the operator remembered to pass the flag twice.
    #
    # `catalog_privileges(n)` slices the spec-ordered enum, so 50 is a strict
    # SUPERSET of the 25 an existing fixture holds (test_polaris_seed pins
    # that). The upgrade stays additive; --revert-grants still returns to the
    # 25-name CORE baseline, which is what every older ledger and report means
    # by "baseline".
    target = args.grants_per_role
    spec_privileges = catalog_privileges(target)
    upgrade_target = target

    spec = SeedSpec(
        n_users=args.users,
        namespaces_per_catalog=2,
        tables_per_namespace=5,
        create_tables=args.tables,
        views_per_namespace=args.views_per_namespace,
        policies_per_namespace=args.policies_per_namespace,
        generic_tables_per_namespace=args.generic_tables_per_namespace,
        assign_service_admin=args.service_admin,
        prefix=args.prefix,
        privileges=spec_privileges,
    )
    lp = ledger_path(args.prefix)

    # BEFORE connect(): a ledger that cannot deliver the target is a local
    # fact, and refusing on it needs no cluster. Only the seed path is
    # affected -- every other mode either reads the fixture or rewrites the
    # grants directly, and none of them consult `Ledger.done_users`.
    seeding = not any(
        (
            args.cleanup_probes,
            args.probe_privileges,
            args.upgrade_grants,
            args.revert_grants,
            args.verify,
            args.teardown,
        )
    )
    if seeding:
        refuse_on_foreign_ledger(lp, args.prefix)
        refuse_on_short_ledger(lp, target)

    pc, ic = connect()

    print(f"polaris : {POLARIS_URL}  realm={REALM}")
    print(f"ledger  : {lp}")
    print(
        f"fixture : {args.users} users, tables={args.tables}, "
        f"{len(spec_privileges)} grants/role"
    )
    print(f"expected: {spec.expected_counts()}")
    print()

    if args.cleanup_probes:
        sys.exit(cleanup_probes(pc, args.cleanup_probes))

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
    elif res.completed_users == 0 and res.skipped_users:
        # `seeded=0 skipped=N failed=0` is not success. Two causes, and the
        # output has to say which rather than printing a "Next:" that implies
        # a fixture exists.
        print(f"\nNOTHING WAS CREATED — all {res.skipped_users} users were skipped.")
        print(f"  The ledger at {lp} already records those user indexes.")
        print("  Either this fixture is already seeded — check with")
        print(f"      python3 seed_polaris.py --verify --prefix {spec.prefix}")
        print("  or the ledger belongs to a different fixture, in which case")
        print("  move it aside and re-run.")
    else:
        if res.features_off:
            # Feature-flagged off on this build. A fact about the deployment,
            # so `--verify` will report a shortfall that is NOT a seeding fault.
            print(f"\nFEATURE(S) NOT CREATED: {sorted(res.features_off)}")
            for kind, why in sorted(res.feature_errors.items()):
                print(f"  {kind}: {why}")
            print(
                "  Those entities do not exist and --verify will show a "
                "shortfall.\n"
                "  A 404/501 is the FEATURE being off. Any other status is the "
                "PAYLOAD\n"
                "  being wrong — which is the seeder's fault, not the "
                "deployment's."
            )
        if res.service_admin_failures:
            print(
                f"\n{len(res.service_admin_failures)} principals did NOT get "
                "service_admin."
                "\n  They are still valid catalog-scoped identities, but the "
                "service-level"
                "\n  reads will 403 for them — the probe will show it."
            )
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
    res = None
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
        # Always, and thoroughly. The first version of this called
        # `delete_catalog(purge=True)` directly, got a 400, printed the status
        # code and threw the body away -- leaving the catalog, its role and 51
        # grant_records rows on the cluster, where they showed up in the next
        # baseline as a 51-row grantee that nobody would have remembered.
        ok, d = delete_catalog_fully(pc, name, result)
        if not ok:
            print(f"\nWARNING: probe catalog {name} NOT deleted [{d.status_code}]")
            print(f"  {(d.text or '')[:400]}")
            print("  It holds real grant_records rows and will contaminate the")
            print("  next baseline. Remove it before measuring anything:")
            print("      python3 seed_polaris.py --cleanup-probes")

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


def cleanup_probes(pc, prefix="privprobe-"):
    """Remove any catalog matching `prefix` that a failed teardown stranded.

    Defaults to the probe prefix, but takes any prefix — a bare
    `delete_catalog(purge=True)` has now stranded catalogs under two different
    names, so the prefix is a parameter rather than a constant.

    Prefix-scoped and local-only, like everything else here. Read the list it
    prints before answering yes to anything -- this deletes catalogs.

    Returns a process exit code: 0 = nothing left behind.
    """
    result = SeedResult()
    r = pc.list_catalogs()
    if r.status_code >= 300:
        print(f"cannot list catalogs [{r.status_code}]: {r.text[:200]}")
        return 1
    names = sorted(
        c.get("name")
        for c in (r.json() or {}).get("catalogs", [])
        if str(c.get("name", "")).startswith(prefix)
    )
    if not names:
        print(f"no {prefix}* catalogs found; nothing to clean.")
        return 0

    print(f"found {len(names)} stranded catalog(s) under {prefix!r}: {names}")
    failed = []
    for n in names:
        ok, d = delete_catalog_fully(pc, n, result)
        print(f"  {n}: {'deleted' if ok else f'FAILED [{d.status_code}]'}")
        if not ok:
            print(f"    {(d.text or '')[:400]}")
            failed.append(n)
    if failed:
        print("\nStill present:", failed)
        print("The body above is the thing to read -- the previous attempt")
        print("reported only a status code, which is why this happened twice.")
        return 1
    print("\nclean. Re-take the baseline before measuring anything:")
    print("      python3 baseline_grants.py")
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
