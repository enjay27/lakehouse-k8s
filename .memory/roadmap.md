# Roadmap — what is done, what is next

A line here needs a **number or a verified state**. Anything still hypothetical
belongs in [`active-issues.md`](active-issues.md); the story of how it was found
belongs in [`sessions/`](sessions/).

## Next — the cluster rebuild

The plan is written and approved in shape; **nothing has been torn down and
nothing has been installed.** `RESET-AND-CLEAN-INSTALL.md` is the procedure.

| # | step | gate | state |
|---|---|---|---|
| 0 | Decide the three open blockers | Polaris root secret, one MinIO credential set, the stale PG secret | **blocked on developer** — `active-issues.md` #1, #3, #4 |
| 1 | Pre-flight image audit | zero `UNAVAILABLE` in §1.2 / `preflight-triage.sh` | not run |
| 2 | Insurance | image tarball, chart tarballs, `helm get values` per release, PG + MinIO dumps | not run |
| 3 | Teardown | releases uninstalled, namespace deleted, full OrbStack K8s reset | not run |
| 4 | Reinstall, 12 steps in order | each row `Running` before the next starts | not run |
| 5 | Verification block | the seven `MUST show` assertions in §5 | not run |
| 6 | Documentation | `MEMORY.md` *Now*, this file, `CLAUDE.md` tech stack | this convention rewrite is step 6's prerequisite |

Reinstall order, because it is load-bearing and one-directional:
`minio → postgresql → polaris → datahub-prerequisites → kafka → schema-registry →
datahub → spark → airflow → argo → jupyter → fluent-bit`.

## Verification assertions worth keeping

These are the checks that would have caught #F1 years earlier. Each is a fact, not
an intention — run them after any PostgreSQL change:

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

## After the rebuild

Hand back to `polaris-learning` (HANDOFF §8): tail
`deploy/benchmarks-polaris` into `capture/polaris.log`, then
`check_sql_logging.py` should print *SQL DEBUG logging is WORKING*. Two
corrections to carry across: `polaris-learning/CLAUDE.md` says PgBouncer and must
say **Pgpool-II**, and its pre-rebuild configuration table becomes historical.
