# Goal — the standing objective

Merged 2026-09-29 from `goal-platform.md` and `goal-catalog.md`, which described the two repos
before the 2026-09-21 merge.

One repo, two halves:

- **platform** (`charts/ releases/ logging/ schema/ runbooks/ images/`): run a **local,
  single-node data platform** on OrbStack Kubernetes, close enough to the company DEV/PROD topology
  to be worth measuring against, with this repo as the authoritative copy of its configuration.
- **suite** (`src/ tests/ notebooks/ diagnostics/`): diagnostic and verification notebooks and
  sweeps that measure Apache Polaris on that platform (API → SQL behaviour, privileges, purge,
  log coverage), and run the non-destructive subset against company DEV / PROD.

The suite is the platform's one consumer: it needs a cluster whose settings are *known*, not
assumed. Hence CLAUDE.md's rule to verify a setting against the running object and the chart
default, never against a values file.

## Structural model — as measured 2026-09-29 (`helm list`, `kubectl get`)

```
Docker / OrbStack host
├── Kubernetes (context: orbstack)
│   └── namespace datahub-hynix          ← every platform service
│       ├── benchmarks-minio             MinIO, Deployment + PVC benchmarks-minio-data   (release rev 1; see #53)
│       ├── benchmarks-postgresql        PostgreSQL HA: 3-replica StatefulSet + Pgpool-II   (Polaris metastore, schema v4)
│       ├── benchmarks-polaris           Apache Polaris 1.6.0, HPA 1..3 (#39); JSON log per pod on PVC polaris-logs-pvc
│       └── benchmarks-fluent-bit        DaemonSet, fluent-bit 5.1.1 → OpenSearch (k8s-logs / polaris-logs / polaris-report v6)
├── opensearch-node, opensearch-dashboards   Docker containers, outside Kubernetes and outside this repo
```

**Written, not installed:** `releases/` also holds values for airflow, argo, datahub, jupyter, kafka,
schema-registry and spark. None of them is a Helm release on the cluster. `charts/polaris-log-batch/`
(the hourly log batch CronJob) is written and tested but has not been built or installed.

Dependency order is real and one-directional: **MinIO → PostgreSQL → Polaris → everything else.**
Polaris will not bootstrap without its bucket and its metastore.

## What this repo is not

- Not a production deployment. No shared cluster is ever targeted from the platform half.
- Not a chart mirror. Only `minio/`, `polaris/`, `postgresql/` (an umbrella) and
  `polaris-log-batch/` are local charts; the rest are values files against upstream charts.
- Not a schema lab. Every measurement is taken on the schema Polaris ships (CLAUDE.md *Schema Policy*).
