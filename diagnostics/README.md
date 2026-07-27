# Diagnostics

## Concept
Read/inspect notebooks that surface the internal state of Polaris and its backing stores — configuration, metastore (PostgreSQL), data layers (MinIO), entity inventory, and API dependency relationships.

## Purpose
Provide visibility for debugging and verification: what catalogs/namespaces/entities exist, how config is set, how the metastore and storage layers map to catalog records, and which API calls depend on which.

## Notebooks
- `polaris_configuration.ipynb` — Polaris configuration inspection.
- `polaris_metastore.ipynb` — PostgreSQL metastore inspection.
- `polaris_data_layers.ipynb` — MinIO / storage-layer mapping.
- `polaris_entities.ipynb` — catalog/namespace/table/view inventory.
- `polaris_api_dependency_test.ipynb` — API call dependency mapping.

## How to run
**Restart & Run All.** Linear execution; close DB cursors/pools in the teardown cell.

## Configuration
All five now bootstrap `../src` and call `init_env("local")` — no hardcoded endpoints or credentials. Polaris/MinIO settings come from `init_env`; the PostgreSQL ones (`metastore`, `configuration`, `entities`) use the `PG_URL` / `PG_CONFIG` globals (`src/config/<env>.yaml` → `postgres_*`, password overridable via `POSTGRES_PASSWORD`). Switch environments with `init_env("dev")`.

## Reference reports
- `doc-shm-exhaustion-test-plan.md` — plain Postgres `/dev/shm` exhaustion reproduction (Docker + OrbStack K8s), tied to a production incident. Not a notebook and not wired to `src`/`init_env` — it's raw Docker/psql/K8s, run manually on the host and outside this repo's Polaris-testing model. Docker leg executed and verified 2026-07-09 (results in §10); OrbStack K8s leg still pending.
