# Repository map

Where things live. The layout rules themselves are in `CLAUDE.md`; this is the
current inventory, which moves faster than the rules do.

- `src/polaris_test_utils.py`, `src/minio_rest.py`, `src/polaris_rest.py` — shared modules.
- `src/iceberg_rest.py` — Iceberg REST Catalog v1 client (28 methods; separate from `polaris_rest.py` by decision). `src/api_trace.py` — three-stream trace capture + correlation + entity-access-shape classification. `src/schema_audit.py` — schema/index/EXPLAIN audit. `src/polaris_seed.py` — bulk fixture seeding (resumable ledger, PG-HA lag handling). `src/run_manifest.py` — per-run manifests + live-cluster verification (`test_run_manifest.py`, 13 mocked cases).
- `diagnostics/api-sql-profile/` — Phase 1 API→SQL profiling: `01_api_access_map.ipynb`, `02_index_audit.ipynb`, `seed_polaris.py`, `capture.sh`, `HANDOFF-phase1.md` + `HANDOFF-02.md`, timestamped `reports/`, and `runs/<run_id>.json` manifests (tracked; they pair 1:1 with the reports by `run_id`).
- `src/config/` — `common.yaml` + `<env>.yaml` (merged by `init_env`); secrets via env vars. `dev.yaml`/`prod.yaml` gitignored.
- `lifecycle/` — entity lifecycle. `privilege/` — min-privilege matrix. `rbac/` — RBAC verify + role graph.
- `purge/` — purge→MinIO (purge_practice, view_purge, prove_minio, plus `table_view_purge_privilege_test.ipynb` and its successor `table_purge_privilege_test.ipynb` — table purge + privilege). `etl/` — ingestion/flow. `diagnostics/` — config/metastore/data_layers/entities/api_deps.
- `scenario/` — composite scenario. `availability/` — read-only checks (**PROD-safe**). `error-cases/` — 21 negative tests. `admin/` — teardown + rotate_credential.
- `attic/` — superseded dups/backups (delete on host). `datahub-error-cases/` — separate product, left untouched (will move to a datahub root later).

