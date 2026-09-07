# 2026-09-07 — reviewing the 500-coverage handoff against the report windows it was written from

Cowork session, no cluster reach. Inputs: `polaris-learning`'s
`HANDOFF-500-coverage-2026-09-07.md`, `log-coverage/README.md` and
`doc-log-coverage-results.md` for run `1788760757`, plus three report windows pasted out of the
VictoriaLogs UI — seq **196 / 197 / 198**, `05:59:00Z .. 06:00:30Z`, which are that run's own
windows (rows per window 40 and 48, merged principal totals 140/116/10/9 = 275 = 237 + 38,
all matching the results document).

## What was closed

**`active-issues.md` #14's deferred row said `question 3: 0 of 5 ERROR records carried an
exception`. That number is disproven and the row now says so.** Run `1788760757` reports
**8 of 8** WARN/ERROR records carrying `exception.exceptionType` / `.frames` / `.message` /
`.refId`. `roadmap.md`'s *Handing back* section had already recorded the correction from the
earlier three runs; `active-issues.md` had not, so the file you are told to read *before
trusting a value* was the one carrying the wrong one. Only the `%D` half of that row is still
open, and it is Polaris-side (#11).

The failure shape is worth keeping, because it is this repo's recurring one: a query for
`exception` and a `grep -c stackTrace` **agreed with each other** and were both looking for a
name this build does not emit. VictoriaLogs flattens nested objects. Two searches agreeing is
not corroboration when they share the assumption.

## What the windows confirm, recomputed rather than taken on trust

Summed from the pasted rows and compared against the summary the filter emitted for the same
window:

- `Σ resource.requests` = `Σ principal.requests` = `access_seen − parse_errors` — **237** in
  seq 196, **38** in seq 197. Two independently built row sets, exact on both.
- `access_kept + access_counted == access_seen` (107+130, 27+11) — tautological in the filter,
  a transport check end to end: Fluent Bit split the array and VictoriaLogs kept the numbers
  numeric.
- `errors_4xx + errors_5xx == errors_kept` (46+7=53, 13+1=14), and `auth_denied` (13, 0)
  reconciles across both row sets.
- **Carry and decay at both steps.** 196's 35 keys → 197 emits 22 at zero + 2 principals = 24 =
  `carried_rows`. 197's 21 keys with traffic → 198 emits exactly those at zero + 2 = 23 =
  `carried_rows`, and 197's own zeroed rows are gone.
- **The v1 cardinality bug is confirmed fixed on a real idle window.** Seq 198 carries 23 rows
  and reports `distinct_resources: 0` / `distinct_principals: 0`; seq 197 emits 43 resource
  rows and reports 21. Commit `a500ab2` verified against deployed data, not only its unit test.
- `resources_other` (36 / 9) and `resources_other_distinct` (13 / 6) are present as fields and
  appear in **no** summary `_msg` — #14d's format-string fix confirmed still owed, and it still
  rides with the fast-run revert.
- Fast-run settings **not** reverted: `fb-values.yaml` sha `d58b9203a830…`, `WINDOW_SECONDS 30`,
  `Interval_Sec 5`; the three windows are 30s apart, so this is confirmed from the deployed
  side and not only from the file.

## Left open, for `polaris-learning` — the leads this review turned up

None of these is a filter fault and none was changed here. Full write-up lives with that repo's
handoff; the short form:

1. **The run stored 8 unhandled-exception 500s while its own document concludes the ERROR path
   was not exercised.** `errors_5xx` 7 + 1; question 1 `ERROR x8`; question 3 `8 of 8`. The
   oracle predicted 2 and the matrix names 2, so **six are unattributed** — visible only as
   `root errors_5xx oracle=0 stored=3` inside a diff labelled *read, not asserted*. The
   handoff's "`lc.trace_verdict` has never had a real driven record to judge" is stronger than
   the data: there is no **repeatable** 500, which is a different and smaller claim.
2. **Seq 197's `__other__` row contradicts NOT PROVOKED.** It is exactly 9 requests / 9 writes /
   9 errors — the ladder's nine `create_table` POSTs, the only calls in that window that cannot
   own a key — split **8 `4xx` and 1 `5xx`**. The client recorded nine 4xx. Either a rung really
   returned 500, or client status and access-log status disagree, which would be systematic
   across every prediction in section 11c. One LogsQL query for `http_status:500` scoped to
   `05:59:00Z..06:00:00Z` settles it, and it is the only open item that changes what the next
   session does.
3. **The replica-lag probe may be unnecessary.** The PG-HA 500 fired twice on the happy path in
   this run; 8 5xx over 275 requests is ~3%. That is a rate, not an accident that "cannot be
   driven" — a repeated-`create_namespace` rung is API-only and needs no `kubectl`. Separately,
   **a ~3% unhandled-exception rate on writes is a platform finding in its own right** and is
   not in `MEMORY.md`.
4. `min_record_time` / `max_record_time` are **absent entirely** from a zero-traffic window
   (seq 198). The PLAN-7 assertion that they fall inside the merged range must return VOID over
   a merge containing an idle window, or it is the `0 of 0` shape again.
5. The 30 named fixture mismatches are **all one-sided** (`stored > oracle`), which reads as the
   oracle replaying `ALL_CALLS` while the window also carries setup, cleanup and the
   correlation probe against the same paths — testable, and if right the diff becomes assertable.

## Also

`Claude outputs/review-500-coverage-2026-09-07.md` appeared in the working tree during this
session (the desktop app writing the delivered review beside the repo). **Left untracked and
uncommitted** — it is a chat artefact, not part of the record.

## Not verified

No `helm`, `kubectl` or `psql` from a Cowork session, and this task touched no chart: nothing
was rendered and no live object was queried. Every claim above is arithmetic over the pasted
report windows or a read of a file in this repo.
