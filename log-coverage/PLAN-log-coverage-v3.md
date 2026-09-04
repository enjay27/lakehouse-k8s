# PLAN — policy v3, the scheduled flush report, and what the notebook must prove about both

**Status: PROPOSED, not signed off. Nothing in `src/`, the notebook, or the tests has been
changed.** This document is step 1 of the repo's plan-first protocol; step 2 is Kade's
confirmation.

**Written to be read cold.** It supersedes nothing in
[`PLAN-log-coverage.md`](PLAN-log-coverage.md) — that plan describes the harness that exists and
is still the right first read for *how* the oracle works. This one describes what has to change
now that the policy under test is v3 and a second record type exists.

**Status markers, as in the source handoff.** **[verified]** was observed in a real record or a
running object. **[from values]** was read from a values file or a rendered ConfigMap.
**[assumed]** has not been checked, and every one below is listed in §11 as something the run
settles rather than something the plan asserts.

---

## 0. Read order for someone starting cold

1. `log-coverage/README.md` — the pipeline, and the v2 result (*the policy was never installed*).
2. `MEMORY.md` *Now* — where the project is.
3. This file.
4. `PLAN-log-coverage.md` §4 — the modules, because §5 below only says what *changes* in them.

The two documents Kade brought in from `local-k8s` (`POLARIS-LOG-COVERAGE-V3-HANDOFF.md`,
`POLARIS-API-LOG-COVERAGE-NOTEBOOK.md`) are the upstream statement of intent. Where this plan
disagrees with them it says so explicitly, in §2 and §11 — the same discipline the v2 plan used,
for the same reason: four conclusions drawn from config files were wrong about the running
system.

---

## 1. Where this leaves the existing notebook

`polaris_log_coverage.ipynb` runs cells 0–10 and answers *keep or drop, per endpoint*. Under v3
that question has three answers, not two — **kept**, **counted**, or **neither** — and most calls
now land on *counted*. Two consequences, and they are the whole task:

- **The characterization test is supposed to fail now.** `test_the_deployed_policy_still_drops_exactly_what_the_report_says`
  and `test_the_dropped_mutations_are_still_ten_and_still_these` pin v2's behaviour. The policy
  changed; a green characterization test after a policy change would mean the oracle is not
  reading the deployed file. **Read the diff it prints, then update it — do not delete it.**
- **A matrix of `expected` vs `stored` now mostly reads "correctly dropped"** and hides the
  interesting half. §7 changes its shape.

And run 1's headline still stands until re-measured: **the v2 policy was never deployed.** v3 is
reported deployed on 2026-09-04 **[from Kade, not independently verified]**. Cell 0 already aborts
when the running ConfigMap does not carry the policy under test; §3 updates what it looks for.
Nothing else in this plan is worth running until that gate is green.

---

## 2. The two things being tested, and why the second one is a *scheduled-job* test

### 2.1 Policy v3 — first match wins

```
0. tag polaris.report ......................... becomes the flush report
1. level ERROR or WARN ........................ keep
2. not an access-log record ................... keep (untouched)
--- every access-log record is COUNTED here, before any decision ---
3. http_status >= 400, or unparseable ......... keep — ALL of them, no cap
4. PUT / DELETE / PATCH ....................... keep — all
5. POST under /api/management/ ................ keep — all
   POST anywhere else ......................... counted only
6. GET / HEAD, 2xx ............................ counted only
7. anything else .............................. keep
```

Per-day deduplication is **gone** — no dedup keys, no KST buckets, no cap, no per-pod state for a
shipper restart to lose. Rule 5 is split because **in Polaris, POST is the create verb**:
`create_principal`, `create_principal_role`, `create_catalog_role`, `reset_principal_credentials`
are POSTs; PUT covers assignment and grants, DELETE covers removal. So v3 closes the audit hole
v2's run measured — **the ten invisible mutations** — and pays for it by turning successful reads
into counts.

### 2.2 The flush report is the scheduled-job scenario

Kade's question was whether this test can also cover *cron-job event summary logs*. **It can, and
that is exactly what the flush report is**: a `dummy` INPUT tagged `polaris.report` ticks every
30 s into the same Lua filter instance; on each `:00`/`:30` wall-clock boundary the filter
replaces the tick with an **array** of records and resets its counters. They land on their own
stream, `{app="polaris-shipper-report", level="REPORT"}`, so `app:polaris` queries are unaffected.

Treating it as a scheduled job rather than as "more fields to assert" is what produces the tests
in §6.3, and they are the ones that catch the failures a schema check cannot:

| a scheduled summariser fails like this | the test that catches it |
|---|---|
| fires on the tick instead of the period | ticks are 30 s, windows are `window_seconds`; count reports per window — **one**, never 60 |
| emits at an unaligned instant | `window_start % window_seconds == 0` |
| double-fires, or skips a window | `report_seq` increments by exactly 1 per window per `hostname` |
| never resets its accumulator | window N+1's `access_seen` is not N's plus more |
| forgets a row that went quiet | **zero-carry** — a resource active in N emits an explicit `0` in N+1 |
| carries dead rows forever | **carry decay** — a row that stayed 0 is not carried a third time |
| restarts mid-window and reports it as whole | `partial_window: true`, and `hostname`/`report_seq` reset |
| leaks its trigger into the data stream | `tick:polaris-report` returns **zero** rows |

**The tick rate is not the report period. Only the boundary matters.** That single sentence is
the most misread thing in the design and it gets its own assertion.

### 2.3 Schema v1 — field names are contract

**Envelope, every row:** `app`, `level`, `schema_version`, `report_type`, `report_seq`,
`hostname`, `window_start`, `window_end`, `window_seconds`, `_time` (= `window_end`), `_msg`.

**`summary`** (one per window): `access_seen`, `access_kept`, `access_counted`, `counted_get`,
`counted_post`, `errors_kept`, `parse_errors`, `distinct_resources`, `distinct_principals`,
`resources_other`, `principals_other`, `min_record_time`, `max_record_time`, `partial_window`.

**`resource`** (one per resource per window): `resource`, `resource_kind`, `requests`, `reads`,
`writes`, `errors`, `response_bytes`.

**`principal`** (one per principal per window): `user_principal_name`, `requests`, `reads`,
`writes`, `errors`, `response_bytes`.

Invariants:

```
access_kept + access_counted == access_seen
sum(resource.requests) == sum(principal.requests) == access_seen - parse_errors
reads + writes <= requests        (per row)
errors <= requests                (per row)
```

`errors` deliberately overlaps `reads`/`writes` — reads and writes are counted by method, errors
by status. **The margin equality is the schema's own self-check: if the two margins disagree the
report is miscounting, and no trend built on it can be trusted.** It goes in the *invariants*
half of `test_log_coverage.py`, not the characterization half — it is policy-independent.

**Correction, from reading the deployed `build_report` (2026-09-04):** the first of those four is
**tautological and is not a check.** The filter computes `s.access_kept = counts.access_seen -
counts.access_counted`; nothing counts kept records independently, so the identity holds by
construction and can never fail. Asserting it would be a test that cannot go red. **The only real
self-check is the resource/principal margin pair**, and the tests must say so rather than listing
four invariants as if they were four pieces of evidence.

Three more facts read off the source rather than assumed, all of which the tests have to encode:

- **`partial_window` is a string**, `"true"`/`"false"`, not a boolean; `min_record_time` /
  `max_record_time` fall back to `""`, not null.
- **`hostname` is `os.getenv("HOSTNAME") or "unknown"`** and `report_seq` is a per-process counter.
  Both are properties of the *process that emitted the report*, so **cell 12's diff must exclude
  them** — the oracle runs on Kade's machine and would otherwise report a mismatch on every row.
- **`REPORT_MAX_RESOURCES = 500`, `REPORT_MAX_PRINCIPALS = 200`, `REPORT_OTHER = "__other__"`,
  `WINDOW_SECONDS = 1800`.** Read, not assumed.

### A startup blind spot, found by the gate

`report_tick` opens its first window **on the first tick**: until one arrives, `counts` is `nil`
and `count_record()` returns immediately. So **every access record processed between shipper start
and the first tick is counted into no window at all.** It is still routed by the policy normally —
kept or dropped correctly, nothing is lost from the log — but it is invisible to the report, and
the window it lands in is flagged `partial_window: true`. Bounded by the tick period (30 s), so
small; it is a real property and belongs in the results doc, not a bug to file. It also explains
the first observed report exactly: seq=1, `access_seen: 0`, `partial_window: true`, for a pod that
started at 07:12:37 inside the 07:00–07:30 window.

The same function documents a second skew, deliberately: records arriving between a boundary and
the tick that notices it are counted into the window **just closed**. Up to one tick period of
attribution slack — assertions must not demand exact per-window placement for calls made within
30 s of a boundary.

---

## 3. The gate, and it comes before any code

Two things were shipped unverified. If the first is false the schema is different and every test
below targets the wrong thing. **Cell 0 runs these and aborts; I do not extend the notebook until
they are green in a real run.**

| check | LogsQL | pass |
|---|---|---|
| the ConfigMap carries **v3** | (kubectl, as today) `RESOURCE_PATTERNS` and `MGMT_PREFIX` present, `DEDUP_MAX_KEYS` **absent** — **strip Lua comments first**: the v3 script carries a comment saying the dedup machinery was removed, and a naive grep reads that as the machinery still being present (2026-09-04, my error, caught by printing the matching lines) | match |
| the tick reaches the filter | `app:polaris-shipper-report \| stats count()` | ≥ 1 |
| **the array return splits** | `app:polaris-shipper-report \| stats by (report_type) count()` | three types |
| `type_int_key` worked | `app:polaris-shipper-report report_type:resource requests:>0` | matches numerically, not `"482.0"` |
| the tick is not leaking raw | `tick:polaris-report` | **zero** |
| the margins agree | `sum(requests)` across the two `report_type`s for one `_time` | equal |

**If the array does not split**, the filter emits one record per window carrying numeric-keyed
fields. That is a change in `local-k8s/logging/fb-values.yaml`, not here: I stop, say so, and the
fallback (a single summary with top-K resources inline) is Kade's call, not a workaround I build
around.

Port-forwards, unchanged:

```bash
kubectl -n logging       port-forward svc/vlsingle-victoria-logs-single-server 9428:9428
kubectl -n datahub-hynix port-forward deploy/fb-polaris-shipper 2020:2020
```

---

## 4. Scope decision, taken: **extend the existing notebook**

Kade chose one notebook over a fast/slow split. So `polaris_log_coverage.ipynb` grows from cells
0–10 to **0–14**, and the whole run becomes long. What that costs, stated plainly so it is not a
surprise later:

- A full run is **~3 window boundaries**. At the deployed `window_seconds` that is roughly
  **90 minutes, mostly waiting**, against today's few minutes.
- The waiting is real wall-clock and cannot be faked from the client side. `_now_override` moves
  the *oracle's* clock (§5.1); it is inert in the deployed pipeline, by design — the dummy input
  never sets it.
- Mitigation, and it is the reason `window_seconds` is never hardcoded: with
  `WINDOW_SECONDS: 120` redeployed in `local-k8s`, the same notebook completes in ~6 minutes with
  **every assertion unchanged and still honest**. That is a `local-k8s` change and therefore
  Kade's — §11, decision 3.
- **Do not hardcode 1800.** Read `window_seconds` off an actual report record, fall back to
  `WINDOW_SECONDS` in the running ConfigMap, and derive every wait from it.

---

## 5. Module changes — what moves into `src/`, and why none of it is a cell

Per CLAUDE.md, notebooks visualize; logic lives in `src/`. Three files change, one is new.

### 5.1 `src/log_coverage.py` — the oracle has to return arrays

Today `Policy.predict()` runs the deployed Lua over synthetic records and **raises if the number
of verdicts does not match the number of records**. A report tick returns *many* records for one
input, so that check is exactly what blocks this. This is the handoff's `[assumed]` and it is
confirmed by reading the code, not assumed: `predict()` ends with

> `if len(out) != len(records): raise PolicyUnavailable(...)`

Changes, additive — `predict()` keeps its signature and its guard for the non-tick path:

| new | what it does |
|---|---|
| `REPORT_TAG = "polaris.report"`, `REPORT_APP = "polaris-shipper-report"`, `SCHEMA_VERSION = 1` | names, in one place |
| `report_tick(now=None)` | the record the dummy INPUT emits; `_now_override` set only when `now` is given |
| `Policy.run(records, ticks=())` → `(verdicts, reports)` | one interpreter, records and ticks interleaved in issue order, so counters accumulate exactly as the shipper's do |
| `Policy.report(now)` | one tick, returns the array as a list of dicts — **this is the expected report** |
| `SUMMARY_FIELDS` / `RESOURCE_FIELDS` / `PRINCIPAL_FIELDS` / `ENVELOPE_FIELDS` | §2.3 as frozen sets, so a missing or extra field is a named failure, not a `KeyError` |
| `check_invariants(rows)` → list of violations | the four assertions of §2.3, evaluated on either expected or actual rows |
| `diff_reports(expected, actual)` → DataFrame-ready rows | field-by-field, joined on `(report_type, key)`; **the whole point — "all schema coverage" becomes a diff, not hand-written expectations** |
| `window_bounds(t, seconds)` | `(start, end)`, and the alignment check |
| `resource_key(api_path)` | the normalisation under test, **read out of the deployed Lua's `RESOURCE_PATTERNS`, never re-implemented** |
| `disposition(verdict, record)` | `kept` / `counted` / `neither`, plus which resource row and which principal row should have incremented — §7 |

The Lua driver string grows one branch: after each record it calls the filter as today; for a
tick it calls `polaris_noise_filter("polaris.report", 0, tick)` and serialises the returned array.
Output stays line-oriented TSV so the parse stays boring.

**The standing rule does not bend: there is no Python re-implementation of any of this.** A port
that agrees with itself is not evidence, and the first disagreement would be reported as a
pipeline finding when it was a translation bug.

### 5.2 `src/vlogs.py` — the report stream is a different stream

`_stream_fields=app,level`, so `{app="polaris-shipper-report", level="REPORT"}` is its own stream
and none of the existing helpers select it. Added:

`app_report()`, `reports(since, report_type=None)`, `report_window(window_start)`,
`report_types()` (the gate's `stats by (report_type)`), `latest_seq(hostname)`,
`wait_for_boundary(window_seconds, lag)` (sleep to the next boundary **plus ingest lag**, and
return the boundary it waited for), `tick_leak()` (the `tick:polaris-report` zero check).

`numeric_status_filters_work()` already exists for the "every field is a string" trap; the gate's
`requests:>0` check reuses it rather than inventing a second one.

### 5.3 `src/log_coverage.py` correlation — report rows do not join on a request id

Access-log records correlate by `mdc.requestId`, **exact [verified]**. Report records carry no
request id; they are per-window aggregates. They join on **`report_seq` (unique per `hostname`)**
or on `window_start`. The existing correlation machinery is not forced onto them — a separate,
small join, and `drive_tagged`'s per-call rows gain a `window_start` column so a call can be
attributed to the window that should have counted it.

### 5.4 `log-coverage/fetch_specs.sh`, `src/config/*` — unchanged

No new config key. The report stream is discovered from `victorialogs_url`; `window_seconds`
comes off a record. If the ConfigMap read needs a key it is the one cell 0 already uses.

---

## 6. Notebook cell map — what changes, what is new

Cells **0–10 keep their numbers and their jobs**; 11–14 are new. Linear, `Restart & Run All`.

### 6.1 Changed cells

| # | change |
|---|---|
| 0 | ConfigMap check updated to v3 (`RESOURCE_PATTERNS` + `MGMT_PREFIX` present, `DEDUP_MAX_KEYS` absent). Adds the six gate rows of §3 and **aborts on any of them**. Records `window_seconds`, the shipper `hostname` and the first `report_seq` seen — the run's baseline. |
| 3 | Ordering becomes load-bearing: for one resource, **read it successfully, then write it, then provoke a 403 on it**, so one `resource` row carries `requests`, `reads`, `writes` and `errors` all non-zero. An error on a resource never read successfully lands in `__other__` instead of creating a key — which is the design property, not an accident. |
| 4 | Unchanged in intent; its 4xx/5xx now also feed `errors_kept` and the per-row `errors`. |
| 5 | **Rewritten.** The v2 dedup probes are meaningless under v3 (no dedup exists). Replaced by the v3 branch probes of §6.2. The old expectations move into the characterization test's diff, not into the bin. |
| 8 | Matrix gains `disposition`, `expected_resource_row`, `expected_principal_row` — §7. |
| 10 | Renders `doc-log-coverage-results.md` with the report sections and the answers of §10. |

### 6.2 Coverage of the policy branches (cell 5, rewritten)

| rule | drive | expect |
|---|---|---|
| 1 | the known 500 (`error-cases/09_500_null_pointer`) | stored, **not** counted |
| 2 | any call — application lines ride along | stored untouched, **not** counted |
| 3 | 400, 401, 403, 404, 405, 409, 500 | every one stored, no cap |
| 4 | PUT (`grant_privilege`, `assign_*_role`), DELETE (drop table/view/namespace, delete principal/role) | every one stored |
| 5a | POST `/api/management/v1/{principals, principal-roles, catalogs/{c}/catalog-roles, principals/{p}/reset}` | every one stored — **the v2 audit hole, now closed; assert it explicitly** |
| 5b | POST `create_table`, `stage_create_table`, `commit_table`, `tables/rename`, `views/rename`, `namespaces`, `namespaces/{ns}/properties`, `tables/{t}/metrics`, `oauth/tokens` | **none** stored; all counted |
| 6 | GET and HEAD on table, view, namespace, both collections, `/config`, a management read | **none** stored; all counted |
| 7 | not callable from a client **[assumed]** — Polaris exposes no method outside the above | Lua unit suite only |

`resource_kind`, all six values: `table`, `view`, `collection` (tables / views / namespaces
lists), `namespace`, `management`, `other` (`GET /api/catalog/v1/config`, `POST .../oauth/tokens`,
`POST .../tables/rename`).

Field coverage the ordering forces:

- **`response_bytes`** — one resource non-zero (any GET with a body), one zero (HEAD, or a DELETE
  returning 204). `%b` writes `-` for a zero-byte body and the parser normalises to 0 **[verified]**.
- **`resources_other` > 0** — GET a table name that never existed. Cheap, and it simultaneously
  proves errors do not create resource keys.
- **`/metrics` normalisation** — POST `.../tables/{t}/metrics`, then assert the table's `requests`
  includes it and that **no row exists for the `/metrics` path**. v2 emitted two rows for one table.
- **Two principals with different mixes** — one read-heavy, one write-heavy — so the principal
  margin is proved per-principal and not a global total.
- **`min_record_time` / `max_record_time`** bracket the run's own timestamps.
- **`schema_version == 1`**; `hostname` == the shipper pod name cell 0 recorded; `window_seconds`
  == the deployed constant; `window_start` aligned to a multiple of `window_seconds`.

### 6.3 New cells — the scheduled-job scenario

| # | cell | what it does |
|---|---|---|
| 11 | **Window 1 — the report exists and its margins agree** | `wait_for_boundary()`; pull the window's `summary`/`resource`/`principal` rows; run `check_invariants`; assert alignment, `schema_version`, `hostname`, `window_seconds`. Prints the three-type table. |
| 12 | **The oracle diff** | Replay the run's own calls as synthetic records through the deployed Lua (`Policy.run`), tick at the same boundary, and **`diff_reports` the array against what VictoriaLogs stored.** A mismatch names the row and the field. This is the cell that makes "all schema coverage" checkable rather than asserted. |
| 13 | **Window 2 — increment, reset, zero-carry** | Stay deliberately silent for one whole window. Assert `report_seq` +1 with the same `hostname`; counters reset (window 2's `access_seen` is not window 1's plus more); **every resource active in window 1 emits an explicit `0` row in window 2.** |
| 14 | **Window 3 — carry decay, and the tick/period separation** | Silent again. Assert a row that stayed 0 is **not** carried a third time; assert exactly **one** report per window per host across all three (not one per 30 s tick); assert `tick:polaris-report` is still zero. |

Cell 9 (cleanup) and cell 10 (findings) stay last — the DELETEs are part of the test and must land
inside a counted window, so cleanup runs **before** cell 11's wait, and its rows are asserted in
window 1.

**`partial_window: true` is deliberately NOT in the main run.** It requires a shipper restart
mid-run, and a restart invalidates the counts (§8). It is covered as a separate, explicitly
flagged scenario appended to `doc-log-coverage-results.md`, never inside the run that produces the
numbers.

**A run will usually straddle a boundary.** Every assertion sums across the windows covering the
run rather than assuming one window holds it all, and `report_seq` + `hostname` are checked for a
mid-run restart before any count is believed.

---

## 7. The results matrix changes shape

`stored` is 0 for most calls **by design** now, so `expected` vs `stored` mostly says "correctly
dropped". Columns added, per call:

| column | |
|---|---|
| `disposition` | `kept` / `counted` / `neither`, from the deployed Lua |
| `expected_resource_row` | the resource key this call should have incremented, after normalisation |
| `expected_principal_row` | the `user_principal_name` row it should have incremented |
| `window_start` | which window should hold it |
| `counted_where` | the row that actually moved, from the stored report |

A mismatch then **names the row that is wrong** instead of saying a call is missing.

---

## 8. What invalidates a v3 run

Recorded before and after, as cell 0 already does for the first two:

- **The shipper pod restarting.** Counters are per-process; `report_seq` restarts at 1 and a window
  is flagged `partial_window`. A restart mid-run makes the counts unusable — the run is void, and
  the report says so rather than reporting numbers.
- **Polaris scaling.** The HPA allows 3 replicas appending to one log file (`local-k8s` #8). The
  ×20 loops are two orders of magnitude below that; replica count is still recorded either side.
- **The running ConfigMap not carrying v3.** Cell 0 aborts. This is the repo's signature failure
  and run 1 caught it empirically — the gate stays.
- **A `helm upgrade` during the run.** The tail DB is on an `emptyDir` with `Read_from_Head true`
  and VictoriaLogs does not deduplicate on ingest, so the whole file replays. Under v3 replayed
  reads are absorbed as counts, but **every error and mutation replays as a full record**, and the
  counters attribute the entire replay to whichever window it lands in. **A window whose
  `min_record_time`/`max_record_time` span is far wider than `window_seconds` is a replay** —
  cell 11 checks that before believing any spike.

---

## 9. Tests — both kinds, and the schema invariants belong to the first

`test_log_coverage.py` (currently 22 tests) and `test_vlogs.py` (17).

**Invariants — must hold under any policy worth shipping.** Kept as-is: an error is never
summarised away, every DELETE is kept, a line that will not parse is kept. Added:

- the four schema invariants of §2.3, on synthetic report arrays;
- `access_kept + access_counted == access_seen` under a mixed record sequence;
- an error on a never-read resource lands in `__other__` and **does not create a key** — while the
  request itself is still stored in full by rule 3, so the count is not lost;
- `/namespaces/ns/tables/t/metrics` normalises to `/namespaces/ns/tables/t`;
- exactly one report per window regardless of tick count (drive 60 ticks inside one window).

**Characterization — expected to fail on the next policy change.** The two v2 tests are updated,
not deleted, and the update is recorded in the same commit as the results doc. Their new content:
the v3 disposition of the full 43-operation sequence, and the report array for a fixed synthetic
window under `_now_override`.

**Not reachable from a client — Lua unit suite only** (`local-k8s/logging/scripts/test-polaris-filters.py`,
48/48 today): `parse_errors` (needs the access-log pattern to change), `principals_other` (>200
distinct authenticating principals in one window), the `resources_other` 500-key cap,
`partial_window: true`, rule 7 and `PATCH` (Polaris exposes neither **[assumed]**).

---

## 10. What the run must send back

Both files updated together, as the README requires — a report nobody updated is worse than none:

- `test_log_coverage.py` — invariants + updated characterization.
- `doc-log-coverage-results.md` — written by cell 10.

Plus the two questions run 1 left open, both cheap once connected:

1. **Where does `app_lines` come from?** The last report said "34 of 122 calls produce no record at
   all" while those same calls carried 628 application lines, and `90 + 1,928 ≈ 2,026` implies the
   column is read from VictoriaLogs. Settle which, and correct the claim.
2. **`stats by (loggerName)`** — 1,928 of 2,018 stored records were application lines, so the
   filter governs ~4.5% of the volume. Which logger dominates is the input to the only remaining
   volume decision.

And three known-open items are not re-derived: `neg.client_timeout` → "EXPECTED DROPPED, PRESENT"
is an **oracle artefact** and is fixed here (a call with no client-side status is not predictable
and must not be scored `drop`); **there is no `%D`** and Polaris is not to be changed; **a
server-side hang leaves no line at all** and no test can change that.

---

## 11. Decisions needed before I build anything

1. **The gate (§3) is half-answered (2026-09-04).** Settled: the deployed script is v3 (markers present, dedup gone — the apparent `DEDUP_MAX_KEYS` survival was a comment), the ConfigMap carries it, the report stream is alive, the envelope is exactly schema v1, `window_seconds` is **1800**, `partial_window: true` fired correctly on the shipper's first, truncated window, and the tick does not leak. **Open: the array split**, because the only window flushed so far saw `access_seen: 0` — no traffic, so no `resource` or `principal` rows to split into. `verify_v3_gate.ipynb` answers it offline via `_now_override`.
   Superseded: **The gate (§3) has not been run.** I cannot reach the cluster from Cowork — the bridge VM has
   no `kubectl`, no port-forward and no network to it. **You run cell 0's gate, or paste its
   output, and I build against the result.** If the array does not split, this plan targets the
   wrong schema and stops at §3.
2. **v3 is reported deployed [from Kade, unverified here].** Same gate settles it. Run 1's whole
   finding was that a policy can be written and never applied.
3. **A fast run needs `WINDOW_SECONDS: 120` in `local-k8s`** — your change, not mine. Without it
   every full run is ~90 minutes. The notebook works unchanged either way; I would rather you
   redeploy short for development and long for the run of record.
4. **Cleanup before the first boundary** (§6.3). It makes the DELETEs land in window 1 where they
   are asserted, but it means a failed later cell leaves nothing to inspect. Say if you would
   rather keep the fixture alive and assert the DELETEs in a fourth window.
5. **The characterization tests will go red the moment the oracle reads v3.** Confirm you want them
   updated in this task's commit rather than left red as a marker.

---

## 12. Definition of Done

1. Cells 0–14 run top to bottom, `Restart & Run All`, zero errors, gate green.
2. `black . && isort .` on the changed modules. **`pytest` is the gate and it is not runnable from
   Cowork** (`.venv` was rebuilt against macOS Python; the bridge sees Linux). If it cannot run, the
   commit body says `NOT VERIFIED: pytest could not be run, <reason>` — per CLAUDE.md, never a
   silent skip.
3. `doc-log-coverage-results.md` rewritten by cell 10; `README.md` result section replaced.
4. `MEMORY.md` *Now* updated (≤40 lines), a numbered finding in `.memory/roadmap.md`, the narrative
   including the wrong turns in `.memory/sessions/2026-09-04-log-coverage-v3.md`.
5. One commit, this plan and the two handoff documents included, subject line stating the finding.
