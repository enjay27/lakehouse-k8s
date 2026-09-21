# 2026-09-07 — reading run 1's results document against the code that wrote it

No cluster, no run. The task was a review of `doc-log-coverage-results.md` for run
`1788511328` and then, on sign-off, the fixes. Everything below is about the harness;
**nothing here is a finding about the filter.**

## The first thing that mattered was noticing the document was stale

Four of the review's items — the missing `loggerName` breakdown, `0 of 0` on questions 1
and 3, the tick interval printed as 30s, the top-20 mismatch dump — were already fixed in
the notebook. The results file was written at 08:43 and the notebook edited at 08:47, so
the document predates its own writer by four minutes. **Check the mtimes before writing a
finding about a generated file**; four of nine "defects" evaporated on that one `ls -la`.

## What was actually wrong

**The oracle diff failed and the document reported it as a scalar.**
`oracle diff, THIS run's fixture resources | 66 mismatches` sits two lines under
`merged invariants | OK`, and PLAN 6.3 says cell 11 is the cell that makes "all schema
coverage" checkable rather than asserted, with a mismatch naming the row and the field.
66 on paths belonging to this run alone is that assertion failing. Cell 11 *prints* the
first 20 of them; the document writer never carried them across.

**"Management POSTs kept: 5 of 5" — six were driven and six were kept.** The count
filtered `M.path`, which is truncated to its last 58 characters for printing. The cut
removes `/api/management` from
`POST /api/management/v1/catalogs/{c}/catalog-roles`, so that call left the numerator
AND the denominator together and the fraction agreed with itself. This is the wrong-turn
worth remembering: **a display column that is also a data column will eventually be
filtered**, and the failure is silent and self-consistent.

**`principal_row` was the constant `DRIVE_PRINCIPAL` on all 132 rows.** The management
block drives on `adm_pc` (root) and the 403 case on `nb_<run>_denied`, so the column was
an assertion about the notebook. Worse, it hid that only ONE principal really drove the
run — which makes `sum(principal.requests) == access_seen - parse_errors`, described in
three documents as the schema's only real self-check, **satisfied identically by a global
counter**. A filter that attributed nothing at all would have passed it. PLAN 6.2 asks for
two principals with different mixes for exactly this reason.

**`merged rows: 49`** against 30 distinct resource keys with a success and 4 error-only
ones. Nothing compared the two, so ~15 rows sat unexplained on the page. The innocent
reading (carries from a window that opened before `STARTED`, or another client) is still a
reading someone has to be given the means to check.

**2,117 records vs 2,109 in the matrix's own columns.** `app_lines` is
`len(found) - len(access)` from the same pull, so the two agree by construction unless a
record carries a run request id for a call outside `ALL_CALLS`, or none at all.

**`http_status:"404" -> 138` in a *Validity* block** for a run that made 23 of them: the
check scans 24h cluster-wide. As an instrument check ("does `type_int_key` work") it is
sound; printed unlabelled next to run statistics it reads as one.

**`window_start` and `counted_where` were missing** (PLAN 7 names five matrix columns and
run 1 shipped three) — which is *why* the mismatches could only arrive as a number.
`counted_where` is also the column that distinguishes the row a call classifies to from
the row that moved: an error on a resource nobody read successfully increments
`__other__`, so for a 4xx `resource_row` is a counterfactual.

**Four assertions PLAN 7 names were computed or implied and never stated:** `/metrics`
folding onto its table (the v2 two-rows-per-table bug staying fixed), `resources_other > 0`,
`response_bytes` taking both a zero and a non-zero value, and min/max_record_time
bracketing the run.

**One thing worth reading as a finding rather than a defect:** exactly 1 record carries the
granted privilege name. There is no `%D` and no request body in the access log, so what a
`grant_privilege` PUT actually granted survives only in an application line that rule 2
passes through untouched — the auditability of grants rests on a Polaris logger's level,
not on the policy under test. v3 closed "who created a principal"; "what privilege was
granted" is one configuration change from disappearing and nothing here protects it.

## How it was verified without pytest

Same position as session 7: the Cowork device VM has no `pytest` and no package index
(both `pip` and `uv` fail at the proxy), and `.venv` is a macOS 3.12 tree the Linux VM
cannot execute. `luatex --luaonly` is present, and requesting access to
`~/hynix/local-k8s/logging` put the deployed `fb-values.yaml` (sha `063c184df3f9…`,
`WINDOW_SECONDS` 30 / `Interval_Sec` 5) in reach — **so the oracle itself ran here**, which
it could not in the session that wrote the harness.

Run under the minimal pytest stand-in: **81 passed, 0 failed** (`test_log_coverage` 54,
`test_vlogs` 27). The doc writer and the new cell 11b were additionally executed against a
synthetic run in `/tmp`, which is how the two bugs I introduced were caught: a
`principals=` keyword placed before a positional lambda (`SyntaxError`), and a `{m}` in the
management-POST list that no name bound (`NameError`, and only at the very end of a live
run). **A notebook cell that renders a document should be dry-runnable; these two would
each have cost a full run.** `black`/`isort` still cannot run — black 26.5 needs `tomli`
under 3.10 — so the wrapping is by hand.
