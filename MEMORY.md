# Active Service Testing State

**Index, not the record.** Current state below; everything else is a link into
[`.memory/`](.memory/README.md). If you are picking this up cold, read the
handoff named in *Now* — it is standalone.

## Now — 2026-09-14 (session 12)

**THE NOTEBOOK RAN END TO END FOR THE FIRST TIME — run `1789365275`, and the pipeline HELD.** 286
calls, **286/286 correlated**, **235/235 error cells recovered: rule 3 is an assertion now.** Margins
6/6, `report_seq` contiguous, Gate 6 clean over 129 rows. **Four 500s, all `unhandled`, from malformed
bodies alone** (`getToken`, `createNamespace`, `renameTable`, `renameView`) with exception fields
intact — **the roadmap's standing question is answered: an unhandled exception is provokable on demand,
no cluster surgery.** Kade rolled the filter first, so **Gate 7 PASSES 58/58** and `GATE7_SCOPED` is
back to empty; the assertion count is **58**, neither the 16 nor the 46 the two documents claim.

**THE REPORT ASSIGNS WINDOWS BY PROCESSING TIME, NOT RECORD TIME.** Window `05:57:30..05:58:00` carries
`min_record_time 05:58:00.607` and `max 05:58:01.475` — **both past `window_end`** — and §15 passed,
because it only asked `max - min <= window_seconds` (0.87s). Fourth instance of a check that passes
while its subject is wrong. New invariant added; the offset is a local-k8s question, and it is the
mechanism behind Gate 2 going VOID.

**FIXED THIS SESSION:** the commit is now created a window clear of phase F's fixture (that CREATE was
sharing phase E's window, which is the one premise Gate 2 has); Gate 4 selects its role by **exact**
match (`mx_<run>_crole` is a prefix of `_crole2` and `_crole_doomed`, so it reported `writes=1
granted=3` against a role that received **no grants**, and that sentence shipped to local-k8s);
`teardown_all` drops the rename DESTINATIONS (leaving them is why `probe_ns` answered 409 and the
catalog delete 400); gate findings now carry real remedies.

**STILL OPEN FOR local-k8s:** Gate 4 `auth_denied=0` — a 403 on a catalog role falls to `__errors__`
instead of forcing the role row, so the `ROLE_KINDS` exemption is not firing. And the window offset.

**DO NOT "FIX" `RESOURCE_KINDS`.** It is six values with `management`; v3 emits twelve without it. But
`_policy()` resolves the **Deployment's** `fb-values.yaml` — the oracle and the whole suite test **v2**,
so the constant is right for what it tests and the predicted test failure did not happen (956 passed).
Nothing in this repo has a v3 oracle; that is the real gap.

**`min_record_time` is still `text` — and the empty-string hypothesis is now DOUBTFUL.** Same index maps
`window_start` as `date`. The difference is nine fractional digits, not emptiness. Next day's index
decides it for free.

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
