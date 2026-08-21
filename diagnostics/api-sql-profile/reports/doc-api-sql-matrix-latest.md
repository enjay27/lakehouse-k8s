# API → SQL → MinIO Access Matrix

Generated 2026-08-20 17:30 from a live local run — Polaris 1.3.0, realm POLARIS.
Schema version 3 (OK).

R = read, W = write, RW = both.

## API → PostgreSQL tables

| API | entities | grant_records | policy_mapping_record | principal_authentication_data |
|---|---|---|---|---|
| `iceberg.commit_table` | RW | R | · | · |
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
| `preflight` | R | R | · | · |

## API → MinIO objects

| API | Method | Path | Count |
|---|---|---|---|
| `iceberg.load_table` |  | `/data-catalog-bucket/apiprofile1787214579_cat/probe_ns/probe_tbl/metadata/00000-1b556ee0-a1dd-439a-9cbe-71d3646f1944.metadata.json` | 1 |
| `iceberg.load_table[snapshots=refs]` |  | `/data-catalog-bucket/apiprofile1787214579_cat/probe_ns/probe_tbl/metadata/00000-1b556ee0-a1dd-439a-9cbe-71d3646f1944.metadata.json` | 1 |
| `iceberg.head_table` |  | `/data-catalog-bucket/apiprofile1787214579_cat/probe_ns/probe_tbl/metadata/00000-1b556ee0-a1dd-439a-9cbe-71d3646f1944.metadata.json` | 1 |
| `iceberg.create_table` |  | `/data-catalog-bucket/apiprofile1787214579_cat/probe_ns/probe_tbl2/metadata/00000-a1684285-f43c-4ef6-9a4e-96a68caa1af4.metadata.json` | 1 |
| `iceberg.commit_table` |  | `/data-catalog-bucket/apiprofile1787214579_cat/probe_ns/probe_tbl/metadata/00000-1b556ee0-a1dd-439a-9cbe-71d3646f1944.metadata.json` | 2 |
| `iceberg.commit_table` |  | `/data-catalog-bucket/apiprofile1787214579_cat/probe_ns/probe_tbl/metadata/00001-9c1c6c51-2b70-45d5-a5e5-f0cbdbc624c3.metadata.json` | 1 |
| `iceberg.create_view` |  | `/data-catalog-bucket/apiprofile1787214579_cat/probe_ns/probe_view/metadata/00000-e41c88e7-0742-4ee9-846a-66427be9cabc.gz.metadata.json` | 1 |
| `iceberg.load_view` |  | `/data-catalog-bucket/apiprofile1787214579_cat/probe_ns/probe_view/metadata/00000-e41c88e7-0742-4ee9-846a-66427be9cabc.gz.metadata.json` | 2 |
| `iceberg.head_view` |  | `/data-catalog-bucket/apiprofile1787214579_cat/probe_ns/probe_view/metadata/00000-e41c88e7-0742-4ee9-846a-66427be9cabc.gz.metadata.json` | 2 |

## Per-API detail

### `preflight`

- `GET /probe` → **None**
- wall 58 ms · 8 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

**[1]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1, 2, 0`

**[2]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1`

**[3]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1, POLARIS, 0`

**[4]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

**[5]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

**[6]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 0, POLARIS`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND realm_id = ? AND type_code = ? AND catalog_id = ?
```
params: `0, POLARIS, 4, 0`

### `iceberg.get_config`

- `GET /v1/config` → **200**
- wall 25 ms · 7 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

**[1]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1, 2, 0`

**[2]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1`

**[3]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1, POLARIS, 0`

**[4]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

**[5]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

**[6]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, POLARIS`

### `iceberg.list_namespaces`

- `GET /v1/{cat}/namespaces` → **200**
- wall 30 ms · 8 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

**[1]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1, 2, 0`

**[2]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1`

**[3]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1, POLARIS, 0`

**[4]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

**[5]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

**[6]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 0, 0, POLARIS`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND sub_type_code = ? AND realm_id = ? AND parent_id = ? AND type_code = ?
```
params: `7985247348701050877, 0, POLARIS, 7985247348701050877, 6`

### `iceberg.load_namespace`

- `GET /v1/{cat}/namespaces/{ns}` → **200**
- wall 10 ms · 7 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

**[1]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1, 2, 0`

**[2]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1`

**[3]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1, POLARIS, 0`

**[4]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

**[5]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

**[6]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 0, 0, 7985247348701050877, 4330322395356732719, POLARIS`

### `iceberg.head_namespace`

- `HEAD /v1/{cat}/namespaces/{ns}` → **204**
- wall 25 ms · 7 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

**[1]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1, 2, 0`

**[2]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1`

**[3]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1, POLARIS, 0`

**[4]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

**[5]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

**[6]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 0, 0, 7985247348701050877, 4330322395356732719, POLARIS`

### `iceberg.update_namespace_properties`

- `POST /v1/{cat}/namespaces/{ns}/properties` → **200**
- wall 23 ms · 10 statements · 0 object ops · entity access: MIXED (batched 43% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

**[1]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1, 2, 0`

**[2]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1`

**[3]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1, POLARIS, 0`

**[4]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

**[5]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

**[6]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 0, 0, 7985247348701050877, 4330322395356732719, POLARIS`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND realm_id = ? AND type_code = ? AND catalog_id = ?
```
params: `7985247348701050877, POLARIS, 6, 7985247348701050877`

**[8]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 0, 0, 7985247348701050877, 4330322395356732719, 7985247348701050877, 81815684489211632, POLARIS`

**[9]** `entities` · UPDATE · no timing

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE realm_id = ? AND entity_version = ? AND id = ? AND catalog_id = ?
```
params: `4330322395356732719, 7985247348701050877, 7985247348701050877, 6, probe_ns, 2, 0, 1787214579710, 0, 0, 0, 1787214582272, {"location":"s3a://data-catalog-bucket/apiprofile1787214579_cat/probe_ns/","k":"v"}, {}, 1, //data-catalog-bucket/apiprofile1787214579_cat/probe_ns/, POLARIS, 1, 4330322395356732719, 7985247348701050877`

### `iceberg.create_namespace`

- `POST /v1/{cat}/namespaces` → **500**
- wall 15 ms · 15 statements · 0 object ops · entity access: MIXED (batched 42% of 12 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

**[1]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1, 2, 0`

**[2]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1`

**[3]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1, POLARIS, 0`

**[4]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

**[5]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

**[6]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, probe_ns_tmp, 7985247348701050877, 7985247348701050877, 6`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 0, 0, POLARIS`

**[8]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND realm_id = ? AND type_code = ? AND catalog_id = ?
```
params: `7985247348701050877, POLARIS, 6, 7985247348701050877`

**[9]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 0, 0, 7985247348701050877, 4330322395356732719, 7985247348701050877, 81815684489211632, POLARIS`

**[10]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `7985247348701050877, 4330322395356732719, POLARIS`

**[11]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 4330322395356732719, 6, 7985247348701050877`

**[12]** `entities` · INSERT · no timing

```sql
INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme, realm_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```
params: `9085954845997121812, 7985247348701050877, 7985247348701050877, 6, probe_ns_tmp, 1, 0, 1787214582590, 0, 0, 0, 1787214582590, {"location":"s3a://data-catalog-bucket/apiprofile1787214579_cat/probe_ns_tmp/"}, {}, 1, //data-catalog-bucket/apiprofile1787214579_cat/probe_ns_tmp/, POLARIS`

**[13]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, probe_ns_tmp, 7985247348701050877, 7985247348701050877, 6`

**[14]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, POLARIS`

### `iceberg.drop_namespace`

- `DELETE /v1/{cat}/namespaces/{ns}` → **204**
- wall 48 ms · 16 statements · 0 object ops · entity access: MIXED (batched 25% of 8 reads)
- tables: entities, grant_records, policy_mapping_record

**[0]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

**[1]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1, 2, 0`

**[2]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1`

**[3]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1, POLARIS, 0`

**[4]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

**[5]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

**[6]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, probe_ns_tmp, 7985247348701050877, 7985247348701050877, 6`

**[7]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `7985247348701050877, POLARIS, 9085954845997121812`

**[8]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 0, 0, POLARIS`

**[9]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9085954845997121812, 6, 7985247348701050877`

**[10]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND realm_id = ?
```
params: `7985247348701050877, 9085954845997121812, POLARIS`

**[11]** `entities` · DELETE · no timing

```sql
DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 7985247348701050877, 9085954845997121812`

**[12]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `7985247348701050877, POLARIS, 9085954845997121812`

**[13]** `grant_records` · DELETE · no timing

```sql
DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (
    (grantee_id = ? AND grantee_catalog_id = ?) OR
    (securable_id = ? AND securable_catalog_id = ?)
) AND realm_id = ?
```
params: `9085954845997121812, 7985247348701050877, 9085954845997121812, 7985247348701050877, POLARIS`

**[14]** `policy_mapping_record` · SELECT · no timing

```sql
SELECT target_catalog_id, target_id, policy_type_code, policy_catalog_id, policy_id, parameters FROM POLARIS_SCHEMA.POLICY_MAPPING_RECORD WHERE realm_id = ? AND target_id = ? AND target_catalog_id = ?
```
params: `POLARIS, 9085954845997121812, 7985247348701050877`

**[15]** `policy_mapping_record` · DELETE · no timing

```sql
DELETE FROM POLARIS_SCHEMA.POLICY_MAPPING_RECORD WHERE target_catalog_id = ? AND target_id = ? AND realm_id = ?
```
params: `7985247348701050877, 9085954845997121812, POLARIS`

### `iceberg.list_tables`

- `GET /v1/{cat}/namespaces/{ns}/tables` → **200**
- wall 27 ms · 8 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

**[1]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1, 2, 0`

**[2]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1`

**[3]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1, POLARIS, 0`

**[4]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

**[5]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

**[6]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 0, 0, 7985247348701050877, 4330322395356732719, POLARIS`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND sub_type_code = ? AND realm_id = ? AND parent_id = ? AND type_code = ?
```
params: `7985247348701050877, 2, POLARIS, 4330322395356732719, 7`

### `iceberg.load_table`

- `GET /v1/{cat}/namespaces/{ns}/tables/{tbl}` → **200**
- wall 61 ms · 12 statements · 1 object ops · entity access: MIXED (batched 30% of 10 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

**[1]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1, 2, 0`

**[2]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1`

**[3]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1, POLARIS, 0`

**[4]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

**[5]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

**[6]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, probe_tbl, 7985247348701050877, 4330322395356732719, 7`

**[7]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `7985247348701050877, POLARIS, 2490852191059560064`

**[8]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 0, 0, 7985247348701050877, 4330322395356732719, POLARIS`

**[9]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 7985247348701050877, 4330322395356732719, 7985247348701050877, 2490852191059560064, POLARIS`

**[10]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 7985247348701050877, 4, 0`

**[11]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 7985247348701050877, 4, 0`

| # | Method | Path | ms |
|---|---|---|---|
| 0 |  | `/data-catalog-bucket/apiprofile1787214579_cat/probe_ns/probe_tbl/metadata/00000-1b556ee0-a1dd-439a-9cbe-71d3646f1944.metadata.json` | 1.88 |

### `iceberg.load_table[snapshots=refs]`

- `GET /v1/{cat}/.../tables/{tbl}?snapshots=refs` → **200**
- wall 46 ms · 8 statements · 1 object ops · entity access: MIXED (batched 43% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

**[1]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1, 2, 0`

**[2]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1`

**[3]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1, POLARIS, 0`

**[4]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

**[5]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

**[6]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 0, 0, 7985247348701050877, 4330322395356732719, 7985247348701050877, 2490852191059560064, POLARIS`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 7985247348701050877, 4330322395356732719, 7985247348701050877, 2490852191059560064, POLARIS`

| # | Method | Path | ms |
|---|---|---|---|
| 0 |  | `/data-catalog-bucket/apiprofile1787214579_cat/probe_ns/probe_tbl/metadata/00000-1b556ee0-a1dd-439a-9cbe-71d3646f1944.metadata.json` | 1.60 |

### `iceberg.head_table`

- `HEAD /v1/{cat}/namespaces/{ns}/tables/{tbl}` → **204**
- wall 33 ms · 8 statements · 1 object ops · entity access: MIXED (batched 43% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

**[1]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1, 2, 0`

**[2]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1`

**[3]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1, POLARIS, 0`

**[4]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

**[5]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

**[6]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 0, 0, 7985247348701050877, 4330322395356732719, 7985247348701050877, 2490852191059560064, POLARIS`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 7985247348701050877, 4330322395356732719, 7985247348701050877, 2490852191059560064, POLARIS`

| # | Method | Path | ms |
|---|---|---|---|
| 0 |  | `/data-catalog-bucket/apiprofile1787214579_cat/probe_ns/probe_tbl/metadata/00000-1b556ee0-a1dd-439a-9cbe-71d3646f1944.metadata.json` | 2.29 |

### `iceberg.create_table`

- `POST /v1/{cat}/namespaces/{ns}/tables` → **200**
- wall 108 ms · 23 statements · 1 object ops · entity access: MIXED (batched 42% of 19 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

**[1]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1, 2, 0`

**[2]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1`

**[3]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1, POLARIS, 0`

**[4]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

**[5]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

**[6]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, probe_tbl2, 7985247348701050877, 4330322395356732719, 7`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 0, 0, 7985247348701050877, 4330322395356732719, POLARIS`

**[8]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, probe_tbl2, 7985247348701050877, 4330322395356732719, 7`

**[9]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 7985247348701050877, 4330322395356732719, POLARIS`

**[10]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, probe_tbl2, 7985247348701050877, 4330322395356732719, 7`

**[11]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 7985247348701050877, 4330322395356732719, POLARIS`

**[12]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, probe_tbl2, 7985247348701050877, 4330322395356732719, 7`

**[13]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 7985247348701050877, 4330322395356732719, POLARIS`

**[14]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 7985247348701050877, 4, 0`

**[15]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND realm_id = ? AND type_code = ? AND catalog_id = ?
```
params: `4330322395356732719, POLARIS, 6, 7985247348701050877`

**[16]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND realm_id = ? AND type_code = ? AND catalog_id = ?
```
params: `4330322395356732719, POLARIS, 7, 7985247348701050877`

**[17]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 0, 0, 7985247348701050877, 4330322395356732719, 7985247348701050877, 2490852191059560064, POLARIS`

**[18]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, probe_tbl2, 7985247348701050877, 4330322395356732719, 7`

**[19]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 7985247348701050877, 4330322395356732719, POLARIS`

**[20]** `entities` · INSERT · no timing

```sql
INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme, realm_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```
params: `7284585148917262979, 7985247348701050877, 4330322395356732719, 7, probe_tbl2, 1, 2, 1787214585840, 0, 0, 0, 1787214585840, {"location":"s3a://data-catalog-bucket/apiprofile1787214579_cat/probe_ns/probe_tbl2/"}, {"last-sequence-number":"0","last-updated-ms":"1787214585780","next-row-id":"0","format-version":"2","metadata-location":"s3a://data-catalog-bucket/apiprofile1787214579_cat/probe_ns/probe_tbl2/metadata/00000-a1684285-f43c-4ef6-9a4e-96a68caa1af4.metadata.json","table-uuid":"91766716-ee0c-46f5-955f-9a3b9d4da5bd","default-sort-order-id":"0","last-partition-id":"999","parent-namespace":"probe_ns","current-schema-id":"0","location":"s3a://data-catalog-bucket/apiprofile1787214579_cat/probe_ns/probe_tbl2","last-column-id":"2","default-spec-id":"0"}, 1, //data-catalog-bucket/apiprofile1787214579_cat/probe_ns/probe_tbl2/, POLARIS`

**[21]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, probe_tbl2, 7985247348701050877, 4330322395356732719, 7`

**[22]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 7985247348701050877, 4330322395356732719, POLARIS`

| # | Method | Path | ms |
|---|---|---|---|
| 0 |  | `/data-catalog-bucket/apiprofile1787214579_cat/probe_ns/probe_tbl2/metadata/00000-a1684285-f43c-4ef6-9a4e-96a68caa1af4.metadata.json` | 15.86 |

### `iceberg.stage_create_table`

- `POST /v1/{cat}/namespaces/{ns}/tables[stage]` → **200**
- wall 52 ms · 13 statements · 0 object ops · entity access: MIXED (batched 33% of 12 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

**[1]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1, 2, 0`

**[2]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1`

**[3]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1, POLARIS, 0`

**[4]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

**[5]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

**[6]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, probe_staged, 7985247348701050877, 4330322395356732719, 7`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 0, 0, 7985247348701050877, 4330322395356732719, POLARIS`

**[8]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, probe_staged, 7985247348701050877, 4330322395356732719, 7`

**[9]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 7985247348701050877, 4330322395356732719, POLARIS`

**[10]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, probe_staged, 7985247348701050877, 4330322395356732719, 7`

**[11]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 7985247348701050877, 4330322395356732719, POLARIS`

**[12]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 7985247348701050877, 4, 0`

### `iceberg.commit_table`

- `POST /v1/{cat}/namespaces/{ns}/tables/{tbl}` → **200**
- wall 78 ms · 12 statements · 3 object ops · entity access: MIXED (batched 60% of 10 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

**[1]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1, 2, 0`

**[2]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1`

**[3]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1, POLARIS, 0`

**[4]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

**[5]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

**[6]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 0, 0, 7985247348701050877, 4330322395356732719, 7985247348701050877, 2490852191059560064, POLARIS`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 7985247348701050877, 4330322395356732719, 7985247348701050877, 2490852191059560064, POLARIS`

**[8]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 7985247348701050877, 4330322395356732719, 7985247348701050877, 2490852191059560064, POLARIS`

**[9]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 7985247348701050877, 4330322395356732719, 7985247348701050877, 2490852191059560064, POLARIS`

**[10]** `entities` · UPDATE · no timing

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE realm_id = ? AND entity_version = ? AND id = ? AND catalog_id = ?
```
params: `2490852191059560064, 7985247348701050877, 4330322395356732719, 7, probe_tbl, 2, 2, 1787214579791, 0, 0, 0, 1787214586578, {"location":"s3a://data-catalog-bucket/apiprofile1787214579_cat/probe_ns/probe_tbl/"}, {"last-sequence-number":"0","last-updated-ms":"1787214586559","next-row-id":"0","format-version":"2","metadata-location":"s3a://data-catalog-bucket/apiprofile1787214579_cat/probe_ns/probe_tbl/metadata/00001-9c1c6c51-2b70-45d5-a5e5-f0cbdbc624c3.metadata.json","table-uuid":"6cd24cab-5f56-4325-a11b-3bd22fcccb41","default-sort-order-id":"0","last-partition-id":"999","parent-namespace":"probe_ns","current-schema-id":"0","location":"s3a://data-catalog-bucket/apiprofile1787214579_cat/probe_ns/probe_tbl","last-column-id":"2","default-spec-id":"0"}, 1, //data-catalog-bucket/apiprofile1787214579_cat/probe_ns/probe_tbl/, POLARIS, 1, 2490852191059560064, 7985247348701050877`

**[11]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 7985247348701050877, 4330322395356732719, 7985247348701050877, 2490852191059560064, POLARIS`

| # | Method | Path | ms |
|---|---|---|---|
| 0 |  | `/data-catalog-bucket/apiprofile1787214579_cat/probe_ns/probe_tbl/metadata/00000-1b556ee0-a1dd-439a-9cbe-71d3646f1944.metadata.json` | 2.46 |
| 1 |  | `/data-catalog-bucket/apiprofile1787214579_cat/probe_ns/probe_tbl/metadata/00001-9c1c6c51-2b70-45d5-a5e5-f0cbdbc624c3.metadata.json` | 7.28 |
| 2 |  | `/data-catalog-bucket/apiprofile1787214579_cat/probe_ns/probe_tbl/metadata/00000-1b556ee0-a1dd-439a-9cbe-71d3646f1944.metadata.json` | 1.34 |

### `iceberg.rename_table`

- `POST /v1/{cat}/tables/rename` → **200**
- wall 41 ms · 13 statements · 0 object ops · entity access: MIXED (batched 20% of 10 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

**[1]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1, 2, 0`

**[2]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1`

**[3]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1, POLARIS, 0`

**[4]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

**[5]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

**[6]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, probe_tbl2, 7985247348701050877, 4330322395356732719, 7`

**[7]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `7985247348701050877, POLARIS, 7284585148917262979`

**[8]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, probe_tbl3, 7985247348701050877, 4330322395356732719, 7`

**[9]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 0, 0, 7985247348701050877, 4330322395356732719, POLARIS`

**[10]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 7284585148917262979, 7, 7985247348701050877`

**[11]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, probe_tbl3, 7985247348701050877, 4330322395356732719, 7`

**[12]** `entities` · UPDATE · no timing

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE realm_id = ? AND entity_version = ? AND id = ? AND catalog_id = ?
```
params: `7284585148917262979, 7985247348701050877, 4330322395356732719, 7, probe_tbl3, 2, 2, 1787214585840, 0, 0, 0, 1787214586933, {"location":"s3a://data-catalog-bucket/apiprofile1787214579_cat/probe_ns/probe_tbl2/"}, {"last-updated-ms":"1787214585780","last-sequence-number":"0","next-row-id":"0","format-version":"2","metadata-location":"s3a://data-catalog-bucket/apiprofile1787214579_cat/probe_ns/probe_tbl2/metadata/00000-a1684285-f43c-4ef6-9a4e-96a68caa1af4.metadata.json","table-uuid":"91766716-ee0c-46f5-955f-9a3b9d4da5bd","default-sort-order-id":"0","last-partition-id":"999","parent-namespace":"probe_ns","current-schema-id":"0","location":"s3a://data-catalog-bucket/apiprofile1787214579_cat/probe_ns/probe_tbl2","last-column-id":"2","default-spec-id":"0"}, 1, //data-catalog-bucket/apiprofile1787214579_cat/probe_ns/probe_tbl2/, POLARIS, 1, 7284585148917262979, 7985247348701050877`

### `iceberg.report_metrics`

- `POST /v1/{cat}/.../tables/{tbl}/metrics` → **204**
- wall 12 ms · 6 statements · 0 object ops · entity access: MIXED (batched 20% of 5 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

**[1]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1, 2, 0`

**[2]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1`

**[3]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1, POLARIS, 0`

**[4]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

**[5]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

### `iceberg.load_table[missing]`

- `GET /v1/{cat}/.../tables/{missing}` → **404**
- wall 7 ms · 8 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

**[1]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1, 2, 0`

**[2]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1`

**[3]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1, POLARIS, 0`

**[4]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

**[5]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

**[6]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, does_not_exist, 7985247348701050877, 4330322395356732719, 7`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 0, 0, 7985247348701050877, 4330322395356732719, POLARIS`

### `iceberg.drop_table`

- `DELETE /v1/{cat}/namespaces/{ns}/tables/{tbl}` → **204**
- wall 34 ms · 15 statements · 0 object ops · entity access: MIXED (batched 25% of 8 reads)
- tables: entities, grant_records, policy_mapping_record

**[0]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

**[1]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1, 2, 0`

**[2]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1`

**[3]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1, POLARIS, 0`

**[4]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

**[5]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

**[6]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, probe_tbl3, 7985247348701050877, 4330322395356732719, 7`

**[7]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `7985247348701050877, POLARIS, 7284585148917262979`

**[8]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 0, 0, 7985247348701050877, 4330322395356732719, POLARIS`

**[9]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 7284585148917262979, 7, 7985247348701050877`

**[10]** `entities` · DELETE · no timing

```sql
DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 7985247348701050877, 7284585148917262979`

**[11]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `7985247348701050877, POLARIS, 7284585148917262979`

**[12]** `grant_records` · DELETE · no timing

```sql
DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (
    (grantee_id = ? AND grantee_catalog_id = ?) OR
    (securable_id = ? AND securable_catalog_id = ?)
) AND realm_id = ?
```
params: `7284585148917262979, 7985247348701050877, 7284585148917262979, 7985247348701050877, POLARIS`

**[13]** `policy_mapping_record` · SELECT · no timing

```sql
SELECT target_catalog_id, target_id, policy_type_code, policy_catalog_id, policy_id, parameters FROM POLARIS_SCHEMA.POLICY_MAPPING_RECORD WHERE realm_id = ? AND target_id = ? AND target_catalog_id = ?
```
params: `POLARIS, 7284585148917262979, 7985247348701050877`

**[14]** `policy_mapping_record` · DELETE · no timing

```sql
DELETE FROM POLARIS_SCHEMA.POLICY_MAPPING_RECORD WHERE target_catalog_id = ? AND target_id = ? AND realm_id = ?
```
params: `7985247348701050877, 7284585148917262979, POLARIS`

### `iceberg.create_view`

- `POST /v1/{cat}/namespaces/{ns}/views` → **500**
- wall 82 ms · 21 statements · 1 object ops · entity access: MIXED (batched 41% of 17 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

**[1]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1, 2, 0`

**[2]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1`

**[3]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1, POLARIS, 0`

**[4]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

**[5]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

**[6]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, probe_view, 7985247348701050877, 4330322395356732719, 7`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 0, 0, 7985247348701050877, 4330322395356732719, POLARIS`

**[8]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, probe_view, 7985247348701050877, 4330322395356732719, 7`

**[9]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 7985247348701050877, 4330322395356732719, POLARIS`

**[10]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, probe_view, 7985247348701050877, 4330322395356732719, 7`

**[11]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 7985247348701050877, 4330322395356732719, POLARIS`

**[12]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, probe_view, 7985247348701050877, 4330322395356732719, 7`

**[13]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 7985247348701050877, 4330322395356732719, POLARIS`

**[14]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND realm_id = ? AND type_code = ? AND catalog_id = ?
```
params: `4330322395356732719, POLARIS, 6, 7985247348701050877`

**[15]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND realm_id = ? AND type_code = ? AND catalog_id = ?
```
params: `4330322395356732719, POLARIS, 7, 7985247348701050877`

**[16]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 0, 0, 7985247348701050877, 4330322395356732719, 7985247348701050877, 2490852191059560064, POLARIS`

**[17]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 7985247348701050877, 4, 0`

**[18]** `entities` · INSERT · no timing

```sql
INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme, realm_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```
params: `77192520090151552, 7985247348701050877, 4330322395356732719, 7, probe_view, 1, 3, 1787214589160, 0, 0, 0, 1787214589160, {}, {"metadata-location":"s3a://data-catalog-bucket/apiprofile1787214579_cat/probe_ns/probe_view/metadata/00000-e41c88e7-0742-4ee9-846a-66427be9cabc.gz.metadata.json","parent-namespace":"probe_ns"}, 1, NULL, POLARIS`

**[19]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, probe_view, 7985247348701050877, 4330322395356732719, 7`

**[20]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 7985247348701050877, 4330322395356732719, POLARIS`

| # | Method | Path | ms |
|---|---|---|---|
| 0 |  | `/data-catalog-bucket/apiprofile1787214579_cat/probe_ns/probe_view/metadata/00000-e41c88e7-0742-4ee9-846a-66427be9cabc.gz.metadata.json` | 3.35 |

### `iceberg.list_views`

- `GET /v1/{cat}/namespaces/{ns}/views` → **200**
- wall 9 ms · 8 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

**[1]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1, 2, 0`

**[2]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1`

**[3]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1, POLARIS, 0`

**[4]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

**[5]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

**[6]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 0, 0, 7985247348701050877, 4330322395356732719, POLARIS`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND sub_type_code = ? AND realm_id = ? AND parent_id = ? AND type_code = ?
```
params: `7985247348701050877, 3, POLARIS, 4330322395356732719, 7`

### `iceberg.load_view`

- `GET /v1/{cat}/namespaces/{ns}/views/{view}` → **200**
- wall 61 ms · 12 statements · 2 object ops · entity access: MIXED (batched 40% of 10 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

**[1]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1, 2, 0`

**[2]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1`

**[3]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1, POLARIS, 0`

**[4]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

**[5]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

**[6]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, probe_view, 7985247348701050877, 4330322395356732719, 7`

**[7]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `7985247348701050877, POLARIS, 77192520090151552`

**[8]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 0, 0, 7985247348701050877, 4330322395356732719, POLARIS`

**[9]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 7985247348701050877, 4330322395356732719, 7985247348701050877, 77192520090151552, POLARIS`

**[10]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 7985247348701050877, 4, 0`

**[11]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 7985247348701050877, 4330322395356732719, 7985247348701050877, 77192520090151552, POLARIS`

| # | Method | Path | ms |
|---|---|---|---|
| 0 |  | `/data-catalog-bucket/apiprofile1787214579_cat/probe_ns/probe_view/metadata/00000-e41c88e7-0742-4ee9-846a-66427be9cabc.gz.metadata.json` | 2.14 |
| 1 |  | `/data-catalog-bucket/apiprofile1787214579_cat/probe_ns/probe_view/metadata/00000-e41c88e7-0742-4ee9-846a-66427be9cabc.gz.metadata.json` | 1.59 |

### `iceberg.head_view`

- `HEAD /v1/{cat}/namespaces/{ns}/views/{view}` → **204**
- wall 34 ms · 9 statements · 2 object ops · entity access: MIXED (batched 50% of 8 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

**[1]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1, 2, 0`

**[2]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1`

**[3]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1, POLARIS, 0`

**[4]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

**[5]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

**[6]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 0, 0, 7985247348701050877, 4330322395356732719, 7985247348701050877, 77192520090151552, POLARIS`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 7985247348701050877, 4330322395356732719, 7985247348701050877, 77192520090151552, POLARIS`

**[8]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 7985247348701050877, 4330322395356732719, 7985247348701050877, 77192520090151552, POLARIS`

| # | Method | Path | ms |
|---|---|---|---|
| 0 |  | `/data-catalog-bucket/apiprofile1787214579_cat/probe_ns/probe_view/metadata/00000-e41c88e7-0742-4ee9-846a-66427be9cabc.gz.metadata.json` | 1.88 |
| 1 |  | `/data-catalog-bucket/apiprofile1787214579_cat/probe_ns/probe_view/metadata/00000-e41c88e7-0742-4ee9-846a-66427be9cabc.gz.metadata.json` | 1.65 |

### `iceberg.rename_view`

- `POST /v1/{cat}/views/rename` → **204**
- wall 65 ms · 12 statements · 0 object ops · entity access: MIXED (batched 20% of 10 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

**[1]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1, 2, 0`

**[2]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1`

**[3]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1, POLARIS, 0`

**[4]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

**[5]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

**[6]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, probe_view2, 7985247348701050877, 4330322395356732719, 7`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 0, 0, 7985247348701050877, 4330322395356732719, 7985247348701050877, 77192520090151552, POLARIS`

**[8]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 77192520090151552, 7, 7985247348701050877`

**[9]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, probe_view2, 7985247348701050877, 4330322395356732719, 7`

**[10]** `entities` · UPDATE · no timing

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE realm_id = ? AND entity_version = ? AND id = ? AND catalog_id = ?
```
params: `77192520090151552, 7985247348701050877, 4330322395356732719, 7, probe_view2, 2, 3, 1787214589160, 0, 0, 0, 1787214590564, {}, {"metadata-location":"s3a://data-catalog-bucket/apiprofile1787214579_cat/probe_ns/probe_view/metadata/00000-e41c88e7-0742-4ee9-846a-66427be9cabc.gz.metadata.json","parent-namespace":"probe_ns"}, 1, NULL, POLARIS, 1, 77192520090151552, 7985247348701050877`

**[11]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

### `iceberg.drop_view`

- `DELETE /v1/{cat}/namespaces/{ns}/views/{view}` → **204**
- wall 42 ms · 14 statements · 0 object ops · entity access: MIXED (batched 25% of 8 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

**[1]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1, 2, 0`

**[2]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1`

**[3]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1, POLARIS, 0`

**[4]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

**[5]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

**[6]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, probe_view2, 7985247348701050877, 4330322395356732719, 7`

**[7]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `7985247348701050877, POLARIS, 77192520090151552`

**[8]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 0, 0, 7985247348701050877, 4330322395356732719, POLARIS`

**[9]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 77192520090151552, 7, 7985247348701050877`

**[10]** `entities` · DELETE · no timing

```sql
DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 7985247348701050877, 77192520090151552`

**[11]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `7985247348701050877, POLARIS, 77192520090151552`

**[12]** `grant_records` · DELETE · no timing

```sql
DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (
    (grantee_id = ? AND grantee_catalog_id = ?) OR
    (securable_id = ? AND securable_catalog_id = ?)
) AND realm_id = ?
```
params: `77192520090151552, 7985247348701050877, 77192520090151552, 7985247348701050877, POLARIS`

**[13]** `entities` · INSERT · no timing

```sql
INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme, realm_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```
params: `6923719808841152165, 0, 0, 8, entityCleanup_77192520090151552, 1, 0, 1787214590943, 0, 0, 0, 1787214590943, {"taskType":"1","data":"{\"catalogId\":7985247348701050877,\"id\":77192520090151552,\"parentId\":4330322395356732719,\"typeCode\":7,\"name\":\"probe_view2\",\"entityVersion\":2,\"subTypeCode\":3,\"createTimestamp\":1787214589160,\"dropTimestamp\":0,\"purgeTimestamp\":0,\"toPurgeTimestamp\":0,\"lastUpdateTimestamp\":1787214590564,\"properties\":\"{}\",\"internalProperties\":\"{\\\"parent-namespace\\\": \\\"probe_ns\\\", \\\"metadata-location\\\": \\\"s3a://data-catalog-bucket/apiprofile1787214579_cat/probe_ns/probe_view/metadata/00000-e41c88e7-0742-4ee9-846a-66427be9cabc.gz.metadata.json\\\"}\",\"grantRecordsVersion\":1}"}, {}, 1, NULL, POLARIS`

### `mgmt.list_catalogs`

- `GET /v1/catalogs` → **200**
- wall 68 ms · 8 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

**[1]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1, 2, 0`

**[2]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1`

**[3]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1, POLARIS, 0`

**[4]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

**[5]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

**[6]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 0, POLARIS`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND realm_id = ? AND type_code = ? AND catalog_id = ?
```
params: `0, POLARIS, 4, 0`

### `mgmt.get_catalog`

- `GET /v1/catalogs/{cat}` → **200**
- wall 14 ms · 7 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

**[1]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1, 2, 0`

**[2]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1`

**[3]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1, POLARIS, 0`

**[4]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

**[5]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

**[6]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 0, 0, POLARIS`

### `mgmt.create_principal`

- `POST /v1/principals` → **201**
- wall 28 ms · 11 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records, principal_authentication_data

**[0]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

**[1]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1, 2, 0`

**[2]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1`

**[3]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1, POLARIS, 0`

**[4]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

**[5]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

**[6]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 0, POLARIS`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 6217675878453576188, 2, 0`

**[8]** `principal_authentication_data` · SELECT · no timing

```sql
SELECT principal_id, principal_client_id, main_secret_hash, secondary_secret_hash, secret_salt FROM POLARIS_SCHEMA.PRINCIPAL_AUTHENTICATION_DATA WHERE realm_id = ? AND principal_client_id = ?
```
params: `<redacted>`

**[9]** `principal_authentication_data` · INSERT · no timing

```sql
INSERT INTO POLARIS_SCHEMA.PRINCIPAL_AUTHENTICATION_DATA (principal_id, principal_client_id, main_secret_hash, secondary_secret_hash, secret_salt, realm_id) VALUES (?, ?, ?, ?, ?, ?)
```
params: `<redacted>`

**[10]** `entities` · INSERT · no timing

```sql
INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme, realm_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```
params: `6217675878453576188, 0, 0, 2, apiprofile1787214579_p, 1, 0, 1787214592719, 0, 0, 0, 1787214592719, {}, {"client_id":"69ad09789820d84c"}, 1, NULL, POLARIS`

### `mgmt.get_principal`

- `GET /v1/principals/{p}` → **200**
- wall 24 ms · 10 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

**[1]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1, 2, 0`

**[2]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1`

**[3]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1, POLARIS, 0`

**[4]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

**[5]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

**[6]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, apiprofile1787214579_p, 0, 0, 2`

**[7]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `6217675878453576188, POLARIS, 0`

**[8]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `0, POLARIS, 6217675878453576188`

**[9]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 0, POLARIS`

### `mgmt.list_principals`

- `GET /v1/principals` → **200**
- wall 37 ms · 8 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

**[1]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1, 2, 0`

**[2]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1`

**[3]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1, POLARIS, 0`

**[4]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

**[5]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

**[6]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 0, POLARIS`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND sub_type_code = ? AND realm_id = ? AND parent_id = ? AND type_code = ?
```
params: `0, 0, POLARIS, 0, 2`

### `mgmt.create_principal_role`

- `POST /v1/principal-roles` → **201**
- wall 25 ms · 8 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

**[1]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1, 2, 0`

**[2]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1`

**[3]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1, POLARIS, 0`

**[4]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

**[5]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

**[6]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 0, POLARIS`

**[7]** `entities` · INSERT · no timing

```sql
INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme, realm_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```
params: `4048965183459567800, 0, 0, 3, apiprofile1787214579_pr, 1, 0, 1787214593733, 0, 0, 0, 1787214593733, {}, {}, 1, NULL, POLARIS`

### `mgmt.get_principal_role`

- `GET /v1/principal-roles/{r}` → **200**
- wall 17 ms · 10 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

**[1]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1, 2, 0`

**[2]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1`

**[3]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1, POLARIS, 0`

**[4]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

**[5]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

**[6]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, apiprofile1787214579_pr, 0, 0, 3`

**[7]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `4048965183459567800, POLARIS, 0`

**[8]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `0, POLARIS, 4048965183459567800`

**[9]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 0, POLARIS`

### `mgmt.list_principal_roles`

- `GET /v1/principal-roles` → **200**
- wall 50 ms · 8 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

**[1]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1, 2, 0`

**[2]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1`

**[3]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1, POLARIS, 0`

**[4]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

**[5]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

**[6]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 0, POLARIS`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND sub_type_code = ? AND realm_id = ? AND parent_id = ? AND type_code = ?
```
params: `0, 0, POLARIS, 0, 3`

### `mgmt.assign_principal_role`

- `PUT /v1/principals/{p}/principal-roles` → **201**
- wall 45 ms · 12 statements · 0 object ops · entity access: MIXED (batched 25% of 8 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

**[1]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1, 2, 0`

**[2]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1`

**[3]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1, POLARIS, 0`

**[4]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

**[5]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

**[6]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 4048965183459567800, 0, 6217675878453576188, 0, 0, POLARIS`

**[7]** `grant_records` · INSERT · no timing

```sql
INSERT INTO POLARIS_SCHEMA.GRANT_RECORDS (securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code, realm_id) VALUES (?, ?, ?, ?, ?, ?)
```
params: `0, 4048965183459567800, 0, 6217675878453576188, 4, POLARIS`

**[8]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 6217675878453576188, 2, 0`

**[9]** `entities` · UPDATE · no timing

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE realm_id = ? AND entity_version = ? AND id = ? AND catalog_id = ?
```
params: `6217675878453576188, 0, 0, 2, apiprofile1787214579_p, 1, 0, 1787214592719, 0, 0, 0, 1787214592719, {}, {"client_id": "69ad09789820d84c"}, 2, NULL, POLARIS, 1, 6217675878453576188, 0`

**[10]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 4048965183459567800, 3, 0`

**[11]** `entities` · UPDATE · no timing

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE realm_id = ? AND entity_version = ? AND id = ? AND catalog_id = ?
```
params: `4048965183459567800, 0, 0, 3, apiprofile1787214579_pr, 1, 0, 1787214593733, 0, 0, 0, 1787214593733, {}, {}, 2, NULL, POLARIS, 1, 4048965183459567800, 0`

### `mgmt.create_catalog_role`

- `POST /v1/catalogs/{cat}/catalog-roles` → **201**
- wall 16 ms · 8 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

**[1]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1, 2, 0`

**[2]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1`

**[3]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1, POLARIS, 0`

**[4]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

**[5]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

**[6]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 0, 0, POLARIS`

**[7]** `entities` · INSERT · no timing

```sql
INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme, realm_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```
params: `7467285224520653546, 7985247348701050877, 7985247348701050877, 5, apiprofile1787214579_cr, 1, 0, 1787214595093, 0, 0, 0, 1787214595093, {}, {}, 1, NULL, POLARIS`

### `mgmt.list_catalog_roles`

- `GET /v1/catalogs/{cat}/catalog-roles` → **200**
- wall 14 ms · 8 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

**[1]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1, 2, 0`

**[2]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1`

**[3]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1, POLARIS, 0`

**[4]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

**[5]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

**[6]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 0, 0, POLARIS`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND sub_type_code = ? AND realm_id = ? AND parent_id = ? AND type_code = ?
```
params: `7985247348701050877, 0, POLARIS, 7985247348701050877, 5`

### `mgmt.assign_catalog_role`

- `PUT /v1/principal-roles/{r}/catalog-roles/{cat}` → **201**
- wall 36 ms · 19 statements · 0 object ops · entity access: MIXED (batched 36% of 11 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

**[1]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1, 2, 0`

**[2]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1`

**[3]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1, POLARIS, 0`

**[4]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

**[5]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

**[6]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, apiprofile1787214579_cr, 7985247348701050877, 7985247348701050877, 5`

**[7]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `7467285224520653546, POLARIS, 7985247348701050877`

**[8]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `7985247348701050877, POLARIS, 7467285224520653546`

**[9]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 0, 4048965183459567800, 0, 0, POLARIS`

**[10]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 4048965183459567800, POLARIS`

**[11]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `4048965183459567800, POLARIS, 0`

**[12]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `0, POLARIS, 4048965183459567800`

**[13]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `7985247348701050877, 6558898342658688962, POLARIS`

**[14]** `grant_records` · INSERT · no timing

```sql
INSERT INTO POLARIS_SCHEMA.GRANT_RECORDS (securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code, realm_id) VALUES (?, ?, ?, ?, ?, ?)
```
params: `7985247348701050877, 7467285224520653546, 0, 4048965183459567800, 3, POLARIS`

**[15]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 4048965183459567800, 3, 0`

**[16]** `entities` · UPDATE · no timing

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE realm_id = ? AND entity_version = ? AND id = ? AND catalog_id = ?
```
params: `4048965183459567800, 0, 0, 3, apiprofile1787214579_pr, 1, 0, 1787214593733, 0, 0, 0, 1787214593733, {}, {}, 3, NULL, POLARIS, 1, 4048965183459567800, 0`

**[17]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 7467285224520653546, 5, 7985247348701050877`

**[18]** `entities` · UPDATE · no timing

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE realm_id = ? AND entity_version = ? AND id = ? AND catalog_id = ?
```
params: `7467285224520653546, 7985247348701050877, 7985247348701050877, 5, apiprofile1787214579_cr, 1, 0, 1787214595093, 0, 0, 0, 1787214595093, {}, {}, 2, NULL, POLARIS, 1, 7467285224520653546, 7985247348701050877`

### `mgmt.grant_privilege`

- `PUT /v1/catalogs/{cat}/catalog-roles/{cr}/grants` → **201**
- wall 55 ms · 24 statements · 0 object ops · entity access: MIXED (batched 31% of 16 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

**[1]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1, 2, 0`

**[2]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1`

**[3]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1, POLARIS, 0`

**[4]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

**[5]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

**[6]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 0, 0, 7985247348701050877, 7467285224520653546, POLARIS`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `7985247348701050877, 7467285224520653546, POLARIS`

**[8]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `7467285224520653546, POLARIS, 7985247348701050877`

**[9]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `7985247348701050877, POLARIS, 7467285224520653546`

**[10]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 7985247348701050877, 7467285224520653546`

**[11]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `7467285224520653546, POLARIS, 7985247348701050877`

**[12]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

**[13]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1, 2, 0`

**[14]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1`

**[15]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1, POLARIS, 0`

**[16]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

**[17]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

**[18]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 0, 0, 7985247348701050877, 7467285224520653546, POLARIS`

**[19]** `grant_records` · INSERT · no timing

```sql
INSERT INTO POLARIS_SCHEMA.GRANT_RECORDS (securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code, realm_id) VALUES (?, ?, ?, ?, ?, ?)
```
params: `0, 7985247348701050877, 7985247348701050877, 7467285224520653546, 20, POLARIS`

**[20]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 7467285224520653546, 5, 7985247348701050877`

**[21]** `entities` · UPDATE · no timing

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE realm_id = ? AND entity_version = ? AND id = ? AND catalog_id = ?
```
params: `7467285224520653546, 7985247348701050877, 7985247348701050877, 5, apiprofile1787214579_cr, 1, 0, 1787214595093, 0, 0, 0, 1787214595093, {}, {}, 3, NULL, POLARIS, 1, 7467285224520653546, 7985247348701050877`

**[22]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 7985247348701050877, 4, 0`

**[23]** `entities` · UPDATE · no timing

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE realm_id = ? AND entity_version = ? AND id = ? AND catalog_id = ?
```
params: `7985247348701050877, 0, 0, 4, apiprofile1787214579_cat, 1, 0, 1787214579207, 0, 0, 0, 1787214579207, {"default-base-location": "s3a://data-catalog-bucket/apiprofile1787214579_cat/", "polaris.config.drop-with-purge.enabled": "true"}, {"catalogType": "INTERNAL", "storage_configuration_info": "{\"@type\":\"AwsStorageConfigurationInfo\",\"allowedLocations\":[\"s3a://data-catalog-bucket/apiprofile1787214579_cat/\",\"s3a://data-catalog-bucket/\"],\"endpoint\":\"http://192.168.139.2:9000\",\"endpointInternal\":\"http://192.168.139.2:9000\",\"pathStyleAccess\":true,\"storageType\":\"S3\",\"fileIoImplClassName\":\"org.apache.iceberg.aws.s3.S3FileIO\"}"}, 5, NULL, POLARIS, 1, 7985247348701050877, 0`

### `mgmt.list_grants`

- `GET /v1/catalogs/{cat}/catalog-roles/{cr}/grants` → **200**
- wall 16 ms · 15 statements · 0 object ops · entity access: MIXED (batched 50% of 10 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

**[1]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1, 2, 0`

**[2]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1`

**[3]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1, POLARIS, 0`

**[4]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

**[5]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

**[6]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 0, 0, 7985247348701050877, 7467285224520653546, POLARIS`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 7985247348701050877, POLARIS`

**[8]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `0, POLARIS, 7985247348701050877`

**[9]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `7985247348701050877, 7467285224520653546, POLARIS`

**[10]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `7467285224520653546, POLARIS, 7985247348701050877`

**[11]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `7985247348701050877, POLARIS, 7467285224520653546`

**[12]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 7985247348701050877, 7467285224520653546`

**[13]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `7467285224520653546, POLARIS, 7985247348701050877`

**[14]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 7985247348701050877, POLARIS`

### `mgmt.list_principals_for_principal_role`

- `GET /v1/principal-roles/{r}/principals` → **200**
- wall 13 ms · 13 statements · 0 object ops · entity access: MIXED (batched 44% of 9 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

**[1]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1, 2, 0`

**[2]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1`

**[3]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1, POLARIS, 0`

**[4]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

**[5]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

**[6]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 4048965183459567800, 0, 0, POLARIS`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 4048965183459567800, POLARIS`

**[8]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `4048965183459567800, POLARIS, 0`

**[9]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `0, POLARIS, 4048965183459567800`

**[10]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 4048965183459567800`

**[11]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `0, POLARIS, 4048965183459567800`

**[12]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 6217675878453576188, POLARIS`

### `mgmt.reset_principal_credentials`

- `POST /v1/principals/{p}/reset` → **200**
- wall 26 ms · 14 statements · 0 object ops · entity access: MIXED (batched 38% of 8 reads)
- tables: entities, grant_records, principal_authentication_data

**[0]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

**[1]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1, 2, 0`

**[2]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1`

**[3]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1, POLARIS, 0`

**[4]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

**[5]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

**[6]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 6217675878453576188, 0, 0, POLARIS`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 6217675878453576188, POLARIS`

**[8]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `6217675878453576188, POLARIS, 0`

**[9]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `0, POLARIS, 6217675878453576188`

**[10]** `principal_authentication_data` · SELECT · no timing

```sql
SELECT principal_id, principal_client_id, main_secret_hash, secondary_secret_hash, secret_salt FROM POLARIS_SCHEMA.PRINCIPAL_AUTHENTICATION_DATA WHERE realm_id = ? AND principal_client_id = ?
```
params: `<redacted>`

**[11]** `principal_authentication_data` · DELETE · no timing

```sql
DELETE FROM POLARIS_SCHEMA.PRINCIPAL_AUTHENTICATION_DATA WHERE realm_id = ? AND principal_id = ? AND principal_client_id = ?
```
params: `<redacted>`

**[12]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 6217675878453576188, 2, 0`

**[13]** `principal_authentication_data` · INSERT · no timing

```sql
INSERT INTO POLARIS_SCHEMA.PRINCIPAL_AUTHENTICATION_DATA (principal_id, principal_client_id, main_secret_hash, secondary_secret_hash, secret_salt, realm_id) VALUES (?, ?, ?, ?, ?, ?)
```
params: `<redacted>`

### `mgmt.delete_catalog_role`

- `DELETE /v1/catalogs/{cat}/catalog-roles/{cr}` → **204**
- wall 35 ms · 16 statements · 0 object ops · entity access: MIXED (batched 38% of 8 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

**[1]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1, 2, 0`

**[2]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1`

**[3]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1, POLARIS, 0`

**[4]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

**[5]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

**[6]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 7985247348701050877, 7985247348701050877, 6558898342658688962, 0, 0, 7985247348701050877, 7467285224520653546, POLARIS`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 7467285224520653546, 5, 7985247348701050877`

**[8]** `entities` · DELETE · no timing

```sql
DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 7985247348701050877, 7467285224520653546`

**[9]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `7467285224520653546, POLARIS, 7985247348701050877`

**[10]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `7985247348701050877, POLARIS, 7467285224520653546`

**[11]** `grant_records` · DELETE · no timing

```sql
DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (
    (grantee_id = ? AND grantee_catalog_id = ?) OR
    (securable_id = ? AND securable_catalog_id = ?)
) AND realm_id = ?
```
params: `7467285224520653546, 7985247348701050877, 7467285224520653546, 7985247348701050877, POLARIS`

**[12]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 4048965183459567800, 0, 7985247348701050877, POLARIS`

**[13]** `entities` · UPDATE · no timing

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE realm_id = ? AND entity_version = ? AND id = ? AND catalog_id = ?
```
params: `4048965183459567800, 0, 0, 3, apiprofile1787214579_pr, 1, 0, 1787214593733, 0, 0, 0, 1787214593733, {}, {}, 4, NULL, POLARIS, 1, 4048965183459567800, 0`

**[14]** `entities` · UPDATE · no timing

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE realm_id = ? AND entity_version = ? AND id = ? AND catalog_id = ?
```
params: `7985247348701050877, 0, 0, 4, apiprofile1787214579_cat, 1, 0, 1787214579207, 0, 0, 0, 1787214579207, {"default-base-location": "s3a://data-catalog-bucket/apiprofile1787214579_cat/", "polaris.config.drop-with-purge.enabled": "true"}, {"catalogType": "INTERNAL", "storage_configuration_info": "{\"@type\":\"AwsStorageConfigurationInfo\",\"allowedLocations\":[\"s3a://data-catalog-bucket/apiprofile1787214579_cat/\",\"s3a://data-catalog-bucket/\"],\"endpoint\":\"http://192.168.139.2:9000\",\"endpointInternal\":\"http://192.168.139.2:9000\",\"pathStyleAccess\":true,\"storageType\":\"S3\",\"fileIoImplClassName\":\"org.apache.iceberg.aws.s3.S3FileIO\"}"}, 6, NULL, POLARIS, 1, 7985247348701050877, 0`

**[15]** `entities` · INSERT · no timing

```sql
INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme, realm_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```
params: `1112109472076797526, 0, 0, 8, entityCleanup_7467285224520653546, 1, 0, 1787214597425, 0, 0, 0, 1787214597425, {"taskType":"1","data":"{\"catalogId\":7985247348701050877,\"id\":7467285224520653546,\"parentId\":7985247348701050877,\"typeCode\":5,\"name\":\"apiprofile1787214579_cr\",\"entityVersion\":1,\"subTypeCode\":0,\"createTimestamp\":1787214595093,\"dropTimestamp\":0,\"purgeTimestamp\":0,\"toPurgeTimestamp\":0,\"lastUpdateTimestamp\":1787214595093,\"properties\":\"{}\",\"internalProperties\":\"{}\",\"grantRecordsVersion\":3}"}, {}, 1, NULL, POLARIS`

### `mgmt.delete_principal_role`

- `DELETE /v1/principal-roles/{r}` → **204**
- wall 29 ms · 18 statements · 0 object ops · entity access: MIXED (batched 44% of 9 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

**[1]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1, 2, 0`

**[2]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1`

**[3]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1, POLARIS, 0`

**[4]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

**[5]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

**[6]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 4048965183459567800, 0, 0, POLARIS`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 4048965183459567800, POLARIS`

**[8]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `4048965183459567800, POLARIS, 0`

**[9]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `0, POLARIS, 4048965183459567800`

**[10]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 4048965183459567800, 3, 0`

**[11]** `entities` · DELETE · no timing

```sql
DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 4048965183459567800`

**[12]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `4048965183459567800, POLARIS, 0`

**[13]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `0, POLARIS, 4048965183459567800`

**[14]** `grant_records` · DELETE · no timing

```sql
DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (
    (grantee_id = ? AND grantee_catalog_id = ?) OR
    (securable_id = ? AND securable_catalog_id = ?)
) AND realm_id = ?
```
params: `4048965183459567800, 0, 4048965183459567800, 0, POLARIS`

**[15]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 6217675878453576188, POLARIS`

**[16]** `entities` · UPDATE · no timing

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE realm_id = ? AND entity_version = ? AND id = ? AND catalog_id = ?
```
params: `6217675878453576188, 0, 0, 2, apiprofile1787214579_p, 1, 0, 1787214592719, 0, 0, 0, 1787214592719, {}, {"client_id": "69ad09789820d84c"}, 3, NULL, POLARIS, 1, 6217675878453576188, 0`

**[17]** `entities` · INSERT · no timing

```sql
INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme, realm_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```
params: `5538300155321123739, 0, 0, 8, entityCleanup_4048965183459567800, 1, 0, 1787214597768, 0, 0, 0, 1787214597768, {"taskType":"1","data":"{\"catalogId\":0,\"id\":4048965183459567800,\"parentId\":0,\"typeCode\":3,\"name\":\"apiprofile1787214579_pr\",\"entityVersion\":1,\"subTypeCode\":0,\"createTimestamp\":1787214593733,\"dropTimestamp\":0,\"purgeTimestamp\":0,\"toPurgeTimestamp\":0,\"lastUpdateTimestamp\":1787214593733,\"properties\":\"{}\",\"internalProperties\":\"{}\",\"grantRecordsVersion\":4}"}, {}, 1, NULL, POLARIS`

### `mgmt.delete_principal`

- `DELETE /v1/principals/{p}` → **204**
- wall 28 ms · 16 statements · 0 object ops · entity access: MIXED (batched 38% of 8 reads)
- tables: entities, grant_records, principal_authentication_data

**[0]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

**[1]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1, 2, 0`

**[2]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1`

**[3]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1, POLARIS, 0`

**[4]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

**[5]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

**[6]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 6217675878453576188, 0, 0, POLARIS`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 6217675878453576188, POLARIS`

**[8]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `6217675878453576188, POLARIS, 0`

**[9]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `0, POLARIS, 6217675878453576188`

**[10]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 6217675878453576188, 2, 0`

**[11]** `entities` · DELETE · no timing

```sql
DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 6217675878453576188`

**[12]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `6217675878453576188, POLARIS, 0`

**[13]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `0, POLARIS, 6217675878453576188`

**[14]** `grant_records` · DELETE · no timing

```sql
DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (
    (grantee_id = ? AND grantee_catalog_id = ?) OR
    (securable_id = ? AND securable_catalog_id = ?)
) AND realm_id = ?
```
params: `6217675878453576188, 0, 6217675878453576188, 0, POLARIS`

**[15]** `principal_authentication_data` · DELETE · no timing

```sql
DELETE FROM POLARIS_SCHEMA.PRINCIPAL_AUTHENTICATION_DATA WHERE realm_id = ? AND principal_id = ? AND principal_client_id = ?
```
params: `<redacted>`
