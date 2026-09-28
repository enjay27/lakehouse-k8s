# lakehouse-k8s

A local, single-node lakehouse platform on OrbStack Kubernetes (Apache Polaris 1.6.0 as the Iceberg
REST catalog, on PostgreSQL HA + Pgpool-II and MinIO, with Polaris audit logs shipped to OpenSearch),
and the Python suite that measures it.

| half | trees | what it is |
|---|---|---|
| **platform** | `charts/` `releases/` `logging/` `schema/` `runbooks/` `images/` | Helm charts and values for namespace `datahub-hynix` on context `orbstack`, the audit-log pipeline, the Polaris DDL |
| **suite** | `src/` `tests/` `notebooks/` `diagnostics/` | notebooks, sweeps and pytest for Polaris behaviour: API → SQL, privileges, purge, log coverage |

**Working rules** (plan-first, which gate each half must pass, the cluster-context guard,
commit conventions) are in [`CLAUDE.md`](CLAUDE.md). **What is true now** is in
[`MEMORY.md`](MEMORY.md); the detail behind it is in [`.memory/`](.memory/README.md).

## Suite: set up and test

```bash
uv sync                                          # Python 3.12, from uv.lock
diagnostics/ladders/log-coverage/fetch_specs.sh  # once per clone: vendors the OpenAPI documents (gitignored)
uv run pytest                                    # offline: no cluster needed
uv run black . && uv run isort .
```

Without `fetch_specs.sh` a fresh clone fails 13 tests and errors 49 on `SpecUnavailable`. The Lua
policy tests also need a Lua interpreter (`brew install luajit`).

Notebooks read their settings through `init_env("local" | "dev" | "prod")`. Copy
`src/config/<env>.example.yaml` to `src/config/<env>.yaml` (gitignored) and supply secrets as
environment variables. `dev` and `prod` are shared company environments: see
[`.memory/environments.md`](.memory/environments.md) for what may run where.

## Platform: check before changing

```bash
kubectl config current-context                   # must be exactly: orbstack
helm list -n datahub-hynix
helm lint charts/<chart>
helm upgrade --install <release> ./charts/<chart> -n datahub-hynix --dry-run=client --debug
```

Install order: MinIO → PostgreSQL → Polaris → everything else. A Fluent Bit Lua change is rolled only
with `bash releases/fluent-bit/apply-lua.sh`. Read `.memory/active-issues/platform.md` before any
upgrade. In particular, `#53`: upgrading `benchmarks-minio` from this chart would start MinIO on an
empty volume.

## Where to read

| | |
|---|---|
| [`logging/README.md`](logging/README.md) | the audit-log pipelines and which document is current |
| [`diagnostics/README.md`](diagnostics/README.md) · [`diagnostics/ladders/*/README.md`](diagnostics/ladders/) | inspection notebooks and the high-rigor sweeps |
| `notebooks/<domain>/README.md` | each test domain |
| [`runbooks/RESET-AND-CLEAN-INSTALL.md`](runbooks/RESET-AND-CLEAN-INSTALL.md) | rebuilding the cluster from nothing |
| [`docs/MERGE-2026-09-21.md`](docs/MERGE-2026-09-21.md) | why the two former repos are one |
| [`docs/DELETED-2026-09-29.md`](docs/DELETED-2026-09-29.md) | a file an older note names that no longer exists |
