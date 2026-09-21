# Active Service Testing State

**Index, not the record.** Current state below; everything else is a link into
[`.memory/`](.memory/README.md). If you are picking this up cold, read the
handoff named in *Now* — it is standalone.

## Now — 2026-09-21 (session 17b: the fixes measured, and three more in)

**POLARIS IS 1.6.0** (since 2026-09-18 17:33 KST). `init_env` prints a config string and nothing
measures the server, so re-read old notes with that in hand — the 500 ladder PROVOKING is a version
difference. **The denominator moved** 19 minutes after run `1789950539`; `inventory.json` records
both fingerprints now and `assert_denominator` fails on drift. `api_report.py:307` still hardcodes
the old version.

**RUN `1789955605` MEASURED SESSION 17's FIXES: +8 on the shared 286-cell subset** (231 -> 239),
decomposing exactly as +6 fixture view, +3 rename family, −1 `renameView` 409. Raw 245/297, 35/65
operations complete — **quote the +8, not the 245/297**, the denominators differ. **198/198
in-window kept access lines are tagged** (was 167/186), which is what makes `counted_404` = 100 =
grid 91 + teardown 9 checkable at all. Gate 2 reproduced at 1941 bytes. The ladder catalog no
longer leaks.

**THE FIXTURE CATALOG STILL DOES, AND THAT IS THE NEXT ANSWER TO GET.**
`apimatrix1789955605_shared` deleted 204 and `delete catalog` still 400: *"cannot be dropped, it is
not empty"*. The suspect is `createNamespace`'s 400 cell returning 500 with a null namespace. The
teardown now walks nested namespaces, lists roles instead of naming them, purges, and prints
`remaining_in_catalog` — **an empty inventory is itself the finding**, and the next drive resolves
it.

**ALSO IN (all unverified):** one id per call, so `ISSUED` claims an equality rather than "at
least"; `PAYLOADS` may be keyed by target, so the rename 409s have a source that survives phase B
and `updateTable` 409 carries a requirement that cannot hold. **Open and deliberately undecided:**
`replaceView` 400/409 both answer 200, which turns on whether an explicit 400 payload may override
the parse-time malform strategy — the thing that keeps eighteen cells byte-identical across runs.

**NEEDS KADE (unchanged):** a real principal credential in `availability/polaris_availability_test.ipynb`
cell 2 (deliberately uncommitted); `04_explain_sweep.ipynb`'s `latest_report()` returns `hits[-2]`;
`03_api_index_matrix` has a literal `clientSecret` in `HEAD`. **Fast-run settings are live and
TEMPORARY** (30/5): revert together and re-check that the tick divides the window.

**START FROM [`sessions/2026-09-21-the-denominator-and-the-view.md`](.memory/sessions/2026-09-21-the-denominator-and-the-view.md)**,
Part 6 for the current state. The replica-staleness notebook is still UNRUN and run 1's `REFUTED`
is withdrawn ([`2026-09-17`](.memory/sessions/2026-09-17-replica-staleness-probe.md)).

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
