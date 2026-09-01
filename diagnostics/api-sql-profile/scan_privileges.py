#!/usr/bin/env python3
"""Drive the seeded principals through the GET surface, from a terminal.

The runner for `src/privilege_scan.py`. Four modes, in the order you want them:

    python3 scan_privileges.py --list                # what the metastore holds
    python3 scan_privileges.py --footprint           # grants each identity walks
    python3 scan_privileges.py --probe               # ONE identity, all 13 GETs
    python3 scan_privileges.py --drive               # every identity, authorized subset

RUN --probe FIRST, AND READ IT
------------------------------
A `user{N}_principal` holds `owner_principal` on its OWN catalog and nothing
else. The service-level reads -- `GET /principals`, `/principal-roles`,
`/catalogs` -- are expected to 403 for it, and an error path has a latency too:
timing one and putting it in a column headed "ms" reports a 403 as a
performance characteristic. `--probe` costs 13 calls and settles empirically
which operations the drive may include. `--drive` refuses to run without a
probe result on disk, because the alternative is baking an assumption into
~7,000 requests.

THE SECRET IS NOT IN THIS FILE
------------------------------
Export it. There is no default and no prompt:

    export POLARIS_USER_SECRET='...'          # the shared principal secret
    export POLARIS_ROOT_SECRET='...'          # only --footprint needs PG, not this

WHERE IT FITS IN THE TWO-PASS MEASUREMENT
------------------------------------------
    PGDUR=1 ./capture.sh pgon                    # SEPARATE from rotate. See below.
    ./capture.sh rotate capture-scan-noindex     # start the streams AFTER Polaris
                                                 # is ready, or the tail is dead
    ./capture.sh preflight                       # both halves, per pod
    python3 drop_grantee_index.py                # then ANALYZE grant_records
    python3 scan_privileges.py --probe
    python3 scan_privileges.py --drive --capture capture-scan-noindex
    # ... CREATE INDEX CONCURRENTLY, ANALYZE, pgon+rotate again, --drive again
    ./capture.sh pgoff                           # PASS B is a latency pass and
                                                 # belongs to api_sweep, not here

`rotate` DOES NOT ENABLE STATEMENT LOGGING -- 2026-08-24, cost one full pass.
It is `do_stop; do_start`: it restarts the log tails and never touches
`log_statement`, which 02's timing work had correctly left at `'none'` via
`pgoff`. A 9,000-request drive then completed with 1000/1000 and zero errors
into a capture holding 410 bytes -- one line, `Apache Polaris Server stopped`,
because the tail was attached to a pod that restarted three minutes earlier.
Hence `--capture DIR`: one call, then look for ITS output, and refuse the pass
if it is not there.

This runner does NOT time anything. Pass A's clock is discarded (statement
logging inflates it 4.6x, measured), so a scan that reported milliseconds would
be reporting a number nobody may quote.
"""

import argparse
import collections
import json
import os
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE
while not (REPO / "src").is_dir() and REPO != REPO.parent:
    REPO = REPO.parent
sys.path.insert(0, str(REPO / "src"))

import api_sweep  # noqa: E402
import privilege_scan as ps  # noqa: E402
from polaris_rest import PolarisREST  # noqa: E402

POLARIS_URL = os.environ.get("POLARIS_URL", "http://192.168.139.2:8181")
REALM = os.environ.get("POLARIS_REALM", "POLARIS")
#: The active identity tier. Set from --profile in main(); every prefix and op
#: list below derives from it, so the two suites cannot drift apart by one of
#: them being changed and the other forgotten.
PROFILE = ps.PROFILES[ps.DEFAULT_PROFILE]

#: An explicit SCAN_PREFIX still wins, for driving a fixture seeded under a
#: name the profile does not know about.
PREFIX_OVERRIDE = os.environ.get("SCAN_PREFIX")


def prefix():
    return PREFIX_OVERRIDE or PROFILE.prefix


PG = dict(
    host=os.environ.get("PG_HOST", "192.168.139.2"),
    port=int(os.environ.get("PG_PORT", "5432")),
    dbname=os.environ.get("PG_DB", "polaris"),
    user=os.environ.get("PG_USER", "polaris"),
    password=os.environ.get("PG_PASSWORD", "polaris"),
)
SCHEMA = os.environ.get("PG_SCHEMA", "polaris_schema")


#: Where the probe result lives between runs. `--drive` reads it rather than
#: re-probing, so the op set it drove is recoverable from disk afterwards --
#: a report that cannot say which operations were in the denominator is not
#: reporting a distribution.
def probe_path(profile=None):
    """Where THIS profile's probe result lives.

    Per-profile, and it has to be: `--drive` reads the probe to decide which
    operations to issue, so one shared file would let a 29-op service-scoped
    probe select the op set for a 13-op catalog-scoped drive -- silently, since
    both are valid JSON and both name real operations.

    `catalog-scoped` keeps the original unsuffixed filename so the completed
    pass (`privscan-20260824-123408`) still resolves against the probe it was
    actually driven with.
    """
    profile = profile or PROFILE
    if profile.name == ps.DEFAULT_PROFILE:
        return HERE / "capture" / "privscan_probe.json"
    return HERE / "capture" / f"privscan_probe-{profile.name}.json"


RUNS_DIR = HERE / "runs"


def secret_or_exit():
    s = os.environ.get("POLARIS_USER_SECRET")
    if not s:
        sys.exit(
            "POLARIS_USER_SECRET is not set. This is the shared secret every\n"
            "seeded principal authenticates with; it is deliberately not\n"
            "defaulted here (CLAUDE.md: zero hardcoded credentials).\n"
            "    export POLARIS_USER_SECRET='...'"
        )
    return s


def pg_connect():
    import psycopg2

    try:
        conn = psycopg2.connect(**PG)
    except Exception as e:  # noqa: BLE001
        sys.exit(
            f"cannot reach PostgreSQL ({str(e).splitlines()[0][:90]})\n"
            f"  expected the Pgpool LoadBalancer at {PG['host']}:{PG['port']}\n"
            "  override with PG_HOST / PG_PORT / PG_USER / PG_PASSWORD"
        )
    conn.autocommit = True
    return conn


def client():
    return PolarisREST(POLARIS_URL, REALM)


def load(conn, limit=None):
    identities, problems = ps.load_identities(
        conn, SCHEMA, REALM, prefix=prefix(), limit=limit
    )
    if not identities:
        sys.exit(
            f"no seeded identities found for prefix {prefix()!r} in realm {REALM}.\n"
            "  Is the fixture there? python3 seed_polaris.py --verify"
        )
    for reason, names in problems.items():
        if names:
            print(f"  {len(names)} principal(s) excluded — {reason}: {names[:5]}")
    return identities


def ops_for_identity(identity):
    """The full 13-op GET surface, bound to THIS identity's own entities.

    `api_sweep.read_operations` is the single definition of the surface; this
    just supplies a different fixture per identity. Building a second op list
    here is how the two drift apart.
    """
    return PROFILE.ops(identity.fixture())


# ----------------------------------------------------------------------
# modes
# ----------------------------------------------------------------------
def cmd_list(args):
    conn = pg_connect()
    identities = load(conn, args.limit)
    conn.close()
    print(f"{len(identities)} identities, prefix {prefix()!r}, realm {REALM}")
    print()
    print(f"  {'user':>6}  {'client_id':<24} {'catalog':<24} principal-role")
    for i in identities[:10]:
        print(f"  {i.index:>6}  {i.client_id:<24} {i.catalog:<24} {i.principal_role}")
    if len(identities) > 10:
        print(f"  ... and {len(identities) - 10} more")
    return 0


def cmd_footprint(args):
    """How many grant_records each identity's authorization actually walks.

    "Each principal has 50 privileges" is a statement about how the fixture was
    seeded. This is the measurement -- and the distribution is what the index
    effect tracks, since Seq Scan cost is flat while index-scan cost follows
    rows returned.
    """
    conn = pg_connect()
    identities = load(conn, args.limit)
    sample = identities[: args.sample] if args.sample else identities
    print(f"measuring the grant footprint of {len(sample)} identities...")
    sizes = []
    for n, ident in enumerate(sample, start=1):
        sizes.append(
            api_sweep.identity_grant_footprint(conn, SCHEMA, REALM, ident.principal)
        )
        if n % 100 == 0:
            print(f"  {n}/{len(sample)}", flush=True)
    conn.close()

    sizes.sort()
    if not sizes:
        return 1

    def pct(p):
        return sizes[min(len(sizes) - 1, int(len(sizes) * p))]

    print()
    print(f"  n      {len(sizes)}")
    print(f"  min    {sizes[0]}")
    print(f"  p50    {pct(0.50)}")
    print(f"  p95    {pct(0.95)}")
    print(f"  max    {sizes[-1]}")
    distinct = sorted(set(sizes))
    #: "Uniform" means ONE value. The old test was `len(distinct) <= 5`, so a
    #: fixture holding [52, 78] printed "a uniform fixture, as seeded" while
    #: showing two numbers -- reassuring wrongly, which is worse than crying
    #: wolf: nobody investigates a green light. That mattered on 2026-09-01,
    #: when granting authz1 rights on the shared probe catalog moved it from 52
    #: to 78 and made its tier non-uniform, which is exactly the kind of thing
    #: this line exists to surface.
    if len(distinct) == 1:
        print(f"  values {distinct}   (uniform — every identity resolves the same)")
    elif len(distinct) <= 5:
        counts = collections.Counter(sizes)
        spread = ", ".join(f"{v}\u00d7{counts[v]}" for v in distinct)
        print(f"  values {distinct}   (NOT uniform: {spread})")
        print(
            "    A tier whose identities resolve different grant counts is not "
            "footprint-comparable with itself."
        )
        print("    Say WHICH identity a run used, and at what footprint.")
    else:
        print(f"  {len(distinct)} distinct footprints — NOT uniform")
    return 0


def cmd_probe(args):
    secret = secret_or_exit()
    conn = pg_connect()
    identities = load(conn, None)
    conn.close()

    chosen = next((i for i in identities if i.index == args.user), None)
    if chosen is None:
        sys.exit(f"user index {args.user} is not among the loaded identities")

    pc = client()
    token, scope, detail = ps.authenticate(pc, chosen, secret, scope=PROFILE.scope)
    if not token:
        sys.exit(
            f"could not authenticate as {chosen.principal} at scope {scope}:\n"
            f"  {detail}\n"
            "  A non-root principal must request its OWN principal-role, not\n"
            "  PRINCIPAL_ROLE:ALL — but a wrong shared secret looks the same\n"
            "  from here. Check both."
        )
    pc.token = token
    print(f"authenticated as {chosen.principal}  scope={scope}")

    ns, why = ps.resolve_namespace(pc, chosen)
    if not ns:
        sys.exit(f"cannot resolve a namespace in {chosen.catalog}: {why}")
    chosen.namespace = ns
    print(f"namespace       {ns}  (resolved from the API, not assumed)")

    if PROFILE.resolve_entities:
        gone, _statuses = ps.resolve_entities(pc, chosen)
        found = {
            k: getattr(chosen, k)
            for k in ("table", "view", "generic_table", "policy")
            if getattr(chosen, k)
        }
        for k, v in found.items():
            print(f"{k:<15} {v}  (resolved from the API)")
        for k, why in sorted(gone.items()):
            print(f"{k:<15} —  UNDRIVEABLE: {why}")
        if gone:
            print()
            print(
                "  An unresolved kind is a FIXTURE fact, not a refusal. Its "
                "operations\n  below will read `undriveable`, which is "
                "deliberately not a 404 finding."
            )
    print()

    ops = ops_for_identity(chosen)
    statuses = ps.probe_surface(pc, chosen, ops)
    print(ps.render_probe_table(statuses))

    probe_path().parent.mkdir(parents=True, exist_ok=True)
    probe_path().write_text(
        json.dumps(
            {
                "profile": PROFILE.name,
                "probed_user": chosen.index,
                "scope": scope,
                "namespace": ns,
                "authorized": [s.label for s in statuses if s.ok],
                "refused": {s.label: s.status for s in statuses if not s.ok},
                #: The BODY too. A probe that records only the status sends the
                #: next reader back to the cluster to find out why -- which is
                #: what a 400 with no explanation cost on 2026-08-31.
                "refused_detail": {
                    s.label: s.detail for s in statuses if not s.ok and s.detail
                },
                "verdicts": {s.label: s.verdict for s in statuses},
                "at": int(time.time()),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print()
    print(f"probe written to {probe_path()}")
    unexpected = [s for s in statuses if s.status == 0]
    if unexpected:
        print("\nNOTE: some operations raised rather than answering:")
        for s in unexpected:
            print(f"  {s.label}: {s.detail}")
        return 1
    return 0


def cmd_union(args):
    """What the WHOLE suite reaches, across every probe on disk.

    Needs no cluster: it reads the probe files `--probe` already wrote. Exists
    because the two tiers turned out to be COMPLEMENTARY rather than nested --
    `catalog-scoped-full` can vend credentials and cannot read the service
    surface; `service-admin` is the reverse -- so quoting either one's count as
    "the coverage" understates the suite, and intersecting two tables by eye is
    how that gets quoted wrong.
    """
    probes = {}
    for path in sorted((HERE / "capture").glob("privscan_probe*.json")):
        tier = path.stem.replace("privscan_probe-", "")
        if tier == "privscan_probe":
            tier = ps.DEFAULT_PROFILE
        probes[tier] = json.loads(path.read_text(encoding="utf-8"))
    if not probes:
        sys.exit(
            "no probe results on disk. Run --probe for each profile first:\n"
            + "\n".join(
                f"    python3 scan_privileges.py --probe --profile {n}"
                for n in sorted(ps.PROFILES)
            )
        )
    print(f"{len(probes)} probe(s): {', '.join(sorted(probes))}")
    print()
    union = ps.union_verdicts(probes)
    print(ps.render_union(union, probes))
    return 0 if not union["uncovered"] else 1


def cmd_drive(args):
    secret = secret_or_exit()
    if not probe_path().exists():
        sys.exit(
            f"no probe result at {probe_path()}.\n"
            "  Run `python3 scan_privileges.py --probe` first. Driving 7,000\n"
            "  requests against an assumed op set is how a 403 column becomes\n"
            "  a finding."
        )
    probe = json.loads(probe_path().read_text(encoding="utf-8"))
    allowed = set(probe["authorized"])
    if not allowed:
        sys.exit("the probe found NO authorized GET operations; nothing to drive.")
    refused = probe.get("refused", {})
    print(f"driving {len(allowed)} authorized operations per identity")
    print(f"  (probe: user{probe['probed_user']}, scope {probe['scope']})")
    for label, status in sorted(refused.items()):
        print(f"  excluded [{status}]  {label.strip()}")

    #: A refused request still pays the full 7-statement authorization prelude
    #: -- Polaris has to resolve the grants to decide it is a 403 -- so the
    #: grantee lookup fires on the denial path too. Driving a SAMPLE of the
    #: refusals makes that capture evidence instead of a claim read off the
    #: source, which is the precise mistake `cache_verdict` was.
    deny_sample = set()
    if args.deny_sample and refused:
        deny_sample = set(refused)
        print()
        print(
            f"  + the {len(deny_sample)} refused operations, for the first "
            f"{args.deny_sample} identities only, as prelude-on-denial evidence"
        )
    print()

    conn = pg_connect()
    identities = load(conn, args.limit)
    conn.close()

    if args.capture:
        rc = assert_capture_live(args.capture, identities[0], secret)
        if rc:
            return rc
    else:
        print("NO --capture given: this run produces NO index evidence.")
        print("  Pass A must be captured. Only a latency pass runs uncaptured,")
        print("  and this runner does not time anything.")
        print()

    def ops_for(_client, identity):
        wanted = set(allowed)
        if deny_sample and identity.index <= args.deny_sample:
            wanted |= deny_sample
        return [o for o in ops_for_identity(identity) if o[0] in wanted]

    t0 = time.time()
    result = ps.drive(
        client,
        identities,
        secret,
        ops_for,
        on_progress=_progress,
        progress_every=args.progress_every,
        stop_after_auth_failures=args.stop_after_auth_failures,
        tolerated_labels=deny_sample,
        resolve_entity_targets=PROFILE.resolve_entities,
        auth_scope=PROFILE.scope,
    )
    print()
    print(result.summary())

    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    run_id = time.strftime("%Y%m%d-%H%M%S")
    out = RUNS_DIR / f"privscan-{run_id}.json"
    out.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "realm": REALM,
                "prefix": prefix(),
                "profile": PROFILE.name,
                "probe": probe,
                "identities": result.identities,
                "authenticated": result.authenticated,
                "requests": result.requests,
                "auth_failures": result.auth_failures,
                "skipped": result.skipped,
                "unresolved": result.unresolved,
                "errors": [list(e) for e in result.errors],
                "status_counts": {
                    label: buckets
                    for label, buckets in ps.status_matrix(
                        result, ops_for_identity(identities[0])
                    ).items()
                },
                "elapsed_s": round(time.time() - t0, 1),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"run written to {out}")
    print()
    print(ps.render_scan_report(result, ops_for_identity(identities[0])))

    if result.unresolved:
        print()
        print("entity targets that did NOT resolve (fixture facts, not refusals):")
        for kind, reasons in sorted(result.unresolved.items()):
            for why, n in sorted(reasons.items(), key=lambda kv: -kv[1]):
                print(f"  {kind:<15} {n:>5} identities — {why}")

    if result.errors or result.auth_failures or result.skipped:
        print()
        print("NOT a clean pass. Every line above is an identity or an operation")
        print("missing from the distribution this scan exists to measure — resolve")
        print("them before the capture is correlated.")
        return 1
    return 0


def assert_capture_live(capture_dir, identity, secret, settle_s=2.0):
    """Make ONE call and prove the capture recorded it. Refuse otherwise.

    Costs one API call and two seconds. On 2026-08-24 its absence cost a full
    9,000-request pass: the drive reported 1000/1000 and zero errors against a
    capture holding 410 bytes — a dead Polaris tail and `log_statement='none'`,
    neither visible from the drive's own output.
    """
    print(f"proving the capture at {capture_dir} is live...")
    before = ps.capture_snapshot(capture_dir)
    if not before:
        print(f"  no .log files under {capture_dir}")

    pc = client()
    token, scope, detail = ps.authenticate(pc, identity, secret, scope=PROFILE.scope)
    if not token:
        sys.exit(f"could not authenticate for the capture check: {detail}")
    pc.token = token
    r = pc.get_catalog(identity.catalog)
    if r.status_code >= 300:
        sys.exit(
            f"the capture-check call failed [{r.status_code}] — fix that before "
            "reading anything into the capture."
        )
    time.sleep(settle_s)

    after = ps.capture_snapshot(capture_dir)
    ok, reasons = ps.capture_verdict(
        before,
        after,
        polaris_tail=_tail(pathlib.Path(capture_dir) / "polaris.log"),
        pg_tail="\n".join(
            _tail(p) for p in sorted(pathlib.Path(capture_dir).glob("pg-*.log"))
        ),
    )
    if ok:
        grew = {
            n: after[n] - before.get(n, 0) for n in after if after[n] > before.get(n, 0)
        }
        print(f"  captured: {grew}")
        print()
        return 0

    print()
    print("REFUSING to drive: the capture is not recording.")
    for reason in reasons:
        print(f"  - {reason}")
    print()
    print("  A pass driven into a capture that is not recording completes")
    print("  cleanly and produces nothing. That has already happened once.")
    return 3


def _tail(path, n_bytes=60_000):
    try:
        with open(path, "rb") as fh:
            fh.seek(0, 2)
            fh.seek(max(0, fh.tell() - n_bytes))
            return fh.read().decode("utf-8", "replace")
    except OSError:
        return ""


def _progress(done, total, result):
    print(
        f"  {done:>5}/{total}  {result.requests:>6} requests  "
        f"{result.elapsed_s:6.0f}s  {len(result.errors)} non-2xx",
        flush=True,
    )


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--list", action="store_true", help="what the metastore holds")
    ap.add_argument(
        "--union",
        action="store_true",
        help="merge every probe on disk: what the WHOLE suite reaches across "
        "identity tiers, and which operations no tier reached. No cluster "
        "needed.",
    )
    ap.add_argument(
        "--footprint",
        action="store_true",
        help="grant_records each identity's authorization walks (measured)",
    )
    ap.add_argument(
        "--probe",
        action="store_true",
        help="one identity, all 13 GETs, record which are authorized",
    )
    ap.add_argument(
        "--drive",
        action="store_true",
        help="every identity through the probe's authorized subset",
    )
    ap.add_argument(
        "--profile",
        default=ps.DEFAULT_PROFILE,
        choices=sorted(ps.PROFILES),
        help="identity tier to drive. "
        + "; ".join(f"{n}: {p.description}" for n, p in sorted(ps.PROFILES.items())),
    )
    ap.add_argument("--user", type=int, default=1, help="identity index to probe")
    ap.add_argument("--limit", type=int, default=None, help="first N identities only")
    ap.add_argument(
        "--sample", type=int, default=None, help="--footprint: measure N of them"
    )
    ap.add_argument("--progress-every", type=int, default=25)
    ap.add_argument(
        "--capture",
        default=None,
        metavar="DIR",
        help="--drive: the capture directory this pass must be recorded into. "
        "Issues ONE call first and refuses to drive unless that call's SQL "
        "actually landed. Required for Pass A; omit only for an uncaptured run.",
    )
    ap.add_argument(
        "--deny-sample",
        type=int,
        default=0,
        help="--drive: ALSO issue the probe's refused operations for the first "
        "N identities. A 403 still pays the authorization prelude, so this is "
        "how the report shows the grantee lookup firing on the denial path "
        "without asserting it from source. Their 403s are expected, recorded, "
        "and not counted as errors.",
    )
    ap.add_argument(
        "--stop-after-auth-failures",
        type=int,
        default=5,
        help="abort after this many consecutive token failures (0 = never). A "
        "wrong shared secret fails all 1,000 identically.",
    )
    args = ap.parse_args()

    global PROFILE
    PROFILE = ps.PROFILES[args.profile]

    print(f"polaris : {POLARIS_URL}  realm={REALM}  prefix={prefix()}")
    print(f"profile : {PROFILE.name} — {PROFILE.description}")
    print(f"postgres: {PG['host']}:{PG['port']}/{PG['dbname']} schema={SCHEMA}")
    print()

    if args.union:
        sys.exit(cmd_union(args))
    if args.probe:
        sys.exit(cmd_probe(args))
    if args.drive:
        sys.exit(cmd_drive(args))
    if args.footprint:
        sys.exit(cmd_footprint(args))
    if args.list:
        sys.exit(cmd_list(args))
    ap.print_help()
    return 0


if __name__ == "__main__":
    main()
