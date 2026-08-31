# Active Service Testing State

**Index, not the record.** Current state below; everything else is a link into
[`.memory/`](.memory/README.md). If you are picking this up cold, read the
handoff named in *Now* — it is standalone.

## Now — 2026-08-31

**Task: EXPLAIN every API in `doc-api-sql-matrix-latest.md`, under three identities.** Plan is standalone —
read [`PLAN-api-index-matrix.md`](diagnostics/api-sql-profile/PLAN-api-index-matrix.md) first. 43 APIs, 505
statement instances, **115 distinct (SQL, params) pairs** — the pair is the sweep unit, not the 27 SQL texts.
Cases: admin (seeded `service_admin`, ~1,100 grants) / authorized (`authz`, 52) / unauthorized (zero grants),
each from a **restarted Polaris**, then plain EXPLAIN (no ANALYZE, so writes are safe) in both index states.

**PHASE 3 IS DONE — 167 tests green, nothing has touched a cluster.** Built: `parse_api_statements`
(pair-keyed + parse audit), `_summarise_plan` reporting every scan node, `explain_statements(analyze=False)`,
`src/api_surface.py` (43 ops + fixture setup/teardown), `src/api_report.py` (renderer; round-trip tested
against the parser), and runners `drive_api_surface.py` + `explain_api_matrix.py`.

**NEXT IS KADE'S, and it is Phases 0–2 then 4–5:** dump + prove the restore → `--probe-policy` → seed
(1000 users, 5 views + 5 generic tables/ns, plus a **verified zero-grant** principal) → archive the current
matrix as a **tracked** file → `drive_api_surface.py --setup`, then restart-and-drive per case
(**unauthorized, authorized, admin last**) → `explain_api_matrix.py` per case × both index states → Claude
writes the report. Of the 115 pairs, **112 replay**; the 3 refused are redacted
secret-table statements and always will be.

## Where the detail is

| read | when |
|---|---|
| [`.memory/roadmap.md`](.memory/roadmap.md) | what is done, what is next |
| [`.memory/active-issues.md`](.memory/active-issues.md) | before trusting a number or a tool (13 open, 5 resolved-but-instructive) |
| [`.memory/environments.md`](.memory/environments.md) | **before running anything** — local / dev / prod, and what must never run where |
| [`.memory/repository-map.md`](.memory/repository-map.md) | looking for where something lives |
| [`.memory/goal.md`](.memory/goal.md) | the standing objective and structural model |
| [`.memory/sessions/`](.memory/sessions/) | why a decision was made, including the wrong turns |
| [`.memory/completed.md`](.memory/completed.md) | finished structural work |

Task-specific handoffs live beside the code they describe, in
`diagnostics/api-sql-profile/HANDOFF-*.md`. They are written for someone
starting cold and are the right first read for a task; this file is the right
first read for the *project*.

## Rules for keeping this file useful

- **This file stays under ~40 lines.** Growth belongs in `.memory/`, not here.
  It was 198 lines against its own 150-line limit once, and a tracking document
  nobody finishes reading tracks nothing.
- **Update *Now* every session**, even when the answer is "unchanged".
- **A finding with a number goes in `.memory/roadmap.md`; the story goes in
  `.memory/sessions/`.** The wrong turns do not survive summarising and are the
  part most likely to be repeated.
