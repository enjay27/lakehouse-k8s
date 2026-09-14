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

### The part that matters: this test is one-sided

The notebook asserts **presence**:

```
correlation: 286/286 calls recovered by request id
of those, errors (rule 3 keeps ALL of them -- an ASSERTION): 235/235
```

It never asserts **absence**. There is no check that a COUNTED call left no individual
record. And `286/286` does not mean 286 access-log lines were kept — `FOUND` searches
`polaris-logs-*` for the request id, and the application DEBUG lines carry that same id.
A counted-only call is findable *incidentally*, through whatever SQL its handler logged.

**Consequence: a filter that kept every single line would pass every retention check this
notebook makes.** The complementary test is specified — `SCENARIO-logging-test.md` T5,
"every counted call is absent (rule 6)" — and is not implemented here. Its own text says
it: *"T4 and T5 are the pair that matters and neither means anything alone: testing only
the first reports a policy that keeps everything as a pass."*

So the honest summary of this section is: **the run proves what is logged. It proves
nothing about what is not logged.**

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
