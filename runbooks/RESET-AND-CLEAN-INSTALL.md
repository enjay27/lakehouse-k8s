# RESET CLUSTER — Full OrbStack Reset & Clean Install

**Prepared 2026-08-18** for `local-k8s` / namespace `datahub-hynix`.
Companion to `local-k8s-HANDOFF.md` — the handoff explains *why*; this is the *how*, with the
gaps between the handoff's assumptions and what is actually on disk closed out.

**Decisions taken (developer, this session):**

| Decision | Choice |
|---|---|
| Reset depth | **Full OrbStack Kubernetes reset** (image cache is wiped) |
| Reinstall set | **Everything in the repo** |
| Image versions | **Unchanged** — whatever each `values.yaml` already pins |
| MinIO chart | **Write templates for the local chart** |

**Status: PLAN ONLY. Nothing has been written to disk and nothing has been executed.**
Per `CLAUDE.md` Strict Plan-First Mode, §2 waits on your explicit approval.

---

## 0. Read this first — the shape of the risk

A full OrbStack reset destroys the local image cache. Every image has to be pulled again.
`HANDOFF.md` §2 already flags this for the four PostgreSQL/Polaris images, all of which sit in
Bitnami's time-limited `bitnamilegacy` archive. Reinstalling **everything** widens that exposure
considerably, because several charts in this repo **do not pin an image at all** and will resolve
to their chart's default — which for Bitnami charts is now the paywalled `bitnami/*` path:

| Chart | Image pinned in values? |
|---|---|
| postgresql, spark | yes — `bitnamilegacy/*` (archive, at risk) |
| polaris, minio, airflow, jupyter, fluent-bit | yes — non-Bitnami, low risk |
| **kafka** | **no** — resolves to Bitnami chart default |
| **schema-registry** | **no** — resolves to Bitnami chart default |
| **datahub / prerequisites** | **no** — prerequisites pulls Bitnami ES, MySQL, Kafka, ZK |
| argo | no — upstream `quay.io/argoproj/*`, low risk |

So the pre-flight in §1 is not a formality. It is the step that decides whether this reset is
recoverable. **If any image fails to resolve, stop and do not reset.**

Two other things a reset takes with it that are easy to forget:

- **Helm release history lives in cluster Secrets.** `helm get values --revision N` — the tool
  §7 of the handoff calls out as the way to turn "what did I break" into a fact — is gone
  afterwards. Export first (§1.3).
- **All PVCs.** PostgreSQL data, MinIO objects, Kafka logs, Jupyter user volumes, Airflow
  metadata. If anything in MinIO or PostgreSQL matters, dump it in §1.3.

---

## 1. Pre-flight — BLOCKING GATE

Nothing in this section mutates anything. Do all of it before touching the reset.

### 1.1 Confirm you are pointed at the right cluster

`CLAUDE.md` Cluster-Context Guard:

```bash
kubectl config current-context     # must print exactly: orbstack
```

If it prints anything else, stop.

### 1.2 Prove every image can still be pulled

> **Correction 2026-08-18.** The first version of this section had two bugs. It called
> `helm template` against repo-qualified charts (`bitnami/kafka`, `datahub/datahub`, …) **without
> adding the repos first**, and then hid the resulting errors with `2>/dev/null` — so
> `rebuild-image-list.txt` came out empty and the audit silently degraded to the `$PINNED` list
> alone. The image-name filter also excluded uppercase, which would have dropped
> `minio/minio:RELEASE.2024-...`. Both are fixed below.
>
> **If the pull loop reports UNAVAILABLE for images from more than one registry** — e.g. both
> `bitnamilegacy/*` and `apache/polaris` and `cr.fluentbit.io/*` — that is not an upstream
> withdrawal. Unrelated registries do not fail together. Run `preflight-triage.sh` (delivered
> alongside this document) before drawing any conclusion. A blanket failure is nearly always a
> stopped Docker daemon, a Docker Hub rate limit, or a network problem.

**Step 1 — add the chart repos.** Without this the render step below produces nothing:

```bash
helm repo add bitnami        https://charts.bitnami.com/bitnami
helm repo add datahub        https://helm.datahubproject.io/
helm repo add argo           https://argoproj.github.io/argo-helm
helm repo add apache-airflow https://airflow.apache.org
helm repo add jupyterhub     https://hub.jupyter.org/helm-chart/
helm repo add fluent         https://fluent.github.io/helm-charts
helm repo update
```

**Step 2 — discover the images the unpinned charts will actually use.** Render, don't guess.
Note `2>&1` on the render: a chart that fails to resolve must be loud, not silent.

```bash
NS=datahub-hynix
cd ~/hynix/local-k8s

for c in \
  "benchmarks-kafka        bitnami/kafka                 kafka/values.yaml" \
  "benchmarks-schema-registry bitnami/schema-registry    schema-registry/values.yaml" \
  "datahub-prerequisites   datahub/datahub-prerequisites datahub/prerequisites-values.yaml" \
  "datahub                 datahub/datahub               datahub/datahub-values.yaml" \
  "benchmarks-argo         argo/argo-workflows           argo/values.yaml" \
  "benchmarks-airflow      apache-airflow/airflow        airflow/values.yaml" \
  "benchmarks-jupyter      jupyterhub/jupyterhub         jupyter/values.yaml" \
  "benchmarks-fluent-bit   fluent/fluent-bit             releases/fluent-bit/values.yaml" \
  "benchmarks-spark        bitnami/spark                 spark/values.yaml" ; do
    set -- $c
    echo "=== $1 ==="
    helm template "$1" "$2" -f "$3" -n $NS 2>&1 \
      | grep -oE '^[[:space:]]*image:[[:space:]]*"?[^"]+' \
      | sed 's/.*image:[[:space:]]*//' | tr -d '"' | sort -u
done | tee ~/rebuild-image-list.txt

# Sanity check before trusting it — a near-empty file means the renders failed
grep -c ':' ~/rebuild-image-list.txt
```

**Step 3 — pull everything.** The pinned set from the handoff plus whatever the render turned up.
Errors are shown, not swallowed, so a failure says *why*:

```bash
PINNED="
bitnamilegacy/postgresql-repmgr:17.6.0-debian-12-r2
bitnamilegacy/pgpool:4.6.3-debian-12-r0
bitnamilegacy/os-shell:12-debian-12-r51
apache/polaris:1.3.0-incubating
minio/minio:RELEASE.2024-01-01T16-36-33Z
minio/mc:latest
bitnamilegacy/spark:3.5.3
apache/airflow:2.9.1
jupyter/pyspark-notebook:spark-3.5.0
cr.fluentbit.io/fluent/fluent-bit:3.2.2
"

# note: [A-Za-z] — tags carry uppercase, e.g. minio RELEASE.2024-01-01T16-36-33Z
for img in $PINNED $(grep -E '^[A-Za-z0-9][A-Za-z0-9./:@_-]+$' ~/rebuild-image-list.txt | sort -u); do
  if err=$(docker pull "$img" 2>&1 >/dev/null); then
    echo "ok           $img"
  else
    echo "!! FAILED    $img"
    echo "             $(echo "$err" | tail -1 | cut -c1-100)"
  fi
done
```

**Before acting on any failure, classify it.** The one-line reason printed above is the whole
signal:

| Reason contains | Meaning | Action |
|---|---|---|
| `manifest unknown` / `not found` | genuinely withdrawn | **REAL STOP** — do not reset |
| `unauthorized` / `authentication required` | paywall or not logged in | `docker login`; for `bitnami/*` this is the Aug-2025 policy |
| `toomanyrequests` | Docker Hub anonymous rate limit | wait for the window, or `docker login` |
| `dial tcp` / `no such host` / `timeout` | network or DNS | fix connectivity, re-run |
| `Cannot connect to the Docker daemon` | OrbStack is not running | start it, re-run |
| `no space left on device` | local disk | prune, re-run |

Only the first row is the condition HANDOFF §2 warns about. Every other row is a fixable local
problem that must not be mistaken for one.

> **`minio/mc:latest` is a floating tag.** It is the only unpinned tag you control directly.
> Resolve it to a digest now and pin it in `minio/values.yaml`, or a future reset silently gets a
> different `mc`:
> `docker inspect --format='{{index .RepoDigests 0}}' minio/mc:latest`

**Gate: if any line fails with `manifest unknown`, stop here.** Migrating off a withdrawn image is
a job for a cluster that still works.

**Gate: if images from more than one registry fail, the audit itself is invalid.** Run
`preflight-triage.sh`, fix the environment, and re-run this section from Step 1. Do not proceed on
an inconclusive audit, and equally do not abandon the rebuild on one — a failed control test tells
you nothing about the images either way.

### 1.3 Take the insurance

```bash
# Image tarball — survives the cache wipe regardless of what upstream does
docker save -o ~/rebuild-images.tar $PINNED

# Helm chart tarballs — the OCI Bitnami repo is under the same policy as the images
helm dependency update ./postgresql       # postgresql/charts/postgresql-ha-16.3.2.tgz already present
helm pull bitnami/kafka           -d ~/rebuild-charts/
helm pull bitnami/schema-registry -d ~/rebuild-charts/
helm pull bitnami/spark           -d ~/rebuild-charts/
helm pull datahub/datahub-prerequisites -d ~/rebuild-charts/
helm pull datahub/datahub         -d ~/rebuild-charts/

# Live values, per release — the only copy of what is actually running
mkdir -p ~/rebuild-state
for r in $(helm -n $NS list -q); do
  helm -n $NS get values "$r" > ~/rebuild-state/$r.values.yaml
done
kubectl -n $NS get all,pvc,secret,cm -o yaml > ~/rebuild-state/namespace-dump.yaml

# The generated Polaris bootstrap credential — see §2.3, you will need this
kubectl -n $NS get secret polaris-persistence-secret \
  -o jsonpath='{.data.bootstrapCredentials}' | base64 -d > ~/rebuild-state/polaris-bootstrap.txt; cat ~/rebuild-state/polaris-bootstrap.txt
```

### 1.4 Dump any data you care about

```bash
# PostgreSQL — polaris catalog metadata
kubectl -n $NS exec benchmarks-postgresql-postgresql-ha-postgresql-0 -- \
  env PGUSER=postgres PGPASSWORD=polaris pg_dumpall > ~/rebuild-state/pg-dumpall.sql

# MinIO — object data (adjust alias/bucket to what mc reports)
kubectl -n $NS port-forward svc/benchmarks-minio 9000:9000 &
mc alias set rebuild http://localhost:9000 minioadmin minioadmin
mc mirror rebuild/ ~/rebuild-state/minio/
kill %1
```

---

## 2. Configuration changes required before install — IMPACT PLAN

**This is the section that needs your approval.** These are the edits I would make to files on
disk. None are applied yet.

### 2.1 `minio/` — write the missing chart templates  *(BLOCKER)*

**Current state:** `minio/` contains only `Chart.yaml` and `values.yaml`. There is no
`templates/` directory and no dependency on an upstream chart. `helm install benchmarks-minio
./minio` renders **zero resources**. This is a hard blocker: HANDOFF §3 makes MinIO step 1 because
Polaris needs the bucket and the credentials secret to exist at install time, and `argo/values.yaml`
independently references `benchmarks-minio-credentials`.

**Proposed:** author `minio/templates/` against the existing `values.yaml` keys, which are already
written as though the templates exist (`mode`, `auth`, `persistence`, `buckets`, `policies`,
`postInstall`, `polaris.sts`, `metrics.serviceMonitor`):

| File | Purpose |
|---|---|
| `_helpers.tpl` | name/label helpers, matching the Polaris chart's conventions |
| `secret.yaml` | **`benchmarks-minio-credentials`** — root user/password, honouring `auth.existingSecret` |
| `statefulset.yaml` | standalone MinIO, `persistence.size`, probes, securityContext from values |
| `service.yaml` | LoadBalancer, ports 9000 / 9001 |
| `serviceaccount.yaml` | gated on `serviceAccount.create` |
| `job-postinstall.yaml` | `minio/mc` post-install hook: create `buckets`, apply `policies`, create `users` |
| `servicemonitor.yaml` | gated on `metrics.serviceMonitor.enabled` |
| `ingress.yaml`, `console-ingress.yaml` | gated on `ingress.enabled` (currently false) |
| `hpa.yaml` | gated on `autoscaling.enabled` (currently false) |

### 2.2 `minio/values.yaml` — three corrections

| Key | Now | Proposed | Why |
|---|---|---|---|
| `buckets` / `polaris.defaultBucket` | `user-catalog-bucket` | add **`data-catalog-bucket`** | `polaris/values.yaml` line 398 sets `warehouse: s3://data-catalog-bucket/`. Mismatch — Polaris writes to a bucket that is never created. |
| `buckets` | — | add **`argo-artifacts`** | `argo/values.yaml` artifact repository expects it. |
| `auth.rootUser` / `rootPassword` | `admin` / `""` | `minioadmin` / from env or `values-secret.yaml` | `polaris/values.yaml` authenticates as `minioadmin`/`minioadmin`; `spark/values.yaml` uses `admin` + a different key. Three components, three different credentials — they must agree. `CLAUDE.md` Zero Hardcoded Credentials means the password goes via `--set-string` from an env var, **not** into the committed file. |

### 2.3 `polaris/values.yaml` — bootstrap credentials must be set explicitly  *(BLOCKER)*

**Current state:** `persistence.relationalJdbc.createSecret: true`, but line 340
`bootstrapCredentials` is **commented out**. `templates/secret-persistence.yaml` renders it
unconditionally through `| quote`, so a nil value produces `bootstrapCredentials: ""` — an *empty*
credential, not a generated one. (HANDOFF §5.1 assumes the chart generates one; it does not.)
Polaris bootstrap fails, and `root_token()` in `polaris-learning` fails with an auth error that
looks nothing like a bootstrap problem.

**Proposed:** uncomment and set it to match `root_secret` in
`polaris-learning/src/config/local.yaml`, sourced as a secret (per Zero Hardcoded Credentials):

```yaml
persistence:
  relationalJdbc:
    secret:
      bootstrapCredentials: "POLARIS,root,<root_secret>"   # via --set-string, not committed
```

Use the value you captured in §1.3, or pick a new one and update `local.yaml` to match.

### 2.4 `polaris/values.yaml` — connection budget

| Key | Now | Proposed |
|---|---|---|
| `QUARKUS_DATASOURCE_JDBC_MAX_SIZE` (line 169) | `300` | `150` |

HANDOFF §5.2. 300 per pod × HPA to 3 pods, against `max_connections = 200` per node, produces
`FATAL: sorry, too many clients already` on the profiling seed run.

### 2.5 `polaris/values.yaml` — SQL DEBUG logging

Line 281 is **already** `DatasourceOperations: DEBUG` (uncommitted change). That is correct *for
the profiling run* and wrong as a resting state — it emits one line per SQL statement per request.
**Proposed:** leave it as-is through the rebuild so §5's `check_sql_logging.py` passes, and add a
note to `MEMORY.md` to revert it after profiling.

### 2.6 `postgresql/values.yaml` — `persistence.size` is now-or-never

**Current state:** line 225 is `size: 8Gi`, with a comment block at lines 70–74 explaining it was
deliberately left at the subchart default because `volumeClaimTemplates` are immutable on a live
StatefulSet.

**That reasoning inverts on a fresh install.** HANDOFF §4.4: a clean install is the only moment
`10Gi` can be set. **Proposed:** `size: 10Gi`, and rewrite the lines 60–80 comment block, which is
now written for an in-place upgrade that will never happen and would mislead the next reader.

Everything else in this file is already correct for the rebuild — nesting under `postgresql-ha:`,
dual-family `pgHbaConfiguration`, the `dshm` emptyDir, `sharedPreloadLibraries: "pgaudit, repmgr"`.
No change needed to any of those.

### 2.7 `postgresql/secret/polaris-persistence-secret.yaml` — stale and conflicting

**Current state:** hardcodes `jdbcUrl: jdbc:postgresql://postgres-postgresql:5432/polaris` — a
service name that does not exist; the live one is
`benchmarks-postgresql-postgresql-ha-pgpool:5432`. It also declares no `namespace`, and it creates
the **same secret name** the Polaris chart creates via `createSecret: true`. Whichever is applied
second wins, silently.

**Proposed:** delete this file, or move it to `postgresql/secret/_unused/`, and let the Polaris
chart own `polaris-persistence-secret`. It also carries a plaintext
`bootstrapCredentials: POLARIS,root,polaris-secret`, which `CLAUDE.md` forbids in a committed file.

### 2.8 `spark/values.yaml` — hardcoded credentials

Lines 25 and 30–31 contain a plaintext Polaris client credential and an S3 secret key. `CLAUDE.md`
Zero Hardcoded Credentials. **Proposed:** move both to `--set-string` from env, and align the S3
key with the MinIO credentials settled in §2.2. Note the Polaris credential is a *client* secret
that will not survive the rebuild anyway — it has to be reissued after Polaris bootstraps.

### 2.9 `.gitignore`

**Proposed:** add `values-secret.yaml` and `*.values-secret.yaml` so the secret overlay files
§2.2/§2.3/§2.8 rely on cannot be committed by accident.

---

## 3. Teardown

Only after §1 passes clean and §2 is approved and applied.

`CLAUDE.md` Destructive Commands Prohibited — each of these needs your explicit go-ahead at the
moment of execution, not just approval of this document.

```bash
NS=datahub-hynix
kubectl config current-context     # orbstack. Again. Right before the destructive step.

# 1. Uninstall releases cleanly first — leaves fewer orphaned PVs behind
for r in $(helm -n $NS list -q); do echo "helm -n $NS uninstall $r"; done   # review, then run

# 2. Namespace
kubectl delete namespace $NS

# 3. Full OrbStack Kubernetes reset
#    GUI: OrbStack → Settings → Kubernetes → Reset Kubernetes cluster
#    Verify the CLI equivalent for your OrbStack version before relying on it: `orb --help`
```

After the reset, confirm you have an empty cluster and that the context still resolves:

```bash
kubectl config current-context
kubectl get nodes
kubectl get ns
```

If the image cache is empty and §1.2 said everything was available, reload the tarball to skip the
re-pull entirely:

```bash
docker load -i ~/rebuild-images.tar
```

---

## 4. Reinstall — order matters

```bash
NS=datahub-hynix
kubectl create namespace $NS
cd ~/hynix/local-k8s
```

Dependency order. Each step has a gate — do not start the next until the previous is `Running`.

| # | Release | Chart | Gate before proceeding |
|---|---|---|---|
| 1 | `benchmarks-minio` | `./minio` (local, §2.1) | `data-catalog-bucket`, `argo-artifacts` exist; secret `benchmarks-minio-credentials` exists |
| 2 | `benchmarks-postgresql` | `./postgresql` | all 3 PG pods Ready, one primary — §5 |
| 3 | `benchmarks-polaris` | `./polaris` | `/q/health` green on mgmt port **8182** |
| 4 | `datahub-prerequisites` | `datahub/datahub-prerequisites` | ES + MySQL + Kafka Ready |
| 5 | `benchmarks-kafka` | `bitnami/kafka` | KRaft controller Ready, topics provisioned |
| 6 | `benchmarks-schema-registry` | `bitnami/schema-registry` | REST 8081 responds |
| 7 | `datahub` | `datahub/datahub` | GMS + frontend Ready |
| 8 | `benchmarks-spark` | `bitnami/spark` | master + workers Ready |
| 9 | `benchmarks-airflow` | `apache-airflow/airflow` | scheduler + webserver Ready |
| 10 | `benchmarks-argo` | `argo/argo-workflows` | controller Ready, artifact repo reachable |
| 11 | `benchmarks-jupyter` | `jupyterhub/jupyterhub` | hub Ready |
| 12 | `benchmarks-fluent-bit` | `fluent/fluent-bit` | DaemonSet 1/1, OpenSearch receiving |

Every command carries `-n datahub-hynix`, and every one gets a `--dry-run --debug` render first —
`CLAUDE.md` DoD item 2, since `helm lint` alone does not catch values/template errors:

```bash
# pattern, applied to each row above
helm upgrade --install benchmarks-minio ./minio -f minio/values.yaml -n $NS --dry-run --debug
helm upgrade --install benchmarks-minio ./minio -f minio/values.yaml -n $NS --wait --timeout 10m
```

For releases needing a secret overlay (§2.2 / §2.3 / §2.8):

```bash
helm upgrade --install benchmarks-polaris ./polaris -f polaris/values.yaml -n $NS \
  --set-string persistence.relationalJdbc.secret.bootstrapCredentials="POLARIS,root,${POLARIS_ROOT_SECRET}" \
  --wait --timeout 10m
```

**Timeout guard** (`CLAUDE.md`): PostgreSQL HA and Polaris routinely take several minutes.
A command is only hung if it produces **no new output for 30 seconds** — not because total runtime
exceeded 30 seconds.

**OpenSearch** is Docker Compose, not Kubernetes, and is untouched by a K8s reset. Its compose file
is not in this repo — confirm it is still up before step 12, since Fluent Bit routes to it:

```bash
docker-compose ps        # from wherever the OpenSearch compose file lives
```

---

## 5. Verification — the step whose absence hid Fault 1 for months

HANDOFF §6, verbatim, plus the new checks this rebuild introduces. **Check values that differ from
the subchart defaults.** Anything matching a default proves nothing.

```bash
NS=datahub-hynix

# --- from HANDOFF §6 ---
# 3, not default 1 → the nested pgpool block is live
kubectl -n $NS get deploy benchmarks-postgresql-postgresql-ha-pgpool -o jsonpath='{.spec.replicas}{"\n"}'

# 10Gi, not 8Gi → §2.6 applied AND the nested postgresql block is live
kubectl -n $NS get pvc | grep postgresql

# 200 / 384MB, not 100 / 128MB → extendedConf is live
kubectl -n $NS exec benchmarks-postgresql-postgresql-ha-postgresql-0 -- \
  env PGUSER=postgres PGPASSWORD=polaris psql -c 'SHOW max_connections; SHOW shared_buffers;'

# 1G, not 64M → the /dev/shm emptyDir is live. Closes the OrbStack K8s leg of S5.
kubectl -n $NS exec benchmarks-postgresql-postgresql-ha-postgresql-0 -- df -h /dev/shm

# 3 → both address families present in pg_hba
kubectl -n $NS exec benchmarks-postgresql-postgresql-ha-postgresql-0 -- \
  grep -c '::/0' /opt/bitnami/postgresql/conf/pg_hba.conf

# repmgr still preloaded → automatic failover works
kubectl -n $NS exec benchmarks-postgresql-postgresql-ha-postgresql-0 -- \
  env PGUSER=postgres PGPASSWORD=polaris psql -c 'SHOW shared_preload_libraries;'

# all three nodes healthy, exactly one primary
kubectl -n $NS exec benchmarks-postgresql-postgresql-ha-postgresql-0 -- \
  env PGUSER=repmgr PGPASSWORD=repmgr \
  repmgr -f /opt/bitnami/repmgr/conf/repmgr.conf cluster show

# --- new, for this rebuild ---
# bootstrapCredentials non-empty → §2.3 applied
kubectl -n $NS get secret polaris-persistence-secret \
  -o jsonpath='{.data.bootstrapCredentials}' | base64 -d; echo

# 150, not 300 → §2.4 applied
kubectl -n $NS get deploy benchmarks-polaris \
  -o jsonpath='{range .spec.template.spec.containers[0].env[?(@.name=="QUARKUS_DATASOURCE_JDBC_MAX_SIZE")]}{.value}{"\n"}{end}'

# both buckets present → §2.2 applied
kubectl -n $NS port-forward svc/benchmarks-minio 9000:9000 &
mc alias set local http://localhost:9000 minioadmin "$MINIO_ROOT_PASSWORD" && mc ls local/

# Polaris management port is 8182, NOT the 8282 upstream docs default to
kubectl -n $NS port-forward svc/benchmarks-polaris-mgmt 8182:8182 &
curl -s localhost:8182/q/health | head -20

# nothing landed outside the namespace
helm list -A
```

`CLAUDE.md` DoD item 1: Compose `opensearch` and all `datahub-hynix` pods stable and `Running`.

---

## 6. Gotchas that will otherwise cost you an hour each

From HANDOFF §7, kept here so this document stands alone:

- **`kubectl exec ... repmgr ...` → `could not get current user name: Success`.** The Bitnami UID
  has no `/etc/passwd` entry, so libpq's `getpwuid()` fails. Always
  `env PGUSER=repmgr PGPASSWORD=repmgr repmgr ...`.
- **`PostgreSQL is not ready after 60 seconds` tells you nothing.** The Bitnami wrapper redirects
  postgres output to a file. Grab the real error during the crash window:
  `kubectl -n $NS exec $POD -- tail -100 /opt/bitnami/postgresql/logs/postgresql.log`
- **repmgrd `unable to write to shared memory` at startup** is transient and expected — it starts
  before PostgreSQL is ready. Unrelated to `/dev/shm`.
- **A StatefulSet RollingUpdate halts at the first pod that never becomes Ready.** Check pod AGE to
  see how far a rollout actually got.
- **Pgpool-II, not PgBouncer.** It load-balances SELECTs across all three replicas, so a server log
  tailed from one pod misses statements. (`CLAUDE.md` in this repo also says PgBouncer — that is
  wrong; see §7.)
- **Only pgpool is a LoadBalancer.** Direct PostgreSQL access needs
  `kubectl -n $NS port-forward pod/benchmarks-postgresql-postgresql-ha-postgresql-0 5433:5432`.
- **`ALTER SYSTEM SET shared_preload_libraries` replaces, it does not append.** Never run it bare —
  dropping `repmgr` silently disables automatic failover, and `postgresql.auto.conf` lives on each
  pod's PVC and does not replicate.

---

## 7. Documentation to update once §5 passes

`CLAUDE.md` DoD item 3 and the workflow-control skill's Topology Handoff step:

- **`MEMORY.md`** — rebuild date 2026-08-18; DataHub/prerequisites move from "UNINSTALLED" to
  installed; note the `/dev/shm` fix closes the OrbStack K8s leg of S5 in
  `shm-exhaustion-orbstack-leg-runbook.md`; note SQL DEBUG logging is temporarily on.
- **`CLAUDE.md`** — PgBouncer → **Pgpool-II** in the PostgreSQL HA line; DataHub and prerequisites
  are no longer "Currently UNINSTALLED"; add MinIO, Kafka, Spark, Airflow, Argo, Jupyter,
  Schema Registry to the tech stack, which currently omits them.
- **`polaris-learning/CLAUDE.md`** — PgBouncer → Pgpool-II.
- **`polaris-learning/MEMORY.md`** — rebuild date; the pre-rebuild configuration table is now
  historical.
- **`shm-exhaustion-orbstack-leg-runbook.md`** — re-run S1 to confirm the failure no longer
  reproduces, and record the result.

Then hand back to `polaris-learning` per HANDOFF §8:

```bash
cd polaris-learning
mkdir -p capture
kubectl -n datahub-hynix logs -f deploy/benchmarks-polaris > capture/polaris.log &
python diagnostics/api-sql-profile/check_sql_logging.py     # expect "SQL DEBUG logging is WORKING"
```

---

## Approval checklist

- [ ] §1.2 image audit ran clean — zero `UNAVAILABLE`
- [ ] §1.3 tarball, chart pulls, and live values exported
- [ ] §1.4 PostgreSQL and MinIO data dumped (or confirmed disposable)
- [ ] §2 config changes reviewed and approved for me to apply
- [ ] §2.2 MinIO credentials decided — one set, agreed across Polaris / Spark / Argo
- [ ] §2.3 Polaris root secret decided and reconciled with `polaris-learning/src/config/local.yaml`
- [ ] §3 teardown explicitly authorised at the moment of execution
