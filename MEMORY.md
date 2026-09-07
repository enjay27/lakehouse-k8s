# Active Service Testing State

**Index, not the record.** Current state below; everything else is a link into
[`.memory/`](.memory/README.md). If you are picking this up cold, read the
handoff named in *Now* — it is standalone.

## Now — 2026-09-07 (session 8)

**Read [`log-coverage/PLAN-log-coverage-v3.md`](log-coverage/PLAN-log-coverage-v3.md) first — standalone.**

**Run 3 (`1788745242`) is the first run whose report can be checked against itself throughout,
and the two questions it left open are now closed.** The fixture diff is down to 30 with **0**
metadata lines and, for the second run running, **0 mismatches in the direction that would mean
a lost record**; all four named assertions PASS; the margin holds across four principals with
distinct mixes; 6 of 6 management POSTs; volume reconciles exactly. What remains in that diff
is entirely the notebook's own fixture setup and teardown, which are not in `ALL_CALLS` — the
last structural gap between oracle and pipeline.

**STACK TRACES: the "none exist" finding was WRONG and is retracted.** Polaris emits Quarkus's
**structured** exception output — an object with a `frames` array of `{class, method, line}` —
so `grep -c stackTrace` found nothing for the same reason the notebook reported `0 of 5`:
**both searched for a name this build does not use, and agreeing with each other was not
corroboration.** `lc.exception_fields` now reports the field NAMES, since absence and a
mis-named search have opposite remedies. **Open again, and unmeasured:** whether the payload is
in the log FILE (as opposed to container stdout, which reaches OpenSearch by another path), and
whether it survives into VictoriaLogs. Only the second is about the pipeline under test.

**THE DROP COUNTER now works.** Fluent Bit's Prometheus encoder appends a millisecond timestamp
after the sample value and the parser was reading it as the value (hence 7,154,980,971,680).
Fixed; the real figure is 1,943 and it reconciles with the tick and tail counters exactly.

**THE MISSING WINDOWS are the MacBook sleeping.** Transit loss is excluded (output `errors`,
`retries_failed`, `dropped_records` all 0 since the pod started); the tick input has fired
1,495 times against ~65.5h of uptime, ~3%. The OrbStack VM suspends with the host, so windows
never open. A gap here is expected after any sleep — **and no report-stream measurement
spanning a sleep can be read as elapsed time.**

**Fast-run settings still live and TEMPORARY** (sha `063c184df3f9…`): `WINDOW_SECONDS` 30,
`Interval_Sec` 5. **Revert together** when the run of record is done.

**Next:** `neg.500_null_pointer` has returned 200 for three runs — the ERROR path has only ever
been driven by accident, via the PG-HA 500s. Fix that probe, decide whether to tag
setup/teardown into `ALL_CALLS`, take the run of record, then revert.

**Gate:** 88 green under the minimal pytest stand-in; Kade's `pytest` last ran 719 passed /
1 pre-existing `test_privilege_scan` renderer drift.

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
