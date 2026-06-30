# Error-Case Tests

## Concept
A catalog of **negative tests** — each notebook deliberately provokes a specific Polaris/infra failure and asserts the expected error response and log signature. Numbered by HTTP/condition (401/403/404/409/500/503, plus FATAL/connection-pool cases).

## Purpose
Verify that Polaris fails *correctly* and observably: the right status code, error body, and OpenSearch log evidence for each fault — auth failures, missing privileges, conflicts, malformed requests, version mismatches, connection-pool exhaustion, MinIO/Postgres faults, etc.

## Notebooks
21 cases, e.g.:
- `01_401_expired_token`, `02_401_deleted_principal`, `03_401_wrong_credentials`, `17_401_token_refresh_race_condition`, `20_401_credential_rotation_required`
- `04_403_no_catalog_role`, `05_403_wrong_privilege`, `06_403_purge_disabled`, `11_403_principal_role_not_assigned`
- `07_409_entity_exists`, `08_409_namespace_not_empty`, `14_409_duplicate_grant`
- `09_500_null_pointer`, `16_500_entity_version_mismatch`, `18_500_concurrent_modification_conflict`, `23_500_minio_bucket_not_found`
- `10_404_missing_realm_header`, `13_404_catalog_not_found`, `12_400_malformed_request`, `15_FATAL_connection_pool_error`, `27_503_postgresql_max_connections`

## How to run
**Restart & Run All** an individual case. Each first cell bootstraps `../src`, reloads `polaris_test_utils`, and calls `require_not_prod(...)` — these are run on `local`/`dev`, never PROD (they intentionally create faults).

## Reference docs
- `issue-report-postgresql-restore.md` — PostgreSQL restore issue write-up.
- `opensearch-alerts.md` — OpenSearch alerting notes.
