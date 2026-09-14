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

**A ROW LABELLED W HOLDS THE TRAFFIC OF W+1 — a constant −30s, measured, agreed by every summary
row.** The containment invariant failed **6/6 windows**: `06:19:00..06:19:30` carries records from
`06:19:30.587..06:19:31.494`. **This explains Gate 2 and Gate 4 completely** — phase E's commit is
labelled 06:17:30, so Gate 2 asking 06:18:00 was handed phase F's DELETE, exactly what its scope
printed. Compensated by `WINDOW_OFFSET_S`, **derived at collection**, zero when local-k8s fixes it,
refusing to guess if rows disagree. **The invariant still FAILS on purpose.** **RETRACTED: the two
Gate 4 items already sent to local-k8s were measured in a window with no grants in it.**

**RULE 6 IS PROVEN BY QUANTITY.** Run `1789370776`, 11 report windows: filter says seen **433**,
kept **343**, counted **90**; the index holds **exactly 343**. **Delta 0** — so the 90 counted records
are demonstrably absent, and nothing was lost in transit. Margin holds **11/11 rows**. Zero successful
GET/HEAD among the kept, on a second run. **`last_write_bytes` works** (536 / 117 / read 53, absent at
0 bytes); Gate 2's "the field did not fire" was wrong and is corrected.

**THE OFFSET'S MECHANISM IS VISIBLE AND NO SHIFT CAN WORK.** Every phase lands one window early
(label 07:26:30 = phase C driven at 07:27:00, and so on down the run), and the single offset-0 row is
the FIXTURE-SETUP window, whose traffic is spread rather than a post-boundary burst. The window a row
gets depends on WHEN INSIDE IT the traffic landed. `{-30: 5, 0: 1}` is signal, not noise — the fix is
a **`report_seq` join** via the summary row's own record bounds.

**THE REPORT IS NOW SAFE TO SEND, and it is much shorter.** The findings cell read `GATES` and never
`INVARIANTS`, so the window attribution — proven three runs running — reached no document while two
unreproduced Gate 4 items went to local-k8s. Invariants are findings now and the window one leads.
The guard meant to hold those items back had **inverted** (it tested `WINDOW_OFFSET_S`, which is 0
both when there is no offset and when none could be determined); it gates on `WINDOWS_TRUSTED` now,
derived from the invariant, failing closed. The four 500s moved to a **Build findings** section:
Polaris facts, not pipeline work.

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
