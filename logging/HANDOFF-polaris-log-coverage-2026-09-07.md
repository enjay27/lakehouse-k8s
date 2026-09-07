# HANDOFF — what the Polaris log-coverage runs measured, and what `local-k8s` has to do about it

**Written 2026-09-07 for a session starting cold in this repo.** Everything below was measured
against the deployed pipeline, not inferred from the values file. It is written to be read
without the conversation that produced it.

- **Where the measurements come from:** `polaris-practice/polaris-learning/log-coverage/` —
  `polaris_log_coverage.ipynb` drives the whole Polaris API surface, then compares what
  VictoriaLogs stored against what the **deployed** `logging/fb-values.yaml` Lua predicts, by
  extracting `polaris_noise_filter` from this file and running it under a real Lua interpreter.
  The full record is `log-coverage/doc-log-coverage-results.md` in that repo.
- **Runs referenced here:** `1788511328` (2026-09-04), `1788744260` and `1788745242`
  (2026-09-07). Shipper pod `fb-polaris-shipper-fluent-bit-68b4959db4-4f7tf`, up since
  2026-09-04T08:14:13Z, unrestarted throughout. `fb-values.yaml` sha256 `063c184df3f9f475`.
- **What this repo owns and the test repo does not:** the three items in the next section.

---

## Three things for this repo

### 1. Revert the fast-run settings — they are still live

`fb-values.yaml` is running values that were made temporary for testing and say so in their own
comments:

| | line | now | steady state |
|---|---|---|---|
| `WINDOW_SECONDS` (in `polaris_noise_filter`) | ~187 | **30** | 1800 |
| dummy INPUT `Interval_Sec` | ~596 | **5** | 30 |

They must be reverted **together** — the tick has to stay well under the window, or a late tick
lets a boundary pass unnoticed and a whole window's counters are attributed to the next one.
The file's own comments at lines 187–193 and 583–589 say the same thing.

```bash
helm upgrade --install fb-polaris-shipper fluent/fluent-bit \
  --version 0.58.1 -n datahub-hynix -f logging/fb-values.yaml
```

**Cheap confirmation, no full run needed:** in the test repo, execute only cells 0 and 0b of
`polaris_log_coverage.ipynb` (preflight and the v3 gate). They check that the running ConfigMap
carries the file's script, read `WINDOW_SECONDS` and `Interval_Sec` from the deployment, assert
the tick is well under the window, and assert zero raw tick leak. Minutes, not the ~90 that a
full drive at 1800 would cost.

> **RESULT (fill in):**
>
> - reverted on:
> - `helm upgrade` output / ConfigMap sha:
> - cells 0–0b verdict:

---

### 2. Exception stack traces DO survive the pipeline — no action needed here

**Confirmed 2026-09-07, and this section previously said the opposite.** The earlier claim —
"Polaris writes no stack traces" — was an artefact of searching for a field name this build does
not use. It is corrected here rather than deleted, because the shape of the mistake is worth
more than the conclusion was.

**What is true.** An ERROR record in `/deployments/logs/polaris.log` carries a top-level
`exception` key, alongside the standard Quarkus JSON fields:

```
['exception', 'hostName', 'level', 'loggerClassName', 'loggerName', 'mdc', 'message',
 'ndc', 'processId', 'processName', 'sequence', 'threadId', 'threadName', 'timestamp']
```

The payload is Quarkus's **structured** exception output — an object carrying a `frames` array
of `{class, method, line}`, roughly 60 frames for an unhandled 500 — **not** a `stackTrace`
string. And it **reaches VictoriaLogs intact**: the frames were read back from VMUI for a
`createNamespace` 500, top frame
`org.apache.polaris.service.catalog.iceberg.IcebergCatalogHandler.createNamespace:306`.

**So the spec's §1 SLA holds for this field.** "Sub-second query across arbitrary structured
JSON fields (… exception stack traces)" is satisfied: the traces exist, they survive the
shipper, and they are structured rather than a blob of text. **Do not change the Quarkus
exception-output configuration.** There was never anything wrong with it.

**Why it was reported as missing, because the trap is reusable.** Two checks were run and both
returned zero: `grep -c stackTrace` on the source file, and the notebook's
`"exception" in record` against what VictoriaLogs returned. The first used a name this build
does not emit. The second failed because **VictoriaLogs flattens nested objects into dotted
keys**, so the stored field is `exception.frames`, not `exception`. Two searches for the wrong
name agreeing with each other read as corroboration and are not. Anyone querying these records
should expect `exception.*`, exactly as `mdc.requestId` is already the flattened form of `mdc`.

**The one thing left, and it belongs to the test repo, not here:** the 500 that produced these
records arrived by accident — the PG-HA read-after-write failures on `create_namespace` /
`create_view`. The deliberate probe (`neg.500_null_pointer`) has returned 200 for three runs, so
nothing in the suite provokes an ERROR on purpose yet, and the coverage of this path is
therefore not repeatable.

> **RESULT (fill in) — only if something here changes:**
>
> - exception field name as stored in VictoriaLogs:
> - is it queryable (a filter on the exception type that matches):

### 3. The retention policy governs ~2% of the volume

Run `1788745242`, 146 API calls, 2,500 records stored in VictoriaLogs:

| | |
|---|---|
| access-log records (**everything the policy can decide about**) | **56 — 2.2%** |
| application lines, passed through untouched by rule 2 | 2,444 — 97.8% |
| `…jdbc.DatasourceOperations` alone | **1,521 — 60.8%** |
| `…iceberg.IcebergCatalog` | 250 |
| `…io.StorageAccessConfigProvider` | 172 |
| `…storage.cache.StorageCredentialCache` | 93 |
| `io.quarkus.http.access-log` | 56 |

`fluentbit_filter_drop_records_total` on `polaris_noise_filter` reads **1,943** cumulative,
which reconciles exactly: the filter has seen `records 21,817 = 20,322 tailed + 1,495 ticks`,
and the drops are the non-boundary ticks it swallows plus the counted-only access records of
every run so far.

**Why this matters here:** the spec's storage-reduction strategy is built on deduplicating
high-frequency access-log traffic — "slashing redundant access log volume by >99%". On this
cluster that strategy is pointed at a fiftieth of what is being stored, and **the single largest
producer is a JDBC operations logger that no retention rule touches.**

**Caveat, and it is a real one:** this is a single-user local cluster driving 146 calls. The
spec's 10M–140M records/day and its ~11M table GETs/day are production projections, where the
access-log share would be far higher. **The finding is not "the strategy is wrong" — it is that
the assumption behind it has never been measured on real traffic, and on the only traffic that
has been measured it does not hold.** The decision this repo owns: measure the logger mix on a
production-like load before trusting the volume model, and decide whether
`DatasourceOperations` should be at its current level at all.

> **RESULT (fill in):**
>
> - logger mix on prod-like traffic:
> - decision on `DatasourceOperations` level:
> - change to the volume model, if any:

---

## What is settled about the deployed filter — do not re-derive it

All of this was verified against the running pipeline, not the oracle alone.

- **Policy v3 does what its table says.** First match wins; every access record is counted
  before any keep/drop decision. Errors (`>= 400`) are kept with no cap; PUT/DELETE/PATCH kept;
  **every `POST` under `/api/management/` kept** — measured 6 of 6, which closes the v2 audit
  hole where a credential reset left no trace at all. Successful reads, `/config`, table LISTs,
  renames and the OAuth token exchange are counted only.
- **The scheduled flush report works end to end.** Fluent Bit splits the Lua's array return into
  separate records; VictoriaLogs indexes their numbers as numbers (`requests:>0` matches);
  no raw tick leaks; `report_seq` increments by one per report; counters reset; exactly one
  summary per window per host at six ticks per window.
- **Zero-carry and carry decay hold in the pipeline**, not just in the oracle: a resource active
  in one window reports an explicit 0 in the next and is not carried a third time.
- **The margins are exact and non-trivial.** `sum(principal.requests) == access_seen -
  parse_errors` verified at 249 across **four** principals with different mixes (a write-heavy
  root, a read-and-error-only denied principal), so the equality is no longer satisfiable by a
  global counter.
- **`/metrics` folds onto its table's row** (v2 emitted two rows for one table), an error never
  creates a resource key (it lands in `__other__`), and all six `resource_kind` values are
  reachable from the deployed `classify()`.
- **`type_int_key` is in effect.** `http_status:>=400 -> 46`, `http_status:"404" -> 25` scoped to
  one run's own errors. The status-range recipes in the spec are not silently empty.
- **The pipeline agrees with the deployed Lua.** Three runs, and in the last two, **zero**
  mismatches in the direction that would mean a record was lost. The residual differences are
  the test notebook's own fixture setup and teardown, which the oracle is not given.

## Properties of the filter worth knowing before changing it

1. **A startup blind spot.** `report_tick` opens its first window on the FIRST tick, and
   `count_record()` returns immediately while `counts` is nil. Records processed between shipper
   start and that first tick are routed by the policy correctly but appear in **no report at
   all**. Bounded by the tick interval — **which means reverting `Interval_Sec` to 30 widens
   this window from 5 seconds to 30.** The window they land in is flagged `partial_window: true`.
2. **One of the report's four invariants is tautological.** `build_report` computes
   `access_kept` by subtraction, so `access_kept + access_counted == access_seen` can never
   fail. It is worth asserting only end to end, where it becomes a transport check. The only
   real self-check is the resource/principal margin pair.
3. **`WINDOW_SECONDS` is not a parameter a caller can pass in.** The filter indexes windows with
   its own constant, so anything assuming a different value crosses no boundary and gets an
   empty result rather than an error.
4. **The report stream's clock only advances while the host is awake** — see below.

## What NOT to re-test — falsified, with the measurement

- **"Three report windows are missing, so the filter stalls."** They are missing
  (`2026-09-07T00:36:00Z`–`00:37:00Z`) and it is not the filter. The HTTP output reports
  `errors 0, retries 0, retries_failed 0, dropped_records 0` cumulative since the pod started,
  so nothing emitted was lost in transit; and `polaris_report_tick` has produced **1,495
  records against ~65.5 hours of uptime**, where `Interval_Sec 5` implies ~47,000 — about 3%.
  **The OrbStack VM is suspended with the MacBook**, the container's timer does not fire, and a
  window that never opened cannot be reported. A gap after a sleep is expected here.
  **Corollary: no measurement over the report stream that spans a sleep can be read as elapsed
  time** — "333 reports in 24h" is 2.8 hours of windows, not a rate.
- **"`fluentbit_filter_drop_records_total` is enormous."** It read 7,154,980,971,680 once. That
  was a bug in the *test repo's* parser — Fluent Bit's Prometheus encoder appends a millisecond
  timestamp after the sample value and the parser took it as the value. Fixed there. The real
  figure is 1,943 and this repo need do nothing.
- **"A client-side timeout demonstrates the pipeline's blind spot."** It cannot. Quarkus still
  completes the response and writes the access line. The real blind spot is a **server** hang,
  which leaves no line at all and which no client can provoke.
- **"There is a `%D` somewhere."** There is not. No request's duration is recorded anywhere in
  this pipeline; the only latency figures in existence are client-side (median 13 ms, p95 65 ms,
  max 92 ms across 146 calls). If durations are wanted, the access-log pattern in the Polaris
  deployment is the place, and that is a change this repo owns.

## Two open items that are not this repo's, listed so they are not lost

- `neg.500_null_pointer` in the test notebook has returned **200** for three runs — the
  `create_catalog_no_endpoint` provocation no longer reproduces on this build. The ERROR path
  has only ever been exercised by accident, via the PG-HA read-after-write 500s on
  `iceberg.create_namespace` / `iceberg.create_view`. Those 500s are themselves unexplained and
  recur across sessions.
- The test repo's fixture setup and teardown are not tagged into its own call inventory, which
  is the entire remaining difference between its oracle and the pipeline.

---

## How to reproduce any of this

```bash
# port-forwards the notebook expects
kubectl -n logging       port-forward svc/vlsingle-victoria-logs-single-server 9428:9428
kubectl -n datahub-hynix port-forward deploy/fb-polaris-shipper 2020:2020   # metrics
kubectl -n datahub-hynix port-forward pod/benchmarks-postgresql-postgresql-ha-postgresql-0 5433:5432

# then, in polaris-practice/polaris-learning/log-coverage/
uv run jupyter lab      # Restart & Run All on polaris_log_coverage.ipynb
```

The notebook aborts before driving anything if the ConfigMap does not carry the script in
`fb-values.yaml` — it was written after a run measured a policy that had been written and never
deployed, and that check exists so it cannot happen twice.

> **RESULT — anything else this session found (fill in):**
>
