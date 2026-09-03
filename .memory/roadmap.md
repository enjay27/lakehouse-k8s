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

| # | step | why it is next |
|---|---|---|
| 1 | Reconcile the repo against the live cluster — `helm get values` per release, diffed against each `values.yaml` | `active-issues.md` #1. The rebuild's fixes live in the releases; the repo is not yet evidence of anything. |
| 2 | Rotate the MinIO key at `spark/values.yaml:30` and pin images in `kafka/` / `schema-registry/` / `datahub/` | A committed plaintext key stays leaked after the cluster stops using it, and an unpinned image is still unpinned next install. |
| 3 | Settle which sink the Fluent Bit DaemonSet ships to, then write it into `CLAUDE.md` | `active-issues.md` #2 — one `kubectl get cm` answers it. |
| 4 | Hand back to `polaris-learning` | The platform exists to serve that suite; see below. |

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
