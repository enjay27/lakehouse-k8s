# 2026-09-08 — api-sql-profile, Korean guide + results for a manager

**Task:** Kade's manager reads Korean. He needed a document explaining what the
api-sql-profile analysis did, how to read the three `api-explain-*-latest.xlsx`
workbooks, and what they found. Plan-first, signed off, then built.

## What was decided, and why it is two documents rather than one

Kade chose **guide + results split**, and the boundary is *not* "concept vs
numbers" — it is **what survives the next sweep**. `doc-api-sql-profile-guide-ko.md`
holds purpose, flow, the three identity cases, the sheet-by-sheet reading order
and the trap columns; all of that stays true when the sweep is re-run.
`doc-api-sql-profile-results-ko.md` holds the 2026-09-03 figures and is the
throwaway. The method-level caveats (plain `EXPLAIN` never executes, shape-only
reproduction, the parallel pin) went in the GUIDE; the run-level ones (one
volume, empty `policy_mapping_record`, the 10 unreplayable statements) went in
the RESULTS. Putting all caveats in one place would have meant deleting half of
them at the next re-run.

Audience decided as **DB/backend-literate**: plan node names, cost figures and
the PK-prefix argument are stated outright rather than softened.

## The part worth keeping: the docs are hand-written, so they got a checker

`render_index_findings.py` and `render_explain_workbook.py` cannot drift because
nobody types their numbers. Korean prose can. `_check_guide_figures.py`
recomputes every quoted figure from the workbooks and the run files and asserts
the documents still say it — **22 figures, all matching**.

Its check direction is the design decision: a figure whose anchor pattern no
longer matches is reported `NOT QUOTED` and does **not** fail (prose is allowed
to stop making a claim), while a pattern that matches with a *different* value
fails. Editing prose is cheap; silently editing a number is not. **Negative-tested**
— perturbing `60,815` to `60,814` and `95.5 %` to `95.4 %` produced exactly two
failures and a non-zero exit, then restoring produced a clean pass.

It also asserts §0 before checking anything: each workbook's `Provenance`
(`explain_run`, `matrix_report`, `APIs`, `statement occurrences`, `pairs`,
volume) must agree with the run JSON it names. The workbook is a view; the run
file is the authority, and a document checked against a mismatched pair would
look entirely correct.

## Wrong turns and things found on the way

- **Newer runs exist than the workbooks were built from** —
  `apiexplain-*-20260903-140930` / `-142056` postdate the `-1101xx` the `-latest`
  workbooks name. They are re-sweeps taken against the *explained* matrices
  (`05_merge_explain` output) and report identical `apis` / `instances` / `pairs`,
  so nothing is stale. Checked rather than assumed; the first read of the
  directory listing looked like drift.
- **The three uploaded workbooks are byte-identical** (md5) to the repo's
  `reports/api-explain-*-latest.xlsx`. Confirmed before writing a word.
- **`Summary.skipped` and the `Unplanned` row count are different units** and do
  not reconcile — admin 10 vs 13, authorized 5 vs 2. `skipped` sums per API, so a
  pair refused across three APIs counts three times; `Unplanned` is one row per
  distinct refusal, plus `redacted` rows that were never in the worklist. The
  results doc says this out loud rather than picking one number.
- **`README.md` and `PLAN-explain-workbook.md` both say the workbook has seven
  sheets. It has eight** — `Cost` was added afterwards. The guide states the
  discrepancy; the two English docs are still wrong and were left alone (not this
  task).
- **The DoD gate could not be run at all this session.** See below.

## The gate: NOT VERIFIED, and this contradicts `MEMORY.md`

`pytest` did not run. Three routes, all closed:

1. The repo `.venv` was created on the macOS host — its shebangs point at
   `/Users/kade/...`, which does not exist inside the mounted Linux VM.
   `PYTHONPATH` into its `site-packages` gets further but dies on
   `ModuleNotFoundError: exceptiongroup`, and `black` there dies on `tomli`.
2. `pip install` from the device VM: proxy returns **403**.
3. `pip install` in the Cowork cloud container: PyPI also **403** (`curl
   https://pypi.org/simple/pytest/` → 403).

`MEMORY.md`'s *Now* says "the oracle tests RUN FROM COWORK now — 115 passed".
**That was true of a previous session's network and is not true of this one.**
Recorded in `.memory/active-issues.md` so the next session does not plan around
a gate that may not be available.

What *was* run instead: `isort` (via `PYTHONPATH`, once delete permission was
granted — it needs to unlink its `.isorted` temp file), `py_compile`, a manual
88-column pass standing in for `black`, and `_check_guide_figures.py` itself.
No module under `src/` and no notebook was touched, so the tree's test surface
is unchanged by this commit.

## Also

Delete permission on the repo folder was granted this session — needed for
`git commit` (the `.git/index.lock` history in `CLAUDE.md`) and for `isort`.
The working tree had unrelated pre-existing modifications (eight notebooks, a
deleted `runs/api-surface-fixture.json`), so this commit names its files
explicitly rather than `git add -A`.
