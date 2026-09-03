# Active issues — check here before trusting a value or a runbook

Status vocabulary: **OPEN** (will bite you), **ON DISK, UNVERIFIED** (fixed in a
file, never proved against a running cluster), **RESOLVED-INSTRUCTIVE** (fixed,
kept because the failure mode recurs).

## Blocking the rebuild

**#1 — Polaris bootstrap credentials render EMPTY. OPEN.**
`polaris/values.yaml` sets `bootstrap.createSecret: true` while
`bootstrapCredentials` (line ~349) stays commented out. The template passes it
through `| quote`, so it emits `""` — an *empty* credential, not a generated one.
Polaris bootstraps with no usable root principal and the `polaris-learning` suite
cannot authenticate. `local-k8s-HANDOFF.md` §5.1 is wrong about this; the
correction is `RESET-AND-CLEAN-INSTALL.md` §2.3. Whatever is chosen must be
reconciled with `polaris-learning/src/config/local.yaml`.

**#2 — Image availability is a one-way gate. OPEN.**
A full OrbStack reset wipes the image cache. `postgresql/` and `spark/` pin
`bitnamilegacy/*` archive tags that upstream may withdraw; `kafka/`,
`schema-registry/` and `datahub/` pin **no image at all** and resolve to their
chart's default, which for Bitnami charts is now the paywalled `bitnami/*` path.
Run `RESET-AND-CLEAN-INSTALL.md` §1.2 (or `preflight-triage.sh`) and pull a local
tarball first. **If any image fails to resolve, do not reset.**

**#3 — Three different MinIO credential sets. OPEN, and one is a committed secret.**
`polaris/values.yaml` → `minioadmin/minioadmin`; `spark/values.yaml` line 29-30 →
`admin/bhEenDzTEAVPKbukhuY0tRY4WjpZXzh0` **in plaintext, committed**;
`minio/values.yaml` → `minio/minio`. Polaris and Argo both reference the
`benchmarks-minio-credentials` secret, so at most one of these inline sets can be
right. Violates CLAUDE.md *Zero Hardcoded Credentials*. Decide one set, move it to
`--set-string` / a gitignored overlay, and rotate the leaked Spark key.

**#4 — `postgresql/secret/polaris-persistence-secret.yaml` is stale and collides. OPEN.**
Its `jdbcUrl` still points at `postgres-postgresql:5432`, a service name from a
previous install, and the secret name duplicates the one the Polaris chart creates
itself. Applying both makes which one wins an ordering accident.

## Written, not proved

**#5 — `minio/` templates exist but have never been installed. ON DISK, UNVERIFIED.**
Written 2026-08-18 to close the "chart with no `templates/`" blocker; still
untracked in git and never rendered against a cluster. `helm template ./minio`
and a `--dry-run --debug` are the minimum before trusting the rebuild order.

**#6 — `postgresql/values.yaml` fixes are on disk, unapplied. ON DISK, UNVERIFIED.**
Nesting under `postgresql-ha:`, `persistence.size: 10Gi`, the `/dev/shm` emptyDir
and the dual-family `pg_hba` are all written. None has run. `persistence.size` is
**now-or-never** — a PVC cannot be grown in place after install.

**#7 — The Fluent Bit → VictoriaLogs switch is uncommitted. ON DISK, UNVERIFIED.**
`logging/fb-values.yaml` was changed from an Elasticsearch output to an HTTP
`jsonline` output against VictoriaLogs in namespace `logging`, and `_stream_fields`
moved from a `modify` filter into the ingest URI. Not committed, not deployed.
It also leaves an open question: `CLAUDE.md` used to describe a Docker Compose
**OpenSearch** as the log sink, and no compose file exists anywhere in this repo —
so either OpenSearch is now superseded by VictoriaLogs, or its compose file lives
outside version control. Settle this before writing either into the tech stack.

## Resolved, kept because they recur

**#F1 — An entire values block was inert for months. RESOLVED-INSTRUCTIVE.**
`postgresql/` is an umbrella chart. Helm passes values to a subchart only when
nested under the subchart's name — everything at the top level was silently
ignored, and the cluster ran on subchart defaults:

| intended | actually in effect |
|---|---|
| `max_connections = 200` | **100** |
| `shared_buffers = 384MB` | 128MB |
| `log_min_duration_statement = 1000` | -1 (off) |
| `persistence.size: 10Gi` | 8Gi |
| explicit 2Gi resources | `resourcesPreset: micro` |
| `disableLoadBalancingOnWrite: always` | `transaction` |
| `/dev/shm` emptyDir | not mounted (64MB default) |

Detected by comparing a value against the **subchart default**, not against the
values file: `pgpool.replicaCount: 3` with one pgpool pod running proved the block
was dead. `postgresql.replicaCount: 3` matched only because 3 is also the default —
a coincidence, not evidence. **Verify against defaults, never against intent.**

**#F2 — `0.0.0.0/0` does not match IPv6. RESOLVED-INSTRUCTIVE.**
The custom `pgHbaConfiguration` was IPv4-only; OrbStack's pod network is IPv6
(`fd00::/8`), so repmgr's pod-to-pod connection was rejected and a standby went
into CrashLoopBackOff. It never bit while #F1 was in force, because Bitnami's
*default* pg_hba includes `::/0`. **Un-inerting configuration that has never
executed is a change, not a fix** — review it line by line against the defaults it
replaces.

## Standing constraints

- **Resource footprint.** The full set (DataHub + prerequisites + Kafka + Spark +
  Airflow) needs >7GB RAM on the daemon node. Bring services up in the §4 order and
  stop where the host runs out rather than debugging phantom scheduling failures.
- **`ALTER SYSTEM SET shared_preload_libraries` replaces, it does not append.**
  Running it bare drops `repmgr` and silently disables automatic failover.
  `postgresql.auto.conf` lives on each pod's PVC and does not replicate.
- **`git status` hygiene.** `.gitignore` now covers `.idea`, `node_modules`,
  `postgresql-ha-*.tgz` and `.DS_Store` (added 2026-09-03). Nothing under
  `server/node_modules/` is tracked. Still check `git status` **before** `git add -A`,
  never after — chart tarballs and `helm get values` exports pulled as rebuild
  insurance are not covered by any pattern.
