# Active Service Testing State

**Index, not the record.** Current state below; everything else is a link into
[`.memory/`](.memory/README.md). If you are picking this up cold, read the
handoff named in *Now* — it is standalone.

## Now — 2026-09-07 (session 8)

**Read [`log-coverage/PLAN-log-coverage-v3.md`](log-coverage/PLAN-log-coverage-v3.md) first — standalone.**

**v3 is deployed and run 1 happened (`1788511328`, 132 calls, correlation exact on all 132).
The report works; its results document cannot be trusted as it stands.** Settled: the policy
keeps every `POST` under `/api/management/` (the v2 audit hole, where a credential reset left
no trace), counts every successful read, and emits a flush report per window on its own stream;
Fluent Bit splits the array, VictoriaLogs indexes the numbers as numbers, zero-carry and carry
decay hold in the pipeline and not only in the oracle.

**NOT settled, and the next run's first question: run 1's oracle diff FAILED.** `oracle diff,
THIS run's fixture resources | 66 mismatches` sits two lines under `merged invariants | OK`,
and none of the 66 was named. One query decides which kind of failure it is —
`app:polaris-shipper-report | stats by (window_start, report_type) count()` over
08:41:00–08:43:30: traffic in `08:41:30` means the run was split and cell 10 read part of it;
none means the pipeline and the deployed Lua disagree. `.memory/active-issues.md`.

**Session 8 reviewed that document against the code that wrote it: nine harness defects, none
in the filter.** Kept management POSTs were counted from a display column truncated to 58
characters (six, not five); `principal_row` was a constant, hiding that ONE identity drove the
run — which makes the margin equality satisfiable by a global counter; the merged row count and
the record total reconciled against nothing; `window_start`/`counted_where` (PLAN 7) were
missing; four named assertions were computed and never stated. The notebook now drives **two
principals with different mixes**, names every fixture mismatch, and states each assertion
PASS/FAIL. `.memory/roadmap.md`; wrong turns in
`.memory/sessions/2026-09-07-log-coverage-harness-review.md`.

**Fast-run settings are live and TEMPORARY** (sha `063c184df3f9…`): `WINDOW_SECONDS` 1800→**30**,
`Interval_Sec` 30→**5**, both read from the deployed file, never hardcoded. **Revert together.**

**Next:** re-run the notebook, read the oracle diff row by row, then revert those two values.

**Gate:** 81 green under the minimal pytest stand-in (`test_log_coverage` 54, `test_vlogs` 27),
and the oracle now runs from Cowork (`luatex --luaonly` + access to `~/hynix/local-k8s/logging`).
`pytest`/`black`/`isort` still not installable there — **the real gate is Kade's `pytest`.**

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
