# Active Service Testing State

**Index, not the record.** Current state below; everything else is a link into
[`.memory/`](.memory/README.md). If you are picking this up cold, read the
handoff named in *Now* — it is standalone.

## Now — 2026-09-07 (session 8, run 3 of v3)

**Read [`log-coverage/PLAN-log-coverage-v3.md`](log-coverage/PLAN-log-coverage-v3.md) first — standalone.**

**Run 3 (`1788745242`) is the first run whose report can be checked against itself throughout.**
The fixture diff is down to **30** with **0** metadata lines and, for the second run running,
**0 mismatches in the direction that would mean a lost record**; all four named assertions
PASS; the margin holds across four principals with distinct mixes; 6 of 6 management POSTs;
volume reconciles exactly. What remains in that diff is entirely the notebook's own fixture
setup and teardown, which are not in `ALL_CALLS` — the last structural gap, and the only thing
between it and a strict assertion.

**Questions 1 and 3 have data for the first time: 5 ERROR records, 0 carrying an exception
object.** Not yet a conclusion — Polaris may never have written a throwable, or the pipeline
may drop them; `grep -c stackTrace /deployments/logs/polaris.log` decides. Either way `_msg` is
only `Unhandled exception returning INTERNAL_SERVER_ERROR`, so **a 500 currently reaches
VictoriaLogs as proof that something failed and nothing about what.** The path was exercised by
accident (the PG-HA 500s on `create_namespace`/`create_view`); `neg.500_null_pointer` has
returned 200 for three runs.

**`fluentbit_filter_drop_records_total` has never been read correctly** — its first-ever value
was 7,154,980,971,680, four times the epoch in milliseconds. Guarded now; the parser still
needs the endpoint's real shape, which no Cowork shell can reach.

**Also open:** three consecutive report windows missing at `00:36:00Z`–`00:37:00Z`, cause not
distinguished between a shipper stall and transit loss.

**Fast-run settings still live and TEMPORARY** (sha `063c184df3f9…`): `WINDOW_SECONDS` 30,
`Interval_Sec` 5. **Revert together** when the run of record is done.

**Next:** settle the stack-trace question and the metrics shape (one command each), then decide
whether to tag setup/teardown into `ALL_CALLS` before the final run and the revert.

**Gate:** 86 green under the minimal pytest stand-in; `pytest` on Kade's machine last ran
719 passed / 1 pre-existing `test_privilege_scan` renderer drift.

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
