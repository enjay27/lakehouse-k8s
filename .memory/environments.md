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

- **Only pgpool is a LoadBalancer.** Direct PostgreSQL access needs
  `kubectl -n datahub-hynix port-forward pod/benchmarks-postgresql-postgresql-ha-postgresql-0 5433:5432`.
- **Polaris management port is 8182**, not the 8282 the upstream docs default to.
  `/q/health` and `/q/metrics` live there.
- **Pgpool-II, not PgBouncer.** It load-balances SELECTs across all three
  replicas, so a PostgreSQL server log tailed from one pod misses statements.
- VictoriaLogs UI/ingest: `9428`, namespace `logging`, LoadBalancer.
- **OpenSearch runs in Docker**, not in Kubernetes — outside this repo, so no compose
  file is versioned here. It survives a cluster reset because nothing in the cluster
  owns it.
- **Fluent Bit runs as a K8s DaemonSet** (confirmed working 2026-09-03). Which sink it
  ships to is `active-issues.md` #2.

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
