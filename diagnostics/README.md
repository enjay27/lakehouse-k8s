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

## ⚠️ Migration note
These were migrated **self-contained** — they currently hardcode `POLARIS_URL` (and some, credentials) rather than using `init_env`/`../src`. They target the local device. Porting them onto `../src/polaris_test_utils.py` + `init_env` (and removing hardcoded secrets per the Zero-Hardcoded-Credentials rule) is tracked in `MEMORY.md`.
