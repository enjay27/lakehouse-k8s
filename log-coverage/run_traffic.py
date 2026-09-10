#!/usr/bin/env python3
"""Drive Polaris traffic from this repo alone. No logging, no `local-k8s`.

`make_traffic` is a library -- `local-k8s` imports it and calls `drive()` as
part of the logging test. This is the other caller: a person, here, who wants
traffic made without standing up a verifier. It is deliberately thin. Anything
it does that is not argument parsing belongs in the module instead.

Three things it will do, cheapest first:

    # 1. build all 286 requests and contact NOTHING. Safe with Polaris down.
    uv run python log-coverage/run_traffic.py --dry-run

    # 2. validate every one of those requests against the vendored specs,
    #    through Prism. Still no Polaris. See --spec-check below.
    uv run python log-coverage/run_traffic.py --spec-check

    # 3. actually drive Polaris. THIS MUTATES -- see the warning below.
    uv run python log-coverage/run_traffic.py --profile smoke

## Running Prism for --spec-check

Two documents, two servers, because they mount at different paths:

    npx @stoplight/prism-cli mock -p 4010 --errors \\
        log-coverage/spec/polaris-management-service.yml
    npx @stoplight/prism-cli mock -p 4011 --errors \\
        log-coverage/spec/rest-catalog-open-api.yaml

**`--errors` is not optional.** Without it Prism logs violations and answers
200 anyway, and the check would report every request valid without having
looked. `spec_check` sends a deliberately invalid request first and reports
VOID if it is not rejected, so a forgotten `--errors` is caught rather than
believed -- but starting it right is cheaper than reading a VOID.

## What --profile actually does to the cluster

It MUTATES. A catalog, two principals, two roles, a namespace, a table and a
view are created and deleted, and the 500 ladder deliberately provokes errors.
`local` only; `config_from_env` calls `require_not_prod` and `check_config`
refuses a config whose env is prod. `smoke` is ~12 cells in one window and is
the one to run first.
"""

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

import make_traffic as mt  # noqa: E402

SPEC_DIR = pathlib.Path(__file__).resolve().parent / "spec"


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Drive Polaris traffic, or check the requests without driving.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument(
        "--env",
        default="local",
        help="init_env target. Default local, and the only safe one.",
    )
    ap.add_argument(
        "--profile",
        default="smoke",
        choices=sorted(mt.PROFILES),
        help="; ".join(f"{k}: {v}" for k, v in sorted(mt.PROFILES.items())),
    )
    ap.add_argument(
        "--window-seconds",
        type=float,
        default=30.0,
        help="The grid the phases align to. THE CALLER OWNS THIS -- "
        "make_traffic never reads it from a ConfigMap. Match it "
        "to the shipper's WINDOW_SECONDS if a verifier will "
        "read the result. Default 30.",
    )
    ap.add_argument("--run", default=None, help="Run id. Default the epoch second.")
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Build every request, contact nothing, create nothing.",
    )
    ap.add_argument(
        "--spec-check",
        action="store_true",
        help="Validate every request against the specs, through Prism.",
    )
    ap.add_argument("--prism-management", default="http://127.0.0.1:4010")
    ap.add_argument("--prism-catalog", default="http://127.0.0.1:4011")
    ap.add_argument(
        "--report", default=None, help="Write the --spec-check report here as markdown."
    )
    ap.add_argument(
        "--runs-dir",
        default=None,
        help="Where traffic-<run>.json goes. Default runs/ in the repo.",
    )
    args = ap.parse_args(argv)

    if args.spec_check:
        return _spec_check(args)

    config = (
        {k: "dry-run-not-contacted" for k in mt._REQUIRED_CONFIG}
        if args.dry_run
        else mt.config_from_env(args.env)
    )
    if args.dry_run:
        config["realm"] = "POLARIS"
    else:
        print(f"  env      {config['env']}  ->  {config['polaris_url']}")
        print(f"  profile  {args.profile}: {mt.PROFILES[args.profile]}")
        print("  THIS MUTATES: a catalog, principals, roles, a namespace, a table")
        print("  and a view are created and deleted.")

    traffic = mt.drive(
        config,
        window_seconds=args.window_seconds,
        profile=args.profile,
        run=args.run,
        dry_run=args.dry_run,
        spec_dir=SPEC_DIR,
        runs_dir=args.runs_dir,
        on_row=None if args.dry_run else _progress,
    )
    return _report_traffic(traffic)


def _progress(row):
    mark = "  " if row.get("verdict") == "covered" else "!!"
    print(
        f"  {mark} {row['op_id']:34} target {str(row['target']):>4} -> "
        f"{row['status']}  [{row['phase']}]"
    )


def _report_traffic(traffic):
    print()
    print(f"  run        {traffic.run}")
    print(f"  calls      {len(traffic.calls)}")
    if traffic.calls:
        cov = traffic.coverage
        print(
            f"  coverage   {cov['covered']} covered, {cov['missed']} missed, "
            f"{cov['error']} error"
        )
        print(
            f"  windows    {traffic.windows['first']} .. {traffic.windows['last']} "
            f"({len(traffic.windows['distinct'])} distinct)"
        )
        print(f"  claims     {len(traffic.claims)}")
        bad = mt.echo_failures(traffic.calls)
        if bad:
            # A fault HERE, not in any pipeline: the id never reached the
            # server as sent, and a verifier must report those UNPROVEN.
            print(
                f"  !! {len(bad)} request id(s) did not echo back -- a TRAFFIC "
                "fault, not a pipeline one"
            )
    for f in traffic.build_findings:
        print(f"  build finding ({f['about']}): {f['title']}")
    if traffic.incomplete:
        print(f"  incomplete {traffic.incomplete}")
    # A drive that stopped early still drove something; the caller decides.
    return 0


def _spec_check(args):
    import spec_check as sc

    prism = {"management": args.prism_management, "catalog": args.prism_catalog}
    print(f"  prism      {prism}")
    try:
        report = sc.check_requests(SPEC_DIR, prism, run=args.run or "speccheck")
    except sc.PrismUnavailable as exc:
        print(f"  PRISM UNAVAILABLE -- nothing was measured.\n    {exc}")
        print(
            "    Start it:  npx @stoplight/prism-cli mock -p 4010 --errors "
            "log-coverage/spec/polaris-management-service.yml"
        )
        return 2
    text = sc.render_report(report)
    print()
    print(text)
    if args.report:
        pathlib.Path(args.report).write_text(text)
        print(f"\n  written    {args.report}")
    # VOID is not a pass and must not exit 0: nothing was measured.
    return {sc.PASS: 0, sc.FAIL: 1, sc.VOID: 2}[report["verdict"]]


if __name__ == "__main__":
    sys.exit(main())
