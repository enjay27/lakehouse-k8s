# Goal — the standing objective

Run a **local, single-node data platform** on OrbStack Kubernetes that is close
enough to the company DEV/PROD topology to be worth measuring against, and keep
its configuration in this repo as the authoritative copy.

Everything here exists to serve one downstream consumer: the `polaris-learning`
test suite, which profiles Apache Polaris API/SQL behaviour and needs a cluster
whose settings are known, not assumed.

## Structural model

```
Docker / OrbStack host
└── Kubernetes (context: orbstack)
    ├── namespace datahub-hynix     ← every platform service
    │   ├── benchmarks-minio        object store (S3) — Iceberg warehouse + Argo artifacts
    │   ├── benchmarks-postgresql   PostgreSQL HA, 3 replicas + Pgpool-II  (Polaris metastore)
    │   ├── benchmarks-polaris      Apache Polaris — Iceberg REST catalog
    │   ├── datahub + prerequisites Kafka / Elasticsearch / MySQL / ZooKeeper
    │   ├── benchmarks-spark        compute
    │   ├── benchmarks-airflow      / benchmarks-argo   orchestration
    │   ├── benchmarks-jupyter      notebooks
    │   └── benchmarks-fluent-bit   log shipper (DaemonSet + Polaris log PVC tail)
    └── namespace logging           ← log sink only
        └── VictoriaLogs (vlsingle), 9428
```

Dependency order is real and one-directional: **MinIO → PostgreSQL → Polaris →
everything else.** Polaris will not bootstrap without its bucket and its metastore.

## What this repo is not

- Not a production deployment. No shared cluster is ever targeted from here.
- Not the test suite. Notebooks, assertions and findings live in
  `polaris-learning`; this repo only makes the cluster they run against.
- Not a chart mirror. Only `minio/`, `polaris/` and `postgresql/` are local
  charts; the rest are values files against upstream charts.
