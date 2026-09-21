# Active Service Testing State

**Index, not the record.** Current state below; everything else is a link into
[`.memory/`](.memory/README.md). If you are picking this up cold, read the
handoff named in *Now* — it is standalone.

## Now — 2026-09-21 (session 17: the denominator moved, and five harness faults fixed)

**POLARIS IS 1.6.0** (since 2026-09-18 17:33 KST, helm rev 9). Run `1789950539` printed `Polaris
1.3.0` on every output: `init_env` prints a config string and **nothing measures the server**.
So the 500 ladder now PROVOKING is a version difference, not a mystery. `api_report.py:307` still
hardcodes the old version.

**THE DENOMINATOR MOVED 19 MINUTES AFTER THAT RUN.** 63 ops / 286 cells then, 65 / 297 now, no
`inventory.json` — so **`231/286` is unreproducible** and survives only in the notebook output at
`253f6de`. Now recorded, `history` and all, and `assert_denominator` fails on drift. The re-fetch
had already left 8 tests red and would have stopped the next drive at call 0.

**FIVE FIXES, ALL UNVERIFIED — RUNNING IT IS THE NEXT THING.** The fixture never built `fx.view`
(8 of 55 misses); phase B's renames consumed phase D's 409 targets (`createView` 409 returned
**200**); phase I and both ends of every ladder rung were untagged on every run to date; two
catalogs leaked from every run with both cleanups reporting success; `registerView` and
`signRequest` have never been driven. **Gate 2's positive half is answered** (`last_write_bytes`
1941, byte-identical); **its negative half leaves the field ABSENT, not `0`** — assert absence.

**NEEDS KADE (unchanged):** a real principal credential in `availability/polaris_availability_test.ipynb`
cell 2 (deliberately uncommitted); `04_explain_sweep.ipynb`'s `latest_report()` returns `hits[-2]`;
`03_api_index_matrix` has a literal `clientSecret` in `HEAD`. **Fast-run settings are live and
TEMPORARY** (30/5): revert together and re-check that the tick divides the window.

**START FROM [`sessions/2026-09-21-the-denominator-and-the-view.md`](.memory/sessions/2026-09-21-the-denominator-and-the-view.md).**
The replica-staleness notebook is still UNRUN and run 1's `REFUTED` is withdrawn
([`2026-09-17`](.memory/sessions/2026-09-17-replica-staleness-probe.md)).

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
