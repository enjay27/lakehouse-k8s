# Active Service Testing State

**Index, not the record.** Current state below; everything else is a link into
[`.memory/`](.memory/README.md). If you are picking this up cold, read the
handoff named in *Now* — it is standalone.

## Now — 2026-09-07 (session 8, run 2 of v3)

**Read [`log-coverage/PLAN-log-coverage-v3.md`](log-coverage/PLAN-log-coverage-v3.md) first — standalone.**

**Run 2 (`1788744260`, 146 calls) settled the question run 1 left open: the 66 fixture
mismatches were NOT the pipeline disagreeing with the deployed Lua.** 34 were `_stream` /
`_stream_id`, which VictoriaLogs adds on the way out and the oracle cannot have; 5 were rows
the oracle never could predict; 21 were count deltas, **every one `stored > oracle`**, all of
them the notebook's own untagged fixture setup and cleanup. **Zero mismatches in the direction
that would mean a lost record.**

**Also measured, for the first time:** the margin equality with content — four principals, none
carrying the total, `249 == access_seen - parse_errors`; **6 of 6** management POSTs (5 by
rule 5, the 403 `reset` by rule 3); volume reconciling exactly (2,416 = 2,408 + 8 + 0) with
**only 2.2% of stored records access-log** and `DatasourceOperations` at 61%; the multi-window
merge running live across 3 windows; and `type_int_key` settled (`>=400 -> 41`, `"404" -> 25`).

**Two things carried out of it.** A real **skipped window** — `00:36:00Z`–`00:37:00Z`, three
windows with no report, cause not yet distinguished between a shipper stall and transit loss;
the Fluent Bit output metrics settle it and are still readable. And **questions 1 and 3 remain
unanswered for the second run running**, because `neg.500_null_pointer` returns 200
(`error-cases/09` is stale) — so whether an exception stack trace survives this pipeline has
never been measured.

**Fast-run settings are still live and TEMPORARY** (sha `063c184df3f9…`): `WINDOW_SECONDS` 30,
`Interval_Sec` 5, both read from the deployed file. **Revert together** once the next run is in.

**Next:** re-run with the two fixes from this session (VictoriaLogs metadata out of the diff,
record times bracketed by the window range) for a fixture diff that should be near-clean; then
revert the fast-run values.

**Gate:** `pytest` on Kade's machine — **719 passed, 1 failed**, the failure being the
pre-existing `test_privilege_scan` renderer drift. That retires the `NOT VERIFIED` on `bb08dce`.

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
