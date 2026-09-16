# Active Service Testing State

**Index, not the record.** Current state below; everything else is a link into
[`.memory/`](.memory/README.md). If you are picking this up cold, read the
handoff named in *Now* — it is standalone.

## Now — 2026-09-15 (sessions 13–14)

**Session 14: `log-coverage/polaris_api_traffic_v1.ipynb` is v2's traffic with every verification cell removed** — no OpenSearch, no kubectl, and **one window wait**: it waits once for a fresh window (lag 6.5 s at 30/5 fast-run, edit on revert), then runs B–I back to back (~6 s measured) and reports if the drive crossed a boundary. Kept cells diff against v2 only in printed strings. ~~`src/make_traffic.py` still uses `lag=0.5`~~ **fixed session 15 (2026-09-16): `drive()` requires `tick_interval_s`, one validated `_wait_for_window`, AST-tested**; **phase J added and RUN** (run `1789535345`: 6/6 calls as targeted, Polaris accepts a nested namespace; local-k8s found one table row with commit_count 2 and no phantom) — [`sessions/2026-09-16-phase-lag-and-nested-namespace.md`](.memory/sessions/2026-09-16-phase-lag-and-nested-namespace.md). Not run on the cluster. [`.memory/sessions/2026-09-15-traffic-only-notebook.md`](.memory/sessions/2026-09-15-traffic-only-notebook.md)

**THE WINDOW OFFSET WAS `lag=0.5`. THE NOTEBOOK CAUSED THE CONDITION IT SPENT THREE RUNS
REPORTING TO `local-k8s`, AND NOTHING IN THE CLUSTER IS WRONG.** A window closes when the 5 s
report tick notices its boundary — measured at **`window_end + 3.673 s`, σ < 2 ms**, and it cannot
drift while `Interval_Sec` **divides** `WINDOW_SECONDS`. Every phase fired 0.5 s past a boundary,
**inside that blind spot**, so 100 % of every burst was booked to the previous row,
deterministically. **`{-30: 5, 0: 1}` was an artefact of cell 32 flooring `min_record_time`
before differencing — raw it is `{30.5: 5, 16.9: 1}`. Do not quote the INCONSISTENT sentence, it
is withdrawn.** Fixed in four commits: `PHASE_LAG = Interval_Sec + 1.5` read from the running
ConfigMap (five call sites); `row_for()`, which picks a report row by its **records** and retires
`lbl()` / `WINDOW_OFFSET_S`; the raw displacement statistic; the invariant renamed to **`no record
fell outside its row's label window`**, because under the old name `WINDOWS_TRUSTED` would have
suppressed Gate 2 and Gate 4 forever against a pipeline behaving as designed.

**THREE SENTENCES SHIPPED TO ANOTHER TEAM AS WORK ITEMS FOR A PIPELINE THAT DID NOTHING WRONG.**
`auth_denied=0 (… fell to `__errors__`)` and `writes=1 granted=3` were **adjacent rows**, checked
in the export. Verdict strings now carry the measurement; causes moved to `GATE_REMEDIES`, which
lead with *check the resolved window — it was this both times*. **`REPORT-for-local-k8s.md` item 1
is no longer needed** and contradicts the Lua's deliberate no-re-dating decision.

**FOUND ON THE WAY, not in the handoff:** Gate 2's negative half compared **two different
windows** (`_absent` wall-clock, `_present` shifted) — a real latent bug. `INVARIANT_REMEDIES` is
keyed by the invariant's **name string** with a defaulting lookup, so a rename alone degrades a
remedy silently. **And the handoff's own §8-2 check is wrong:** `PHASE_LAG = Interval_Sec + 1.5`
lands a *correct* run just past `Interval_Sec`; the meaningful band is `[0, window_seconds)`.

**NOT VERIFIED — the notebook was not executed; it needs the cluster.** `pytest` 911/45 green
before every commit. **Next run answers exactly three things:** Gate 2 `last_write_bytes` (VOID
twice, and it is the feature), Gate 4's two FAILs (expected PASS; a FAIL with the invariant green
is the first quotable window-scoped finding this project has had), and one `_analyze` call on
`__errors__` — underscore is `ExtendNumLet`, so the guide's "the analyser splits it" is probably
wrong while `.keyword` stays right on case-folding grounds.

**NEEDS KADE:** `availability/polaris_availability_test.ipynb` holds a **real principal
credential** in cell 2 and is deliberately uncommitted; `04_explain_sweep.ipynb`'s
`latest_report()` now returns `hits[-2]`, which looks like a leftover; and `03_api_index_matrix`
already has a literal `clientSecret` in `HEAD`.

**Fast-run settings are live and TEMPORARY** (`WINDOW_SECONDS` 30, `Interval_Sec` 5). Revert
together, AFTER the api-status-matrix phase schedule — and **re-check that the tick still divides
the window**, since `PHASE_LAG` becomes 31.5 s at 1800/30.

**NEXT SESSION STARTS FROM
[`.memory/sessions/2026-09-15-window-lag-is-the-harness.md`](.memory/sessions/2026-09-15-window-lag-is-the-harness.md)**.

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
