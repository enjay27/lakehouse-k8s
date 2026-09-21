CREATE SCHEMA polaris_schema;
SET search_path TO polaris_schema;
-- Version 테이블
CREATE TABLE version (
  version_key TEXT PRIMARY KEY,
  version_value INTEGER NOT NULL
);
INSERT INTO version (version_key, version_value) VALUES ('version', 3);
-- Entities 테이블 (모든 Polaris 엔티티 저장)
CREATE TABLE entities (
  realm_id TEXT NOT NULL,
  catalog_id BIGINT NOT NULL,
  id BIGINT NOT NULL,
  parent_id BIGINT NOT NULL,
  name TEXT NOT NULL,
  entity_version INT NOT NULL,
  type_code INT NOT NULL,
  sub_type_code INT NOT NULL,
  create_timestamp BIGINT NOT NULL,
  drop_timestamp BIGINT NOT NULL,
  purge_timestamp BIGINT NOT NULL,
  to_purge_timestamp BIGINT NOT NULL,
  last_update_timestamp BIGINT NOT NULL,
  properties JSONB not null default '{}'::JSONB,
  internal_properties JSONB not null default '{}'::JSONB,
  grant_records_version INT NOT NULL,
  location_without_scheme TEXT,
  PRIMARY KEY (realm_id, id),
  CONSTRAINT constraint_name UNIQUE (realm_id, catalog_id, parent_id, type_code, name)
);
CREATE INDEX idx_entities ON entities (realm_id, catalog_id, id);
CREATE INDEX idx_locations ON entities USING btree (realm_id, parent_id, location_without_scheme) WHERE location_without_scheme IS NOT NULL;

-- Grant Records 테이블
CREATE TABLE grant_records (
  realm_id TEXT NOT NULL,
  securable_catalog_id BIGINT NOT NULL,
  securable_id BIGINT NOT NULL,
  grantee_catalog_id BIGINT NOT NULL,
  grantee_id BIGINT NOT NULL,
  privilege_code INTEGER,
  PRIMARY KEY (realm_id, securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code)
);
-- Principal Authentication Data 테이블
CREATE TABLE principal_authentication_data (
  realm_id TEXT NOT NULL,
  principal_id BIGINT NOT NULL,
  principal_client_id VARCHAR(255) NOT NULL,
  main_secret_hash VARCHAR(255) NOT NULL,
  secondary_secret_hash VARCHAR(255) NOT NULL,
  secret_salt VARCHAR(255) NOT NULL,
  PRIMARY KEY (realm_id, principal_client_id)
);
-- Policy Mapping Record 테이블
CREATE TABLE policy_mapping_record (
  realm_id TEXT NOT NULL,
  target_catalog_id BIGINT NOT NULL,
  target_id BIGINT NOT NULL,
  policy_type_code INTEGER NOT NULL,
  policy_catalog_id BIGINT NOT NULL,
  policy_id BIGINT NOT NULL,
  parameters JSONB NOT NULL DEFAULT '{}'::JSONB,
  PRIMARY KEY (realm_id, target_catalog_id, target_id, policy_type_code, policy_catalog_id, policy_id)
);
CREATE INDEX idx_policy_mapping_record ON policy_mapping_record (realm_id, policy_type_code, policy_catalog_id, policy_id, target_catalog_id, target_id);
-- Events 테이블
CREATE TABLE events (
  realm_id TEXT NOT NULL,
  catalog_id TEXT NOT NULL,
  event_id TEXT NOT NULL,
  request_id TEXT,
  event_type TEXT NOT NULL,
  timestamp_ms BIGINT NOT NULL,
  principal_name TEXT,
  resource_type TEXT NOT NULL,
  resource_identifier TEXT NOT NULL,
  additional_properties JSONB NOT NULL DEFAULT '{}'::JSONB,
  PRIMARY KEY (event_id)
);
