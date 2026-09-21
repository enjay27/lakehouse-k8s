# ETL / Data Flow Tests

## Concept
Data ingestion and end-to-end flow through Polaris + Iceberg: writing rows into a table (snapshots) and validating the full extract/load path.

## Purpose
Exercise data writes and confirm the flow lands correctly (catalog record + MinIO Parquet + snapshot history), distinct from the structural lifecycle in `lifecycle/`.

## Notebooks
- `polaris_etl_flow_test.ipynb` — end-to-end ETL flow assertions via `../src/polaris_test_utils.py`.
- `polaris_insert_data.ipynb` — data-insertion notebook.

## How to run
**Restart & Run All.** `polaris_etl_flow_test.ipynb` bootstraps `../src` and calls `require_not_prod(...)`.

## Configuration
Both notebooks bootstrap `../src` and call `init_env("local")` (no hardcoded endpoints/credentials). `polaris_insert_data.ipynb` mutates state, so it calls `require_not_prod(...)`.
