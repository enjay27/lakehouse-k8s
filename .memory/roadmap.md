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

Polaris logging is the live thread. The design it is being built against is
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
