#!/usr/bin/env python3
"""Read a privilege-scan capture and say which SQL each API issued, and how.

The reading end of `scan_privileges.py`. That runner drove 15,000 requests into
a capture and proved the capture was recording when it STARTED. This one proves
it was still recording when it finished, correlates every request on
`mdc.requestId`, and answers the question the whole pass exists for:

    for each API on the authenticated GET surface, which SQL, how many times,
    and -- with --explain -- which access path at the measured volume.

    python3 profile_queries.py --capture capture-scan-noindex-2 \
                               --run privscan-20260824-123408
    python3 profile_queries.py --capture ... --run ... --explain
    python3 profile_queries.py --capture ... --run ... --explain --report

RUN IT WITHOUT --explain FIRST
------------------------------
Correlation needs no database at all -- it is a pure read of files already on
disk. If the capture disagrees with the run JSON about how many requests
happened, that is the finding, and spending an EXPLAIN sweep on a capture that
holds two thirds of a pass produces a confident report about a subset.

WHAT IT REFUSES TO DO
---------------------
* Read a capture whose `polaris.log` holds no `DatasourceOperations` line. A
  capture can be 119 MB of access log and contain no SQL at all if the level is
  above DEBUG -- a different fault, with a different fix, from a dead tail.
* EXPLAIN on a replica. `pg_is_in_recovery()` is asserted false and every
  statement carries `/*NO LOAD BALANCE*/`. The primary is `postgresql-1` today
  and it MOVES; it is detected, never assumed.
* Report an index state it did not look up. `--explain` records `pg_indexes`
  for `grant_records` into the run JSON, so a report can never claim to be the
  no-index pass while describing the indexed one.

WHAT IT DOES NOT MEASURE
------------------------
Latency. This capture was taken with statement logging ON, which inflates the
clock 4.6x (measured). PostgreSQL's own `duration:` lines are rendered, always
labelled inflated. Real latency is Pass B, with logging off, and is not this
task.

    export POLARIS_USER_SECRET=...     # not needed here -- no API calls are made
    export PG_PASSWORD=...             # only --explain touches PostgreSQL
"""

import argparse
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

import query_profile as qp  # noqa: E402

PG = dict(
    host=os.environ.get("PG_HOST", "192.168.139.2"),
    port=int(os.environ.get("PG_PORT", "5432")),
    dbname=os.environ.get("PG_DB", "polaris"),
    user=os.environ.get("PG_USER", "polaris"),
    password=os.environ.get("PG_PASSWORD", "polaris"),
)
SCHEMA = os.environ.get("PG_SCHEMA", "polaris_schema")
REALM = os.environ.get("POLARIS_REALM", "POLARIS")

RUNS_DIR = HERE / "runs"
REPORTS_DIR = HERE / "reports"

#: The table under the microscope. Everything else on the surface is expected
#: to be an index scan already; the value of sweeping all of them is confirming
#: that, and catching anything that is not.
FOCUS_TABLE = "grant_records"


# ----------------------------------------------------------------------
# resolving the inputs, by content
# ----------------------------------------------------------------------
def resolve_capture(name):
    """A capture directory holding a Polaris log with SQL in it. By CONTENT."""
    d = pathlib.Path(name)
    if not d.is_absolute():
        d = HERE / name
    if not d.is_dir():
        sys.exit(f"no such capture directory: {d}")
    log = d / "polaris.log"
    if not log.exists() or log.stat().st_size == 0:
        sys.exit(
            f"{log} is missing or empty.\n"
            "  A pass driven into a capture that is not recording completes\n"
            "  cleanly and produces nothing. That has already happened once."
        )
    with open(log, "r", encoding="utf-8", errors="replace") as fh:
        head = fh.read(4 << 20)
    if "DatasourceOperations" not in head:
        sys.exit(
            f"{log} holds no DatasourceOperations line in its first 4 MB.\n"
            "  The tail is alive but the SQL logger is above DEBUG -- a\n"
            "  different fault from a dead stream, with a different fix.\n"
            "  Re-enable Polaris DEBUG and re-drive; nothing here can be\n"
            "  recovered from this capture."
        )
    return d


def resolve_run(name):
    p = pathlib.Path(name)
    if not p.is_absolute():
        p = RUNS_DIR / name
    if p.suffix != ".json":
        p = p.with_suffix(".json")
    if not p.exists():
        sys.exit(
            f"no run manifest at {p}.\n"
            "  The report's denominator comes from the drive's own record of\n"
            "  what it issued. Without it there is nothing to reconcile the\n"
            "  capture against, and a short capture is invisible."
        )
    return json.loads(p.read_text(encoding="utf-8"))


# ----------------------------------------------------------------------
# PostgreSQL, for --explain only
# ----------------------------------------------------------------------
def pg_connect(host=None):
    import psycopg2

    cfg = dict(PG)
    if host:
        cfg["host"] = host
    try:
        conn = psycopg2.connect(**cfg)
    except Exception as e:  # noqa: BLE001
        sys.exit(
            f"cannot reach PostgreSQL ({str(e).splitlines()[0][:90]})\n"
            f"  expected the Pgpool LoadBalancer at {cfg['host']}:{cfg['port']}\n"
            "  override with PG_HOST / PG_PORT / PG_USER / PG_PASSWORD"
        )
    conn.autocommit = True
    return conn


def assert_primary(conn):
    """Refuse to EXPLAIN on a replica, and say which node answered.

    A plan measured on a standby is a plan for a different machine's cache and
    a different machine's statistics. The primary is `postgresql-1` today and
    it moves -- MEMORY records Kade's manual resets having silently hit a
    read-only replica for exactly this reason.
    """
    cur = conn.cursor()
    cur.execute("/*NO LOAD BALANCE*/ SELECT pg_is_in_recovery(), inet_server_addr()")
    in_recovery, addr = cur.fetchone()
    cur.close()
    if in_recovery:
        sys.exit(
            f"connected node ({addr}) is IN RECOVERY -- it is a replica.\n"
            "  Pgpool routed the session to a standby. Point PG_HOST at the\n"
            "  primary directly; do not hardcode which pod that is, it moves."
        )
    return str(addr)


def index_state(conn, table=FOCUS_TABLE):
    """Every index on `table`, right now. Recorded so the pass cannot be mislabelled."""
    cur = conn.cursor()
    cur.execute(
        "/*NO LOAD BALANCE*/ SELECT indexname, indexdef FROM pg_indexes "
        "WHERE schemaname = %s AND tablename = %s ORDER BY indexname",
        (SCHEMA, table),
    )
    rows = cur.fetchall()
    cur.close()
    return [{"name": n, "def": d} for n, d in rows]


def table_rows(conn, table=FOCUS_TABLE):
    cur = conn.cursor()
    cur.execute(f"/*NO LOAD BALANCE*/ SELECT count(*) FROM {SCHEMA}.{table}")
    n = cur.fetchone()[0]
    cur.close()
    return n


def explain_statements(conn, worklist, k=11, pin_serial=True):
    """EXPLAIN (ANALYZE, BUFFERS) each distinct statement, on the primary.

    Replays `sp.sample_sql` -- ONE occurrence's raw text -- not `sp.sql`, which
    is `normalize_sql` output and a grouping key rather than a statement. The
    first `--explain` run replayed the key and lost 7 of 8 statements to
    `syntax error at or near "<"` (from `IN (<rows>)`) and `at or near "AND"`
    (from `?` parsing as a PostgreSQL operator). `StatementProfile.replay()`
    now owns both conversions and refuses when the placeholder count and the
    parameter count disagree.

    `pin_serial` sets `max_parallel_workers_per_gather = 0` for the SESSION --
    reversible, not an ALTER SYSTEM. 02b measured parallel Seq Scan timings as
    unusable: identical plan cost and buffers, 3-10x clock spread. Whether the
    unindexed path WOULD escalate is recorded separately rather than being
    allowed to contaminate the comparison.
    """
    from api_trace import explain_n

    if pin_serial:
        cur = conn.cursor()
        cur.execute("SET max_parallel_workers_per_gather = 0")
        cur.close()

    out = []
    for sp in worklist:
        sql, params = sp.replay()
        entry = {
            "sql": sp.sql,
            "replayed_sql": sp.sample_sql,
            "table": sp.table,
            "verb": sp.verb,
            "occurrences": sp.occurrences,
            "requests": sp.requests,
            "per_request": round(sp.per_request, 3),
            "params_observed": sp.params_observed,
            "params": sp.sample_params if sp.params_observed else None,
        }
        if sql is None:
            #: §3.4 of the plan, plus the placeholder-count guard. Saying which
            #: of the two refused beats one message that covers both: a redacted
            #: secret table is expected forever, a count mismatch is a bug.
            entry["skipped"] = (
                "parameters were redacted at capture (secret table); replay "
                "would need them reconstructed from the metastore"
                if not sp.params_observed
                else (
                    f"placeholder/parameter mismatch: SQL has "
                    f"{(sp.sample_sql or '').count('?')} placeholders, "
                    f"{len(qp.param_tuple(sp.sample_params))} values captured"
                )
            )
            out.append(entry)
            continue
        try:
            med, lo, hi, plan, _times = explain_n(
                conn, sql, params, k=k, analyze=True, no_lb=True
            )
        except Exception as exc:  # noqa: BLE001
            entry["error"] = f"{type(exc).__name__}: {str(exc).splitlines()[0][:160]}"
            out.append(entry)
            continue
        entry.update(_summarise_plan(plan, sp.table))
        #: A range, never a headline. This pass ran with statement logging on
        #: (4.6x inflation, measured) and these EXPLAINs were taken afterwards
        #: on a cluster that may still have it enabled, so even the honest
        #: number here is not the API's latency -- it is one statement's, in
        #: isolation, on the primary.
        entry["explain_ms"] = {
            "median": round(med, 3),
            "min": round(lo, 3),
            "max": round(hi, 3),
        }
        out.append(entry)
    return out


def _walk(node):
    yield node
    for child in node.get("Plans") or []:
        yield from _walk(child)


def _summarise_plan(plan, table=None):
    """Plan shape, buffers and rows-filtered -- the numbers that survive a rerun.

    `explain_n` returns the plan as a FORMAT JSON dict, so this reads named
    fields rather than grepping rendered text. That matters for exactly one
    reason: "Seq Scan" appearing in a plan is not the same as the scan on the
    relation under audit appearing as a Seq Scan, and a substring search cannot
    tell those apart in a plan with more than one node.
    """
    if not isinstance(plan, dict) or "Plan" not in plan:
        return {"plan": None}
    root = plan["Plan"]
    nodes = list(_walk(root))
    scans = [n for n in nodes if "Scan" in (n.get("Node Type") or "")]
    chosen = None
    if table:
        chosen = next(
            (
                n
                for n in scans
                if (n.get("Relation Name") or "").lower() == table.lower()
            ),
            None,
        )
    chosen = chosen or (scans[0] if scans else root)
    hit = chosen.get("Shared Hit Blocks")
    read = chosen.get("Shared Read Blocks")
    return {
        "plan": plan,
        "scan": chosen.get("Node Type"),
        "relation": chosen.get("Relation Name"),
        "index": chosen.get("Index Name"),
        "rows_removed_by_filter": chosen.get("Rows Removed by Filter"),
        "actual_rows": chosen.get("Actual Rows"),
        "plan_rows": chosen.get("Plan Rows"),
        "shared_hit_blocks": hit,
        "shared_read_blocks": read,
        "buffers": (None if hit is None and read is None else f"hit={hit} read={read}"),
        "parallel": any(n.get("Workers Planned") for n in nodes)
        or any("Parallel" in (n.get("Node Type") or "") for n in nodes),
        "node_types": [n.get("Node Type") for n in nodes],
    }


# ----------------------------------------------------------------------
# report
# ----------------------------------------------------------------------
def _num(v):
    return "—" if v is None else f"{v:,}"


def render_report(corr, rec, run, explains, meta):
    shapes = qp.statement_profile(corr.profiles)
    classes, diff = qp.prelude_by_outcome(corr, table=FOCUS_TABLE)
    first, last = qp.profile_window(corr.profiles)
    L = []
    a = L.append

    a(f"# Privilege query performance — Pass A, {meta['index_state_label']}")
    a("")
    a(
        f"Generated {meta['generated']} from capture `{meta['capture']}` and run "
        f"`{run.get('run_id')}`. Volume, index state and request counts below are "
        "**measured**, not carried over from a plan document."
    )
    a("")

    a("## What was measured")
    a("")
    a(f"- realm `{run.get('realm')}`, prefix `{run.get('prefix')}`")
    a(
        f"- **{run.get('identities')} identities**, {run.get('authenticated')} "
        f"authenticated, **{run.get('requests')} requests** in "
        f"{run.get('elapsed_s')} s (the drive's own clock, discarded — logging on)"
    )
    a(f"- capture window `{first}` → `{last}`")
    if meta.get("grant_rows") is not None:
        a(
            f"- `{SCHEMA}.{FOCUS_TABLE}`: **{meta['grant_rows']:,} rows** at "
            "EXPLAIN time"
        )
    a(f"- index state on `{FOCUS_TABLE}`: {meta['index_state_label']}")
    for ix in meta.get("indexes", []):
        a(f"  - `{ix['name']}`")
    a(
        "- provenance: 1,000 real API-seeded principals. Nothing synthetic, "
        "nothing to disclose."
    )
    a("")

    a("## Capture integrity")
    a("")
    a(qp.render_integrity(corr))
    a("")
    a(qp.render_reconciliation(rec))
    a("")
    if rec["clean"]:
        a(
            "Every request the drive recorded is present in the capture. The "
            "distribution below is the whole pass, not a subset of it."
        )
    else:
        a(
            f"**The capture and the run disagree by {rec['delta_total']:+d} "
            "requests.** Every figure below describes what the capture holds, "
            "which is not what the drive issued. Resolve this before quoting "
            "anything from it."
        )
    a("")

    a("## Does a refused request pay the authorization prelude?")
    a("")
    a(
        "`scan_privileges.py` asserts that it does. This pass drove "
        "the refused operations for **every** identity, so the question is "
        "answered from the capture instead:"
    )
    a("")
    a(qp.render_outcome_split(classes, diff, table=FOCUS_TABLE))
    a("")

    a("## Per-API SQL and statement volume")
    a("")
    a(qp.render_per_label(qp.per_label_summary(corr, table=FOCUS_TABLE), FOCUS_TABLE))
    a("")

    a("## Distinct statements")
    a("")
    a(qp.render_statements(shapes))
    a("")

    if explains:
        a("## Access path per statement")
        a("")
        a(
            f"EXPLAIN (ANALYZE, BUFFERS) on the primary at `{meta.get('primary')}`, "
            "`/*NO LOAD BALANCE*/`, `pg_is_in_recovery() = false` asserted, "
            "`max_parallel_workers_per_gather = 0` pinned session-scoped."
        )
        a("")
        a(
            "| n | table | scan | index | buffers | rows removed by filter | "
            "rows out |"
        )
        a("|---:|---|---|---|---|---:|---:|")
        for e in explains:
            if e.get("skipped") or e.get("error"):
                note = e.get("skipped") or e.get("error")
                a(
                    f"| {e['occurrences']} | {e.get('table') or '—'} | *not "
                    f"replayed* | — | — | — | {note} |"
                )
                continue
            a(
                f"| {e['occurrences']} | {e.get('table') or '—'} | "
                f"{e.get('scan')} | {e.get('index') or '—'} | "
                f"{(e.get('buffers') or '—')} | "
                f"{_num(e.get('rows_removed_by_filter'))} | "
                f"{_num(e.get('actual_rows'))} |"
            )
        a("")
        focus = [
            e
            for e in explains
            if (e.get("table") or "") == FOCUS_TABLE and e.get("plan")
        ]
        if focus:
            a(f"### The {FOCUS_TABLE} lookup")
            a("")
            for e in focus[:3]:
                a(
                    f"Issued **{e['occurrences']} times** across "
                    f"{e['requests']} requests ({e['per_request']} per request)."
                )
                a("")
                a(f"```sql\n{e.get('replayed_sql') or e['sql']}\n```")
                a("")
                a("```json")
                a(json.dumps(e["plan"], indent=2)[:6000])
                a("```")
                a("")
                if e.get("rows_removed_by_filter") is not None:
                    a(
                        f"The scan returned **{_num(e.get('actual_rows'))}** rows "
                        f"and discarded **{_num(e.get('rows_removed_by_filter'))}** "
                        "to get them. That ratio, and the buffer count beside it, "
                        "are identical across reruns; the milliseconds are not."
                    )
                    a("")
    else:
        a("## Access path per statement")
        a("")
        a(
            "*Not measured in this run — `--explain` was not passed. Plan shape, "
            "buffers and rows-filtered are the durable evidence and this report "
            "does not have them yet.*"
        )
        a("")

    a("## What this pass does not establish")
    a("")
    a(
        f"- **The index-present contrast.** This is the {meta['index_state_label']} "
        "half. The Seq→Index comparison needs the same drive re-run with "
        "`idx_grant_records_grantee` created and `ANALYZE` done, into a rotated "
        "capture."
    )
    a(
        "- **Latency.** Statement logging was on for this pass, a measured 4.6x "
        "inflation. Any millisecond figure here is illustration beside the "
        "buffer evidence, never a number to quote. Real latency is Pass B, "
        "logging off."
    )
    a(
        "- **Write paths.** The drive is read-only by construction; four write "
        "statements remain `NO_PARAMS` and unmeasured (MEMORY, Active Issues)."
    )
    a(
        "- **Generic vs custom plans.** These statements are replayed verbatim "
        "from the capture — the same SQL Polaris executed — but psycopg2 "
        "interpolates the bound values as literals, so the planner sees "
        "constants and produces a CUSTOM plan. Polaris issues them through "
        "JDBC as server-side prepared statements, which PostgreSQL may switch "
        "to a GENERIC plan after five executions. For an unindexed scan at this "
        "volume both are the same shape, so the finding holds either way — but "
        "the plans here are not proof about which one the server chose at "
        "runtime, and this report does not claim they are."
    )
    a("")
    return "\n".join(L)


# ----------------------------------------------------------------------
# main
# ----------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--capture",
        required=True,
        metavar="DIR",
        help="the capture directory the pass was recorded into",
    )
    ap.add_argument(
        "--run",
        required=True,
        metavar="RUN",
        help="the drive's manifest, e.g. privscan-20260824-123408",
    )
    ap.add_argument(
        "--explain",
        action="store_true",
        help="EXPLAIN (ANALYZE, BUFFERS) each distinct statement on the PRIMARY",
    )
    ap.add_argument(
        "--explain-n", type=int, default=11, help="EXPLAIN repeats; first discarded"
    )
    ap.add_argument(
        "--explain-limit",
        type=int,
        default=None,
        help="EXPLAIN only the N most frequent statements",
    )
    ap.add_argument("--report", action="store_true", help="write the Markdown report")
    ap.add_argument(
        "--pg-host",
        default=None,
        help="connect straight to the primary, bypassing Pgpool routing",
    )
    ap.add_argument(
        "--chunk-mb", type=int, default=8, help="log read chunk size, in MB"
    )
    args = ap.parse_args()

    capture = resolve_capture(args.capture)
    run = resolve_run(args.run)
    log = capture / "polaris.log"

    print(f"capture : {capture}")
    print(f"run     : {run.get('run_id')}  ({run.get('requests')} requests recorded)")
    print(f"log     : {log.stat().st_size / (1 << 20):.0f} MB")
    print()

    t0 = time.time()
    print("correlating on mdc.requestId ...", flush=True)
    corr = qp.correlate(str(log), chunk_bytes=args.chunk_mb << 20)
    print(f"  {time.time() - t0:.0f}s")
    print()
    print(qp.render_integrity(corr))
    print()

    rec = qp.reconcile(corr, run)
    print(qp.render_reconciliation(rec))
    print()
    if not rec["clean"]:
        print(
            f"NOT reconciled: the capture and the drive disagree by "
            f"{rec['delta_total']:+d} requests. Everything below describes the\n"
            "capture, which is not what the drive issued."
        )
        print()

    classes, diff = qp.prelude_by_outcome(corr, table=FOCUS_TABLE)
    print("Prelude by outcome")
    print(qp.render_outcome_split(classes, diff, table=FOCUS_TABLE))
    print()
    print("Per-API")
    print(
        qp.render_per_label(qp.per_label_summary(corr, table=FOCUS_TABLE), FOCUS_TABLE)
    )
    print()

    shapes = qp.statement_profile(corr.profiles)
    print("Distinct statements")
    print(qp.render_statements(shapes))
    print()

    meta = {
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "capture": capture.name,
        "index_state_label": "index state NOT looked up (no --explain)",
        "indexes": [],
        "grant_rows": None,
        "primary": None,
    }
    explains = []
    if args.explain:
        conn = pg_connect(args.pg_host)
        meta["primary"] = assert_primary(conn)
        meta["indexes"] = index_state(conn)
        meta["grant_rows"] = table_rows(conn)
        names = [i["name"] for i in meta["indexes"]]
        has_grantee = any("grantee" in n for n in names)
        meta["index_state_label"] = "index PRESENT" if has_grantee else "index ABSENT"
        print(f"primary : {meta['primary']}")
        print(f"{FOCUS_TABLE}: {meta['grant_rows']:,} rows, indexes {names}")
        print(f"  -> {meta['index_state_label']}")
        print()
        worklist = qp.explain_worklist(shapes, limit=args.explain_limit)
        print(f"EXPLAINing {len(worklist)} distinct statements ...", flush=True)
        explains = explain_statements(conn, worklist, k=args.explain_n)
        conn.close()
        for e in explains:
            if e.get("table") == FOCUS_TABLE and e.get("plan"):
                print(f"  {FOCUS_TABLE}: {e.get('scan')}  {e.get('buffers')}")
        #: Loud, not buried in the JSON. The first --explain run errored on 7
        #: of 8 statements and said so only in a file nobody had opened yet.
        errors = [e for e in explains if e.get("error")]
        skipped = [e for e in explains if e.get("skipped")]
        for e in skipped:
            print(f"  not replayed [{e.get('table')}]: {e['skipped']}")
        if errors:
            print()
            print(f"  {len(errors)} of {len(explains)} statements FAILED to EXPLAIN:")
            for e in errors:
                print(f"    [{e.get('table')}] {e['error']}")
            print()
            print("  A plan table built from this is a table of blanks. Fix the")
            print("  replay before reading anything into the report.")
        print()

    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    out = RUNS_DIR / f"qprofile-{run.get('run_id')}.json"
    out.write_text(
        json.dumps(
            {
                "run_id": run.get("run_id"),
                "capture": capture.name,
                "generated": meta["generated"],
                "index_state": meta["index_state_label"],
                "indexes": meta["indexes"],
                "grant_rows": meta["grant_rows"],
                "primary": meta["primary"],
                "reconciliation": rec,
                "integrity": {
                    "access_records": corr.access_records,
                    "statements": corr.statements,
                    "orphan_statements": corr.orphan_statements,
                    "unclassified_paths": corr.unclassified_paths,
                },
                "per_label": qp.per_label_summary(corr, table=FOCUS_TABLE),
                "outcome_classes": {
                    k: {kk: vv for kk, vv in v.items() if kk != "shapes"}
                    for k, v in classes.items()
                },
                "statements": [
                    {
                        "sql": s.sql,
                        "table": s.table,
                        "verb": s.verb,
                        "occurrences": s.occurrences,
                        "requests": s.requests,
                        "params_observed": s.params_observed,
                    }
                    for s in qp.explain_worklist(shapes)
                ],
                "explains": explains,
            },
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )
    print(f"profile written to {out}")

    if args.report:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        doc = REPORTS_DIR / (f"doc-privilege-query-performance-{run.get('run_id')}.md")
        doc.write_text(render_report(corr, rec, run, explains, meta), encoding="utf-8")
        latest = REPORTS_DIR / "doc-privilege-query-performance-latest.md"
        latest.write_text(doc.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"report written to {doc}")

    return 0 if rec["clean"] else 1


if __name__ == "__main__":
    sys.exit(main())
