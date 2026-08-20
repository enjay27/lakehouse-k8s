# API → SQL → MinIO Access Matrix

Generated 2026-08-20 13:53 from a live local run — Polaris 1.3.0, realm POLARIS.
Schema version 3 (OK).

R = read, W = write, RW = both.

## API → PostgreSQL tables

| API | entities | grant_records | nodes | pg_stat_replication | policy_mapping_record | principal_authentication_data |
|---|---|---|---|---|---|---|
| `iceberg.commit_table` | RW | R | · | · | · | · |
| `iceberg.create_namespace` | RW | R | · | · | · | · |
| `iceberg.create_table` | RW | R | · | · | · | · |
| `iceberg.create_view` | RW | R | · | · | · | · |
| `iceberg.drop_namespace` | RW | RW | · | · | RW | · |
| `iceberg.drop_table` | RW | RW | R | R | RW | · |
| `iceberg.drop_view` | RW | RW | R | R | · | · |
| `iceberg.get_config` | R | R | · | · | · | · |
| `iceberg.head_namespace` | R | R | R | R | · | · |
| `iceberg.head_table` | R | R | · | · | · | · |
| `iceberg.head_view` | R | R | R | · | · | · |
| `iceberg.list_namespaces` | R | R | R | · | · | · |
| `iceberg.list_tables` | R | R | · | · | · | · |
| `iceberg.list_views` | R | R | R | R | · | · |
| `iceberg.load_namespace` | R | R | · | · | · | · |
| `iceberg.load_table` | R | R | R | R | · | · |
| `iceberg.load_table[missing]` | R | R | · | · | · | · |
| `iceberg.load_table[snapshots=refs]` | R | R | · | · | · | · |
| `iceberg.load_view` | R | R | · | · | · | · |
| `iceberg.rename_table` | RW | R | · | · | · | · |
| `iceberg.rename_view` | RW | R | · | · | · | · |
| `iceberg.report_metrics` | R | R | · | · | · | · |
| `iceberg.stage_create_table` | R | R | R | · | · | · |
| `iceberg.update_namespace_properties` | RW | R | · | · | · | · |
| `mgmt.assign_catalog_role` | RW | RW | R | R | · | · |
| `mgmt.assign_principal_role` | RW | RW | · | · | · | · |
| `mgmt.create_catalog_role` | RW | R | R | · | · | · |
| `mgmt.create_principal` | RW | R | · | · | · | RW |
| `mgmt.create_principal_role` | RW | R | R | R | · | · |
| `mgmt.delete_catalog_role` | RW | RW | R | R | · | · |
| `mgmt.delete_principal` | RW | RW | · | · | · | W |
| `mgmt.delete_principal_role` | RW | RW | · | · | · | · |
| `mgmt.get_catalog` | R | R | · | · | · | · |
| `mgmt.get_principal` | R | R | · | · | · | · |
| `mgmt.get_principal_role` | R | R | · | · | · | · |
| `mgmt.grant_privilege` | RW | RW | · | · | · | · |
| `mgmt.list_catalog_roles` | R | R | R | · | · | · |
| `mgmt.list_catalogs` | R | R | · | · | · | · |
| `mgmt.list_grants` | R | R | · | · | · | · |
| `mgmt.list_principal_roles` | R | R | R | R | · | · |
| `mgmt.list_principals` | R | R | R | · | · | · |
| `mgmt.list_principals_for_principal_role` | R | R | · | · | · | · |
| `mgmt.reset_principal_credentials` | R | R | R | · | · | RW |

## API → MinIO objects

| API | Method | Path | Count |
|---|---|---|---|
| `iceberg.load_table` |  | `/data-catalog-bucket/apiprofile1787201504_cat/probe_ns/probe_tbl/metadata/00000-53ffa6cb-ede3-4852-872b-0ec48f3afe70.metadata.json` | 1 |
| `iceberg.load_table[snapshots=refs]` |  | `/data-catalog-bucket/apiprofile1787201504_cat/probe_ns/probe_tbl/metadata/00000-53ffa6cb-ede3-4852-872b-0ec48f3afe70.metadata.json` | 1 |
| `iceberg.head_table` |  | `/data-catalog-bucket/apiprofile1787201504_cat/probe_ns/probe_tbl/metadata/00000-53ffa6cb-ede3-4852-872b-0ec48f3afe70.metadata.json` | 1 |
| `iceberg.create_table` |  | `/data-catalog-bucket/apiprofile1787201504_cat/probe_ns/probe_tbl2/metadata/00000-a8c14702-97e6-467b-b688-9ba4b0967c33.metadata.json` | 1 |
| `iceberg.commit_table` |  | `/data-catalog-bucket/apiprofile1787201504_cat/probe_ns/probe_tbl/metadata/00000-53ffa6cb-ede3-4852-872b-0ec48f3afe70.metadata.json` | 2 |
| `iceberg.commit_table` |  | `/data-catalog-bucket/apiprofile1787201504_cat/probe_ns/probe_tbl/metadata/00001-e7fcc1c1-92b1-43d9-a349-05f55cc29874.metadata.json` | 1 |
| `iceberg.create_view` |  | `/data-catalog-bucket/apiprofile1787201504_cat/probe_ns/probe_view/metadata/00000-06590ed6-b3b7-44f0-a6fd-f5e9e70c3d6d.gz.metadata.json` | 1 |
| `iceberg.load_view` |  | `/data-catalog-bucket/apiprofile1787201504_cat/probe_ns/probe_view/metadata/00000-06590ed6-b3b7-44f0-a6fd-f5e9e70c3d6d.gz.metadata.json` | 2 |
| `iceberg.head_view` |  | `/data-catalog-bucket/apiprofile1787201504_cat/probe_ns/probe_view/metadata/00000-06590ed6-b3b7-44f0-a6fd-f5e9e70c3d6d.gz.metadata.json` | 2 |

## Per-API detail

### `iceberg.get_config`

- `GET /v1/config` → **200**
- wall 28 ms · 14 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.14 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 3.78 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.11 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.12 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | — | — | 0.13 | ` ` |
| 8 | — | — | 0.15 | ` ` |
| 9 | — | — | 0.04 | ` ` |
| 10 | — | — | 0.05 | ` ` |
| 11 | — | — | 0.04 | ` ` |
| 12 | — | — | 0.06 | ` ` |
| 13 | — | — | 0.08 | ` ` |

### `iceberg.list_namespaces`

- `GET /v1/{cat}/namespaces` → **200**
- wall 32 ms · 26 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, nodes

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.20 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 4.53 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 1.19 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.11 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND sub_type_code = ? AND realm_id = ? AND parent_id = ? AND type` |
| 8 | — | — | 0.25 | ` ` |
| 9 | — | — | 0.13 | ` ` |
| 10 | — | — | 0.04 | ` ` |
| 11 | — | — | 0.07 | ` ` |
| 12 | — | — | 0.37 | ` ` |
| 13 | — | — | 0.10 | ` ` |
| 14 | — | — | 0.08 | ` ` |
| 15 | — | — | 0.02 | ` ` |
| 16 | — | SELECT | 0.14 | `SELECT repmgr.set_upstream_last_seen(1001)` |
| 17 | — | SELECT | 0.02 | `SELECT TRUE` |
| 18 | — | SELECT | 0.07 | `SELECT repmgr.get_local_node_id()` |
| 19 | nodes | SELECT | 0.09 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 20 | — | SELECT | 0.04 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 21 | — | SELECT | 0.05 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 22 | — | SELECT | 0.07 | `SELECT repmgr.set_upstream_last_seen(1001)` |
| 23 | — | SELECT | 0.02 | `SELECT TRUE` |
| 24 | — | SELECT | 0.06 | `SELECT repmgr.get_local_node_id()` |
| 25 | nodes | SELECT | 0.08 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |

### `iceberg.load_namespace`

- `GET /v1/{cat}/namespaces/{ns}` → **200**
- wall 12 ms · 16 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 1.66 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | — | — | 0.07 | ` ` |
| 8 | — | — | 0.02 | ` ` |
| 9 | — | — | 0.02 | ` ` |
| 10 | — | — | 0.02 | ` ` |
| 11 | — | — | 0.02 | ` ` |
| 12 | — | — | 0.09 | ` ` |
| 13 | — | — | 0.02 | ` ` |
| 14 | — | SELECT | 0.06 | `SELECT TRUE` |
| 15 | — | SELECT | 0.07 | `SELECT pg_catalog.pg_is_in_recovery()` |

### `iceberg.head_namespace`

- `HEAD /v1/{cat}/namespaces/{ns}` → **204**
- wall 12 ms · 19 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, nodes, pg_stat_replication

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 2.56 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | — | — | 0.10 | ` ` |
| 8 | — | — | 0.04 | ` ` |
| 9 | — | — | 0.06 | ` ` |
| 10 | — | — | 0.02 | ` ` |
| 11 | — | — | 0.05 | ` ` |
| 12 | — | — | 0.01 | ` ` |
| 13 | — | — | 0.02 | ` ` |
| 14 | — | SELECT | 0.14 | `SELECT 1` |
| 15 | — | SET | 0.07 | `SET synchronous_commit TO 'local'` |
| 16 | nodes | SELECT | 0.48 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 17 | pg_stat_replication | SELECT | 1.10 | `SELECT pg_catalog.current_setting('max_wal_senders')::INT AS max_wal_senders,         (SELECT pg_catalog.count(*) FROM pg_catalog.pg_stat_replication) AS attached_wal_receivers,   ` |
| 18 | — | SELECT | 0.03 | `SELECT pg_catalog.pg_is_in_recovery()` |

### `iceberg.update_namespace_properties`

- `POST /v1/{cat}/namespaces/{ns}/properties` → **200**
- wall 33 ms · 20 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.22 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 4.08 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND realm_id = ? AND type_code = ? AND catalog_id = ?` |
| 8 | entities | SELECT | 0.12 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | UPDATE | 0.10 | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |
| 10 | — | — | 0.24 | ` ` |
| 11 | — | — | 0.05 | ` ` |
| 12 | — | — | 0.01 | ` ` |
| 13 | — | — | 0.05 | ` ` |
| 14 | — | — | 0.05 | ` ` |
| 15 | — | — | 0.01 | ` ` |
| 16 | — | — | 0.04 | ` ` |
| 17 | — | — | 0.02 | ` ` |
| 18 | — | — | 0.04 | ` ` |
| 19 | — | — | 0.04 | ` ` |

### `iceberg.create_namespace`

- `POST /v1/{cat}/namespaces` → **500**
- wall 54 ms · 30 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.13 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.12 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.17 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 6.25 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 1.14 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.11 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND realm_id = ? AND type_code = ? AND catalog_id = ?` |
| 9 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 12 | entities | INSERT | 0.18 | `INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestam` |
| 13 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 14 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 15 | — | — | 0.25 | ` ` |
| 16 | — | — | 0.13 | ` ` |
| 17 | — | — | 0.12 | ` ` |
| 18 | — | — | 0.06 | ` ` |
| 19 | — | — | 0.13 | ` ` |
| 20 | — | — | 0.30 | ` ` |
| 21 | — | — | 0.21 | ` ` |
| 22 | — | — | 0.05 | ` ` |
| 23 | — | — | 0.08 | ` ` |
| 24 | — | — | 0.02 | ` ` |
| 25 | — | — | 0.03 | ` ` |
| 26 | — | — | 0.06 | ` ` |
| 27 | — | — | 0.07 | ` ` |
| 28 | — | — | 0.08 | ` ` |
| 29 | — | — | 0.01 | ` ` |

### `iceberg.drop_namespace`

- `DELETE /v1/{cat}/namespaces/{ns}` → **204**
- wall 50 ms · 33 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, policy_mapping_record

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.15 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.15 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 5.95 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.14 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | grant_records | SELECT | 0.07 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 8 | entities | SELECT | 0.22 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | entities | DELETE | — | `DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?` |
| 12 | grant_records | SELECT | 0.03 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 13 | grant_records | DELETE | 4.61 | `DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (
    (grantee_id = ? AND grantee_catalog_id = ?) OR
    (securable_id = ? AND securable_catalog_id = ?)
) AND realm_id = ?` |
| 14 | policy_mapping_record | SELECT | 0.01 | `SELECT target_catalog_id, target_id, policy_type_code, policy_catalog_id, policy_id, parameters FROM POLARIS_SCHEMA.POLICY_MAPPING_RECORD WHERE realm_id = ? AND target_id = ? AND t` |
| 15 | policy_mapping_record | DELETE | 0.03 | `DELETE FROM POLARIS_SCHEMA.POLICY_MAPPING_RECORD WHERE target_catalog_id = ? AND target_id = ? AND realm_id = ?` |
| 16 | — | — | 0.14 | ` ` |
| 17 | — | — | 0.07 | ` ` |
| 18 | — | — | 0.03 | ` ` |
| 19 | — | — | 0.04 | ` ` |
| 20 | — | — | 0.05 | ` ` |
| 21 | — | — | 0.08 | ` ` |
| 22 | — | — | 0.07 | ` ` |
| 23 | — | — | 0.07 | ` ` |
| 24 | — | — | 0.05 | ` ` |
| 25 | — | — | 0.08 | ` ` |
| 26 | — | — | 0.03 | ` ` |
| 27 | — | — | 0.08 | ` ` |
| 28 | — | — | 0.02 | ` ` |
| 29 | — | — | 0.04 | ` ` |
| 30 | — | — | 0.04 | ` ` |
| 31 | — | — | 0.05 | ` ` |
| 32 | entities | DELETE | 0.12 | `DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = $1 AND catalog_id = $2 AND id = $3 (grantee_id = $1 AND grantee_catalog_id = $2) OR (securable_id = $3 AND securable_catalog_id` |

### `iceberg.list_tables`

- `GET /v1/{cat}/namespaces/{ns}/tables` → **200**
- wall 12 ms · 18 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 1.58 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND sub_type_code = ? AND realm_id = ? AND parent_id = ? AND type` |
| 8 | — | — | 0.08 | ` ` |
| 9 | — | — | 0.08 | ` ` |
| 10 | — | — | 0.03 | ` ` |
| 11 | — | — | 0.03 | ` ` |
| 12 | — | — | 0.02 | ` ` |
| 13 | — | — | 0.01 | ` ` |
| 14 | — | — | 0.02 | ` ` |
| 15 | — | — | 0.02 | ` ` |
| 16 | — | SELECT | 0.13 | `SELECT TRUE` |
| 17 | — | SELECT | 0.09 | `SELECT pg_catalog.pg_is_in_recovery()` |

### `iceberg.load_table`

- `GET /v1/{cat}/namespaces/{ns}/tables/{tbl}` → **200**
- wall 94 ms · 29 statements · 1 object ops · cache: MISS
- tables: entities, grant_records, nodes, pg_stat_replication

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 1.95 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | grant_records | SELECT | 0.02 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 8 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 12 | — | — | 0.10 | ` ` |
| 13 | — | — | 0.02 | ` ` |
| 14 | — | — | 0.07 | ` ` |
| 15 | — | — | 0.03 | ` ` |
| 16 | — | — | 0.02 | ` ` |
| 17 | — | — | 0.01 | ` ` |
| 18 | — | — | 0.03 | ` ` |
| 19 | — | — | 0.01 | ` ` |
| 20 | — | — | 0.02 | ` ` |
| 21 | — | — | 0.02 | ` ` |
| 22 | — | SELECT | 0.18 | `SELECT 1` |
| 23 | — | — | 0.04 | ` ` |
| 24 | — | — | 0.08 | ` ` |
| 25 | — | SET | 0.07 | `SET synchronous_commit TO 'local'` |
| 26 | nodes | SELECT | 0.37 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 27 | pg_stat_replication | SELECT | 1.15 | `SELECT pg_catalog.current_setting('max_wal_senders')::INT AS max_wal_senders,         (SELECT pg_catalog.count(*) FROM pg_catalog.pg_stat_replication) AS attached_wal_receivers,   ` |
| 28 | — | SELECT | 0.02 | `SELECT pg_catalog.pg_is_in_recovery()` |

| # | Method | Path | ms |
|---|---|---|---|
| 0 |  | `/data-catalog-bucket/apiprofile1787201504_cat/probe_ns/probe_tbl/metadata/00000-53ffa6cb-ede3-4852-872b-0ec48f3afe70.metadata.json` | 1.05 |

### `iceberg.load_table[snapshots=refs]`

- `GET /v1/{cat}/.../tables/{tbl}?snapshots=refs` → **200**
- wall 26 ms · 16 statements · 1 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 1.79 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | — | — | 1.82 | ` ` |
| 9 | — | — | 0.02 | ` ` |
| 10 | — | — | 0.01 | ` ` |
| 11 | — | — | 0.01 | ` ` |
| 12 | — | — | 0.01 | ` ` |
| 13 | — | — | 0.01 | ` ` |
| 14 | — | — | 0.01 | ` ` |
| 15 | — | — | 0.02 | ` ` |

| # | Method | Path | ms |
|---|---|---|---|
| 0 |  | `/data-catalog-bucket/apiprofile1787201504_cat/probe_ns/probe_tbl/metadata/00000-53ffa6cb-ede3-4852-872b-0ec48f3afe70.metadata.json` | 1.19 |

### `iceberg.head_table`

- `HEAD /v1/{cat}/namespaces/{ns}/tables/{tbl}` → **204**
- wall 42 ms · 16 statements · 1 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.33 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 3.78 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.16 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.17 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | — | — | 0.20 | ` ` |
| 9 | — | — | 0.08 | ` ` |
| 10 | — | — | 0.09 | ` ` |
| 11 | — | — | 0.10 | ` ` |
| 12 | — | — | 0.07 | ` ` |
| 13 | — | — | 0.05 | ` ` |
| 14 | — | — | 0.06 | ` ` |
| 15 | — | — | 0.07 | ` ` |

| # | Method | Path | ms |
|---|---|---|---|
| 0 |  | `/data-catalog-bucket/apiprofile1787201504_cat/probe_ns/probe_tbl/metadata/00000-53ffa6cb-ede3-4852-872b-0ec48f3afe70.metadata.json` | 2.00 |

### `iceberg.create_table`

- `POST /v1/{cat}/namespaces/{ns}/tables` → **200**
- wall 71 ms · 46 statements · 1 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.10 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.10 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 6.22 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.13 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 12 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 13 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 14 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 15 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND realm_id = ? AND type_code = ? AND catalog_id = ?` |
| 16 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND realm_id = ? AND type_code = ? AND catalog_id = ?` |
| 17 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 18 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 19 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 20 | entities | INSERT | 0.16 | `INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestam` |
| 21 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 22 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 23 | — | — | 0.20 | ` ` |
| 24 | — | — | 0.12 | ` ` |
| 25 | — | — | 0.07 | ` ` |
| 26 | — | — | 0.07 | ` ` |
| 27 | — | — | 0.09 | ` ` |
| 28 | — | — | 0.03 | ` ` |
| 29 | — | — | 0.04 | ` ` |
| 30 | — | — | 0.01 | ` ` |
| 31 | — | — | 0.02 | ` ` |
| 32 | — | — | 0.01 | ` ` |
| 33 | — | — | 0.04 | ` ` |
| 34 | — | — | 0.01 | ` ` |
| 35 | — | — | 0.02 | ` ` |
| 36 | — | — | 0.00 | ` ` |
| 37 | — | — | 0.02 | ` ` |
| 38 | — | — | 0.06 | ` ` |
| 39 | — | — | 0.01 | ` ` |
| 40 | — | — | 0.04 | ` ` |
| 41 | — | — | 0.04 | ` ` |
| 42 | — | — | 0.01 | ` ` |
| 43 | — | — | 0.02 | ` ` |
| 44 | — | — | 0.04 | ` ` |
| 45 | — | — | 0.03 | ` ` |

| # | Method | Path | ms |
|---|---|---|---|
| 0 |  | `/data-catalog-bucket/apiprofile1787201504_cat/probe_ns/probe_tbl2/metadata/00000-a8c14702-97e6-467b-b688-9ba4b0967c33.metadata.json` | 4.13 |

### `iceberg.stage_create_table`

- `POST /v1/{cat}/namespaces/{ns}/tables[stage]` → **200**
- wall 52 ms · 38 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, nodes

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.10 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 6.66 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.13 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.13 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 12 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 13 | — | — | 0.19 | ` ` |
| 14 | — | — | 0.06 | ` ` |
| 15 | — | — | 0.05 | ` ` |
| 16 | — | — | 0.06 | ` ` |
| 17 | — | — | 0.16 | ` ` |
| 18 | — | — | 0.04 | ` ` |
| 19 | — | — | 0.06 | ` ` |
| 20 | — | — | 0.07 | ` ` |
| 21 | — | — | 0.09 | ` ` |
| 22 | — | — | 0.05 | ` ` |
| 23 | — | — | 0.05 | ` ` |
| 24 | — | — | 0.02 | ` ` |
| 25 | — | — | 0.02 | ` ` |
| 26 | — | SELECT | 0.33 | `SELECT repmgr.set_upstream_last_seen(1001)` |
| 27 | — | SELECT | 0.11 | `SELECT TRUE` |
| 28 | — | SELECT | 0.11 | `SELECT repmgr.get_local_node_id()` |
| 29 | nodes | SELECT | 0.15 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 30 | — | SELECT | 0.08 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 31 | — | SELECT | 0.16 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 32 | — | SELECT | 0.24 | `SELECT TRUE` |
| 33 | — | SELECT | 0.13 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 34 | — | SELECT | 0.70 | `SELECT repmgr.set_upstream_last_seen(1001)` |
| 35 | — | SELECT | 0.24 | `SELECT TRUE` |
| 36 | — | SELECT | 0.69 | `SELECT repmgr.get_local_node_id()` |
| 37 | nodes | SELECT | 0.43 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |

### `iceberg.commit_table`

- `POST /v1/{cat}/namespaces/{ns}/tables/{tbl}` → **200**
- wall 78 ms · 30 statements · 3 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.14 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.10 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 4.15 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.12 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.16 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | entities | SELECT | 0.11 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | SELECT | 0.11 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | entities | UPDATE | 0.12 | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |
| 11 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 12 | — | — | 0.18 | ` ` |
| 13 | — | — | 0.09 | ` ` |
| 14 | — | — | 0.03 | ` ` |
| 15 | — | — | 0.03 | ` ` |
| 16 | — | — | 0.06 | ` ` |
| 17 | — | — | 0.09 | ` ` |
| 18 | — | — | 0.04 | ` ` |
| 19 | — | — | 0.03 | ` ` |
| 20 | — | — | 0.07 | ` ` |
| 21 | — | — | 0.05 | ` ` |
| 22 | — | — | 0.02 | ` ` |
| 23 | — | — | 0.08 | ` ` |
| 24 | — | SET | 0.40 | `SET application_name TO 'psql'` |
| 25 | — | SELECT | 0.66 | `SELECT 1` |
| 26 | — | — | 0.66 | `DISCARD ALL` |
| 27 | — | SET | 0.16 | `SET application_name TO 'psql'` |
| 28 | — | — | 0.10 | `DISCARD ALL` |
| 29 | — | SET | 0.16 | `SET application_name TO 'psql'` |

| # | Method | Path | ms |
|---|---|---|---|
| 0 |  | `/data-catalog-bucket/apiprofile1787201504_cat/probe_ns/probe_tbl/metadata/00000-53ffa6cb-ede3-4852-872b-0ec48f3afe70.metadata.json` | 1.49 |
| 1 |  | `/data-catalog-bucket/apiprofile1787201504_cat/probe_ns/probe_tbl/metadata/00001-e7fcc1c1-92b1-43d9-a349-05f55cc29874.metadata.json` | 7.00 |
| 2 |  | `/data-catalog-bucket/apiprofile1787201504_cat/probe_ns/probe_tbl/metadata/00000-53ffa6cb-ede3-4852-872b-0ec48f3afe70.metadata.json` | 1.34 |

### `iceberg.rename_table`

- `POST /v1/{cat}/tables/rename` → **200**
- wall 31 ms · 26 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.16 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 2.18 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | grant_records | SELECT | 0.02 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 8 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 12 | entities | UPDATE | 0.18 | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |
| 13 | — | — | 0.14 | ` ` |
| 14 | — | — | 0.06 | ` ` |
| 15 | — | — | 0.01 | ` ` |
| 16 | — | — | 0.01 | ` ` |
| 17 | — | — | 0.03 | ` ` |
| 18 | — | — | 0.02 | ` ` |
| 19 | — | — | 0.02 | ` ` |
| 20 | — | — | 0.01 | ` ` |
| 21 | — | — | 0.01 | ` ` |
| 22 | — | — | 0.02 | ` ` |
| 23 | — | — | 0.03 | ` ` |
| 24 | — | — | 0.02 | ` ` |
| 25 | — | — | 0.01 | ` ` |

### `iceberg.report_metrics`

- `POST /v1/{cat}/.../tables/{tbl}/metrics` → **204**
- wall 9 ms · 12 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 2.04 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | — | — | 0.04 | ` ` |
| 7 | — | — | 0.03 | ` ` |
| 8 | — | — | 0.01 | ` ` |
| 9 | — | — | 0.02 | ` ` |
| 10 | — | — | 0.01 | ` ` |
| 11 | — | — | 0.01 | ` ` |

### `iceberg.load_table[missing]`

- `GET /v1/{cat}/.../tables/{missing}` → **404**
- wall 32 ms · 16 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.24 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 4.66 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.10 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.18 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | — | — | 0.14 | ` ` |
| 9 | — | — | 0.07 | ` ` |
| 10 | — | — | 0.09 | ` ` |
| 11 | — | — | 0.06 | ` ` |
| 12 | — | — | 0.04 | ` ` |
| 13 | — | — | 0.10 | ` ` |
| 14 | — | — | 0.20 | ` ` |
| 15 | — | — | 0.04 | ` ` |

### `iceberg.drop_table`

- `DELETE /v1/{cat}/namespaces/{ns}/tables/{tbl}` → **204**
- wall 60 ms · 87 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, nodes, pg_stat_replication, policy_mapping_record

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.17 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 2.68 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.48 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | grant_records | SELECT | 0.02 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 8 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | entities | DELETE | — | `DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?` |
| 11 | grant_records | SELECT | 0.04 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 12 | grant_records | DELETE | 3.39 | `DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (
    (grantee_id = ? AND grantee_catalog_id = ?) OR
    (securable_id = ? AND securable_catalog_id = ?)
) AND realm_id = ?` |
| 13 | policy_mapping_record | SELECT | 0.01 | `SELECT target_catalog_id, target_id, policy_type_code, policy_catalog_id, policy_id, parameters FROM POLARIS_SCHEMA.POLICY_MAPPING_RECORD WHERE realm_id = ? AND target_id = ? AND t` |
| 14 | policy_mapping_record | DELETE | 0.02 | `DELETE FROM POLARIS_SCHEMA.POLICY_MAPPING_RECORD WHERE target_catalog_id = ? AND target_id = ? AND realm_id = ?` |
| 15 | — | — | 0.10 | ` ` |
| 16 | — | — | 0.17 | ` ` |
| 17 | — | — | 0.03 | ` ` |
| 18 | — | — | 0.02 | ` ` |
| 19 | — | — | 0.04 | ` ` |
| 20 | — | — | 0.08 | ` ` |
| 21 | — | — | 0.02 | ` ` |
| 22 | — | — | 0.01 | ` ` |
| 23 | — | — | 0.02 | ` ` |
| 24 | — | — | 0.04 | ` ` |
| 25 | — | — | 0.06 | ` ` |
| 26 | — | — | 0.06 | ` ` |
| 27 | — | — | 0.01 | ` ` |
| 28 | — | — | 0.02 | ` ` |
| 29 | — | — | 0.01 | ` ` |
| 30 | — | SET | 0.10 | `SET synchronous_commit TO 'local'` |
| 31 | — | SELECT | 0.17 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 32 | — | SELECT | 0.09 | `SELECT repmgr.get_repmgrd_pid()` |
| 33 | — | SELECT | 0.04 | `SELECT repmgr.repmgrd_is_running()` |
| 34 | — | SELECT | 0.06 | `SELECT repmgr.repmgrd_is_paused()` |
| 35 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 36 | — | SELECT | 0.16 | `SELECT paused.wal_replay_paused  AND pg_catalog.pg_last_wal_replay_lsn() < pg_catalog.pg_last_wal_receive_lsn()  FROM (SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE     ` |
| 37 | — | SELECT | 0.04 | `SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE    THEN -1    ELSE repmgr.get_upstream_last_seen()  END AS upstream_last_seen` |
| 38 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 39 | nodes | SELECT | 0.50 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, un.node_name AS upstream_node_name,` |
| 40 | — | SELECT | 0.03 | `SELECT paused.wal_replay_paused  AND pg_catalog.pg_last_wal_replay_lsn() < pg_catalog.pg_last_wal_receive_lsn()  FROM (SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE     ` |
| 41 | nodes | SELECT | 0.04 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 42 | — | SELECT | 0.10 | `SELECT repmgr.set_upstream_last_seen(1001)` |
| 43 | — | SELECT | 0.06 | `SELECT TRUE` |
| 44 | — | SELECT | 0.09 | `SELECT repmgr.get_local_node_id()` |
| 45 | nodes | SELECT | 0.19 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 46 | entities | DELETE | 0.14 | `DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = $1 AND catalog_id = $2 AND id = $3 (grantee_id = $1 AND grantee_catalog_id = $2) OR (securable_id = $3 AND securable_catalog_id` |
| 47 | — | SET | 0.17 | `SET synchronous_commit TO 'local'` |
| 48 | nodes | SELECT | 0.67 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 49 | pg_stat_replication | SELECT | 2.13 | `SELECT pg_catalog.current_setting('max_wal_senders')::INT AS max_wal_senders,         (SELECT pg_catalog.count(*) FROM pg_catalog.pg_stat_replication) AS attached_wal_receivers,   ` |
| 50 | — | SELECT | 0.04 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 51 | — | SET | 0.10 | `SET synchronous_commit TO 'local'` |
| 52 | nodes | SELECT | 0.81 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, un.node_name AS upstream_node_name,` |
| 53 | — | SET | 0.11 | `SET synchronous_commit TO 'local'` |
| 54 | pg_stat_replication | SELECT | 1.23 | `SELECT pid, state    FROM pg_catalog.pg_stat_replication   WHERE application_name = 'benchmarks-postgresql-postgresql-ha-postgresql-0'` |
| 55 | — | SET | 0.06 | `SET synchronous_commit TO 'local'` |
| 56 | — | SELECT | 0.14 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 57 | — | SELECT | 0.06 | `SELECT repmgr.get_repmgrd_pid()` |
| 58 | — | SELECT | 0.04 | `SELECT repmgr.repmgrd_is_running()` |
| 59 | — | SELECT | 0.02 | `SELECT repmgr.repmgrd_is_paused()` |
| 60 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 61 | — | SELECT | 0.04 | `SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE    THEN -1    ELSE repmgr.get_upstream_last_seen()  END AS upstream_last_seen` |
| 62 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 63 | nodes | SELECT | 0.70 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, un.node_name AS upstream_node_name,` |
| 64 | — | SET | 0.10 | `SET synchronous_commit TO 'local'` |
| 65 | pg_stat_replication | SELECT | 1.23 | `SELECT pid, state    FROM pg_catalog.pg_stat_replication   WHERE application_name = 'benchmarks-postgresql-postgresql-ha-postgresql-2'` |
| 66 | — | SELECT | 0.04 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 67 | — | SELECT | 0.05 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 68 | — | SELECT | 0.14 | `SELECT TRUE` |
| 69 | nodes | SELECT | 0.51 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser,            n.slot_name, n.location, n.priority, n.active, n.config_file,            '' AS upstrea` |
| 70 | — | SELECT | 0.03 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 71 | — | SET | 0.08 | `SET synchronous_commit TO 'local'` |
| 72 | — | SELECT | 0.10 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 73 | — | SELECT | 0.04 | `SELECT repmgr.get_repmgrd_pid()` |
| 74 | — | SELECT | 0.03 | `SELECT repmgr.repmgrd_is_running()` |
| 75 | — | SELECT | 0.02 | `SELECT repmgr.repmgrd_is_paused()` |
| 76 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 77 | — | SELECT | 0.10 | `SELECT paused.wal_replay_paused  AND pg_catalog.pg_last_wal_replay_lsn() < pg_catalog.pg_last_wal_receive_lsn()  FROM (SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE     ` |
| 78 | — | SELECT | 0.03 | `SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE    THEN -1    ELSE repmgr.get_upstream_last_seen()  END AS upstream_last_seen` |
| 79 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 80 | nodes | SELECT | 0.41 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, un.node_name AS upstream_node_name,` |
| 81 | — | SELECT | 0.03 | `SELECT paused.wal_replay_paused  AND pg_catalog.pg_last_wal_replay_lsn() < pg_catalog.pg_last_wal_receive_lsn()  FROM (SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE     ` |
| 82 | nodes | SELECT | 0.04 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 83 | — | SELECT | 0.18 | `SELECT repmgr.set_upstream_last_seen(1001)` |
| 84 | — | SELECT | 0.03 | `SELECT TRUE` |
| 85 | — | SELECT | 0.08 | `SELECT repmgr.get_local_node_id()` |
| 86 | nodes | SELECT | 0.10 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |

### `iceberg.create_view`

- `POST /v1/{cat}/namespaces/{ns}/views` → **500**
- wall 47 ms · 42 statements · 1 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.10 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 3.49 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 12 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 13 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 14 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND realm_id = ? AND type_code = ? AND catalog_id = ?` |
| 15 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND realm_id = ? AND type_code = ? AND catalog_id = ?` |
| 16 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 17 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 18 | entities | INSERT | 0.08 | `INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestam` |
| 19 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 20 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 21 | — | — | 0.13 | ` ` |
| 22 | — | — | 0.15 | ` ` |
| 23 | — | — | 0.04 | ` ` |
| 24 | — | — | 0.04 | ` ` |
| 25 | — | — | 0.06 | ` ` |
| 26 | — | — | 0.03 | ` ` |
| 27 | — | — | 0.03 | ` ` |
| 28 | — | — | 0.01 | ` ` |
| 29 | — | — | 0.02 | ` ` |
| 30 | — | — | 0.02 | ` ` |
| 31 | — | — | 0.01 | ` ` |
| 32 | — | — | 0.01 | ` ` |
| 33 | — | — | 0.03 | ` ` |
| 34 | — | — | 0.01 | ` ` |
| 35 | — | — | 0.01 | ` ` |
| 36 | — | — | 0.01 | ` ` |
| 37 | — | — | 0.01 | ` ` |
| 38 | — | — | 0.03 | ` ` |
| 39 | — | — | 0.05 | ` ` |
| 40 | — | — | 0.02 | ` ` |
| 41 | — | — | 0.03 | ` ` |

| # | Method | Path | ms |
|---|---|---|---|
| 0 |  | `/data-catalog-bucket/apiprofile1787201504_cat/probe_ns/probe_view/metadata/00000-06590ed6-b3b7-44f0-a6fd-f5e9e70c3d6d.gz.metadata.json` | 3.12 |

### `iceberg.list_views`

- `GET /v1/{cat}/namespaces/{ns}/views` → **200**
- wall 15 ms · 60 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, nodes, pg_stat_replication

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 2.35 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.31 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND sub_type_code = ? AND realm_id = ? AND parent_id = ? AND type` |
| 8 | — | — | 0.05 | ` ` |
| 9 | — | — | 0.04 | ` ` |
| 10 | — | — | 0.01 | ` ` |
| 11 | — | — | 0.01 | ` ` |
| 12 | — | — | 0.02 | ` ` |
| 13 | — | — | 0.02 | ` ` |
| 14 | — | — | 0.02 | ` ` |
| 15 | — | — | 0.03 | ` ` |
| 16 | — | SET | 0.05 | `SET synchronous_commit TO 'local'` |
| 17 | — | SELECT | 0.14 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 18 | — | SELECT | 0.09 | `SELECT repmgr.get_repmgrd_pid()` |
| 19 | — | SELECT | 0.03 | `SELECT repmgr.repmgrd_is_running()` |
| 20 | — | SELECT | 0.02 | `SELECT repmgr.repmgrd_is_paused()` |
| 21 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 22 | — | SELECT | 0.21 | `SELECT paused.wal_replay_paused  AND pg_catalog.pg_last_wal_replay_lsn() < pg_catalog.pg_last_wal_receive_lsn()  FROM (SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE     ` |
| 23 | — | SELECT | 0.03 | `SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE    THEN -1    ELSE repmgr.get_upstream_last_seen()  END AS upstream_last_seen` |
| 24 | — | SELECT | 0.02 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 25 | nodes | SELECT | 0.39 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, un.node_name AS upstream_node_name,` |
| 26 | — | SELECT | 0.02 | `SELECT paused.wal_replay_paused  AND pg_catalog.pg_last_wal_replay_lsn() < pg_catalog.pg_last_wal_receive_lsn()  FROM (SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE     ` |
| 27 | nodes | SELECT | 0.04 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 28 | — | SELECT | 0.28 | `SELECT 1` |
| 29 | — | SET | 0.15 | `SET synchronous_commit TO 'local'` |
| 30 | nodes | SELECT | 0.47 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 31 | pg_stat_replication | SELECT | 1.32 | `SELECT pg_catalog.current_setting('max_wal_senders')::INT AS max_wal_senders,         (SELECT pg_catalog.count(*) FROM pg_catalog.pg_stat_replication) AS attached_wal_receivers,   ` |
| 32 | — | SELECT | 0.02 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 33 | — | SET | 0.09 | `SET synchronous_commit TO 'local'` |
| 34 | nodes | SELECT | 0.57 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, un.node_name AS upstream_node_name,` |
| 35 | — | SET | 0.05 | `SET synchronous_commit TO 'local'` |
| 36 | pg_stat_replication | SELECT | 1.01 | `SELECT pid, state    FROM pg_catalog.pg_stat_replication   WHERE application_name = 'benchmarks-postgresql-postgresql-ha-postgresql-0'` |
| 37 | — | SET | 0.10 | `SET synchronous_commit TO 'local'` |
| 38 | — | SELECT | 0.16 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 39 | — | SELECT | 0.07 | `SELECT repmgr.get_repmgrd_pid()` |
| 40 | — | SELECT | 0.03 | `SELECT repmgr.repmgrd_is_running()` |
| 41 | — | SELECT | 0.02 | `SELECT repmgr.repmgrd_is_paused()` |
| 42 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 43 | — | SELECT | 0.04 | `SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE    THEN -1    ELSE repmgr.get_upstream_last_seen()  END AS upstream_last_seen` |
| 44 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 45 | nodes | SELECT | 0.48 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, un.node_name AS upstream_node_name,` |
| 46 | — | SET | 0.07 | `SET synchronous_commit TO 'local'` |
| 47 | pg_stat_replication | SELECT | 1.10 | `SELECT pid, state    FROM pg_catalog.pg_stat_replication   WHERE application_name = 'benchmarks-postgresql-postgresql-ha-postgresql-2'` |
| 48 | — | SET | 0.06 | `SET synchronous_commit TO 'local'` |
| 49 | — | SELECT | 0.11 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 50 | — | SELECT | 0.04 | `SELECT repmgr.get_repmgrd_pid()` |
| 51 | — | SELECT | 0.02 | `SELECT repmgr.repmgrd_is_running()` |
| 52 | — | SELECT | 0.02 | `SELECT repmgr.repmgrd_is_paused()` |
| 53 | — | SELECT | 0.02 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 54 | — | SELECT | 0.14 | `SELECT paused.wal_replay_paused  AND pg_catalog.pg_last_wal_replay_lsn() < pg_catalog.pg_last_wal_receive_lsn()  FROM (SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE     ` |
| 55 | — | SELECT | 0.04 | `SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE    THEN -1    ELSE repmgr.get_upstream_last_seen()  END AS upstream_last_seen` |
| 56 | — | SELECT | 0.02 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 57 | nodes | SELECT | 0.39 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, un.node_name AS upstream_node_name,` |
| 58 | — | SELECT | 0.03 | `SELECT paused.wal_replay_paused  AND pg_catalog.pg_last_wal_replay_lsn() < pg_catalog.pg_last_wal_receive_lsn()  FROM (SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE     ` |
| 59 | nodes | SELECT | 0.04 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |

### `iceberg.load_view`

- `GET /v1/{cat}/namespaces/{ns}/views/{view}` → **200**
- wall 37 ms · 30 statements · 2 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 2.07 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | grant_records | SELECT | 0.02 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 8 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 12 | — | — | 0.12 | ` ` |
| 13 | — | — | 0.02 | ` ` |
| 14 | — | — | 0.01 | ` ` |
| 15 | — | — | 0.01 | ` ` |
| 16 | — | — | 0.01 | ` ` |
| 17 | — | — | 0.02 | ` ` |
| 18 | — | — | 0.07 | ` ` |
| 19 | — | — | 0.01 | ` ` |
| 20 | — | — | 0.01 | ` ` |
| 21 | — | — | 0.01 | ` ` |
| 22 | — | — | 0.02 | ` ` |
| 23 | — | — | 0.06 | ` ` |
| 24 | — | SET | 0.10 | `SET application_name TO 'psql'` |
| 25 | — | SET | 0.06 | `SET application_name TO 'psql'` |
| 26 | — | — | 0.04 | `DISCARD ALL` |
| 27 | — | SET | 0.03 | `SET application_name TO 'psql'` |
| 28 | — | SELECT | 0.11 | `SELECT 1` |
| 29 | — | — | 0.03 | `DISCARD ALL` |

| # | Method | Path | ms |
|---|---|---|---|
| 0 |  | `/data-catalog-bucket/apiprofile1787201504_cat/probe_ns/probe_view/metadata/00000-06590ed6-b3b7-44f0-a6fd-f5e9e70c3d6d.gz.metadata.json` | 1.10 |
| 1 |  | `/data-catalog-bucket/apiprofile1787201504_cat/probe_ns/probe_view/metadata/00000-06590ed6-b3b7-44f0-a6fd-f5e9e70c3d6d.gz.metadata.json` | 1.04 |

### `iceberg.head_view`

- `HEAD /v1/{cat}/namespaces/{ns}/views/{view}` → **204**
- wall 29 ms · 30 statements · 2 object ops · cache: MISS
- tables: entities, grant_records, nodes

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.39 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.42 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 1.80 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | — | — | 0.16 | ` ` |
| 10 | — | — | 0.17 | ` ` |
| 11 | — | — | 0.03 | ` ` |
| 12 | — | — | 0.03 | ` ` |
| 13 | — | — | 0.02 | ` ` |
| 14 | — | — | 0.04 | ` ` |
| 15 | — | — | 0.02 | ` ` |
| 16 | — | — | 0.03 | ` ` |
| 17 | — | — | 0.02 | ` ` |
| 18 | — | SELECT | 0.31 | `SELECT repmgr.set_upstream_last_seen(1001)` |
| 19 | — | SELECT | 0.07 | `SELECT TRUE` |
| 20 | — | SELECT | 0.16 | `SELECT repmgr.get_local_node_id()` |
| 21 | nodes | SELECT | 0.12 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 22 | — | SELECT | 0.40 | `SELECT TRUE` |
| 23 | — | SELECT | 0.07 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 24 | — | SELECT | 0.06 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 25 | — | SELECT | 0.10 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 26 | — | SELECT | 0.29 | `SELECT repmgr.set_upstream_last_seen(1001)` |
| 27 | — | SELECT | 0.04 | `SELECT TRUE` |
| 28 | — | SELECT | 0.09 | `SELECT repmgr.get_local_node_id()` |
| 29 | nodes | SELECT | 0.16 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |

| # | Method | Path | ms |
|---|---|---|---|
| 0 |  | `/data-catalog-bucket/apiprofile1787201504_cat/probe_ns/probe_view/metadata/00000-06590ed6-b3b7-44f0-a6fd-f5e9e70c3d6d.gz.metadata.json` | 1.11 |
| 1 |  | `/data-catalog-bucket/apiprofile1787201504_cat/probe_ns/probe_view/metadata/00000-06590ed6-b3b7-44f0-a6fd-f5e9e70c3d6d.gz.metadata.json` | 1.08 |

### `iceberg.rename_view`

- `POST /v1/{cat}/views/rename` → **204**
- wall 18 ms · 22 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 2.56 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | entities | UPDATE | 0.11 | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |
| 11 | — | — | 0.08 | ` ` |
| 12 | — | — | 0.06 | ` ` |
| 13 | — | — | 0.02 | ` ` |
| 14 | — | — | 0.01 | ` ` |
| 15 | — | — | 0.07 | ` ` |
| 16 | — | — | 0.02 | ` ` |
| 17 | — | — | 0.02 | ` ` |
| 18 | — | — | 0.02 | ` ` |
| 19 | — | — | 0.02 | ` ` |
| 20 | — | — | 0.01 | ` ` |
| 21 | — | — | 0.01 | ` ` |

### `iceberg.drop_view`

- `DELETE /v1/{cat}/namespaces/{ns}/views/{view}` → **204**
- wall 46 ms · 33 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, nodes, pg_stat_replication

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.15 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.19 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 4.96 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | grant_records | SELECT | 0.03 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 8 | entities | SELECT | 0.10 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | entities | DELETE | — | `DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?` |
| 11 | grant_records | SELECT | 0.02 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 12 | grant_records | DELETE | 2.51 | `DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (
    (grantee_id = ? AND grantee_catalog_id = ?) OR
    (securable_id = ? AND securable_catalog_id = ?)
) AND realm_id = ?` |
| 13 | entities | INSERT | 0.16 | `INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestam` |
| 14 | — | — | 0.18 | ` ` |
| 15 | — | — | 0.10 | ` ` |
| 16 | — | — | 0.07 | ` ` |
| 17 | — | — | 0.07 | ` ` |
| 18 | — | — | 0.04 | ` ` |
| 19 | — | — | 0.06 | ` ` |
| 20 | — | — | 0.06 | ` ` |
| 21 | — | — | 0.01 | ` ` |
| 22 | — | — | 0.01 | ` ` |
| 23 | — | — | 0.01 | ` ` |
| 24 | — | — | 0.00 | ` ` |
| 25 | — | — | 0.04 | ` ` |
| 26 | — | — | 0.01 | ` ` |
| 27 | — | — | 0.03 | ` ` |
| 28 | — | SET | 0.21 | `SET synchronous_commit TO 'local'` |
| 29 | nodes | SELECT | 0.64 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 30 | pg_stat_replication | SELECT | 1.61 | `SELECT pg_catalog.current_setting('max_wal_senders')::INT AS max_wal_senders,         (SELECT pg_catalog.count(*) FROM pg_catalog.pg_stat_replication) AS attached_wal_receivers,   ` |
| 31 | — | SELECT | 0.04 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 32 | entities | DELETE | 0.07 | `DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = $1 AND catalog_id = $2 AND id = $3 (grantee_id = $1 AND grantee_catalog_id = $2) OR (securable_id = $3 AND securable_catalog_id` |

### `mgmt.list_catalogs`

- `GET /v1/catalogs` → **200**
- wall 46 ms · 16 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 1.85 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 3.29 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | — | — | 0.07 | ` ` |
| 9 | — | — | 0.02 | ` ` |
| 10 | — | — | 0.04 | ` ` |
| 11 | — | — | 0.02 | ` ` |
| 12 | — | — | 0.01 | ` ` |
| 13 | — | — | 0.03 | ` ` |
| 14 | — | — | 0.03 | ` ` |
| 15 | — | — | 0.03 | ` ` |

### `mgmt.get_catalog`

- `GET /v1/catalogs/{cat}` → **200**
- wall 29 ms · 14 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.43 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.11 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 5.56 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.16 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.17 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | — | — | 0.31 | ` ` |
| 8 | — | — | 0.06 | ` ` |
| 9 | — | — | 0.03 | ` ` |
| 10 | — | — | 0.04 | ` ` |
| 11 | — | — | 0.06 | ` ` |
| 12 | — | — | 0.04 | ` ` |
| 13 | — | — | 0.05 | ` ` |

### `mgmt.create_principal`

- `POST /v1/principals` → **201**
- wall 35 ms · 23 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, principal_authentication_data

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 2.62 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | principal_authentication_data | SELECT | 0.02 | `SELECT principal_id, principal_client_id, main_secret_hash, secondary_secret_hash, secret_salt FROM POLARIS_SCHEMA.PRINCIPAL_AUTHENTICATION_DATA WHERE realm_id = ? AND principal_cl` |
| 9 | principal_authentication_data | INSERT | 0.31 | `INSERT INTO POLARIS_SCHEMA.PRINCIPAL_AUTHENTICATION_DATA (principal_id, principal_client_id, main_secret_hash, secondary_secret_hash, secret_salt, realm_id) VALUES (?, ?, ?, ?, ?, ` |
| 10 | entities | INSERT | 0.17 | `INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestam` |
| 11 | — | — | 0.19 | ` ` |
| 12 | — | — | 0.04 | ` ` |
| 13 | — | — | 0.02 | ` ` |
| 14 | — | — | 0.03 | ` ` |
| 15 | — | — | 0.05 | ` ` |
| 16 | — | — | 0.06 | ` ` |
| 17 | — | — | 0.01 | ` ` |
| 18 | — | — | 0.03 | ` ` |
| 19 | — | — | 0.03 | ` ` |
| 20 | — | — | 0.02 | ` ` |
| 21 | — | — | 0.07 | ` ` |
| 22 | — | — | 0.23 | ` ` |

### `mgmt.get_principal`

- `GET /v1/principals/{p}` → **200**
- wall 22 ms · 20 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.17 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 3.20 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | grant_records | SELECT | 2.31 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 8 | grant_records | SELECT | 0.03 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 9 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | — | — | 0.20 | ` ` |
| 11 | — | — | 0.05 | ` ` |
| 12 | — | — | 0.03 | ` ` |
| 13 | — | — | 0.02 | ` ` |
| 14 | — | — | 0.03 | ` ` |
| 15 | — | — | 0.04 | ` ` |
| 16 | — | — | 0.04 | ` ` |
| 17 | — | — | 0.03 | ` ` |
| 18 | — | — | 0.05 | ` ` |
| 19 | — | — | 0.02 | ` ` |

### `mgmt.list_principals`

- `GET /v1/principals` → **200**
- wall 58 ms · 29 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, nodes

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.32 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.10 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.91 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 4.91 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.11 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 5.50 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | — | — | 0.13 | ` ` |
| 9 | — | — | 0.21 | ` ` |
| 10 | — | — | 0.19 | ` ` |
| 11 | — | — | 0.09 | ` ` |
| 12 | — | — | 0.05 | ` ` |
| 13 | — | — | 0.02 | ` ` |
| 14 | — | — | 0.20 | ` ` |
| 15 | — | — | 0.08 | ` ` |
| 16 | — | SELECT | 0.16 | `SELECT repmgr.set_upstream_last_seen(1001)` |
| 17 | — | SELECT | 0.03 | `SELECT TRUE` |
| 18 | — | SELECT | 0.08 | `SELECT repmgr.get_local_node_id()` |
| 19 | nodes | SELECT | 0.16 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 20 | — | SELECT | 0.32 | `SELECT TRUE` |
| 21 | nodes | SELECT | 0.92 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser,            n.slot_name, n.location, n.priority, n.active, n.config_file,            '' AS upstrea` |
| 22 | — | SELECT | 0.16 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 23 | — | SELECT | 0.16 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 24 | — | SELECT | 0.37 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 25 | — | SELECT | 0.32 | `SELECT repmgr.set_upstream_last_seen(1001)` |
| 26 | — | SELECT | 0.06 | `SELECT TRUE` |
| 27 | — | SELECT | 0.22 | `SELECT repmgr.get_local_node_id()` |
| 28 | nodes | SELECT | 0.26 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |

### `mgmt.create_principal_role`

- `POST /v1/principal-roles` → **201**
- wall 67 ms · 21 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, nodes, pg_stat_replication

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 2.27 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | INSERT | 0.14 | `INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestam` |
| 8 | — | — | 0.12 | ` ` |
| 9 | — | — | 0.03 | ` ` |
| 10 | — | — | 0.61 | ` ` |
| 11 | — | — | 0.01 | ` ` |
| 12 | — | — | 0.10 | ` ` |
| 13 | — | — | 0.05 | ` ` |
| 14 | — | — | 0.02 | ` ` |
| 15 | — | — | 0.02 | ` ` |
| 16 | — | SELECT | 0.25 | `SELECT 1` |
| 17 | — | SET | 0.14 | `SET synchronous_commit TO 'local'` |
| 18 | nodes | SELECT | 0.75 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 19 | pg_stat_replication | SELECT | 1.60 | `SELECT pg_catalog.current_setting('max_wal_senders')::INT AS max_wal_senders,         (SELECT pg_catalog.count(*) FROM pg_catalog.pg_stat_replication) AS attached_wal_receivers,   ` |
| 20 | — | SELECT | 0.02 | `SELECT pg_catalog.pg_is_in_recovery()` |

### `mgmt.get_principal_role`

- `GET /v1/principal-roles/{r}` → **200**
- wall 32 ms · 21 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.13 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 5.67 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.10 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | grant_records | SELECT | 2.83 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 8 | grant_records | SELECT | 0.06 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 9 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | — | — | 0.14 | ` ` |
| 11 | — | — | 0.06 | ` ` |
| 12 | — | — | 0.09 | ` ` |
| 13 | — | — | 0.08 | ` ` |
| 14 | — | — | 0.08 | ` ` |
| 15 | — | — | 0.08 | ` ` |
| 16 | — | — | 0.05 | ` ` |
| 17 | — | — | 0.08 | ` ` |
| 18 | — | — | 0.06 | ` ` |
| 19 | — | — | 0.01 | ` ` |
| 20 | — | SELECT | 0.16 | `SELECT 1` |

### `mgmt.list_principal_roles`

- `GET /v1/principal-roles` → **200**
- wall 33 ms · 65 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, nodes, pg_stat_replication

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 1.97 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 1.63 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | — | — | 0.08 | ` ` |
| 9 | — | — | 0.01 | ` ` |
| 10 | — | — | 0.01 | ` ` |
| 11 | — | — | 0.01 | ` ` |
| 12 | — | — | 0.01 | ` ` |
| 13 | — | — | 0.03 | ` ` |
| 14 | — | — | 0.04 | ` ` |
| 15 | — | — | 0.01 | ` ` |
| 16 | — | SET | 0.08 | `SET synchronous_commit TO 'local'` |
| 17 | — | SELECT | 0.16 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 18 | — | SELECT | 0.06 | `SELECT repmgr.get_repmgrd_pid()` |
| 19 | — | SELECT | 0.02 | `SELECT repmgr.repmgrd_is_running()` |
| 20 | — | SELECT | 0.03 | `SELECT repmgr.repmgrd_is_paused()` |
| 21 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 22 | — | SELECT | 0.12 | `SELECT paused.wal_replay_paused  AND pg_catalog.pg_last_wal_replay_lsn() < pg_catalog.pg_last_wal_receive_lsn()  FROM (SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE     ` |
| 23 | — | SELECT | 0.03 | `SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE    THEN -1    ELSE repmgr.get_upstream_last_seen()  END AS upstream_last_seen` |
| 24 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 25 | nodes | SELECT | 0.36 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, un.node_name AS upstream_node_name,` |
| 26 | — | SELECT | 0.02 | `SELECT paused.wal_replay_paused  AND pg_catalog.pg_last_wal_replay_lsn() < pg_catalog.pg_last_wal_receive_lsn()  FROM (SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE     ` |
| 27 | nodes | SELECT | 0.03 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 28 | — | SET | 0.12 | `SET application_name TO 'psql'` |
| 29 | — | SET | 0.10 | `SET synchronous_commit TO 'local'` |
| 30 | nodes | SELECT | 0.45 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 31 | pg_stat_replication | SELECT | 1.63 | `SELECT pg_catalog.current_setting('max_wal_senders')::INT AS max_wal_senders,         (SELECT pg_catalog.count(*) FROM pg_catalog.pg_stat_replication) AS attached_wal_receivers,   ` |
| 32 | — | SELECT | 0.03 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 33 | — | SET | 0.11 | `SET synchronous_commit TO 'local'` |
| 34 | nodes | SELECT | 0.67 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, un.node_name AS upstream_node_name,` |
| 35 | — | SET | 0.07 | `SET synchronous_commit TO 'local'` |
| 36 | pg_stat_replication | SELECT | 0.81 | `SELECT pid, state    FROM pg_catalog.pg_stat_replication   WHERE application_name = 'benchmarks-postgresql-postgresql-ha-postgresql-0'` |
| 37 | — | SET | 0.11 | `SET synchronous_commit TO 'local'` |
| 38 | — | SELECT | 0.17 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 39 | — | SELECT | 0.06 | `SELECT repmgr.get_repmgrd_pid()` |
| 40 | — | SELECT | 0.03 | `SELECT repmgr.repmgrd_is_running()` |
| 41 | — | SELECT | 0.03 | `SELECT repmgr.repmgrd_is_paused()` |
| 42 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 43 | — | SELECT | 0.03 | `SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE    THEN -1    ELSE repmgr.get_upstream_last_seen()  END AS upstream_last_seen` |
| 44 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 45 | nodes | SELECT | 0.47 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, un.node_name AS upstream_node_name,` |
| 46 | — | SET | 0.06 | `SET synchronous_commit TO 'local'` |
| 47 | pg_stat_replication | SELECT | 0.93 | `SELECT pid, state    FROM pg_catalog.pg_stat_replication   WHERE application_name = 'benchmarks-postgresql-postgresql-ha-postgresql-2'` |
| 48 | — | SET | 0.05 | `SET application_name TO 'psql'` |
| 49 | — | — | 0.07 | `DISCARD ALL` |
| 50 | — | SET | 0.08 | `SET synchronous_commit TO 'local'` |
| 51 | — | SELECT | 0.10 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 52 | — | SELECT | 0.05 | `SELECT repmgr.get_repmgrd_pid()` |
| 53 | — | SELECT | 0.03 | `SELECT repmgr.repmgrd_is_running()` |
| 54 | — | SELECT | 0.02 | `SELECT repmgr.repmgrd_is_paused()` |
| 55 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 56 | — | SELECT | 0.08 | `SELECT paused.wal_replay_paused  AND pg_catalog.pg_last_wal_replay_lsn() < pg_catalog.pg_last_wal_receive_lsn()  FROM (SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE     ` |
| 57 | — | SELECT | 0.02 | `SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE    THEN -1    ELSE repmgr.get_upstream_last_seen()  END AS upstream_last_seen` |
| 58 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 59 | nodes | SELECT | 0.29 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, un.node_name AS upstream_node_name,` |
| 60 | — | SELECT | 0.02 | `SELECT paused.wal_replay_paused  AND pg_catalog.pg_last_wal_replay_lsn() < pg_catalog.pg_last_wal_receive_lsn()  FROM (SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE     ` |
| 61 | nodes | SELECT | 0.03 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 62 | — | SET | 0.10 | `SET application_name TO 'psql'` |
| 63 | — | SELECT | 0.14 | `SELECT 1` |
| 64 | — | — | 0.09 | `DISCARD ALL` |

### `mgmt.assign_principal_role`

- `PUT /v1/principals/{p}/principal-roles` → **201**
- wall 27 ms · 24 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 1.65 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | grant_records | INSERT | 0.08 | `INSERT INTO POLARIS_SCHEMA.GRANT_RECORDS (securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code, realm_id) VALUES (?, ?, ?, ?, ?, ?)` |
| 8 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | UPDATE | 0.06 | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |
| 10 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | entities | UPDATE | 0.05 | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |
| 12 | — | — | 0.15 | ` ` |
| 13 | — | — | 0.03 | ` ` |
| 14 | — | — | 0.02 | ` ` |
| 15 | — | — | 0.01 | ` ` |
| 16 | — | — | 0.01 | ` ` |
| 17 | — | — | 0.03 | ` ` |
| 18 | — | — | 0.02 | ` ` |
| 19 | — | — | 0.01 | ` ` |
| 20 | — | — | 0.05 | ` ` |
| 21 | — | — | 0.02 | ` ` |
| 22 | — | — | 0.03 | ` ` |
| 23 | — | — | 0.02 | ` ` |

### `mgmt.create_catalog_role`

- `POST /v1/catalogs/{cat}/catalog-roles` → **201**
- wall 35 ms · 23 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, nodes

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.14 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.18 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.25 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 5.52 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.12 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.11 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | INSERT | 0.09 | `INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestam` |
| 8 | — | — | 0.12 | ` ` |
| 9 | — | — | 0.08 | ` ` |
| 10 | — | — | 0.19 | ` ` |
| 11 | — | — | 0.10 | ` ` |
| 12 | — | — | 0.07 | ` ` |
| 13 | — | — | 0.04 | ` ` |
| 14 | — | — | 0.18 | ` ` |
| 15 | — | — | 0.04 | ` ` |
| 16 | — | SELECT | 0.41 | `SELECT TRUE` |
| 17 | — | SELECT | 0.31 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 18 | — | SELECT | 0.16 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 19 | — | SELECT | 0.80 | `SELECT repmgr.set_upstream_last_seen(1001)` |
| 20 | — | SELECT | 0.05 | `SELECT TRUE` |
| 21 | — | SELECT | 0.16 | `SELECT repmgr.get_local_node_id()` |
| 22 | nodes | SELECT | 0.27 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |

### `mgmt.list_catalog_roles`

- `GET /v1/catalogs/{cat}/catalog-roles` → **200**
- wall 17 ms · 21 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, nodes

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 2.46 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | — | — | 0.15 | ` ` |
| 9 | — | SELECT | 0.16 | `SELECT repmgr.set_upstream_last_seen(1001)` |
| 10 | — | SELECT | 0.04 | `SELECT TRUE` |
| 11 | — | — | 0.06 | ` ` |
| 12 | — | — | 0.03 | ` ` |
| 13 | — | — | 0.04 | ` ` |
| 14 | — | SELECT | 0.10 | `SELECT repmgr.get_local_node_id()` |
| 15 | nodes | SELECT | 0.24 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 16 | — | — | 0.03 | ` ` |
| 17 | — | — | 0.03 | ` ` |
| 18 | — | — | 0.02 | ` ` |
| 19 | — | — | 0.02 | ` ` |
| 20 | — | SELECT | 0.09 | `SELECT pg_catalog.pg_is_in_recovery()` |

### `mgmt.assign_catalog_role`

- `PUT /v1/principal-roles/{r}/catalog-roles/{cat}` → **201**
- wall 37 ms · 42 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, nodes, pg_stat_replication

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 1.45 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | grant_records | SELECT | 1.67 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 8 | grant_records | SELECT | 0.02 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 9 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | grant_records | SELECT | 1.31 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 12 | grant_records | SELECT | 0.01 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 13 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 14 | grant_records | INSERT | 0.04 | `INSERT INTO POLARIS_SCHEMA.GRANT_RECORDS (securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code, realm_id) VALUES (?, ?, ?, ?, ?, ?)` |
| 15 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 16 | entities | UPDATE | 0.05 | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |
| 17 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 18 | entities | UPDATE | 0.07 | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |
| 19 | — | — | 0.05 | ` ` |
| 20 | — | — | 0.02 | ` ` |
| 21 | — | — | 0.01 | ` ` |
| 22 | — | — | 0.02 | ` ` |
| 23 | — | — | 0.03 | ` ` |
| 24 | — | — | 0.01 | ` ` |
| 25 | — | — | 0.04 | ` ` |
| 26 | — | — | 0.01 | ` ` |
| 27 | — | — | 0.02 | ` ` |
| 28 | — | — | 0.02 | ` ` |
| 29 | — | — | 0.01 | ` ` |
| 30 | — | — | 0.03 | ` ` |
| 31 | — | — | 0.01 | ` ` |
| 32 | — | — | 0.01 | ` ` |
| 33 | — | — | 0.02 | ` ` |
| 34 | — | — | 0.04 | ` ` |
| 35 | — | — | 0.01 | ` ` |
| 36 | — | — | 0.02 | ` ` |
| 37 | — | — | 0.01 | ` ` |
| 38 | — | SET | 0.07 | `SET synchronous_commit TO 'local'` |
| 39 | nodes | SELECT | 0.33 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 40 | pg_stat_replication | SELECT | 1.00 | `SELECT pg_catalog.current_setting('max_wal_senders')::INT AS max_wal_senders,         (SELECT pg_catalog.count(*) FROM pg_catalog.pg_stat_replication) AS attached_wal_receivers,   ` |
| 41 | — | SELECT | 0.02 | `SELECT pg_catalog.pg_is_in_recovery()` |

### `mgmt.grant_privilege`

- `PUT /v1/catalogs/{cat}/catalog-roles/{cr}/grants` → **201**
- wall 60 ms · 48 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.11 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 4.84 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.10 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.26 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | grant_records | SELECT | 3.13 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 9 | grant_records | SELECT | 0.06 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 10 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | grant_records | SELECT | 2.44 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 12 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 13 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 14 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 15 | grant_records | SELECT | 2.00 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 16 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 17 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 18 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 19 | grant_records | INSERT | 0.06 | `INSERT INTO POLARIS_SCHEMA.GRANT_RECORDS (securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code, realm_id) VALUES (?, ?, ?, ?, ?, ?)` |
| 20 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 21 | entities | UPDATE | 0.09 | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |
| 22 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 23 | entities | UPDATE | 0.11 | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |
| 24 | — | — | 0.11 | ` ` |
| 25 | — | — | 0.10 | ` ` |
| 26 | — | — | 0.07 | ` ` |
| 27 | — | — | 0.04 | ` ` |
| 28 | — | — | 0.06 | ` ` |
| 29 | — | — | 0.04 | ` ` |
| 30 | — | — | 0.07 | ` ` |
| 31 | — | — | 0.06 | ` ` |
| 32 | — | — | 0.03 | ` ` |
| 33 | — | — | 0.04 | ` ` |
| 34 | — | — | 0.05 | ` ` |
| 35 | — | — | 0.01 | ` ` |
| 36 | — | — | 0.06 | ` ` |
| 37 | — | — | 0.03 | ` ` |
| 38 | — | — | 0.03 | ` ` |
| 39 | — | — | 0.02 | ` ` |
| 40 | — | — | 0.03 | ` ` |
| 41 | — | — | 0.03 | ` ` |
| 42 | — | — | 0.03 | ` ` |
| 43 | — | — | 0.01 | ` ` |
| 44 | — | — | 0.05 | ` ` |
| 45 | — | — | 0.02 | ` ` |
| 46 | — | — | 0.01 | ` ` |
| 47 | — | — | 0.01 | ` ` |

### `mgmt.list_grants`

- `GET /v1/catalogs/{cat}/catalog-roles/{cr}/grants` → **200**
- wall 35 ms · 30 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.19 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 3.16 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.20 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | grant_records | SELECT | 0.06 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 9 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | grant_records | SELECT | 1.56 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 11 | grant_records | SELECT | 0.06 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 12 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 13 | grant_records | SELECT | 1.76 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 14 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 15 | — | — | 0.08 | ` ` |
| 16 | — | — | 0.05 | ` ` |
| 17 | — | — | 0.06 | ` ` |
| 18 | — | — | 0.05 | ` ` |
| 19 | — | — | 0.06 | ` ` |
| 20 | — | — | 0.04 | ` ` |
| 21 | — | — | 0.07 | ` ` |
| 22 | — | — | 0.07 | ` ` |
| 23 | — | — | 0.04 | ` ` |
| 24 | — | — | 0.10 | ` ` |
| 25 | — | — | 0.04 | ` ` |
| 26 | — | — | 0.06 | ` ` |
| 27 | — | — | 0.02 | ` ` |
| 28 | — | — | 0.04 | ` ` |
| 29 | — | — | 0.01 | ` ` |

### `mgmt.list_principals_for_principal_role`

- `GET /v1/principal-roles/{r}/principals` → **200**
- wall 19 ms · 26 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 2.24 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | grant_records | SELECT | 2.29 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 9 | grant_records | SELECT | 0.07 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 10 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | grant_records | SELECT | 0.02 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 12 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 13 | — | — | 0.13 | ` ` |
| 14 | — | — | 0.04 | ` ` |
| 15 | — | — | 0.03 | ` ` |
| 16 | — | — | 0.02 | ` ` |
| 17 | — | — | 0.04 | ` ` |
| 18 | — | — | 0.01 | ` ` |
| 19 | — | — | 0.03 | ` ` |
| 20 | — | — | 0.03 | ` ` |
| 21 | — | — | 0.01 | ` ` |
| 22 | — | — | 0.01 | ` ` |
| 23 | — | — | 0.03 | ` ` |
| 24 | — | — | 0.02 | ` ` |
| 25 | — | — | 0.01 | ` ` |

### `mgmt.reset_principal_credentials`

- `POST /v1/principals/{p}/reset` → **200**
- wall 27 ms · 40 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, nodes, principal_authentication_data

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.10 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 2.04 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | grant_records | SELECT | 2.23 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 9 | grant_records | SELECT | 0.03 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 10 | principal_authentication_data | SELECT | 0.02 | `SELECT principal_id, principal_client_id, main_secret_hash, secondary_secret_hash, secret_salt FROM POLARIS_SCHEMA.PRINCIPAL_AUTHENTICATION_DATA WHERE realm_id = ? AND principal_cl` |
| 11 | principal_authentication_data | DELETE | 0.16 | `DELETE FROM POLARIS_SCHEMA.PRINCIPAL_AUTHENTICATION_DATA WHERE realm_id = ? AND principal_id = ? AND principal_client_id = ?` |
| 12 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 13 | principal_authentication_data | INSERT | 0.05 | `INSERT INTO POLARIS_SCHEMA.PRINCIPAL_AUTHENTICATION_DATA (principal_id, principal_client_id, main_secret_hash, secondary_secret_hash, secret_salt, realm_id) VALUES (?, ?, ?, ?, ?, ` |
| 14 | — | — | 0.09 | ` ` |
| 15 | — | — | 0.09 | ` ` |
| 16 | — | — | 0.02 | ` ` |
| 17 | — | — | 0.02 | ` ` |
| 18 | — | — | 0.01 | ` ` |
| 19 | — | — | 0.01 | ` ` |
| 20 | — | — | 0.06 | ` ` |
| 21 | — | — | 0.02 | ` ` |
| 22 | — | — | 0.01 | ` ` |
| 23 | — | — | 0.04 | ` ` |
| 24 | — | — | 0.01 | ` ` |
| 25 | — | — | 0.03 | ` ` |
| 26 | — | — | 0.04 | ` ` |
| 27 | — | — | 0.06 | ` ` |
| 28 | — | SELECT | 0.11 | `SELECT repmgr.set_upstream_last_seen(1001)` |
| 29 | — | SELECT | 0.02 | `SELECT TRUE` |
| 30 | — | SELECT | 0.05 | `SELECT repmgr.get_local_node_id()` |
| 31 | nodes | SELECT | 0.10 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 32 | — | SELECT | 0.30 | `SELECT TRUE` |
| 33 | — | SELECT | 0.12 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 34 | — | SELECT | 0.10 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 35 | — | SELECT | 0.08 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 36 | — | SELECT | 0.19 | `SELECT repmgr.set_upstream_last_seen(1001)` |
| 37 | — | SELECT | 0.02 | `SELECT TRUE` |
| 38 | — | SELECT | 0.17 | `SELECT repmgr.get_local_node_id()` |
| 39 | nodes | SELECT | 0.14 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |

### `mgmt.delete_catalog_role`

- `DELETE /v1/catalogs/{cat}/catalog-roles/{cr}` → **204**
- wall 72 ms · 38 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, nodes, pg_stat_replication

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 41.06 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | entities | DELETE | — | `DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?` |
| 9 | grant_records | SELECT | 1.39 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 10 | grant_records | SELECT | 0.02 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 11 | grant_records | DELETE | 2.37 | `DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (
    (grantee_id = ? AND grantee_catalog_id = ?) OR
    (securable_id = ? AND securable_catalog_id = ?)
) AND realm_id = ?` |
| 12 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 13 | entities | UPDATE | 0.06 | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |
| 14 | entities | UPDATE | 0.09 | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |
| 15 | entities | INSERT | 0.11 | `INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestam` |
| 16 | — | — | 0.05 | ` ` |
| 17 | — | — | 0.01 | ` ` |
| 18 | — | — | 0.01 | ` ` |
| 19 | — | — | 0.01 | ` ` |
| 20 | — | — | 0.01 | ` ` |
| 21 | — | — | 0.01 | ` ` |
| 22 | — | — | 0.01 | ` ` |
| 23 | — | — | 0.02 | ` ` |
| 24 | — | — | 0.01 | ` ` |
| 25 | — | — | 0.01 | ` ` |
| 26 | — | SELECT | 0.14 | `SELECT 1` |
| 27 | — | — | 0.01 | ` ` |
| 28 | — | — | 0.02 | ` ` |
| 29 | — | — | 0.04 | ` ` |
| 30 | — | — | 0.02 | ` ` |
| 31 | — | — | 0.03 | ` ` |
| 32 | — | — | 0.03 | ` ` |
| 33 | — | SET | 0.07 | `SET synchronous_commit TO 'local'` |
| 34 | nodes | SELECT | 0.33 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 35 | pg_stat_replication | SELECT | 68.82 | `SELECT pg_catalog.current_setting('max_wal_senders')::INT AS max_wal_senders,         (SELECT pg_catalog.count(*) FROM pg_catalog.pg_stat_replication) AS attached_wal_receivers,   ` |
| 36 | — | SELECT | 0.06 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 37 | entities | DELETE | 0.04 | `DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = $1 AND catalog_id = $2 AND id = $3 (grantee_id = $1 AND grantee_catalog_id = $2) OR (securable_id = $3 AND securable_catalog_id` |

### `mgmt.delete_principal_role`

- `DELETE /v1/principal-roles/{r}` → **204**
- wall 29 ms · 37 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 1.85 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.14 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | grant_records | SELECT | 1.54 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 9 | grant_records | SELECT | 0.02 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 10 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | entities | DELETE | — | `DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?` |
| 12 | grant_records | SELECT | 1.41 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 13 | grant_records | SELECT | 0.02 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 14 | grant_records | DELETE | 2.08 | `DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (
    (grantee_id = ? AND grantee_catalog_id = ?) OR
    (securable_id = ? AND securable_catalog_id = ?)
) AND realm_id = ?` |
| 15 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 16 | entities | UPDATE | 0.07 | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |
| 17 | entities | INSERT | 0.06 | `INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestam` |
| 18 | — | — | 0.25 | ` ` |
| 19 | — | — | 0.01 | ` ` |
| 20 | — | — | 0.02 | ` ` |
| 21 | — | — | 0.02 | ` ` |
| 22 | — | — | 0.03 | ` ` |
| 23 | — | — | 0.01 | ` ` |
| 24 | — | — | 0.03 | ` ` |
| 25 | — | — | 0.01 | ` ` |
| 26 | — | — | 0.01 | ` ` |
| 27 | — | — | 0.03 | ` ` |
| 28 | — | — | 0.03 | ` ` |
| 29 | — | — | 0.01 | ` ` |
| 30 | — | — | 0.03 | ` ` |
| 31 | — | — | 0.01 | ` ` |
| 32 | — | — | 0.01 | ` ` |
| 33 | — | — | 0.04 | ` ` |
| 34 | — | — | 0.02 | ` ` |
| 35 | — | — | 0.02 | ` ` |
| 36 | entities | DELETE | 0.03 | `DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = $1 AND catalog_id = $2 AND id = $3 (grantee_id = $1 AND grantee_catalog_id = $2) OR (securable_id = $3 AND securable_catalog_id` |

### `mgmt.delete_principal`

- `DELETE /v1/principals/{p}` → **204**
- wall 43 ms · 33 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, principal_authentication_data

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.13 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 4.29 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.14 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | grant_records | SELECT | 3.59 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 9 | grant_records | SELECT | 0.06 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 10 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | entities | DELETE | — | `DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?` |
| 12 | grant_records | SELECT | 1.58 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 13 | grant_records | SELECT | 0.02 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 14 | grant_records | DELETE | 2.03 | `DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (
    (grantee_id = ? AND grantee_catalog_id = ?) OR
    (securable_id = ? AND securable_catalog_id = ?)
) AND realm_id = ?` |
| 15 | principal_authentication_data | DELETE | 0.04 | `DELETE FROM POLARIS_SCHEMA.PRINCIPAL_AUTHENTICATION_DATA WHERE realm_id = ? AND principal_id = ? AND principal_client_id = ?` |
| 16 | — | — | 0.10 | ` ` |
| 17 | — | — | 0.16 | ` ` |
| 18 | — | — | 0.04 | ` ` |
| 19 | — | — | 0.01 | ` ` |
| 20 | — | — | 0.05 | ` ` |
| 21 | — | — | 0.33 | ` ` |
| 22 | — | — | 0.03 | ` ` |
| 23 | — | — | 0.07 | ` ` |
| 24 | — | — | 0.09 | ` ` |
| 25 | — | — | 0.04 | ` ` |
| 26 | — | — | 0.06 | ` ` |
| 27 | — | — | 0.04 | ` ` |
| 28 | — | — | 0.05 | ` ` |
| 29 | — | — | 0.01 | ` ` |
| 30 | — | — | 0.01 | ` ` |
| 31 | — | — | 0.01 | ` ` |
| 32 | entities | DELETE | 0.13 | `DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = $1 AND catalog_id = $2 AND id = $3 (grantee_id = $1 AND grantee_catalog_id = $2) OR (securable_id = $3 AND securable_catalog_id` |
