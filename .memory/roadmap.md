# Roadmap — what is done, what is next

A line here needs a **number or a verified state**. Anything still hypothetical
belongs in [`active-issues.md`](active-issues.md); the story of how it was found
belongs in [`sessions/`](sessions/).

## Done

**The cluster rebuild closed on 2026-09-03.** Kade reset the whole OrbStack cluster
and rebuilt the K8s services himself, outside the runbook, resolving the four config
blockers along the way. Fluent Bit runs as a DaemonSet and is confirmed working.
OpenSearch runs in Docker, outside the cluster. Detail in
[`completed.md`](completed.md); `RESET-AND-CLEAN-INSTALL.md` and
`local-k8s-HANDOFF.md` are now historical.

## Next

**Current (2026-09-16, late) — read this first; the table below is the VictoriaLogs-shipper era and mostly historical.**
The built pipeline is the Fluent Bit DaemonSet → OpenSearch, policy v5 / report schema 6 with the refactored one-filter Lua
(`active-issues.md` #28, #30, #31, #32, all verified on traffic). The order of work is
`logging/HANDOFF-pipeline-next-2026-09-16.md` §3; the task table is `logging/PLAN-audit-log-todo-2026-09-16.md`; open design
decisions are `logging/REVIEW-pipeline-2026-09-16.md` P1–P12. Retention/ISM is the Monitoring team's.

Numbers from 2026-09-16, one traffic window (30 s, identical on 08:41Z, 14:44Z, 15:01Z): 720 Polaris records → 355 access lines,
300 detail docs (200 access / 22 PolarisServiceImpl / 78 IcebergExceptionMapper), 67 report rows; 404: 100 counted, 0 stored.
Lua time per record ~5.8 µs → ~2.1 µs after the refactor (LuaJIT bench, not pod CPU). A record enters the Lua with 16 keys /
~717 B, 7 of them removed right after (review P1) — fixed in v6. v6 on the same traffic (16:02:30Z): counts identical; JSON doc size
access 705 → 649 B, app 799 → 743 B, report row 755 → 518 B.

*Historical, 2026-09-03 onward:* Polaris logging is the live thread. The design it is being built against is
`logging/polaris-logging-architecture-spec.md` (filed 2026-09-03); the audit that found the
gaps is [`sessions/2026-09-03-polaris-vlogs-audit.md`](sessions/2026-09-03-polaris-vlogs-audit.md).

| # | step | why it is next |
|---|---|---|
| 1 | **Done** — access-log field extraction, the retention policy (`polaris_noise_filter`), and the shipper's silent faults: tail `DB`, `Skip_Long_Lines On`, `Rotate_Wait`, filesystem buffering, `json_date_key false`, per-record `Remove_key` | all in `logging/fb-values.yaml`; **46/46** in `logging/scripts/test-polaris-filters.py`. Installed 2026-09-04T04:57:36Z and measured working (34 of 34 drops). **Policy v2 written 2026-09-04 and not yet installed** — `active-issues.md` #14. `Alias` on the filters now makes `fluentbit_filter_drop_records_total` attributable per filter; sample it **before** the v2 upgrade. |
| 2 | **Done** — the API-coverage notebook exists in `polaris-learning/log-coverage` and has run twice (2026-09-04). It runs the *deployed* Lua as its oracle, which is what caught #13 | it is what answers the parked questions — the WARN messages behind the "Deprecated Config" exclusion, where a PUT body is logged (or that the PostgreSQL `events` table is the real audit channel), whether stack traces survive, whether `mdc.requestId` joins reliably, and the create/delete audit asymmetry below. |
| 2 | Give the tail DB a PVC instead of the emptyDir | the emptyDir survives a container restart but not `helm upgrade`, and a fresh DB with `Read_from_Head true` re-posts the whole file. Block to uncomment is in `fb-values.yaml`. |
| 3 | Harden VictoriaLogs: `retention.maxDiskSpaceUsageBytes`, right-size 50Gi/4Gi, decide on the 9428 `LoadBalancer` | `active-issues.md` #7. 9428 is unauthenticated ingest **and** query; `persistence.size` is now-or-never. |
| 4 | Rotate the OpenSearch password (#4), the JDBC password (#9), the MinIO keys | a committed credential stays leaked after the file is edited. Three places now. |
| 4b | **Decided, in policy v2** — rule 5 is now a drop-list, not a keep-list: every POST is kept except `/oauth/tokens`, which is kept once per principal per KST day | the asymmetry was measured, not predicted: eight endpoints including `reset_principal_credentials` left no access-log record. Cost of the fix, in that run's profile: **+10 records per 122 calls, 0.5%**. Not running until the shipper is upgraded (#14b). |
| 5 | Decide on `autoscaling` vs the shared log file | `active-issues.md` #8. Three Polaris pods appending to one file; RWO does not stop it on one node. Needs a Polaris change, so it waits. |
| 6 | `%D` in the access-log pattern — **then exempt slow requests from dedup** | spec §7's P99 panels need it, and a table GET that normally takes 8ms taking 4s is exactly the record daily dedup discards. Needs a Polaris change, so parked with #5. |
| 6b | The "Deprecated Config" WARN exclusion, and PUT request bodies | hook is in the filter, marked TODO. Request bodies are not in the access log at all — Kade is locating the source. |
| 6c | **Report schema v2 — DEPLOYED 2026-09-07 and measured correct** (run `1788755035`, sha `d58b9203a8304030`: both margins 158, `errors_4xx` 41/41/41, `auth_denied` 12/12/12, `bytes_total` 1,186,348 on both sides; 38 active + 4 + 6 carried = 48 rows, carry decays in two windows). **The harness has not caught up — 34 mismatches, none a filter fault** ([`HANDOFF-harness-schema-v2`](../logging/HANDOFF-harness-schema-v2-2026-09-07.md)). `SCHEMA_VERSION 2`: `distinct_resources`/`_principals` count only rows with `requests > 0`, remainder in `carried_rows`; `counted_get` -> `counted_read` (it counted HEAD); added `errors_4xx`/`errors_5xx`/`auth_denied`, `bytes_total`, `resources_other_distinct`, `windows_skipped` | **60/60** in `logging/scripts/test-polaris-filters.py`, incl. a new suite 4 that fails when a numeric field is missing from `type_int_key` — the failure mode is a silently-stored string and an empty numeric query. `helm lint`/`--dry-run` NOT run, no cluster reach. Decisions in [`sessions/2026-09-07-report-schema-v2.md`](sessions/2026-09-07-report-schema-v2.md). |
| 7 | `vmalert` + log→metric downsampling | spec §8. **The shipper-side half now exists**: the flush report counts table reads, principal requests and suppressions per 30-minute window and ships them to VictoriaLogs as `app:polaris-shipper-report`, queryable with `\| stats`. What is still missing is alerting on it, and there is no VictoriaMetrics in this cluster — the alternative shape, a `log_to_metrics` filter scraped into a TSDB, needs a component that does not exist yet. |
| 8 | Hand back to `polaris-learning` | The platform exists to serve that suite; see below. |

**Measured 2026-09-04, and it reframes the exercise:** 122 API calls stored **2,026
records** — 90 access-log lines and **1,928 application lines**. The noise filter can only act
on the first group, so it governs **4.5% of the volume** and its 34 drops removed **1.7%**.
Rules 3–7 buy audit fidelity, not storage; storage is the DEBUG SQL records (`active-issues.md`
#5b), which must be *routed*, not turned down.

Numbers worth holding on to, from the design doc: the pipeline is specified for **10M/day
normal and 140M/day peak at 30-day retention**, with the `GET .../tables/{t}` poll traffic
(**~11M/day**) deduplicated at the shipper. On this single OrbStack node none of those
numbers apply — the local instance is a correctness rehearsal for that design, not a load
test of it, and sizing should be chosen for the laptop, not copied from the doc.

## Polaris 1.6.0 — the numbers, and what to assert after the upgrade

Established 2026-09-18 by reading upstream at tag `apache-polaris-1.6.0`. Cluster side
unverified — see `active-issues.md` #33.

| fact | value |
|---|---|
| 1.6.0 required metastore schema version | **4** (`DatabaseType.java`, all three DB types) |
| this install's schema version | **4** — MIGRATED and MEASURED 2026-09-18 on primary pg-1: `version|4`, 9 tables in `polaris_schema` (was 3 / 6 tables before step 2e) |
| v3 → v4 new objects | 3 indexes + 3 tables + 5 indexes = **11 objects**, 0 ALTERs — VERIFIED 2026-09-18 against the shipped files (`#34`) |
| shipped v3 vs repo `schema_v3.sql` | **indentation only** — the "authority" claim in CLAUDE.md is true, tested 2026-09-18 |
| shipped v4 object counts | v3 10, v4 21, adds 11; 10 shared objects, **0 differing** |
| shipped v4 non-object statements our migration lacked | **2** `COMMENT ON TABLE` (lines 226, 295) — added; no GRANT / FUNCTION / ALTER / seed INSERT exists in v4 |
| live `polaris_schema` after step 2 | 9 tables, **21 indexes** (8 new + v3's 3 + 9 PKs + `constraint_name`), `version_value` 4 — MEASURED 2026-09-18 |
| `schema.sql` vs `schema_v3.sql` | same 10 objects, **0 differing**, both version 3; differ only by v3's **24 `COMMENT ON`** statements (`#36`) |
| v3's 4 table comments in the live DB | **absent** — so it was not bootstrapped from `schema_v3.sql` (`#36`) |
| HPA and a Deployment at 0 replicas | **cannot scale it up** — scaling from 0 needs the alpha `HPAScaleToZero` gate. Scale-to-0 is a safe hold; step 4 must scale back up explicitly |
| step 3 render, 2026-09-18 | `console.level=INFO`, **0** category lines at DEBUG, `event-listener.types` plural with `PT5S`/`1000`, `apache/polaris:1.6.0` — all PASS |
| categories demoted DEBUG → INFO | **13**, counted from the step 3 diff (this repo said "ten" until 2026-09-18) |
| total config change in step 3 vs live | exactly two kinds: the listener key `type` → `types`, and those 13 categories. Nothing else moved |
| `quarkus.log.file.enabled` | **`false`, live and rendered** — so no log file is written, and `extraEnv`'s two `QUARKUS_LOG_FILE_JSON_*` vars are inert (`#38`) |
| Polaris chart hook image | `bitnami/kubectl:latest`, `pre-install,pre-upgrade`, no `imagePullPolicy` → pulled `Always` from Bitnami's retired public catalog (`#37`) |
| Polaris replicas after step 4 | **3** — HPA scaled on `memory: 88%/80%` at `cpu: 2%`, MEASURED 2026-09-18 (`#39`) |
| why 3 and not 1 | HPA measures memory against the **`1Gi` request**; `-XX:InitialRAMPercentage=50` commits **`1Gi`** (50% of the `2Gi` limit) at startup → target exceeded at idle, and it cannot fall back |
| JVM heap vs container | initial `1Gi`, max `1.33Gi` (65% of `2Gi` limit) → ~`0.67Gi` for all non-heap. Watch `restartCount` for OOMKills |
| `#15` hypothesis C | **ALIVE again** as of 2026-09-18 — killed at step 0b on one pod, revived six hours later by `#39` |
| `events` max `timestamp_ms` after step 4 | `1789574562296` = **2026-09-16T16:02:42Z**, i.e. PRE-upgrade. 2528 rows. Proves survival, **not** that the listener writes on 1.6.0 |
| v5 (`events.catalog_id` nullable) | **1.7.0**, not 1.6.0 |
| 1.6.0 image tag | `1.6.0` — no `-incubating`; graduated after 1.3.0 |
| `polaris.event-listener.type` | deprecated upstream **since 1.5.0**; plural `types` is current |
| upstream chart default `logging.console.threshold` | **`ALL`** — so INFO discriminates |
| 1.7.0 trap | `OPTIMIZED_SIBLING_CHECK` 403s every nested namespace (apache/polaris#5521); 1.6.0 clear |

**Measured on 1.3.0, 2026-09-18 — step 0 complete:**

| measurement | value |
|---|---|
| `polaris/values.yaml` (working tree) vs live R5 user-supplied | **identical on 210 keys** bar the 14 `afc88e2` changed → `#5` REFUTED |
| live user-supplied vs computed (`--all`) | 209/210 identical → **no chart-default layer** |
| Polaris pods / HPA | **1 pod**, `MINPODS 1 MAXPODS 3 REPLICAS 1`, `cpu 1%/80% memory 30%/80%` |
| release revisions | 5; R5 `deployed` 2026-09-15 17:34 |
| console output format | **JSON** — `QUARKUS_LOG_CONSOLE_JSON_ENABLED=true` (ordinal 300) beats the ConfigMap `format` (250) |
| `topologySpreadConstraints` selector | `app.kubernetes.io/name: polaris` → **matches 0 pods**, inert since install |
| Agroal pool per pod | `MIN_SIZE 10`, `MAX_SIZE 300` |
| 1.6.0 base image | `registry.access.redhat.com/ubi9/openjdk-21-runtime` → `-XX:+ZGenerational` valid (removed in JDK 25) |
| 1.6.0 Quarkus | **3.36.3** |

**Assertions to run after the upgrade** — each reads the running object, not a values file:

1. `kubectl -n datahub-hynix get pods -l app.kubernetes.io/name=benchmarks-polaris -o jsonpath='{.items[*].spec.containers[0].image}'`
   (the label is the **chart** name, `benchmarks-polaris`; `=polaris` matches nothing)
   → every pod `apache/polaris:1.6.0`.
2. `SELECT version_value FROM polaris_schema.version` → **4**.
3. ConfigMap `application.properties` contains `quarkus.log.console.level=INFO` and
   **zero** `quarkus.log.category."…".level=DEBUG` lines.
4. ConfigMap contains `polaris.event-listener.types=persistence-in-memory-buffer`, with
   `buffer-time=PT5S` and `max-buffer-size=1000`.
5. `SELECT count(*), max(timestamp_ms) FROM polaris_schema.events` advances after the
   upgrade — the listener survived 1.6.0's event-persistence overhaul.
6. `\dt polaris_schema.*` lists `idempotency_records`, `scan_metrics_report`,
   `commit_metrics_report`.
7. One `polaris-logs-*` window after the upgrade is **comparable to** one before — *not*
   smaller. Stdout has been INFO-only since R5, so there is no DEBUG traffic for the
   threshold to remove. A material shrink is an unexplained change, not a success.
   (`step10` / `step11`, not Dev Tools copies.)
8. `kubectl logs deploy/benchmarks-polaris --tail=5` still returns **JSON objects**. Plain
   text means `QUARKUS_LOG_CONSOLE_JSON_ENABLED` stopped being honoured and the tier-2 Lua
   is parsing nothing.
9. No `Unrecognized VM option` in the pod log — the ZGC flags survived the image change.

## PostgreSQL verification assertions

Not run against the rebuilt cluster — Kade's call, to be run if a PostgreSQL setting
needs changing. Kept here because these are the checks that would have caught #F1
years earlier. Each is a fact, not an intention:

| assertion | expected | proves |
|---|---|---|
| pgpool pod count | **3**, not default 1 | the nested `pgpool:` block is live |
| `persistence.size` | **10Gi**, not 8Gi | the nested `postgresql:` block is live |
| `max_connections` / `shared_buffers` | **200 / 384MB**, not 100 / 128MB | `extendedConf` is live |
| `/dev/shm` | **1G**, not 64M | the emptyDir mount is live; closes the OrbStack K8s leg of S5 |
| `pg_hba` matching rules | **3** | both address families present |
| `shared_preload_libraries` | `repmgr` still present | automatic failover works |
| repmgr cluster show | 3 nodes healthy, exactly one primary | replication is real |
| Polaris `/q/health` on **8182** | green | Polaris reached its metastore and its bucket |

Install order, kept because it is one-directional and still true for any reinstall:
`minio → postgresql → polaris → datahub-prerequisites → kafka → schema-registry →
datahub → spark → airflow → argo → jupyter → fluent-bit`.

## Handing back to `polaris-learning`

Tail `deploy/benchmarks-polaris` into `capture/polaris.log`, then
`check_sql_logging.py` should print *SQL DEBUG logging is WORKING*. Two corrections
to carry across: `polaris-learning/CLAUDE.md` says PgBouncer and must say
**Pgpool-II**, and its pre-rebuild configuration table is now historical — the
cluster it describes no longer exists.

**Measured 2026-09-07** — three runs (`1788511328`, `1788744260`, `1788745242`), full record in
`logging/HANDOFF-polaris-log-coverage-2026-09-07.md`:

- **146 API calls stored 2,500 records; 56 of them — 2.2% — are access-log lines.** Everything
  the retention policy can decide about is that 2.2%. `…jdbc.DatasourceOperations` alone is
  **1,521 records, 60.8%**, and no retention rule touches it. The spec's ">99% access-log
  reduction" strategy is pointed at a fiftieth of this cluster's volume. Single-user local
  traffic, so the finding is that **the assumption has never been measured**, not that it is wrong.
- **Exception stack traces DO survive the pipeline.** Quarkus writes a structured `exception`
  object with a ~60-frame `frames` array; VictoriaLogs flattens it, so the stored field is
  **`exception.frames`**, not `exception`. The earlier "no stack traces" claim was two searches
  for a name this build does not emit, agreeing with each other.
- `fluentbit_filter_drop_records_total` on `polaris_noise_filter` = **1,943**, reconciling
  exactly against 21,817 records seen (20,322 tailed + 1,495 ticks). The 7.1-trillion reading
  was the test repo's parser taking Fluent Bit's millisecond timestamp as the sample value.
- **Schema v2 measured across the shipper pod's whole life, 2026-09-07.** `hi - lo + 1 == n`
  on `report_seq` for one host: **417 consecutive reports, exactly one summary per window, no
  gaps and no duplicates.** The margin equality holds on **8 of 8** windows that carried traffic
  (398 idle ones satisfy it trivially and are not evidence); `carried_rows` matches the rows
  actually carried in **406 of 406** windows; and the startup blind spot is measured for the
  first time — seq 1, `window_start 04:21:30Z`, `partial_window: true`, `access_seen 0`, so the
  hole is real, bounded by the tick interval, and cost nothing on this pod.
- **Polaris 500s only on the create path.** 15 five-hundreds in 5 windows out of ~400, in two
  clusters matching the two notebook runs; every idle hour is clean. `active-issues.md` #15.
- **A gap in the report stream is usually the OrbStack VM suspending with the laptop**, not a
  stalled filter: 1,495 ticks against ~65.5h of uptime where `Interval_Sec 5` implies ~47,000.
  **No measurement over the report stream that spans a sleep can be read as elapsed time.**
- **The stdout-vs-file completeness measurement is still UNTAKEN, and the baseline is
  `0 == 0`.** 2026-09-09: `polaris-report-2026.09.09` holds **56 docs**, 30 most-recent are
  all summaries, `access_seen` **0 in every window on both sides**; `polaris-logs-*` does not
  exist in `_cat/indices` at all. What the baseline did settle: both report streams arrive,
  and the two releases' windows **share `window_start` on the same 30s wall-clock grid**
  (`04:53:00Z`…`04:57:00Z` present on both), so the comparison is takeable — it needs traffic,
  not repair.
- **An unordered LogsQL query was being printed as if it were sorted.** The readout's
  VictoriaLogs side had no `sort` pipe and used `tail -8`, i.e. 8 arbitrary rows of ~60,
  beside an OpenSearch side sorted desc. Invisible while everything was 0; with traffic it
  compares unrelated windows. Now `| sort by (window_start) desc | limit 12`. **Match by
  `window_start`, never by position.**
- **Stdout carries 0 of the 270 access-log lines the file carried.** 2026-09-09, matched windows:
  `05:07:00Z` file 226 seen / 99 kept, `05:07:30Z` file 44 / 33; stdout 0 in both. The question
  three plan revisions had to leave open is answered, and answered NO. It was takeable only while
  both releases ran.
- **`polaris-logs-2026.09.09`: 4,718 docs / 2.7 MB for ~270 requests, with `access_seen 0`.**
  Both figures at once are the finding: the chain works, recognition does not, so policy v3 keeps
  everything. ~17 stored documents per request on a tier whose purpose is >99% reduction.
- **`polaris-report-*` 56 -> 74 docs across the run** — the report stream stayed healthy
  throughout, so the zero on the stdout side is a real count, not a missing one.
- **Stdout and the log file carry the SAME access-log set: 265 == 265, and kept 126 == 126.**
  2026-09-09, one burst, both releases running, after the `multiline.parser cri -> docker, cri`
  fix. Per-window diffs (+15, -17, +2) sum to zero — boundary assignment, not loss. The earlier
  "270 vs 0" was measured through a filter that was not parsing and is void.
- **Root cause of the tier 2 fault: `multiline.parser cri` alone on the tail input.** With
  `docker, cri` the same files, same parser filter and same parser produce parsed records —
  4,314/4,314 on probe 5, and 4,403/4,403 post-fix documents in `polaris-logs-*`. Mechanism
  unknown. Tier 1 always used `docker, cri`, which is why only tier 2 was affected.
- **The `unwrap -> rename` byte delta is the tier 2 health check: 12.00 B/rec = failing
  (`app` added, neither rename fires), 5.00-7.00 = working.** Measured 6.97 after the fix.
- **There is no `k8s-logs` double write: ratio 1.000 (13,796 docs / 13,797 distinct `sequence`,
  30-minute window), busiest buckets one document each.** #16's "~2x inflated, dedup before any
  comparison" is disproved and the instruction is removed from `PLAN-opensearch-cutover` §7.
  Cause: OUTPUT 1 drops every record because `Id_Key sequence` is an integer and the plugin needs
  a string, so **tier 1 has no dedup at all and never had** (#18).
- **Tier 2 is a strict subset of tier 1, measured on sets rather than counts.** 2026-09-09, 10-minute
  window matched on `sequence`: tier 1 **4,627** distinct, tier 2 **4,483**, **0 in tier 2 and not
  in tier 1**, 144 in tier 1 only. The two tails agree about what Polaris wrote. This was
  *unmeasurable* before the `multiline.parser` fix — tier 2 carried no `sequence` field to match on.
- **THE GAP IS FULLY ACCOUNTED FOR: 288 tier1-only records against `access_counted` 288, exact.**
  Second run, 10-minute window: tier 1 **9,254** distinct, tier 2 **8,966**, 0 in tier 2 and not in
  tier 1, gap **288**. Every record tier 1 holds and tier 2 lacks is an access-log line policy v3
  *counted* instead of storing. **No residue, so no loss hiding in that column** — a dropped chunk
  would land there looking exactly like policy doing its job.
- **A free corroboration from the same pair of runs:** all three figures are exactly **2.000×** the
  first run's (4,627/4,483/144 -> 9,254/8,966/288) — a second burst of the same shape. It is the
  *distinct* counts that doubled, which **a double write cannot do**: duplicating records leaves the
  distinct-`sequence` count unchanged. Independent re-confirmation that `#16`'s double write does
  not happen, and that `sequence` is unique per record within a window.
- **The 144-record gap is predicted, not merely expected.** Policy v3 keeps every NON-access-log
  record, so the only records tier 1 can hold and tier 2 lack are access-log lines the policy
  *counted* instead of storing — i.e. exactly `access_counted`. From the 06:35 burst,
  `access_seen 265 − access_kept 126 = 139`, against a 144 gap in a different window: right
  magnitude, **not yet compared on one window**. `step8` now reads `access_counted` and does that
  comparison itself.

**Measured 2026-09-10 — the API status matrix, run `1789026666`** (`log-coverage/polaris_log_coverage_v2.ipynb`,
63 operations from the vendored OpenAPI documents, **286 (operation × status) cells**, boundary-aligned
30s phases). The first run that drives the WHOLE API surface rather than a hand-picked path set:

- **228 cells covered, 58 missed, 0 transport errors**, and correlation on error cells **235/235**.
  Eight statuses are unreachable by construction and are recorded as such — `429` (the rate limiter
  is a no-op on this build), `502`/`504` (nothing proxies Polaris; a port-forward is not a gateway),
  `503` (the only route is scaling Polaris, and HPA movement invalidates the run, `#8`), `5XX` (a
  spec placeholder, not a status), plus `304`/`406`/`419` needing client features this build lacks.
- **Gate 6 found exactly ONE real path with no `RESOURCE_PATTERNS` rule** across all 63 operations:
  `/api/catalog/v1/{cat}/transactions/commit`. Now classified `transaction` (2026-09-10). This gate
  had never had traffic on that endpoint before — **the coverage of the driver is part of the gate**.
- **`min_record_time` is `text` in `polaris-report-2026.09.10`**, the fault `SCHEMA-report.md`
  review #2 predicted, now measured. Fixed on both sides: the Lua omits the key when nil, and
  `logging/opensearch/polaris-report-template.json` types it `date`. Neither is retroactive. `#25`.
- **Four operations answer 500 to a malformed request** — `getToken`, `createNamespace`,
  `renameTable`, `renameView`, all `unhandled`. So `errors_5xx` is drivable through the API alone,
  which answers the standing "how do we provoke one" question above without cluster surgery. `#24`.
- **Gate 2 — the v3 feature — is VOID, not passing.** `last_write_bytes` did not appear on any table
  row in the window read, though the matrix drove `createTable`, `updateTable` and `commitTransaction`
  to 2xx. The gate read a window of zero-carry rows. **58/58 in `logging/scripts/test-schema-v3.lua`
  says the Lua does set the field** (2xx, size > 0, last-wins), so the next step is to re-drive one
  commit and query THAT window, not to change the filter. Until then v3 is unproven: every other
  gate tests plumbing that already worked in v2.
- **The guide's gate queries were the fault in at least one FAIL, and could not have passed in
  three.** `{"term": {"<text field>": ...}}` matches the analyser's output, so `__errors__` looked
  for `errors`, `catalog-role` for `catalog`+`role`, and `POST` for `post` — none can ever match. A
  gate that matches nothing reports zero and **passes**. Fixed in `GUIDE-schema-v3-testing.md`
  2026-09-10, with `.keyword` throughout and a rule that row-level gates pin `window_start` instead
  of sorting by time. The notebook had already diverged from the guide, which is how Gate 5 returned
  63 requests over 4 docs while the guide's own query for it returns nothing.
