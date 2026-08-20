# API → SQL → MinIO Access Matrix

Generated 2026-08-20 13:35 from a live local run — Polaris 1.3.0, realm POLARIS.
Schema version 3 (OK).

R = read, W = write, RW = both.

## API → PostgreSQL tables

| API | entities | grant_records | nodes | pg_stat_replication | policy_mapping_record | principal_authentication_data | replay_lag |
|---|---|---|---|---|---|---|---|
| `iceberg.commit_table` | RW | R | · | · | · | · | · |
| `iceberg.create_namespace` | RW | R | R | · | · | · | · |
| `iceberg.create_table` | RW | R | · | · | · | · | · |
| `iceberg.create_view` | RW | R | · | · | · | · | · |
| `iceberg.drop_namespace` | RW | RW | R | R | RW | · | · |
| `iceberg.drop_table` | RW | RW | · | · | RW | · | · |
| `iceberg.drop_view` | RW | RW | · | · | · | · | · |
| `iceberg.get_config` | R | R | · | · | · | · | · |
| `iceberg.head_namespace` | R | R | · | · | · | · | · |
| `iceberg.head_table` | R | R | · | · | · | · | · |
| `iceberg.head_view` | R | R | · | · | · | · | · |
| `iceberg.list_namespaces` | R | R | · | · | · | · | · |
| `iceberg.list_tables` | R | R | R | R | · | · | · |
| `iceberg.list_views` | R | R | · | · | · | · | · |
| `iceberg.load_namespace` | R | R | · | · | · | · | · |
| `iceberg.load_table` | R | R | R | · | · | · | R |
| `iceberg.load_table[missing]` | R | R | R | R | · | · | · |
| `iceberg.load_table[snapshots=refs]` | R | R | · | · | · | · | · |
| `iceberg.load_view` | R | R | R | R | · | · | · |
| `iceberg.rename_table` | RW | R | · | · | · | · | · |
| `iceberg.rename_view` | RW | R | R | · | · | · | · |
| `iceberg.report_metrics` | R | R | · | · | · | · | · |
| `iceberg.stage_create_table` | R | R | · | · | · | · | · |
| `iceberg.update_namespace_properties` | RW | R | R | R | · | · | · |
| `mgmt.assign_catalog_role` | RW | RW | R | R | · | · | · |
| `mgmt.assign_principal_role` | RW | RW | · | · | · | · | · |
| `mgmt.create_catalog_role` | RW | R | R | R | · | · | · |
| `mgmt.create_principal` | RW | R | · | · | · | RW | · |
| `mgmt.create_principal_role` | RW | R | · | · | · | · | · |
| `mgmt.delete_catalog_role` | RW | RW | R | · | · | · | · |
| `mgmt.delete_principal` | RW | RW | · | · | · | W | · |
| `mgmt.delete_principal_role` | RW | RW | · | · | · | · | · |
| `mgmt.get_catalog` | R | R | · | · | · | · | · |
| `mgmt.get_principal` | R | R | R | R | · | · | · |
| `mgmt.get_principal_role` | R | R | · | · | · | · | · |
| `mgmt.grant_privilege` | RW | RW | · | · | · | · | · |
| `mgmt.list_catalog_roles` | R | R | R | R | · | · | · |
| `mgmt.list_catalogs` | R | R | R | R | · | · | · |
| `mgmt.list_grants` | R | R | · | · | · | · | · |
| `mgmt.list_principal_roles` | R | R | · | · | · | · | · |
| `mgmt.list_principals` | R | R | R | · | · | · | · |
| `mgmt.list_principals_for_principal_role` | R | R | · | · | · | · | · |
| `mgmt.reset_principal_credentials` | R | R | R | R | · | RW | · |

## API → MinIO objects

| API | Method | Path | Count |
|---|---|---|---|
| `iceberg.load_table` |  | `/data-catalog-bucket/apiprofile1787200467_cat/probe_ns/probe_tbl/metadata/00000-79afa883-70eb-4f10-9032-08202c8761f7.metadata.json` | 1 |
| `iceberg.load_table[snapshots=refs]` |  | `/data-catalog-bucket/apiprofile1787200467_cat/probe_ns/probe_tbl/metadata/00000-79afa883-70eb-4f10-9032-08202c8761f7.metadata.json` | 1 |
| `iceberg.head_table` |  | `/data-catalog-bucket/apiprofile1787200467_cat/probe_ns/probe_tbl/metadata/00000-79afa883-70eb-4f10-9032-08202c8761f7.metadata.json` | 1 |
| `iceberg.create_table` |  | `/data-catalog-bucket/apiprofile1787200467_cat/probe_ns/probe_tbl2/metadata/00000-e3a9f0de-fb89-4490-b70f-dc6641f2390e.metadata.json` | 1 |
| `iceberg.commit_table` |  | `/data-catalog-bucket/apiprofile1787200467_cat/probe_ns/probe_tbl/metadata/00000-79afa883-70eb-4f10-9032-08202c8761f7.metadata.json` | 1 |
| `iceberg.commit_table` |  | `/data-catalog-bucket/apiprofile1787200467_cat/probe_ns/probe_tbl/metadata/00001-956a046f-0c1d-445b-9edc-831094e7ec8e.metadata.json` | 1 |
| `iceberg.create_view` |  | `/data-catalog-bucket/apiprofile1787200467_cat/probe_ns/probe_view/metadata/00000-fdb7fbb2-1e0b-42da-ba57-b928bb366f29.gz.metadata.json` | 2 |
| `iceberg.load_view` |  | `/data-catalog-bucket/apiprofile1787200467_cat/probe_ns/probe_view/metadata/00000-fdb7fbb2-1e0b-42da-ba57-b928bb366f29.gz.metadata.json` | 2 |
| `iceberg.head_view` |  | `/data-catalog-bucket/apiprofile1787200467_cat/probe_ns/probe_view/metadata/00000-fdb7fbb2-1e0b-42da-ba57-b928bb366f29.gz.metadata.json` | 2 |

## Per-API detail

### `iceberg.get_config`

- `GET /v1/config` → **200**
- wall 29 ms · 24 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.18 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 5.65 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.11 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | — | — | 0.15 | ` ` |
| 8 | — | — | 0.08 | ` ` |
| 9 | — | — | 0.05 | ` ` |
| 10 | — | — | 0.07 | ` ` |
| 11 | — | — | 0.07 | ` ` |
| 12 | — | — | 0.10 | ` ` |
| 13 | — | — | 0.03 | ` ` |
| 14 | — | — | 0.05 | ` ` |
| 15 | — | — | 0.03 | ` ` |
| 16 | — | — | 0.04 | ` ` |
| 17 | — | — | 0.09 | ` ` |
| 18 | — | — | 0.05 | ` ` |
| 19 | — | — | 0.06 | ` ` |
| 20 | — | — | 0.12 | ` ` |
| 21 | — | — | 0.23 | ` ` |
| 22 | — | — | 0.06 | ` ` |
| 23 | — | — | 0.05 | ` ` |

### `iceberg.list_namespaces`

- `GET /v1/{cat}/namespaces` → **200**
- wall 14 ms · 17 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 1.69 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND sub_type_code = ? AND realm_id = ? AND parent_id = ? AND type` |
| 8 | — | — | 0.08 | ` ` |
| 9 | — | — | 0.03 | ` ` |
| 10 | — | — | 0.02 | ` ` |
| 11 | — | — | 0.01 | ` ` |
| 12 | — | — | 0.02 | ` ` |
| 13 | — | — | 0.02 | ` ` |
| 14 | — | — | 0.03 | ` ` |
| 15 | — | — | 0.01 | ` ` |
| 16 | — | — | 0.15 | ` ` |

### `iceberg.load_namespace`

- `GET /v1/{cat}/namespaces/{ns}` → **200**
- wall 21 ms · 14 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.10 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 3.22 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.13 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | — | — | 0.19 | ` ` |
| 8 | — | — | 0.08 | ` ` |
| 9 | — | — | 0.06 | ` ` |
| 10 | — | — | 0.04 | ` ` |
| 11 | — | — | 0.05 | ` ` |
| 12 | — | — | 0.05 | ` ` |
| 13 | — | — | 0.05 | ` ` |

### `iceberg.head_namespace`

- `HEAD /v1/{cat}/namespaces/{ns}` → **204**
- wall 31 ms · 14 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.12 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 2.24 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.35 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | — | — | 0.39 | ` ` |
| 8 | — | — | 0.03 | ` ` |
| 9 | — | — | 0.05 | ` ` |
| 10 | — | — | 0.03 | ` ` |
| 11 | — | — | 0.02 | ` ` |
| 12 | — | — | 0.01 | ` ` |
| 13 | — | — | 0.04 | ` ` |

### `iceberg.update_namespace_properties`

- `POST /v1/{cat}/namespaces/{ns}/properties` → **200**
- wall 27 ms · 27 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, nodes, pg_stat_replication

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 2.20 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND realm_id = ? AND type_code = ? AND catalog_id = ?` |
| 8 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | UPDATE | 0.08 | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |
| 10 | — | — | 0.12 | ` ` |
| 11 | — | — | 0.03 | ` ` |
| 12 | — | — | 0.02 | ` ` |
| 13 | — | — | 0.01 | ` ` |
| 14 | — | — | 0.02 | ` ` |
| 15 | — | — | 0.01 | ` ` |
| 16 | — | — | 0.01 | ` ` |
| 17 | — | — | 0.02 | ` ` |
| 18 | — | — | 0.03 | ` ` |
| 19 | — | — | 0.03 | ` ` |
| 20 | — | SELECT | 0.14 | `SELECT TRUE` |
| 21 | — | SELECT | 0.10 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 22 | — | SELECT | 0.21 | `SELECT 1` |
| 23 | — | SET | 0.10 | `SET synchronous_commit TO 'local'` |
| 24 | nodes | SELECT | 0.41 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 25 | pg_stat_replication | SELECT | 1.27 | `SELECT pg_catalog.current_setting('max_wal_senders')::INT AS max_wal_senders,         (SELECT pg_catalog.count(*) FROM pg_catalog.pg_stat_replication) AS attached_wal_receivers,   ` |
| 26 | — | SELECT | 0.04 | `SELECT pg_catalog.pg_is_in_recovery()` |

### `iceberg.create_namespace`

- `POST /v1/{cat}/namespaces` → **200**
- wall 23 ms · 43 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, nodes

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 1.96 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND realm_id = ? AND type_code = ? AND catalog_id = ?` |
| 9 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 12 | entities | INSERT | 0.07 | `INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestam` |
| 13 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 14 | grant_records | SELECT | 0.02 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 15 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 16 | — | SELECT | 0.26 | `SELECT repmgr.set_upstream_last_seen(1001)` |
| 17 | — | SELECT | 0.30 | `SELECT TRUE` |
| 18 | — | SELECT | 0.06 | `SELECT repmgr.get_local_node_id()` |
| 19 | nodes | SELECT | 0.11 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 20 | — | — | 0.05 | ` ` |
| 21 | — | — | 0.02 | ` ` |
| 22 | — | — | 0.01 | ` ` |
| 23 | — | — | 0.01 | ` ` |
| 24 | — | — | 0.01 | ` ` |
| 25 | — | — | 0.01 | ` ` |
| 26 | — | — | 0.03 | ` ` |
| 27 | — | — | 0.06 | ` ` |
| 28 | — | — | 0.01 | ` ` |
| 29 | — | — | 0.01 | ` ` |
| 30 | — | — | 0.01 | ` ` |
| 31 | — | — | 0.01 | ` ` |
| 32 | — | — | 0.02 | ` ` |
| 33 | — | SELECT | 0.06 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 34 | — | — | 0.01 | ` ` |
| 35 | — | — | 0.01 | ` ` |
| 36 | — | — | 0.01 | ` ` |
| 37 | — | SELECT | 0.05 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 38 | — | SELECT | 0.24 | `SELECT 1` |
| 39 | — | SELECT | 0.08 | `SELECT repmgr.set_upstream_last_seen(1001)` |
| 40 | — | SELECT | 0.05 | `SELECT TRUE` |
| 41 | — | SELECT | 0.10 | `SELECT repmgr.get_local_node_id()` |
| 42 | nodes | SELECT | 0.11 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |

### `iceberg.drop_namespace`

- `DELETE /v1/{cat}/namespaces/{ns}` → **204**
- wall 77 ms · 83 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, nodes, pg_stat_replication, policy_mapping_record

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 31.96 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | DELETE | 0.09 | `DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?` |
| 10 | grant_records | SELECT | 0.02 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 11 | grant_records | DELETE | 2.30 | `DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (
    (grantee_id = ? AND grantee_catalog_id = ?) OR
    (securable_id = ? AND securable_catalog_id = ?)
) AND realm_id = ?` |
| 12 | policy_mapping_record | SELECT | 0.01 | `SELECT target_catalog_id, target_id, policy_type_code, policy_catalog_id, policy_id, parameters FROM POLARIS_SCHEMA.POLICY_MAPPING_RECORD WHERE realm_id = ? AND target_id = ? AND t` |
| 13 | policy_mapping_record | DELETE | 0.03 | `DELETE FROM POLARIS_SCHEMA.POLICY_MAPPING_RECORD WHERE target_catalog_id = ? AND target_id = ? AND realm_id = ?` |
| 14 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 15 | — | SET | 0.07 | `SET synchronous_commit TO 'local'` |
| 16 | — | SELECT | 0.14 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 17 | — | SELECT | 0.05 | `SELECT repmgr.get_repmgrd_pid()` |
| 18 | — | SELECT | 0.03 | `SELECT repmgr.repmgrd_is_running()` |
| 19 | — | SELECT | 0.02 | `SELECT repmgr.repmgrd_is_paused()` |
| 20 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 21 | — | SELECT | 0.12 | `SELECT paused.wal_replay_paused  AND pg_catalog.pg_last_wal_replay_lsn() < pg_catalog.pg_last_wal_receive_lsn()  FROM (SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE     ` |
| 22 | — | SELECT | 0.02 | `SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE    THEN -1    ELSE repmgr.get_upstream_last_seen()  END AS upstream_last_seen` |
| 23 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 24 | nodes | SELECT | 0.34 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, un.node_name AS upstream_node_name,` |
| 25 | — | SELECT | 0.02 | `SELECT paused.wal_replay_paused  AND pg_catalog.pg_last_wal_replay_lsn() < pg_catalog.pg_last_wal_receive_lsn()  FROM (SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE     ` |
| 26 | nodes | SELECT | 0.03 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 27 | — | SET | 0.19 | `SET application_name TO 'psql'` |
| 28 | — | — | 0.06 | ` ` |
| 29 | — | — | 0.02 | ` ` |
| 30 | — | — | 0.01 | ` ` |
| 31 | — | — | 0.01 | ` ` |
| 32 | — | — | 0.02 | ` ` |
| 33 | — | — | 0.02 | ` ` |
| 34 | — | — | 0.01 | ` ` |
| 35 | — | — | 0.03 | ` ` |
| 36 | — | — | 0.08 | ` ` |
| 37 | — | — | 0.01 | ` ` |
| 38 | — | — | 0.01 | ` ` |
| 39 | — | SET | 0.07 | `SET synchronous_commit TO 'local'` |
| 40 | nodes | SELECT | 0.37 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 41 | — | — | 0.01 | `  (grantee_id = $1 AND grantee_catalog_id = $2) OR (securable_id = $3 AND securable_catalog_id = $4) ) AND realm_id = $5 (grantee_id = $1 AND grantee_catalog_id = $2) OR (securable` |
| 42 | pg_stat_replication | SELECT | 1.24 | `SELECT pg_catalog.current_setting('max_wal_senders')::INT AS max_wal_senders,         (SELECT pg_catalog.count(*) FROM pg_catalog.pg_stat_replication) AS attached_wal_receivers,   ` |
| 43 | — | SELECT | 0.03 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 44 | — | — | 0.01 | ` ` |
| 45 | — | — | 0.01 | ` ` |
| 46 | — | SET | 0.04 | `SET synchronous_commit TO 'local'` |
| 47 | nodes | SELECT | 0.41 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, un.node_name AS upstream_node_name,` |
| 48 | — | SET | 0.09 | `SET synchronous_commit TO 'local'` |
| 49 | pg_stat_replication | SELECT | 0.94 | `SELECT pid, state    FROM pg_catalog.pg_stat_replication   WHERE application_name = 'benchmarks-postgresql-postgresql-ha-postgresql-0'` |
| 50 | — | SET | 0.09 | `SET synchronous_commit TO 'local'` |
| 51 | — | SELECT | 0.13 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 52 | — | SELECT | 0.05 | `SELECT repmgr.get_repmgrd_pid()` |
| 53 | — | SELECT | 0.02 | `SELECT repmgr.repmgrd_is_running()` |
| 54 | — | SELECT | 0.02 | `SELECT repmgr.repmgrd_is_paused()` |
| 55 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 56 | — | SELECT | 0.03 | `SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE    THEN -1    ELSE repmgr.get_upstream_last_seen()  END AS upstream_last_seen` |
| 57 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 58 | nodes | SELECT | 0.37 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, un.node_name AS upstream_node_name,` |
| 59 | — | SET | 0.03 | `SET synchronous_commit TO 'local'` |
| 60 | pg_stat_replication | SELECT | 0.81 | `SELECT pid, state    FROM pg_catalog.pg_stat_replication   WHERE application_name = 'benchmarks-postgresql-postgresql-ha-postgresql-2'` |
| 61 | — | — | 0.06 | ` ` |
| 62 | — | — | 0.03 | ` ` |
| 63 | — | BEGIN | 0.03 | `BEGIN` |
| 64 | events | INSERT | 0.06 | `INSERT INTO POLARIS_SCHEMA.EVENTS (catalog_id, event_id, request_id, event_type, timestamp_ms, principal_name, resource_type, resource_identifier, additional_properties, realm_id) ` |
| 65 | events | INSERT | 0.03 | `INSERT INTO POLARIS_SCHEMA.EVENTS (catalog_id, event_id, request_id, event_type, timestamp_ms, principal_name, resource_type, resource_identifier, additional_properties, realm_id) ` |
| 66 | — | COMMIT | 4.07 | `COMMIT` |
| 67 | — | SET | 0.08 | `SET application_name TO 'psql'` |
| 68 | — | SELECT | 0.07 | `SELECT 1` |
| 69 | — | — | 0.05 | `DISCARD ALL` |
| 70 | — | SET | 0.07 | `SET synchronous_commit TO 'local'` |
| 71 | — | SELECT | 0.13 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 72 | — | SELECT | 0.05 | `SELECT repmgr.get_repmgrd_pid()` |
| 73 | — | SELECT | 0.04 | `SELECT repmgr.repmgrd_is_running()` |
| 74 | — | SELECT | 0.02 | `SELECT repmgr.repmgrd_is_paused()` |
| 75 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 76 | — | SELECT | 0.11 | `SELECT paused.wal_replay_paused  AND pg_catalog.pg_last_wal_replay_lsn() < pg_catalog.pg_last_wal_receive_lsn()  FROM (SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE     ` |
| 77 | — | SELECT | 0.04 | `SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE    THEN -1    ELSE repmgr.get_upstream_last_seen()  END AS upstream_last_seen` |
| 78 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 79 | nodes | SELECT | 0.41 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, un.node_name AS upstream_node_name,` |
| 80 | — | SELECT | 0.03 | `SELECT paused.wal_replay_paused  AND pg_catalog.pg_last_wal_replay_lsn() < pg_catalog.pg_last_wal_receive_lsn()  FROM (SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE     ` |
| 81 | nodes | SELECT | 0.04 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 82 | — | SET | 0.09 | `SET application_name TO 'psql'` |

### `iceberg.list_tables`

- `GET /v1/{cat}/namespaces/{ns}/tables` → **200**
- wall 15 ms · 21 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, nodes, pg_stat_replication

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 1.75 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND sub_type_code = ? AND realm_id = ? AND parent_id = ? AND type` |
| 8 | — | SELECT | 0.20 | `SELECT 1` |
| 9 | — | SET | 0.10 | `SET synchronous_commit TO 'local'` |
| 10 | nodes | SELECT | 0.45 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 11 | pg_stat_replication | SELECT | 1.27 | `SELECT pg_catalog.current_setting('max_wal_senders')::INT AS max_wal_senders,         (SELECT pg_catalog.count(*) FROM pg_catalog.pg_stat_replication) AS attached_wal_receivers,   ` |
| 12 | — | SELECT | 0.03 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 13 | — | — | 0.15 | ` ` |
| 14 | — | — | 0.05 | ` ` |
| 15 | — | — | 0.03 | ` ` |
| 16 | — | — | 0.01 | ` ` |
| 17 | — | — | 0.04 | ` ` |
| 18 | — | — | 0.04 | ` ` |
| 19 | — | — | 0.16 | ` ` |
| 20 | — | — | 0.02 | ` ` |

### `iceberg.load_table`

- `GET /v1/{cat}/namespaces/{ns}/tables/{tbl}` → **200**
- wall 64 ms · 40 statements · 1 object ops · cache: MISS
- tables: entities, grant_records, nodes, replay_lag

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.16 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.13 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 3.30 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.11 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | — | SELECT | 0.43 | `SELECT pg_catalog.pg_last_wal_replay_lsn()` |
| 11 | — | SELECT | 0.07 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 12 | — | SELECT | 0.20 | `SELECT repmgr.set_upstream_last_seen(1001)` |
| 13 | — | SELECT | 0.03 | `SELECT TRUE` |
| 14 | — | SELECT | 0.09 | `SELECT repmgr.get_local_node_id()` |
| 15 | nodes | SELECT | 0.19 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 16 | — | — | 0.27 | ` ` |
| 17 | — | — | 0.16 | ` ` |
| 18 | — | — | 0.03 | ` ` |
| 19 | — | — | 0.03 | ` ` |
| 20 | — | SELECT | 0.26 | `SELECT TRUE` |
| 21 | — | — | 0.05 | ` ` |
| 22 | — | — | 0.02 | ` ` |
| 23 | — | — | 0.07 | ` ` |
| 24 | — | — | 0.03 | ` ` |
| 25 | — | — | 0.01 | ` ` |
| 26 | nodes | SELECT | 1.04 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser,            n.slot_name, n.location, n.priority, n.active, n.config_file,            '' AS upstrea` |
| 27 | — | SELECT | 0.09 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 28 | — | — | 0.08 | ` ` |
| 29 | — | SELECT | 0.19 | `SELECT pg_catalog.pg_current_wal_lsn()` |
| 30 | replay_lag | SELECT | 1.18 | `SELECT application_name, state, sync_state,(EXTRACT(EPOCH FROM replay_lag)*1000000)::BIGINT FROM pg_catalog.pg_stat_replication` |
| 31 | — | SELECT | 0.03 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 32 | — | SELECT | 0.57 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 33 | — | SELECT | 0.05 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 34 | — | SELECT | 0.17 | `SELECT pg_catalog.pg_last_wal_replay_lsn()` |
| 35 | — | SELECT | 0.05 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 36 | — | SELECT | 0.10 | `SELECT repmgr.set_upstream_last_seen(1001)` |
| 37 | — | SELECT | 0.04 | `SELECT TRUE` |
| 38 | — | SELECT | 0.03 | `SELECT repmgr.get_local_node_id()` |
| 39 | nodes | SELECT | 0.06 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |

| # | Method | Path | ms |
|---|---|---|---|
| 0 |  | `/data-catalog-bucket/apiprofile1787200467_cat/probe_ns/probe_tbl/metadata/00000-79afa883-70eb-4f10-9032-08202c8761f7.metadata.json` | 1.83 |

### `iceberg.load_table[snapshots=refs]`

- `GET /v1/{cat}/.../tables/{tbl}?snapshots=refs` → **200**
- wall 38 ms · 16 statements · 1 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.21 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 2.65 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | — | — | 0.35 | ` ` |
| 9 | — | — | 0.11 | ` ` |
| 10 | — | — | 0.11 | ` ` |
| 11 | — | — | 0.06 | ` ` |
| 12 | — | — | 0.04 | ` ` |
| 13 | — | — | 0.02 | ` ` |
| 14 | — | — | 0.05 | ` ` |
| 15 | — | — | 0.03 | ` ` |

| # | Method | Path | ms |
|---|---|---|---|
| 0 |  | `/data-catalog-bucket/apiprofile1787200467_cat/probe_ns/probe_tbl/metadata/00000-79afa883-70eb-4f10-9032-08202c8761f7.metadata.json` | 2.89 |

### `iceberg.head_table`

- `HEAD /v1/{cat}/namespaces/{ns}/tables/{tbl}` → **204**
- wall 39 ms · 16 statements · 1 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.11 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 3.47 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.17 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.13 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | — | — | 0.31 | ` ` |
| 9 | — | — | 0.04 | ` ` |
| 10 | — | — | 0.01 | ` ` |
| 11 | — | — | 0.02 | ` ` |
| 12 | — | — | 0.04 | ` ` |
| 13 | — | — | 0.05 | ` ` |
| 14 | — | — | 0.04 | ` ` |
| 15 | — | — | 0.09 | ` ` |

| # | Method | Path | ms |
|---|---|---|---|
| 0 |  | `/data-catalog-bucket/apiprofile1787200467_cat/probe_ns/probe_tbl/metadata/00000-79afa883-70eb-4f10-9032-08202c8761f7.metadata.json` | 1.72 |

### `iceberg.create_table`

- `POST /v1/{cat}/namespaces/{ns}/tables` → **200**
- wall 44 ms · 48 statements · 1 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 1.75 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 12 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 13 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 14 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 15 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND realm_id = ? AND type_code = ? AND catalog_id = ?` |
| 16 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND realm_id = ? AND type_code = ? AND catalog_id = ?` |
| 17 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 18 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 19 | entities | SELECT | 0.10 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 20 | entities | INSERT | 0.07 | `INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestam` |
| 21 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 22 | grant_records | SELECT | 0.02 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 23 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 24 | — | — | 0.11 | ` ` |
| 25 | — | — | 0.05 | ` ` |
| 26 | — | — | 0.03 | ` ` |
| 27 | — | — | 0.02 | ` ` |
| 28 | — | — | 0.02 | ` ` |
| 29 | — | — | 0.02 | ` ` |
| 30 | — | — | 0.01 | ` ` |
| 31 | — | — | 0.01 | ` ` |
| 32 | — | — | 0.01 | ` ` |
| 33 | — | — | 0.03 | ` ` |
| 34 | — | — | 0.02 | ` ` |
| 35 | — | — | 0.02 | ` ` |
| 36 | — | — | 0.03 | ` ` |
| 37 | — | — | 0.01 | ` ` |
| 38 | — | — | 0.02 | ` ` |
| 39 | — | — | 0.05 | ` ` |
| 40 | — | — | 0.01 | ` ` |
| 41 | — | — | 0.03 | ` ` |
| 42 | — | — | 0.03 | ` ` |
| 43 | — | — | 0.01 | ` ` |
| 44 | — | — | 0.04 | ` ` |
| 45 | — | — | 0.03 | ` ` |
| 46 | — | — | 0.02 | ` ` |
| 47 | — | — | 0.01 | ` ` |

| # | Method | Path | ms |
|---|---|---|---|
| 0 |  | `/data-catalog-bucket/apiprofile1787200467_cat/probe_ns/probe_tbl2/metadata/00000-e3a9f0de-fb89-4490-b70f-dc6641f2390e.metadata.json` | 4.72 |

### `iceberg.stage_create_table`

- `POST /v1/{cat}/namespaces/{ns}/tables[stage]` → **200**
- wall 43 ms · 26 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.39 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.27 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 6.40 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.16 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | SELECT | 0.11 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 12 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 13 | — | — | 0.26 | ` ` |
| 14 | — | — | 0.28 | ` ` |
| 15 | — | — | 0.57 | ` ` |
| 16 | — | — | 0.07 | ` ` |
| 17 | — | — | 0.03 | ` ` |
| 18 | — | — | 0.02 | ` ` |
| 19 | — | — | 0.05 | ` ` |
| 20 | — | — | 0.02 | ` ` |
| 21 | — | — | 0.12 | ` ` |
| 22 | — | — | 0.06 | ` ` |
| 23 | — | — | 0.04 | ` ` |
| 24 | — | — | 0.01 | ` ` |
| 25 | — | — | 0.02 | ` ` |

### `iceberg.commit_table`

- `POST /v1/{cat}/namespaces/{ns}/tables/{tbl}` → **200**
- wall 49 ms · 37 statements · 2 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 2.11 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | entities | SELECT | 0.10 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | entities | UPDATE | 0.10 | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |
| 11 | entities | SELECT | 0.17 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 12 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 13 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 14 | — | SET | 0.25 | `SET application_name TO 'psql'` |
| 15 | — | SELECT | 0.34 | `SELECT 1` |
| 16 | — | — | 0.06 | `DISCARD ALL` |
| 17 | — | SET | 0.11 | `SET application_name TO 'psql'` |
| 18 | — | — | 0.63 | `DISCARD ALL` |
| 19 | — | — | 0.04 | ` ` |
| 20 | — | — | 0.03 | ` ` |
| 21 | — | — | 0.02 | ` ` |
| 22 | — | — | 0.01 | ` ` |
| 23 | — | — | 0.02 | ` ` |
| 24 | — | — | 0.05 | ` ` |
| 25 | — | — | 0.02 | ` ` |
| 26 | — | — | 0.04 | ` ` |
| 27 | — | — | 0.12 | ` ` |
| 28 | — | — | 0.05 | ` ` |
| 29 | — | — | 0.02 | ` ` |
| 30 | — | — | 0.03 | ` ` |
| 31 | — | — | 0.02 | ` ` |
| 32 | — | — | 0.01 | ` ` |
| 33 | — | SELECT | 0.25 | `SELECT TRUE` |
| 34 | — | SELECT | 0.11 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 35 | — | SET | 0.18 | `SET application_name TO 'psql'` |
| 36 | — | SELECT | — | `SELECT repmgr.set_upstream_last_seen(1001)` |

| # | Method | Path | ms |
|---|---|---|---|
| 0 |  | `/data-catalog-bucket/apiprofile1787200467_cat/probe_ns/probe_tbl/metadata/00000-79afa883-70eb-4f10-9032-08202c8761f7.metadata.json` | 1.13 |
| 1 |  | `/data-catalog-bucket/apiprofile1787200467_cat/probe_ns/probe_tbl/metadata/00001-956a046f-0c1d-445b-9edc-831094e7ec8e.metadata.json` | 5.44 |

### `iceberg.rename_table`

- `POST /v1/{cat}/tables/rename` → **200**
- wall 22 ms · 22 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.19 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 1.81 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | entities | UPDATE | 0.07 | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |
| 11 | — | — | 0.40 | ` ` |
| 12 | — | — | 0.07 | ` ` |
| 13 | — | — | 0.03 | ` ` |
| 14 | — | — | 0.02 | ` ` |
| 15 | — | — | 0.03 | ` ` |
| 16 | — | — | 0.01 | ` ` |
| 17 | — | — | 0.03 | ` ` |
| 18 | — | — | 0.01 | ` ` |
| 19 | — | — | 0.04 | ` ` |
| 20 | — | — | 0.01 | ` ` |
| 21 | — | — | 0.01 | ` ` |

### `iceberg.report_metrics`

- `POST /v1/{cat}/.../tables/{tbl}/metrics` → **204**
- wall 60 ms · 12 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 1.93 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | — | — | 0.07 | ` ` |
| 7 | — | — | 0.03 | ` ` |
| 8 | — | — | 0.04 | ` ` |
| 9 | — | — | 0.01 | ` ` |
| 10 | — | — | 0.01 | ` ` |
| 11 | — | — | 0.01 | ` ` |

### `iceberg.load_table[missing]`

- `GET /v1/{cat}/.../tables/{missing}` → **404**
- wall 33 ms · 59 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, nodes, pg_stat_replication

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 20.72 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | — | SET | 0.09 | `SET synchronous_commit TO 'local'` |
| 9 | — | SELECT | 0.16 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 10 | — | SELECT | 0.07 | `SELECT repmgr.get_repmgrd_pid()` |
| 11 | — | SELECT | 0.04 | `SELECT repmgr.repmgrd_is_running()` |
| 12 | — | SELECT | 0.02 | `SELECT repmgr.repmgrd_is_paused()` |
| 13 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 14 | — | SELECT | 0.15 | `SELECT paused.wal_replay_paused  AND pg_catalog.pg_last_wal_replay_lsn() < pg_catalog.pg_last_wal_receive_lsn()  FROM (SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE     ` |
| 15 | — | SELECT | 0.05 | `SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE    THEN -1    ELSE repmgr.get_upstream_last_seen()  END AS upstream_last_seen` |
| 16 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 17 | nodes | SELECT | 0.48 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, un.node_name AS upstream_node_name,` |
| 18 | — | SELECT | 0.03 | `SELECT paused.wal_replay_paused  AND pg_catalog.pg_last_wal_replay_lsn() < pg_catalog.pg_last_wal_receive_lsn()  FROM (SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE     ` |
| 19 | nodes | SELECT | 0.03 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 20 | — | — | 0.13 | ` ` |
| 21 | — | — | 0.04 | ` ` |
| 22 | — | — | 0.01 | ` ` |
| 23 | — | — | 0.02 | ` ` |
| 24 | — | — | 0.04 | ` ` |
| 25 | — | — | 0.04 | ` ` |
| 26 | — | — | 0.07 | ` ` |
| 27 | — | — | 0.03 | ` ` |
| 28 | — | SET | 0.09 | `SET synchronous_commit TO 'local'` |
| 29 | nodes | SELECT | 0.47 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 30 | pg_stat_replication | SELECT | 1.26 | `SELECT pg_catalog.current_setting('max_wal_senders')::INT AS max_wal_senders,         (SELECT pg_catalog.count(*) FROM pg_catalog.pg_stat_replication) AS attached_wal_receivers,   ` |
| 31 | — | SELECT | 0.02 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 32 | — | SET | 0.09 | `SET synchronous_commit TO 'local'` |
| 33 | nodes | SELECT | 0.61 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, un.node_name AS upstream_node_name,` |
| 34 | — | SET | 0.04 | `SET synchronous_commit TO 'local'` |
| 35 | pg_stat_replication | SELECT | 1.15 | `SELECT pid, state    FROM pg_catalog.pg_stat_replication   WHERE application_name = 'benchmarks-postgresql-postgresql-ha-postgresql-0'` |
| 36 | — | SET | 0.04 | `SET synchronous_commit TO 'local'` |
| 37 | — | SELECT | 0.10 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 38 | — | SELECT | 0.05 | `SELECT repmgr.get_repmgrd_pid()` |
| 39 | — | SELECT | 0.03 | `SELECT repmgr.repmgrd_is_running()` |
| 40 | — | SELECT | 0.02 | `SELECT repmgr.repmgrd_is_paused()` |
| 41 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 42 | — | SELECT | 0.03 | `SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE    THEN -1    ELSE repmgr.get_upstream_last_seen()  END AS upstream_last_seen` |
| 43 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 44 | nodes | SELECT | 0.35 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, un.node_name AS upstream_node_name,` |
| 45 | — | SET | 0.07 | `SET synchronous_commit TO 'local'` |
| 46 | pg_stat_replication | SELECT | 1.04 | `SELECT pid, state    FROM pg_catalog.pg_stat_replication   WHERE application_name = 'benchmarks-postgresql-postgresql-ha-postgresql-2'` |
| 47 | — | SET | 0.07 | `SET synchronous_commit TO 'local'` |
| 48 | — | SELECT | 0.10 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 49 | — | SELECT | 0.04 | `SELECT repmgr.get_repmgrd_pid()` |
| 50 | — | SELECT | 0.04 | `SELECT repmgr.repmgrd_is_running()` |
| 51 | — | SELECT | 0.02 | `SELECT repmgr.repmgrd_is_paused()` |
| 52 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 53 | — | SELECT | 0.10 | `SELECT paused.wal_replay_paused  AND pg_catalog.pg_last_wal_replay_lsn() < pg_catalog.pg_last_wal_receive_lsn()  FROM (SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE     ` |
| 54 | — | SELECT | 0.03 | `SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE    THEN -1    ELSE repmgr.get_upstream_last_seen()  END AS upstream_last_seen` |
| 55 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 56 | nodes | SELECT | 0.40 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, un.node_name AS upstream_node_name,` |
| 57 | — | SELECT | 0.02 | `SELECT paused.wal_replay_paused  AND pg_catalog.pg_last_wal_replay_lsn() < pg_catalog.pg_last_wal_receive_lsn()  FROM (SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE     ` |
| 58 | nodes | SELECT | 0.03 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |

### `iceberg.drop_table`

- `DELETE /v1/{cat}/namespaces/{ns}/tables/{tbl}` → **204**
- wall 31 ms · 33 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, policy_mapping_record

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.16 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 2.78 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | grant_records | SELECT | 0.04 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 8 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | entities | DELETE | 0.05 | `DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?` |
| 11 | grant_records | SELECT | 0.03 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 12 | grant_records | DELETE | 3.27 | `DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (
    (grantee_id = ? AND grantee_catalog_id = ?) OR
    (securable_id = ? AND securable_catalog_id = ?)
) AND realm_id = ?` |
| 13 | policy_mapping_record | SELECT | 0.01 | `SELECT target_catalog_id, target_id, policy_type_code, policy_catalog_id, policy_id, parameters FROM POLARIS_SCHEMA.POLICY_MAPPING_RECORD WHERE realm_id = ? AND target_id = ? AND t` |
| 14 | policy_mapping_record | DELETE | 0.01 | `DELETE FROM POLARIS_SCHEMA.POLICY_MAPPING_RECORD WHERE target_catalog_id = ? AND target_id = ? AND realm_id = ?` |
| 15 | — | SELECT | 0.45 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 16 | — | — | 0.15 | ` ` |
| 17 | — | — | 0.04 | ` ` |
| 18 | — | — | 0.02 | ` ` |
| 19 | — | — | 0.04 | ` ` |
| 20 | — | — | 0.04 | ` ` |
| 21 | — | — | 0.03 | ` ` |
| 22 | — | — | 0.03 | ` ` |
| 23 | — | — | 0.01 | ` ` |
| 24 | — | — | 0.02 | ` ` |
| 25 | — | — | 0.03 | ` ` |
| 26 | — | — | 0.02 | ` ` |
| 27 | — | — | 0.05 | ` ` |
| 28 | — | — | 0.05 | `  (grantee_id = $1 AND grantee_catalog_id = $2) OR (securable_id = $3 AND securable_catalog_id = $4) ) AND realm_id = $5 (grantee_id = $1 AND grantee_catalog_id = $2) OR (securable` |
| 29 | — | — | 0.01 | ` ` |
| 30 | — | — | 0.02 | ` ` |
| 31 | — | SELECT | 0.28 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 32 | — | SELECT | 0.35 | `SELECT pg_catalog.pg_is_in_recovery()` |

### `iceberg.create_view`

- `POST /v1/{cat}/namespaces/{ns}/views` → **200**
- wall 75 ms · 46 statements · 2 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.12 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 3.18 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.12 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | SELECT | 0.10 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 12 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 13 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 14 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND realm_id = ? AND type_code = ? AND catalog_id = ?` |
| 15 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND realm_id = ? AND type_code = ? AND catalog_id = ?` |
| 16 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 17 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 18 | entities | INSERT | 0.19 | `INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestam` |
| 19 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 20 | grant_records | SELECT | 0.02 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 21 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 22 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 23 | — | — | 0.13 | ` ` |
| 24 | — | — | 0.05 | ` ` |
| 25 | — | — | 0.04 | ` ` |
| 26 | — | — | 0.05 | ` ` |
| 27 | — | — | 0.04 | ` ` |
| 28 | — | — | 0.06 | ` ` |
| 29 | — | — | 0.07 | ` ` |
| 30 | — | — | 0.03 | ` ` |
| 31 | — | — | 0.05 | ` ` |
| 32 | — | — | 0.05 | ` ` |
| 33 | — | — | 0.06 | ` ` |
| 34 | — | — | 0.03 | ` ` |
| 35 | — | — | 0.05 | ` ` |
| 36 | — | — | 0.09 | ` ` |
| 37 | — | — | 0.02 | ` ` |
| 38 | — | — | 0.01 | ` ` |
| 39 | — | — | 0.01 | ` ` |
| 40 | — | — | 0.01 | ` ` |
| 41 | — | — | 0.07 | ` ` |
| 42 | — | — | 0.01 | ` ` |
| 43 | — | — | 0.02 | ` ` |
| 44 | — | — | 0.01 | ` ` |
| 45 | — | — | 0.01 | ` ` |

| # | Method | Path | ms |
|---|---|---|---|
| 0 |  | `/data-catalog-bucket/apiprofile1787200467_cat/probe_ns/probe_view/metadata/00000-fdb7fbb2-1e0b-42da-ba57-b928bb366f29.gz.metadata.json` | 3.39 |
| 1 |  | `/data-catalog-bucket/apiprofile1787200467_cat/probe_ns/probe_view/metadata/00000-fdb7fbb2-1e0b-42da-ba57-b928bb366f29.gz.metadata.json` | 0.89 |

### `iceberg.list_views`

- `GET /v1/{cat}/namespaces/{ns}/views` → **200**
- wall 23 ms · 16 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 3.27 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.15 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND sub_type_code = ? AND realm_id = ? AND parent_id = ? AND type` |
| 8 | — | — | 0.16 | ` ` |
| 9 | — | — | 0.04 | ` ` |
| 10 | — | — | 0.02 | ` ` |
| 11 | — | — | 0.03 | ` ` |
| 12 | — | — | 0.15 | ` ` |
| 13 | — | — | 0.04 | ` ` |
| 14 | — | — | 0.05 | ` ` |
| 15 | — | — | 0.06 | ` ` |

### `iceberg.load_view`

- `GET /v1/{cat}/namespaces/{ns}/views/{view}` → **200**
- wall 58 ms · 23 statements · 2 object ops · cache: MISS
- tables: entities, grant_records, nodes, pg_stat_replication

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.17 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 4.33 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.10 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.17 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.35 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | entities | SELECT | 0.11 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | — | SELECT | 0.18 | `SELECT 1` |
| 10 | — | SET | 0.07 | `SET synchronous_commit TO 'local'` |
| 11 | nodes | SELECT | 0.37 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 12 | pg_stat_replication | SELECT | 1.07 | `SELECT pg_catalog.current_setting('max_wal_senders')::INT AS max_wal_senders,         (SELECT pg_catalog.count(*) FROM pg_catalog.pg_stat_replication) AS attached_wal_receivers,   ` |
| 13 | — | SELECT | 0.02 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 14 | — | — | 0.23 | ` ` |
| 15 | — | — | 0.11 | ` ` |
| 16 | — | — | 0.09 | ` ` |
| 17 | — | — | 0.09 | ` ` |
| 18 | — | — | 0.05 | ` ` |
| 19 | — | — | 0.07 | ` ` |
| 20 | — | — | 0.08 | ` ` |
| 21 | — | — | 0.07 | ` ` |
| 22 | — | — | 0.07 | ` ` |

| # | Method | Path | ms |
|---|---|---|---|
| 0 |  | `/data-catalog-bucket/apiprofile1787200467_cat/probe_ns/probe_view/metadata/00000-fdb7fbb2-1e0b-42da-ba57-b928bb366f29.gz.metadata.json` | 1.78 |
| 1 |  | `/data-catalog-bucket/apiprofile1787200467_cat/probe_ns/probe_view/metadata/00000-fdb7fbb2-1e0b-42da-ba57-b928bb366f29.gz.metadata.json` | 1.38 |

### `iceberg.head_view`

- `HEAD /v1/{cat}/namespaces/{ns}/views/{view}` → **204**
- wall 22 ms · 20 statements · 2 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 1.37 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | — | — | 0.09 | ` ` |
| 10 | — | — | 0.04 | ` ` |
| 11 | — | — | 0.03 | ` ` |
| 12 | — | — | 0.01 | ` ` |
| 13 | — | — | 0.03 | ` ` |
| 14 | — | — | 0.03 | ` ` |
| 15 | — | — | 0.04 | ` ` |
| 16 | — | — | 0.01 | ` ` |
| 17 | — | — | 0.06 | ` ` |
| 18 | — | SELECT | 0.38 | `SELECT TRUE` |
| 19 | — | SELECT | 0.16 | `SELECT pg_catalog.pg_is_in_recovery()` |

| # | Method | Path | ms |
|---|---|---|---|
| 0 |  | `/data-catalog-bucket/apiprofile1787200467_cat/probe_ns/probe_view/metadata/00000-fdb7fbb2-1e0b-42da-ba57-b928bb366f29.gz.metadata.json` | 0.89 |
| 1 |  | `/data-catalog-bucket/apiprofile1787200467_cat/probe_ns/probe_view/metadata/00000-fdb7fbb2-1e0b-42da-ba57-b928bb366f29.gz.metadata.json` | 0.91 |

### `iceberg.rename_view`

- `POST /v1/{cat}/views/rename` → **204**
- wall 38 ms · 32 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, nodes

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.11 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 1.73 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.14 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | entities | UPDATE | 0.07 | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |
| 11 | — | SELECT | 0.17 | `SELECT repmgr.set_upstream_last_seen(1001)` |
| 12 | — | SELECT | 0.02 | `SELECT TRUE` |
| 13 | — | SELECT | 0.08 | `SELECT repmgr.get_local_node_id()` |
| 14 | nodes | SELECT | 0.13 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 15 | — | — | 0.20 | ` ` |
| 16 | — | — | 0.17 | ` ` |
| 17 | — | — | 0.06 | ` ` |
| 18 | — | — | 0.01 | ` ` |
| 19 | — | — | 0.01 | ` ` |
| 20 | — | — | 0.20 | ` ` |
| 21 | — | — | 0.07 | ` ` |
| 22 | — | — | 0.01 | ` ` |
| 23 | — | — | 0.03 | ` ` |
| 24 | — | — | 0.05 | ` ` |
| 25 | — | — | 0.01 | ` ` |
| 26 | — | SELECT | 0.07 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 27 | — | SELECT | 0.07 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 28 | — | SELECT | 0.10 | `SELECT repmgr.set_upstream_last_seen(1001)` |
| 29 | — | SELECT | 0.02 | `SELECT TRUE` |
| 30 | — | SELECT | 0.07 | `SELECT repmgr.get_local_node_id()` |
| 31 | nodes | SELECT | 0.12 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |

### `iceberg.drop_view`

- `DELETE /v1/{cat}/namespaces/{ns}/views/{view}` → **204**
- wall 45 ms · 28 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.17 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.15 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 4.80 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.11 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.10 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | grant_records | SELECT | 0.03 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 8 | entities | SELECT | 0.11 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | entities | DELETE | 0.07 | `DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?` |
| 11 | grant_records | SELECT | 0.04 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 12 | grant_records | DELETE | 3.24 | `DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (
    (grantee_id = ? AND grantee_catalog_id = ?) OR
    (securable_id = ? AND securable_catalog_id = ?)
) AND realm_id = ?` |
| 13 | entities | INSERT | 0.08 | `INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestam` |
| 14 | — | — | 0.21 | ` ` |
| 15 | — | — | 0.09 | ` ` |
| 16 | — | — | 0.03 | ` ` |
| 17 | — | — | 0.02 | ` ` |
| 18 | — | — | 0.05 | ` ` |
| 19 | — | — | 0.10 | ` ` |
| 20 | — | — | 0.05 | ` ` |
| 21 | — | — | 0.05 | ` ` |
| 22 | — | — | 0.04 | ` ` |
| 23 | — | — | 0.03 | ` ` |
| 24 | — | — | 0.05 | ` ` |
| 25 | — | — | 0.05 | ` ` |
| 26 | — | — | 0.03 | `  (grantee_id = $1 AND grantee_catalog_id = $2) OR (securable_id = $3 AND securable_catalog_id = $4) ) AND realm_id = $5 (grantee_id = $1 AND grantee_catalog_id = $2) OR (securable` |
| 27 | — | — | 0.03 | ` ` |

### `mgmt.list_catalogs`

- `GET /v1/catalogs` → **200**
- wall 73 ms · 59 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, nodes, pg_stat_replication

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.11 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 2.84 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 6.42 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | — | SET | 0.07 | `SET synchronous_commit TO 'local'` |
| 9 | — | SELECT | 0.08 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 10 | — | SELECT | 0.04 | `SELECT repmgr.get_repmgrd_pid()` |
| 11 | — | SELECT | 0.02 | `SELECT repmgr.repmgrd_is_running()` |
| 12 | — | SELECT | 0.02 | `SELECT repmgr.repmgrd_is_paused()` |
| 13 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 14 | — | SELECT | 0.10 | `SELECT paused.wal_replay_paused  AND pg_catalog.pg_last_wal_replay_lsn() < pg_catalog.pg_last_wal_receive_lsn()  FROM (SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE     ` |
| 15 | — | SELECT | 0.03 | `SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE    THEN -1    ELSE repmgr.get_upstream_last_seen()  END AS upstream_last_seen` |
| 16 | — | SELECT | 0.02 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 17 | nodes | SELECT | 0.26 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, un.node_name AS upstream_node_name,` |
| 18 | — | SELECT | 0.03 | `SELECT paused.wal_replay_paused  AND pg_catalog.pg_last_wal_replay_lsn() < pg_catalog.pg_last_wal_receive_lsn()  FROM (SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE     ` |
| 19 | nodes | SELECT | 0.03 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 20 | — | — | 0.07 | ` ` |
| 21 | — | — | 0.07 | ` ` |
| 22 | — | — | 0.05 | ` ` |
| 23 | — | — | 0.05 | ` ` |
| 24 | — | — | 0.05 | ` ` |
| 25 | — | — | 0.07 | ` ` |
| 26 | — | — | 0.10 | ` ` |
| 27 | — | — | 0.04 | ` ` |
| 28 | — | SET | 0.09 | `SET synchronous_commit TO 'local'` |
| 29 | nodes | SELECT | 0.38 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 30 | pg_stat_replication | SELECT | 1.11 | `SELECT pg_catalog.current_setting('max_wal_senders')::INT AS max_wal_senders,         (SELECT pg_catalog.count(*) FROM pg_catalog.pg_stat_replication) AS attached_wal_receivers,   ` |
| 31 | — | SELECT | 0.03 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 32 | — | SET | 0.08 | `SET synchronous_commit TO 'local'` |
| 33 | nodes | SELECT | 0.58 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, un.node_name AS upstream_node_name,` |
| 34 | — | SET | 52.33 | `SET synchronous_commit TO 'local'` |
| 35 | pg_stat_replication | SELECT | 1.11 | `SELECT pid, state    FROM pg_catalog.pg_stat_replication   WHERE application_name = 'benchmarks-postgresql-postgresql-ha-postgresql-0'` |
| 36 | — | SET | 0.07 | `SET synchronous_commit TO 'local'` |
| 37 | — | SELECT | 0.12 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 38 | — | SELECT | 0.05 | `SELECT repmgr.get_repmgrd_pid()` |
| 39 | — | SELECT | 0.03 | `SELECT repmgr.repmgrd_is_running()` |
| 40 | — | SELECT | 0.02 | `SELECT repmgr.repmgrd_is_paused()` |
| 41 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 42 | — | SELECT | 0.03 | `SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE    THEN -1    ELSE repmgr.get_upstream_last_seen()  END AS upstream_last_seen` |
| 43 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 44 | nodes | SELECT | 0.36 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, un.node_name AS upstream_node_name,` |
| 45 | — | SET | 0.05 | `SET synchronous_commit TO 'local'` |
| 46 | pg_stat_replication | SELECT | 0.88 | `SELECT pid, state    FROM pg_catalog.pg_stat_replication   WHERE application_name = 'benchmarks-postgresql-postgresql-ha-postgresql-2'` |
| 47 | — | SET | 0.06 | `SET synchronous_commit TO 'local'` |
| 48 | — | SELECT | 0.09 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 49 | — | SELECT | 0.04 | `SELECT repmgr.get_repmgrd_pid()` |
| 50 | — | SELECT | 0.02 | `SELECT repmgr.repmgrd_is_running()` |
| 51 | — | SELECT | 0.01 | `SELECT repmgr.repmgrd_is_paused()` |
| 52 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 53 | — | SELECT | 0.07 | `SELECT paused.wal_replay_paused  AND pg_catalog.pg_last_wal_replay_lsn() < pg_catalog.pg_last_wal_receive_lsn()  FROM (SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE     ` |
| 54 | — | SELECT | 0.02 | `SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE    THEN -1    ELSE repmgr.get_upstream_last_seen()  END AS upstream_last_seen` |
| 55 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 56 | nodes | SELECT | 0.40 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, un.node_name AS upstream_node_name,` |
| 57 | — | SELECT | 0.07 | `SELECT paused.wal_replay_paused  AND pg_catalog.pg_last_wal_replay_lsn() < pg_catalog.pg_last_wal_receive_lsn()  FROM (SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE     ` |
| 58 | nodes | SELECT | 0.07 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |

### `mgmt.get_catalog`

- `GET /v1/catalogs/{cat}` → **200**
- wall 8 ms · 14 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 1.25 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | — | — | 0.04 | ` ` |
| 8 | — | — | 0.01 | ` ` |
| 9 | — | — | 0.02 | ` ` |
| 10 | — | — | 0.02 | ` ` |
| 11 | — | — | 0.01 | ` ` |
| 12 | — | — | 0.01 | ` ` |
| 13 | — | — | 0.01 | ` ` |

### `mgmt.create_principal`

- `POST /v1/principals` → **201**
- wall 36 ms · 28 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, principal_authentication_data

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.14 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.16 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 2.42 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | principal_authentication_data | SELECT | 0.02 | `SELECT principal_id, principal_client_id, main_secret_hash, secondary_secret_hash, secret_salt FROM POLARIS_SCHEMA.PRINCIPAL_AUTHENTICATION_DATA WHERE realm_id = ? AND principal_cl` |
| 9 | principal_authentication_data | INSERT | 0.07 | `INSERT INTO POLARIS_SCHEMA.PRINCIPAL_AUTHENTICATION_DATA (principal_id, principal_client_id, main_secret_hash, secondary_secret_hash, secret_salt, realm_id) VALUES (?, ?, ?, ?, ?, ` |
| 10 | entities | INSERT | 0.07 | `INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestam` |
| 11 | — | SELECT | 0.20 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 12 | — | SELECT | 0.28 | `SELECT 1` |
| 13 | — | — | 0.04 | `DISCARD ALL` |
| 14 | — | — | 0.12 | ` ` |
| 15 | — | — | 0.16 | ` ` |
| 16 | — | — | 0.04 | ` ` |
| 17 | — | — | 0.04 | ` ` |
| 18 | — | — | 0.06 | ` ` |
| 19 | — | — | 0.01 | ` ` |
| 20 | — | — | 0.02 | ` ` |
| 21 | — | — | 0.02 | ` ` |
| 22 | — | — | 0.02 | ` ` |
| 23 | — | — | 0.01 | ` ` |
| 24 | — | — | 0.03 | ` ` |
| 25 | — | SELECT | 0.21 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 26 | — | — | 0.07 | `DISCARD ALL` |
| 27 | — | SELECT | 0.19 | `SELECT pg_catalog.pg_is_in_recovery()` |

### `mgmt.get_principal`

- `GET /v1/principals/{p}` → **200**
- wall 16 ms · 26 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, nodes, pg_stat_replication

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 2.12 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | grant_records | SELECT | 1.78 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 8 | grant_records | SELECT | 0.02 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 9 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | — | — | 0.05 | ` ` |
| 11 | — | — | 0.09 | ` ` |
| 12 | — | — | 0.03 | ` ` |
| 13 | — | — | 0.01 | ` ` |
| 14 | — | — | 0.01 | ` ` |
| 15 | — | — | 0.02 | ` ` |
| 16 | — | — | 0.06 | ` ` |
| 17 | — | — | 0.02 | ` ` |
| 18 | — | — | 0.03 | ` ` |
| 19 | — | — | 0.01 | ` ` |
| 20 | — | SELECT | 0.26 | `SELECT TRUE` |
| 21 | — | SELECT | 0.13 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 22 | — | SET | 0.08 | `SET synchronous_commit TO 'local'` |
| 23 | nodes | SELECT | 0.36 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 24 | pg_stat_replication | SELECT | 1.06 | `SELECT pg_catalog.current_setting('max_wal_senders')::INT AS max_wal_senders,         (SELECT pg_catalog.count(*) FROM pg_catalog.pg_stat_replication) AS attached_wal_receivers,   ` |
| 25 | — | SELECT | 0.02 | `SELECT pg_catalog.pg_is_in_recovery()` |

### `mgmt.list_principals`

- `GET /v1/principals` → **200**
- wall 25 ms · 26 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, nodes

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 2.00 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 1.64 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | — | SELECT | 0.14 | `SELECT repmgr.set_upstream_last_seen(1001)` |
| 9 | — | SELECT | 0.06 | `SELECT TRUE` |
| 10 | — | SELECT | 0.22 | `SELECT repmgr.get_local_node_id()` |
| 11 | nodes | SELECT | 0.24 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 12 | — | — | 0.09 | ` ` |
| 13 | — | — | 0.08 | ` ` |
| 14 | — | — | 0.01 | ` ` |
| 15 | — | — | 0.04 | ` ` |
| 16 | — | — | 0.02 | ` ` |
| 17 | — | — | 0.02 | ` ` |
| 18 | — | — | 0.02 | ` ` |
| 19 | — | — | 0.01 | ` ` |
| 20 | — | SELECT | 0.22 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 21 | — | SELECT | 0.12 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 22 | — | SELECT | 0.24 | `SELECT repmgr.set_upstream_last_seen(1001)` |
| 23 | — | SELECT | 0.03 | `SELECT TRUE` |
| 24 | — | SELECT | 0.12 | `SELECT repmgr.get_local_node_id()` |
| 25 | nodes | SELECT | 0.22 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |

### `mgmt.create_principal_role`

- `POST /v1/principal-roles` → **201**
- wall 34 ms · 16 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.17 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 2.54 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | INSERT | 0.15 | `INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestam` |
| 8 | — | — | 0.19 | ` ` |
| 9 | — | — | 0.06 | ` ` |
| 10 | — | — | 0.04 | ` ` |
| 11 | — | — | 0.06 | ` ` |
| 12 | — | — | 0.07 | ` ` |
| 13 | — | — | 0.03 | ` ` |
| 14 | — | — | 0.03 | ` ` |
| 15 | — | — | 0.02 | ` ` |

### `mgmt.get_principal_role`

- `GET /v1/principal-roles/{r}` → **200**
- wall 38 ms · 21 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 3.55 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.12 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.14 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | grant_records | SELECT | 2.84 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 8 | grant_records | SELECT | 0.04 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 9 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | — | — | 0.53 | ` ` |
| 11 | — | — | 0.07 | ` ` |
| 12 | — | — | 0.07 | ` ` |
| 13 | — | — | 0.03 | ` ` |
| 14 | — | — | 0.08 | ` ` |
| 15 | — | — | 0.04 | ` ` |
| 16 | — | — | 0.04 | ` ` |
| 17 | — | — | 0.03 | ` ` |
| 18 | — | — | 0.02 | ` ` |
| 19 | — | — | 0.02 | ` ` |
| 20 | — | — | 0.28 | ` ` |

### `mgmt.list_principal_roles`

- `GET /v1/principal-roles` → **200**
- wall 47 ms · 16 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.16 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.10 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 5.54 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.11 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.12 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 2.90 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | — | — | 0.28 | ` ` |
| 9 | — | — | 0.08 | ` ` |
| 10 | — | — | 0.05 | ` ` |
| 11 | — | — | 0.04 | ` ` |
| 12 | — | — | 0.09 | ` ` |
| 13 | — | — | 0.10 | ` ` |
| 14 | — | — | 0.12 | ` ` |
| 15 | — | — | 0.07 | ` ` |

### `mgmt.assign_principal_role`

- `PUT /v1/principals/{p}/principal-roles` → **201**
- wall 55 ms · 24 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.22 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.11 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 3.69 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.21 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | grant_records | INSERT | 0.11 | `INSERT INTO POLARIS_SCHEMA.GRANT_RECORDS (securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code, realm_id) VALUES (?, ?, ?, ?, ?, ?)` |
| 8 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | UPDATE | 0.10 | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |
| 10 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | entities | UPDATE | 0.06 | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |
| 12 | — | — | 0.35 | ` ` |
| 13 | — | — | 0.10 | ` ` |
| 14 | — | — | 0.05 | ` ` |
| 15 | — | — | 0.08 | ` ` |
| 16 | — | — | 0.14 | ` ` |
| 17 | — | — | 0.09 | ` ` |
| 18 | — | — | 0.07 | ` ` |
| 19 | — | — | 0.07 | ` ` |
| 20 | — | — | 0.04 | ` ` |
| 21 | — | — | 0.04 | ` ` |
| 22 | — | — | 0.06 | ` ` |
| 23 | — | — | 0.02 | ` ` |

### `mgmt.create_catalog_role`

- `POST /v1/catalogs/{cat}/catalog-roles` → **201**
- wall 19 ms · 22 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, nodes, pg_stat_replication

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 1.87 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | INSERT | 0.11 | `INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestam` |
| 8 | — | — | 0.08 | ` ` |
| 9 | — | — | 0.06 | ` ` |
| 10 | — | — | 0.01 | ` ` |
| 11 | — | — | 0.02 | ` ` |
| 12 | — | — | 0.02 | ` ` |
| 13 | — | — | 0.01 | ` ` |
| 14 | — | — | 0.04 | ` ` |
| 15 | — | — | 0.03 | ` ` |
| 16 | — | SELECT | 0.23 | `SELECT TRUE` |
| 17 | — | SELECT | 0.14 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 18 | — | SET | 0.09 | `SET synchronous_commit TO 'local'` |
| 19 | nodes | SELECT | 0.48 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 20 | pg_stat_replication | SELECT | 1.50 | `SELECT pg_catalog.current_setting('max_wal_senders')::INT AS max_wal_senders,         (SELECT pg_catalog.count(*) FROM pg_catalog.pg_stat_replication) AS attached_wal_receivers,   ` |
| 21 | — | SELECT | 0.02 | `SELECT pg_catalog.pg_is_in_recovery()` |

### `mgmt.list_catalog_roles`

- `GET /v1/catalogs/{cat}/catalog-roles` → **200**
- wall 11 ms · 31 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, nodes, pg_stat_replication

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 1.76 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.14 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | — | SELECT | 0.09 | `SELECT repmgr.set_upstream_last_seen(1001)` |
| 9 | — | SELECT | 0.02 | `SELECT TRUE` |
| 10 | — | SELECT | 0.13 | `SELECT repmgr.get_local_node_id()` |
| 11 | nodes | SELECT | 1.86 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 12 | — | — | 0.07 | ` ` |
| 13 | — | — | 0.04 | ` ` |
| 14 | — | — | 0.01 | ` ` |
| 15 | — | — | 0.01 | ` ` |
| 16 | — | — | 0.02 | ` ` |
| 17 | — | — | 0.02 | ` ` |
| 18 | — | — | 0.02 | ` ` |
| 19 | — | — | 0.04 | ` ` |
| 20 | — | SELECT | 0.07 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 21 | — | SELECT | 0.06 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 22 | — | SELECT | 0.17 | `SELECT 1` |
| 23 | — | SET | 0.11 | `SET synchronous_commit TO 'local'` |
| 24 | nodes | SELECT | 0.55 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 25 | pg_stat_replication | SELECT | 2.00 | `SELECT pg_catalog.current_setting('max_wal_senders')::INT AS max_wal_senders,         (SELECT pg_catalog.count(*) FROM pg_catalog.pg_stat_replication) AS attached_wal_receivers,   ` |
| 26 | — | SELECT | 0.04 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 27 | — | SELECT | 0.20 | `SELECT repmgr.set_upstream_last_seen(1001)` |
| 28 | — | SELECT | 0.04 | `SELECT TRUE` |
| 29 | — | SELECT | 0.11 | `SELECT repmgr.get_local_node_id()` |
| 30 | nodes | SELECT | 0.41 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |

### `mgmt.assign_catalog_role`

- `PUT /v1/principal-roles/{r}/catalog-roles/{cat}` → **201**
- wall 27 ms · 83 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, nodes, pg_stat_replication

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 1.91 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | grant_records | SELECT | 1.52 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 8 | grant_records | SELECT | 0.02 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 9 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | grant_records | SELECT | 1.35 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 12 | grant_records | SELECT | 0.02 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 13 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 14 | grant_records | INSERT | 0.04 | `INSERT INTO POLARIS_SCHEMA.GRANT_RECORDS (securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code, realm_id) VALUES (?, ?, ?, ?, ?, ?)` |
| 15 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 16 | entities | UPDATE | 0.04 | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |
| 17 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 18 | entities | UPDATE | 0.03 | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |
| 19 | — | SET | 0.05 | `SET synchronous_commit TO 'local'` |
| 20 | — | SELECT | 0.10 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 21 | — | SELECT | 0.05 | `SELECT repmgr.get_repmgrd_pid()` |
| 22 | — | SELECT | 0.02 | `SELECT repmgr.repmgrd_is_running()` |
| 23 | — | SELECT | 0.01 | `SELECT repmgr.repmgrd_is_paused()` |
| 24 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 25 | — | SELECT | 0.11 | `SELECT paused.wal_replay_paused  AND pg_catalog.pg_last_wal_replay_lsn() < pg_catalog.pg_last_wal_receive_lsn()  FROM (SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE     ` |
| 26 | — | SELECT | 0.03 | `SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE    THEN -1    ELSE repmgr.get_upstream_last_seen()  END AS upstream_last_seen` |
| 27 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 28 | nodes | SELECT | 0.36 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, un.node_name AS upstream_node_name,` |
| 29 | — | SELECT | 0.02 | `SELECT paused.wal_replay_paused  AND pg_catalog.pg_last_wal_replay_lsn() < pg_catalog.pg_last_wal_receive_lsn()  FROM (SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE     ` |
| 30 | nodes | SELECT | 0.03 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 31 | — | SET | 0.09 | `SET application_name TO 'psql'` |
| 32 | — | — | 0.04 | ` ` |
| 33 | — | — | 0.02 | ` ` |
| 34 | — | — | 0.05 | ` ` |
| 35 | — | — | 0.02 | ` ` |
| 36 | — | — | 0.02 | ` ` |
| 37 | — | — | 0.01 | ` ` |
| 38 | — | — | 0.01 | ` ` |
| 39 | — | — | 0.01 | ` ` |
| 40 | — | — | 0.01 | ` ` |
| 41 | — | — | 0.02 | ` ` |
| 42 | — | — | 0.02 | ` ` |
| 43 | — | — | 0.01 | ` ` |
| 44 | — | — | 0.01 | ` ` |
| 45 | — | — | 0.02 | ` ` |
| 46 | — | — | 0.03 | ` ` |
| 47 | — | SET | 0.06 | `SET synchronous_commit TO 'local'` |
| 48 | nodes | SELECT | 0.59 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, un.node_name AS upstream_node_name,` |
| 49 | — | — | 0.04 | ` ` |
| 50 | — | — | 0.02 | ` ` |
| 51 | — | — | 0.05 | ` ` |
| 52 | — | — | 0.01 | ` ` |
| 53 | — | SET | 0.10 | `SET synchronous_commit TO 'local'` |
| 54 | pg_stat_replication | SELECT | 47.00 | `SELECT pid, state    FROM pg_catalog.pg_stat_replication   WHERE application_name = 'benchmarks-postgresql-postgresql-ha-postgresql-0'` |
| 55 | — | SET | 0.05 | `SET synchronous_commit TO 'local'` |
| 56 | — | SELECT | 0.10 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 57 | — | SELECT | 0.05 | `SELECT repmgr.get_repmgrd_pid()` |
| 58 | — | SELECT | 0.03 | `SELECT repmgr.repmgrd_is_running()` |
| 59 | — | SELECT | 0.02 | `SELECT repmgr.repmgrd_is_paused()` |
| 60 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 61 | — | SELECT | 0.04 | `SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE    THEN -1    ELSE repmgr.get_upstream_last_seen()  END AS upstream_last_seen` |
| 62 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 63 | nodes | SELECT | 0.43 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, un.node_name AS upstream_node_name,` |
| 64 | — | SET | 0.05 | `SET synchronous_commit TO 'local'` |
| 65 | pg_stat_replication | SELECT | 0.98 | `SELECT pid, state    FROM pg_catalog.pg_stat_replication   WHERE application_name = 'benchmarks-postgresql-postgresql-ha-postgresql-2'` |
| 66 | — | SET | 0.04 | `SET application_name TO 'psql'` |
| 67 | — | — | 0.04 | `DISCARD ALL` |
| 68 | — | SET | 0.07 | `SET synchronous_commit TO 'local'` |
| 69 | — | SELECT | 0.14 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 70 | — | SELECT | 0.06 | `SELECT repmgr.get_repmgrd_pid()` |
| 71 | — | SELECT | 0.03 | `SELECT repmgr.repmgrd_is_running()` |
| 72 | — | SELECT | 0.07 | `SELECT repmgr.repmgrd_is_paused()` |
| 73 | — | SELECT | 0.02 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 74 | — | SELECT | 0.12 | `SELECT paused.wal_replay_paused  AND pg_catalog.pg_last_wal_replay_lsn() < pg_catalog.pg_last_wal_receive_lsn()  FROM (SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE     ` |
| 75 | — | SELECT | 0.03 | `SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE    THEN -1    ELSE repmgr.get_upstream_last_seen()  END AS upstream_last_seen` |
| 76 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 77 | nodes | SELECT | 0.32 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, un.node_name AS upstream_node_name,` |
| 78 | — | SELECT | 0.03 | `SELECT paused.wal_replay_paused  AND pg_catalog.pg_last_wal_replay_lsn() < pg_catalog.pg_last_wal_receive_lsn()  FROM (SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE     ` |
| 79 | nodes | SELECT | 0.03 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 80 | — | SET | 0.06 | `SET application_name TO 'psql'` |
| 81 | — | SELECT | 0.11 | `SELECT 1` |
| 82 | — | — | 0.07 | `DISCARD ALL` |

### `mgmt.grant_privilege`

- `PUT /v1/catalogs/{cat}/catalog-roles/{cr}/grants` → **201**
- wall 32 ms · 48 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 1.16 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | grant_records | SELECT | 1.13 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 9 | grant_records | SELECT | 0.02 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 10 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | grant_records | SELECT | 1.15 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 12 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 13 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 14 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 15 | grant_records | SELECT | 1.20 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 16 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 17 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 18 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 19 | grant_records | INSERT | 0.04 | `INSERT INTO POLARIS_SCHEMA.GRANT_RECORDS (securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code, realm_id) VALUES (?, ?, ?, ?, ?, ?)` |
| 20 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 21 | entities | UPDATE | 0.03 | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |
| 22 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 23 | entities | UPDATE | 0.05 | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |
| 24 | — | — | 0.04 | ` ` |
| 25 | — | — | 0.04 | ` ` |
| 26 | — | — | 0.02 | ` ` |
| 27 | — | — | 0.01 | ` ` |
| 28 | — | — | 0.01 | ` ` |
| 29 | — | — | 0.01 | ` ` |
| 30 | — | — | 0.02 | ` ` |
| 31 | — | — | 0.02 | ` ` |
| 32 | — | — | 0.01 | ` ` |
| 33 | — | — | 0.01 | ` ` |
| 34 | — | — | 0.02 | ` ` |
| 35 | — | — | 0.02 | ` ` |
| 36 | — | — | 0.03 | ` ` |
| 37 | — | — | 0.01 | ` ` |
| 38 | — | — | 0.01 | ` ` |
| 39 | — | — | 0.01 | ` ` |
| 40 | — | — | 0.01 | ` ` |
| 41 | — | — | 0.01 | ` ` |
| 42 | — | — | 0.01 | ` ` |
| 43 | — | — | 0.01 | ` ` |
| 44 | — | — | 0.02 | ` ` |
| 45 | — | — | 0.01 | ` ` |
| 46 | — | — | 0.01 | ` ` |
| 47 | — | — | 0.01 | ` ` |

### `mgmt.list_grants`

- `GET /v1/catalogs/{cat}/catalog-roles/{cr}/grants` → **200**
- wall 35 ms · 30 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.10 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 3.37 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.21 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | grant_records | SELECT | 0.05 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 9 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | grant_records | SELECT | 1.25 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 11 | grant_records | SELECT | 0.02 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 12 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 13 | grant_records | SELECT | 1.17 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 14 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 15 | — | — | 0.14 | ` ` |
| 16 | — | — | 0.51 | ` ` |
| 17 | — | — | 0.04 | ` ` |
| 18 | — | — | 0.03 | ` ` |
| 19 | — | — | 0.07 | ` ` |
| 20 | — | — | 0.09 | ` ` |
| 21 | — | — | 0.07 | ` ` |
| 22 | — | — | 0.04 | ` ` |
| 23 | — | — | 0.03 | ` ` |
| 24 | — | — | 0.03 | ` ` |
| 25 | — | — | 0.04 | ` ` |
| 26 | — | — | 0.01 | ` ` |
| 27 | — | — | 0.01 | ` ` |
| 28 | — | — | 0.01 | ` ` |
| 29 | — | — | 0.01 | ` ` |

### `mgmt.list_principals_for_principal_role`

- `GET /v1/principal-roles/{r}/principals` → **200**
- wall 40 ms · 26 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.28 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.12 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.11 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 4.52 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.13 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | grant_records | SELECT | 2.29 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 9 | grant_records | SELECT | 0.03 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 10 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | grant_records | SELECT | 0.04 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 12 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 13 | — | — | 0.31 | ` ` |
| 14 | — | — | 0.12 | ` ` |
| 15 | — | — | 0.08 | ` ` |
| 16 | — | — | 0.05 | ` ` |
| 17 | — | — | 0.06 | ` ` |
| 18 | — | — | 0.03 | ` ` |
| 19 | — | — | 0.08 | ` ` |
| 20 | — | — | 0.09 | ` ` |
| 21 | — | — | 0.06 | ` ` |
| 22 | — | — | 0.04 | ` ` |
| 23 | — | — | 0.03 | ` ` |
| 24 | — | — | 0.01 | ` ` |
| 25 | — | — | 0.02 | ` ` |

### `mgmt.reset_principal_credentials`

- `POST /v1/principals/{p}/reset` → **200**
- wall 43 ms · 35 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, nodes, pg_stat_replication, principal_authentication_data

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.15 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.56 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 2.60 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | grant_records | SELECT | 2.12 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 9 | grant_records | SELECT | 0.04 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 10 | principal_authentication_data | SELECT | 0.05 | `SELECT principal_id, principal_client_id, main_secret_hash, secondary_secret_hash, secret_salt FROM POLARIS_SCHEMA.PRINCIPAL_AUTHENTICATION_DATA WHERE realm_id = ? AND principal_cl` |
| 11 | principal_authentication_data | DELETE | 0.07 | `DELETE FROM POLARIS_SCHEMA.PRINCIPAL_AUTHENTICATION_DATA WHERE realm_id = ? AND principal_id = ? AND principal_client_id = ?` |
| 12 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 13 | principal_authentication_data | INSERT | 0.06 | `INSERT INTO POLARIS_SCHEMA.PRINCIPAL_AUTHENTICATION_DATA (principal_id, principal_client_id, main_secret_hash, secondary_secret_hash, secret_salt, realm_id) VALUES (?, ?, ?, ?, ?, ` |
| 14 | — | SET | 0.23 | `SET synchronous_commit TO 'local'` |
| 15 | nodes | SELECT | 0.98 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 16 | pg_stat_replication | SELECT | 1.93 | `SELECT pg_catalog.current_setting('max_wal_senders')::INT AS max_wal_senders,         (SELECT pg_catalog.count(*) FROM pg_catalog.pg_stat_replication) AS attached_wal_receivers,   ` |
| 17 | — | SELECT | 0.05 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 18 | — | — | 0.12 | ` ` |
| 19 | — | — | 0.16 | ` ` |
| 20 | — | — | 0.03 | ` ` |
| 21 | — | — | 0.07 | ` ` |
| 22 | — | — | 0.01 | ` ` |
| 23 | — | — | 0.01 | ` ` |
| 24 | — | — | 0.02 | ` ` |
| 25 | — | — | 0.05 | ` ` |
| 26 | — | — | 0.01 | ` ` |
| 27 | — | — | 0.03 | ` ` |
| 28 | — | — | 0.02 | ` ` |
| 29 | — | — | 0.01 | ` ` |
| 30 | — | — | 0.05 | ` ` |
| 31 | — | — | 0.04 | ` ` |
| 32 | — | SELECT | 0.17 | `SELECT TRUE` |
| 33 | nodes | SELECT | 1.06 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser,            n.slot_name, n.location, n.priority, n.active, n.config_file,            '' AS upstrea` |
| 34 | — | SELECT | 0.10 | `SELECT pg_catalog.pg_is_in_recovery()` |

### `mgmt.delete_catalog_role`

- `DELETE /v1/catalogs/{cat}/catalog-roles/{cr}` → **204**
- wall 41 ms · 42 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, nodes

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.11 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 2.67 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | entities | DELETE | 0.06 | `DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?` |
| 9 | grant_records | SELECT | 2.36 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 10 | grant_records | SELECT | 0.04 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 11 | grant_records | DELETE | 3.18 | `DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (
    (grantee_id = ? AND grantee_catalog_id = ?) OR
    (securable_id = ? AND securable_catalog_id = ?)
) AND realm_id = ?` |
| 12 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 13 | entities | UPDATE | 0.07 | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |
| 14 | entities | UPDATE | 0.09 | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |
| 15 | entities | INSERT | 0.07 | `INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestam` |
| 16 | — | SELECT | 0.13 | `SELECT repmgr.set_upstream_last_seen(1001)` |
| 17 | — | SELECT | 0.02 | `SELECT TRUE` |
| 18 | — | SELECT | 0.06 | `SELECT repmgr.get_local_node_id()` |
| 19 | nodes | SELECT | 0.12 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 20 | — | — | 0.15 | ` ` |
| 21 | — | — | 0.03 | ` ` |
| 22 | — | — | 0.02 | ` ` |
| 23 | — | — | 0.02 | ` ` |
| 24 | — | — | 0.10 | ` ` |
| 25 | — | — | 0.02 | ` ` |
| 26 | — | — | 0.02 | ` ` |
| 27 | — | — | 0.03 | ` ` |
| 28 | — | — | 0.03 | ` ` |
| 29 | — | — | 0.03 | ` ` |
| 30 | — | — | 0.04 | ` ` |
| 31 | — | — | 0.02 | `  (grantee_id = $1 AND grantee_catalog_id = $2) OR (securable_id = $3 AND securable_catalog_id = $4) ) AND realm_id = $5` |
| 32 | — | — | 0.04 | ` ` |
| 33 | — | — | 0.02 | ` ` |
| 34 | — | — | 0.33 | ` ` |
| 35 | — | — | 0.03 | ` ` |
| 36 | — | SELECT | 0.13 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 37 | — | SELECT | 0.09 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 38 | — | SELECT | 0.22 | `SELECT repmgr.set_upstream_last_seen(1001)` |
| 39 | — | SELECT | 0.03 | `SELECT TRUE` |
| 40 | — | SELECT | 0.27 | `SELECT repmgr.get_local_node_id()` |
| 41 | nodes | SELECT | 0.26 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |

### `mgmt.delete_principal_role`

- `DELETE /v1/principal-roles/{r}` → **204**
- wall 48 ms · 36 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.15 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 4.53 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.18 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | grant_records | SELECT | 1.89 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 9 | grant_records | SELECT | 0.03 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 10 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | entities | DELETE | 0.04 | `DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?` |
| 12 | grant_records | SELECT | 1.79 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 13 | grant_records | SELECT | 0.04 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 14 | grant_records | DELETE | 2.48 | `DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (
    (grantee_id = ? AND grantee_catalog_id = ?) OR
    (securable_id = ? AND securable_catalog_id = ?)
) AND realm_id = ?` |
| 15 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 16 | entities | UPDATE | 0.07 | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |
| 17 | entities | INSERT | 0.11 | `INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestam` |
| 18 | — | — | 0.12 | ` ` |
| 19 | — | — | 0.09 | ` ` |
| 20 | — | — | 0.10 | ` ` |
| 21 | — | — | 0.11 | ` ` |
| 22 | — | — | 0.11 | ` ` |
| 23 | — | — | 0.03 | ` ` |
| 24 | — | — | 0.08 | ` ` |
| 25 | — | — | 0.01 | ` ` |
| 26 | — | — | 0.01 | ` ` |
| 27 | — | — | 0.01 | ` ` |
| 28 | — | — | 0.01 | ` ` |
| 29 | — | — | 0.01 | ` ` |
| 30 | — | — | 0.02 | ` ` |
| 31 | — | — | 0.01 | ` ` |
| 32 | — | — | 0.03 | `  (grantee_id = $1 AND grantee_catalog_id = $2) OR (securable_id = $3 AND securable_catalog_id = $4) ) AND realm_id = $5` |
| 33 | — | — | 0.04 | ` ` |
| 34 | — | — | 0.02 | ` ` |
| 35 | — | — | 0.05 | ` ` |

### `mgmt.delete_principal`

- `DELETE /v1/principals/{p}` → **204**
- wall 56 ms · 32 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, principal_authentication_data

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.24 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.10 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.20 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 6.14 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.11 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.18 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | grant_records | SELECT | 2.44 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 9 | grant_records | SELECT | 0.05 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 10 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | entities | DELETE | 0.05 | `DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?` |
| 12 | grant_records | SELECT | 2.23 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 13 | grant_records | SELECT | 0.04 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 14 | grant_records | DELETE | 3.48 | `DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (
    (grantee_id = ? AND grantee_catalog_id = ?) OR
    (securable_id = ? AND securable_catalog_id = ?)
) AND realm_id = ?` |
| 15 | principal_authentication_data | DELETE | 0.06 | `DELETE FROM POLARIS_SCHEMA.PRINCIPAL_AUTHENTICATION_DATA WHERE realm_id = ? AND principal_id = ? AND principal_client_id = ?` |
| 16 | — | — | 0.27 | ` ` |
| 17 | — | — | 0.08 | ` ` |
| 18 | — | — | 0.07 | ` ` |
| 19 | — | — | 0.07 | ` ` |
| 20 | — | — | 0.12 | ` ` |
| 21 | — | — | 0.06 | ` ` |
| 22 | — | — | 0.06 | ` ` |
| 23 | — | — | 0.03 | ` ` |
| 24 | — | — | 0.03 | ` ` |
| 25 | — | — | 0.02 | ` ` |
| 26 | — | — | 0.02 | ` ` |
| 27 | — | — | 0.01 | ` ` |
| 28 | — | — | 0.04 | ` ` |
| 29 | — | — | 0.02 | ` ` |
| 30 | — | — | 0.05 | `  (grantee_id = $1 AND grantee_catalog_id = $2) OR (securable_id = $3 AND securable_catalog_id = $4) ) AND realm_id = $5` |
| 31 | — | — | 0.01 | ` ` |
