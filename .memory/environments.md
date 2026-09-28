# Environments — read before running anything

Merged 2026-09-29 from `environments-platform.md` and `environments-catalog.md`. Facts marked
*measured* were read off the cluster that day.

## The platform: one cluster

A personal OrbStack single-node Kubernetes on Kade's MacBook. No shared company cluster is reachable
from this repo and none must ever be targeted from it. That makes destructive commands *permissible*
here. It does not make them free: the PVCs hold the only copy of the Polaris metastore and the MinIO
warehouse.

| | value | guard |
|---|---|---|
| kubectl context | `orbstack` | `kubectl config current-context` before **every** mutating command; halt on anything else |
| namespace | `datahub-hynix` | every mutation carries `-n datahub-hynix` explicitly. The namespace flag alone is not a guard: against another context it is a deployment into someone else's cluster |
| `logging` namespace | exists, **empty** (*measured*) | nothing belongs there since VictoriaLogs was removed 2026-09-18 |

## The suite: three environments that must not be conflated

Selected with `init_env(<env>)`; settings and secrets are completely different per environment.

1. **`local`** — the OrbStack node. Full suite, plus the destructive utilities in `notebooks/admin/`.
   `src/config/local.yaml` (gitignored). **The default.**
2. **`dev`** — shared company DEV. Functional / integration suites only. **Never** destructive
   teardown: it deletes other users' data.
3. **`prod`** — shared company PROD. **Availability tests only.**

Enforcement: the module default is `local`; mutating notebooks call `require_not_prod(...)`;
`notebooks/admin/polaris_clean_all.ipynb` is hardcoded to localhost with an `assert` host guard
**on purpose**. Do not port it onto `init_env`.

## Reaching things (local)

- **LoadBalancer Services** (*measured*): `benchmarks-minio` (9000, console 9001),
  `benchmarks-polaris` (8181), `benchmarks-polaris-mgmt` (**8182**, not the upstream 8282; `/q/health`,
  `/q/metrics`), `benchmarks-postgresql-postgresql-ha-pgpool` (5432).
- **Pgpool-II, not PgBouncer.** It load-balances SELECTs across all three PostgreSQL replicas, so a
  server log tailed from one pod misses statements. A single replica directly:
  `kubectl -n datahub-hynix port-forward pod/benchmarks-postgresql-postgresql-ha-postgresql-0 5433:5432`.
- **OpenSearch 3.5.0 runs in Docker** (`opensearch-node`, published `0.0.0.0:9200`), with
  `opensearch-dashboards` on 5601. It is outside the cluster and outside this repo, so it survives a
  cluster reset. Pods reach it at **`192.168.194.1:9200`** on the ordinary pod network (no
  `hostNetwork`). Being 3.x, mapping types are gone.
- **Fluent Bit is one release**, DaemonSet `benchmarks-fluent-bit`: chart `fluent-bit-0.57.6`, release
  revision 22 (*measured*), running image **`fluent-bit:5.1.1`**, one container. `appVersion` is the
  chart's field, not the image: read images off the DaemonSet. The image has **no `curl`**; probe
  from a throwaway `curlimages/curl` pod.
- **PVCs** (*measured*): `benchmarks-minio-data` 5Gi, `data-benchmarks-postgresql-postgresql-ha-postgresql-{0,1,2}`
  8Gi each, `polaris-logs-pvc` 5Gi (created by `kubectl apply -f logging/k8s/polaris-logs-pvc.yaml`
  **before** the Polaris release, which uses `existingClaim`).

## Secrets

Never in a committed file. Pass with `--set-string` from an environment variable or a gitignored
overlay; the suite reads them from env vars through `init_env`. The known violations are in
`active-issues/platform.md` (`#4` OpenSearch password in `releases/fluent-bit/values.yaml`, `#9`
database password in the live release) and `active-issues/catalog.md` (a principal secret in `03_api_index_matrix.ipynb` output).

## Cowork sessions

A Cowork session has **no** `kubectl` / `helm` / `docker` reach: `device_bash` is an isolated VM with
only this folder mounted. Claude edits and commits; the developer runs every cluster command, and a
DoD item that needs the cluster is reported `NOT VERIFIED`, never assumed.
