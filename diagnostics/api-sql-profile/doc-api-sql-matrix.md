# API → SQL → MinIO Access Matrix

Generated 2026-08-20 12:05 from a live local run — Polaris 1.3.0, realm POLARIS.
Schema version 3 (DRIFT).

R = read, W = write, RW = both.

## API → PostgreSQL tables

| API | entities | grant_records | nodes | pg_stat_replication | policy_mapping_record | principal_authentication_data | replay_lag |
|---|---|---|---|---|---|---|---|
| `iceberg.commit_table` | RW | R | R | · | · | · | · |
| `iceberg.create_namespace` | RW | R | · | · | · | · | · |
| `iceberg.create_table` | RW | R | · | · | · | · | · |
| `iceberg.create_view` | RW | R | · | · | · | · | · |
| `iceberg.drop_namespace` | RW | RW | R | · | RW | · | · |
| `iceberg.drop_table` | RW | RW | · | · | RW | · | · |
| `iceberg.drop_view` | RW | RW | R | R | · | · | · |
| `iceberg.get_config` | R | R | R | · | · | · | · |
| `iceberg.head_namespace` | R | R | · | · | · | · | · |
| `iceberg.head_table` | R | R | · | · | · | · | · |
| `iceberg.head_view` | R | R | · | · | · | · | · |
| `iceberg.list_namespaces` | R | R | R | R | · | · | · |
| `iceberg.list_tables` | R | R | R | R | · | · | · |
| `iceberg.list_views` | R | R | · | · | · | · | · |
| `iceberg.load_namespace` | R | R | · | · | · | · | · |
| `iceberg.load_table` | R | R | R | · | · | · | · |
| `iceberg.load_table[missing]` | R | R | R | R | · | · | · |
| `iceberg.load_table[snapshots=refs]` | R | R | R | R | · | · | · |
| `iceberg.load_view` | R | R | R | · | · | · | · |
| `iceberg.rename_table` | RW | R | R | R | · | · | R |
| `iceberg.rename_view` | RW | R | · | · | · | · | · |
| `iceberg.report_metrics` | R | R | · | · | · | · | · |
| `iceberg.stage_create_table` | R | R | · | · | · | · | · |
| `iceberg.update_namespace_properties` | RW | R | · | · | · | · | · |
| `mgmt.assign_catalog_role` | RW | RW | · | · | · | · | · |
| `mgmt.assign_principal_role` | RW | RW | · | · | · | · | · |
| `mgmt.create_catalog_role` | RW | R | · | · | · | · | · |
| `mgmt.create_principal` | RW | R | R | · | · | RW | · |
| `mgmt.create_principal_role` | RW | R | R | R | · | · | · |
| `mgmt.delete_catalog_role` | RW | RW | · | · | · | · | · |
| `mgmt.delete_principal` | RW | RW | · | · | · | W | · |
| `mgmt.delete_principal_role` | RW | RW | · | · | · | · | · |
| `mgmt.get_catalog` | R | R | · | · | · | · | · |
| `mgmt.get_principal` | R | R | · | · | · | · | · |
| `mgmt.get_principal_role` | R | R | · | · | · | · | · |
| `mgmt.grant_privilege` | RW | RW | · | · | · | · | · |
| `mgmt.list_catalog_roles` | R | R | · | · | · | · | · |
| `mgmt.list_catalogs` | R | R | · | · | · | · | · |
| `mgmt.list_grants` | R | R | R | R | · | · | R |
| `mgmt.list_principal_roles` | R | R | R | R | · | · | · |
| `mgmt.list_principals` | R | R | R | R | · | · | · |
| `mgmt.list_principals_for_principal_role` | R | R | · | · | · | · | · |
| `mgmt.reset_principal_credentials` | R | R | R | R | · | RW | · |

## API → MinIO objects

| API | Method | Path | Count |
|---|---|---|---|
| `iceberg.load_table` |  | `/data-catalog-bucket/apiprofile1787195026_cat/probe_ns/probe_tbl/metadata/00000-116ee59f-5357-49eb-a97b-a6fde09ca16f.metadata.json` | 1 |
| `iceberg.load_table[snapshots=refs]` |  | `/data-catalog-bucket/apiprofile1787195026_cat/probe_ns/probe_tbl/metadata/00000-116ee59f-5357-49eb-a97b-a6fde09ca16f.metadata.json` | 1 |
| `iceberg.head_table` |  | `/data-catalog-bucket/apiprofile1787195026_cat/probe_ns/probe_tbl/metadata/00000-116ee59f-5357-49eb-a97b-a6fde09ca16f.metadata.json` | 1 |
| `iceberg.create_table` |  | `/data-catalog-bucket/apiprofile1787195026_cat/probe_ns/probe_tbl2/metadata/00000-0dcbeb26-dd38-4382-af63-8808fcec99ee.metadata.json` | 1 |
| `iceberg.commit_table` |  | `/data-catalog-bucket/apiprofile1787195026_cat/probe_ns/probe_tbl/metadata/00000-116ee59f-5357-49eb-a97b-a6fde09ca16f.metadata.json` | 1 |
| `iceberg.commit_table` |  | `/data-catalog-bucket/apiprofile1787195026_cat/probe_ns/probe_tbl/metadata/00001-790df045-cc10-491f-9288-278f6bb34900.metadata.json` | 1 |
| `iceberg.create_view` |  | `/data-catalog-bucket/apiprofile1787195026_cat/probe_ns/probe_view/metadata/00000-11ddf866-6f22-44ad-9a89-7b3aaa90ed84.gz.metadata.json` | 2 |
| `iceberg.load_view` |  | `/data-catalog-bucket/apiprofile1787195026_cat/probe_ns/probe_view/metadata/00000-11ddf866-6f22-44ad-9a89-7b3aaa90ed84.gz.metadata.json` | 2 |
| `iceberg.head_view` |  | `/data-catalog-bucket/apiprofile1787195026_cat/probe_ns/probe_view/metadata/00000-11ddf866-6f22-44ad-9a89-7b3aaa90ed84.gz.metadata.json` | 2 |

## Per-API detail

### `iceberg.get_config`

- `GET /v1/config` → **200**
- wall 33 ms · 32 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, nodes

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.28 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 6.37 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.24 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | — | SELECT | 0.25 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 8 | — | SELECT | 0.09 | `SELECT repmgr.set_upstream_last_seen(1001)` |
| 9 | — | SELECT | 0.01 | `SELECT TRUE` |
| 10 | — | SELECT | 0.07 | `SELECT repmgr.get_local_node_id()` |
| 11 | nodes | SELECT | 0.08 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 12 | — | — | 0.17 | ` ` |
| 13 | — | — | 0.06 | ` ` |
| 14 | — | — | 0.11 | ` ` |
| 15 | — | — | 0.07 | ` ` |
| 16 | — | — | 0.12 | ` ` |
| 17 | — | — | 0.05 | ` ` |
| 18 | — | — | 0.23 | ` ` |
| 19 | — | SELECT | 0.21 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 20 | — | SELECT | 0.18 | `SELECT TRUE` |
| 21 | nodes | SELECT | 0.50 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser,            n.slot_name, n.location, n.priority, n.active, n.config_file,            '' AS upstrea` |
| 22 | — | SELECT | 0.03 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 23 | — | SELECT | 0.05 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 24 | — | SELECT | 0.04 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 25 | — | SELECT | 0.11 | `SELECT 1` |
| 26 | — | — | 0.02 | `DISCARD ALL` |
| 27 | — | SELECT | 0.17 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 28 | — | SELECT | 0.19 | `SELECT repmgr.set_upstream_last_seen(1001)` |
| 29 | — | SELECT | 0.03 | `SELECT TRUE` |
| 30 | — | SELECT | 0.07 | `SELECT repmgr.get_local_node_id()` |
| 31 | nodes | SELECT | 0.10 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |

### `iceberg.list_namespaces`

- `GET /v1/{cat}/namespaces` → **200**
- wall 9 ms · 20 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, nodes, pg_stat_replication

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 1.56 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND sub_type_code = ? AND realm_id = ? AND parent_id = ? AND type` |
| 8 | — | — | 0.04 | ` ` |
| 9 | — | — | 0.01 | ` ` |
| 10 | — | — | 0.01 | ` ` |
| 11 | — | — | 0.01 | ` ` |
| 12 | — | — | 0.02 | ` ` |
| 13 | — | — | 0.01 | ` ` |
| 14 | — | — | 0.03 | ` ` |
| 15 | — | — | 0.01 | ` ` |
| 16 | — | SET | 0.08 | `SET synchronous_commit TO 'local'` |
| 17 | nodes | SELECT | 0.37 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 18 | pg_stat_replication | SELECT | 1.16 | `SELECT pg_catalog.current_setting('max_wal_senders')::INT AS max_wal_senders,         (SELECT pg_catalog.count(*) FROM pg_catalog.pg_stat_replication) AS attached_wal_receivers,   ` |
| 19 | — | SELECT | 0.02 | `SELECT pg_catalog.pg_is_in_recovery()` |

### `iceberg.load_namespace`

- `GET /v1/{cat}/namespaces/{ns}` → **200**
- wall 14 ms · 14 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 2.28 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | — | — | 0.07 | ` ` |
| 8 | — | — | 0.01 | ` ` |
| 9 | — | — | 0.04 | ` ` |
| 10 | — | — | 0.04 | ` ` |
| 11 | — | — | 0.03 | ` ` |
| 12 | — | — | 0.02 | ` ` |
| 13 | — | — | 0.04 | ` ` |

### `iceberg.head_namespace`

- `HEAD /v1/{cat}/namespaces/{ns}` → **204**
- wall 36 ms · 14 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.18 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 3.47 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.17 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | — | — | 0.30 | ` ` |
| 8 | — | — | 0.13 | ` ` |
| 9 | — | — | 0.06 | ` ` |
| 10 | — | — | 0.03 | ` ` |
| 11 | — | — | 0.06 | ` ` |
| 12 | — | — | 0.05 | ` ` |
| 13 | — | — | 0.10 | ` ` |

### `iceberg.update_namespace_properties`

- `POST /v1/{cat}/namespaces/{ns}/properties` → **200**
- wall 50 ms · 21 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.17 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.14 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.16 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 4.78 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.12 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.12 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND realm_id = ? AND type_code = ? AND catalog_id = ?` |
| 8 | entities | SELECT | 0.10 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | UPDATE | 0.12 | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |
| 10 | — | — | 0.39 | ` ` |
| 11 | — | — | 0.28 | ` ` |
| 12 | — | — | 0.14 | ` ` |
| 13 | — | — | 0.08 | ` ` |
| 14 | — | — | 0.20 | ` ` |
| 15 | — | — | 0.06 | ` ` |
| 16 | — | — | 0.09 | ` ` |
| 17 | — | — | 0.05 | ` ` |
| 18 | — | — | 0.04 | ` ` |
| 19 | — | — | 0.03 | ` ` |
| 20 | — | — | 0.34 | ` ` |

### `iceberg.create_namespace`

- `POST /v1/{cat}/namespaces` → **200**
- wall 38 ms · 32 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.14 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 2.26 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND realm_id = ? AND type_code = ? AND catalog_id = ?` |
| 9 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 12 | entities | INSERT | 0.11 | `INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestam` |
| 13 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 14 | grant_records | SELECT | 0.03 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 15 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 16 | — | — | 0.16 | ` ` |
| 17 | — | — | 0.16 | ` ` |
| 18 | — | — | 0.02 | ` ` |
| 19 | — | — | 0.03 | ` ` |
| 20 | — | — | 0.01 | ` ` |
| 21 | — | — | 0.01 | ` ` |
| 22 | — | — | 0.02 | ` ` |
| 23 | — | — | 0.01 | ` ` |
| 24 | — | — | 0.07 | ` ` |
| 25 | — | — | 0.02 | ` ` |
| 26 | — | — | 0.03 | ` ` |
| 27 | — | — | 0.02 | ` ` |
| 28 | — | — | 0.01 | ` ` |
| 29 | — | — | 0.06 | ` ` |
| 30 | — | — | 0.04 | ` ` |
| 31 | — | — | 0.02 | ` ` |

### `iceberg.drop_namespace`

- `DELETE /v1/{cat}/namespaces/{ns}` → **204**
- wall 50 ms · 40 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, nodes, policy_mapping_record

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.14 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.12 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.12 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 6.43 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.16 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.11 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | DELETE | 0.04 | `DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?` |
| 10 | grant_records | SELECT | 0.06 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 11 | grant_records | DELETE | 4.04 | `DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (` |
| 12 | policy_mapping_record | SELECT | 0.02 | `SELECT target_catalog_id, target_id, policy_type_code, policy_catalog_id, policy_id, parameters FROM POLARIS_SCHEMA.POLICY_MAPPING_RECORD WHERE realm_id = ? AND target_id = ? AND t` |
| 13 | policy_mapping_record | DELETE | 0.04 | `DELETE FROM POLARIS_SCHEMA.POLICY_MAPPING_RECORD WHERE target_catalog_id = ? AND target_id = ? AND realm_id = ?` |
| 14 | — | SELECT | 0.23 | `SELECT repmgr.set_upstream_last_seen(1001)` |
| 15 | — | SELECT | 0.04 | `SELECT TRUE` |
| 16 | — | SELECT | 0.27 | `SELECT repmgr.get_local_node_id()` |
| 17 | nodes | SELECT | 0.18 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 18 | — | — | 0.38 | ` ` |
| 19 | — | — | 0.09 | ` ` |
| 20 | — | — | 0.14 | ` ` |
| 21 | — | — | 0.11 | ` ` |
| 22 | — | — | 0.05 | ` ` |
| 23 | — | — | 0.06 | ` ` |
| 24 | — | — | 0.12 | ` ` |
| 25 | — | — | 0.10 | ` ` |
| 26 | — | — | 0.02 | ` ` |
| 27 | — | — | 0.01 | ` ` |
| 28 | — | — | 0.02 | ` ` |
| 29 | — | — | 0.01 | ` ` |
| 30 | — | — | 0.04 | ` ` |
| 31 | — | — | 0.03 | ` ` |
| 32 | — | SELECT | 0.55 | `SELECT TRUE` |
| 33 | — | SELECT | 1.11 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 34 | — | SELECT | 0.12 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 35 | — | SELECT | 0.12 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 36 | — | SELECT | 0.21 | `SELECT repmgr.set_upstream_last_seen(1001)` |
| 37 | — | SELECT | 0.14 | `SELECT TRUE` |
| 38 | — | SELECT | 0.13 | `SELECT repmgr.get_local_node_id()` |
| 39 | nodes | SELECT | 0.21 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |

### `iceberg.list_tables`

- `GET /v1/{cat}/namespaces/{ns}/tables` → **200**
- wall 38 ms · 30 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, nodes, pg_stat_replication

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 27.23 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND sub_type_code = ? AND realm_id = ? AND parent_id = ? AND type` |
| 8 | — | — | 0.03 | ` ` |
| 9 | — | — | 0.03 | ` ` |
| 10 | — | — | 0.02 | ` ` |
| 11 | — | — | 0.02 | ` ` |
| 12 | — | SET | 0.07 | `SET synchronous_commit TO 'local'` |
| 13 | pg_stat_replication | SELECT | 25.26 | `SELECT pid, state    FROM pg_catalog.pg_stat_replication   WHERE application_name = 'benchmarks-postgresql-postgresql-ha-postgresql-2'` |
| 14 | — | — | 0.04 | ` ` |
| 15 | — | — | 0.02 | ` ` |
| 16 | — | — | 0.09 | ` ` |
| 17 | — | — | 0.04 | ` ` |
| 18 | — | SET | 0.13 | `SET synchronous_commit TO 'local'` |
| 19 | — | SELECT | 0.17 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 20 | — | SELECT | 0.07 | `SELECT repmgr.get_repmgrd_pid()` |
| 21 | — | SELECT | 0.03 | `SELECT repmgr.repmgrd_is_running()` |
| 22 | — | SELECT | 0.02 | `SELECT repmgr.repmgrd_is_paused()` |
| 23 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 24 | — | SELECT | 0.13 | `SELECT paused.wal_replay_paused  AND pg_catalog.pg_last_wal_replay_lsn() < pg_catalog.pg_last_wal_receive_lsn()  FROM (SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE     ` |
| 25 | — | SELECT | 0.03 | `SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE    THEN -1    ELSE repmgr.get_upstream_last_seen()  END AS upstream_last_seen` |
| 26 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 27 | nodes | SELECT | 0.44 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, un.node_name AS upstream_node_name,` |
| 28 | — | SELECT | 0.03 | `SELECT paused.wal_replay_paused  AND pg_catalog.pg_last_wal_replay_lsn() < pg_catalog.pg_last_wal_receive_lsn()  FROM (SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE     ` |
| 29 | nodes | SELECT | 0.04 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |

### `iceberg.load_table`

- `GET /v1/{cat}/namespaces/{ns}/tables/{tbl}` → **200**
- wall 55 ms · 38 statements · 1 object ops · cache: MISS
- tables: entities, grant_records, nodes

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 2.07 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | — | SELECT | 0.22 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 11 | — | SELECT | 0.16 | `SELECT 1` |
| 12 | — | — | 0.03 | `DISCARD ALL` |
| 13 | — | SELECT | 0.10 | `SELECT repmgr.set_upstream_last_seen(1001)` |
| 14 | — | SELECT | 0.01 | `SELECT TRUE` |
| 15 | — | SELECT | 0.07 | `SELECT repmgr.get_local_node_id()` |
| 16 | nodes | SELECT | 0.11 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 17 | — | — | 0.17 | ` ` |
| 18 | — | — | 0.02 | ` ` |
| 19 | — | — | 0.01 | ` ` |
| 20 | — | — | 0.02 | ` ` |
| 21 | — | — | 0.01 | ` ` |
| 22 | — | — | 0.01 | ` ` |
| 23 | — | — | 0.04 | ` ` |
| 24 | — | — | 0.02 | ` ` |
| 25 | — | — | 0.04 | ` ` |
| 26 | — | SELECT | 0.20 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 27 | — | — | 0.05 | ` ` |
| 28 | — | — | 0.04 | `DISCARD ALL` |
| 29 | — | SELECT | 0.09 | `SELECT TRUE` |
| 30 | — | SELECT | 0.05 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 31 | — | SELECT | 0.04 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 32 | — | SELECT | 0.05 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 33 | — | SELECT | 0.19 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 34 | — | SELECT | 0.09 | `SELECT repmgr.set_upstream_last_seen(1001)` |
| 35 | — | SELECT | 0.02 | `SELECT TRUE` |
| 36 | — | SELECT | 1.26 | `SELECT repmgr.get_local_node_id()` |
| 37 | nodes | SELECT | 0.10 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |

| # | Method | Path | ms |
|---|---|---|---|
| 0 |  | `/data-catalog-bucket/apiprofile1787195026_cat/probe_ns/probe_tbl/metadata/00000-116ee59f-5357-49eb-a97b-a6fde09ca16f.metadata.json` | 1.07 |

### `iceberg.load_table[snapshots=refs]`

- `GET /v1/{cat}/.../tables/{tbl}?snapshots=refs` → **200**
- wall 20 ms · 20 statements · 1 object ops · cache: MISS
- tables: entities, grant_records, nodes, pg_stat_replication

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 1.20 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.13 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | — | — | 0.04 | ` ` |
| 9 | — | — | 0.01 | ` ` |
| 10 | — | — | 0.01 | ` ` |
| 11 | — | — | 0.01 | ` ` |
| 12 | — | — | 0.01 | ` ` |
| 13 | — | — | 0.00 | ` ` |
| 14 | — | — | 0.04 | ` ` |
| 15 | — | — | 0.02 | ` ` |
| 16 | — | SET | 0.11 | `SET synchronous_commit TO 'local'` |
| 17 | nodes | SELECT | 0.33 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 18 | pg_stat_replication | SELECT | 0.98 | `SELECT pg_catalog.current_setting('max_wal_senders')::INT AS max_wal_senders,         (SELECT pg_catalog.count(*) FROM pg_catalog.pg_stat_replication) AS attached_wal_receivers,   ` |
| 19 | — | SELECT | 0.03 | `SELECT pg_catalog.pg_is_in_recovery()` |

| # | Method | Path | ms |
|---|---|---|---|
| 0 |  | `/data-catalog-bucket/apiprofile1787195026_cat/probe_ns/probe_tbl/metadata/00000-116ee59f-5357-49eb-a97b-a6fde09ca16f.metadata.json` | 0.93 |

### `iceberg.head_table`

- `HEAD /v1/{cat}/namespaces/{ns}/tables/{tbl}` → **204**
- wall 47 ms · 16 statements · 1 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.19 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.10 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 3.20 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.17 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.13 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.12 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.10 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | — | — | 0.18 | ` ` |
| 9 | — | — | 0.15 | ` ` |
| 10 | — | — | 0.16 | ` ` |
| 11 | — | — | 0.02 | ` ` |
| 12 | — | — | 0.06 | ` ` |
| 13 | — | — | 0.07 | ` ` |
| 14 | — | — | 0.08 | ` ` |
| 15 | — | — | 0.04 | ` ` |

| # | Method | Path | ms |
|---|---|---|---|
| 0 |  | `/data-catalog-bucket/apiprofile1787195026_cat/probe_ns/probe_tbl/metadata/00000-116ee59f-5357-49eb-a97b-a6fde09ca16f.metadata.json` | 1.63 |

### `iceberg.create_table`

- `POST /v1/{cat}/namespaces/{ns}/tables` → **200**
- wall 90 ms · 48 statements · 1 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.20 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.10 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 6.28 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.15 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 12 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 13 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 14 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 15 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND realm_id = ? AND type_code = ? AND catalog_id = ?` |
| 16 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND realm_id = ? AND type_code = ? AND catalog_id = ?` |
| 17 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 18 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 19 | entities | SELECT | 0.10 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 20 | entities | INSERT | 0.11 | `INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestam` |
| 21 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 22 | grant_records | SELECT | 0.04 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 23 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 24 | — | — | 0.19 | ` ` |
| 25 | — | — | 0.22 | ` ` |
| 26 | — | — | 0.09 | ` ` |
| 27 | — | — | 0.10 | ` ` |
| 28 | — | — | 0.05 | ` ` |
| 29 | — | — | 0.04 | ` ` |
| 30 | — | — | 0.05 | ` ` |
| 31 | — | — | 0.03 | ` ` |
| 32 | — | — | 0.03 | ` ` |
| 33 | — | — | 0.04 | ` ` |
| 34 | — | — | 0.07 | ` ` |
| 35 | — | — | 0.01 | ` ` |
| 36 | — | — | 0.03 | ` ` |
| 37 | — | — | 0.01 | ` ` |
| 38 | — | — | 0.02 | ` ` |
| 39 | — | — | 0.09 | ` ` |
| 40 | — | — | 0.01 | ` ` |
| 41 | — | — | 0.09 | ` ` |
| 42 | — | — | 0.13 | ` ` |
| 43 | — | — | 0.05 | ` ` |
| 44 | — | — | 0.04 | ` ` |
| 45 | — | — | 0.02 | ` ` |
| 46 | — | — | 0.02 | ` ` |
| 47 | — | — | 0.02 | ` ` |

| # | Method | Path | ms |
|---|---|---|---|
| 0 |  | `/data-catalog-bucket/apiprofile1787195026_cat/probe_ns/probe_tbl2/metadata/00000-0dcbeb26-dd38-4382-af63-8808fcec99ee.metadata.json` | 7.78 |

### `iceberg.stage_create_table`

- `POST /v1/{cat}/namespaces/{ns}/tables[stage]` → **200**
- wall 49 ms · 27 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.12 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 5.02 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.12 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | SELECT | 0.12 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 12 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 13 | — | — | 0.13 | ` ` |
| 14 | — | — | 0.11 | ` ` |
| 15 | — | — | 0.08 | ` ` |
| 16 | — | — | 0.12 | ` ` |
| 17 | — | — | 0.10 | ` ` |
| 18 | — | — | 0.06 | ` ` |
| 19 | — | — | 0.10 | ` ` |
| 20 | — | — | 0.13 | ` ` |
| 21 | — | — | 0.04 | ` ` |
| 22 | — | — | 0.09 | ` ` |
| 23 | — | — | 0.05 | ` ` |
| 24 | — | — | 0.05 | ` ` |
| 25 | — | — | 0.03 | ` ` |
| 26 | — | — | 0.08 | ` ` |

### `iceberg.commit_table`

- `POST /v1/{cat}/namespaces/{ns}/tables/{tbl}` → **200**
- wall 84 ms · 33 statements · 2 object ops · cache: MISS
- tables: entities, grant_records, nodes

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.14 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.10 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 6.47 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.16 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.10 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | entities | SELECT | 0.21 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | SELECT | 0.13 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | entities | UPDATE | 0.09 | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |
| 11 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 12 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 13 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 14 | — | — | 0.10 | ` ` |
| 15 | — | — | 0.07 | ` ` |
| 16 | — | — | 0.05 | ` ` |
| 17 | — | — | 0.07 | ` ` |
| 18 | — | — | 0.04 | ` ` |
| 19 | — | — | 0.32 | ` ` |
| 20 | — | — | 0.38 | ` ` |
| 21 | — | — | 0.09 | ` ` |
| 22 | — | — | 0.04 | ` ` |
| 23 | — | — | 0.08 | ` ` |
| 24 | — | — | 0.02 | ` ` |
| 25 | — | — | 0.04 | ` ` |
| 26 | — | — | 0.02 | ` ` |
| 27 | — | — | 0.01 | ` ` |
| 28 | — | SELECT | 0.34 | `SELECT TRUE` |
| 29 | nodes | SELECT | 2.03 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser,            n.slot_name, n.location, n.priority, n.active, n.config_file,            '' AS upstrea` |
| 30 | — | SELECT | 0.10 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 31 | — | SELECT | 0.23 | `SELECT repmgr.set_upstream_last_seen(1001)` |
| 32 | — | SELECT | 0.09 | `SELECT TRUE` |

| # | Method | Path | ms |
|---|---|---|---|
| 0 |  | `/data-catalog-bucket/apiprofile1787195026_cat/probe_ns/probe_tbl/metadata/00000-116ee59f-5357-49eb-a97b-a6fde09ca16f.metadata.json` | 1.77 |
| 1 |  | `/data-catalog-bucket/apiprofile1787195026_cat/probe_ns/probe_tbl/metadata/00001-790df045-cc10-491f-9288-278f6bb34900.metadata.json` | 7.04 |

### `iceberg.rename_table`

- `POST /v1/{cat}/tables/rename` → **200**
- wall 22 ms · 37 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, nodes, pg_stat_replication, replay_lag

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 1.65 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | entities | UPDATE | 0.08 | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |
| 11 | — | SELECT | 0.25 | `SELECT pg_catalog.pg_last_wal_replay_lsn()` |
| 12 | — | SELECT | 0.05 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 13 | — | — | 0.03 | ` ` |
| 14 | — | — | 0.03 | ` ` |
| 15 | — | — | 0.06 | ` ` |
| 16 | — | — | 0.02 | ` ` |
| 17 | — | — | 0.02 | ` ` |
| 18 | — | — | 0.01 | ` ` |
| 19 | — | — | 0.02 | ` ` |
| 20 | — | — | 0.02 | ` ` |
| 21 | — | — | 0.02 | ` ` |
| 22 | — | — | 0.01 | ` ` |
| 23 | — | — | 0.01 | ` ` |
| 24 | — | SELECT | 0.09 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 25 | — | SELECT | 0.18 | `SELECT pg_catalog.pg_current_wal_lsn()` |
| 26 | replay_lag | SELECT | 1.16 | `SELECT application_name, state, sync_state,(EXTRACT(EPOCH FROM replay_lag)*1000000)::BIGINT FROM pg_catalog.pg_stat_replication` |
| 27 | — | SELECT | 0.03 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 28 | — | SELECT | 0.12 | `SELECT repmgr.get_local_node_id()` |
| 29 | nodes | SELECT | 0.15 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 30 | — | SELECT | 0.13 | `SELECT pg_catalog.pg_last_wal_replay_lsn()` |
| 31 | — | SELECT | 0.04 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 32 | — | SELECT | 0.18 | `SELECT 1` |
| 33 | — | SET | 0.08 | `SET synchronous_commit TO 'local'` |
| 34 | nodes | SELECT | 0.36 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 35 | pg_stat_replication | SELECT | 1.08 | `SELECT pg_catalog.current_setting('max_wal_senders')::INT AS max_wal_senders,         (SELECT pg_catalog.count(*) FROM pg_catalog.pg_stat_replication) AS attached_wal_receivers,   ` |
| 36 | — | SELECT | 0.04 | `SELECT pg_catalog.pg_is_in_recovery()` |

### `iceberg.report_metrics`

- `POST /v1/{cat}/.../tables/{tbl}/metrics` → **400**
- wall 16 ms · 13 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.10 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 3.13 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | — | — | 0.37 | ` ` |
| 7 | — | — | 0.04 | ` ` |
| 8 | — | — | 0.05 | ` ` |
| 9 | — | — | 0.03 | ` ` |
| 10 | — | — | 0.03 | ` ` |
| 11 | — | — | 0.01 | ` ` |
| 12 | — | SELECT | 0.25 | `SELECT 1` |

### `iceberg.load_table[missing]`

- `GET /v1/{cat}/.../tables/{missing}` → **404**
- wall 41 ms · 65 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, nodes, pg_stat_replication

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 2.30 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.11 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | — | SET | 0.08 | `SET synchronous_commit TO 'local'` |
| 9 | — | SELECT | 0.16 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 10 | — | SELECT | 0.08 | `SELECT repmgr.get_repmgrd_pid()` |
| 11 | — | SELECT | 0.03 | `SELECT repmgr.repmgrd_is_running()` |
| 12 | — | SELECT | 0.03 | `SELECT repmgr.repmgrd_is_paused()` |
| 13 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 14 | — | SELECT | 0.13 | `SELECT paused.wal_replay_paused  AND pg_catalog.pg_last_wal_replay_lsn() < pg_catalog.pg_last_wal_receive_lsn()  FROM (SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE     ` |
| 15 | — | SELECT | 0.03 | `SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE    THEN -1    ELSE repmgr.get_upstream_last_seen()  END AS upstream_last_seen` |
| 16 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 17 | nodes | SELECT | 0.44 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, un.node_name AS upstream_node_name,` |
| 18 | — | SELECT | 0.02 | `SELECT paused.wal_replay_paused  AND pg_catalog.pg_last_wal_replay_lsn() < pg_catalog.pg_last_wal_receive_lsn()  FROM (SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE     ` |
| 19 | nodes | SELECT | 0.03 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 20 | — | SET | 0.08 | `SET application_name TO 'psql'` |
| 21 | — | — | 0.10 | ` ` |
| 22 | — | — | 0.01 | ` ` |
| 23 | — | — | 0.01 | ` ` |
| 24 | — | — | 0.04 | ` ` |
| 25 | — | — | 0.04 | ` ` |
| 26 | — | — | 0.03 | ` ` |
| 27 | — | — | 0.04 | ` ` |
| 28 | — | — | 0.02 | ` ` |
| 29 | — | SET | 0.12 | `SET synchronous_commit TO 'local'` |
| 30 | nodes | SELECT | 0.55 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 31 | pg_stat_replication | SELECT | 1.61 | `SELECT pg_catalog.current_setting('max_wal_senders')::INT AS max_wal_senders,         (SELECT pg_catalog.count(*) FROM pg_catalog.pg_stat_replication) AS attached_wal_receivers,   ` |
| 32 | — | SELECT | 0.03 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 33 | — | SET | 0.12 | `SET synchronous_commit TO 'local'` |
| 34 | nodes | SELECT | 0.72 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, un.node_name AS upstream_node_name,` |
| 35 | — | SET | 0.09 | `SET synchronous_commit TO 'local'` |
| 36 | pg_stat_replication | SELECT | 0.98 | `SELECT pid, state    FROM pg_catalog.pg_stat_replication   WHERE application_name = 'benchmarks-postgresql-postgresql-ha-postgresql-0'` |
| 37 | — | SET | 0.06 | `SET synchronous_commit TO 'local'` |
| 38 | — | SELECT | 0.11 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 39 | — | SELECT | 0.05 | `SELECT repmgr.get_repmgrd_pid()` |
| 40 | — | SELECT | 0.03 | `SELECT repmgr.repmgrd_is_running()` |
| 41 | — | SELECT | 0.02 | `SELECT repmgr.repmgrd_is_paused()` |
| 42 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 43 | — | SELECT | 0.04 | `SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE    THEN -1    ELSE repmgr.get_upstream_last_seen()  END AS upstream_last_seen` |
| 44 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 45 | nodes | SELECT | 0.36 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, un.node_name AS upstream_node_name,` |
| 46 | — | SET | 0.11 | `SET synchronous_commit TO 'local'` |
| 47 | pg_stat_replication | SELECT | 1.20 | `SELECT pid, state    FROM pg_catalog.pg_stat_replication   WHERE application_name = 'benchmarks-postgresql-postgresql-ha-postgresql-2'` |
| 48 | — | SET | 0.04 | `SET application_name TO 'psql'` |
| 49 | — | — | 0.05 | `DISCARD ALL` |
| 50 | — | SET | 0.06 | `SET synchronous_commit TO 'local'` |
| 51 | — | SELECT | 0.08 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 52 | — | SELECT | 0.04 | `SELECT repmgr.get_repmgrd_pid()` |
| 53 | — | SELECT | 0.02 | `SELECT repmgr.repmgrd_is_running()` |
| 54 | — | SELECT | 0.09 | `SELECT repmgr.repmgrd_is_paused()` |
| 55 | — | SELECT | 0.05 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 56 | — | SELECT | 0.13 | `SELECT paused.wal_replay_paused  AND pg_catalog.pg_last_wal_replay_lsn() < pg_catalog.pg_last_wal_receive_lsn()  FROM (SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE     ` |
| 57 | — | SELECT | 0.03 | `SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE    THEN -1    ELSE repmgr.get_upstream_last_seen()  END AS upstream_last_seen` |
| 58 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 59 | nodes | SELECT | 0.32 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, un.node_name AS upstream_node_name,` |
| 60 | — | SELECT | 0.03 | `SELECT paused.wal_replay_paused  AND pg_catalog.pg_last_wal_replay_lsn() < pg_catalog.pg_last_wal_receive_lsn()  FROM (SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE     ` |
| 61 | nodes | SELECT | 0.08 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 62 | — | SET | 0.04 | `SET application_name TO 'psql'` |
| 63 | — | SELECT | 0.10 | `SELECT 1` |
| 64 | — | — | 0.03 | `DISCARD ALL` |

### `iceberg.drop_table`

- `DELETE /v1/{cat}/namespaces/{ns}/tables/{tbl}` → **204**
- wall 26 ms · 30 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, policy_mapping_record

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 1.59 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | grant_records | SELECT | 0.01 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 8 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | entities | DELETE | 0.04 | `DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?` |
| 11 | grant_records | SELECT | 0.02 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 12 | grant_records | DELETE | 2.17 | `DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (` |
| 13 | policy_mapping_record | SELECT | 0.01 | `SELECT target_catalog_id, target_id, policy_type_code, policy_catalog_id, policy_id, parameters FROM POLARIS_SCHEMA.POLICY_MAPPING_RECORD WHERE realm_id = ? AND target_id = ? AND t` |
| 14 | policy_mapping_record | DELETE | 0.01 | `DELETE FROM POLARIS_SCHEMA.POLICY_MAPPING_RECORD WHERE target_catalog_id = ? AND target_id = ? AND realm_id = ?` |
| 15 | — | — | 0.08 | ` ` |
| 16 | — | — | 0.04 | ` ` |
| 17 | — | — | 0.01 | ` ` |
| 18 | — | — | 0.01 | ` ` |
| 19 | — | — | 0.00 | ` ` |
| 20 | — | — | 0.01 | ` ` |
| 21 | — | — | 0.01 | ` ` |
| 22 | — | — | 0.01 | ` ` |
| 23 | — | — | 0.00 | ` ` |
| 24 | — | — | 0.01 | ` ` |
| 25 | — | — | 0.03 | ` ` |
| 26 | — | — | 0.03 | ` ` |
| 27 | — | — | 0.01 | ` ` |
| 28 | — | — | 0.01 | ` ` |
| 29 | — | — | 0.01 | ` ` |

### `iceberg.create_view`

- `POST /v1/{cat}/namespaces/{ns}/views` → **200**
- wall 78 ms · 46 statements · 2 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 5.28 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 12 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 13 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 14 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND realm_id = ? AND type_code = ? AND catalog_id = ?` |
| 15 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND realm_id = ? AND type_code = ? AND catalog_id = ?` |
| 16 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 17 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 18 | entities | INSERT | 0.07 | `INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestam` |
| 19 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 20 | grant_records | SELECT | 0.03 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 21 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 22 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 23 | — | — | 0.29 | ` ` |
| 24 | — | — | 0.06 | ` ` |
| 25 | — | — | 0.03 | ` ` |
| 26 | — | — | 0.05 | ` ` |
| 27 | — | — | 0.08 | ` ` |
| 28 | — | — | 0.09 | ` ` |
| 29 | — | — | 0.08 | ` ` |
| 30 | — | — | 0.07 | ` ` |
| 31 | — | — | 0.02 | ` ` |
| 32 | — | — | 0.01 | ` ` |
| 33 | — | — | 0.04 | ` ` |
| 34 | — | — | 0.01 | ` ` |
| 35 | — | — | 0.01 | ` ` |
| 36 | — | — | 0.01 | ` ` |
| 37 | — | — | 0.02 | ` ` |
| 38 | — | — | 0.01 | ` ` |
| 39 | — | — | 0.01 | ` ` |
| 40 | — | — | 0.02 | ` ` |
| 41 | — | — | 0.04 | ` ` |
| 42 | — | — | 0.02 | ` ` |
| 43 | — | — | 0.04 | ` ` |
| 44 | — | — | 0.01 | ` ` |
| 45 | — | — | 0.03 | ` ` |

| # | Method | Path | ms |
|---|---|---|---|
| 0 |  | `/data-catalog-bucket/apiprofile1787195026_cat/probe_ns/probe_view/metadata/00000-11ddf866-6f22-44ad-9a89-7b3aaa90ed84.gz.metadata.json` | 3.87 |
| 1 |  | `/data-catalog-bucket/apiprofile1787195026_cat/probe_ns/probe_view/metadata/00000-11ddf866-6f22-44ad-9a89-7b3aaa90ed84.gz.metadata.json` | 1.04 |

### `iceberg.list_views`

- `GET /v1/{cat}/namespaces/{ns}/views` → **200**
- wall 26 ms · 24 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.10 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 3.75 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.10 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.15 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND sub_type_code = ? AND realm_id = ? AND parent_id = ? AND type` |
| 8 | — | SET | 0.16 | `SET application_name TO 'psql'` |
| 9 | — | — | 0.17 | ` ` |
| 10 | — | — | 0.04 | ` ` |
| 11 | — | — | 0.02 | ` ` |
| 12 | — | — | 0.02 | ` ` |
| 13 | — | — | 0.03 | ` ` |
| 14 | — | — | 0.17 | ` ` |
| 15 | — | — | 0.08 | ` ` |
| 16 | — | — | 0.04 | ` ` |
| 17 | — | SELECT | 0.32 | `SELECT TRUE` |
| 18 | — | SELECT | 0.13 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 19 | — | SET | 0.06 | `SET application_name TO 'psql'` |
| 20 | — | — | 0.10 | `DISCARD ALL` |
| 21 | — | SET | 0.14 | `SET application_name TO 'psql'` |
| 22 | — | SELECT | 0.10 | `SELECT 1` |
| 23 | — | — | 0.04 | `DISCARD ALL` |

### `iceberg.load_view`

- `GET /v1/{cat}/namespaces/{ns}/views/{view}` → **200**
- wall 33 ms · 28 statements · 2 object ops · cache: MISS
- tables: entities, grant_records, nodes

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 1.96 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | — | SELECT | 0.19 | `SELECT repmgr.set_upstream_last_seen(1001)` |
| 10 | — | SELECT | 0.02 | `SELECT TRUE` |
| 11 | — | SELECT | 0.07 | `SELECT repmgr.get_local_node_id()` |
| 12 | nodes | SELECT | 0.11 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 13 | — | — | 0.10 | ` ` |
| 14 | — | — | 0.02 | ` ` |
| 15 | — | — | 0.02 | ` ` |
| 16 | — | — | 0.01 | ` ` |
| 17 | — | — | 0.01 | ` ` |
| 18 | — | — | 0.01 | ` ` |
| 19 | — | — | 0.02 | ` ` |
| 20 | — | — | 0.02 | ` ` |
| 21 | — | — | 0.04 | ` ` |
| 22 | — | SELECT | 0.07 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 23 | — | SELECT | 0.04 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 24 | — | SELECT | 0.10 | `SELECT repmgr.set_upstream_last_seen(1001)` |
| 25 | — | SELECT | 0.01 | `SELECT TRUE` |
| 26 | — | SELECT | 0.04 | `SELECT repmgr.get_local_node_id()` |
| 27 | nodes | SELECT | 0.09 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |

| # | Method | Path | ms |
|---|---|---|---|
| 0 |  | `/data-catalog-bucket/apiprofile1787195026_cat/probe_ns/probe_view/metadata/00000-11ddf866-6f22-44ad-9a89-7b3aaa90ed84.gz.metadata.json` | 1.54 |
| 1 |  | `/data-catalog-bucket/apiprofile1787195026_cat/probe_ns/probe_view/metadata/00000-11ddf866-6f22-44ad-9a89-7b3aaa90ed84.gz.metadata.json` | 1.48 |

### `iceberg.head_view`

- `HEAD /v1/{cat}/namespaces/{ns}/views/{view}` → **204**
- wall 46 ms · 18 statements · 2 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.12 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.10 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 3.82 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.20 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.11 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | entities | SELECT | 0.12 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | — | — | 0.10 | ` ` |
| 10 | — | — | 0.12 | ` ` |
| 11 | — | — | 0.05 | ` ` |
| 12 | — | — | 0.03 | ` ` |
| 13 | — | — | 0.05 | ` ` |
| 14 | — | — | 0.04 | ` ` |
| 15 | — | — | 0.08 | ` ` |
| 16 | — | — | 0.04 | ` ` |
| 17 | — | — | 0.10 | ` ` |

| # | Method | Path | ms |
|---|---|---|---|
| 0 |  | `/data-catalog-bucket/apiprofile1787195026_cat/probe_ns/probe_view/metadata/00000-11ddf866-6f22-44ad-9a89-7b3aaa90ed84.gz.metadata.json` | 2.05 |
| 1 |  | `/data-catalog-bucket/apiprofile1787195026_cat/probe_ns/probe_view/metadata/00000-11ddf866-6f22-44ad-9a89-7b3aaa90ed84.gz.metadata.json` | 1.32 |

### `iceberg.rename_view`

- `POST /v1/{cat}/views/rename` → **204**
- wall 45 ms · 22 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.17 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.33 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.10 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 5.17 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.17 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | entities | SELECT | 0.14 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | entities | UPDATE | 0.10 | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |
| 11 | — | — | 0.20 | ` ` |
| 12 | — | — | 0.19 | ` ` |
| 13 | — | — | 0.35 | ` ` |
| 14 | — | — | 0.15 | ` ` |
| 15 | — | — | 0.05 | ` ` |
| 16 | — | — | 0.03 | ` ` |
| 17 | — | — | 0.09 | ` ` |
| 18 | — | — | 0.08 | ` ` |
| 19 | — | — | 0.16 | ` ` |
| 20 | — | — | 0.03 | ` ` |
| 21 | — | — | 0.02 | ` ` |

### `iceberg.drop_view`

- `DELETE /v1/{cat}/namespaces/{ns}/views/{view}` → **204**
- wall 80 ms · 71 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, nodes, pg_stat_replication

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 31.05 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | grant_records | SELECT | 0.02 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 8 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | entities | DELETE | 0.04 | `DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?` |
| 11 | grant_records | SELECT | 0.02 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 12 | grant_records | DELETE | 26.80 | `DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (` |
| 13 | entities | INSERT | 0.14 | `INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestam` |
| 14 | — | SET | 0.05 | `SET synchronous_commit TO 'local'` |
| 15 | — | SELECT | 0.12 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 16 | — | SELECT | 0.05 | `SELECT repmgr.get_repmgrd_pid()` |
| 17 | — | SELECT | 0.02 | `SELECT repmgr.repmgrd_is_running()` |
| 18 | — | SELECT | 0.02 | `SELECT repmgr.repmgrd_is_paused()` |
| 19 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 20 | — | SELECT | 0.11 | `SELECT paused.wal_replay_paused  AND pg_catalog.pg_last_wal_replay_lsn() < pg_catalog.pg_last_wal_receive_lsn()  FROM (SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE     ` |
| 21 | — | SELECT | 0.03 | `SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE    THEN -1    ELSE repmgr.get_upstream_last_seen()  END AS upstream_last_seen` |
| 22 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 23 | nodes | SELECT | 0.36 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, un.node_name AS upstream_node_name,` |
| 24 | — | SELECT | 0.02 | `SELECT paused.wal_replay_paused  AND pg_catalog.pg_last_wal_replay_lsn() < pg_catalog.pg_last_wal_receive_lsn()  FROM (SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE     ` |
| 25 | nodes | SELECT | 0.03 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 26 | — | — | 0.06 | ` ` |
| 27 | — | — | 0.01 | ` ` |
| 28 | — | — | 0.03 | ` ` |
| 29 | — | — | 0.01 | ` ` |
| 30 | — | — | 0.02 | ` ` |
| 31 | — | — | 0.01 | ` ` |
| 32 | — | — | 0.01 | ` ` |
| 33 | — | — | 0.01 | ` ` |
| 34 | — | — | 0.01 | ` ` |
| 35 | — | — | 0.03 | ` ` |
| 36 | — | — | 0.10 | ` ` |
| 37 | — | — | 0.07 | ` ` |
| 38 | — | — | 0.05 | ` ` |
| 39 | — | — | 0.04 | ` ` |
| 40 | — | SET | 0.10 | `SET synchronous_commit TO 'local'` |
| 41 | nodes | SELECT | 0.43 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 42 | pg_stat_replication | SELECT | 1.39 | `SELECT pg_catalog.current_setting('max_wal_senders')::INT AS max_wal_senders,         (SELECT pg_catalog.count(*) FROM pg_catalog.pg_stat_replication) AS attached_wal_receivers,   ` |
| 43 | — | SELECT | 0.03 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 44 | — | SET | 0.10 | `SET synchronous_commit TO 'local'` |
| 45 | nodes | SELECT | 0.56 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, un.node_name AS upstream_node_name,` |
| 46 | — | SET | 0.06 | `SET synchronous_commit TO 'local'` |
| 47 | pg_stat_replication | SELECT | 14.99 | `SELECT pid, state    FROM pg_catalog.pg_stat_replication   WHERE application_name = 'benchmarks-postgresql-postgresql-ha-postgresql-0'` |
| 48 | — | SET | 0.05 | `SET synchronous_commit TO 'local'` |
| 49 | — | SELECT | 0.08 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 50 | — | SELECT | 0.03 | `SELECT repmgr.get_repmgrd_pid()` |
| 51 | — | SELECT | 0.02 | `SELECT repmgr.repmgrd_is_running()` |
| 52 | — | SELECT | 0.02 | `SELECT repmgr.repmgrd_is_paused()` |
| 53 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 54 | — | SELECT | 0.02 | `SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE    THEN -1    ELSE repmgr.get_upstream_last_seen()  END AS upstream_last_seen` |
| 55 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 56 | nodes | SELECT | 0.30 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, un.node_name AS upstream_node_name,` |
| 57 | — | SET | 0.03 | `SET synchronous_commit TO 'local'` |
| 58 | pg_stat_replication | SELECT | 0.80 | `SELECT pid, state    FROM pg_catalog.pg_stat_replication   WHERE application_name = 'benchmarks-postgresql-postgresql-ha-postgresql-2'` |
| 59 | — | SET | 0.05 | `SET synchronous_commit TO 'local'` |
| 60 | — | SELECT | 0.08 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 61 | — | SELECT | 0.04 | `SELECT repmgr.get_repmgrd_pid()` |
| 62 | — | SELECT | 0.02 | `SELECT repmgr.repmgrd_is_running()` |
| 63 | — | SELECT | 0.02 | `SELECT repmgr.repmgrd_is_paused()` |
| 64 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 65 | — | SELECT | 0.07 | `SELECT paused.wal_replay_paused  AND pg_catalog.pg_last_wal_replay_lsn() < pg_catalog.pg_last_wal_receive_lsn()  FROM (SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE     ` |
| 66 | — | SELECT | 0.02 | `SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE    THEN -1    ELSE repmgr.get_upstream_last_seen()  END AS upstream_last_seen` |
| 67 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 68 | nodes | SELECT | 0.30 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, un.node_name AS upstream_node_name,` |
| 69 | — | SELECT | 0.02 | `SELECT paused.wal_replay_paused  AND pg_catalog.pg_last_wal_replay_lsn() < pg_catalog.pg_last_wal_receive_lsn()  FROM (SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE     ` |
| 70 | nodes | SELECT | 0.03 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |

### `mgmt.list_catalogs`

- `GET /v1/catalogs` → **200**
- wall 77 ms · 16 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.15 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 2.95 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.11 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 9.87 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | — | — | 0.15 | ` ` |
| 9 | — | — | 0.11 | ` ` |
| 10 | — | — | 0.05 | ` ` |
| 11 | — | — | 0.02 | ` ` |
| 12 | — | — | 0.05 | ` ` |
| 13 | — | — | 0.04 | ` ` |
| 14 | — | — | 0.12 | ` ` |
| 15 | — | — | 0.05 | ` ` |

### `mgmt.get_catalog`

- `GET /v1/catalogs/{cat}` → **200**
- wall 29 ms · 22 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.19 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.10 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 4.70 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.13 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | — | SET | 0.25 | `SET application_name TO 'psql'` |
| 8 | — | SELECT | — | `SELECT repmgr.set_upstream_last_seen(1001)` |
| 9 | — | — | 0.18 | ` ` |
| 10 | — | — | 0.09 | ` ` |
| 11 | — | — | 0.05 | ` ` |
| 12 | — | — | 0.03 | ` ` |
| 13 | — | — | 0.03 | ` ` |
| 14 | — | — | 0.03 | ` ` |
| 15 | — | — | 0.06 | ` ` |
| 16 | — | SET | 0.08 | `SET application_name TO 'psql'` |
| 17 | — | SELECT | 0.12 | `SELECT 1` |
| 18 | — | — | 0.08 | `DISCARD ALL` |
| 19 | — | SELECT | 0.27 | `SELECT TRUE` |
| 20 | — | SELECT | 0.10 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 21 | — | SET | 0.06 | `SET application_name TO 'psql'` |

### `mgmt.create_principal`

- `POST /v1/principals` → **201**
- wall 21 ms · 31 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, nodes, principal_authentication_data

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 1.20 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | principal_authentication_data | SELECT | 0.01 | `SELECT principal_id, principal_client_id, main_secret_hash, secondary_secret_hash, secret_salt FROM POLARIS_SCHEMA.PRINCIPAL_AUTHENTICATION_DATA WHERE realm_id = ? AND principal_cl` |
| 9 | principal_authentication_data | INSERT | 0.07 | `INSERT INTO POLARIS_SCHEMA.PRINCIPAL_AUTHENTICATION_DATA (principal_id, principal_client_id, main_secret_hash, secondary_secret_hash, secret_salt, realm_id) VALUES (?, ?, ?, ?, ?, ` |
| 10 | entities | INSERT | 0.04 | `INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestam` |
| 11 | — | SELECT | 0.02 | `SELECT TRUE` |
| 12 | — | SELECT | 0.08 | `SELECT repmgr.get_local_node_id()` |
| 13 | nodes | SELECT | 0.08 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 14 | — | SELECT | 0.06 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 15 | — | — | 0.07 | ` ` |
| 16 | — | — | 0.01 | ` ` |
| 17 | — | SELECT | 0.04 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 18 | — | — | 0.01 | ` ` |
| 19 | — | — | 0.01 | ` ` |
| 20 | — | — | 0.03 | ` ` |
| 21 | — | — | 0.00 | ` ` |
| 22 | — | — | 0.02 | ` ` |
| 23 | — | — | 0.04 | ` ` |
| 24 | — | — | 0.01 | ` ` |
| 25 | — | — | 0.01 | ` ` |
| 26 | — | — | 0.02 | ` ` |
| 27 | — | SELECT | 0.08 | `SELECT repmgr.set_upstream_last_seen(1001)` |
| 28 | — | SELECT | 0.03 | `SELECT TRUE` |
| 29 | — | SELECT | 0.07 | `SELECT repmgr.get_local_node_id()` |
| 30 | nodes | SELECT | 0.11 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |

### `mgmt.get_principal`

- `GET /v1/principals/{p}` → **200**
- wall 34 ms · 20 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.18 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.15 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 5.17 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.10 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | grant_records | SELECT | 2.96 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 8 | grant_records | SELECT | 0.04 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 9 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | — | — | 0.76 | ` ` |
| 11 | — | — | 0.11 | ` ` |
| 12 | — | — | 0.15 | ` ` |
| 13 | — | — | 0.06 | ` ` |
| 14 | — | — | 0.03 | ` ` |
| 15 | — | — | 0.15 | ` ` |
| 16 | — | — | 0.05 | ` ` |
| 17 | — | — | 0.08 | ` ` |
| 18 | — | — | 0.06 | ` ` |
| 19 | — | — | 0.08 | ` ` |

### `mgmt.list_principals`

- `GET /v1/principals` → **200**
- wall 50 ms · 23 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, nodes, pg_stat_replication

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.15 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.12 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.10 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 4.03 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 2.58 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | — | SET | — | `SET synchronous_commit TO 'local'` |
| 9 | — | — | 0.21 | ` ` |
| 10 | — | — | 0.07 | ` ` |
| 11 | — | — | 0.11 | ` ` |
| 12 | — | — | 0.08 | ` ` |
| 13 | — | — | 0.04 | ` ` |
| 14 | — | — | 0.10 | ` ` |
| 15 | — | — | 0.05 | ` ` |
| 16 | — | — | 0.08 | ` ` |
| 17 | — | SET | 0.11 | `SET synchronous_commit TO 'local'` |
| 18 | nodes | SELECT | 0.45 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 19 | pg_stat_replication | SELECT | 1.52 | `SELECT pg_catalog.current_setting('max_wal_senders')::INT AS max_wal_senders,         (SELECT pg_catalog.count(*) FROM pg_catalog.pg_stat_replication) AS attached_wal_receivers,   ` |
| 20 | — | SELECT | 0.04 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 21 | — | SET | 0.08 | `SET synchronous_commit TO 'local'` |
| 22 | nodes | SELECT | 0.44 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, un.node_name AS upstream_node_name,` |

### `mgmt.create_principal_role`

- `POST /v1/principal-roles` → **201**
- wall 18 ms · 41 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, nodes, pg_stat_replication

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 1.35 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | INSERT | 0.05 | `INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestam` |
| 8 | — | — | 0.09 | ` ` |
| 9 | — | SET | 0.05 | `SET synchronous_commit TO 'local'` |
| 10 | pg_stat_replication | SELECT | 0.88 | `SELECT pid, state    FROM pg_catalog.pg_stat_replication   WHERE application_name = 'benchmarks-postgresql-postgresql-ha-postgresql-0'` |
| 11 | — | — | 0.01 | ` ` |
| 12 | — | — | 0.01 | ` ` |
| 13 | — | — | 0.01 | ` ` |
| 14 | — | — | 0.02 | ` ` |
| 15 | — | — | 0.01 | ` ` |
| 16 | — | — | 0.01 | ` ` |
| 17 | — | — | 0.01 | ` ` |
| 18 | — | SET | 0.14 | `SET synchronous_commit TO 'local'` |
| 19 | — | SELECT | 0.12 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 20 | — | SELECT | 0.05 | `SELECT repmgr.get_repmgrd_pid()` |
| 21 | — | SELECT | 0.02 | `SELECT repmgr.repmgrd_is_running()` |
| 22 | — | SELECT | 0.02 | `SELECT repmgr.repmgrd_is_paused()` |
| 23 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 24 | — | SELECT | 0.03 | `SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE    THEN -1    ELSE repmgr.get_upstream_last_seen()  END AS upstream_last_seen` |
| 25 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 26 | nodes | SELECT | 0.38 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, un.node_name AS upstream_node_name,` |
| 27 | — | SET | 0.05 | `SET synchronous_commit TO 'local'` |
| 28 | pg_stat_replication | SELECT | 0.78 | `SELECT pid, state    FROM pg_catalog.pg_stat_replication   WHERE application_name = 'benchmarks-postgresql-postgresql-ha-postgresql-2'` |
| 29 | — | SET | 0.11 | `SET synchronous_commit TO 'local'` |
| 30 | — | SELECT | 0.15 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 31 | — | SELECT | 0.06 | `SELECT repmgr.get_repmgrd_pid()` |
| 32 | — | SELECT | 0.03 | `SELECT repmgr.repmgrd_is_running()` |
| 33 | — | SELECT | 0.02 | `SELECT repmgr.repmgrd_is_paused()` |
| 34 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 35 | — | SELECT | 0.10 | `SELECT paused.wal_replay_paused  AND pg_catalog.pg_last_wal_replay_lsn() < pg_catalog.pg_last_wal_receive_lsn()  FROM (SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE     ` |
| 36 | — | SELECT | 0.03 | `SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE    THEN -1    ELSE repmgr.get_upstream_last_seen()  END AS upstream_last_seen` |
| 37 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 38 | nodes | SELECT | 0.36 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, un.node_name AS upstream_node_name,` |
| 39 | — | SELECT | 0.02 | `SELECT paused.wal_replay_paused  AND pg_catalog.pg_last_wal_replay_lsn() < pg_catalog.pg_last_wal_receive_lsn()  FROM (SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE     ` |
| 40 | nodes | SELECT | 0.04 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |

### `mgmt.get_principal_role`

- `GET /v1/principal-roles/{r}` → **200**
- wall 31 ms · 26 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.15 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.16 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 4.06 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.12 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | grant_records | SELECT | 2.88 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 8 | grant_records | SELECT | 0.06 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 9 | entities | SELECT | 0.10 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | — | SELECT | 0.34 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 11 | — | SELECT | 0.18 | `SELECT 1` |
| 12 | — | — | 0.05 | `DISCARD ALL` |
| 13 | — | — | 0.12 | ` ` |
| 14 | — | — | 0.14 | ` ` |
| 15 | — | — | 0.09 | ` ` |
| 16 | — | — | 0.03 | ` ` |
| 17 | — | — | 0.04 | ` ` |
| 18 | — | — | 0.04 | ` ` |
| 19 | — | — | 0.06 | ` ` |
| 20 | — | — | 0.04 | ` ` |
| 21 | — | — | 0.07 | ` ` |
| 22 | — | — | 0.06 | ` ` |
| 23 | — | SELECT | 0.20 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 24 | — | — | 0.11 | `DISCARD ALL` |
| 25 | — | SELECT | 0.18 | `SELECT pg_catalog.pg_is_in_recovery()` |

### `mgmt.list_principal_roles`

- `GET /v1/principal-roles` → **200**
- wall 19 ms · 29 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, nodes, pg_stat_replication

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 1.28 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 1.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | — | SELECT | 0.12 | `SELECT repmgr.set_upstream_last_seen(1001)` |
| 9 | — | SELECT | 0.03 | `SELECT TRUE` |
| 10 | — | SELECT | 0.07 | `SELECT repmgr.get_local_node_id()` |
| 11 | nodes | SELECT | 0.09 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 12 | — | — | 0.04 | ` ` |
| 13 | — | — | 0.01 | ` ` |
| 14 | — | — | 0.01 | ` ` |
| 15 | — | — | 0.02 | ` ` |
| 16 | — | — | 0.01 | ` ` |
| 17 | — | — | 0.03 | ` ` |
| 18 | — | — | 0.01 | ` ` |
| 19 | — | — | 0.01 | ` ` |
| 20 | — | SELECT | 0.10 | `SELECT TRUE` |
| 21 | — | SELECT | 0.07 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 22 | — | SELECT | 0.05 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 23 | — | SET | 0.07 | `SET synchronous_commit TO 'local'` |
| 24 | nodes | SELECT | 0.36 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 25 | pg_stat_replication | SELECT | 1.00 | `SELECT pg_catalog.current_setting('max_wal_senders')::INT AS max_wal_senders,         (SELECT pg_catalog.count(*) FROM pg_catalog.pg_stat_replication) AS attached_wal_receivers,   ` |
| 26 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 27 | — | SELECT | 0.07 | `SELECT repmgr.set_upstream_last_seen(1001)` |
| 28 | — | SELECT | 0.04 | `SELECT TRUE` |

### `mgmt.assign_principal_role`

- `PUT /v1/principals/{p}/principal-roles` → **201**
- wall 25 ms · 24 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 1.47 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | grant_records | INSERT | 0.06 | `INSERT INTO POLARIS_SCHEMA.GRANT_RECORDS (securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code, realm_id) VALUES (?, ?, ?, ?, ?, ?)` |
| 8 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | UPDATE | 0.04 | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |
| 10 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | entities | UPDATE | 0.03 | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |
| 12 | — | — | 0.02 | ` ` |
| 13 | — | — | 0.04 | ` ` |
| 14 | — | — | 0.01 | ` ` |
| 15 | — | — | 0.02 | ` ` |
| 16 | — | — | 0.02 | ` ` |
| 17 | — | — | 0.01 | ` ` |
| 18 | — | — | 0.01 | ` ` |
| 19 | — | — | 0.01 | ` ` |
| 20 | — | — | 0.03 | ` ` |
| 21 | — | — | 0.03 | ` ` |
| 22 | — | — | 0.02 | ` ` |
| 23 | — | — | 0.01 | ` ` |

### `mgmt.create_catalog_role`

- `POST /v1/catalogs/{cat}/catalog-roles` → **201**
- wall 35 ms · 16 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.18 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.11 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 4.05 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.10 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.14 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | INSERT | 0.16 | `INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestam` |
| 8 | — | — | 0.23 | ` ` |
| 9 | — | — | 0.11 | ` ` |
| 10 | — | — | 0.12 | ` ` |
| 11 | — | — | 0.04 | ` ` |
| 12 | — | — | 0.06 | ` ` |
| 13 | — | — | 0.08 | ` ` |
| 14 | — | — | 0.04 | ` ` |
| 15 | — | — | 0.03 | ` ` |

### `mgmt.list_catalog_roles`

- `GET /v1/catalogs/{cat}/catalog-roles` → **200**
- wall 31 ms · 17 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.10 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 1.23 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 2.99 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.17 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.13 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | — | — | 0.15 | ` ` |
| 9 | — | — | 0.26 | ` ` |
| 10 | — | — | 0.03 | ` ` |
| 11 | — | — | 0.04 | ` ` |
| 12 | — | — | 0.05 | ` ` |
| 13 | — | — | 0.07 | ` ` |
| 14 | — | — | 0.07 | ` ` |
| 15 | — | — | 0.09 | ` ` |
| 16 | — | — | 0.22 | ` ` |

### `mgmt.assign_catalog_role`

- `PUT /v1/principal-roles/{r}/catalog-roles/{cat}` → **201**
- wall 37 ms · 38 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.18 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 2.13 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | grant_records | SELECT | 2.08 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 8 | grant_records | SELECT | 0.03 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 9 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | grant_records | SELECT | 1.93 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 12 | grant_records | SELECT | 0.03 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 13 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 14 | grant_records | INSERT | 0.04 | `INSERT INTO POLARIS_SCHEMA.GRANT_RECORDS (securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code, realm_id) VALUES (?, ?, ?, ?, ?, ?)` |
| 15 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 16 | entities | UPDATE | 0.07 | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |
| 17 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 18 | entities | UPDATE | 0.04 | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |
| 19 | — | — | 0.15 | ` ` |
| 20 | — | — | 0.04 | ` ` |
| 21 | — | — | 0.01 | ` ` |
| 22 | — | — | 0.02 | ` ` |
| 23 | — | — | 0.03 | ` ` |
| 24 | — | — | 0.02 | ` ` |
| 25 | — | — | 0.02 | ` ` |
| 26 | — | — | 0.02 | ` ` |
| 27 | — | — | 0.02 | ` ` |
| 28 | — | — | 0.04 | ` ` |
| 29 | — | — | 0.04 | ` ` |
| 30 | — | — | 0.05 | ` ` |
| 31 | — | — | 0.04 | ` ` |
| 32 | — | — | 0.03 | ` ` |
| 33 | — | — | 0.02 | ` ` |
| 34 | — | — | 0.04 | ` ` |
| 35 | — | — | 0.04 | ` ` |
| 36 | — | — | 0.02 | ` ` |
| 37 | — | — | 0.01 | ` ` |

### `mgmt.grant_privilege`

- `PUT /v1/catalogs/{cat}/catalog-roles/{cr}/grants` → **201**
- wall 59 ms · 48 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.15 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.27 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 3.12 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.26 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.15 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | grant_records | SELECT | 2.91 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 9 | grant_records | SELECT | 0.05 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 10 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | grant_records | SELECT | 2.07 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 12 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 13 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 14 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 15 | grant_records | SELECT | 2.13 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 16 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 17 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 18 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 19 | grant_records | INSERT | 0.06 | `INSERT INTO POLARIS_SCHEMA.GRANT_RECORDS (securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code, realm_id) VALUES (?, ?, ?, ?, ?, ?)` |
| 20 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 21 | entities | UPDATE | 0.09 | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |
| 22 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 23 | entities | UPDATE | 0.06 | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |
| 24 | — | — | 0.22 | ` ` |
| 25 | — | — | 0.07 | ` ` |
| 26 | — | — | 0.05 | ` ` |
| 27 | — | — | 0.07 | ` ` |
| 28 | — | — | 0.04 | ` ` |
| 29 | — | — | 0.02 | ` ` |
| 30 | — | — | 0.07 | ` ` |
| 31 | — | — | 0.04 | ` ` |
| 32 | — | — | 0.04 | ` ` |
| 33 | — | — | 0.04 | ` ` |
| 34 | — | — | 0.47 | ` ` |
| 35 | — | — | 0.04 | ` ` |
| 36 | — | — | 0.05 | ` ` |
| 37 | — | — | 0.03 | ` ` |
| 38 | — | — | 0.03 | ` ` |
| 39 | — | — | 0.01 | ` ` |
| 40 | — | — | 0.03 | ` ` |
| 41 | — | — | 0.04 | ` ` |
| 42 | — | — | 0.03 | ` ` |
| 43 | — | — | 0.01 | ` ` |
| 44 | — | — | 0.02 | ` ` |
| 45 | — | — | 0.03 | ` ` |
| 46 | — | — | 0.03 | ` ` |
| 47 | — | — | 0.01 | ` ` |

### `mgmt.list_grants`

- `GET /v1/catalogs/{cat}/catalog-roles/{cr}/grants` → **200**
- wall 16 ms · 55 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, nodes, pg_stat_replication, replay_lag

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.14 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 1.74 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.14 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | grant_records | SELECT | 0.03 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 9 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | grant_records | SELECT | 1.62 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 11 | grant_records | SELECT | 0.02 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 12 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 13 | grant_records | SELECT | 1.26 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 14 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 15 | — | SELECT | 0.20 | `SELECT pg_catalog.pg_last_wal_replay_lsn()` |
| 16 | — | SELECT | 0.04 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 17 | — | SELECT | 0.10 | `SELECT repmgr.set_upstream_last_seen(1001)` |
| 18 | — | SELECT | 0.01 | `SELECT TRUE` |
| 19 | — | SELECT | 0.08 | `SELECT repmgr.get_local_node_id()` |
| 20 | nodes | SELECT | 0.08 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 21 | — | — | 0.08 | ` ` |
| 22 | — | — | 0.04 | ` ` |
| 23 | — | — | 0.02 | ` ` |
| 24 | — | — | 0.01 | ` ` |
| 25 | — | — | 0.01 | ` ` |
| 26 | — | — | 0.02 | ` ` |
| 27 | — | — | 0.06 | ` ` |
| 28 | — | — | 0.03 | ` ` |
| 29 | — | — | 0.01 | ` ` |
| 30 | — | — | 0.01 | ` ` |
| 31 | — | — | 0.01 | ` ` |
| 32 | — | — | 0.01 | ` ` |
| 33 | — | — | 0.01 | ` ` |
| 34 | — | — | 0.00 | ` ` |
| 35 | — | — | 0.00 | ` ` |
| 36 | — | SELECT | 0.60 | `SELECT TRUE` |
| 37 | nodes | SELECT | 1.28 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser,            n.slot_name, n.location, n.priority, n.active, n.config_file,            '' AS upstrea` |
| 38 | — | SELECT | 0.05 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 39 | — | SELECT | 0.22 | `SELECT pg_catalog.pg_current_wal_lsn()` |
| 40 | replay_lag | SELECT | 0.83 | `SELECT application_name, state, sync_state,(EXTRACT(EPOCH FROM replay_lag)*1000000)::BIGINT FROM pg_catalog.pg_stat_replication` |
| 41 | — | SELECT | 0.03 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 42 | — | SELECT | 0.04 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 43 | — | SELECT | 0.05 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 44 | — | SELECT | 0.21 | `SELECT 1` |
| 45 | — | SELECT | 0.14 | `SELECT pg_catalog.pg_last_wal_replay_lsn()` |
| 46 | — | SELECT | 0.04 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 47 | — | SET | 0.05 | `SET synchronous_commit TO 'local'` |
| 48 | nodes | SELECT | 0.30 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 49 | pg_stat_replication | SELECT | 0.96 | `SELECT pg_catalog.current_setting('max_wal_senders')::INT AS max_wal_senders,         (SELECT pg_catalog.count(*) FROM pg_catalog.pg_stat_replication) AS attached_wal_receivers,   ` |
| 50 | — | SELECT | 0.03 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 51 | — | SELECT | 0.14 | `SELECT repmgr.set_upstream_last_seen(1001)` |
| 52 | — | SELECT | 0.13 | `SELECT TRUE` |
| 53 | — | SELECT | 0.25 | `SELECT repmgr.get_local_node_id()` |
| 54 | nodes | SELECT | 0.08 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |

### `mgmt.list_principals_for_principal_role`

- `GET /v1/principal-roles/{r}/principals` → **200**
- wall 11 ms · 27 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 1.23 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | grant_records | SELECT | 1.19 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 9 | grant_records | SELECT | 0.01 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 10 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | grant_records | SELECT | 0.01 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 12 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 13 | — | — | 0.08 | ` ` |
| 14 | — | — | 0.01 | ` ` |
| 15 | — | — | 0.02 | ` ` |
| 16 | — | — | 0.01 | ` ` |
| 17 | — | — | 0.03 | ` ` |
| 18 | — | — | 0.01 | ` ` |
| 19 | — | — | 0.02 | ` ` |
| 20 | — | — | 0.08 | ` ` |
| 21 | — | — | 0.04 | ` ` |
| 22 | — | — | 0.01 | ` ` |
| 23 | — | — | 0.01 | ` ` |
| 24 | — | — | 0.01 | ` ` |
| 25 | — | — | 0.01 | ` ` |
| 26 | — | SELECT | 0.23 | `SELECT 1` |

### `mgmt.reset_principal_credentials`

- `POST /v1/principals/{p}/reset` → **200**
- wall 47 ms · 77 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, nodes, pg_stat_replication, principal_authentication_data

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 2.20 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | grant_records | SELECT | 1.55 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 9 | grant_records | SELECT | 0.02 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 10 | principal_authentication_data | SELECT | 0.03 | `SELECT principal_id, principal_client_id, main_secret_hash, secondary_secret_hash, secret_salt FROM POLARIS_SCHEMA.PRINCIPAL_AUTHENTICATION_DATA WHERE realm_id = ? AND principal_cl` |
| 11 | principal_authentication_data | DELETE | 0.05 | `DELETE FROM POLARIS_SCHEMA.PRINCIPAL_AUTHENTICATION_DATA WHERE realm_id = ? AND principal_id = ? AND principal_client_id = ?` |
| 12 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 13 | principal_authentication_data | INSERT | 0.04 | `INSERT INTO POLARIS_SCHEMA.PRINCIPAL_AUTHENTICATION_DATA (principal_id, principal_client_id, main_secret_hash, secondary_secret_hash, secret_salt, realm_id) VALUES (?, ?, ?, ?, ?, ` |
| 14 | — | SET | 0.11 | `SET synchronous_commit TO 'local'` |
| 15 | — | SELECT | 0.16 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 16 | — | SELECT | 0.07 | `SELECT repmgr.get_repmgrd_pid()` |
| 17 | — | SELECT | 0.03 | `SELECT repmgr.repmgrd_is_running()` |
| 18 | — | SELECT | 0.02 | `SELECT repmgr.repmgrd_is_paused()` |
| 19 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 20 | — | SELECT | 0.13 | `SELECT paused.wal_replay_paused  AND pg_catalog.pg_last_wal_replay_lsn() < pg_catalog.pg_last_wal_receive_lsn()  FROM (SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE     ` |
| 21 | — | SELECT | 0.04 | `SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE    THEN -1    ELSE repmgr.get_upstream_last_seen()  END AS upstream_last_seen` |
| 22 | — | SELECT | 0.02 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 23 | nodes | SELECT | 0.49 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, un.node_name AS upstream_node_name,` |
| 24 | — | SELECT | 0.06 | `SELECT paused.wal_replay_paused  AND pg_catalog.pg_last_wal_replay_lsn() < pg_catalog.pg_last_wal_receive_lsn()  FROM (SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE     ` |
| 25 | nodes | SELECT | 0.10 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 26 | — | SET | 0.10 | `SET application_name TO 'psql'` |
| 27 | — | — | 0.11 | ` ` |
| 28 | — | — | 0.15 | ` ` |
| 29 | — | SET | 0.14 | `SET synchronous_commit TO 'local'` |
| 30 | nodes | SELECT | 0.76 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 31 | pg_stat_replication | SELECT | 1.65 | `SELECT pg_catalog.current_setting('max_wal_senders')::INT AS max_wal_senders,         (SELECT pg_catalog.count(*) FROM pg_catalog.pg_stat_replication) AS attached_wal_receivers,   ` |
| 32 | — | — | 0.02 | ` ` |
| 33 | — | — | 0.06 | ` ` |
| 34 | — | SELECT | 0.03 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 35 | — | — | 0.02 | ` ` |
| 36 | — | — | 0.01 | ` ` |
| 37 | — | — | 0.02 | ` ` |
| 38 | — | — | 0.03 | ` ` |
| 39 | — | — | 0.02 | ` ` |
| 40 | — | — | 0.02 | ` ` |
| 41 | — | — | 0.03 | ` ` |
| 42 | — | — | 0.01 | ` ` |
| 43 | — | — | 0.02 | ` ` |
| 44 | — | — | 0.01 | ` ` |
| 45 | — | SET | 0.08 | `SET synchronous_commit TO 'local'` |
| 46 | nodes | SELECT | 0.52 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, un.node_name AS upstream_node_name,` |
| 47 | — | SET | 0.09 | `SET synchronous_commit TO 'local'` |
| 48 | pg_stat_replication | SELECT | 19.73 | `SELECT pid, state    FROM pg_catalog.pg_stat_replication   WHERE application_name = 'benchmarks-postgresql-postgresql-ha-postgresql-0'` |
| 49 | — | SET | 0.09 | `SET synchronous_commit TO 'local'` |
| 50 | — | SELECT | 0.17 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 51 | — | SELECT | 0.06 | `SELECT repmgr.get_repmgrd_pid()` |
| 52 | — | SELECT | 0.03 | `SELECT repmgr.repmgrd_is_running()` |
| 53 | — | SELECT | 0.02 | `SELECT repmgr.repmgrd_is_paused()` |
| 54 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 55 | — | SELECT | 0.04 | `SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE    THEN -1    ELSE repmgr.get_upstream_last_seen()  END AS upstream_last_seen` |
| 56 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 57 | nodes | SELECT | 0.47 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, un.node_name AS upstream_node_name,` |
| 58 | — | SET | 0.05 | `SET synchronous_commit TO 'local'` |
| 59 | pg_stat_replication | SELECT | 0.75 | `SELECT pid, state    FROM pg_catalog.pg_stat_replication   WHERE application_name = 'benchmarks-postgresql-postgresql-ha-postgresql-2'` |
| 60 | — | SET | 0.03 | `SET application_name TO 'psql'` |
| 61 | — | — | 0.04 | `DISCARD ALL` |
| 62 | — | SET | 0.07 | `SET synchronous_commit TO 'local'` |
| 63 | — | SELECT | 0.11 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 64 | — | SELECT | 0.05 | `SELECT repmgr.get_repmgrd_pid()` |
| 65 | — | SELECT | 0.02 | `SELECT repmgr.repmgrd_is_running()` |
| 66 | — | SELECT | 0.02 | `SELECT repmgr.repmgrd_is_paused()` |
| 67 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 68 | — | SELECT | 0.11 | `SELECT paused.wal_replay_paused  AND pg_catalog.pg_last_wal_replay_lsn() < pg_catalog.pg_last_wal_receive_lsn()  FROM (SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE     ` |
| 69 | — | SELECT | 0.02 | `SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE    THEN -1    ELSE repmgr.get_upstream_last_seen()  END AS upstream_last_seen` |
| 70 | — | SELECT | 0.01 | `SELECT pg_catalog.pg_is_in_recovery()` |
| 71 | nodes | SELECT | 0.33 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name, n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, un.node_name AS upstream_node_name,` |
| 72 | — | SELECT | 0.02 | `SELECT paused.wal_replay_paused  AND pg_catalog.pg_last_wal_replay_lsn() < pg_catalog.pg_last_wal_receive_lsn()  FROM (SELECT CASE WHEN pg_catalog.pg_is_in_recovery() IS FALSE     ` |
| 73 | nodes | SELECT | 0.04 | `SELECT n.node_id, n.type, n.upstream_node_id, n.node_name,  n.conninfo, n.repluser, n.slot_name, n.location, n.priority, n.active, n.config_file, '' AS upstream_node_name, NULL AS ` |
| 74 | — | SET | 0.03 | `SET application_name TO 'psql'` |
| 75 | — | SELECT | 0.09 | `SELECT 1` |
| 76 | — | — | 0.22 | `DISCARD ALL` |

### `mgmt.delete_catalog_role`

- `DELETE /v1/catalogs/{cat}/catalog-roles/{cr}` → **204**
- wall 33 ms · 32 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 2.39 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.07 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.03 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | entities | DELETE | 0.04 | `DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?` |
| 9 | grant_records | SELECT | 1.89 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 10 | grant_records | SELECT | 0.02 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 11 | grant_records | DELETE | 2.62 | `DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (` |
| 12 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 13 | entities | UPDATE | 0.07 | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |
| 14 | entities | UPDATE | 0.39 | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |
| 15 | entities | INSERT | 0.09 | `INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestam` |
| 16 | — | — | 0.12 | ` ` |
| 17 | — | — | 0.02 | ` ` |
| 18 | — | — | 0.01 | ` ` |
| 19 | — | — | 0.01 | ` ` |
| 20 | — | — | 0.02 | ` ` |
| 21 | — | — | 0.02 | ` ` |
| 22 | — | — | 0.06 | ` ` |
| 23 | — | — | 0.03 | ` ` |
| 24 | — | — | 0.01 | ` ` |
| 25 | — | — | 0.05 | ` ` |
| 26 | — | — | 0.03 | ` ` |
| 27 | — | — | 0.03 | ` ` |
| 28 | — | — | 0.02 | ` ` |
| 29 | — | — | 0.02 | ` ` |
| 30 | — | — | 0.03 | ` ` |
| 31 | — | — | 0.03 | ` ` |

### `mgmt.delete_principal_role`

- `DELETE /v1/principal-roles/{r}` → **204**
- wall 37 ms · 36 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.09 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.10 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.04 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 3.21 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.01 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | grant_records | SELECT | 1.74 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 9 | grant_records | SELECT | 0.03 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 10 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | entities | DELETE | 0.04 | `DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?` |
| 12 | grant_records | SELECT | 1.63 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 13 | grant_records | SELECT | 0.04 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 14 | grant_records | DELETE | 2.68 | `DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (` |
| 15 | entities | SELECT | 0.02 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 16 | entities | UPDATE | 0.07 | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |
| 17 | entities | INSERT | 0.07 | `INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestam` |
| 18 | — | — | 0.13 | ` ` |
| 19 | — | — | 0.08 | ` ` |
| 20 | — | — | 0.04 | ` ` |
| 21 | — | — | 0.02 | ` ` |
| 22 | — | — | 0.06 | ` ` |
| 23 | — | — | 0.01 | ` ` |
| 24 | — | — | 0.02 | ` ` |
| 25 | — | — | 0.02 | ` ` |
| 26 | — | — | 0.01 | ` ` |
| 27 | — | — | 0.02 | ` ` |
| 28 | — | — | 0.09 | ` ` |
| 29 | — | — | 0.02 | ` ` |
| 30 | — | — | 0.08 | ` ` |
| 31 | — | — | 0.02 | ` ` |
| 32 | — | — | 0.02 | ` ` |
| 33 | — | — | 0.01 | ` ` |
| 34 | — | — | 0.02 | ` ` |
| 35 | — | — | 0.01 | ` ` |

### `mgmt.delete_principal`

- `DELETE /v1/principals/{p}` → **204**
- wall 58 ms · 34 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, principal_authentication_data

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | 0.14 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | 0.10 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | 0.10 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | 4.89 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | 0.08 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | 0.12 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | 0.05 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | grant_records | SELECT | 2.23 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 9 | grant_records | SELECT | 0.07 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 10 | entities | SELECT | 0.06 | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | entities | DELETE | 0.05 | `DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?` |
| 12 | grant_records | SELECT | 2.27 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 13 | grant_records | SELECT | 0.03 | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 14 | grant_records | DELETE | 3.29 | `DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (` |
| 15 | principal_authentication_data | DELETE | 0.10 | `DELETE FROM POLARIS_SCHEMA.PRINCIPAL_AUTHENTICATION_DATA WHERE realm_id = ? AND principal_id = ? AND principal_client_id = ?` |
| 16 | — | — | 0.42 | ` ` |
| 17 | — | — | 0.10 | ` ` |
| 18 | — | — | 0.07 | ` ` |
| 19 | — | — | 0.05 | ` ` |
| 20 | — | — | 0.07 | ` ` |
| 21 | — | — | 0.04 | ` ` |
| 22 | — | — | 0.07 | ` ` |
| 23 | — | — | 0.05 | ` ` |
| 24 | — | — | 0.03 | ` ` |
| 25 | — | — | 0.03 | ` ` |
| 26 | — | — | 0.05 | ` ` |
| 27 | — | — | 0.06 | ` ` |
| 28 | — | — | 0.04 | ` ` |
| 29 | — | — | 0.02 | ` ` |
| 30 | — | — | 0.03 | ` ` |
| 31 | — | — | 0.31 | ` ` |
| 32 | — | SELECT | 0.28 | `SELECT TRUE` |
| 33 | — | SELECT | 0.14 | `SELECT pg_catalog.pg_is_in_recovery()` |
