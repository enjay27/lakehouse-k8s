# Active Service Testing State

**Index, not the record.** Current state below; everything else is a link into
[`.memory/`](.memory/README.md). If you are picking this up cold, read the
handoff named in *Now* — it is standalone.

## Now — 2026-09-07 (session 8)

**Read [`log-coverage/PLAN-log-coverage-schema-v2.md`](log-coverage/PLAN-log-coverage-schema-v2.md)
first, then [`PLAN-log-coverage-v3.md`](log-coverage/PLAN-log-coverage-v3.md) — both standalone.**

**THE DEPLOYED REPORT IS SCHEMA v2 AND THIS REPO'S ORACLE IS STILL v1.** `src/log_coverage.py`
says `SCHEMA_VERSION = 1` and its frozen field sets still carry `counted_get`, which v2 removed.
Migrating it is that plan's §1 (start at 1.1: the window merge must sum every numeric field, read
from the row's own keys — a hardcoded list has now produced the same silent failure twice here).
**Not done, and nothing that asserts on a v2 field can be trusted until it is.**

**COVERAGE: 500 ERROR now exists, and it can fail.** The ERROR path had never been driven on
purpose: `neg.500_null_pointer` returned **200 for three runs** (this build falls back to
`endpoint` when `endpointInternal` is absent), and every stored 500 arrived by accident from the
PG-HA read-after-write signature — writes that **committed**, so not evidence about unhandled
exceptions. Notebook §5c drives a **ladder** of three API-only rungs as a pure-500 burst inside
one window and stops at the first that really 500s; §11c checks **both halves** of a 500 (the
access line, kept *and* counted by rule 3; the application ERROR line, kept and counted into
nothing, carrying the trace as flattened `exception.frames`) and the pure-500 window's
`errors_5xx` / `errors_4xx` / `auth_denied`. **If no rung fires it says NOT PROVOKED and question
3 stays unanswered** — the accidental 500s are not a substitute. All three rungs are `[assumed]`;
no run has confirmed one yet.

**STACK TRACES SURVIVE, END TO END** — Quarkus's **structured** exception output reaches
VictoriaLogs intact, stored **flattened** as `exception.frames`. Reported missing twice because
both searches used a name this build does not emit. No Quarkus change is needed; what was left
was coverage, not capability, and that is §5c.

**Run 3 (`1788745242`)** remains the run whose report checks against itself throughout: fixture
diff 30, **0** metadata lines, **0 mismatches in the loss direction**, four named assertions PASS,
6 of 6 management POSTs, volume reconciles. The drop counter works (1,943). Missing windows are
the MacBook sleeping — no report-stream measurement spanning a sleep is elapsed time.

**Fast-run settings still live and TEMPORARY** (sha `d58b9203a8304030`): `WINDOW_SECONDS` 30,
`Interval_Sec` 5. **Revert together** when the run of record is done.

**Next:** run §5c and find out whether any rung fires. Then schema-v2 §1 (1.1 first), then the run
of record, then revert.

**Gate:** 705 passed / 1 pre-existing `test_privilege_scan` renderer drift, under a `uv run
--no-project` stand-in (`.venv` is a macOS build the Cowork bridge cannot execute).

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
