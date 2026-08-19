# Local Cluster Rebuild — Checklist

Wipe and reinstall PostgreSQL-HA + Polaris on the local OrbStack cluster, `datahub-hynix`.

Written 2026-08-18 after a repair attempt failed. **LOCAL ONLY.** Nothing here goes near the company
DEV/PROD clusters.

---

## Why rebuild rather than repair

The cluster had two independent latent faults that only became visible together:

1. `benchmarks-postgresql` is an **umbrella chart**, and its values were not nested under
   `postgresql-ha:`. Almost the entire tuning block had been inert for months — the cluster ran on
   subchart defaults.
2. The custom `pgHbaConfiguration` was **IPv4-only** (`0.0.0.0/0`, no `::/0`). OrbStack's pod network
   is IPv6, so the moment fault 1 was fixed and the pg_hba became live, repmgr could no longer reach
   the primary and a standby went into CrashLoopBackOff.

Fixing (1) exposed (2). Rebuilding gets both right from the start and removes months of unknown
drift, at the cost of the metastore contents — which were empty anyway (`listCatalogs` returned `[]`).

---

## 0. Capture anything worth keeping

The metastore was empty, so this is short — but check rather than assume.

```bash
NS=datahub-hynix

# Anything in the catalog?
psql -h 192.168.139.2 -p 5432 -U polaris -d polaris \
  -c 'SELECT count(*) FROM polaris_schema.entities'

# Anything in object storage?
mc ls --recursive localminio/data-catalog-bucket | head -50
mc du localminio/data-catalog-bucket

# Record what was ACTUALLY in effect, for the record
kubectl -n $NS exec benchmarks-postgresql-postgresql-ha-postgresql-0 -- \
  env PGUSER=postgres PGPASSWORD=polaris psql -Atc \
  "SELECT name||' = '||setting FROM pg_settings
   WHERE name IN ('max_connections','shared_buffers','shared_preload_libraries',
                  'log_min_duration_statement','work_mem')" | tee /tmp/pg-settings-before.txt

helm -n $NS get values benchmarks-postgresql > /tmp/pg-values-before.yaml
helm -n $NS get values benchmarks-polaris     > /tmp/polaris-values-before.yaml
```

---

## 1. Wipe

### Option A — reset the whole OrbStack cluster (simplest)

Skips every cleanup step below: no PVCs to chase, no lingering secrets, no uninstall ordering, and
no leftover state that a selective uninstall might miss. **But it deletes everything in the cluster,
not just Polaris and PostgreSQL.** From `kubectl get all`, that also means:

- `benchmarks-minio` — and the `data-catalog-bucket` contents
- `datahub-frontend-lb`, the `datahub-system-update` jobs
- `elasticsearch-master` (DataHub's search backend)
- `benchmarks-fluent-bit`

All of those need reinstalling afterwards. If DataHub/Elasticsearch matter, Option B is less work.

> ### ⚠ VERIFY THE IMAGES STILL PULL FIRST
>
> This is the one step that can turn a rebuild into a dead end. Polaris's own startup log carries
> Bitnami's notice:
>
> > *Starting August 28th, 2025, only a limited subset of images/charts will remain available for
> > free. Backup will be available **for some time** at the 'Bitnami Legacy' repository.*
>
> Every PostgreSQL image in these values comes from `bitnamilegacy/*`, which is that time-limited
> archive. A cluster reset clears the image cache — so if those tags have since been pulled, you
> will have wiped a working cluster you cannot rebuild.
>
> **Pull and save them BEFORE resetting:**
>
> ```bash
> for img in \
>   bitnamilegacy/postgresql-repmgr:17.6.0-debian-12-r2 \
>   bitnamilegacy/pgpool:4.6.3-debian-12-r0 \
>   bitnamilegacy/os-shell:12-debian-12-r51 \
>   apache/polaris:1.3.0-incubating ; do
>     docker pull "$img" || echo "!! UNAVAILABLE: $img"
> done
>
> # insurance — a local tarball survives anything
> docker save -o /tmp/rebuild-images.tar \
>   bitnamilegacy/postgresql-repmgr:17.6.0-debian-12-r2 \
>   bitnamilegacy/pgpool:4.6.3-debian-12-r0 \
>   bitnamilegacy/os-shell:12-debian-12-r51 \
>   apache/polaris:1.3.0-incubating
> ```
>
> If any print `UNAVAILABLE`, **stop** — repair the existing cluster instead, or move to the
> maintained `bitnami/*` images (different tags, and worth doing on a working cluster rather than a
> wiped one). Also confirm the Helm chart tarballs are cached or reachable: the chart repo is
> `oci://registry-1.docker.io/bitnamicharts`, subject to the same policy.

Also confirm these live on disk outside the cluster and will survive:

```bash
ls charts/                      # the umbrella charts themselves
ls *values*.yaml                # every values file
helm -n $NS get values benchmarks-postgresql > /tmp/pg-values-before.yaml
helm -n $NS get values benchmarks-polaris    > /tmp/polaris-values-before.yaml
```

Helm release history lives in cluster Secrets, so `helm history` is gone after a reset. Export
anything you want to diff against later.

Then reset Kubernetes in OrbStack, and recreate the namespace:

```bash
kubectl create namespace datahub-hynix
```

**Reinstall order** — MinIO first, since Polaris needs both the bucket and the credentials secret it
references (`minio.existingSecret: benchmarks-minio-credentials`) at install time:

1. MinIO → create `data-catalog-bucket` → create `benchmarks-minio-credentials`
2. PostgreSQL (§2)
3. Polaris (§3)
4. DataHub / Elasticsearch / Fluent Bit, if you still want them

### Option B — uninstall just the two releases

More steps, but leaves MinIO, DataHub and Elasticsearch alone.

```bash
helm -n $NS uninstall benchmarks-polaris
helm -n $NS uninstall benchmarks-postgresql
```

#### ⚠ PVCs SURVIVE `helm uninstall`

StatefulSet volumeClaimTemplates create PVCs that Helm does not own and will not delete. Leaving
them means the "fresh" install adopts the old data directories — exactly the half-state you are
trying to escape.

```bash
kubectl -n $NS get pvc
kubectl -n $NS delete pvc -l app.kubernetes.io/instance=benchmarks-postgresql
kubectl -n $NS get pvc      # must show none for postgresql
```

#### ⚠ Secrets survive too, and two of them matter

```bash
kubectl -n $NS get secret | grep -E 'polaris|postgres'

# Polaris chart creates this when persistence.relationalJdbc.createSecret=true.
# If it lingers, the reinstall may fail or silently reuse stale credentials.
kubectl -n $NS delete secret polaris-persistence-secret --ignore-not-found

# Created by a Helm pre-install hook and deliberately NOT regenerated if present.
# Delete it only if you want fresh signing keys — every existing token dies with it.
kubectl -n $NS delete secret polaris-rsa-key-pair-secret --ignore-not-found
```

#### Object storage

Polaris catalogs point at `s3://data-catalog-bucket/`. A fresh metastore with old objects still
present leaves orphaned metadata that nothing references — and on this build purge already orphans
files (issue #379), so it will not clean itself up later.

```bash
mc rm --recursive --force localminio/data-catalog-bucket/
```

---

## 2. Reinstall PostgreSQL

Use `postgres-values-FIXED.yaml`. Two things it gets right that the old file did not:

- everything nested under **`postgresql-ha:`**
- pg_hba covers **both address families**, including a `replication` line for each (`replication` is
  a pseudo-database and is NOT matched by `all`)

**On a fresh install you can now set `persistence.size: 10Gi`** — the volumeClaimTemplates
immutability that blocked it before only applies to an existing StatefulSet. Do it now or never.

```bash
helm -n $NS install benchmarks-postgresql ./charts/benchmarks-postgresql \
  -f postgres-values-FIXED.yaml

kubectl -n $NS rollout status statefulset/benchmarks-postgresql-postgresql-ha-postgresql --timeout=10m
```

### ⚠ VERIFY THE VALUES ACTUALLY APPLIED

This is the step whose absence hid the umbrella-chart bug for months. **A silent no-op is the
failure mode here**, so check values that differ from the subchart defaults:

```bash
# 3, not the default 1 → proves the nested pgpool block is live
kubectl -n $NS get deploy benchmarks-postgresql-postgresql-ha-pgpool -o jsonpath='{.spec.replicas}{"\n"}'

# 10Gi, not the default 8Gi → proves the nested postgresql block is live
kubectl -n $NS get pvc | grep postgresql

# 200/384MB, not the defaults 100/128MB → proves extendedConf is live
kubectl -n $NS exec benchmarks-postgresql-postgresql-ha-postgresql-0 -- \
  env PGUSER=postgres PGPASSWORD=polaris psql -c 'SHOW max_connections; SHOW shared_buffers;'

# 1G, not 64M → proves the /dev/shm emptyDir is live
kubectl -n $NS exec benchmarks-postgresql-postgresql-ha-postgresql-0 -- df -h /dev/shm

# both families present
kubectl -n $NS exec benchmarks-postgresql-postgresql-ha-postgresql-0 -- \
  grep -c '::/0' /opt/bitnami/postgresql/conf/pg_hba.conf     # expect 3

# repmgr still preloaded → failover works
kubectl -n $NS exec benchmarks-postgresql-postgresql-ha-postgresql-0 -- \
  env PGUSER=postgres PGPASSWORD=polaris psql -c 'SHOW shared_preload_libraries;'
```

**Do not proceed until all three nodes are Ready and replication is healthy.** Note `PGUSER` — without
it, `kubectl exec` fails with `could not get current user name: Success`, because the Bitnami UID has
no `/etc/passwd` entry.

```bash
kubectl -n $NS exec benchmarks-postgresql-postgresql-ha-postgresql-0 -- \
  env PGUSER=repmgr PGPASSWORD=repmgr \
  repmgr -f /opt/bitnami/repmgr/conf/repmgr.conf cluster show
```

---

## 3. Reinstall Polaris

### ⚠ The root secret must match `src/config/local.yaml`

Polaris bootstraps from `POLARIS_BOOTSTRAP_CREDENTIALS` in the format `REALM,client_id,client_secret`.
In the current values that line is **commented out**, so the chart generates one. If the generated
secret does not match `root_secret` in `src/config/local.yaml`, every notebook in this repo fails at
`root_token()` — an authentication error that looks nothing like a bootstrap problem.

Set it explicitly to the value already in `local.yaml`:

```yaml
persistence:
  relationalJdbc:
    createSecret: true
    secret:
      bootstrapCredentials: "POLARIS,root,<the root_secret from local.yaml>"
```

Or read back what was generated and update `local.yaml` to match:

```bash
kubectl -n $NS get secret polaris-persistence-secret \
  -o jsonpath='{.data.bootstrapCredentials}' | base64 -d; echo
```

### Two changes worth making at the same time

**Enable the SQL logger** — otherwise the profiling notebook has nothing to read. The chart pins it
to INFO under "Noise suppression"; logger resolution is most-specific-wins, so setting the *package*
does nothing:

```yaml
logging:
  categories:
    org.apache.polaris.persistence.relational.jdbc.DatasourceOperations: DEBUG   # was INFO
```

Revert this after the profiling run — it emits one line per statement.

**Fix the connection budget.** Polaris's pool is willing to open more connections than PostgreSQL
accepts, and the 1,000-user seed is what will expose it as
`FATAL: sorry, too many clients already`:

```yaml
- name: QUARKUS_DATASOURCE_JDBC_MAX_SIZE
  value: "150"          # was 300, against max_connections=200 across an HPA of up to 3 pods
```

```bash
helm -n $NS install benchmarks-polaris ./charts/benchmarks-polaris -f polaris-values.yaml
kubectl -n $NS rollout status deploy/benchmarks-polaris --timeout=5m
```

---

## 4. Verify end to end

```bash
# schema created by bootstrap
psql -h 192.168.139.2 -p 5432 -U polaris -d polaris \
  -c "\dt polaris_schema.*"        # entities, grant_records, principal_authentication_data,
                                   # policy_mapping_record, version  (+ events, from the
                                   # persistence event listener — expected, not drift)

# root token works → local.yaml and the bootstrap credentials agree
python -c "
import sys; sys.path.insert(0,'src')
from polaris_test_utils import init_env, root_token
init_env('local'); print('token OK:', bool(root_token()))"

# SQL DEBUG logging is live
mkdir -p capture
kubectl -n $NS logs -f deploy/benchmarks-polaris > capture/polaris.log &
python diagnostics/api-sql-profile/check_sql_logging.py
```

`check_sql_logging.py` should now report **`SQL DEBUG logging is WORKING`**. That is the green light
for `01_api_access_map.ipynb`.

---

## 5. Then, and only then, the profiling work

1. `01_api_access_map.ipynb` with `RUN_SEED = False` — the API→table mapping needs no data, and it
   confirms the whole capture pipeline works before committing to a 30-minute seed.
2. Re-run with `RUN_SEED = True` for the index audit. A fresh cluster is actually the ideal starting
   point: a clean baseline, then a known 16k-entity / 25k-grant fixture on top.
3. `TEARDOWN_SEED = True`, then revert the Polaris log level.

---

## Post-rebuild: update the repo

- `src/config/local.yaml` — confirm `root_secret`, `postgres_password`, MinIO keys still match.
- `CLAUDE.md` — it says "PostgreSQL HA (via **PgBouncer** pool)". It is **Pgpool-II**.
- `diagnostics/api-sql-profile/README.md` — fill in the "Result" section after the first live run.
- `MEMORY.md` — record the rebuild date and what changed, so the next session does not re-derive it.
