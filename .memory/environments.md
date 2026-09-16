# Environments — read before running anything

There is **one** cluster: a personal OrbStack single-node Kubernetes on Kade's
MacBook. No shared company cluster is reachable from this repo and none must ever
be targeted from it. That makes destructive commands *permissible* here — it does
not make them free, because the PVCs hold the only copy of the Polaris metastore
and the MinIO warehouse.

## Context and namespaces

| | value | guard |
|---|---|---|
| kubectl context | `orbstack` | run `kubectl config current-context` before **every** mutating command; halt on anything else |
| platform namespace | `datahub-hynix` | every `kubectl` / `helm` mutation carries `-n datahub-hynix` explicitly |
| log-sink namespace | `logging` | VictoriaLogs only (`vlsingle-victoria-logs-single-server`, port 9428) — the one deliberate exception to the single-namespace rule |

The namespace flag alone is not a guard. `-n datahub-hynix` against a context
pointed somewhere else is a deployment into someone else's cluster with a
plausible-looking name.

## Reaching things

- **Of the PostgreSQL components, only pgpool is a LoadBalancer.** Direct access to a
  *replica* needs
  `kubectl -n datahub-hynix port-forward pod/benchmarks-postgresql-postgresql-ha-postgresql-0 5433:5432`.
  Read this as scoped to PostgreSQL — **the cluster has five LoadBalancer Services**, one
  `svclb-*` DaemonSet each in `kube-system` (measured 2026-09-08, `kubectl get ds -A`):
  `benchmarks-minio`, `benchmarks-polaris`, `benchmarks-polaris-mgmt`,
  `benchmarks-postgresql-postgresql-ha-pgpool`, `vlsingle-victoria-logs-single-server`.
  That is a wider exposed surface than #7 describes for 9428 alone; Polaris' management
  port and MinIO are published the same way. `svclb-vlsingle-…` disappears with the
  VictoriaLogs uninstall.
- **Polaris management port is 8182**, not the 8282 the upstream docs default to.
  `/q/health` and `/q/metrics` live there.
- **Pgpool-II, not PgBouncer.** It load-balances SELECTs across all three
  replicas, so a PostgreSQL server log tailed from one pod misses statements.
- VictoriaLogs UI/ingest: `9428`, namespace `logging`, LoadBalancer.
- **OpenSearch `3.5.0` runs in Docker**, not in Kubernetes — outside this repo, so no
  compose file is versioned here. It survives a cluster reset because nothing in the
  cluster owns it. **Version measured 2026-09-08** (`GET /`, container
  `opensearch-node`, published `0.0.0.0:9200->9200`); it had never been recorded
  anywhere. Being 3.x, mapping types are gone: `Suppress_Type_Name On` is correct and
  `fluent-bit/values.yaml`'s `Type _doc` is dead config.
  `opensearch-dashboards` runs beside it on `5601`.
- **A pod reaches OpenSearch at `192.168.194.1:9200` on the ordinary pod network.**
  Neither Fluent Bit values file sets `hostNetwork`, and the DaemonSet has shipped to
  that address continuously — so this is not a host-network privilege. `192.168.194.1`
  is the host as the cluster sees it, and it appears as `client_ip` in Polaris access
  logs, so it routes both ways. **The Fluent Bit image has no `curl`**: probe it with a
  throwaway `curlimages/curl` pod, not `kubectl exec` into the shipper.
- **Fluent Bit runs as two releases**, both in `datahub-hynix`: the DaemonSet
  **`benchmarks-fluent-bit`** (container stdout → OpenSearch) and the Deployment
  `fb-polaris-shipper`. Names and sinks are settled in `active-issues.md` #2.
  **Neither sets `hostNetwork`** (measured 2026-09-08). `benchmarks-fluent-bit` is
  **chart `fluent-bit-0.57.6`, `appVersion` 5.0.6, SSA, REVISION 17 deployed 2026-09-16** (policy v5;
  16 upgrades since the 2026-08-19 install — *this line said "REVISION 1, never upgraded" and image
  3.2.2 until 2026-09-16*). `appVersion` is the chart's field, *not* the running image: the running
  image is **`fluent-bit:5.1.1`**, one container — rev 17's `reloader` sidecar was removed and rolled the same
  day (#28, step3 PASS). Read images off the DaemonSet, not off `helm get
  metadata`. One pod (DaemonSet, one node); `READY 2/2` on rev 17 is two containers, not two replicas.

## Secrets

Never in a committed file. Pass with `--set-string` from an environment variable,
or a gitignored `values-secret.yaml` overlay. Committed `values.yaml` files carry
non-secret defaults or a Secret *name* only — see `active-issues.md` for the ones
that currently violate this.

## Constraint on Cowork sessions

**A Cowork session has no `kubectl` / `helm` / `docker` reach into OrbStack.**
`device_bash` runs in an isolated VM with only this repo folder mounted. Claude can
read, edit, lint by inspection and commit; it cannot install, verify against a live
cluster, or run the §5 verification block. Every cluster command in this repo's
runbooks is run **by the developer**, and any DoD item that requires a live cluster
must be reported as `NOT VERIFIED` rather than assumed.
