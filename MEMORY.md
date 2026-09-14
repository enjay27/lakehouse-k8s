# Active Service Testing State

**Index, not the record.** Current state below; everything else is a link into
[`.memory/`](.memory/README.md). If you are picking this up cold, read the
handoff named in *Now* — it is standalone.

## Now — 2026-09-14 (session 12)

**`polaris_log_coverage_v2.ipynb` HAS NEVER RUN PAST CELL 4, AND THE GATE THAT STOPPED IT WAS
HIDING ITS OWN FAILURE.** Cell 4 raised on ANY Gate 7 failure; run `1789029836` hit two idle-window
assertions and stopped, so **cells 5-42 carry `execution_count: None`** — 38 cells never executed in
that file, every defect behind them unmeasured. It also stored `detail[-2500:]` and printed
`[-20:]` of that, so **`3 FAILURE(S)` showed two and it raised about the third it had just
truncated**; `assertions` matched a word the harness never prints (always `None`); and `GATE7` was
read by no cell. **Fixed:** `[FAIL]` lines selected by CONTENT, assertions counted, failures
classified against `GATE7_SCOPED` — scoped-only records **FAIL (scoped)** and CONTINUES; anything
unrecognised, or a count that will not reconcile with the visible lines, still raises. `teardown_all`
is registered at fixture creation (idempotent, `atexit`) so an abort between §2 and §11 stops
leaking catalogs. **An abort claims everything downstream depends on what just failed — check that
claim before raising.**

**THE DEPLOYED FILTER SAYS v3 AND IS NOT v3.** Gate 7 fails three assertions and they are ONE
cause: no `transaction` resource kind (v3 added it 2026-09-10 for `transactions/commit` — the path
this grid found unclassified), and an empty string where an idle window requires
`min/max_record_time` ABSENT. `grep -c transaction` on the deployed text is **0**; the only
`transaction` in `local-k8s/logging/` is in the two documents and the test, which went ahead of the
filter as one undelivered change. **Cell 6 compares a CONSTANT and passes; Gate 0 passes; only Gate
7 can see this.** This repo is a third version — `RESOURCE_KINDS` is six values and still carries
`management`, which v3 removed. **Do not update it ahead of the filter.** All three are scoped, the
run continues, and `GATE7_PROVENANCE` is stamped into both generated documents so no figure from
such a run reads as a figure about v3.

**NOT VERIFIED END TO END.** No Cowork session can run this notebook — no `kubectl`, no `lua5.4`, no
cluster, `local-k8s` not mounted. Gate: **911 passed, 45 skipped** in the Linux VM
(`UV_PROJECT_ENVIRONMENT=$HOME/venv-linux`), Kade's macOS **956 passed**; `black` 26.5.1 leaves
`src/` unchanged and skips `.ipynb`. **The third Gate 7 failure is still unseen** — the fix makes it
visible, and whether the run then proceeds depends on what it turns out to be.

**STILL OPEN FROM SESSION 11.** Prism is gone: nothing checks a request without driving it. `_row_from`
stamps `verdict: "covered"` unconditionally (true coverage 12/20, reported 18/20) — **UNFIXED**, and
it lives in `src/make_traffic.py`, **NOT** in this notebook's path: v2 drives `mx.drive` ->
`adjudicate`, which handles MISSED correctly. Grid is **16 omit / 11 wrong-type / 0 unbreakable**,
denominator 286, and **10 verified, 1 UNVERIFIABLE — never quote 11**. Report schema **v3 on the
DaemonSet, v2 on the Deployment**. Session 8's 500 result — every route to a 500 is a closed one, run
`1788759324` — is in [`log-coverage/HANDOFF-500-coverage-2026-09-07.md`](log-coverage/HANDOFF-500-coverage-2026-09-07.md).

**NEXT SESSION STARTS FROM
[`log-coverage/HANDOFF-split-logging-test-2026-09-10.md`](log-coverage/HANDOFF-split-logging-test-2026-09-10.md)**
— steps 3-4 need BOTH folders. Step 2 DONE.

**Fast-run settings are live and TEMPORARY** (`WINDOW_SECONDS` 30, `Interval_Sec` 5). Revert
together, AFTER the api-status-matrix phase schedule, not before.

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
