# Lifecycle Tests

## Concept
The full lifecycle of Apache Polaris (1.3.0) entities — **catalog → namespace → table/view → data snapshots → drop** — across the three services that back it: Polaris (the catalog/index), PostgreSQL (the metadata store), and MinIO (the Parquet data files).

## Purpose
Exercise and assert each lifecycle stage end-to-end so that creation, data writes (Iceberg snapshots), reads, and removal behave as expected, and so that the read-after-write timing characteristics of this build are documented rather than assumed.

## Notebooks
- `polaris_lifecycle_practice.ipynb` — creates a dedicated catalog/namespace/table, writes a real Parquet snapshot through a non-root instance principal, reads it back, and tears everything down.

## How to run
1. Ensure Polaris / MinIO / OpenSearch are port-forwarded to the host as configured in `../src/config/dev.yaml`.
2. Open the notebook and **Restart & Run All** (cells are linear by design).
3. The first cell bootstraps `../src` onto `sys.path` and calls `init_env("dev")`. Switch environments by changing `init_env("dev")` → `init_env("prod")`.

## Result / findings
See `doc-entity-lifecycle.md` for the conceptual model (System Manager vs Data Manager tracks) and the detailed lifecycle walkthrough. Key behavioral note for this build: data operations are performed by a dedicated **instance principal**, not root — root is used only for management-API bootstrap and cleanup.

## Reference docs
- `doc-entity-lifecycle.md` — entity lifecycle guide / conceptual model.
