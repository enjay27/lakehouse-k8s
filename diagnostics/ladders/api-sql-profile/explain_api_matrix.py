#!/usr/bin/env python3
"""EXPLAIN every statement a matrix report records, and say which use an index.

    python3 explain_api_matrix.py --matrix reports/doc-api-sql-matrix-admin-latest.md \
                                  --case admin --index-state present

PRESENCE, NOT PERFORMANCE. Every EXPLAIN here is plan-only -- no ANALYZE. That
is not a cheaper mode, it is the only safe one: `EXPLAIN ANALYZE` on an
INSERT/UPDATE/DELETE really performs it, and this report covers the write half
of the surface. It also means there is no clock in the output, so there is no
clock anyone can misquote.

THE UNIT IS THE (SQL, params) PAIR. 505 statement instances in the 2026-08-20
report collapse to 27 distinct SQL texts but 115 distinct pairs, because 20 of
those texts carry more than one parameter set. PostgreSQL estimates selectivity
from parameter VALUES, so one text can plan as a Seq Scan with one parameter and
an Index Scan with another. Sweeping texts would EXPLAIN each once against an
arbitrary parameter and silently drop 88 plans.

WHY --index-state IS REQUIRED. EXPLAIN replays against the database as it IS,
not as the capture found it. Without the check, EXPLAINing a report captured
with the index absent -- today, with it present -- staples Index Scan plans onto
a Seq Scan drive: one document, two cluster states, and nothing in it saying so.
The flag is checked against live `pg_indexes` and the run refuses on a mismatch.
"""

import argparse
import importlib.util
import json
import pathlib
import sys
from datetime import datetime

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE
while not (REPO / "src").is_dir() and REPO != REPO.parent:
    REPO = REPO.parent
sys.path.insert(0, str(REPO / "src"))

import query_profile as qp  # noqa: E402


def _sibling(name):
    """Reuse `profile_queries`' connection and plan helpers rather than copying.

    Two definitions of "is the index present" would be two things to keep in
    agreement, and the one that drifted would be the one nobody was reading.
    """
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


RUNS_DIR = HERE / "runs"
#: The four tables the surface touches. Their row counts are stamped on the run
#: because every plan is relative to them -- a Seq Scan at 3,064 rows and a Seq
#: Scan at 60,784 are different findings, and the 02c smoke run is the
#: precedent: at 3,064 the PK covered the grantee query and the Seq Scan the
#: audit existed for never appeared.
VOLUME_TABLES = (
    "entities",
    "grant_records",
    "policy_mapping_record",
    "principal_authentication_data",
)


def load_matrix(path):
    """Parse the report, refusing a document that did not fully parse."""
    text = pathlib.Path(path).read_text(encoding="utf-8")
    ms = qp.parse_api_statements(text)
    if not ms.clean:
        sys.exit(
            f"{path}: {ms.unparsed} statement block(s) did not parse.\n"
            "  A short worklist looks exactly like a complete one downstream.\n"
            "  Fix the parse before spending a sweep on it."
        )
    return ms


def per_api_rollup(explains, ms):
    """For each API: does anything it issues sequentially scan, and on what.

    This is the question the report leads with, and it is per-API rather than
    per-statement because that is how anyone reading it thinks about the
    surface. Statements are shared between APIs, so the rollup is a fan-out of
    the pair results, not a second measurement.
    """
    by_key = {}
    for e, pair in zip(explains, ms.pairs):
        by_key[id(pair)] = e
    out = {}
    for pair in ms.pairs:
        e = by_key[id(pair)]
        for api in pair.apis:
            row = out.setdefault(
                api,
                {
                    "statements": 0,
                    "planned": 0,
                    "skipped": 0,
                    "seq_scanned": set(),
                    "indexes_used": set(),
                    "relations": set(),
                },
            )
            row["statements"] += len(pair.apis[api])
            if e.get("skipped") or e.get("error"):
                row["skipped"] += 1
                continue
            row["planned"] += 1
            row["seq_scanned"].update(e.get("seq_scanned") or [])
            row["indexes_used"].update(e.get("indexes_used") or [])
            row["relations"].update(
                c["relation"] for c in (e.get("scans") or []) if c.get("relation")
            )
    for row in out.values():
        for k in ("seq_scanned", "indexes_used", "relations"):
            row[k] = sorted(row[k])
        #: NOT "used an Index Only Scan". This means: nothing this API issued
        #: scanned a table sequentially, AND at least one statement used an
        #: index -- i.e. the API is fully index-served. PostgreSQL's
        #: `Index Only Scan` is a different, specific node type (satisfied from
        #: the index without touching the heap) and appears in these same plans,
        #: so the two are easy to confuse. The name is kept for compatibility
        #: with run files already on disk; the workbook renames it to
        #: `fully_index_served` on the way out.
        row["uses_index_only"] = not row["seq_scanned"] and bool(row["indexes_used"])
    return out


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--matrix", required=True, help="a doc-api-sql-matrix-*.md")
    ap.add_argument(
        "--case",
        required=True,
        choices=("admin", "authorized", "unauthorized", "root"),
        help="which identity drove the report. Recorded, never inferred.",
    )
    ap.add_argument(
        "--index-state",
        required=True,
        choices=("present", "absent"),
        help="the state you believe the cluster is in. Checked against live "
        "pg_indexes; the run refuses on a mismatch.",
    )
    ap.add_argument("--host", default=None, help="PG host (default: the primary)")
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="parse and report the worklist, touch no database",
    )
    args = ap.parse_args()

    ms = load_matrix(args.matrix)
    print(f"{args.matrix}")
    print(f"  {len(ms.apis)} APIs, {ms.instances} statement instances")
    print(f"  {len(ms.pairs)} (SQL, params) pairs over {ms.texts} distinct SQL texts")
    print(f"  {len(ms.replayable)} replayable, {len(ms.refused)} refused")
    for pair, why in ms.refused:
        print(f"    - {pair.table} {pair.verb}: {why}")
    if args.dry_run:
        return 0

    pqm = _sibling("profile_queries")
    conn = pqm.pg_connect(args.host)
    pqm.assert_primary(conn)

    #: Every index on the focus table, recorded for provenance...
    live = pqm.index_state(conn)
    #: ...but the STATE is whether the ONE index this audit toggles is there.
    #: `bool(live)` was the test, and `grant_records` always has a primary key,
    #: so it answered "present" in both halves of every sweep -- unable to
    #: detect the state it guards against, and blocking the index-absent pass
    #: outright.
    live_state = "present" if pqm.has_index(conn) else "absent"
    if live_state != args.index_state:
        sys.exit(
            f"--index-state {args.index_state} but pg_indexes says {live_state}.\n"
            f"  Indexes on {pqm.FOCUS_TABLE} right now: "
            f"{', '.join(i['name'] for i in live) or '(none)'}\n"
            "  EXPLAIN replays against the database as it IS. Planning this\n"
            f"  report now would staple {live_state} plans onto a drive taken\n"
            "  in another state, and the document would not say so."
        )

    volume = {}
    for t in VOLUME_TABLES:
        try:
            volume[t] = pqm.table_rows(conn, t)
        except Exception as exc:  # noqa: BLE001
            volume[t] = f"unread: {type(exc).__name__}"

    #: analyze=False everywhere. See the module docstring -- this is what makes
    #: the write half askable at all.
    explains = pqm.explain_statements(conn, ms.pairs, analyze=False)
    rollup = per_api_rollup(explains, ms)

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = {
        "run_id": f"apiexplain-{args.case}-{stamp}",
        "case": args.case,
        "matrix": str(args.matrix),
        "index_state": args.index_state,
        "index_state_live": live_state,
        "indexes_on_focus_table": live,
        "volume": volume,
        "analyze": False,
        "apis": len(ms.apis),
        "instances": ms.instances,
        "pairs": len(ms.pairs),
        "texts": ms.texts,
        "explains": explains,
        "per_api": rollup,
    }
    RUNS_DIR.mkdir(exist_ok=True)
    dest = RUNS_DIR / f"{out['run_id']}.json"
    dest.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")

    seq = sorted({r for row in rollup.values() for r in row["seq_scanned"]})
    apis_seq = sorted(a for a, r in rollup.items() if r["seq_scanned"])
    print(
        f"\nvolume: "
        + ", ".join(
            f"{k}={v:,}" if isinstance(v, int) else f"{k}={v}"
            for k, v in sorted(volume.items())
        )
    )
    print(
        f"index {live_state}: {len(apis_seq)} of {len(rollup)} APIs "
        f"sequentially scan something"
    )
    print(f"  relations seq-scanned: {', '.join(seq) or 'none'}")
    print(f"  -> {dest.name}")
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
