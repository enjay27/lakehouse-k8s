# Active Service Testing State

**Index, not the record.** Current state below; everything else is a link into
[`.memory/`](.memory/README.md). If you are picking this up cold, read the
handoff named in *Now* — it is standalone.

## Now — 2026-09-04 (session 7)

**Read [`log-coverage/PLAN-log-coverage-v3.md`](log-coverage/PLAN-log-coverage-v3.md) first — standalone.**

**v3 IS DEPLOYED and the harness now covers it; the run has not happened yet.** Run 1's finding
(the v2 policy was written and never installed) is resolved: the ConfigMap carries
`89aa2624f1f5…` and matches the file. v3 deletes per-day dedup, **keeps every `POST` under
`/api/management/`** — closing the audit hole where a credential reset left no trace — counts
every successful read, and adds a **scheduled flush report** on its own stream
(`{app="polaris-shipper-report"}`), schema v1, three record types per window.

**Verified offline against the deployed Lua, no cluster needed:** 14/14 record dispositions match
v3; three report types with agreeing margins; **zero-carry and carry decay** across three
simulated windows via the filter's own `_now_override`; all six `resource_kind` values;
`/metrics` folds onto its table (v2 emitted two rows); an error lands in `__other__` and never
creates a key. **67 tests green** (`test_log_coverage` 40, `test_vlogs` 27).

**Two findings about the filter, not the harness.** (1) **A startup blind spot:** `report_tick`
opens its first window on the FIRST tick and `count_record()` returns while `counts` is nil, so
records between shipper start and that tick appear in NO report — bounded by the 30s tick
interval, and it explains the first observed report exactly. (2) `access_kept + access_counted ==
access_seen` is **tautological** (`build_report` computes `access_kept` by subtraction); the only
real self-check is the resource/principal margin pair.

**THE ARRAY SPLITS — settled live 2026-09-04 08:23Z.** `{summary: 1, resource: 3,
principal: 2}` for one window; VictoriaLogs indexes the numbers as numbers (`requests:>0`
matched); no tick leak; **zero-carry and carry decay hold in the pipeline**, 3 of 3 rows carried
at an explicit 0 and none carried a third time; `report_seq` 20→21, counters reset, one summary
per window per host. **68 tests green under real `pytest`.** Nothing about the report is
unverified now except a full driven run.

**Fast-run settings written 2026-09-04** (sha `063c184df3f9…`): `WINDOW_SECONDS` 1800→**30**,
dummy `Interval_Sec` 30→**5** (6 ticks per window, so jitter cannot skip one). **TEMPORARY —
revert both together.** Nothing hardcodes them; `Policy.window_seconds`/`tick_seconds` read the
deployed file, and the tick-rate test broke correctly on the change instead of passing
vacuously. **68 tests green at the new settings.**

**Two harness bugs the verify run caught**, both of which would have fired on every window of
the real run: `check_invariants` read VictoriaLogs' own `_stream`/`_stream_id` as schema drift,
and the skipped-window check compared window starts across a shipper restart and the 1800→30
change, reporting the switch itself as a skipped window. Both fixed, both now tested.

**Next:** run the notebook, cells 0–15. `black`/`isort` still not runnable from Cowork; `pytest`
runs on Kade's machine and is green.

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
