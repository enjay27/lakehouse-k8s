# Active Service Testing State

**Index, not the record.** Current state below; everything else is a link into
[`.memory/`](.memory/README.md). If you are picking this up cold, read the
handoff named in *Now* — it is standalone.

## Now — 2026-08-31

**Task: EXPLAIN every API in `doc-api-sql-matrix-latest.md`, under three identities.** Plan is standalone — read [`PLAN-api-index-matrix.md`](diagnostics/api-sql-profile/PLAN-api-index-matrix.md) first.
43 APIs, 505 statement instances, **115 distinct (SQL, params) pairs** — the pair is the sweep unit, not the
27 distinct SQL texts. Driven as admin / authorized / unauthorized, each from a **restarted Polaris** (cold
cache), then EXPLAINed with each case's own parameters, both index states, plain EXPLAIN so writes are safe.

**Phase 3 (Claude, offline) is ~60% done and BLOCKS the drives.** Landed: `parse_api_statements` (pair-keyed,
parse-audit guard); `_summarise_plan` reports every scan node; `explain_statements(analyze=False)`;
`src/api_surface.py`, the 43 ops as a catalogue any identity can drive. **143 tests green.** REMAINING:
probe-fixture setup/teardown (nb cells 14/35), the matrix renderer (cell 33), and runners
`drive_api_surface.py` + `explain_api_matrix.py`. Kade's Phases 0–2 (dump, seed, archive) need no code.

Prior task done: the index contrast — 572 pages vs 3 — in [`doc-grant-index-contrast-20260831.md`](diagnostics/api-sql-profile/doc-grant-index-contrast-20260831.md).
Pass B stays blocked on the statement-count asymmetry; see [`HANDOFF-pass-b.md`](diagnostics/api-sql-profile/HANDOFF-pass-b.md).

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
