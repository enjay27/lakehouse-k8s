"""Re-derive a capture's OP LABELS, and nothing else. No database, ever.

WHY THIS EXISTS
---------------
`query_profile.operation_templates` classified against `api_sweep`'s frozen
13-op surface. Every capture driven by an AUTHORISED tier therefore left its
other 16 operations unclassified, and an unclassified request keeps its raw
path as its label -- so `GET  /policies` appeared as 200 one-request "ops"
named `.../admin3_catalog/namespaces/ns1/policies`, while the template row for
it showed nothing at all.

The totals hid it. 75 requests missing from 13 template rows and 77 landing on
61 raw-path rows net to +2, which is exactly what the capture-liveness probe
costs, so the reconciliation summary line read normal on every one of the six
captures. Only the per-row composition showed the fault.

The templates are fixed now (the full surface is the default). But the six
qprofile JSONs already on disk hold something that cannot be recomputed
without the cluster -- the EXPLAIN plans, taken in a specific index state that
no longer exists for half of them. Re-running `profile_queries.py` to fix the
labels would overwrite those plans with nothing.

So this recomputes ONLY the label-derived sections, into a separate file. The
qprofile JSON stays the EXPLAIN record; this is the label record; the combined
report joins them. Nothing here opens a database connection.
"""

import argparse
import json
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "src"))

import query_profile as qp  # noqa: E402

RUNS_DIR = HERE / "runs"
FOCUS_TABLE = "grant_records"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--capture", required=True)
    ap.add_argument("--run", required=True, help="run id or run JSON filename")
    ap.add_argument("--chunk-mb", type=int, default=8)
    args = ap.parse_args()

    capture = HERE / args.capture
    log = capture / "polaris.log"
    if not log.exists() or log.stat().st_size == 0:
        sys.exit(f"{log} is missing or empty -- a capture that recorded nothing")

    run_path = RUNS_DIR / f"privscan-{args.run}.json"
    if not run_path.exists():
        name = args.run if args.run.endswith(".json") else args.run + ".json"
        run_path = RUNS_DIR / name
    if not run_path.exists():
        sys.exit(f"no run manifest for {args.run!r}")
    run = json.loads(run_path.read_text(encoding="utf-8"))

    t0 = time.time()
    corr = qp.correlate(str(log), chunk_bytes=args.chunk_mb << 20)
    shapes = qp.statement_profile(corr.profiles)
    rec = qp.reconcile(corr, run)

    labels = {}
    for label, ps in corr.by_label().items():
        tables = {}
        for p in ps:
            for st in p.statements:
                key = (st.table or "?").lower()
                tables[key] = tables.get(key, 0) + 1
        statuses = {}
        for p in ps:
            statuses[str(p.status)] = statuses.get(str(p.status), 0) + 1
        labels[label] = {
            "surface": ps[0].surface,
            "requests": len(ps),
            "statuses": statuses,
            "statements": sum(p.n_statements for p in ps),
            "tables": dict(sorted(tables.items(), key=lambda kv: -kv[1])),
        }

    out = {
        "capture": args.capture,
        "run_id": run.get("run_id"),
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "templates": len(qp.operation_templates()),
        "access_records": corr.access_records,
        "statements": corr.statements,
        "orphan_statements": corr.orphan_statements,
        "unclassified_paths": corr.unclassified_paths,
        "reconciliation": rec,
        #: Recomputed here for the same reason the labels are: the class
        #: `unclassified (not an op)` is assigned from the SURFACE, and an op
        #: that failed to match a template had no surface. On the authz and
        #: admin captures that put 1,600 and 75 permitted requests into the
        #: not-an-op bucket, which is the bucket whose whole purpose is to keep
        #: non-API traffic out of the permitted mean.
        "outcome_classes": qp.prelude_by_outcome(corr, table=FOCUS_TABLE)[0],
        "per_label": qp.per_label_summary(corr, table=FOCUS_TABLE),
        "labels": labels,
        #: distinct statement shape -> the ops that issued it. Joins to
        #: `qprofile[...]["explains"][]["sql"]` on the same normalised key,
        #: which is what makes a scan type attributable to an operation.
        "shapes": [
            {
                "sql": key,
                "table": sp.table,
                "verb": sp.verb,
                "occurrences": sp.occurrences,
                "requests": sp.requests,
                "labels": sp.labels,
            }
            for key, sp in sorted(shapes.items(), key=lambda kv: -kv[1].occurrences)
        ],
    }

    dest = RUNS_DIR / f"relabel-{out['run_id']}.json"

    #: `prelude_by_outcome` returns each class's statement shapes as a set.
    def _jsonable(o):
        if isinstance(o, (set, frozenset)):
            return sorted(o)
        raise TypeError(f"not JSON-serialisable: {type(o).__name__}")

    dest.write_text(json.dumps(out, indent=2, default=_jsonable), encoding="utf-8")
    unc = (
        sum(v for v in corr.unclassified_paths.values())
        if isinstance(corr.unclassified_paths, dict)
        else 0
    )
    print(
        f"{dest.name}: {len(labels)} ops, {len(out['shapes'])} shapes, "
        f"{corr.access_records} requests, {corr.statements} statements, "
        f"{len(corr.unclassified_paths)} unclassified paths ({unc} requests), "
        f"reconcile clean={rec['clean']} probe={rec['probe_total']:+d} "
        f"unexplained={rec['unexplained_total']:+d}  [{time.time() - t0:.0f}s]"
    )
    return 0 if rec["clean"] else 2


if __name__ == "__main__":
    sys.exit(main())
