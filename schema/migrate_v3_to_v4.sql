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
-- PROVENANCE -- CHECKED AGAINST THE SHIPPED FILE, 2026-09-18. PASS.
--   The statements below were transcribed from upstream schema-v4.sql at tag
--   apache-polaris-1.6.0. They are NOT the shipped file, so they were verified against it:
--
--     python3 postgresql/schema/verify_v4_transcription.py \
--         --v3        /tmp/schema-v3.shipped.sql \
--         --v4        /tmp/schema-v4.shipped.sql \
--         --migration postgresql/schema/migrate_v3_to_v4.sql
--
--   -> PASS. v3 10 objects, v4 21, v4 adds 11, this file has those 11 and nothing else;
--      the 10 objects v3 and v4 share are declared identically, so the delta really is
--      additive. Both shipped files came out of the 1.6.0 image via Docker -- see the
--      runbook's step 2c, and do NOT use the `kubectl exec deploy/benchmarks-polaris --
--      unzip -p /deployments/*.jar` form this header used to give: the running pod is
--      1.3.0, which does not ship schema-v4.sql at all, and a Quarkus thin jar keeps its
--      resources under /deployments/lib/ regardless. That command hung, and it could not
--      have answered the question even if it had returned.
--
--   The same run also settled a claim nothing had ever tested: CLAUDE.md calls this repo's
--   schema_v3.sql "the ASF-shipped file and the authority", and every conclusion above was
--   computed against it. Diffed against the shipped v3 it differs in INDENTATION ONLY (plus
--   a missing trailing newline) -- no column, type, constraint, index or version value
--   moves. The baseline holds.
--
--   Every statement here is IF NOT EXISTS, so running the shipped schema-v4.sql directly
--   against a v3 database is itself a valid migration and is preferable if you have it.
--   The one thing the shipped file does not do is refuse to run on a non-v3 database.
--
-- HOW TO RUN
--   Take a metastore dump first. Then, against the PRIMARY (pg-1 as of 2026-09-17, confirm
--   with repmgr -- do not assume pg-0), from the repo root:
--
--     kubectl -n datahub-hynix exec -i benchmarks-postgresql-postgresql-ha-postgresql-1 -- \
--       env PGPASSWORD=polaris psql -U polaris -d polaris -v ON_ERROR_STOP=1 \
--       < postgresql/schema/migrate_v3_to_v4.sql
--
--   `exec -i`, NOT `exec -it`: a TTY adds carriage returns and can corrupt piped SQL.
--   NOT `kubectl port-forward` + a local `psql -f`: port-forward blocks the terminal
--   (CLAUDE.md, Persistent Server Block), assumes a psql on the Mac, and routes through
--   nothing useful. `PGPASSWORD` must be passed or psql prompts and the exec hangs silently.
--   Do NOT run this through pgpool: a read there can be load-balanced onto a standby, which
--   is the `#15` hypothesis A mechanism, so a version check through pgpool begs the question.
--
--   Polaris should be scaled to 0 while this runs, and started on 1.6.0 afterwards. Check the
--   HPA did not undo the scale-to-0 -- `minReplicas: 1` is live (`#8`).
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
-- 4. Table comments, verbatim from the shipped schema-v4.sql (its lines 226, 295).
--
--    These were missing until 2026-09-18. The verifier's two original claims are about
--    CREATE TABLE/INDEX/SCHEMA/VIEW and could not see them, so it reported PASS on a
--    migration that left the database one annotation short of the shipped file's. Harmless
--    in itself -- which is exactly why it is the useful kind of miss to find: the same blind
--    spot would have hidden a CREATE FUNCTION or a GRANT. The verifier now checks residual
--    statements too (its CLAIM 3).
--
--    Upstream comments only these two tables; idempotency_records carries none. Do not add
--    one for symmetry -- the point is to match the shipped file, not to improve on it.
-- ---------------------------------------------------------------------------

COMMENT ON TABLE scan_metrics_report IS 'Scan metrics reports as first-class entities';
COMMENT ON TABLE commit_metrics_report IS 'Commit metrics reports as first-class entities';

-- ---------------------------------------------------------------------------
-- 5. Record the new version LAST, so a failure above leaves the row at 3.
-- ---------------------------------------------------------------------------

UPDATE polaris_schema.version SET version_value = 4 WHERE version_key = 'version';

COMMIT;

-- Read it back:
--   SELECT * FROM polaris_schema.version;
