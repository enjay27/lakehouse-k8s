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
    return ids[0], problems


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

    secret = os.environ.get("POLARIS_USER_SECRET")
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


def do_teardown(args):
    _, _, adm_ic, adm_pc = build_clients("root", args)
    fx = load_fixture()
    print("teardown:", json.dumps(surf.teardown_fixture(fx, adm_pc, adm_ic), indent=2))
    STATE.unlink(missing_ok=True)
    return 0


def do_drive(args):
    from api_trace import FileStream, Tracer, api_table_matrix, find_capture_dir
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
    tracer = Tracer(FileStream(capture))
    ops = surf.operations(ctx, build_create_table_payload, build_scan_report)
    res = surf.drive(tracer, ops, ctx)

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
        f"refused {len(res.refused)}  errors {len(res.errors)}"
    )
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
    if args.teardown:
        return do_teardown(args)
    if args.drive:
        if not args.case:
            sys.exit("--drive needs --case")
        return do_drive(args)
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
