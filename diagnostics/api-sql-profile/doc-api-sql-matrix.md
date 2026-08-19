# API → SQL → MinIO Access Matrix

Generated 2026-08-19 17:22 from a live local run — Polaris 1.3.0, realm POLARIS.
Schema version 3 (DRIFT).

R = read, W = write, RW = both.

## API → PostgreSQL tables

| API | entities | grant_records | policy_mapping_record | principal_authentication_data |
|---|---|---|---|---|
| `iceberg.commit_table` | R | R | · | · |
| `iceberg.create_namespace` | RW | R | · | · |
| `iceberg.create_table` | RW | R | · | · |
| `iceberg.create_view` | RW | R | · | · |
| `iceberg.drop_namespace` | RW | RW | RW | · |
| `iceberg.drop_table` | RW | RW | RW | · |
| `iceberg.drop_view` | RW | RW | · | · |
| `iceberg.get_config` | R | R | · | · |
| `iceberg.head_namespace` | R | R | · | · |
| `iceberg.head_table` | R | R | · | · |
| `iceberg.head_view` | R | R | · | · |
| `iceberg.list_namespaces` | R | R | · | · |
| `iceberg.list_tables` | R | R | · | · |
| `iceberg.list_views` | R | R | · | · |
| `iceberg.load_namespace` | R | R | · | · |
| `iceberg.load_table` | R | R | · | · |
| `iceberg.load_table[missing]` | R | R | · | · |
| `iceberg.load_table[snapshots=refs]` | R | R | · | · |
| `iceberg.load_view` | R | R | · | · |
| `iceberg.rename_table` | RW | R | · | · |
| `iceberg.rename_view` | RW | R | · | · |
| `iceberg.report_metrics` | R | R | · | · |
| `iceberg.stage_create_table` | R | R | · | · |
| `iceberg.update_namespace_properties` | RW | R | · | · |
| `mgmt.assign_catalog_role` | RW | RW | · | · |
| `mgmt.assign_principal_role` | RW | RW | · | · |
| `mgmt.create_catalog_role` | RW | R | · | · |
| `mgmt.create_principal` | RW | R | · | RW |
| `mgmt.create_principal_role` | RW | R | · | · |
| `mgmt.delete_catalog_role` | RW | RW | · | · |
| `mgmt.delete_principal` | RW | RW | · | W |
| `mgmt.delete_principal_role` | RW | RW | · | · |
| `mgmt.get_catalog` | R | R | · | · |
| `mgmt.get_principal` | R | R | · | · |
| `mgmt.get_principal_role` | R | R | · | · |
| `mgmt.grant_privilege` | RW | RW | · | · |
| `mgmt.list_catalog_roles` | R | R | · | · |
| `mgmt.list_catalogs` | R | R | · | · |
| `mgmt.list_grants` | R | R | · | · |
| `mgmt.list_principal_roles` | R | R | · | · |
| `mgmt.list_principals` | R | R | · | · |
| `mgmt.list_principals_for_principal_role` | R | R | · | · |
| `mgmt.reset_principal_credentials` | R | R | · | RW |

## API → MinIO objects

| API | Method | Path | Count |
|---|---|---|---|
| `iceberg.create_table` |  | `/data-catalog-bucket/apiprofile1787127682_cat/probe_ns/probe_tbl2/metadata/00000-4fde6964-29d0-4065-8c05-32cae6e2d0af.metadata.json` | 1 |
| `iceberg.create_view` |  | `/data-catalog-bucket/apiprofile1787127682_cat/probe_ns/probe_view/metadata/00000-2c27b22e-aa69-41f0-b713-130c0788b47f.gz.metadata.json` | 2 |
| `iceberg.load_view` |  | `/data-catalog-bucket/apiprofile1787127682_cat/probe_ns/probe_view/metadata/00000-2c27b22e-aa69-41f0-b713-130c0788b47f.gz.metadata.json` | 2 |
| `iceberg.head_view` |  | `/data-catalog-bucket/apiprofile1787127682_cat/probe_ns/probe_view/metadata/00000-2c27b22e-aa69-41f0-b713-130c0788b47f.gz.metadata.json` | 2 |

## Per-API detail

### `iceberg.get_config`

- `GET /v1/config` → **200**
- wall 44 ms · 7 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |

### `iceberg.list_namespaces`

- `GET /v1/{cat}/namespaces` → **200**
- wall 17 ms · 8 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND sub_type_code = ? AND realm_id = ? AND parent_id = ? AND type` |

### `iceberg.load_namespace`

- `GET /v1/{cat}/namespaces/{ns}` → **200**
- wall 43 ms · 9 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 8 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |

### `iceberg.head_namespace`

- `HEAD /v1/{cat}/namespaces/{ns}` → **204**
- wall 33 ms · 7 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |

### `iceberg.update_namespace_properties`

- `POST /v1/{cat}/namespaces/{ns}/properties` → **200**
- wall 61 ms · 10 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND realm_id = ? AND type_code = ? AND catalog_id = ?` |
| 8 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | UPDATE | — | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |

### `iceberg.create_namespace`

- `POST /v1/{cat}/namespaces` → **500**
- wall 39 ms · 15 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND realm_id = ? AND type_code = ? AND catalog_id = ?` |
| 9 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 12 | entities | INSERT | — | `INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestam` |
| 13 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 14 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |

### `iceberg.drop_namespace`

- `DELETE /v1/{cat}/namespaces/{ns}` → **204**
- wall 35 ms · 16 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, policy_mapping_record

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 8 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | entities | DELETE | — | `DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?` |
| 12 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 13 | grant_records | DELETE | — | `DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (` |
| 14 | policy_mapping_record | SELECT | — | `SELECT target_catalog_id, target_id, policy_type_code, policy_catalog_id, policy_id, parameters FROM POLARIS_SCHEMA.POLICY_MAPPING_RECORD WHERE realm_id = ? AND target_id = ? AND t` |
| 15 | policy_mapping_record | DELETE | — | `DELETE FROM POLARIS_SCHEMA.POLICY_MAPPING_RECORD WHERE target_catalog_id = ? AND target_id = ? AND realm_id = ?` |

### `iceberg.list_tables`

- `GET /v1/{cat}/namespaces/{ns}/tables` → **200**
- wall 29 ms · 8 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND sub_type_code = ? AND realm_id = ? AND parent_id = ? AND type` |

### `iceberg.load_table`

- `GET /v1/{cat}/namespaces/{ns}/tables/{tbl}` → **404**
- wall 17 ms · 8 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |

### `iceberg.load_table[snapshots=refs]`

- `GET /v1/{cat}/.../tables/{tbl}?snapshots=refs` → **404**
- wall 28 ms · 8 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |

### `iceberg.head_table`

- `HEAD /v1/{cat}/namespaces/{ns}/tables/{tbl}` → **404**
- wall 26 ms · 8 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |

### `iceberg.create_table`

- `POST /v1/{cat}/namespaces/{ns}/tables` → **200**
- wall 105 ms · 23 statements · 1 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 12 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 13 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 14 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 15 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND realm_id = ? AND type_code = ? AND catalog_id = ?` |
| 16 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND realm_id = ? AND type_code = ? AND catalog_id = ?` |
| 17 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 18 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 19 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 20 | entities | INSERT | — | `INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestam` |
| 21 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 22 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |

| # | Method | Path | ms |
|---|---|---|---|
| 0 |  | `/data-catalog-bucket/apiprofile1787127682_cat/probe_ns/probe_tbl2/metadata/00000-4fde6964-29d0-4065-8c05-32cae6e2d0af.metadata.json` | 9.85 |

### `iceberg.stage_create_table`

- `POST /v1/{cat}/namespaces/{ns}/tables[stage]` → **200**
- wall 73 ms · 13 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 12 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |

### `iceberg.commit_table`

- `POST /v1/{cat}/namespaces/{ns}/tables/{tbl}` → **404**
- wall 24 ms · 8 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |

### `iceberg.rename_table`

- `POST /v1/{cat}/tables/rename` → **200**
- wall 40 ms · 13 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 8 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 12 | entities | UPDATE | — | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |

### `iceberg.report_metrics`

- `POST /v1/{cat}/.../tables/{tbl}/metrics` → **400**
- wall 25 ms · 6 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |

### `iceberg.load_table[missing]`

- `GET /v1/{cat}/.../tables/{missing}` → **404**
- wall 37 ms · 8 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |

### `iceberg.drop_table`

- `DELETE /v1/{cat}/namespaces/{ns}/tables/{tbl}` → **204**
- wall 53 ms · 15 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, policy_mapping_record

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 8 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | entities | DELETE | — | `DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?` |
| 11 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 12 | grant_records | DELETE | — | `DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (` |
| 13 | policy_mapping_record | SELECT | — | `SELECT target_catalog_id, target_id, policy_type_code, policy_catalog_id, policy_id, parameters FROM POLARIS_SCHEMA.POLICY_MAPPING_RECORD WHERE realm_id = ? AND target_id = ? AND t` |
| 14 | policy_mapping_record | DELETE | — | `DELETE FROM POLARIS_SCHEMA.POLICY_MAPPING_RECORD WHERE target_catalog_id = ? AND target_id = ? AND realm_id = ?` |

### `iceberg.create_view`

- `POST /v1/{cat}/namespaces/{ns}/views` → **200**
- wall 81 ms · 23 statements · 2 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 12 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 13 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 14 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND realm_id = ? AND type_code = ? AND catalog_id = ?` |
| 15 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND realm_id = ? AND type_code = ? AND catalog_id = ?` |
| 16 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 17 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 18 | entities | INSERT | — | `INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestam` |
| 19 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 20 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 21 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 22 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |

| # | Method | Path | ms |
|---|---|---|---|
| 0 |  | `/data-catalog-bucket/apiprofile1787127682_cat/probe_ns/probe_view/metadata/00000-2c27b22e-aa69-41f0-b713-130c0788b47f.gz.metadata.json` | 2.71 |
| 1 |  | `/data-catalog-bucket/apiprofile1787127682_cat/probe_ns/probe_view/metadata/00000-2c27b22e-aa69-41f0-b713-130c0788b47f.gz.metadata.json` | 0.78 |

### `iceberg.list_views`

- `GET /v1/{cat}/namespaces/{ns}/views` → **200**
- wall 16 ms · 8 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND sub_type_code = ? AND realm_id = ? AND parent_id = ? AND type` |

### `iceberg.load_view`

- `GET /v1/{cat}/namespaces/{ns}/views/{view}` → **200**
- wall 58 ms · 9 statements · 2 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |

| # | Method | Path | ms |
|---|---|---|---|
| 0 |  | `/data-catalog-bucket/apiprofile1787127682_cat/probe_ns/probe_view/metadata/00000-2c27b22e-aa69-41f0-b713-130c0788b47f.gz.metadata.json` | 1.88 |
| 1 |  | `/data-catalog-bucket/apiprofile1787127682_cat/probe_ns/probe_view/metadata/00000-2c27b22e-aa69-41f0-b713-130c0788b47f.gz.metadata.json` | 1.20 |

### `iceberg.head_view`

- `HEAD /v1/{cat}/namespaces/{ns}/views/{view}` → **204**
- wall 64 ms · 10 statements · 2 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |

| # | Method | Path | ms |
|---|---|---|---|
| 0 |  | `/data-catalog-bucket/apiprofile1787127682_cat/probe_ns/probe_view/metadata/00000-2c27b22e-aa69-41f0-b713-130c0788b47f.gz.metadata.json` | 1.64 |
| 1 |  | `/data-catalog-bucket/apiprofile1787127682_cat/probe_ns/probe_view/metadata/00000-2c27b22e-aa69-41f0-b713-130c0788b47f.gz.metadata.json` | 1.09 |

### `iceberg.rename_view`

- `POST /v1/{cat}/views/rename` → **204**
- wall 43 ms · 11 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | entities | UPDATE | — | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |

### `iceberg.drop_view`

- `DELETE /v1/{cat}/namespaces/{ns}/views/{view}` → **204**
- wall 21 ms · 14 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 8 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | entities | DELETE | — | `DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?` |
| 11 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 12 | grant_records | DELETE | — | `DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (` |
| 13 | entities | INSERT | — | `INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestam` |

### `mgmt.list_catalogs`

- `GET /v1/catalogs` → **200**
- wall 28 ms · 8 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |

### `mgmt.get_catalog`

- `GET /v1/catalogs/{cat}` → **200**
- wall 30 ms · 7 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |

### `mgmt.create_principal`

- `POST /v1/principals` → **201**
- wall 42 ms · 11 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, principal_authentication_data

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | principal_authentication_data | SELECT | — | `SELECT principal_id, principal_client_id, main_secret_hash, secondary_secret_hash, secret_salt FROM POLARIS_SCHEMA.PRINCIPAL_AUTHENTICATION_DATA WHERE realm_id = ? AND principal_cl` |
| 9 | principal_authentication_data | INSERT | — | `INSERT INTO POLARIS_SCHEMA.PRINCIPAL_AUTHENTICATION_DATA (principal_id, principal_client_id, main_secret_hash, secondary_secret_hash, secret_salt, realm_id) VALUES (?, ?, ?, ?, ?, ` |
| 10 | entities | INSERT | — | `INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestam` |

### `mgmt.get_principal`

- `GET /v1/principals/{p}` → **200**
- wall 22 ms · 10 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 8 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 9 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |

### `mgmt.list_principals`

- `GET /v1/principals` → **200**
- wall 34 ms · 8 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |

### `mgmt.create_principal_role`

- `POST /v1/principal-roles` → **201**
- wall 42 ms · 8 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | INSERT | — | `INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestam` |

### `mgmt.get_principal_role`

- `GET /v1/principal-roles/{r}` → **200**
- wall 27 ms · 10 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 8 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 9 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |

### `mgmt.list_principal_roles`

- `GET /v1/principal-roles` → **200**
- wall 65 ms · 8 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |

### `mgmt.assign_principal_role`

- `PUT /v1/principals/{p}/principal-roles` → **201**
- wall 25 ms · 12 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | grant_records | INSERT | — | `INSERT INTO POLARIS_SCHEMA.GRANT_RECORDS (securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code, realm_id) VALUES (?, ?, ?, ?, ?, ?)` |
| 8 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 9 | entities | UPDATE | — | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |
| 10 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | entities | UPDATE | — | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |

### `mgmt.create_catalog_role`

- `POST /v1/catalogs/{cat}/catalog-roles` → **201**
- wall 38 ms · 8 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | INSERT | — | `INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestam` |

### `mgmt.list_catalog_roles`

- `GET /v1/catalogs/{cat}/catalog-roles` → **200**
- wall 44 ms · 8 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |

### `mgmt.assign_catalog_role`

- `PUT /v1/principal-roles/{r}/catalog-roles/{cat}` → **201**
- wall 61 ms · 19 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 8 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 9 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 12 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 13 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 14 | grant_records | INSERT | — | `INSERT INTO POLARIS_SCHEMA.GRANT_RECORDS (securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code, realm_id) VALUES (?, ?, ?, ?, ?, ?)` |
| 15 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 16 | entities | UPDATE | — | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |
| 17 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 18 | entities | UPDATE | — | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |

### `mgmt.grant_privilege`

- `PUT /v1/catalogs/{cat}/catalog-roles/{cr}/grants` → **201**
- wall 54 ms · 24 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 9 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 10 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 12 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 13 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 14 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 15 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 16 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 17 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 18 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 19 | grant_records | INSERT | — | `INSERT INTO POLARIS_SCHEMA.GRANT_RECORDS (securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code, realm_id) VALUES (?, ?, ?, ?, ?, ?)` |
| 20 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 21 | entities | UPDATE | — | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |
| 22 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 23 | entities | UPDATE | — | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |

### `mgmt.list_grants`

- `GET /v1/catalogs/{cat}/catalog-roles/{cr}/grants` → **200**
- wall 36 ms · 15 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 9 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 10 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 11 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 12 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 13 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 14 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |

### `mgmt.list_principals_for_principal_role`

- `GET /v1/principal-roles/{r}/principals` → **200**
- wall 42 ms · 13 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 9 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 10 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 12 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |

### `mgmt.reset_principal_credentials`

- `POST /v1/principals/{p}/reset` → **200**
- wall 85 ms · 14 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, principal_authentication_data

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 9 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 10 | principal_authentication_data | SELECT | — | `SELECT principal_id, principal_client_id, main_secret_hash, secondary_secret_hash, secret_salt FROM POLARIS_SCHEMA.PRINCIPAL_AUTHENTICATION_DATA WHERE realm_id = ? AND principal_cl` |
| 11 | principal_authentication_data | DELETE | — | `DELETE FROM POLARIS_SCHEMA.PRINCIPAL_AUTHENTICATION_DATA WHERE realm_id = ? AND principal_id = ? AND principal_client_id = ?` |
| 12 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 13 | principal_authentication_data | INSERT | — | `INSERT INTO POLARIS_SCHEMA.PRINCIPAL_AUTHENTICATION_DATA (principal_id, principal_client_id, main_secret_hash, secondary_secret_hash, secret_salt, realm_id) VALUES (?, ?, ?, ?, ?, ` |

### `mgmt.delete_catalog_role`

- `DELETE /v1/catalogs/{cat}/catalog-roles/{cr}` → **204**
- wall 45 ms · 16 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | entities | DELETE | — | `DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?` |
| 9 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 10 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 11 | grant_records | DELETE | — | `DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (` |
| 12 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 13 | entities | UPDATE | — | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |
| 14 | entities | UPDATE | — | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |
| 15 | entities | INSERT | — | `INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestam` |

### `mgmt.delete_principal_role`

- `DELETE /v1/principal-roles/{r}` → **204**
- wall 46 ms · 18 statements · 0 object ops · cache: MISS
- tables: entities, grant_records

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 9 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 10 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | entities | DELETE | — | `DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?` |
| 12 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 13 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 14 | grant_records | DELETE | — | `DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (` |
| 15 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 16 | entities | UPDATE | — | `UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, ` |
| 17 | entities | INSERT | — | `INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestam` |

### `mgmt.delete_principal`

- `DELETE /v1/principals/{p}` → **204**
- wall 19 ms · 16 statements · 0 object ops · cache: MISS
- tables: entities, grant_records, principal_authentication_data

| # | Table | Verb | ms | SQL |
|---|---|---|---|---|
| 0 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 1 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 2 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 3 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 4 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 5 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 6 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 7 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 8 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 9 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 10 | entities | SELECT | — | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, prop` |
| 11 | entities | DELETE | — | `DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?` |
| 12 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalo` |
| 13 | grant_records | SELECT | — | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND secu` |
| 14 | grant_records | DELETE | — | `DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (` |
| 15 | principal_authentication_data | DELETE | — | `DELETE FROM POLARIS_SCHEMA.PRINCIPAL_AUTHENTICATION_DATA WHERE realm_id = ? AND principal_id = ? AND principal_client_id = ?` |
