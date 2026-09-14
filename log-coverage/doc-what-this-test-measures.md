# What this traffic test covers, what it logs, and what it summarises

Reference for `polaris_log_coverage_v2.ipynb`. Figures from run `1789368559`
(2026-09-14), 286 calls, schema v3, 30s windows.

Written because three runs in a row produced findings that could not be read without
re-deriving all of this, and because the second section below is not what the notebook's
own headline numbers suggest.

---

## 1. What the traffic covers

**The denominator is the vendored OpenAPI documents, not the run.** `load_spec` reads
`log-coverage/spec/` and builds **63 operations** (33 management, 30 catalog) and
**286 cells**, where a cell is one (operation x status) pair. The grid exists before
anything is driven, which is why a drive that falls over halfway still has a denominator.

| target | cells | covered (run 1789368559) |
|---|---|---|
| 2xx (each operation's own success code) | 63 | 50 |
| 400 | 28 | 16 |
| 401 | 63 | 59 |
| 403 | 62 | 42 |
| 404 | 55 | 54 |
| 409 | 15 | 7 |
| **total** | **286** | **228** |

**30 of 63 operations have every planned cell covered.**

### What is deliberately out of scope, and why

Eight statuses are in the ledger rather than the grid. Three are `probe` (one call each,
recorded either way): **304** needs If-None-Match on `loadTable`, **406** needs content
negotiation, **419** is Iceberg credential-refresh that this build answers 401 to. Five are
`settled` with a structural reason: **429** (`rateLimiter.type` is no-op here), **502/504**
(nothing proxies Polaris; a port-forward is not a gateway), **503** (only reachable by
scaling Polaris, and HPA movement invalidates the run), **5XX** (a spec placeholder, not a
status). The build also returns two statuses the spec never declares: **405** and **500**.

### What is not covered, in order of size

1. **18 cells targeting 403 return 404.** Polaris declines to confirm a resource exists to
   a principal that may not see it. This is almost certainly correct behaviour and belongs
   in the ledger with that reason; counted as misses it makes the 403 column read as a hole.
2. **~14 cells across `planTableScan`, `cancelPlanning`, `fetchPlanningResult`,
   `fetchScanTasks`** — not routed on this build, 404 to everything.
3. **View reads** (`loadView`, `viewExists`, `replaceView`) miss their 2xx and 403.
4. **4 cells targeting 400 return 500** — malformed bodies that reach an unhandled path.

### What the run cannot cover at all

**`errors_5xx` is never exercised deliberately.** The 500 ladder walks four storage rungs
and every one is mapped to a 4xx by `IcebergExceptionMapper` (422, 400, 409) — NOT PROVOKED
is the contract working. The 500s that do appear are the PG-HA read-after-write signature
arriving by accident, and they are **writes that committed**, so they say nothing about the
unhandled-exception path. They also land on different cells every run: 4, then 8, then 4,
off identical code, moving coverage 228 -> 225 -> 228. **A coverage figure quoted without
its 500 count beside it is not a measurement.**

---

## 2. What is logged and what is not

### Two streams, one join key

A single API call produces records in two shapes, joined on `mdc.requestId`:

| | what it is | disposition |
|---|---|---|
| **access-log line** | `loggerName io.quarkus.http.access-log`, carries `http_status`, `response_size` | **counted first, then kept or dropped** by rules 3-6 |
| **application lines** | DEBUG/INFO/ERROR from Polaris itself — SQL, resolution, handler errors | rule 2 hands them to rule 1: **always KEPT, counted into nothing** |

Every access-log record is **counted before any keep/drop decision**, which is what makes
the report's margins exact regardless of retention.

### v3 dispositions

- **KEPT** — every 4xx/5xx (rule 3, no cap); every DELETE (rule 4); management POSTs
  (rule 5, the hole v2 left open); any line that will not parse (rule 1).
- **COUNTED ONLY** — successful reads, `/config`, table LISTs, renames, the token
  exchange (rule 6).
- **KEPT and NOT COUNTED** — every non-access-log record (rule 2). These appear in **no
  report field at all**.

### What the NOTEBOOK proves, and what it does not

The notebook asserts **presence** only:

```
correlation: 286/286 calls recovered by request id
of those, errors (rule 3 keeps ALL of them -- an ASSERTION): 235/235
```

It never asserts **absence**. There is no check that a COUNTED call left no individual
record, and `286/286` is not evidence about the access-log line at all — `FOUND` searches
`polaris-logs-*` by request id, and the application lines carry that same id, so a
counted-only call is findable *incidentally*. **On the notebook's evidence alone, a filter
that kept every single line would pass every retention check it makes.** The complementary
test is specified and unimplemented: `SCENARIO-logging-test.md` T5, *"every counted call is
absent (rule 6)"*, with its own warning that *"testing only the first reports a policy that
keeps everything as a pass."*

### What the OpenSearch export DOES prove — rule 6 holds

Run `1789368559`, exported from OpenSearch and checked by hand. **343 kept access-log
records** spanning the whole run (`06:49:20` → `06:52:31`):

| method | statuses present among KEPT records |
|---|---|
| GET | 400 ×1, 401 ×21, 403 ×20, 404 ×25 |
| HEAD | 401 ×3, 403 ×2, 404 ×5 |
| POST | 200 ×1, 201 ×20, 400 ×16, 401 ×19, 403 ×16, 404 ×31, 409 ×4, 422 ×6, 500 ×4 |
| PUT | 200 ×4, 201 ×40, 400 ×5, 401 ×7, 403 ×7, 404 ×7, 409 ×7 |
| DELETE | 204 ×25, 400 ×4, 401 ×9, 404 ×34 |

**Successful `GET` / `HEAD`: zero.** Not one read that succeeded survived into
`polaris-logs-*`, while 66 failing GETs did — so this is not an export artifact, since a
filter on the export would have to drop 2xx GETs and keep 4xx GETs.

And it pairs exactly with the report side. `seq=117` states *"7 counted (4 read, 3 POST)"*,
and those four reads are visible as `last read 53 / 41 / 41 / 548` on four resource rows —
with **no corresponding access-log record anywhere in the export**. Counted, not kept,
demonstrated on both sides of the same window.

**So rule 6 is proven for the access-log stream** — by the export, not by the notebook. T5
is still worth implementing, because this was a hand check of one run.

### The reconciliation that settles it — run `1789370776`

The second export is complete enough to check the filter's own arithmetic against the index,
across **11 consecutive report windows** (`seq` 184–194):

| | |
|---|---|
| access lines the filter says it **saw** | **433** |
| it says it **kept** | **343** |
| it says it **counted only** | **90** |
| access-log records actually in `polaris-logs-*` | **343** |
| **delta** | **0** |

**Every record the filter claims to have kept is in the index, and not one more.** So the 90
counted-only records are demonstrably absent — this is rule 6 verified by quantity, not just by
the shape of what survived. It also rules out transit loss over the same window.

And the margin holds on **11 of 11 rows**, not merely the six the notebook checks:
`sum(resource.requests) == sum(principal.requests) == access_seen` on every window in the
export.

Successful `GET`/`HEAD` among the 343: **zero**, on a second independent run.

### Where the offset comes from, visible in the same table

Mapping the report's per-window counts onto the phases the notebook drove:

| report label | access lines | the phase that actually ran |
|---|---|---|
| 07:26:30Z | 180 | phase C, driven at **07:27:00** |
| 07:27:00Z | 44 | phase D, driven at **07:27:30** |
| 07:27:30Z | 1 | phase E, driven at **07:28:00** |
| 07:28:30Z | 7 | phase G, driven at **07:29:00** |
| 07:29:00Z | 53 | phase H + teardown, driven at **07:29:30** |

Every phase lands one window early. And the exception proves the mechanism: the one window
measured at offset `0` is the fixture setup, whose traffic is spread across its window instead
of arriving as a burst just after a boundary. **The window a row receives depends on when
inside it the traffic landed** — so no fixed shift can correct this downstream, and the join
has to be on `report_seq` via the summary row's own record bounds.

### Also confirmed by the export

- **`last_write_bytes` / `last_read_bytes` work.** `last write 536` and `117`, `last read
  53`, and the field **absent** exactly where the response was 0 bytes — the `> 0` guard.
  A Gate 2 VOID means the gate read a window with no sized table write in it, not that the
  feature failed.
- **The margins hold, hand-checked.** `seq=117`: 53 access lines; principals 26+27+0 =
  **53**; the 27 resource rows sum to **53**.
- **Zero-carry works.** `seq=118` is fully carried: 29 rows all zero, `carried 29` = 27
  resources + 2 principals.
- **The window offset is visible in OpenSearch, independently of the notebook.** `seq=117`
  is labelled `06:52:00Z..06:52:30Z` and its kept access lines are stamped `06:52:31`.

### Volume, for scale

3,336 records carried this run's request ids — about **11.7 records per call**, and the
sampled audit record is a DEBUG line containing full SQL with bound parameter values. The
access-log stream is a small minority of what reaches OpenSearch.

---

## 3. What is summarised

`polaris-report-*` carries **three document types per flush**, all sharing `report_seq`,
`hostname`, `window_start/end/seconds` and `schema_version`.

**`summary`** — one per window per host, 34 fields. The window's accounting:
`access_seen` / `access_kept` / `access_counted`, split `counted_read` / `counted_post`;
`errors_kept` / `errors_4xx` / `errors_5xx` / `auth_denied`; `bytes_total`;
`distinct_resources` / `distinct_principals`; the overflow counters `resources_other`,
`resources_other_distinct`, `principals_other`; `carried_rows`; `role_keys_forced`;
`parse_errors`; `min_record_time` / `max_record_time`; `partial_window`; `windows_skipped`.

**`resource`** — one per resource key per window, 24 fields. `resource` (the normalised
path), `resource_kind`, `api_kind`, then `requests` / `reads` / `writes` / `errors`
(+`errors_4xx`, `errors_5xx`, `auth_denied`), `response_bytes`, and the v3 feature
`last_write_bytes` / `last_read_bytes`.

**`principal`** — one per principal per window, 21 fields: `user_principal_name` plus the
same counters.

### Structure worth knowing

- **`resource_kind` in v3** (observed live): `table`, `view`, `collection`, `namespace`,
  `auth`, `config`, `transaction` under `api_kind: catalog`; `catalog`, `catalog-role`,
  `principal`, `principal-role`, `collection` under `management`; `error` under `mixed`.
  **`management` is no longer a `resource_kind`** — it moved to `api_kind`.
- **Two synthetic keys.** `__errors__` holds requests whose resource attribution was lost
  (the record is still kept by rule 3); `__other__` is overflow past the key cap
  (`REPORT_MAX_ROLE_KEYS = 100`). An error never creates a resource key — that is what
  keeps the margins exact.
- **Zero-carry.** Each window re-seeds the previous window's keys at zero, counted by
  `carried_rows`. "The only resource row" is therefore the wrong selector; the row a call
  incremented is the one with a non-zero request count.
- **The margins**, and they hold 6/6: `sum(resource.requests) == sum(principal.requests)
  == access_seen - parse_errors`.

### What is NOT summarised

- **The application records.** Rule 2 keeps them and counts them into nothing, so the
  ~11 DEBUG/INFO/ERROR lines per call appear in no report number. The report describes the
  access-log stream only.
- **Per-status detail** beyond the 4xx/5xx/denied split. There is no per-code histogram.
- **Latency.** Nothing in any shape carries a duration.
- **Operation identity.** `resource` is a normalised path, not an `operationId`; two
  operations on one path are one row.

### Known defects in the summarised data

1. **Window attribution is wrong and is not a constant offset.** A row labelled W can hold
   the traffic of W+1: `window_start 06:52:00Z` carried `min_record_time 06:52:30.573`.
   Measured across rows the offset is `{-30: 5, 0: 1}` — it depends on where in the window
   the traffic lands, so **no single shift can correct it**. This is why Gate 2 is VOID and
   Gate 4's counts come from a window that does not contain its grants. The invariant
   `record times fall INSIDE their own window` fails 6/6 and is the only record of it.
2. **`min_record_time` is mapped `text`**, so no date maths works on it in-index. Likely
   cause is the nine fractional digits (`window_start`, with none, maps `date` in the same
   index), not the empty string the earlier hypothesis blamed.
