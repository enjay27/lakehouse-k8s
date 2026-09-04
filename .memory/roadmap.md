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
| 7 | `vmalert` + log→metric downsampling | spec §8. Nothing exists yet. |
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
