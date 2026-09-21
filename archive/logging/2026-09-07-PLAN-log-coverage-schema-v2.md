# PLAN — log coverage against report schema v2

**For `polaris-practice/polaris-learning/log-coverage/`, written 2026-09-07 in `local-k8s`.**
Supersedes nothing: `PLAN-log-coverage-v3.md` still describes the *policy*, which v2 did not
touch. This plan is about the **report schema** only, and about a rerun that can actually fail
for the right reasons.

**Premise.** Run `1788755035` drove 146 calls against the deployed v2 filter and reported 34
fixture mismatches. **Every one of them was the harness.** The filter's own numbers reconciled
exactly — both request margins at 158, and `errors_4xx`, `auth_denied` and `bytes_total` each
reconciled twice over across two independently built row sets. So a rerun before the harness is
fixed reproduces the same 34 lines and proves nothing. **Fix first, then run.**

**Assumed still true at run time; check, do not assume:**

| | |
|---|---|
| deployed script sha256 | `d58b9203a8304030` — repo file byte-identical to the running ConfigMap |
| `WINDOW_SECONDS` / `Interval_Sec` | **30 / 5** (the fast-run settings, deliberately not yet reverted) |
| `REPORT_MAX_RESOURCES` / `_PRINCIPALS` | 500 / 200 |
| `SCHEMA_VERSION` | 2 |

If the revert to 1800/30 has already happened, **§3's window-scoped assertions still hold but
cost ~90 minutes per drive instead of ~2**. That is the reason to run this before the revert.

---

## 1. Fix these first — the run is not meaningful until they are done

Detail and evidence: `2026-09-07-HANDOFF-harness-schema-v2.md` (in `local-k8s/logging/`).

| # | change | acceptance, testable WITHOUT a full drive |
|---|---|---|
| 1.1 | **window merge must sum every numeric field**, derived from the row's own keys rather than a hardcoded list | feed two synthetic windows where a v2 field differs (e.g. `errors_4xx` 1 and 25) and assert the merge yields 26, not 1. This is the bug that made `errors` merge correctly and `errors_4xx` not, **in the same row** |
| 1.2 | replace the cardinality invariant | `distinct_resources + distinct_principals + carried_rows == rows_emitted - 1`; add `errors_4xx + errors_5xx <= errors` (inequality on purpose — a `nil` status is an error charged to neither split) and `auth_denied <= errors_4xx` |
| 1.3 | frozen field sets | add `errors_4xx`, `errors_5xx`, `auth_denied`, `bytes_total`, `carried_rows`, `resources_other_distinct`, `windows_skipped`, `counted_read`; **remove `counted_get`** |
| 1.4 | oracle computes the new fields | 401 and 403 increment `auth_denied` **and** `errors_4xx`; `counted_read` counts GET **and HEAD**; `errors_5xx` is `status >= 500`; a `nil`/unparsed status increments `errors` only |
| 1.5 | `diff_reports` excludes `windows_skipped` | like `partial_window` — it is a property of the emitting process's clock and no oracle can predict it |
| 1.6 | characterization test | goes red on `SCHEMA_VERSION 2` by design. Read the diff, then update it and `doc-log-coverage-results.md` together |
| 1.7 | results template prose | still says "Schema v1, three record types on one envelope" |

**1.1 is the one to do first.** A hardcoded field list has now produced the same failure mode
twice in this pipeline — here, and as `type_int_key` on the shipper — and both times the symptom
was a plausible number rather than an exception. `local-k8s` closed its instance with a check
that reads the field names out of the same file the filter comes from; this one deserves the
same treatment rather than a longer list.

---

## 2. Assert on ONE window, not on the merge

The merge is a harness convenience, and it is where the v2 numbers went wrong. Every assertion
in §3 should name **the single window that contains its probe burst**, identified by
`min_record_time`/`max_record_time`, with the merge used only for the coverage matrix.

At `WINDOW_SECONDS 30` that is a real constraint: **a probe burst must complete inside one
30-second window** or its counts split across two and every expected value below is wrong. Drive
each group in §3 as a tight burst, then read the window whose `min/max_record_time` bracket it.
A burst that straddles a boundary is a **void run of that group**, not a finding — detect it
(the group's calls appear in two windows) and re-drive rather than reasoning about the split.

---

## 3. What the run must assert, and what provokes it

Each row is a distinct provocation. **The negative cases are the point** — v1 could produce the
right total while attributing it to the wrong bucket, and only the negatives catch that.

| field | provoke with | assert | negative case that must also hold |
|---|---|---|---|
| `counted_read` | ≥3 GET and ≥2 HEAD, all 2xx | `counted_read == GET + HEAD`, all counted-only | **no field named `counted_get` exists on any row** — the rename, not just the value |
| `errors_4xx` | ≥2 404s | summed `errors_4xx` == the 404 count | a 404 must **not** increment `auth_denied` |
| `auth_denied` | one 401 (bad/expired token) **and** one 403 (denied principal) | `auth_denied == 2`, and both also counted in `errors_4xx` | `auth_denied <= errors_4xx` on **every** row, and a 5xx must not increment it |
| `errors_5xx` | **a real 500 — see §4** | `errors_5xx >= 1`; that row's `errors_4xx` unchanged | a 500 must **not** increment `errors_4xx`; `errors_5xx` must be 0 in a window with only 4xx |
| `resources_other_distinct` | 404 against **3 distinct invented table names**, one of them hit **3 times** (5 calls) | `resources_other == 5` (requests folded), `resources_other_distinct == 3` (keys folded) | neither invented name may appear as its own resource row — an error never creates a key |
| `carried_rows` | any active window, then a window with **no** traffic | active window: `carried_rows == 0` if the previous was idle; idle window: `distinct_resources == 0`, `distinct_principals == 0`, `carried_rows == previous active rows` | the window after that: `carried_rows == 0` (decay). **`distinct_resources` must be 0 in the idle window** — this is the v1 defect and the single most important assertion here |
| `bytes_total` | any traffic with a mix of zero and non-zero bodies | `bytes_total == sum(resource.response_bytes) == sum(principal.response_bytes)` | must be excluded from the oracle diff (no `%b` client-side), asserted only as an internal margin |
| `windows_skipped` | an uninterrupted stretch | present, integer-typed, `0` across consecutive `report_seq` | **never assert across a host sleep** — the OrbStack VM suspends with the laptop and a large value there is expected, not a fault |
| every numeric field | — | `type_int_key`: each is stored as a **number**, i.e. a `field:>0` LogsQL filter matches | assert this for **every** field in the list, not one representative — the whole failure mode is that it is silent |

**Extend the margin check to the new counters.** This is new capability, not just new fields:

```
sum(resource.F) == sum(principal.F)   for F in {requests, errors, errors_4xx, errors_5xx,
                                                auth_denied, response_bytes}
sum(resource.requests) == access_seen - parse_errors
```

Under v1 the only real self-check was the request margin. Each v2 counter is now reconciled
across two independently built row sets, so an error attributed to the wrong principal, or bytes
charged to the wrong resource, has somewhere to show up. **Two or more principals must carry a
strict fraction of each total** — with a single identity these equalities are satisfied by a
global counter and prove nothing. Run `1788755035` had four; keep at least the write-heavy root
and the read-and-denied-only principal.

---

## 4. The 500 probe — the one real gap

`neg.500_null_pointer` has returned **200 for three consecutive runs**; the
`create_catalog_no_endpoint` provocation no longer reproduces on this build. The only 500s ever
observed came by accident, from the PG-HA read-after-write failures on
`iceberg.create_namespace` / `iceberg.create_view`. So **`errors_5xx` has never been exercised
against the real pipeline** — it read 0 across the whole live window. The `local-k8s` unit suite
covers the mapping; that is an argument about the Lua, not a measurement of the pipeline.

In order of preference:

1. **Find a probe that still provokes an unhandled 500 on this build** and retire
   `neg.500_null_pointer` with a note saying what it used to do and when it stopped.
2. **Drive a known 500 from `error-cases/`**, if one still reproduces.
3. **Accept the PG-HA 500s as the source**, but then say so explicitly in the results: the
   coverage of the ERROR path is *opportunistic and not repeatable*, and `errors_5xx` is
   asserted only when one happens to occur.

Whichever holds, record it. A field with no repeatable provocation should be named as such
rather than quietly reading 0. **This is also the run that can finally answer the stack-trace
question end to end** — the payload is stored flattened as **`exception.frames`**, not
`exception`; querying the unflattened name is what produced the earlier "no stack traces"
conclusion, twice, in agreement with itself.

---

## 5. Procedure

```bash
kubectl -n logging       port-forward svc/vlsingle-victoria-logs-single-server 9428:9428
kubectl -n datahub-hynix port-forward deploy/fb-polaris-shipper 2020:2020
kubectl -n datahub-hynix port-forward pod/benchmarks-postgresql-postgresql-ha-postgresql-0 5433:5432
```

1. **Cells 0 and 0b only** — preflight and the schema gate. Confirms the running ConfigMap
   carries `d58b9203a8304030`, reads `WINDOW_SECONDS`/`Interval_Sec` off the deployment, asserts
   the tick is well under the window and that no raw tick leaks. Minutes. **Abort on failure**;
   the notebook exists in this shape because a run once measured a policy that had been written
   and never deployed.
2. The §3 probe groups, each as a tight burst inside one window.
3. The full drive for the coverage matrix.
4. Two idle windows after the last call, for the carry and decay assertions.

## 6. Definition of done

- Cells 0–0b green, with the sha recorded.
- The fixture's own resource rows: **0 mismatches**. Neighbour traffic and fixture
  setup/teardown may still differ in the all-fields diff and are read, not asserted.
- Every §3 assertion has a verdict, including the negatives, and `errors_5xx` has either a
  repeatable provocation or an explicit statement that it does not.
- Every numeric field verified as a number, individually.
- `doc-log-coverage-results.md` regenerated; the characterization test read and updated in the
  same commit as the diff that made it red.

## 7. Do not re-derive these — measured, and not findings

- **`level: REPORT` renders as `OTHER` in every viewer.** Deliberate: it is the stream selector
  `{app="polaris-shipper-report", level="REPORT"}` that every existing query and `vlogs.py` use.
  The cost is that the severity column is meaningless for this stream.
- **`access_kept + access_counted == access_seen` is tautological** — `build_report` computes
  `access_kept` by subtraction. Worth asserting only end to end, as a transport check.
- **A startup blind spot**, bounded by the tick interval: records between shipper start and the
  first tick appear in no report. Their window is flagged `partial_window: true`.
- **Gaps in the report stream are usually the OrbStack VM sleeping**, not a stalled filter. No
  measurement over the report stream that spans a sleep can be read as elapsed time.
- **`resources_other` / `resources_other_distinct` appear in no `_msg`.** Known; the fix is a
  format string and it rides with the fast-run revert, so that the repo file stays
  byte-identical to the deployed ConfigMap until then.
