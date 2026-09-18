--
-- Polaris relational-JDBC metastore: migrate schema v3 -> v4.
--
-- WHY THIS FILE EXISTS
--   Polaris does not run automated schema migrations. Bootstrapping applies a *full*
--   schema-vN.sql and records the version in polaris_schema.version; upgrading an existing
--   database is a manual, operator-driven step. Polaris 1.6.0's relational-JDBC backend
--   declares latest schema version 4 (DatabaseType.java, apache-polaris-1.6.0). This repo
--   bootstrapped from schema_v3.sql, so 1.6.0 needs v3 -> v4.
--
-- WHAT THE DELTA ACTUALLY IS -- additive only.
--   Compared object by object, upstream schema-v4.sql and this repo's schema_v3.sql declare
--   IDENTICAL definitions for every table they share: entities, grant_records,
--   principal_authentication_data, policy_mapping_record, events. There is no ALTER, no
--   column type change, no data rewrite. v4 only ADDS:
--     * 3 indexes on existing tables (idx_entities_catalog_id_id, idx_grants_realm_grantee,
--       idx_grants_realm_securable)
--     * idempotency_records + idx_idemp_realm_expires      (REST idempotency)
--     * scan_metrics_report + 2 indexes                    (Iceberg metrics reports)
--     * commit_metrics_report + 2 indexes
--     * version_value 3 -> 4
--   Note the v4 file's own header says only "Changes from v2: added events,
--   idempotency_records". That header is incomplete -- it does not mention the metrics
--   report tables or the new indexes. Do not use it as the delta.
--
--   The risky step this repo was braced for -- ALTER TABLE events ALTER COLUMN catalog_id
--   DROP NOT NULL -- is the v5 migration, and v5 belongs to 1.7.0, NOT to 1.6.0. On 1.6.0
--   events.catalog_id stays TEXT NOT NULL, exactly as v3 has it. The audit event listener
--   configured in polaris/values.yaml keeps writing the same shape.
--
-- PROVENANCE, AND THE ONE THING TO DO BEFORE RUNNING THIS
--   The statements below were transcribed from upstream schema-v4.sql at tag
--   apache-polaris-1.6.0. They are NOT the shipped file. Before running this against the
--   metastore, diff it against the v4 script that actually ships in the 1.6.0 image:
--
--     kubectl -n datahub-hynix exec deploy/benchmarks-polaris -- \
--       sh -c 'unzip -p /deployments/*.jar postgres/schema-v4.sql' > /tmp/schema-v4.shipped.sql
--     # (if the resource is not at that path, find it:
--     #  unzip -l /deployments/*.jar | grep schema-v)
--
--   Every statement here is IF NOT EXISTS, so running the shipped schema-v4.sql directly
--   against a v3 database is itself a valid migration and is preferable if you have it.
--
-- HOW TO RUN
--   Take a metastore dump first. Then, against the PRIMARY (pg-1 as of 2026-09-17, confirm
--   with repmgr -- do not assume pg-0):
--     psql -U polaris -d polaris -v ON_ERROR_STOP=1 -f migrate_v3_to_v4.sql
--   Polaris should be scaled to 0 while this runs, and started on 1.6.0 afterwards.
--
-- NOT VERIFIED: nothing below has been executed. This was written in a Cowork session,
-- which has no kubectl/helm/psql reach.
--

\set ON_ERROR_STOP on

BEGIN;

SET search_path TO POLARIS_SCHEMA;

-- Refuse to run on anything but a v3 database.
DO $$
DECLARE v INTEGER;
BEGIN
    SELECT version_value INTO v FROM polaris_schema.version WHERE version_key = 'version';
    IF v IS NULL THEN
        RAISE EXCEPTION 'polaris_schema.version has no ''version'' row -- this is not a bootstrapped Polaris metastore';
    END IF;
    IF v = 4 THEN
        RAISE EXCEPTION 'metastore is already at schema v4 -- nothing to do';
    END IF;
    IF v <> 3 THEN
        RAISE EXCEPTION 'metastore is at schema v%, not v3 -- this migration covers v3 -> v4 only', v;
    END IF;
END $$;

-- ---------------------------------------------------------------------------
-- 1. New indexes on existing tables.
-- ---------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_entities_catalog_id_id ON entities (catalog_id, id);

CREATE INDEX IF NOT EXISTS idx_grants_realm_grantee
    ON grant_records (realm_id, grantee_id);

CREATE INDEX IF NOT EXISTS idx_grants_realm_securable
    ON grant_records (realm_id, securable_id);

-- ---------------------------------------------------------------------------
-- 2. REST idempotency.
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS idempotency_records (
    realm_id TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    operation_type TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    http_status INTEGER,
    error_subtype TEXT,
    response_summary TEXT,
    response_headers TEXT,
    finalized_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    heartbeat_at TIMESTAMP,
    executor_id TEXT,
    expires_at TIMESTAMP,
    PRIMARY KEY (realm_id, idempotency_key)
);

CREATE INDEX IF NOT EXISTS idx_idemp_realm_expires
    ON idempotency_records (realm_id, expires_at);

-- ---------------------------------------------------------------------------
-- 3. Iceberg metrics reports.
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS scan_metrics_report (
    report_id TEXT NOT NULL,
    realm_id TEXT NOT NULL,
    catalog_id BIGINT NOT NULL,
    table_id BIGINT NOT NULL,
    timestamp_ms BIGINT NOT NULL,
    principal_name TEXT,
    request_id TEXT,
    otel_trace_id TEXT,
    otel_span_id TEXT,
    report_trace_id TEXT,
    snapshot_id BIGINT,
    schema_id INTEGER,
    filter_expression TEXT,
    projected_field_ids TEXT,
    projected_field_names TEXT,
    result_data_files BIGINT DEFAULT 0,
    result_delete_files BIGINT DEFAULT 0,
    total_file_size_bytes BIGINT DEFAULT 0,
    total_data_manifests BIGINT DEFAULT 0,
    total_delete_manifests BIGINT DEFAULT 0,
    scanned_data_manifests BIGINT DEFAULT 0,
    scanned_delete_manifests BIGINT DEFAULT 0,
    skipped_data_manifests BIGINT DEFAULT 0,
    skipped_delete_manifests BIGINT DEFAULT 0,
    skipped_data_files BIGINT DEFAULT 0,
    skipped_delete_files BIGINT DEFAULT 0,
    total_planning_duration_ms BIGINT DEFAULT 0,
    equality_delete_files BIGINT DEFAULT 0,
    positional_delete_files BIGINT DEFAULT 0,
    indexed_delete_files BIGINT DEFAULT 0,
    total_delete_file_size_bytes BIGINT DEFAULT 0,
    metadata JSONB DEFAULT '{}'::JSONB,
    PRIMARY KEY (realm_id, report_id)
);

CREATE INDEX IF NOT EXISTS idx_scan_report_timestamp ON scan_metrics_report(realm_id, timestamp_ms);
CREATE INDEX IF NOT EXISTS idx_scan_report_lookup ON scan_metrics_report(realm_id, catalog_id, table_id, timestamp_ms);

CREATE TABLE IF NOT EXISTS commit_metrics_report (
    report_id TEXT NOT NULL,
    realm_id TEXT NOT NULL,
    catalog_id BIGINT NOT NULL,
    table_id BIGINT NOT NULL,
    timestamp_ms BIGINT NOT NULL,
    principal_name TEXT,
    request_id TEXT,
    otel_trace_id TEXT,
    otel_span_id TEXT,
    report_trace_id TEXT,
    snapshot_id BIGINT NOT NULL,
    sequence_number BIGINT,
    operation TEXT NOT NULL,
    added_data_files BIGINT DEFAULT 0,
    removed_data_files BIGINT DEFAULT 0,
    total_data_files BIGINT DEFAULT 0,
    added_delete_files BIGINT DEFAULT 0,
    removed_delete_files BIGINT DEFAULT 0,
    total_delete_files BIGINT DEFAULT 0,
    added_equality_delete_files BIGINT DEFAULT 0,
    removed_equality_delete_files BIGINT DEFAULT 0,
    added_positional_delete_files BIGINT DEFAULT 0,
    removed_positional_delete_files BIGINT DEFAULT 0,
    added_records BIGINT DEFAULT 0,
    removed_records BIGINT DEFAULT 0,
    total_records BIGINT DEFAULT 0,
    added_file_size_bytes BIGINT DEFAULT 0,
    removed_file_size_bytes BIGINT DEFAULT 0,
    total_file_size_bytes BIGINT DEFAULT 0,
    total_duration_ms BIGINT DEFAULT 0,
    attempts INTEGER DEFAULT 1,
    metadata JSONB DEFAULT '{}'::JSONB,
    PRIMARY KEY (realm_id, report_id)
);

CREATE INDEX IF NOT EXISTS idx_commit_report_timestamp ON commit_metrics_report(realm_id, timestamp_ms);
CREATE INDEX IF NOT EXISTS idx_commit_report_lookup ON commit_metrics_report(realm_id, catalog_id, table_id, timestamp_ms);

-- ---------------------------------------------------------------------------
-- 4. Record the new version LAST, so a failure above leaves the row at 3.
-- ---------------------------------------------------------------------------

UPDATE polaris_schema.version SET version_value = 4 WHERE version_key = 'version';

COMMIT;

-- Read it back:
--   SELECT * FROM polaris_schema.version;
