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
| 1 | Decide the shape: **shared-PVC file tail** (spec as written) vs **second OUTPUT on the existing DaemonSet** | `active-issues.md` #6. Everything below branches on this, and only the file path can carry the access-log parser and the Lua dedup filter. |
| 2 | Turn on the three switches the file path needs — `logging.file.enabled`, a PVC that actually exists, `quarkus.http.access-log.enabled` | `active-issues.md` #5. Until all three are on, `logging/fb-values.yaml` ships an empty file and VictoriaLogs stays at zero Polaris records. |
| 3 | Harden the shipper: tail `DB` + `Skip_Long_Lines On`, `custom_parsers.conf` loaded, filesystem buffering, `_stream_fields` cut to `app,level` | restart-replay, a tail that stops on a long stack trace, and stream cardinality are each a silent data fault, not an error. |
| 4 | Harden VictoriaLogs: `retention.maxDiskSpaceUsageBytes`, right-size 50Gi/4Gi to this node, decide `LoadBalancer` vs `ClusterIP` on 9428 | `active-issues.md` #7. 9428 is unauthenticated ingest **and** query, and `persistence.size` is now-or-never. |
| 5 | Rotate the OpenSearch password out of `fluent-bit/values.yaml`, and the MinIO keys out of `polaris/values.yaml:408` | `active-issues.md` #4. A committed credential stays leaked after the file is edited. |
| 6 | Build the access-log parser + the 24h Lua table dedup | spec §4.1–4.2 — the reason the file path exists at all. Blocked on 1 and 2. |
| 7 | Reconcile the repo against the live cluster — `helm get values` per release, diffed | `active-issues.md` #1. The rebuild's fixes live in the releases; the repo is not yet evidence of anything. |
| 8 | `vmalert` + log→metric downsampling | spec §8. Nothing exists yet; worth doing only once 1–6 land. |
| 9 | Hand back to `polaris-learning` | The platform exists to serve that suite; see below. |

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
