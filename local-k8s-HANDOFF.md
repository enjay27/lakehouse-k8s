# local-k8s — Cluster Rebuild Handoff

**Written 2026-08-18.** Self-contained: everything needed to rebuild the OrbStack cluster
(`datahub-hynix`) without referring back to the `polaris-learning` session this came out of.

Scope: infrastructure only. The Polaris API-profiling work that motivated it stays in
`polaris-learning`; this document is the prerequisite.

---

## 1. Why the rebuild

Two independent latent faults, invisible until they collided:

**Fault 1 — the PostgreSQL chart values were never applied.**
`benchmarks-postgresql` is an **umbrella chart** (`Chart.yaml` declares `postgresql-ha` 16.3.2 as a
dependency). Helm passes values to a subchart **only** when nested under the subchart's name, plus
whatever is under `global:`. The values file had `postgresql:`, `pgpool:`, `service:`, `metrics:` and
`volumePermissions:` at the **top level**, so the subchart never saw them. Helm does not warn.

The cluster had been running on subchart defaults for months:

| Intended | Actually in effect |
|---|---|
| `max_connections = 200` | **100** |
| `shared_buffers = 384MB` | 128MB |
| `log_min_duration_statement = 1000` | -1 (off) |
| `persistence.size: 10Gi` | 8Gi |
| explicit 2Gi resources | `resourcesPreset: micro` |
| `disableLoadBalancingOnWrite: always` | `transaction` |
| `/dev/shm` emptyDir | not mounted (64MB default) |

**How it was detected:** compare a value against the *subchart default*. `pgpool.replicaCount: 3` in
the values with **1** pgpool pod running (default 1) proved the block was inert.
`postgresql.replicaCount: 3` matched only because 3 is *also* the default — a coincidence, not
evidence. Only the correctly-nested `postgresql-ha:` block at the bottom of the file (images +
LoadBalancer service) was ever live.

**Fault 2 — the custom `pgHbaConfiguration` is IPv4-only.**
It had `0.0.0.0/0` but no `::/0`. In `pg_hba.conf`, **`0.0.0.0/0` matches IPv4 connections only**.
OrbStack's pod network is IPv6 (`fd00::/8` ULAs), so repmgr's pod-to-pod connection is rejected:

```
FATAL: no pg_hba.conf entry for host "fd07:b51a:cc66:a::203", user "repmgr",
       database "repmgr", no encryption
```

Fault 2 never bit while Fault 1 was in force, because Bitnami's **default** pg_hba includes `::/0`.
Fixing the nesting activated the custom pg_hba for the first time, replication broke, and a standby
went into CrashLoopBackOff.

> **The general lesson worth keeping:** un-inerting a block of configuration that has never executed
> is a change, not a fix. Review it line by line against the defaults it replaces.

---

## 2. Before you reset — verify the images

**The one step that can turn this into a dead end.** Polaris's startup log carries Bitnami's notice:

> *Starting August 28th, 2025, only a limited subset of images/charts will remain available for free.
> Backup will be available **for some time** at the 'Bitnami Legacy' repository.*

Every PostgreSQL image in these values is `bitnamilegacy/*` — that time-limited archive. An OrbStack
cluster reset clears the image cache. If those tags have since been withdrawn you will have wiped a
working cluster you cannot rebuild.

```bash
for img in \
  bitnamilegacy/postgresql-repmgr:17.6.0-debian-12-r2 \
  bitnamilegacy/pgpool:4.6.3-debian-12-r0 \
  bitnamilegacy/os-shell:12-debian-12-r51 \
  apache/polaris:1.3.0-incubating ; do
    docker pull "$img" || echo "!! UNAVAILABLE: $img"
done

# insurance — a local tarball survives anything
docker save -o ~/rebuild-images.tar \
  bitnamilegacy/postgresql-repmgr:17.6.0-debian-12-r2 \
  bitnamilegacy/pgpool:4.6.3-debian-12-r0 \
  bitnamilegacy/os-shell:12-debian-12-r51 \
  apache/polaris:1.3.0-incubating
```

Also confirm the chart still resolves — `oci://registry-1.docker.io/bitnamicharts` is under the same
policy:

```bash
helm dependency update ./charts/benchmarks-postgresql
```

If anything is unavailable: **do not reset.** Migrating to the maintained `bitnami/*` images is a job
for a working cluster.

Finally, note that a full reset also deletes `benchmarks-minio`, `datahub-frontend-lb`,
`elasticsearch-master` and `benchmarks-fluent-bit` — all of which need reinstalling.

Helm release history lives in cluster Secrets and is lost on reset. Export first if you want it:

```bash
helm -n datahub-hynix get values benchmarks-postgresql > ~/pg-values-before.yaml
helm -n datahub-hynix get values benchmarks-polaris    > ~/polaris-values-before.yaml
```

---

## 3. Rebuild order

```bash
kubectl create namespace datahub-hynix
```

1. **MinIO** — Polaris needs both the `data-catalog-bucket` and the
   `benchmarks-minio-credentials` secret (`minio.existingSecret`) to exist at install time.
2. **PostgreSQL** (§4)
3. **Polaris** (§5)
4. DataHub / Elasticsearch / Fluent Bit, if still wanted.

---

## 4. PostgreSQL values — required changes

Use `postgres-values-FIXED.yaml` (delivered alongside this document). The four things that matter:

### 4.1 Nest everything under `postgresql-ha:`

```yaml
global:            # `global:` DOES propagate — leave it at the top level
  postgresql:
    username: polaris
    # ...

postgresql-ha:     # EVERYTHING else moves under here
  volumePermissions: { ... }
  service: { ... }
  metrics: { ... }
  postgresql: { ... }
  pgpool: { ... }
```

### 4.2 pg_hba must cover both address families

`replication` is a pseudo-database and is **not** matched by `all`, so it needs its own lines:

```yaml
postgresql-ha:
  postgresql:
    pgHbaConfiguration: |-
        local   all             all                                     scram-sha-256
        host    all             all             127.0.0.1/32            scram-sha-256
        host    all             all             ::1/128                 scram-sha-256
        host    all             all             0.0.0.0/0               scram-sha-256
        host    all             all             ::/0                    scram-sha-256
        host    repmgr          repmgr          0.0.0.0/0               scram-sha-256
        host    repmgr          repmgr          ::/0                    scram-sha-256
        host    replication     all             0.0.0.0/0               scram-sha-256
        host    replication     all             ::/0                    scram-sha-256
```

### 4.3 Mount a real `/dev/shm`

Kubernetes gives containers 64MB. PostgreSQL allocates dynamic shared memory there for parallel
query workers, and 64MB is exactly the condition reproduced in the shm-exhaustion test plan (DSM
allocation failure → client `08001`/`08003`/`08006`). The `postgresql-ha` chart has no `shmVolume`
key, so use the extra-volume hooks:

```yaml
postgresql-ha:
  postgresql:
    extraVolumes:
      - name: dshm
        emptyDir: { medium: Memory, sizeLimit: 1Gi }
    extraVolumeMounts:
      - name: dshm
        mountPath: /dev/shm
```

**This closes the OrbStack K8s leg of S5 in the shm-exhaustion test plan**, which was the outstanding
item in this project. Worth re-running S1 afterwards to confirm the failure no longer reproduces.

### 4.4 Set `persistence.size` now or never

`volumeClaimTemplates` are immutable once the StatefulSet exists. A fresh install is the only moment
`10Gi` can be set; changing it later makes `helm upgrade` fail.

### 4.5 Keep `repmgr` in the preload list

```yaml
postgresql-ha:
  postgresql:
    sharedPreloadLibraries: "pgaudit, repmgr"
```

> **Never** run a bare `ALTER SYSTEM SET shared_preload_libraries = '...'`. `ALTER SYSTEM` writes
> `postgresql.auto.conf`, which **overrides** `postgresql.conf` — it replaces, it does not append.
> Dropping `repmgr` leaves repmgrd unable to attach to its shared memory and silently disables
> automatic failover. If you want `pg_stat_statements`, add it to the chart key above as a complete
> list. `postgresql.auto.conf` also lives on each pod's PVC and does not replicate, so an
> `ALTER SYSTEM` fix has to be repeated per node.

---

## 5. Polaris values — required changes

### 5.1 Bootstrap credentials must match the test suite

`POLARIS_BOOTSTRAP_CREDENTIALS` is `REALM,client_id,client_secret`. It is currently **commented out**,
so the chart generates one. If it does not match `root_secret` in
`polaris-learning/src/config/local.yaml`, every notebook there fails at `root_token()` — an auth
error that looks nothing like a bootstrap problem.

```yaml
persistence:
  relationalJdbc:
    secret:
      bootstrapCredentials: "POLARIS,root,<root_secret from local.yaml>"
```

Or read back what was generated and update `local.yaml`:

```bash
kubectl -n datahub-hynix get secret polaris-persistence-secret \
  -o jsonpath='{.data.bootstrapCredentials}' | base64 -d; echo
```

### 5.2 Connection budget

Polaris's pool is willing to open more connections than PostgreSQL accepts:

| | |
|---|---|
| PostgreSQL `max_connections` | 200 per node (once §4 applies) |
| `max_wal_senders` | 10 |
| Pgpool `numInitChildren` × `maxPool` × replicas | 64 × 4 × 3 |
| Polaris `QUARKUS_DATASOURCE_JDBC_MAX_SIZE` | **300** per pod, HPA to 3 pods |

Lower it, or the profiling seed run will produce `FATAL: sorry, too many clients already`:

```yaml
- name: QUARKUS_DATASOURCE_JDBC_MAX_SIZE
  value: "150"
```

### 5.3 SQL logging (only when profiling)

The values pin the SQL logger to INFO under "Noise suppression". **Logger resolution is
most-specific-wins**, so setting the *package* has no effect — the class-level entry wins:

```yaml
logging:
  categories:
    org.apache.polaris.persistence.relational.jdbc.DatasourceOperations: DEBUG   # was INFO
```

Revert after the profiling run — it emits one line per SQL statement on every request.

---

## 6. Verify the values actually applied

**Do not skip this.** Its absence is what hid Fault 1 for months: a silent no-op is the failure mode.
Check values that **differ from the subchart defaults** — anything matching a default proves nothing.

```bash
NS=datahub-hynix

# 3, not default 1 → the nested pgpool block is live
kubectl -n $NS get deploy benchmarks-postgresql-postgresql-ha-pgpool -o jsonpath='{.spec.replicas}{"\n"}'

# 10Gi, not default 8Gi → the nested postgresql block is live
kubectl -n $NS get pvc | grep postgresql

# 200 / 384MB, not defaults 100 / 128MB → extendedConf is live
kubectl -n $NS exec benchmarks-postgresql-postgresql-ha-postgresql-0 -- \
  env PGUSER=postgres PGPASSWORD=polaris psql -c 'SHOW max_connections; SHOW shared_buffers;'

# 1G, not 64M → the /dev/shm emptyDir is live
kubectl -n $NS exec benchmarks-postgresql-postgresql-ha-postgresql-0 -- df -h /dev/shm

# 3 → both address families present in pg_hba
kubectl -n $NS exec benchmarks-postgresql-postgresql-ha-postgresql-0 -- \
  grep -c '::/0' /opt/bitnami/postgresql/conf/pg_hba.conf

# repmgr still preloaded → failover works
kubectl -n $NS exec benchmarks-postgresql-postgresql-ha-postgresql-0 -- \
  env PGUSER=postgres PGPASSWORD=polaris psql -c 'SHOW shared_preload_libraries;'

# all three nodes healthy, one primary
kubectl -n $NS exec benchmarks-postgresql-postgresql-ha-postgresql-0 -- \
  env PGUSER=repmgr PGPASSWORD=repmgr \
  repmgr -f /opt/bitnami/repmgr/conf/repmgr.conf cluster show
```

---

## 7. Operational gotchas (each cost time this session)

- **`kubectl exec ... repmgr ...` fails with `could not get current user name: Success`.** The
  Bitnami UID has no `/etc/passwd` entry, so libpq's `getpwuid()` fails. Pass a user explicitly:
  `env PGUSER=repmgr PGPASSWORD=repmgr repmgr ...`.
- **`PostgreSQL is not ready after 60 seconds` tells you nothing.** The Bitnami wrapper starts
  postgres with output redirected to a **file**, so the real error never reaches `kubectl logs`. Grab
  it during the crash window:
  `kubectl -n $NS exec $POD -- tail -100 /opt/bitnami/postgresql/logs/postgresql.log`
- **repmgrd logs `[<ts>] [ERROR] unable to write to shared memory` during pod startup.** Transient
  and expected — it starts before PostgreSQL is ready. Unrelated to `/dev/shm`: repmgrd uses
  PostgreSQL's shared memory via the `repmgr` preload library.
- **A StatefulSet RollingUpdate halts at the first pod that never becomes Ready.** A broken `-2`
  leaves `-0`/`-1` untouched and serving — check pod AGE to see how far a rollout actually got. This
  is why the earlier failure did not take the cluster down.
- **`helm -n $NS get values <release> --revision N`**, diffed across revisions, turns "what did I
  break" into a fact rather than a guess.
- **Pgpool-II, not PgBouncer.** The Bitnami `postgresql-ha` chart ships Pgpool-II. It load-balances
  SELECTs across all three replicas, so a PostgreSQL server log tailed from one pod misses
  statements. (`polaris-learning/CLAUDE.md` says PgBouncer — that is wrong and should be corrected.)
- **Only pgpool is a LoadBalancer.** Reaching PostgreSQL directly needs
  `kubectl -n $NS port-forward pod/benchmarks-postgresql-postgresql-ha-postgresql-0 5433:5432`.
- **Polaris management port is 8182**, not the 8282 the upstream docs default to. `/q/metrics` lives
  there.

---

## 8. Handing back to `polaris-learning`

Once §6 passes, the profiling suite is ready to run:

```bash
cd polaris-learning
mkdir -p capture
kubectl -n datahub-hynix logs -f deploy/benchmarks-polaris > capture/polaris.log &
python diagnostics/api-sql-profile/check_sql_logging.py     # expect "SQL DEBUG logging is WORKING"
```

Then `diagnostics/api-sql-profile/01_api_access_map.ipynb` — first with `RUN_SEED = False` to prove
the capture pipeline end to end, then `RUN_SEED = True` for the index audit.

Also worth updating after the rebuild:
`polaris-learning/CLAUDE.md` (PgBouncer → Pgpool-II) and `polaris-learning/MEMORY.md` (rebuild date,
and the fact that the pre-rebuild configuration table is now historical).
