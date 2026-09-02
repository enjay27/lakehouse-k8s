#!/usr/bin/env python3
"""Drive the 43-operation surface as one identity, and write its matrix report.

    # once, as admin — builds the fixture every case is driven against
    python3 drive_api_surface.py --setup

    # then per case, each from a RESTARTED Polaris (cold entity cache)
    python3 drive_api_surface.py --case unauthorized --drive
    python3 drive_api_surface.py --case authorized   --drive
    python3 drive_api_surface.py --case admin        --drive     # LAST

    # once, when all three are captured
    python3 drive_api_surface.py --teardown

WHY SETUP IS SEPARATE FROM DRIVE. Two of the three identities cannot build the
fixture: an unauthorized principal 403s on the setup itself, and a
catalog-scoped principal cannot create a catalog, since Polaris 1.3.0 has no
service-level grant type. A fixture built by the identity under test would
restrict the experiment to identities that do not need testing.

WHY ADMIN GOES LAST. Only the admin drive mutates -- the other two are refused
before touching anything -- so running it last leaves the fixture pristine for
the cases that must see it unchanged. The sweep is self-cleaning by
construction: every entity it creates is dropped by a later operation in the
same list.

WHY EACH DRIVE NEEDS A RESTART FIRST. A cold `InMemoryEntityCache` yields the
MAXIMAL statement set, so the capture shows every query an API can issue, and it
is what makes the three cases comparable to each other rather than to whichever
ran first. This runner does NOT restart Polaris -- it verifies nothing about
warmth and cannot -- so the restart is the operator's step, and `--drive`
prints the reminder rather than pretending.

The statement capture itself is `./capture.sh pgon` plus a rotate into a fresh
directory. `rotate` alone does NOT enable statement logging -- it is stop-then-
start -- and that mistake once cost a clean 9,000-request pass.
"""

import argparse
import json
import os
import pathlib
import sys
from datetime import datetime

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE
while not (REPO / "src").is_dir() and REPO != REPO.parent:
    REPO = REPO.parent
sys.path.insert(0, str(REPO / "src"))

import api_report as rep  # noqa: E402
import api_surface as surf  # noqa: E402

RUNS_DIR = HERE / "runs"
REPORTS_DIR = HERE / "reports"
#: Where the fixture's names are kept between invocations. Setup, three drives
#: and teardown are five separate processes; a fixture whose name is recomputed
#: from a timestamp in each of them is five different fixtures.
STATE = HERE / "runs" / "api-surface-fixture.json"

#: Which seeded principal each case drives as. `admin` is a seeded
#: service_admin principal, NOT root: root's authorization resolves two grant
#: rows and is the least representative identity in the realm, where a seeded
#: admin resolves ~1,100 and an authz principal 52. The selectivity spread is
#: the entire point of the three cases.
CASE_PREFIX = {"admin": "admin", "authorized": "authz", "unauthorized": "zerograve"}


def save_fixture(fx):
    RUNS_DIR.mkdir(exist_ok=True)
    STATE.write_text(json.dumps(fx.__dict__, indent=2), encoding="utf-8")
    return STATE


def load_fixture():
    if not STATE.exists():
        sys.exit(
            f"no fixture recorded at {STATE}.\n"
            "  Run --setup first: the three cases must drive the SAME fixture,\n"
            "  or their parameters differ by more than the identity and the\n"
            "  comparison stops meaning anything."
        )
    return surf.ProbeFixture(**json.loads(STATE.read_text()))


def resolve_identity(
    case, conn=None, client_id=None, principal_role=None, schema=None, realm=None
):
    """The `Identity` to drive as, from the metastore or stated outright.

    TWO PATHS, AND THE SECOND IS NOT A SHORTCUT. `load_identities` requires a
    principal to own a catalog named `{prefix}{N}_catalog` and reports anything
    else as `no_catalog` -- correct for the seeded tiers, and fatal for the
    unauthorized case, whose whole definition is a principal holding nothing.
    So a zero-grant principal is named outright with --client-id and
    --principal-role rather than discovered, and the runner says which path it
    took.
    """
    from dataclasses import replace

    from privilege_scan import Identity, load_identities

    if client_id:
        if not principal_role:
            sys.exit("--client-id also needs --principal-role (the token scope)")
        return (
            Identity(
                index=0,
                principal=principal_role.replace("_principal_role", ""),
                principal_role=principal_role,
                client_id=client_id,
                catalog=None,
            ),
            {},
        )

    prefix = CASE_PREFIX[case]
    ids, problems = load_identities(conn, schema, realm, prefix=prefix, limit=1)
    if not ids:
        sys.exit(
            f"no drivable principal with prefix {prefix!r}.\n"
            f"  load_identities reported: {problems}\n"
            "  'no_catalog' means the principal exists but owns no\n"
            f"  {prefix}N_catalog -- expected for a zero-grant principal, which\n"
            "  must be named with --client-id/--principal-role instead."
        )
    ident = ids[0]
    if case == "admin":
        #: THE TRAP privilege_scan documents by name: "A token is scoped to ONE
        #: principal-role. An identity holding two gets the grants of the one it
        #: asked for."
        #:
        #: An admin{N}_principal holds TWO -- its own admin{N}_principal_role,
        #: which is catalog-scoped on admin{N}_catalog, and service_admin, which
        #: is the entire reason the tier exists. load_identities builds the name
        #: from the seeder's convention, so it hands back the own-role, and a
        #: token scoped to that carries NO service-level authority. Driven
        #: against the shared probe catalog it is refused on all 43 operations
        #: and returns a distribution byte-identical to the ZERO-GRANT case.
        #:
        #: --footprint measures 3,377 for this identity because it walks every
        #: role the principal holds. The TOKEN carries one of them. Potential
        #: authority and exercised authority are different numbers, and only the
        #: second one drives.
        from privilege_scan import SERVICE_ADMIN_ROLE

        ident = replace(ident, principal_role=SERVICE_ADMIN_ROLE)
    return ident, problems


def build_clients(case, args):
    """(drive_ic, drive_pc, admin_ic, admin_pc) for this case.

    The admin pair always authenticates as the bootstrap identity. The drive
    pair authenticates as the CASE's principal -- and for `root` they are the
    same object, which is the degenerate case rather than a special path.
    """
    from iceberg_rest import IcebergREST
    from polaris_rest import PolarisREST
    from polaris_test_utils import POLARIS_URL, REALM, root_token

    admin_token = root_token()
    adm_pc = PolarisREST(POLARIS_URL, REALM, token=admin_token)
    adm_ic = IcebergREST(POLARIS_URL, REALM, token=admin_token)
    if case == "root":
        return adm_ic, adm_pc, adm_ic, adm_pc

    #: env first, then the env-specific config file. init_env already applies
    #: that precedence; reading os.environ alone would ignore local.yaml and
    #: report a missing secret that is sitting right there.
    from polaris_test_utils import POLARIS_USER_SECRET as _cfg_secret

    secret = os.environ.get("POLARIS_USER_SECRET") or _cfg_secret
    if not secret:
        sys.exit(
            "POLARIS_USER_SECRET is unset and has no default.\n"
            "  The seeded principals share one secret, set by hand in\n"
            "  principal_authentication_data; the seeder discards the ones\n"
            "  create_principal returns."
        )

    conn = None
    if not getattr(args, "client_id", None):
        import psycopg2

        from polaris_test_utils import PG_URL

        conn = psycopg2.connect(PG_URL)
    try:
        ident, problems = resolve_identity(
            case,
            conn=conn,
            client_id=getattr(args, "client_id", None),
            principal_role=getattr(args, "principal_role", None),
            schema=os.environ.get("PG_SCHEMA", "polaris_schema"),
            realm=REALM,
        )
    finally:
        if conn:
            conn.close()

    #: authenticate() returns (token, scope_used, detail) -- and NEVER asks for
    #: PRINCIPAL_ROLE:ALL. That is root's scope; a non-root principal handed it
    #: gets a 200 and a token with no effective role, then 403s on everything,
    #: which would read as "the surface is unauthorized" and be a statement
    #: about a scope string.
    token, scope, detail = authenticate_via(adm_pc, ident, secret)
    if not token:
        sys.exit(f"could not authenticate as {ident.principal}: {detail}")
    print(f"  driving as {ident.principal}  scope={scope}")
    if problems and any(problems.values()):
        print(f"  (not drivable: {problems})")
    return (
        IcebergREST(POLARIS_URL, REALM, token=token),
        PolarisREST(POLARIS_URL, REALM, token=token),
        adm_ic,
        adm_pc,
    )


def authenticate_via(pc, identity, secret):
    from privilege_scan import authenticate

    return authenticate(pc, identity, secret)


def capture_streams(capture):
    """The three streams a `Tracer` wants, from a capture DIRECTORY.

    `Tracer` takes stream objects -- polaris_log, pg_log, minio_trace -- not a
    path. Handing it the directory raised `IsADirectoryError` on every one of 43
    operations (2026-09-01), which the drive correctly reported as 43 ERRORS
    rather than 43 refusals. That distinction is the only reason the run was not
    mistaken for a flawless unauthorized pass.

    `pg*.log` is a MultiStream because pgpool routes reads across the replicas
    and capture.sh tails each one separately; older runs wrote a single pg.log,
    so both shapes are accepted.
    """
    from api_trace import FileStream, MultiStream

    capture = pathlib.Path(capture)
    pg = sorted(capture.glob("pg*.log")) or [capture / "pg.log"]
    return {
        "polaris_log": FileStream(str(capture / "polaris.log")),
        "pg_log": MultiStream(pg),
        "minio_trace": FileStream(str(capture / "minio.json")),
    }


def reap_report(capture):
    """Which tails `capture.sh` started are still alive, from `.pids`.

    A capture that dies MID-DRIVE looks identical, from the drive's own output,
    to one that never started: 43/43 operations, zero errors, an empty report.
    `capture.sh status` answers this before a run; nothing answered it after
    one, which is how three drives were published as complete.

    Returns a short human string rather than a structure -- it is printed, and
    a caller that wants to branch on it should be reading `.pids` itself.
    """
    pf = pathlib.Path(capture) / ".pids"
    if not pf.exists():
        return "no .pids file — capture.sh did not start these, or stop removed it"
    alive, dead = [], []
    for line in pf.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) != 2:
            continue
        pid, label = int(parts[0]), parts[1]
        try:
            os.kill(pid, 0)
        except OSError:
            dead.append(label)
        else:
            alive.append(label)
    if not dead:
        return f"all {len(alive)} alive ({', '.join(alive)})"
    return f"DEAD: {', '.join(dead)}  |  alive: {', '.join(alive) or 'none'}"


def do_setup(args):
    from iceberg_rest import build_create_table_payload, build_schema
    from polaris_test_utils import BUCKET, MINIO_ENDPOINT

    _, _, adm_ic, adm_pc = build_clients("root", args)
    fx = surf.ProbeFixture.stamped()
    schema = build_schema([(1, "id", "long", True), (2, "val", "string", False)])
    surf.setup_fixture(
        fx, adm_pc, adm_ic, BUCKET, MINIO_ENDPOINT, schema, build_create_table_payload
    )
    save_fixture(fx)
    print(f"probe fixture ready: {fx.cat}\n  recorded in {STATE.name}")
    print("  drive order: unauthorized, authorized, admin LAST (only admin mutates)")
    return 0


def do_authorize(args):
    """Give a principal-role rights on the probe catalog, as admin.

    The authorized case cannot drive the shared fixture without this: it holds
    grants on its OWN catalog, and Polaris authorizes against grant_records for
    the target catalog. See api_surface.authorize_on_fixture.
    """
    _, _, adm_ic, adm_pc = build_clients("root", args)
    fx = load_fixture()
    role = args.principal_role or f"{CASE_PREFIX['authorized']}1_principal_role"
    out = surf.authorize_on_fixture(fx, adm_pc, role)
    print(f"authorized {role} on {fx.cat}")
    print(f"  catalog role : {out['catalog_role']} [{out['create_catalog_role']}]")
    print(f"  granted      : {len(out['granted'])} privileges")
    if out["failed"]:
        print(f"  REFUSED      : {out['failed']}")
    print(f"  assign       : [{out['assign']}]")
    if not out["granted"]:
        sys.exit("no privilege was granted — the drive would still be refused")
    return 0


def _catalog_gone(report):
    """Did this `drop_catalog_tree` report actually remove the catalog?"""
    c = report.get("catalog")
    return c == "absent" or (isinstance(c, int) and 200 <= c < 300)


def do_teardown(args):
    """Remove the fixture. Keep the state file if the catalog SURVIVED.

    WHY THE UNLINK IS CONDITIONAL (2026-09-02). It was unconditional, so a
    teardown whose catalog delete answered 400 destroyed the only record of the
    fixture it had just failed to remove -- and `--teardown` cannot run again
    without one, because `load_fixture` exits. The stale-sweep that would have
    cleaned it up lives INSIDE teardown, so the orphan became unreachable by
    every path the tool offers. Losing the name of the thing you failed to
    delete is a strictly worse outcome than leaving a stale file behind.
    """
    _, _, adm_ic, adm_pc = build_clients("root", args)
    fx = load_fixture()
    out = surf.teardown_fixture(fx, adm_pc, adm_ic)
    print("teardown:", json.dumps(out, indent=2))
    if _catalog_gone(out.get("fixture", {})):
        STATE.unlink(missing_ok=True)
        return 0
    print(
        f"\n  KEPT {STATE.name}: {fx.cat} was NOT removed, so the fixture's name\n"
        "  is still the only handle on it. `remaining` above says what is holding\n"
        "  it. Re-run --teardown after clearing that, or --sweep to drop every\n"
        "  apiprofile* catalog without needing a fixture at all."
    )
    return 1


def do_sweep(args):
    """Drop every `apiprofile*` catalog, with NO fixture required.

    `--teardown`'s sweep needs a fixture it can no longer be given once the
    state file is gone. This is the same operation without that requirement, so
    residue is always reachable. Safe by prefix: `apiprofile*` is this
    harness's own namespace and nothing else creates one.
    """
    _, _, adm_ic, adm_pc = build_clients("root", args)
    names = [
        c["name"] if isinstance(c, dict) else c
        for c in adm_pc.list_catalogs().json().get("catalogs", [])
    ]
    mine = sorted(n for n in names if n.startswith("apiprofile"))
    if not mine:
        print("no apiprofile* catalogs — nothing to sweep")
        return 0
    print(f"sweeping {len(mine)}: {', '.join(mine)}")
    out = {n: surf.drop_catalog_tree(n, adm_pc, adm_ic) for n in mine}
    print(json.dumps(out, indent=2))
    stuck = [n for n, r in out.items() if not _catalog_gone(r)]
    if stuck:
        print(f"\n  STILL PRESENT: {', '.join(stuck)} — see `remaining` above.")
        return 1
    STATE.unlink(missing_ok=True)
    print("\n  all clear")
    return 0


def do_drive(args):
    from api_trace import Tracer, api_table_matrix, find_capture_dir
    from iceberg_rest import build_create_table_payload, build_scan_report

    fx = load_fixture()
    ic, pc, adm_ic, adm_pc = build_clients(args.case, args)
    capture = pathlib.Path(args.capture) if args.capture else find_capture_dir()
    print(f"case={args.case}  fixture={fx.cat}  capture={capture}")
    print("  (Polaris must have been RESTARTED since the last drive — a cold")
    print("   entity cache is what makes the three cases comparable.)")

    schema = None
    try:
        from iceberg_rest import build_schema

        schema = build_schema([(1, "id", "long", True), (2, "val", "string", False)])
    except Exception:  # noqa: BLE001
        pass

    ctx = fx.context(ic, pc, adm_ic, schema)
    tracer = Tracer(**capture_streams(capture))
    ops = surf.operations(ctx, build_create_table_payload, build_scan_report)
    try:
        res = surf.drive(tracer, ops, ctx)
    except surf.CaptureNotRecording as exc:
        print(f"\n  ABORTED after {len(tracer.records)} operations.\n{exc}")
        print(f"\n  tails: {reap_report(capture)}")
        return 2

    #: The tails are checked AFTER the sweep, not only before it. The
    #: 2026-09-01 drives had a capture that was alive when the run started and
    #: dead by the time it finished, and nothing in the run's own output said
    #: so -- it reported 43/43 and zero errors into an empty report.
    _reap = reap_report(capture)
    _sql = sum(r.sql_count for r in res.records)
    print(f"\n  captured {_sql:,} statements across {len(res.records)} records")
    print(f"  tails: {_reap}")
    if _sql == 0:
        print("  ! ZERO statements captured. The report will be empty; do not")
        print("    publish it. See HANDOFF-api-index-matrix.md §1.")

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    text = rep.render_matrix_report(
        res.records,
        api_table_matrix(res.records),
        case=args.case,
        identity=getattr(ctx.pc, "principal_name", None),
    )
    #: latest=False by default: only `doc-*-latest.md` is tracked, so refreshing
    #: it would replace the only version-controlled copy of the previous report.
    dest = rep.write_report(
        REPORTS_DIR,
        f"doc-api-sql-matrix-{args.case}",
        text,
        stamp=stamp,
        latest=args.latest,
    )
    RUNS_DIR.mkdir(exist_ok=True)
    run = RUNS_DIR / f"apidrive-{args.case}-{stamp}.json"
    run.write_text(
        json.dumps(
            {
                "run_id": run.stem,
                "case": args.case,
                "fixture": fx.cat,
                "capture": str(capture),
                "report": str(dest),
                "driven": res.driven,
                "permitted": res.permitted,
                "refused": res.refused,
                "errors": res.errors,
                "statuses": res.statuses,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        f"\n  driven {res.driven}/43  permitted {len(res.permitted)}  "
        f"refused {len(res.refused)}  other {len(res.other)}  "
        f"errors {len(res.errors)}"
    )
    print(f"  status distribution: {res.distribution}")
    if res.permitted:
        print("  PERMITTED:")
        for _k in res.permitted:
            print(f"    {res.statuses[_k]}  {_k}")
    if res.other:
        #: Usually SECOND-ORDER: a create was refused, so every operation
        #: targeting what it would have made returns 404. Those are not
        #: authorization outcomes and must not be read as any.
        print("  OTHER (neither 2xx nor 401/403 — often a refused prerequisite):")
        for _k, _v in sorted(res.other.items(), key=lambda kv: (kv[1] or 0)):
            print(f"    {_v}  {_k}")
    if res.errors:
        print("  ERRORS (harness faults, NOT refusals — a 403 is a measurement):")
        for k, v in res.errors.items():
            print(f"    {k}: {v}")
    print(f"  -> {dest.name}\n  -> {run.name}")
    return 0


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--case", choices=tuple(CASE_PREFIX) + ("root",))
    ap.add_argument("--setup", action="store_true")
    ap.add_argument("--drive", action="store_true")
    ap.add_argument("--teardown", action="store_true")
    ap.add_argument(
        "--sweep",
        action="store_true",
        help="drop every apiprofile* catalog, no fixture required. For "
        "residue a failed --teardown left behind, which --teardown "
        "itself cannot reach once the state file is gone.",
    )
    ap.add_argument(
        "--authorize",
        action="store_true",
        help="grant --principal-role rights on the probe catalog, as "
        "admin. Required before the authorized case can drive the "
        "shared fixture: it owns a different catalog.",
    )
    ap.add_argument("--capture", default=None, help="capture directory")
    ap.add_argument(
        "--client-id",
        default=None,
        help="drive as this principal_client_id instead of discovering one. "
        "Required for the unauthorized case: load_identities filters out "
        "any principal that owns no catalog, which is exactly what a "
        "zero-grant principal is.",
    )
    ap.add_argument(
        "--principal-role",
        default=None,
        help="the principal-role to scope the token to. Never ALL.",
    )
    ap.add_argument(
        "--latest",
        action="store_true",
        help="also refresh doc-api-sql-matrix-<case>-latest.md. Off by default: "
        "only doc-*-latest.md is tracked, so it is the copy git keeps.",
    )
    args = ap.parse_args()
    if args.setup:
        return do_setup(args)
    if args.authorize:
        return do_authorize(args)
    if args.teardown:
        return do_teardown(args)
    if args.sweep:
        return do_sweep(args)
    if args.drive:
        if not args.case:
            sys.exit("--drive needs --case")
        return do_drive(args)
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
