# API → SQL → MinIO Access Matrix

Generated 2026-08-20 17:16 from a live local run — Polaris 1.3.0, realm POLARIS.
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
| `iceberg.load_table` |  | `/data-catalog-bucket/apiprofile1787213725_cat/probe_ns/probe_tbl/metadata/00000-a20f1c8c-3e5b-4a85-b2e9-6876b03ec128.metadata.json` | 1 |
| `iceberg.load_table[snapshots=refs]` |  | `/data-catalog-bucket/apiprofile1787213725_cat/probe_ns/probe_tbl/metadata/00000-a20f1c8c-3e5b-4a85-b2e9-6876b03ec128.metadata.json` | 1 |
| `iceberg.head_table` |  | `/data-catalog-bucket/apiprofile1787213725_cat/probe_ns/probe_tbl/metadata/00000-a20f1c8c-3e5b-4a85-b2e9-6876b03ec128.metadata.json` | 1 |
| `iceberg.create_table` |  | `/data-catalog-bucket/apiprofile1787213725_cat/probe_ns/probe_tbl2/metadata/00000-f6c5c79f-6174-498a-9fda-04a9fd511002.metadata.json` | 1 |
| `iceberg.commit_table` |  | `/data-catalog-bucket/apiprofile1787213725_cat/probe_ns/probe_tbl/metadata/00000-a20f1c8c-3e5b-4a85-b2e9-6876b03ec128.metadata.json` | 1 |
| `iceberg.commit_table` |  | `/data-catalog-bucket/apiprofile1787213725_cat/probe_ns/probe_tbl/metadata/00001-0927ea1d-5209-408b-a422-7b832ea1fba3.metadata.json` | 1 |
| `iceberg.create_view` |  | `/data-catalog-bucket/apiprofile1787213725_cat/probe_ns/probe_view/metadata/00000-281ff723-cdf7-4f4a-b9d8-eb28c228b95a.gz.metadata.json` | 2 |
| `iceberg.load_view` |  | `/data-catalog-bucket/apiprofile1787213725_cat/probe_ns/probe_view/metadata/00000-281ff723-cdf7-4f4a-b9d8-eb28c228b95a.gz.metadata.json` | 2 |
| `iceberg.head_view` |  | `/data-catalog-bucket/apiprofile1787213725_cat/probe_ns/probe_view/metadata/00000-281ff723-cdf7-4f4a-b9d8-eb28c228b95a.gz.metadata.json` | 2 |

## Per-API detail

### `preflight`

- `GET /probe` → **None**
- wall 87 ms · 8 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
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
- wall 9 ms · 7 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
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
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, POLARIS`

### `iceberg.list_namespaces`

- `GET /v1/{cat}/namespaces` → **200**
- wall 11 ms · 8 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
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
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 0, 0, POLARIS`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND sub_type_code = ? AND realm_id = ? AND parent_id = ? AND type_code = ?
```
params: `2798065426209788516, 0, POLARIS, 2798065426209788516, 6`

### `iceberg.load_namespace`

- `GET /v1/{cat}/namespaces/{ns}` → **200**
- wall 11 ms · 7 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
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
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 0, 0, 2798065426209788516, 881064999555903699, POLARIS`

### `iceberg.head_namespace`

- `HEAD /v1/{cat}/namespaces/{ns}` → **204**
- wall 16 ms · 7 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
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
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 0, 0, 2798065426209788516, 881064999555903699, POLARIS`

### `iceberg.update_namespace_properties`

- `POST /v1/{cat}/namespaces/{ns}/properties` → **200**
- wall 38 ms · 10 statements · 0 object ops · entity access: MIXED (batched 43% of 7 reads)
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
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 0, 0, 2798065426209788516, 881064999555903699, POLARIS`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND realm_id = ? AND type_code = ? AND catalog_id = ?
```
params: `2798065426209788516, POLARIS, 6, 2798065426209788516`

**[8]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 0, 0, 2798065426209788516, 881064999555903699, 2798065426209788516, 3597830810017700629, POLARIS`

**[9]** `entities` · UPDATE · no timing

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE realm_id = ? AND entity_version = ? AND id = ? AND catalog_id = ?
```
params: `881064999555903699, 2798065426209788516, 2798065426209788516, 6, probe_ns, 2, 0, 1787213726271, 0, 0, 0, 1787213730015, {"location":"s3a://data-catalog-bucket/apiprofile1787213725_cat/probe_ns/","k":"v"}, {}, 1, //data-catalog-bucket/apiprofile1787213725_cat/probe_ns/, POLARIS, 1, 881064999555903699, 2798065426209788516`

### `iceberg.create_namespace`

- `POST /v1/{cat}/namespaces` → **200**
- wall 46 ms · 16 statements · 0 object ops · entity access: MIXED (batched 42% of 12 reads)
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
params: `POLARIS, probe_ns_tmp, 2798065426209788516, 2798065426209788516, 6`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 0, 0, POLARIS`

**[8]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND realm_id = ? AND type_code = ? AND catalog_id = ?
```
params: `2798065426209788516, POLARIS, 6, 2798065426209788516`

**[9]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 0, 0, 2798065426209788516, 881064999555903699, 2798065426209788516, 3597830810017700629, POLARIS`

**[10]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `2798065426209788516, 881064999555903699, POLARIS`

**[11]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 881064999555903699, 6, 2798065426209788516`

**[12]** `entities` · INSERT · no timing

```sql
INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme, realm_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```
params: `3588032628894147540, 2798065426209788516, 2798065426209788516, 6, probe_ns_tmp, 1, 0, 1787213730359, 0, 0, 0, 1787213730359, {"location":"s3a://data-catalog-bucket/apiprofile1787213725_cat/probe_ns_tmp/"}, {}, 1, //data-catalog-bucket/apiprofile1787213725_cat/probe_ns_tmp/, POLARIS`

**[13]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, probe_ns_tmp, 2798065426209788516, 2798065426209788516, 6`

**[14]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `2798065426209788516, POLARIS, 3588032628894147540`

**[15]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, POLARIS`

### `iceberg.drop_namespace`

- `DELETE /v1/{cat}/namespaces/{ns}` → **204**
- wall 29 ms · 15 statements · 0 object ops · entity access: MIXED (batched 25% of 8 reads)
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
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 0, 0, 2798065426209788516, 3588032628894147540, POLARIS`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3588032628894147540, 6, 2798065426209788516`

**[8]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND realm_id = ?
```
params: `2798065426209788516, 3588032628894147540, POLARIS`

**[9]** `entities` · DELETE · no timing

```sql
DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 2798065426209788516, 3588032628894147540`

**[10]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `2798065426209788516, POLARIS, 3588032628894147540`

**[11]** `grant_records` · DELETE · no timing

```sql
DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (
    (grantee_id = ? AND grantee_catalog_id = ?) OR
    (securable_id = ? AND securable_catalog_id = ?)
) AND realm_id = ?
```
params: `3588032628894147540, 2798065426209788516, 3588032628894147540, 2798065426209788516, POLARIS`

**[12]** `policy_mapping_record` · SELECT · no timing

```sql
SELECT target_catalog_id, target_id, policy_type_code, policy_catalog_id, policy_id, parameters FROM POLARIS_SCHEMA.POLICY_MAPPING_RECORD WHERE realm_id = ? AND target_id = ? AND target_catalog_id = ?
```
params: `POLARIS, 3588032628894147540, 2798065426209788516`

**[13]** `policy_mapping_record` · DELETE · no timing

```sql
DELETE FROM POLARIS_SCHEMA.POLICY_MAPPING_RECORD WHERE target_catalog_id = ? AND target_id = ? AND realm_id = ?
```
params: `2798065426209788516, 3588032628894147540, POLARIS`

**[14]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

### `iceberg.list_tables`

- `GET /v1/{cat}/namespaces/{ns}/tables` → **200**
- wall 20 ms · 8 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
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
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 0, 0, 2798065426209788516, 881064999555903699, POLARIS`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND sub_type_code = ? AND realm_id = ? AND parent_id = ? AND type_code = ?
```
params: `2798065426209788516, 2, POLARIS, 881064999555903699, 7`

### `iceberg.load_table`

- `GET /v1/{cat}/namespaces/{ns}/tables/{tbl}` → **200**
- wall 68 ms · 10 statements · 1 object ops · entity access: MIXED (batched 33% of 9 reads)
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
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 0, 0, 2798065426209788516, 881064999555903699, 2798065426209788516, 7993667961783143670, POLARIS`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 2798065426209788516, 881064999555903699, 2798065426209788516, 7993667961783143670, POLARIS`

**[8]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2798065426209788516, 4, 0`

**[9]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2798065426209788516, 4, 0`

| # | Method | Path | ms |
|---|---|---|---|
| 0 |  | `/data-catalog-bucket/apiprofile1787213725_cat/probe_ns/probe_tbl/metadata/00000-a20f1c8c-3e5b-4a85-b2e9-6876b03ec128.metadata.json` | 2.27 |

### `iceberg.load_table[snapshots=refs]`

- `GET /v1/{cat}/.../tables/{tbl}?snapshots=refs` → **200**
- wall 43 ms · 8 statements · 1 object ops · entity access: MIXED (batched 43% of 7 reads)
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
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 0, 0, 2798065426209788516, 881064999555903699, 2798065426209788516, 7993667961783143670, POLARIS`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 2798065426209788516, 881064999555903699, 2798065426209788516, 7993667961783143670, POLARIS`

| # | Method | Path | ms |
|---|---|---|---|
| 0 |  | `/data-catalog-bucket/apiprofile1787213725_cat/probe_ns/probe_tbl/metadata/00000-a20f1c8c-3e5b-4a85-b2e9-6876b03ec128.metadata.json` | 2.06 |

### `iceberg.head_table`

- `HEAD /v1/{cat}/namespaces/{ns}/tables/{tbl}` → **204**
- wall 24 ms · 8 statements · 1 object ops · entity access: MIXED (batched 43% of 7 reads)
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
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 0, 0, 2798065426209788516, 881064999555903699, 2798065426209788516, 7993667961783143670, POLARIS`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 2798065426209788516, 881064999555903699, 2798065426209788516, 7993667961783143670, POLARIS`

| # | Method | Path | ms |
|---|---|---|---|
| 0 |  | `/data-catalog-bucket/apiprofile1787213725_cat/probe_ns/probe_tbl/metadata/00000-a20f1c8c-3e5b-4a85-b2e9-6876b03ec128.metadata.json` | 1.86 |

### `iceberg.create_table`

- `POST /v1/{cat}/namespaces/{ns}/tables` → **200**
- wall 80 ms · 24 statements · 1 object ops · entity access: MIXED (batched 42% of 19 reads)
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
params: `POLARIS, probe_tbl2, 2798065426209788516, 881064999555903699, 7`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 0, 0, 2798065426209788516, 881064999555903699, POLARIS`

**[8]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, probe_tbl2, 2798065426209788516, 881064999555903699, 7`

**[9]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 2798065426209788516, 881064999555903699, POLARIS`

**[10]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, probe_tbl2, 2798065426209788516, 881064999555903699, 7`

**[11]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 2798065426209788516, 881064999555903699, POLARIS`

**[12]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, probe_tbl2, 2798065426209788516, 881064999555903699, 7`

**[13]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 2798065426209788516, 881064999555903699, POLARIS`

**[14]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2798065426209788516, 4, 0`

**[15]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND realm_id = ? AND type_code = ? AND catalog_id = ?
```
params: `881064999555903699, POLARIS, 6, 2798065426209788516`

**[16]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND realm_id = ? AND type_code = ? AND catalog_id = ?
```
params: `881064999555903699, POLARIS, 7, 2798065426209788516`

**[17]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 0, 0, 2798065426209788516, 881064999555903699, 2798065426209788516, 7993667961783143670, POLARIS`

**[18]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, probe_tbl2, 2798065426209788516, 881064999555903699, 7`

**[19]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 2798065426209788516, 881064999555903699, POLARIS`

**[20]** `entities` · INSERT · no timing

```sql
INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme, realm_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```
params: `9094655437436980233, 2798065426209788516, 881064999555903699, 7, probe_tbl2, 1, 2, 1787213734001, 0, 0, 0, 1787213734001, {"location":"s3a://data-catalog-bucket/apiprofile1787213725_cat/probe_ns/probe_tbl2/"}, {"last-sequence-number":"0","last-updated-ms":"1787213733958","next-row-id":"0","format-version":"2","metadata-location":"s3a://data-catalog-bucket/apiprofile1787213725_cat/probe_ns/probe_tbl2/metadata/00000-f6c5c79f-6174-498a-9fda-04a9fd511002.metadata.json","table-uuid":"512d3b3f-48ff-49e7-a40f-107908cb8583","default-sort-order-id":"0","last-partition-id":"999","parent-namespace":"probe_ns","current-schema-id":"0","location":"s3a://data-catalog-bucket/apiprofile1787213725_cat/probe_ns/probe_tbl2","last-column-id":"2","default-spec-id":"0"}, 1, //data-catalog-bucket/apiprofile1787213725_cat/probe_ns/probe_tbl2/, POLARIS`

**[21]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, probe_tbl2, 2798065426209788516, 881064999555903699, 7`

**[22]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `2798065426209788516, POLARIS, 9094655437436980233`

**[23]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 2798065426209788516, 881064999555903699, POLARIS`

| # | Method | Path | ms |
|---|---|---|---|
| 0 |  | `/data-catalog-bucket/apiprofile1787213725_cat/probe_ns/probe_tbl2/metadata/00000-f6c5c79f-6174-498a-9fda-04a9fd511002.metadata.json` | 7.55 |

### `iceberg.stage_create_table`

- `POST /v1/{cat}/namespaces/{ns}/tables[stage]` → **200**
- wall 43 ms · 13 statements · 0 object ops · entity access: MIXED (batched 33% of 12 reads)
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
params: `POLARIS, probe_staged, 2798065426209788516, 881064999555903699, 7`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 0, 0, 2798065426209788516, 881064999555903699, POLARIS`

**[8]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, probe_staged, 2798065426209788516, 881064999555903699, 7`

**[9]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 2798065426209788516, 881064999555903699, POLARIS`

**[10]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, probe_staged, 2798065426209788516, 881064999555903699, 7`

**[11]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 2798065426209788516, 881064999555903699, POLARIS`

**[12]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2798065426209788516, 4, 0`

### `iceberg.commit_table`

- `POST /v1/{cat}/namespaces/{ns}/tables/{tbl}` → **200**
- wall 71 ms · 14 statements · 2 object ops · entity access: MIXED (batched 58% of 12 reads)
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
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 0, 0, 2798065426209788516, 881064999555903699, 2798065426209788516, 7993667961783143670, POLARIS`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 2798065426209788516, 881064999555903699, 2798065426209788516, 7993667961783143670, POLARIS`

**[8]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 2798065426209788516, 881064999555903699, 2798065426209788516, 7993667961783143670, POLARIS`

**[9]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 2798065426209788516, 881064999555903699, 2798065426209788516, 7993667961783143670, POLARIS`

**[10]** `entities` · UPDATE · no timing

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE realm_id = ? AND entity_version = ? AND id = ? AND catalog_id = ?
```
params: `7993667961783143670, 2798065426209788516, 881064999555903699, 7, probe_tbl, 2, 2, 1787213726367, 0, 0, 0, 1787213734734, {"location":"s3a://data-catalog-bucket/apiprofile1787213725_cat/probe_ns/probe_tbl/"}, {"last-sequence-number":"0","last-updated-ms":"1787213734713","next-row-id":"0","format-version":"2","metadata-location":"s3a://data-catalog-bucket/apiprofile1787213725_cat/probe_ns/probe_tbl/metadata/00001-0927ea1d-5209-408b-a422-7b832ea1fba3.metadata.json","table-uuid":"50281f4a-196b-45af-a2b5-d44af4d37d5d","default-sort-order-id":"0","last-partition-id":"999","parent-namespace":"probe_ns","current-schema-id":"0","location":"s3a://data-catalog-bucket/apiprofile1787213725_cat/probe_ns/probe_tbl","last-column-id":"2","default-spec-id":"0"}, 1, //data-catalog-bucket/apiprofile1787213725_cat/probe_ns/probe_tbl/, POLARIS, 1, 7993667961783143670, 2798065426209788516`

**[11]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 2798065426209788516, 881064999555903699, 2798065426209788516, 7993667961783143670, POLARIS`

**[12]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `2798065426209788516, 7993667961783143670, POLARIS`

**[13]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 7993667961783143670, 7, 2798065426209788516`

| # | Method | Path | ms |
|---|---|---|---|
| 0 |  | `/data-catalog-bucket/apiprofile1787213725_cat/probe_ns/probe_tbl/metadata/00000-a20f1c8c-3e5b-4a85-b2e9-6876b03ec128.metadata.json` | 2.56 |
| 1 |  | `/data-catalog-bucket/apiprofile1787213725_cat/probe_ns/probe_tbl/metadata/00001-0927ea1d-5209-408b-a422-7b832ea1fba3.metadata.json` | 7.24 |

### `iceberg.rename_table`

- `POST /v1/{cat}/tables/rename` → **200**
- wall 33 ms · 11 statements · 0 object ops · entity access: MIXED (batched 22% of 9 reads)
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
params: `POLARIS, probe_tbl3, 2798065426209788516, 881064999555903699, 7`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 0, 0, 2798065426209788516, 881064999555903699, 2798065426209788516, 9094655437436980233, POLARIS`

**[8]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9094655437436980233, 7, 2798065426209788516`

**[9]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, probe_tbl3, 2798065426209788516, 881064999555903699, 7`

**[10]** `entities` · UPDATE · no timing

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE realm_id = ? AND entity_version = ? AND id = ? AND catalog_id = ?
```
params: `9094655437436980233, 2798065426209788516, 881064999555903699, 7, probe_tbl3, 2, 2, 1787213734001, 0, 0, 0, 1787213735075, {"location":"s3a://data-catalog-bucket/apiprofile1787213725_cat/probe_ns/probe_tbl2/"}, {"last-updated-ms":"1787213733958","last-sequence-number":"0","next-row-id":"0","format-version":"2","metadata-location":"s3a://data-catalog-bucket/apiprofile1787213725_cat/probe_ns/probe_tbl2/metadata/00000-f6c5c79f-6174-498a-9fda-04a9fd511002.metadata.json","table-uuid":"512d3b3f-48ff-49e7-a40f-107908cb8583","default-sort-order-id":"0","last-partition-id":"999","parent-namespace":"probe_ns","current-schema-id":"0","location":"s3a://data-catalog-bucket/apiprofile1787213725_cat/probe_ns/probe_tbl2","last-column-id":"2","default-spec-id":"0"}, 1, //data-catalog-bucket/apiprofile1787213725_cat/probe_ns/probe_tbl2/, POLARIS, 1, 9094655437436980233, 2798065426209788516`

### `iceberg.report_metrics`

- `POST /v1/{cat}/.../tables/{tbl}/metrics` → **204**
- wall 10 ms · 6 statements · 0 object ops · entity access: MIXED (batched 20% of 5 reads)
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
- wall 25 ms · 8 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
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
params: `POLARIS, does_not_exist, 2798065426209788516, 881064999555903699, 7`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 0, 0, 2798065426209788516, 881064999555903699, POLARIS`

### `iceberg.drop_table`

- `DELETE /v1/{cat}/namespaces/{ns}/tables/{tbl}` → **204**
- wall 43 ms · 15 statements · 0 object ops · entity access: MIXED (batched 25% of 8 reads)
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
params: `POLARIS, probe_tbl3, 2798065426209788516, 881064999555903699, 7`

**[7]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `2798065426209788516, POLARIS, 9094655437436980233`

**[8]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 0, 0, 2798065426209788516, 881064999555903699, POLARIS`

**[9]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9094655437436980233, 7, 2798065426209788516`

**[10]** `entities` · DELETE · no timing

```sql
DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 2798065426209788516, 9094655437436980233`

**[11]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `2798065426209788516, POLARIS, 9094655437436980233`

**[12]** `grant_records` · DELETE · no timing

```sql
DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (
    (grantee_id = ? AND grantee_catalog_id = ?) OR
    (securable_id = ? AND securable_catalog_id = ?)
) AND realm_id = ?
```
params: `9094655437436980233, 2798065426209788516, 9094655437436980233, 2798065426209788516, POLARIS`

**[13]** `policy_mapping_record` · SELECT · no timing

```sql
SELECT target_catalog_id, target_id, policy_type_code, policy_catalog_id, policy_id, parameters FROM POLARIS_SCHEMA.POLICY_MAPPING_RECORD WHERE realm_id = ? AND target_id = ? AND target_catalog_id = ?
```
params: `POLARIS, 9094655437436980233, 2798065426209788516`

**[14]** `policy_mapping_record` · DELETE · no timing

```sql
DELETE FROM POLARIS_SCHEMA.POLICY_MAPPING_RECORD WHERE target_catalog_id = ? AND target_id = ? AND realm_id = ?
```
params: `2798065426209788516, 9094655437436980233, POLARIS`

### `iceberg.create_view`

- `POST /v1/{cat}/namespaces/{ns}/views` → **200**
- wall 76 ms · 23 statements · 2 object ops · entity access: MIXED (batched 39% of 18 reads)
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
params: `POLARIS, probe_view, 2798065426209788516, 881064999555903699, 7`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 0, 0, 2798065426209788516, 881064999555903699, POLARIS`

**[8]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, probe_view, 2798065426209788516, 881064999555903699, 7`

**[9]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 2798065426209788516, 881064999555903699, POLARIS`

**[10]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, probe_view, 2798065426209788516, 881064999555903699, 7`

**[11]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 2798065426209788516, 881064999555903699, POLARIS`

**[12]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, probe_view, 2798065426209788516, 881064999555903699, 7`

**[13]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 2798065426209788516, 881064999555903699, POLARIS`

**[14]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND realm_id = ? AND type_code = ? AND catalog_id = ?
```
params: `881064999555903699, POLARIS, 6, 2798065426209788516`

**[15]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND realm_id = ? AND type_code = ? AND catalog_id = ?
```
params: `881064999555903699, POLARIS, 7, 2798065426209788516`

**[16]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 0, 0, 2798065426209788516, 881064999555903699, 2798065426209788516, 7993667961783143670, POLARIS`

**[17]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2798065426209788516, 4, 0`

**[18]** `entities` · INSERT · no timing

```sql
INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme, realm_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```
params: `3486438586481650344, 2798065426209788516, 881064999555903699, 7, probe_view, 1, 3, 1787213737779, 0, 0, 0, 1787213737779, {}, {"metadata-location":"s3a://data-catalog-bucket/apiprofile1787213725_cat/probe_ns/probe_view/metadata/00000-281ff723-cdf7-4f4a-b9d8-eb28c228b95a.gz.metadata.json","parent-namespace":"probe_ns"}, 1, NULL, POLARIS`

**[19]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, probe_view, 2798065426209788516, 881064999555903699, 7`

**[20]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `2798065426209788516, POLARIS, 3486438586481650344`

**[21]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 2798065426209788516, 881064999555903699, POLARIS`

**[22]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2798065426209788516, 4, 0`

| # | Method | Path | ms |
|---|---|---|---|
| 0 |  | `/data-catalog-bucket/apiprofile1787213725_cat/probe_ns/probe_view/metadata/00000-281ff723-cdf7-4f4a-b9d8-eb28c228b95a.gz.metadata.json` | 3.38 |
| 1 |  | `/data-catalog-bucket/apiprofile1787213725_cat/probe_ns/probe_view/metadata/00000-281ff723-cdf7-4f4a-b9d8-eb28c228b95a.gz.metadata.json` | 1.09 |

### `iceberg.list_views`

- `GET /v1/{cat}/namespaces/{ns}/views` → **200**
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
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 0, 0, 2798065426209788516, 881064999555903699, POLARIS`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND sub_type_code = ? AND realm_id = ? AND parent_id = ? AND type_code = ?
```
params: `2798065426209788516, 3, POLARIS, 881064999555903699, 7`

### `iceberg.load_view`

- `GET /v1/{cat}/namespaces/{ns}/views/{view}` → **200**
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
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 0, 0, 2798065426209788516, 881064999555903699, 2798065426209788516, 3486438586481650344, POLARIS`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 2798065426209788516, 881064999555903699, 2798065426209788516, 3486438586481650344, POLARIS`

**[8]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 2798065426209788516, 881064999555903699, 2798065426209788516, 3486438586481650344, POLARIS`

| # | Method | Path | ms |
|---|---|---|---|
| 0 |  | `/data-catalog-bucket/apiprofile1787213725_cat/probe_ns/probe_view/metadata/00000-281ff723-cdf7-4f4a-b9d8-eb28c228b95a.gz.metadata.json` | 1.35 |
| 1 |  | `/data-catalog-bucket/apiprofile1787213725_cat/probe_ns/probe_view/metadata/00000-281ff723-cdf7-4f4a-b9d8-eb28c228b95a.gz.metadata.json` | 1.32 |

### `iceberg.head_view`

- `HEAD /v1/{cat}/namespaces/{ns}/views/{view}` → **204**
- wall 32 ms · 10 statements · 2 object ops · entity access: MIXED (batched 44% of 9 reads)
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
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 0, 0, 2798065426209788516, 881064999555903699, 2798065426209788516, 3486438586481650344, POLARIS`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 2798065426209788516, 881064999555903699, 2798065426209788516, 3486438586481650344, POLARIS`

**[8]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 2798065426209788516, 881064999555903699, 2798065426209788516, 3486438586481650344, POLARIS`

**[9]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, root, 0, 0, 2`

| # | Method | Path | ms |
|---|---|---|---|
| 0 |  | `/data-catalog-bucket/apiprofile1787213725_cat/probe_ns/probe_view/metadata/00000-281ff723-cdf7-4f4a-b9d8-eb28c228b95a.gz.metadata.json` | 1.76 |
| 1 |  | `/data-catalog-bucket/apiprofile1787213725_cat/probe_ns/probe_view/metadata/00000-281ff723-cdf7-4f4a-b9d8-eb28c228b95a.gz.metadata.json` | 1.51 |

### `iceberg.rename_view`

- `POST /v1/{cat}/views/rename` → **204**
- wall 17 ms · 11 statements · 0 object ops · entity access: MIXED (batched 22% of 9 reads)
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
params: `POLARIS, probe_view2, 2798065426209788516, 881064999555903699, 7`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 0, 0, 2798065426209788516, 881064999555903699, 2798065426209788516, 3486438586481650344, POLARIS`

**[8]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3486438586481650344, 7, 2798065426209788516`

**[9]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```
params: `POLARIS, probe_view2, 2798065426209788516, 881064999555903699, 7`

**[10]** `entities` · UPDATE · no timing

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE realm_id = ? AND entity_version = ? AND id = ? AND catalog_id = ?
```
params: `3486438586481650344, 2798065426209788516, 881064999555903699, 7, probe_view2, 2, 3, 1787213737779, 0, 0, 0, 1787213739132, {}, {"metadata-location":"s3a://data-catalog-bucket/apiprofile1787213725_cat/probe_ns/probe_view/metadata/00000-281ff723-cdf7-4f4a-b9d8-eb28c228b95a.gz.metadata.json","parent-namespace":"probe_ns"}, 1, NULL, POLARIS, 1, 3486438586481650344, 2798065426209788516`

### `iceberg.drop_view`

- `DELETE /v1/{cat}/namespaces/{ns}/views/{view}` → **204**
- wall 17 ms · 14 statements · 0 object ops · entity access: MIXED (batched 25% of 8 reads)
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
params: `POLARIS, probe_view2, 2798065426209788516, 881064999555903699, 7`

**[7]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `2798065426209788516, POLARIS, 3486438586481650344`

**[8]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 0, 0, 2798065426209788516, 881064999555903699, POLARIS`

**[9]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3486438586481650344, 7, 2798065426209788516`

**[10]** `entities` · DELETE · no timing

```sql
DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 2798065426209788516, 3486438586481650344`

**[11]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `2798065426209788516, POLARIS, 3486438586481650344`

**[12]** `grant_records` · DELETE · no timing

```sql
DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (
    (grantee_id = ? AND grantee_catalog_id = ?) OR
    (securable_id = ? AND securable_catalog_id = ?)
) AND realm_id = ?
```
params: `3486438586481650344, 2798065426209788516, 3486438586481650344, 2798065426209788516, POLARIS`

**[13]** `entities` · INSERT · no timing

```sql
INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme, realm_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```
params: `6196727799167266467, 0, 0, 8, entityCleanup_3486438586481650344, 1, 0, 1787213739455, 0, 0, 0, 1787213739455, {"taskType":"1","data":"{\"catalogId\":2798065426209788516,\"id\":3486438586481650344,\"parentId\":881064999555903699,\"typeCode\":7,\"name\":\"probe_view2\",\"entityVersion\":2,\"subTypeCode\":3,\"createTimestamp\":1787213737779,\"dropTimestamp\":0,\"purgeTimestamp\":0,\"toPurgeTimestamp\":0,\"lastUpdateTimestamp\":1787213739132,\"properties\":\"{}\",\"internalProperties\":\"{\\\"parent-namespace\\\": \\\"probe_ns\\\", \\\"metadata-location\\\": \\\"s3a://data-catalog-bucket/apiprofile1787213725_cat/probe_ns/probe_view/metadata/00000-281ff723-cdf7-4f4a-b9d8-eb28c228b95a.gz.metadata.json\\\"}\",\"grantRecordsVersion\":1}"}, {}, 1, NULL, POLARIS`

### `mgmt.list_catalogs`

- `GET /v1/catalogs` → **200**
- wall 57 ms · 8 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
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
- wall 11 ms · 7 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
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
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 0, 0, POLARIS`

### `mgmt.create_principal`

- `POST /v1/principals` → **201**
- wall 30 ms · 11 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
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
params: `POLARIS, 7668633578041483543, 2, 0`

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
params: `7668633578041483543, 0, 0, 2, apiprofile1787213725_p, 1, 0, 1787213741978, 0, 0, 0, 1787213741978, {}, {"client_id":"5669544fa4391412"}, 1, NULL, POLARIS`

### `mgmt.get_principal`

- `GET /v1/principals/{p}` → **200**
- wall 8 ms · 10 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
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
params: `POLARIS, apiprofile1787213725_p, 0, 0, 2`

**[7]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `7668633578041483543, POLARIS, 0`

**[8]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `0, POLARIS, 7668633578041483543`

**[9]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 0, POLARIS`

### `mgmt.list_principals`

- `GET /v1/principals` → **200**
- wall 23 ms · 8 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
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
- wall 26 ms · 8 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
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
params: `1344730803478824001, 0, 0, 3, apiprofile1787213725_pr, 1, 0, 1787213742957, 0, 0, 0, 1787213742957, {}, {}, 1, NULL, POLARIS`

### `mgmt.get_principal_role`

- `GET /v1/principal-roles/{r}` → **200**
- wall 26 ms · 10 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
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
params: `POLARIS, apiprofile1787213725_pr, 0, 0, 3`

**[7]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1344730803478824001, POLARIS, 0`

**[8]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `0, POLARIS, 1344730803478824001`

**[9]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 0, POLARIS`

### `mgmt.list_principal_roles`

- `GET /v1/principal-roles` → **200**
- wall 26 ms · 8 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
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
- wall 34 ms · 12 statements · 0 object ops · entity access: MIXED (batched 25% of 8 reads)
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
params: `0, 1, 0, 2, 0, 1344730803478824001, 0, 7668633578041483543, 0, 0, POLARIS`

**[7]** `grant_records` · INSERT · no timing

```sql
INSERT INTO POLARIS_SCHEMA.GRANT_RECORDS (securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code, realm_id) VALUES (?, ?, ?, ?, ?, ?)
```
params: `0, 1344730803478824001, 0, 7668633578041483543, 4, POLARIS`

**[8]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 7668633578041483543, 2, 0`

**[9]** `entities` · UPDATE · no timing

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE realm_id = ? AND entity_version = ? AND id = ? AND catalog_id = ?
```
params: `7668633578041483543, 0, 0, 2, apiprofile1787213725_p, 1, 0, 1787213741978, 0, 0, 0, 1787213741978, {}, {"client_id": "5669544fa4391412"}, 2, NULL, POLARIS, 1, 7668633578041483543, 0`

**[10]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1344730803478824001, 3, 0`

**[11]** `entities` · UPDATE · no timing

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE realm_id = ? AND entity_version = ? AND id = ? AND catalog_id = ?
```
params: `1344730803478824001, 0, 0, 3, apiprofile1787213725_pr, 1, 0, 1787213742957, 0, 0, 0, 1787213742957, {}, {}, 2, NULL, POLARIS, 1, 1344730803478824001, 0`

### `mgmt.create_catalog_role`

- `POST /v1/catalogs/{cat}/catalog-roles` → **201**
- wall 18 ms · 8 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
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
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 0, 0, POLARIS`

**[7]** `entities` · INSERT · no timing

```sql
INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme, realm_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```
params: `8439685745060622136, 2798065426209788516, 2798065426209788516, 5, apiprofile1787213725_cr, 1, 0, 1787213744288, 0, 0, 0, 1787213744288, {}, {}, 1, NULL, POLARIS`

### `mgmt.list_catalog_roles`

- `GET /v1/catalogs/{cat}/catalog-roles` → **200**
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
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 0, 0, POLARIS`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND sub_type_code = ? AND realm_id = ? AND parent_id = ? AND type_code = ?
```
params: `2798065426209788516, 0, POLARIS, 2798065426209788516, 5`

### `mgmt.assign_catalog_role`

- `PUT /v1/principal-roles/{r}/catalog-roles/{cat}` → **201**
- wall 47 ms · 19 statements · 0 object ops · entity access: MIXED (batched 36% of 11 reads)
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
params: `POLARIS, apiprofile1787213725_cr, 2798065426209788516, 2798065426209788516, 5`

**[7]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `8439685745060622136, POLARIS, 2798065426209788516`

**[8]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `2798065426209788516, POLARIS, 8439685745060622136`

**[9]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 0, 1344730803478824001, 0, 0, POLARIS`

**[10]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 1344730803478824001, POLARIS`

**[11]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1344730803478824001, POLARIS, 0`

**[12]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `0, POLARIS, 1344730803478824001`

**[13]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `2798065426209788516, 4473363673752462693, POLARIS`

**[14]** `grant_records` · INSERT · no timing

```sql
INSERT INTO POLARIS_SCHEMA.GRANT_RECORDS (securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code, realm_id) VALUES (?, ?, ?, ?, ?, ?)
```
params: `2798065426209788516, 8439685745060622136, 0, 1344730803478824001, 3, POLARIS`

**[15]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1344730803478824001, 3, 0`

**[16]** `entities` · UPDATE · no timing

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE realm_id = ? AND entity_version = ? AND id = ? AND catalog_id = ?
```
params: `1344730803478824001, 0, 0, 3, apiprofile1787213725_pr, 1, 0, 1787213742957, 0, 0, 0, 1787213742957, {}, {}, 3, NULL, POLARIS, 1, 1344730803478824001, 0`

**[17]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 8439685745060622136, 5, 2798065426209788516`

**[18]** `entities` · UPDATE · no timing

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE realm_id = ? AND entity_version = ? AND id = ? AND catalog_id = ?
```
params: `8439685745060622136, 2798065426209788516, 2798065426209788516, 5, apiprofile1787213725_cr, 1, 0, 1787213744288, 0, 0, 0, 1787213744288, {}, {}, 2, NULL, POLARIS, 1, 8439685745060622136, 2798065426209788516`

### `mgmt.grant_privilege`

- `PUT /v1/catalogs/{cat}/catalog-roles/{cr}/grants` → **201**
- wall 34 ms · 24 statements · 0 object ops · entity access: MIXED (batched 31% of 16 reads)
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
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 0, 0, 2798065426209788516, 8439685745060622136, POLARIS`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `2798065426209788516, 8439685745060622136, POLARIS`

**[8]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `8439685745060622136, POLARIS, 2798065426209788516`

**[9]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `2798065426209788516, POLARIS, 8439685745060622136`

**[10]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 2798065426209788516, 8439685745060622136`

**[11]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `8439685745060622136, POLARIS, 2798065426209788516`

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
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 0, 0, 2798065426209788516, 8439685745060622136, POLARIS`

**[19]** `grant_records` · INSERT · no timing

```sql
INSERT INTO POLARIS_SCHEMA.GRANT_RECORDS (securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code, realm_id) VALUES (?, ?, ?, ?, ?, ?)
```
params: `0, 2798065426209788516, 2798065426209788516, 8439685745060622136, 20, POLARIS`

**[20]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 8439685745060622136, 5, 2798065426209788516`

**[21]** `entities` · UPDATE · no timing

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE realm_id = ? AND entity_version = ? AND id = ? AND catalog_id = ?
```
params: `8439685745060622136, 2798065426209788516, 2798065426209788516, 5, apiprofile1787213725_cr, 1, 0, 1787213744288, 0, 0, 0, 1787213744288, {}, {}, 3, NULL, POLARIS, 1, 8439685745060622136, 2798065426209788516`

**[22]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2798065426209788516, 4, 0`

**[23]** `entities` · UPDATE · no timing

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE realm_id = ? AND entity_version = ? AND id = ? AND catalog_id = ?
```
params: `2798065426209788516, 0, 0, 4, apiprofile1787213725_cat, 1, 0, 1787213725729, 0, 0, 0, 1787213725729, {"default-base-location": "s3a://data-catalog-bucket/apiprofile1787213725_cat/", "polaris.config.drop-with-purge.enabled": "true"}, {"catalogType": "INTERNAL", "storage_configuration_info": "{\"@type\":\"AwsStorageConfigurationInfo\",\"allowedLocations\":[\"s3a://data-catalog-bucket/apiprofile1787213725_cat/\",\"s3a://data-catalog-bucket/\"],\"endpoint\":\"http://192.168.139.2:9000\",\"endpointInternal\":\"http://192.168.139.2:9000\",\"pathStyleAccess\":true,\"storageType\":\"S3\",\"fileIoImplClassName\":\"org.apache.iceberg.aws.s3.S3FileIO\"}"}, 5, NULL, POLARIS, 1, 2798065426209788516, 0`

### `mgmt.list_grants`

- `GET /v1/catalogs/{cat}/catalog-roles/{cr}/grants` → **200**
- wall 27 ms · 15 statements · 0 object ops · entity access: MIXED (batched 50% of 10 reads)
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
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 0, 0, 2798065426209788516, 8439685745060622136, POLARIS`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2798065426209788516, POLARIS`

**[8]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `0, POLARIS, 2798065426209788516`

**[9]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `2798065426209788516, 8439685745060622136, POLARIS`

**[10]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `8439685745060622136, POLARIS, 2798065426209788516`

**[11]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `2798065426209788516, POLARIS, 8439685745060622136`

**[12]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 2798065426209788516, 8439685745060622136`

**[13]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `8439685745060622136, POLARIS, 2798065426209788516`

**[14]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2798065426209788516, POLARIS`

### `mgmt.list_principals_for_principal_role`

- `GET /v1/principal-roles/{r}/principals` → **200**
- wall 18 ms · 13 statements · 0 object ops · entity access: MIXED (batched 44% of 9 reads)
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
params: `0, 1, 0, 2, 0, 1344730803478824001, 0, 0, POLARIS`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 1344730803478824001, POLARIS`

**[8]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1344730803478824001, POLARIS, 0`

**[9]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `0, POLARIS, 1344730803478824001`

**[10]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1344730803478824001`

**[11]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `0, POLARIS, 1344730803478824001`

**[12]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 7668633578041483543, POLARIS`

### `mgmt.reset_principal_credentials`

- `POST /v1/principals/{p}/reset` → **200**
- wall 42 ms · 14 statements · 0 object ops · entity access: MIXED (batched 38% of 8 reads)
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
params: `0, 1, 0, 2, 0, 7668633578041483543, 0, 0, POLARIS`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 7668633578041483543, POLARIS`

**[8]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `7668633578041483543, POLARIS, 0`

**[9]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `0, POLARIS, 7668633578041483543`

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
params: `POLARIS, 7668633578041483543, 2, 0`

**[13]** `principal_authentication_data` · INSERT · no timing

```sql
INSERT INTO POLARIS_SCHEMA.PRINCIPAL_AUTHENTICATION_DATA (principal_id, principal_client_id, main_secret_hash, secondary_secret_hash, secret_salt, realm_id) VALUES (?, ?, ?, ?, ?, ?)
```
params: `<redacted>`

### `mgmt.delete_catalog_role`

- `DELETE /v1/catalogs/{cat}/catalog-roles/{cr}` → **204**
- wall 51 ms · 16 statements · 0 object ops · entity access: MIXED (batched 38% of 8 reads)
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
params: `0, 1, 0, 2, 0, 2798065426209788516, 2798065426209788516, 4473363673752462693, 0, 0, 2798065426209788516, 8439685745060622136, POLARIS`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 8439685745060622136, 5, 2798065426209788516`

**[8]** `entities` · DELETE · no timing

```sql
DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 2798065426209788516, 8439685745060622136`

**[9]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `8439685745060622136, POLARIS, 2798065426209788516`

**[10]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `2798065426209788516, POLARIS, 8439685745060622136`

**[11]** `grant_records` · DELETE · no timing

```sql
DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (
    (grantee_id = ? AND grantee_catalog_id = ?) OR
    (securable_id = ? AND securable_catalog_id = ?)
) AND realm_id = ?
```
params: `8439685745060622136, 2798065426209788516, 8439685745060622136, 2798065426209788516, POLARIS`

**[12]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1344730803478824001, 0, 2798065426209788516, POLARIS`

**[13]** `entities` · UPDATE · no timing

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE realm_id = ? AND entity_version = ? AND id = ? AND catalog_id = ?
```
params: `1344730803478824001, 0, 0, 3, apiprofile1787213725_pr, 1, 0, 1787213742957, 0, 0, 0, 1787213742957, {}, {}, 4, NULL, POLARIS, 1, 1344730803478824001, 0`

**[14]** `entities` · UPDATE · no timing

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE realm_id = ? AND entity_version = ? AND id = ? AND catalog_id = ?
```
params: `2798065426209788516, 0, 0, 4, apiprofile1787213725_cat, 1, 0, 1787213725729, 0, 0, 0, 1787213725729, {"default-base-location": "s3a://data-catalog-bucket/apiprofile1787213725_cat/", "polaris.config.drop-with-purge.enabled": "true"}, {"catalogType": "INTERNAL", "storage_configuration_info": "{\"@type\":\"AwsStorageConfigurationInfo\",\"allowedLocations\":[\"s3a://data-catalog-bucket/apiprofile1787213725_cat/\",\"s3a://data-catalog-bucket/\"],\"endpoint\":\"http://192.168.139.2:9000\",\"endpointInternal\":\"http://192.168.139.2:9000\",\"pathStyleAccess\":true,\"storageType\":\"S3\",\"fileIoImplClassName\":\"org.apache.iceberg.aws.s3.S3FileIO\"}"}, 6, NULL, POLARIS, 1, 2798065426209788516, 0`

**[15]** `entities` · INSERT · no timing

```sql
INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme, realm_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```
params: `2114860770158593825, 0, 0, 8, entityCleanup_8439685745060622136, 1, 0, 1787213746682, 0, 0, 0, 1787213746682, {"taskType":"1","data":"{\"catalogId\":2798065426209788516,\"id\":8439685745060622136,\"parentId\":2798065426209788516,\"typeCode\":5,\"name\":\"apiprofile1787213725_cr\",\"entityVersion\":1,\"subTypeCode\":0,\"createTimestamp\":1787213744288,\"dropTimestamp\":0,\"purgeTimestamp\":0,\"toPurgeTimestamp\":0,\"lastUpdateTimestamp\":1787213744288,\"properties\":\"{}\",\"internalProperties\":\"{}\",\"grantRecordsVersion\":3}"}, {}, 1, NULL, POLARIS`

### `mgmt.delete_principal_role`

- `DELETE /v1/principal-roles/{r}` → **204**
- wall 49 ms · 18 statements · 0 object ops · entity access: MIXED (batched 44% of 9 reads)
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
params: `0, 1, 0, 2, 0, 1344730803478824001, 0, 0, POLARIS`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 1344730803478824001, POLARIS`

**[8]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1344730803478824001, POLARIS, 0`

**[9]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `0, POLARIS, 1344730803478824001`

**[10]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1344730803478824001, 3, 0`

**[11]** `entities` · DELETE · no timing

```sql
DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 1344730803478824001`

**[12]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1344730803478824001, POLARIS, 0`

**[13]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `0, POLARIS, 1344730803478824001`

**[14]** `grant_records` · DELETE · no timing

```sql
DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (
    (grantee_id = ? AND grantee_catalog_id = ?) OR
    (securable_id = ? AND securable_catalog_id = ?)
) AND realm_id = ?
```
params: `1344730803478824001, 0, 1344730803478824001, 0, POLARIS`

**[15]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 7668633578041483543, POLARIS`

**[16]** `entities` · UPDATE · no timing

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE realm_id = ? AND entity_version = ? AND id = ? AND catalog_id = ?
```
params: `7668633578041483543, 0, 0, 2, apiprofile1787213725_p, 1, 0, 1787213741978, 0, 0, 0, 1787213741978, {}, {"client_id": "5669544fa4391412"}, 3, NULL, POLARIS, 1, 7668633578041483543, 0`

**[17]** `entities` · INSERT · no timing

```sql
INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme, realm_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```
params: `3916734583598815517, 0, 0, 8, entityCleanup_1344730803478824001, 1, 0, 1787213747040, 0, 0, 0, 1787213747040, {"taskType":"1","data":"{\"catalogId\":0,\"id\":1344730803478824001,\"parentId\":0,\"typeCode\":3,\"name\":\"apiprofile1787213725_pr\",\"entityVersion\":1,\"subTypeCode\":0,\"createTimestamp\":1787213742957,\"dropTimestamp\":0,\"purgeTimestamp\":0,\"toPurgeTimestamp\":0,\"lastUpdateTimestamp\":1787213742957,\"properties\":\"{}\",\"internalProperties\":\"{}\",\"grantRecordsVersion\":4}"}, {}, 1, NULL, POLARIS`

### `mgmt.delete_principal`

- `DELETE /v1/principals/{p}` → **204**
- wall 20 ms · 16 statements · 0 object ops · entity access: MIXED (batched 38% of 8 reads)
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
params: `0, 1, 0, 2, 0, 7668633578041483543, 0, 0, POLARIS`

**[7]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 7668633578041483543, POLARIS`

**[8]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `7668633578041483543, POLARIS, 0`

**[9]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `0, POLARIS, 7668633578041483543`

**[10]** `entities` · SELECT · no timing

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 7668633578041483543, 2, 0`

**[11]** `entities` · DELETE · no timing

```sql
DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```
params: `POLARIS, 0, 7668633578041483543`

**[12]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `7668633578041483543, POLARIS, 0`

**[13]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `0, POLARIS, 7668633578041483543`

**[14]** `grant_records` · DELETE · no timing

```sql
DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (
    (grantee_id = ? AND grantee_catalog_id = ?) OR
    (securable_id = ? AND securable_catalog_id = ?)
) AND realm_id = ?
```
params: `7668633578041483543, 0, 7668633578041483543, 0, POLARIS`

**[15]** `principal_authentication_data` · DELETE · no timing

```sql
DELETE FROM POLARIS_SCHEMA.PRINCIPAL_AUTHENTICATION_DATA WHERE realm_id = ? AND principal_id = ? AND principal_client_id = ?
```
params: `<redacted>`
