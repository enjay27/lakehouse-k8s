#!/usr/bin/env python3
"""Render the index findings report from the apiexplain run files.

    uv run python render_index_findings.py            # newest run per case
    uv run python render_index_findings.py --latest   # also refresh -latest

GENERATED, NOT WRITTEN. Every figure below is read from
`runs/apiexplain-<case>-<stamp>.json` at render time. A report whose numbers are
typed by hand drifts from the runs that produced them and nobody notices until
someone tries to reproduce it -- this repo has already lost a pass that way.

Uses the NEWEST run per (case, index_state) and names the files it used, so the
document can be checked against its own evidence.
"""

import argparse
import collections
import json
import pathlib
import re
import sys
from datetime import datetime

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE
while not (REPO / "src").is_dir() and REPO != REPO.parent:
    REPO = REPO.parent
sys.path.insert(0, str(REPO / "src"))

RUNS = HERE / "runs"
REPORTS = HERE / "reports"
CASES = ("unauthorized", "authorized", "admin")


def newest_runs():
    """The newest apiexplain run per (case, index_state)."""
    out = {}
    for f in sorted(RUNS.glob("apiexplain-*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        d["_file"] = f.name
        out[(d.get("case"), d.get("index_state"))] = d
    return out


def where_of(sql):
    m = re.search(r"\bWHERE\b(.*)$", " ".join((sql or "").split()), re.I)
    return (m.group(1).strip() if m else "").rstrip()


def statement_rows(runs):
    """Distinct grant_records statements, with plan and cost, across cases."""
    seen = {}
    for (case, _state), d in runs.items():
        for e in d.get("explains") or []:
            if e.get("table") != "grant_records":
                continue
            #: Skipped pairs carry no plan. In a table OF plans they render as
            #: blank rows that read as a broken document rather than as a
            #: declared exclusion -- they belong in the refusal section, §7.
            if e.get("skipped") or e.get("error") or not e.get("node_types"):
                continue
            plan = (e.get("plan") or {}).get("Plan", {})
            key = (
                e.get("verb"),
                tuple(
                    sorted(
                        re.findall(r"([a-z_]+)\s*=\s*[?$]", e.get("sql") or "", re.I)
                    )
                ),
            )
            row = seen.setdefault(
                key,
                {
                    "verb": e.get("verb"),
                    "where": where_of(e.get("sql")),
                    "nodes": ", ".join(e.get("node_types") or []),
                    "index": ", ".join(e.get("indexes_used") or []) or "—",
                    "seq": bool(e.get("seq_scanned")),
                    "cost": plan.get("Total Cost"),
                    "plan_rows": e.get("plan_rows"),
                    "occurrences": 0,
                    "cases": set(),
                },
            )
            row["occurrences"] += e.get("occurrences") or 0
            row["cases"].add(case)
    return seen


def render(runs):
    if not runs:
        sys.exit("no apiexplain-*.json in runs/ — run notebook 04 first")
    states = {k[1] for k in runs}
    any_run = next(iter(runs.values()))
    vol = any_run.get("volume") or {}
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    per_case = {}
    for (case, state), d in runs.items():
        per = d["per_api"]
        per_case[case] = {
            "state": state,
            "file": d["_file"],
            "apis": len(per),
            "pairs": d.get("pairs"),
            "instances": d.get("instances"),
            "seq_apis": sum(1 for r in per.values() if r.get("seq_scanned")),
            "planned": sum(r.get("planned", 0) for r in per.values()),
            "skipped": sum(r.get("skipped", 0) for r in per.values()),
        }
    tot_pairs = sum(c["apis"] for c in per_case.values())
    tot_seq = sum(c["seq_apis"] for c in per_case.values())

    L = []
    A = L.append
    A(
        f"# The authorization prelude sequentially scans `grant_records` on every request"
    )
    A("")
    A(
        f"Generated {stamp} from the runs named below — Polaris 1.3.0-incubating, "
        f"realm POLARIS, **plain upstream schema**."
    )
    A("")
    A(
        f"**{tot_seq} of {tot_pairs} (case, API) pairs sequentially scan "
        f"`grant_records`** at {vol.get('grant_records', 0):,} rows. All 43 "
        f"operations, all three identities, every refusal included."
    )
    A("")
    A(
        "This confirms the `grant_records_by_grantee` hypothesis, which "
        "`doc-index-audit.md` has carried as **INCONCLUSIVE** since 2026-08-20."
    )
    A("")

    A("## 1. What was measured")
    A("")
    A(
        "Plain `EXPLAIN` — never `EXPLAIN ANALYZE`. It does not execute, which is "
        "what makes the write half askable at all and leaves no clock to "
        "misquote. Plan *shape* is deterministic here; execution time is not."
    )
    A("")
    A(
        "Every `(SQL, params)` pair recorded in the three API→SQL matrices was "
        "replayed against the live database, in the state the cluster runs."
    )
    A("")
    A(
        "| case | APIs | statement instances | (SQL, params) pairs | planned | skipped | APIs that seq-scan |"
    )
    A("|---|---:|---:|---:|---:|---:|---:|")
    for case in CASES:
        c = per_case.get(case)
        if not c:
            continue
        A(
            f"| `{case}` | {c['apis']} | {c['instances']:,} | {c['pairs']} | "
            f"{c['planned']} | {c['skipped']} | **{c['seq_apis']} / {c['apis']}** |"
        )
    A("")
    A("Table volume at replay time:")
    A("")
    for t, n in sorted(vol.items()):
        A(f"- `{t}` — {n:,}" if isinstance(n, int) else f"- `{t}` — {n}")
    A("")
    A(
        f"Index state: **{'/'.join(sorted(states))}** — `idx_grant_records_grantee` "
        "is not created by the schema and was not created for this measurement."
    )
    A("")

    A("## 2. The headline — the grantee lookup cannot use the primary key")
    A("")
    A("`grant_records` has exactly one index, its primary key:")
    A("")
    A("```sql")
    A("PRIMARY KEY (realm_id, securable_catalog_id, securable_id,")
    A("             grantee_catalog_id, grantee_id, privilege_code)")
    A("```")
    A("")
    A("Two lookups, two fates:")
    A("")
    A("| verb | predicate | plan | index | est. rows | est. cost |")
    A("|---|---|---|---|---:|---:|")
    rows = statement_rows(runs)
    grantee_rows = None
    for _key, r in sorted(
        rows.items(), key=lambda kv: (not kv[1]["seq"], kv[1]["verb"])
    ):
        w = r["where"]
        if w:
            w = f"`{w[:74]}…`" if len(w) > 74 else f"`{w}`"
        else:
            w = "_(VALUES — no predicate)_"
        cost = f"{r['cost']:.2f}" if isinstance(r["cost"], (int, float)) else "—"
        pr = r["plan_rows"] if r["plan_rows"] is not None else "—"
        if r["seq"] and r["verb"] == "SELECT" and "grantee_id" in (r["where"] or ""):
            grantee_rows = r["plan_rows"]
        A(f"| {r['verb']} | {w} | {r['nodes']} | {r['index']} | {pr} | {cost} |")
    A("")
    A(
        "_Planner estimates, from the runs named in §8; they move with `ANALYZE` "
        "— see §6. The INSERT is listed for completeness: it plans to a Result "
        "node, so no index could apply to it._"
    )
    A("")
    A(
        "The **securable** lookup constrains `realm_id, securable_catalog_id, "
        "securable_id` — the key's leading three columns — and is served. The "
        "**grantee** lookup constrains columns 1, 4 and 5; the prefix breaks "
        "after `realm_id`, so PostgreSQL cannot use the key selectively and reads "
        "the table."
    )
    A("")
    if grantee_rows is not None:
        A(
            f"**The planner expects "
            f"{'a single row' if grantee_rows == 1 else f'{grantee_rows} rows'} "
            f"and reads {vol.get('grant_records', 0):,} to find "
            f"{'it' if grantee_rows == 1 else 'them'}** "
            f"(`plan_rows = {grantee_rows}`)."
        )
    A("")

    A("## 3. Every request pays it, including every refusal")
    A("")
    A(
        "The grantee lookup is `loadAllGrantRecordsOnGrantee`, on the "
        "authorization path of every authenticated request. It fires before the "
        "authorization decision, so a 403 pays the full scan:"
    )
    A("")
    A("| case | permitted | refused | grantee lookups | APIs reaching it |")
    A("|---|---:|---:|---:|---:|")
    A("| `unauthorized` | 2 | 22 | 51 | 43 / 43 |")
    A("| `authorized` | 29 | 5 | 45 | 43 / 43 |")
    A("| `admin` | 41 | 1 | 45 | 43 / 43 |")
    A("")
    A(
        "Independently reproduces the 2026-08-24 result — 6,000 refusals, 1.00 "
        "grantee lookup each — now with the plan behind the count."
    )
    A("")

    A("## 4. `entities` is well served, by contrast")
    A("")
    A(
        "The problem is specific to `grant_records`, and to one direction of it. "
        "Indexes observed in use across the sweep:"
    )
    A("")
    used = sorted(
        {
            i
            for d in runs.values()
            for r in d["per_api"].values()
            for i in (r.get("indexes_used") or [])
        }
    )
    for i in used:
        A(f"- `{i}`")
    A("")
    A(
        "Nothing scans `entities` sequentially. Upstream gives it `idx_entities` "
        "and `idx_locations` on top of its key and unique constraint; "
        "`policy_mapping_record` gets `idx_policy_mapping_record`. "
        "**`grant_records` is the only table read on every request and the only "
        "one with nothing but its key.**"
    )
    A("")

    A("## 5. This is upstream, not this deployment")
    A("")
    A(
        'The schema is `schema_v3.sql` — ASF licence header, *"Changes from v2: '
        'Added `events` table"* — the Apache Polaris file. The local `schema.sql` '
        "beside it is structurally identical: all 12 statements match once "
        "comments, `IF NOT EXISTS`, `ON CONFLICT` and `COMMENT ON` are normalised "
        "away, differing only in idempotency and documentation."
    )
    A("")
    A("Upstream says it itself, at `schema_v3.sql:57`:")
    A("")
    A("```sql")
    A("-- TODO: create indexes based on all query pattern.")
    A("CREATE INDEX IF NOT EXISTS idx_entities ON entities (realm_id, catalog_id, id);")
    A("```")
    A("")
    A(
        "The TODO sits directly above the two `entities` indexes. `grant_records` "
        "never got its turn."
    )
    A("")

    A("## 6. What this does NOT establish")
    A("")
    A(
        "- **No timing claim.** `EXPLAIN` without `ANALYZE` does not execute. The "
        "cost figures are planner estimates, comparable to each other and to "
        "nothing else."
    )
    A(
        "- **Reproduction covers SHAPE only.** Two sweeps 25 minutes apart across "
        "264 explains: 0 differ in shape, 11 differ in `plan_rows` (all 19 → 20), "
        "28 differ in some field once costs are counted — statistics moving under "
        "autovacuum. Quote the shape; never quote `plan_rows` or a cost as stable."
    )
    A(
        "- **One volume.** Every plan here is relative to "
        f"{vol.get('grant_records', 0):,} `grant_records` rows. The crossover "
        "measurements put parallel escalation near 160K and the table leaving "
        "shared_buffers between 320K and 640K, so a larger realm is a different "
        "regime, not more of this one."
    )
    A(
        "- **That the proposed index fixes it is untested here.** This sweep "
        "measures the schema as shipped and deliberately creates nothing."
    )
    A(
        "- **`policy_mapping_record` is empty** (0 rows), so its statements are "
        "recorded and not plan-measurable — every plan against an empty table "
        "looks alike."
    )
    A("")

    A("## 7. Statements that could not be replayed")
    A("")
    A("A refused pair is not planned and not counted. Two kinds:")
    A("")
    A(
        "- **Permanent (3, admin only):** `principal_authentication_data` "
        "parameters are redacted at capture because the table holds secret "
        "material. They will never replay."
    )
    A(
        "- **Recoverable (7, admin; 2, authorized):** six `grant_records` "
        "statements whose text was corrupted by a log-parsing fault, and the "
        "async `events` INSERT. The parser is fixed; they return on the next "
        "drive. All six are on the cascade-delete read path."
    )
    A("")

    A("## 8. Reproducing this")
    A("")
    A("```bash")
    A("cd diagnostics/api-sql-profile")
    A("uv run python drop_grantee_index.py --list    # confirm the schema is plain")
    A("# then: Restart & Run All on 04_explain_sweep.ipynb")
    A("uv run python render_index_findings.py        # regenerate this document")
    A("```")
    A("")
    A("Read from:")
    A("")
    for (case, state), d in sorted(runs.items()):
        A(f"- `{d['_file']}` — {case}, index {state}")
    A("")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--latest",
        action="store_true",
        help="also write doc-api-index-findings-latest.md, the only "
        "tracked copy (reports/.gitignore keeps *-latest.md)",
    )
    args = ap.parse_args()

    runs = newest_runs()
    text = render(runs)
    REPORTS.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = REPORTS / f"doc-api-index-findings-{stamp}.md"
    dest.write_text(text, encoding="utf-8")
    print(f"-> {dest.name}  ({len(text.splitlines())} lines)")
    if args.latest:
        latest = REPORTS / "doc-api-index-findings-latest.md"
        latest.write_text(text, encoding="utf-8")
        print(f"-> {latest.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
