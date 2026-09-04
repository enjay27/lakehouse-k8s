# Handoff — extend `log-coverage` to cover policy v3 and the report schema

**Written to be read cold, from a new session in the `polaris-learning` project.** Nothing here
assumes you have seen `local-k8s` or the session that produced v3. Everything about the pipeline
you are testing is restated below rather than linked.

**Status markers, used throughout.** **[verified]** was observed in a real record or a running
object. **[from values]** was read from a values file or a rendered ConfigMap. **[assumed]** has
*not* been checked and is the first thing to settle. This repo's most expensive failure was
configuration that was written and never applied, so the distinction is load-bearing.

**What is already true:** policy v3 and the flush report were deployed on 2026-09-04
**[from Kade, not independently verified in this document]**. Everything below was written
before any post-deployment observation.

---

## 1. What changed, and why the existing notebook now fails

`polaris_log_coverage.ipynb` drives every Polaris API and reports, per endpoint, what the
pipeline stored versus what the deployed retention policy says it should have. Its
**characterization test is built to fail when the policy changes.** The policy changed. That
failure is the expected starting point, not a bug to work around.

### The policy now in the shipper

```
0. the report tick (tag polaris.report) ....... becomes the flush report
1. level ERROR or WARN ........................ keep
2. not an access-log record ................... keep (untouched)
--- every access-log record is COUNTED here, before any decision ---
3. http_status >= 400, or unparseable ......... keep — ALL of them, no cap
4. PUT / DELETE / PATCH ....................... keep — all
5. POST under /api/management/ ................ keep — all
   POST anywhere else .........................  counted only
6. GET / HEAD, 2xx ............................  counted only
7. anything else .............................. keep
```

It preserves **100% of authorization failures** — every 401 and 403 is a full record via rule 3 —
and **100% of identity and grant mutations**. What becomes a count is traffic that succeeded
routinely. Rule 5 is split that way because **in Polaris, POST is the create verb**:
`create_principal`, `create_principal_role`, `create_catalog_role` and
`reset_principal_credentials` are all POSTs, while PUT covers only assignment and grants and
DELETE only removal.

Everything about per-day deduplication in the previous version is **gone** — no dedup keys, no
KST day buckets, no cap. A successful read is never stored individually, so there is no state.

### The flush report

A `dummy` INPUT tagged `polaris.report` ticks every 30s and reaches the same Lua filter
instance. On each **:00/:30 wall-clock boundary** the filter replaces the tick with an *array* of
records and resets its counters. They land on their own stream,
`{app="polaris-shipper-report", level="REPORT"}` — `app:polaris` queries are unaffected.

**The tick rate is not the report period.** A tick inside the current window is dropped. Only the
boundary matters.

---

## 2. The schema you are being asked to cover

Schema v1. Three record types on one envelope. Field names are contract.

**Envelope — every row:** `app`, `level`, `schema_version`, `report_type`, `report_seq`,
`hostname`, `window_start`, `window_end`, `window_seconds`, `_time` (= `window_end`), `_msg`.

**`report_type: summary`** — one per window

`access_seen`, `access_kept`, `access_counted`, `counted_get`, `counted_post`, `errors_kept`,
`parse_errors`, `distinct_resources`, `distinct_principals`, `resources_other`,
`principals_other`, `min_record_time`, `max_record_time`, `partial_window`.

**`report_type: resource`** — one per resource per window

`resource`, `resource_kind`, `requests`, `reads`, `writes`, `errors`, `response_bytes`.

**`report_type: principal`** — one per principal per window

`user_principal_name`, `requests`, `reads`, `writes`, `errors`, `response_bytes`.

### The invariants the notebook should assert

```
access_kept + access_counted == access_seen
sum(resource.requests) == sum(principal.requests) == access_seen - parse_errors
reads + writes <= requests        (per row)
errors <= requests                (per row)
```

`errors` deliberately **overlaps** `reads` and `writes`: reads/writes are counted by method,
errors by status. The margin equality is the schema's own self-check — **if the two margins
disagree, the report is miscounting and no trend built on it can be trusted.**

### Two design properties that need their own tests

- **The resource key is the resource, not the URL.** `/namespaces/ns/tables/t/metrics` counts
  under `/namespaces/ns/tables/t`. The previous version emitted two rows for one table.
- **Errors increment an existing resource key but never create one.** A GET 404 on a table that
  was never read successfully lands in the `__other__` row — its count is *not* lost, which is
  what keeps the margin totals exact, and the request itself is stored in full by rule 3.

---

## 3. Do this first — the gate

**Do not extend the notebook until the report's shape is confirmed.** Two things were shipped
unverified, and if the first is false the schema is different and every test below targets the
wrong thing.

| check | LogsQL | pass |
|---|---|---|
| the tick reaches the filter | `app:polaris-shipper-report \| stats count()` | ≥ 1 |
| **the array return splits** | `app:polaris-shipper-report \| stats by (report_type) count()` | three types |
| `type_int_key` worked | `app:polaris-shipper-report report_type:resource requests:>0` | matches, not `"482.0"` |
| the tick is not leaking raw | `tick:polaris-report` | **zero** |
| the margins agree | compare `sum(requests)` across the two `report_type`s for one `_time` | equal |

**If the array does not split**, the filter emits one record per window carrying numeric-keyed
fields. Stop and say so — the fallback is a single summary with top-K resources inline, a change
in `local-k8s/logging/fb-values.yaml`, not here.

Port-forwards, as in the project README:

```bash
kubectl -n logging       port-forward svc/vlsingle-victoria-logs-single-server 9428:9428
kubectl -n datahub-hynix port-forward deploy/fb-polaris-shipper 2020:2020
```

---

## 4. The structural change: this notebook now needs wall-clock time

The existing notebook runs in minutes. **Full schema coverage needs at least three window
boundaries**, because three of the behaviours only exist across windows:

| behaviour | needs |
|---|---|
| `report_seq` increments, counters reset | 2 boundaries |
| **zero-carry** — a resource active in window N emits an explicit `0` in N+1 | 2 boundaries and deliberate silence |
| **carry decay** — a row that stayed 0 is not carried a third time | 3 boundaries |

At the deployed `window_seconds` that is ~90 minutes of mostly waiting.

**Do not hardcode 1800.** Read `window_seconds` off an actual report record (or
`WINDOW_SECONDS` out of the running ConfigMap) and derive every wait from it. Then someone can
redeploy with `WINDOW_SECONDS: 120` for a fast run and the notebook still works unchanged — and
the assertions stay honest either way. **[assumed]** that a shortened window is otherwise
behaviourally identical; it should be, since nothing else reads that constant.

Suggested shape: **drive → wait for boundary + ingest lag → assert → stay silent one window →
assert zero-carry → stay silent again → assert decay.** Ingest lag was **2.0s** on the previous
run **[verified]**; give it more.

**A run will usually straddle a boundary.** Sum across the windows that cover the run rather
than assuming one window holds all of it, and use `report_seq` plus `hostname` to detect a
shipper restart mid-run (which invalidates the counts, see §6).

---

## 5. Coverage matrix — what to drive, and what it proves

### Policy branches

| rule | drive | expect |
|---|---|---|
| 1 | provoke an application `ERROR` (the 500 null-pointer call does it) | record stored, not counted |
| 2 | any call at all — application lines ride along | stored untouched, **not** counted |
| 3 | 400, 401, 403, 404, 405, 409, 500 | every one stored |
| 4 | PUT (`grant_privilege`, `assign_*_role`), DELETE (drop table/view/namespace, delete principal/role) | every one stored |
| 5a | POST `/api/management/v1/{principals, principal-roles, catalogs/{c}/catalog-roles, principals/{p}/reset}` | every one stored |
| 5b | POST `create_table`, `stage_create_table`, `commit_table`, `tables/rename`, `views/rename`, `namespaces`, `namespaces/{ns}/properties`, `tables/{t}/metrics`, `oauth/tokens` | **none** stored; all counted |
| 6 | GET and HEAD on table, view, namespace, both collections, `/config`, and a management read | **none** stored; all counted |
| 7 | *not callable* — Polaris exposes no method outside the above **[assumed]** | unit tests only |

### `resource_kind` — all six values must appear

| kind | drive |
|---|---|
| `table` | `GET .../namespaces/{ns}/tables/{t}` |
| `view` | `GET .../namespaces/{ns}/views/{v}` |
| `collection` | `GET .../namespaces/{ns}/tables`, `.../views`, and `.../namespaces` |
| `namespace` | `GET .../namespaces/{ns}` |
| `management` | any `/api/management/v1/...` |
| `other` | `GET /api/catalog/v1/config`, `POST .../oauth/tokens`, `POST /{cat}/tables/rename` |

### Field coverage, and the ordering it forces

- **One resource with `requests`, `reads`, `writes` and `errors` all non-zero.** Order matters:
  **read it successfully first**, then write it, then provoke a 403 on it — an error on a
  resource never read successfully goes to `__other__` instead of creating its key.
- **`response_bytes`** — one resource with a non-zero total (any GET with a body) and one with
  zero (HEAD/DELETE returning 204). `%b` writes `-` for a zero-byte body and the parser
  normalises it to 0 **[verified]**.
- **`resources_other` > 0** — GET a table name that never existed. Cheap, and it simultaneously
  proves errors do not create keys.
- **The `/metrics` normalisation** — POST `.../tables/{t}/metrics`, then assert the table's
  `requests` includes it and that **no** row exists for the `/metrics` path.
- **Two principals with different mixes** — one read-heavy, one write-heavy — so the principal
  margin is proved to be per-principal and not a global total.
- **`min_record_time` / `max_record_time`** — assert they bracket the run's own timestamps.
- **`schema_version == 1`**, **`hostname` == the shipper pod name** (the validity block already
  captures it), **`window_seconds`** matches the deployed constant, **`window_start`** is
  aligned to a multiple of `window_seconds`.

### Not reachable from a client — assert these in the Lua unit suite instead

`local-k8s/logging/scripts/test-polaris-filters.py` runs the Lua extracted from the deployed
values file, so it can reach what an HTTP client cannot. It is at 48/48 today.

| field / branch | why the notebook cannot reach it |
|---|---|
| `parse_errors` | requires the Quarkus access-log pattern to change |
| `principals_other` | requires >200 distinct *authenticating* principals in one window |
| `resources_other` via the 500 cap | requires >500 distinct resources in one window (the error path covers the field itself) |
| `partial_window: true` | requires a shipper restart mid-run, which **invalidates** the run (§6). Cover it as a separate, explicitly flagged scenario, never inside the main run |
| rule 7, `PATCH` | Polaris exposes neither **[assumed]** |

---

## 6. The oracle has to grow, and this is the important part

Today `log_coverage.Policy` extracts `polaris_noise_filter` out of the **deployed**
`local-k8s/logging/fb-values.yaml`, runs it over synthetic records in one Lua interpreter, and
produces the `expected` keep/drop column. There is deliberately **no Python re-implementation to
fall back on**: a port that agrees with itself is not evidence, and the first time it disagreed
with the Lua the notebook would report a pipeline finding that was really a translation bug.

**That principle now has to extend to the counts.** Keep/drop is no longer the whole answer —
for most calls the answer is "counted", and the interesting question is *counted where, and how
much*. So:

1. Feed the same synthetic record sequence through the deployed Lua, as today.
2. Then feed it a **report tick** — call `polaris_noise_filter("polaris.report", 0, {})` — and
   capture the array it returns.
3. That array **is** the expected report. Diff it field-by-field against what VictoriaLogs
   actually stored for the corresponding window.

The filter carries a test hook for exactly this: `_now_override` on the tick record sets the
window clock, so the oracle can cross boundaries deterministically without sleeping. **It is
inert in the deployed pipeline** — the dummy input never sets it.

This makes "all schema coverage" a diff rather than a set of hand-written expectations, and it
keeps the tests un-driftable from what ships. **[assumed]** that `log_coverage.Policy` can be
extended to return array results; it currently expects a single record back.

### Correlation is different for report rows

Access-log records correlate to calls by `mdc.requestId`, exact **[verified]**. **Report records
carry no request id** — they are per-window aggregates. Join them on `report_seq` (unique per
`hostname`) or on `window_start`. The existing correlation machinery does not apply and should
not be forced to.

### The results matrix should change shape

`stored` is now 0 for most calls by design, so a matrix of `expected` vs `stored` mostly says
"correctly dropped" and hides the interesting part. Add columns: the **disposition**
(`kept` / `counted`), and for counted calls **which resource row and which principal row should
have incremented**. Then a mismatch names the row that is wrong.

---

## 7. Validity — what invalidates a v3 run

Record before and after, as the existing notebook already does for the first two:

- **The shipper pod restarting.** Counters are per-process and reset; `report_seq` restarts at 1
  and a window is flagged `partial_window`. A restart mid-run makes the counts unusable.
- **Polaris scaling.** The HPA allows 3 replicas appending to one log file (`local-k8s` #8).
- **The running ConfigMap must carry the v3 script.** Cell 0 already aborts when the deployed
  policy is not the one being tested — keep that, and update what it looks for: `RESOURCE_PATTERNS`
  and `MGMT_PREFIX` present, `DEDUP_MAX_KEYS` **absent**.
- **A `helm upgrade` during the run** replays the whole log file: the tail DB is on an `emptyDir`,
  `Read_from_Head true`, and VictoriaLogs does not deduplicate on ingest. Under v3 the replayed
  reads are absorbed as counts, but **every error and mutation replays as a full record** and the
  counters attribute the whole replay to whichever window it lands in. A window whose
  `min_record_time`/`max_record_time` span is far wider than `window_seconds` is a replay — check
  it before believing a spike.

---

## 8. What to produce

Update **both** together, as the project README requires — a report nobody updated is worse than
no report:

- `test_log_coverage.py` — the **invariants** must hold under any policy worth shipping (an
  error is never summarised away; every DELETE is kept; a line that will not parse is kept). Add
  the schema invariants from §2 to that set: they are policy-independent. The
  **characterization** test records what today's policy does and is expected to fail on the next
  change.
- `doc-log-coverage-results.md` — written by the final cell, for someone who was not there.

Then answer the two questions the previous run left open, both cheap once you are connected:

1. **Where does `app_lines` come from?** The last report said "34 of 122 calls produce no record
   at all" while those same calls carried 628 application lines, and `90 + 1,928 ≈ 2,026` implies
   that column is read from VictoriaLogs. Settle which, and correct the claim.
2. **`stats by (loggerName)`** — 1,928 of 2,018 stored records are application lines, so the
   filter governs ~4.5% of the volume. Which logger dominates is the input to the only remaining
   volume decision, and nothing can be designed for it until that number exists.

## 9. Known-open, do not re-derive

- **`neg.client_timeout` → "EXPECTED DROPPED, PRESENT"** is an oracle artefact, not a pipeline
  finding: a call with no client-side status is not predictable and should not be scored `drop`.
  Fix it here.
- **There is no `%D`**, so no request duration exists anywhere; client-side timing is the only
  source. Adding it needs a Polaris change and **Polaris is not to be changed**.
- **Stack traces:** 0 of 5 ERROR records carried an `exception` object. Settle it against the raw
  file rather than inferring:
  `kubectl -n datahub-hynix exec deploy/benchmarks-polaris -- grep -c stackTrace /deployments/logs/polaris.log`
- **A server-side hang leaves no line at all** — the access log is written when the response is.
  This pipeline is blind to it and no test can change that.
