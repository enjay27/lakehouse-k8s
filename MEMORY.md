# Active Service Testing State

**Index, not the record.** Current state below; everything else is a link into
[`.memory/`](.memory/README.md). If you are picking this up cold, read the
handoff named in *Now* — it is standalone.

## Now — 2026-09-01

**Read [`HANDOFF-api-index-matrix.md`](diagnostics/api-sql-profile/HANDOFF-api-index-matrix.md) first — standalone.**

Task: EXPLAIN every API in `doc-api-sql-matrix-latest.md`, under three identities (admin / authorized /
unauthorized), each from a restarted Polaris, plain EXPLAIN, both index states. Plan:
[`PLAN-api-index-matrix.md`](diagnostics/api-sql-profile/PLAN-api-index-matrix.md); commands:
[`RUNBOOK-api-index-matrix.md`](diagnostics/api-sql-profile/RUNBOOK-api-index-matrix.md); driver:
`03_api_index_matrix.ipynb`.

**BLOCKED: all three drives completed cleanly and captured NO SQL.** Every API in all three reports reads
`0 statements` / `tables: —`. `polaris.log` is ~1,311,11x bytes in all four runs — the Polaris startup burst
and nothing after it — and the liveness gate passed because a restart's own dump supplies both the growth and
the `DatasourceOperations` lines it checks for. **Fix first:** a TRACER-level preflight (01 cell 6 already has
the pattern — `assert rec.sql_count > 0`), then re-drive. Do not re-drive before that; three runs have already
produced nothing.

Measured and worth keeping: authorized is refused exactly the 5 service-scoped ops; **admin is NOT a superset**
(`reset_principal_credentials` → 403); footprints 1 / 78 / 3,377-ceiling; volume `grant_records` 60,819,
`policy_mapping_record` 0 and unmeasurable. Tooling is done and green (183 tests).

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
