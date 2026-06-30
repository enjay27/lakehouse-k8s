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

## Migration note
`polaris_insert_data.ipynb` was migrated self-contained (hardcoded local endpoint); porting it onto `init_env`/`../src` is tracked in `MEMORY.md`.
