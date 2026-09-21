# API → SQL → MinIO Access Matrix

Generated 2026-09-02 17:26 from a live local run — Polaris 1.3.0-incubating, realm POLARIS.

**Identity case: `authorized`**.

Every plan and every refusal below is a statement about THIS caller. A 403 here is a measurement, not a gap: it still pays the full authorization prelude, including the `grant_records` grantee lookup, before the decision is made.

R = read, W = write, RW = both.

## API → PostgreSQL tables

| API | entities | grant_records | policy_mapping_record |
|---|---|---|---|
| `iceberg.commit_table` | RW | R | · |
| `iceberg.create_namespace` | RW | R | · |
| `iceberg.create_table` | RW | R | · |
| `iceberg.create_view` | RW | R | · |
| `iceberg.drop_namespace` | RW | RW | RW |
| `iceberg.drop_table` | RW | RW | RW |
| `iceberg.drop_view` | RW | RW | · |
| `iceberg.get_config` | R | R | · |
| `iceberg.head_namespace` | R | R | · |
| `iceberg.head_table` | R | R | · |
| `iceberg.head_view` | R | R | · |
| `iceberg.list_namespaces` | R | R | · |
| `iceberg.list_tables` | R | R | · |
| `iceberg.list_views` | R | R | · |
| `iceberg.load_namespace` | R | R | · |
| `iceberg.load_table` | R | R | · |
| `iceberg.load_table[missing]` | R | R | · |
| `iceberg.load_table[snapshots=refs]` | R | R | · |
| `iceberg.load_view` | R | R | · |
| `iceberg.rename_table` | RW | R | · |
| `iceberg.rename_view` | RW | R | · |
| `iceberg.report_metrics` | R | R | · |
| `iceberg.stage_create_table` | R | R | · |
| `iceberg.update_namespace_properties` | RW | R | · |
| `mgmt.assign_catalog_role` | R | R | · |
| `mgmt.assign_principal_role` | R | R | · |
| `mgmt.create_catalog_role` | RW | R | · |
| `mgmt.create_principal` | R | R | · |
| `mgmt.create_principal_role` | R | R | · |
| `mgmt.delete_catalog_role` | RW | RW | · |
| `mgmt.delete_principal` | R | R | · |
| `mgmt.delete_principal_role` | R | R | · |
| `mgmt.get_catalog` | R | R | · |
| `mgmt.get_principal` | R | R | · |
| `mgmt.get_principal_role` | R | R | · |
| `mgmt.grant_privilege` | RW | RW | · |
| `mgmt.list_catalog_roles` | R | R | · |
| `mgmt.list_catalogs` | R | R | · |
| `mgmt.list_grants` | R | R | · |
| `mgmt.list_principal_roles` | R | R | · |
| `mgmt.list_principals` | R | R | · |
| `mgmt.list_principals_for_principal_role` | R | R | · |
| `mgmt.reset_principal_credentials` | R | R | · |

## Per-API detail

### `iceberg.get_config`

- `GET /v1/config` → **200**
- wall 45 ms · 10 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `root, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 2, 2259294436813395972, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `0, POLARIS, 2259294436813395972`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 3.32 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 2259294436813395972, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 3, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `authz1_principal, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `grant_records` · SELECT · 3.45 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 2259294436813395972, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[8]** `grant_records` · SELECT · 0.02 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND securable_catalog_id = ? AND securable_id = ?
```
params: `POLARIS, 0, 2259294436813395972`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 20 rows · cost 14.11
**[9]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×3 · est. 1 row · cost 24.20
### `iceberg.list_namespaces`

- `GET /v1/{cat}/namespaces` → **200**
- wall 71 ms · 8 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `root, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 2, 2259294436813395972, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `0, POLARIS, 2259294436813395972`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 7.71 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 2259294436813395972, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 3, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities · est. 2 rows · cost 40.02
**[7]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND sub_type_code = ? AND realm_id = ? AND parent_id = ? AND type_code = ?
```
params: `1893966347987449989, 0, POLARIS, 1893966347987449989, 6`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
### `iceberg.load_namespace`

- `GET /v1/{cat}/namespaces/{ns}` → **200**
- wall 54 ms · 9 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.08 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `root, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 2, 2259294436813395972, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `0, POLARIS, 2259294436813395972`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 9.06 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 2259294436813395972, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 3, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `probe_ns, POLARIS, 6, 1893966347987449989, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `grant_records` · SELECT · 0.02 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND securable_catalog_id = ? AND securable_id = ?
```
params: `POLARIS, 1893966347987449989, 5184606887867710024`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 1 row · cost 8.44
**[8]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities · est. 2 rows · cost 40.02
### `iceberg.head_namespace`

- `HEAD /v1/{cat}/namespaces/{ns}` → **204**
- wall 47 ms · 7 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.14 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `root, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.14 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 2, 2259294436813395972, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.23 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `0, POLARIS, 2259294436813395972`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 7.68 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 2259294436813395972, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 3, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.10 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 0, 0, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5, idx_entities · est. 2 rows · cost 47.86
### `iceberg.update_namespace_properties`

- `POST /v1/{cat}/namespaces/{ns}/properties` → **200**
- wall 44 ms · 12 statements · 0 object ops · entity access: MIXED (batched 38% of 8 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `root, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 2, 2259294436813395972, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `0, POLARIS, 2259294436813395972`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 5.15 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 2259294436813395972, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 3, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 0, 0, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5, idx_entities · est. 2 rows · cost 47.86
**[7]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND catalog_id = ? AND type_code = ? AND realm_id = ?
```
params: `1893966347987449989, 1893966347987449989, 6, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[8]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `probe_ns2, POLARIS, 6, 1893966347987449989, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[9]** `grant_records` · SELECT · 0.01 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND securable_catalog_id = ? AND securable_id = ?
```
params: `POLARIS, 1893966347987449989, 5976012681773110171`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 1 row · cost 8.44
**[10]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 0, 0, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5, idx_entities · est. 2 rows · cost 47.86
**[11]** `entities` · UPDATE · 0.25 ms

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE realm_id = ? AND catalog_id = ? AND id = ? AND entity_version = ?
```
params: `5184606887867710024, 1893966347987449989, 1893966347987449989, 6, probe_ns, 3, 0, 1788334618893, 0, 0, 0, 1788337582839, {"location":"s3a://data-catalog-bucket/apiprofile1788334618_cat/probe_ns/","k":"v"}, {}, 1, //data-catalog-bucket/apiprofile1788334618_cat/probe_ns/, POLARIS, 1893966347987449989, 5184606887867710024, 2`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
### `iceberg.create_namespace`

- `POST /v1/{cat}/namespaces` → **200**
- wall 60 ms · 16 statements · 0 object ops · entity access: MIXED (batched 42% of 12 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `root, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 2, 2259294436813395972, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `0, POLARIS, 2259294436813395972`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 5.58 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 2259294436813395972, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 3, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `probe_ns_tmp, POLARIS, 6, 1893966347987449989, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities · est. 2 rows · cost 40.02
**[8]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND catalog_id = ? AND type_code = ? AND realm_id = ?
```
params: `1893966347987449989, 1893966347987449989, 6, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[9]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 0, 0, 1893966347987449989, 5184606887867710024, 1893966347987449989, 5976012681773110171, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×6, idx_entities · est. 2 rows · cost 55.67
**[10]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[11]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `1893966347987449989, 6, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[12]** `entities` · INSERT · 0.10 ms

```sql
INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme, realm_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```
params: `9020430652320168994, 1893966347987449989, 1893966347987449989, 6, probe_ns_tmp, 1, 0, 1788337583150, 0, 0, 0, 1788337583150, {"location":"s3a://data-catalog-bucket/apiprofile1788334618_cat/probe_ns_tmp/"}, {}, 1, //data-catalog-bucket/apiprofile1788334618_cat/probe_ns_tmp/, POLARIS`

EXPLAIN (index absent) — ModifyTable, Result · est. 0 rows · cost 0.01
**[13]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `probe_ns_tmp, POLARIS, 6, 1893966347987449989, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[14]** `grant_records` · SELECT · 0.03 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND securable_catalog_id = ? AND securable_id = ?
```
params: `POLARIS, 1893966347987449989, 9020430652320168994`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 1 row · cost 8.44
**[15]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4 · est. 1 row · cost 32.13
### `iceberg.drop_namespace`

- `DELETE /v1/{cat}/namespaces/{ns}` → **204**
- wall 54 ms · 15 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records, policy_mapping_record

**[0]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `root, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 2, 2259294436813395972, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `0, POLARIS, 2259294436813395972`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 5.43 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 2259294436813395972, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 3, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 0, 0, 1893966347987449989, 9020430652320168994, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5, idx_entities · est. 2 rows · cost 47.86
**[7]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `1893966347987449989, 6, 9020430652320168994, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[8]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND realm_id = ?
```
params: `1893966347987449989, 9020430652320168994, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[9]** `entities` · DELETE · 0.02 ms

```sql
DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `1893966347987449989, POLARIS, 9020430652320168994`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[10]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND securable_catalog_id = ? AND securable_id = ?
```
params: `POLARIS, 1893966347987449989, 9020430652320168994`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 1 row · cost 8.44
**[11]** `grant_records` · DELETE · 3.82 ms

```sql
DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (
    (grantee_id = ? AND grantee_catalog_id = ?) OR
    (securable_id = ? AND securable_catalog_id = ?)
) AND realm_id = ?
```
params: `9020430652320168994, 1893966347987449989, 9020430652320168994, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1941.34
**[12]** `policy_mapping_record` · SELECT · 0.01 ms

```sql
SELECT target_catalog_id, target_id, policy_type_code, policy_catalog_id, policy_id, parameters FROM POLARIS_SCHEMA.POLICY_MAPPING_RECORD WHERE realm_id = ? AND target_catalog_id = ? AND target_id = ?
```
params: `POLARIS, 1893966347987449989, 9020430652320168994`

EXPLAIN (index absent) — Index Scan on policy_mapping_record using policy_mapping_record_pkey · est. 1 row · cost 8.17
**[13]** `policy_mapping_record` · DELETE · 0.02 ms

```sql
DELETE FROM POLARIS_SCHEMA.POLICY_MAPPING_RECORD WHERE target_catalog_id = ? AND target_id = ? AND realm_id = ?
```
params: `1893966347987449989, 9020430652320168994, POLARIS`

EXPLAIN (index absent) — Index Scan on policy_mapping_record using policy_mapping_record_pkey · est. 1 row · cost 8.17
**[14]** `grant_records` · SELECT · 0.07 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = $1 AND securable_catalog_id = $2 AND securable_id = $3 (grantee_id = $1 AND grantee_catalog_id = $2) OR (securable_id = $3 AND securable_catalog_id = $4) ) AND realm_id = $5 (grantee_id = $1 AND grantee_catalog_id = $2) OR (securable_id = $3 AND securable_catalog_id = $4) ) AND realm_id = $5
```

EXPLAIN (index absent) — not planned: parameters were redacted at capture (secret table); replay would need them reconstructed from the metastore
### `iceberg.list_tables`

- `GET /v1/{cat}/namespaces/{ns}/tables` → **200**
- wall 49 ms · 8 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `root, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 2, 2259294436813395972, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.13 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `0, POLARIS, 2259294436813395972`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 7.64 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 2259294436813395972, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 3, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.08 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 0, 0, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5, idx_entities · est. 2 rows · cost 47.86
**[7]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND sub_type_code = ? AND realm_id = ? AND parent_id = ? AND type_code = ?
```
params: `1893966347987449989, 2, POLARIS, 5184606887867710024, 7`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
### `iceberg.load_table`

- `GET /v1/{cat}/namespaces/{ns}/tables/{tbl}` → **200**
- wall 894 ms · 12 statements · 0 object ops · entity access: MIXED (batched 30% of 10 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.12 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `root, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 2, 2259294436813395972, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `0, POLARIS, 2259294436813395972`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 7.46 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 2259294436813395972, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 3, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `probe_tbl, POLARIS, 7, 5184606887867710024, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `grant_records` · SELECT · 0.02 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND securable_catalog_id = ? AND securable_id = ?
```
params: `POLARIS, 1893966347987449989, 3861358557659396986`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 1 row · cost 8.44
**[8]** `entities` · SELECT · 0.09 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 0, 0, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5, idx_entities · est. 2 rows · cost 47.86
**[9]** `entities` · SELECT · 0.08 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 1893966347987449989, 5184606887867710024, 1893966347987449989, 3861358557659396986, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×6 · est. 1 row · cost 47.86
**[10]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 4, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[11]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 4, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
### `iceberg.load_table[snapshots=refs]`

- `GET /v1/{cat}/.../tables/{tbl}?snapshots=refs` → **200**
- wall 57 ms · 8 statements · 0 object ops · entity access: MIXED (batched 43% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.09 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `root, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 2, 2259294436813395972, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `0, POLARIS, 2259294436813395972`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 7.80 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 2259294436813395972, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 3, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.11 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 0, 0, 1893966347987449989, 5184606887867710024, 1893966347987449989, 3861358557659396986, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×6, idx_entities · est. 2 rows · cost 55.67
**[7]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 1893966347987449989, 5184606887867710024, 1893966347987449989, 3861358557659396986, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×6 · est. 1 row · cost 47.86
### `iceberg.head_table`

- `HEAD /v1/{cat}/namespaces/{ns}/tables/{tbl}` → **204**
- wall 67 ms · 8 statements · 0 object ops · entity access: MIXED (batched 43% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.08 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `root, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.09 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 2, 2259294436813395972, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.17 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `0, POLARIS, 2259294436813395972`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 9.74 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 2259294436813395972, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 3, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.10 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 0, 0, 1893966347987449989, 5184606887867710024, 1893966347987449989, 3861358557659396986, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×6, idx_entities · est. 2 rows · cost 55.67
**[7]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 1893966347987449989, 5184606887867710024, 1893966347987449989, 3861358557659396986, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×6 · est. 1 row · cost 47.86
### `iceberg.create_table`

- `POST /v1/{cat}/namespaces/{ns}/tables` → **200**
- wall 130 ms · 24 statements · 0 object ops · entity access: MIXED (batched 42% of 19 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.16 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `root, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 2, 2259294436813395972, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `0, POLARIS, 2259294436813395972`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 8.24 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 2259294436813395972, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 3, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `probe_tbl2, POLARIS, 7, 5184606887867710024, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.08 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 0, 0, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5, idx_entities · est. 2 rows · cost 47.86
**[8]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `probe_tbl2, POLARIS, 7, 5184606887867710024, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[9]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5 · est. 1 row · cost 40.01
**[10]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `probe_tbl2, POLARIS, 7, 5184606887867710024, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[11]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5 · est. 1 row · cost 40.01
**[12]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `probe_tbl2, POLARIS, 7, 5184606887867710024, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[13]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5 · est. 1 row · cost 40.01
**[14]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 4, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[15]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND catalog_id = ? AND type_code = ? AND realm_id = ?
```
params: `5184606887867710024, 1893966347987449989, 6, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[16]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND catalog_id = ? AND type_code = ? AND realm_id = ?
```
params: `5184606887867710024, 1893966347987449989, 7, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[17]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 0, 0, 1893966347987449989, 5184606887867710024, 1893966347987449989, 3861358557659396986, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×6, idx_entities · est. 2 rows · cost 55.67
**[18]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `probe_tbl2, POLARIS, 7, 5184606887867710024, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[19]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5 · est. 1 row · cost 40.01
**[20]** `entities` · INSERT · 0.10 ms

```sql
INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme, realm_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```
params: `6530422781087266119, 1893966347987449989, 5184606887867710024, 7, probe_tbl2, 1, 2, 1788337586020, 0, 0, 0, 1788337586020, {"location":"s3a://data-catalog-bucket/apiprofile1788334618_cat/probe_ns/probe_tbl2/"}, {"last-sequence-number":"0","last-updated-ms":"1788337585968","next-row-id":"0","format-version":"2","metadata-location":"s3a://data-catalog-bucket/apiprofile1788334618_cat/probe_ns/probe_tbl2/metadata/00000-d7150ce3-661e-4f6b-9107-09e10b6883bb.metadata.json","table-uuid":"c96895e0-b94a-49fb-88ba-fee4979b32f6","default-sort-order-id":"0","last-partition-id":"999","parent-namespace":"probe_ns","current-schema-id":"0","location":"s3a://data-catalog-bucket/apiprofile1788334618_cat/probe_ns/probe_tbl2","last-column-id":"2","default-spec-id":"0"}, 1, //data-catalog-bucket/apiprofile1788334618_cat/probe_ns/probe_tbl2/, POLARIS`

EXPLAIN (index absent) — ModifyTable, Result · est. 0 rows · cost 0.01
**[21]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `probe_tbl2, POLARIS, 7, 5184606887867710024, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[22]** `grant_records` · SELECT · 0.02 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND securable_catalog_id = ? AND securable_id = ?
```
params: `POLARIS, 1893966347987449989, 6530422781087266119`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 1 row · cost 8.44
**[23]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5 · est. 1 row · cost 40.01
### `iceberg.stage_create_table`

- `POST /v1/{cat}/namespaces/{ns}/tables[stage]` → **200**
- wall 39 ms · 13 statements · 0 object ops · entity access: MIXED (batched 33% of 12 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `root, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 2, 2259294436813395972, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `0, POLARIS, 2259294436813395972`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 4.71 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 2259294436813395972, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 3, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `probe_staged, POLARIS, 7, 5184606887867710024, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 0, 0, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5, idx_entities · est. 2 rows · cost 47.86
**[8]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `probe_staged, POLARIS, 7, 5184606887867710024, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[9]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5 · est. 1 row · cost 40.01
**[10]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `probe_staged, POLARIS, 7, 5184606887867710024, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[11]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5 · est. 1 row · cost 40.01
**[12]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 4, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
### `iceberg.commit_table`

- `POST /v1/{cat}/namespaces/{ns}/tables/{tbl}` → **200**
- wall 62 ms · 15 statements · 0 object ops · entity access: MIXED (batched 54% of 13 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `root, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 2, 2259294436813395972, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `0, POLARIS, 2259294436813395972`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 3.27 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 2259294436813395972, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 3, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 0, 0, 1893966347987449989, 5184606887867710024, 1893966347987449989, 3861358557659396986, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×6, idx_entities · est. 2 rows · cost 55.67
**[7]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 1893966347987449989, 5184606887867710024, 1893966347987449989, 3861358557659396986, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×6 · est. 1 row · cost 47.86
**[8]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 1893966347987449989, 5184606887867710024, 1893966347987449989, 3861358557659396986, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×6 · est. 1 row · cost 47.86
**[9]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 4, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[10]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 1893966347987449989, 5184606887867710024, 1893966347987449989, 3861358557659396986, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×6 · est. 1 row · cost 47.86
**[11]** `entities` · UPDATE · 0.12 ms

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE realm_id = ? AND catalog_id = ? AND id = ? AND entity_version = ?
```
params: `3861358557659396986, 1893966347987449989, 5184606887867710024, 7, probe_tbl, 3, 2, 1788334618980, 0, 0, 0, 1788337586690, {"location":"s3a://data-catalog-bucket/apiprofile1788334618_cat/probe_ns/probe_tbl/"}, {"last-sequence-number":"0","last-updated-ms":"1788337586672","next-row-id":"0","format-version":"2","metadata-location":"s3a://data-catalog-bucket/apiprofile1788334618_cat/probe_ns/probe_tbl/metadata/00002-c187ab17-bb4d-4b06-bb56-68cf87a9e3d9.metadata.json","table-uuid":"16534a69-4a1e-43ea-9d50-f60be0305a0a","default-sort-order-id":"0","last-partition-id":"999","parent-namespace":"probe_ns","current-schema-id":"0","location":"s3a://data-catalog-bucket/apiprofile1788334618_cat/probe_ns/probe_tbl","last-column-id":"2","default-spec-id":"0"}, 1, //data-catalog-bucket/apiprofile1788334618_cat/probe_ns/probe_tbl/, POLARIS, 1893966347987449989, 3861358557659396986, 2`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[12]** `entities` · SELECT · 0.12 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 1893966347987449989, 5184606887867710024, 1893966347987449989, 3861358557659396986, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×6 · est. 1 row · cost 47.86
**[13]** `entities` · SELECT · 0.11 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `1893966347987449989, 3861358557659396986, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[14]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `1893966347987449989, 7, 3861358557659396986, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
### `iceberg.rename_table`

- `POST /v1/{cat}/tables/rename` → **200**
- wall 56 ms · 11 statements · 0 object ops · entity access: MIXED (batched 22% of 9 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.09 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `root, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 2, 2259294436813395972, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `0, POLARIS, 2259294436813395972`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 7.95 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 2259294436813395972, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 3, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `probe_tbl3, POLARIS, 7, 5184606887867710024, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 0, 0, 1893966347987449989, 5184606887867710024, 1893966347987449989, 6530422781087266119, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×6, idx_entities · est. 2 rows · cost 55.67
**[8]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `1893966347987449989, 7, 6530422781087266119, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[9]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `probe_tbl3, POLARIS, 7, 5184606887867710024, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[10]** `entities` · UPDATE · 0.09 ms

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE realm_id = ? AND catalog_id = ? AND id = ? AND entity_version = ?
```
params: `6530422781087266119, 1893966347987449989, 5184606887867710024, 7, probe_tbl3, 2, 2, 1788337586020, 0, 0, 0, 1788337587045, {"location":"s3a://data-catalog-bucket/apiprofile1788334618_cat/probe_ns/probe_tbl2/"}, {"last-updated-ms":"1788337585968","last-sequence-number":"0","next-row-id":"0","format-version":"2","metadata-location":"s3a://data-catalog-bucket/apiprofile1788334618_cat/probe_ns/probe_tbl2/metadata/00000-d7150ce3-661e-4f6b-9107-09e10b6883bb.metadata.json","table-uuid":"c96895e0-b94a-49fb-88ba-fee4979b32f6","default-sort-order-id":"0","last-partition-id":"999","parent-namespace":"probe_ns","current-schema-id":"0","location":"s3a://data-catalog-bucket/apiprofile1788334618_cat/probe_ns/probe_tbl2","last-column-id":"2","default-spec-id":"0"}, 1, //data-catalog-bucket/apiprofile1788334618_cat/probe_ns/probe_tbl2/, POLARIS, 1893966347987449989, 6530422781087266119, 1`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
### `iceberg.report_metrics`

- `POST /v1/{cat}/.../tables/{tbl}/metrics` → **204**
- wall 33 ms · 6 statements · 0 object ops · entity access: MIXED (batched 20% of 5 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `root, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 2, 2259294436813395972, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `0, POLARIS, 2259294436813395972`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 4.58 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 2259294436813395972, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 3, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
### `iceberg.load_table[missing]`

- `GET /v1/{cat}/.../tables/{missing}` → **404**
- wall 18 ms · 8 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `root, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 2, 2259294436813395972, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.34 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `0, POLARIS, 2259294436813395972`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 3.22 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 2259294436813395972, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 3, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `does_not_exist, POLARIS, 7, 5184606887867710024, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 0, 0, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5, idx_entities · est. 2 rows · cost 47.86
### `iceberg.drop_table`

- `DELETE /v1/{cat}/namespaces/{ns}/tables/{tbl}` → **204**
- wall 53 ms · 16 statements · 0 object ops · entity access: MIXED (batched 25% of 8 reads)
- tables: entities, grant_records, policy_mapping_record

**[0]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `root, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 2, 2259294436813395972, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `0, POLARIS, 2259294436813395972`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 7.28 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 2259294436813395972, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 3, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `probe_tbl3, POLARIS, 7, 5184606887867710024, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `grant_records` · SELECT · 0.02 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND securable_catalog_id = ? AND securable_id = ?
```
params: `POLARIS, 1893966347987449989, 6530422781087266119`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 1 row · cost 8.44
**[8]** `entities` · SELECT · 0.09 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 0, 0, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5, idx_entities · est. 2 rows · cost 47.86
**[9]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `1893966347987449989, 7, 6530422781087266119, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[10]** `entities` · DELETE · 0.03 ms

```sql
DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `1893966347987449989, POLARIS, 6530422781087266119`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[11]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND securable_catalog_id = ? AND securable_id = ?
```
params: `POLARIS, 1893966347987449989, 6530422781087266119`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 1 row · cost 8.44
**[12]** `grant_records` · DELETE · 5.25 ms

```sql
DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (
    (grantee_id = ? AND grantee_catalog_id = ?) OR
    (securable_id = ? AND securable_catalog_id = ?)
) AND realm_id = ?
```
params: `6530422781087266119, 1893966347987449989, 6530422781087266119, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1941.34
**[13]** `policy_mapping_record` · SELECT · 0.01 ms

```sql
SELECT target_catalog_id, target_id, policy_type_code, policy_catalog_id, policy_id, parameters FROM POLARIS_SCHEMA.POLICY_MAPPING_RECORD WHERE realm_id = ? AND target_catalog_id = ? AND target_id = ?
```
params: `POLARIS, 1893966347987449989, 6530422781087266119`

EXPLAIN (index absent) — Index Scan on policy_mapping_record using policy_mapping_record_pkey · est. 1 row · cost 8.17
**[14]** `policy_mapping_record` · DELETE · 0.03 ms

```sql
DELETE FROM POLARIS_SCHEMA.POLICY_MAPPING_RECORD WHERE target_catalog_id = ? AND target_id = ? AND realm_id = ?
```
params: `1893966347987449989, 6530422781087266119, POLARIS`

EXPLAIN (index absent) — Index Scan on policy_mapping_record using policy_mapping_record_pkey · est. 1 row · cost 8.17
**[15]** `grant_records` · SELECT · 0.02 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = $1 AND securable_catalog_id = $2 AND securable_id = $3 (grantee_id = $1 AND grantee_catalog_id = $2) OR (securable_id = $3 AND securable_catalog_id = $4) ) AND realm_id = $5 (grantee_id = $1 AND grantee_catalog_id = $2) OR (securable_id = $3 AND securable_catalog_id = $4) ) AND realm_id = $5
```

EXPLAIN (index absent) — not planned: parameters were redacted at capture (secret table); replay would need them reconstructed from the metastore
### `iceberg.create_view`

- `POST /v1/{cat}/namespaces/{ns}/views` → **200**
- wall 107 ms · 23 statements · 0 object ops · entity access: MIXED (batched 39% of 18 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.20 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `root, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 2, 2259294436813395972, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `0, POLARIS, 2259294436813395972`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 7.54 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 2259294436813395972, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 3, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `probe_view, POLARIS, 7, 5184606887867710024, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.08 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 0, 0, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5, idx_entities · est. 2 rows · cost 47.86
**[8]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `probe_view, POLARIS, 7, 5184606887867710024, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[9]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5 · est. 1 row · cost 40.01
**[10]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `probe_view, POLARIS, 7, 5184606887867710024, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[11]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5 · est. 1 row · cost 40.01
**[12]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `probe_view, POLARIS, 7, 5184606887867710024, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[13]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5 · est. 1 row · cost 40.01
**[14]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND catalog_id = ? AND type_code = ? AND realm_id = ?
```
params: `5184606887867710024, 1893966347987449989, 6, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[15]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND catalog_id = ? AND type_code = ? AND realm_id = ?
```
params: `5184606887867710024, 1893966347987449989, 7, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[16]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 0, 0, 1893966347987449989, 5184606887867710024, 1893966347987449989, 3861358557659396986, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×6, idx_entities · est. 2 rows · cost 55.67
**[17]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 4, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[18]** `entities` · INSERT · 0.11 ms

```sql
INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme, realm_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```
params: `8313783549222976721, 1893966347987449989, 5184606887867710024, 7, probe_view, 1, 3, 1788337588369, 0, 0, 0, 1788337588369, {}, {"metadata-location":"s3a://data-catalog-bucket/apiprofile1788334618_cat/probe_ns/probe_view/metadata/00000-29312877-9fae-4202-8513-b20b1d77c55e.gz.metadata.json","parent-namespace":"probe_ns"}, 1, NULL, POLARIS`

EXPLAIN (index absent) — ModifyTable, Result · est. 0 rows · cost 0.01
**[19]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `probe_view, POLARIS, 7, 5184606887867710024, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[20]** `grant_records` · SELECT · 0.01 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND securable_catalog_id = ? AND securable_id = ?
```
params: `POLARIS, 1893966347987449989, 8313783549222976721`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 1 row · cost 8.44
**[21]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5 · est. 1 row · cost 40.01
**[22]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 4, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
### `iceberg.list_views`

- `GET /v1/{cat}/namespaces/{ns}/views` → **200**
- wall 26 ms · 8 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `root, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 2, 2259294436813395972, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `0, POLARIS, 2259294436813395972`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 5.60 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 2259294436813395972, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 3, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.09 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 0, 0, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5, idx_entities · est. 2 rows · cost 47.86
**[7]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND sub_type_code = ? AND realm_id = ? AND parent_id = ? AND type_code = ?
```
params: `1893966347987449989, 3, POLARIS, 5184606887867710024, 7`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
### `iceberg.load_view`

- `GET /v1/{cat}/namespaces/{ns}/views/{view}` → **200**
- wall 44 ms · 9 statements · 0 object ops · entity access: MIXED (batched 50% of 8 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `root, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 2, 2259294436813395972, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `0, POLARIS, 2259294436813395972`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 4.46 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 2259294436813395972, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 3, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 0, 0, 1893966347987449989, 5184606887867710024, 1893966347987449989, 8313783549222976721, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×6, idx_entities · est. 2 rows · cost 55.67
**[7]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 1893966347987449989, 5184606887867710024, 1893966347987449989, 8313783549222976721, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×6 · est. 1 row · cost 47.86
**[8]** `entities` · SELECT · 0.09 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 1893966347987449989, 5184606887867710024, 1893966347987449989, 8313783549222976721, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×6 · est. 1 row · cost 47.86
### `iceberg.head_view`

- `HEAD /v1/{cat}/namespaces/{ns}/views/{view}` → **204**
- wall 68 ms · 9 statements · 0 object ops · entity access: MIXED (batched 50% of 8 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.12 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `root, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.10 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 2, 2259294436813395972, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.10 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `0, POLARIS, 2259294436813395972`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 8.46 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 2259294436813395972, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 3, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.12 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 0, 0, 1893966347987449989, 5184606887867710024, 1893966347987449989, 8313783549222976721, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×6, idx_entities · est. 2 rows · cost 55.67
**[7]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 1893966347987449989, 5184606887867710024, 1893966347987449989, 8313783549222976721, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×6 · est. 1 row · cost 47.86
**[8]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 1893966347987449989, 5184606887867710024, 1893966347987449989, 8313783549222976721, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×6 · est. 1 row · cost 47.86
### `iceberg.rename_view`

- `POST /v1/{cat}/views/rename` → **204**
- wall 62 ms · 11 statements · 0 object ops · entity access: MIXED (batched 22% of 9 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.15 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `root, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.14 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 2, 2259294436813395972, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.09 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `0, POLARIS, 2259294436813395972`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 7.64 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 2259294436813395972, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.09 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 3, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `probe_view2, POLARIS, 7, 5184606887867710024, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.10 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 0, 0, 1893966347987449989, 5184606887867710024, 1893966347987449989, 8313783549222976721, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×6, idx_entities · est. 2 rows · cost 55.67
**[8]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `1893966347987449989, 7, 8313783549222976721, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[9]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `probe_view2, POLARIS, 7, 5184606887867710024, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[10]** `entities` · UPDATE · 0.12 ms

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE realm_id = ? AND catalog_id = ? AND id = ? AND entity_version = ?
```
params: `8313783549222976721, 1893966347987449989, 5184606887867710024, 7, probe_view2, 2, 3, 1788337588369, 0, 0, 0, 1788337589673, {}, {"metadata-location":"s3a://data-catalog-bucket/apiprofile1788334618_cat/probe_ns/probe_view/metadata/00000-29312877-9fae-4202-8513-b20b1d77c55e.gz.metadata.json","parent-namespace":"probe_ns"}, 1, NULL, POLARIS, 1893966347987449989, 8313783549222976721, 1`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
### `iceberg.drop_view`

- `DELETE /v1/{cat}/namespaces/{ns}/views/{view}` → **204**
- wall 72 ms · 15 statements · 0 object ops · entity access: MIXED (batched 25% of 8 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.13 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `root, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.10 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 2, 2259294436813395972, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `0, POLARIS, 2259294436813395972`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 9.90 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 2259294436813395972, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 3, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `probe_view2, POLARIS, 7, 5184606887867710024, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `grant_records` · SELECT · 0.03 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND securable_catalog_id = ? AND securable_id = ?
```
params: `POLARIS, 1893966347987449989, 8313783549222976721`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 1 row · cost 8.44
**[8]** `entities` · SELECT · 0.09 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 0, 0, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5, idx_entities · est. 2 rows · cost 47.86
**[9]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `1893966347987449989, 7, 8313783549222976721, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[10]** `entities` · DELETE · 0.03 ms

```sql
DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `1893966347987449989, POLARIS, 8313783549222976721`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[11]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND securable_catalog_id = ? AND securable_id = ?
```
params: `POLARIS, 1893966347987449989, 8313783549222976721`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 1 row · cost 8.44
**[12]** `grant_records` · DELETE · 5.85 ms

```sql
DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (
    (grantee_id = ? AND grantee_catalog_id = ?) OR
    (securable_id = ? AND securable_catalog_id = ?)
) AND realm_id = ?
```
params: `8313783549222976721, 1893966347987449989, 8313783549222976721, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1941.34
**[13]** `entities` · INSERT · 0.29 ms

```sql
INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme, realm_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```
params: `6587103669520658018, 0, 0, 8, entityCleanup_8313783549222976721, 1, 0, 1788337590018, 0, 0, 0, 1788337590018, {"taskType":"1","data":"{\"catalogId\":1893966347987449989,\"id\":8313783549222976721,\"parentId\":5184606887867710024,\"typeCode\":7,\"name\":\"probe_view2\",\"entityVersion\":2,\"subTypeCode\":3,\"createTimestamp\":1788337588369,\"dropTimestamp\":0,\"purgeTimestamp\":0,\"toPurgeTimestamp\":0,\"lastUpdateTimestamp\":1788337589673,\"properties\":\"{}\",\"internalProperties\":\"{\\\"parent-namespace\\\": \\\"probe_ns\\\", \\\"metadata-location\\\": \\\"s3a://data-catalog-bucket/apiprofile1788334618_cat/probe_ns/probe_view/metadata/00000-29312877-9fae-4202-8513-b20b1d77c55e.gz.metadata.json\\\"}\",\"grantRecordsVersion\":1}"}, {}, 1, NULL, POLARIS`

EXPLAIN (index absent) — ModifyTable, Result · est. 0 rows · cost 0.01
**[14]** `grant_records` · SELECT · 0.05 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = $1 AND securable_catalog_id = $2 AND securable_id = $3 (grantee_id = $1 AND grantee_catalog_id = $2) OR (securable_id = $3 AND securable_catalog_id = $4) ) AND realm_id = $5 (grantee_id = $1 AND grantee_catalog_id = $2) OR (securable_id = $3 AND securable_catalog_id = $4) ) AND realm_id = $5
```

EXPLAIN (index absent) — not planned: parameters were redacted at capture (secret table); replay would need them reconstructed from the metastore
### `mgmt.list_catalogs`

- `GET /v1/catalogs` → **403**
- wall 44 ms · 7 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.19 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `root, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.10 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 2, 2259294436813395972, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `0, POLARIS, 2259294436813395972`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 9.14 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 2259294436813395972, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 3, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×2, idx_entities · est. 1 row · cost 24.19
### `mgmt.get_catalog`

- `GET /v1/catalogs/{cat}` → **200**
- wall 52 ms · 7 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.10 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `root, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.12 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 2, 2259294436813395972, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `0, POLARIS, 2259294436813395972`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 8.92 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 2259294436813395972, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.08 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 3, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities · est. 2 rows · cost 40.02
### `mgmt.create_principal`

- `POST /v1/principals` → **403**
- wall 61 ms · 9 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.12 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `root, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.08 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 2, 2259294436813395972, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `0, POLARIS, 2259294436813395972`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 9.31 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 2259294436813395972, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 3, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.10 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×2, idx_entities · est. 1 row · cost 24.19
**[7]** `entities` · SELECT · 0.08 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `root, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[8]** `events` · INSERT · 1.78 ms

```sql
INSERT INTO POLARIS_SCHEMA.EVENTS (catalog_id, event_id, request_id, event_type, timestamp_ms, principal_name, resource_type, resource_identifier, additional_properties, realm_id) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
```

EXPLAIN (index absent) — not planned: parameters were redacted at capture (secret table); replay would need them reconstructed from the metastore
### `mgmt.get_principal`

- `GET /v1/principals/{p}` → **404**
- wall 37 ms · 8 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.10 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `root, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.10 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 2, 2259294436813395972, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `0, POLARIS, 2259294436813395972`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 5.45 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 2259294436813395972, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 3, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `apiprofile1788334618_p, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×2, idx_entities · est. 1 row · cost 24.19
### `mgmt.list_principals`

- `GET /v1/principals` → **403**
- wall 17 ms · 7 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `root, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 2, 2259294436813395972, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `0, POLARIS, 2259294436813395972`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 3.40 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 2259294436813395972, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 3, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×2, idx_entities · est. 1 row · cost 24.19
### `mgmt.create_principal_role`

- `POST /v1/principal-roles` → **403**
- wall 26 ms · 7 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `root, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 2, 2259294436813395972, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `0, POLARIS, 2259294436813395972`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 5.71 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 2259294436813395972, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 3, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×2, idx_entities · est. 1 row · cost 24.19
### `mgmt.get_principal_role`

- `GET /v1/principal-roles/{r}` → **404**
- wall 49 ms · 8 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.15 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `root, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.12 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 2, 2259294436813395972, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.09 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `0, POLARIS, 2259294436813395972`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 8.23 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 2259294436813395972, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 3, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `apiprofile1788334618_pr, POLARIS, 3, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×2 · est. 1 row · cost 16.21
### `mgmt.list_principal_roles`

- `GET /v1/principal-roles` → **403**
- wall 48 ms · 7 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.21 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `root, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.08 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 2, 2259294436813395972, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.09 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `0, POLARIS, 2259294436813395972`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 9.80 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 2259294436813395972, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 3, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×2, idx_entities · est. 1 row · cost 24.19
### `mgmt.assign_principal_role`

- `PUT /v1/principals/{p}/principal-roles` → **404**
- wall 20 ms · 8 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `root, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 2, 2259294436813395972, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `0, POLARIS, 2259294436813395972`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 3.42 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 2259294436813395972, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 3, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `apiprofile1788334618_pr, POLARIS, 3, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×2 · est. 1 row · cost 16.21
### `mgmt.create_catalog_role`

- `POST /v1/catalogs/{cat}/catalog-roles` → **201**
- wall 25 ms · 8 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `root, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 2, 2259294436813395972, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `0, POLARIS, 2259294436813395972`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 4.03 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 2259294436813395972, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 3, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities · est. 2 rows · cost 40.02
**[7]** `entities` · INSERT · 0.07 ms

```sql
INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme, realm_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```
params: `5724903075050792902, 1893966347987449989, 1893966347987449989, 5, apiprofile1788334618_cr, 1, 0, 1788337593052, 0, 0, 0, 1788337593052, {}, {}, 1, NULL, POLARIS`

EXPLAIN (index absent) — ModifyTable, Result · est. 0 rows · cost 0.01
### `mgmt.list_catalog_roles`

- `GET /v1/catalogs/{cat}/catalog-roles` → **200**
- wall 47 ms · 8 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.14 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `root, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.16 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 2, 2259294436813395972, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `0, POLARIS, 2259294436813395972`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 7.84 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 2259294436813395972, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 3, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.13 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities · est. 2 rows · cost 40.02
**[7]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND sub_type_code = ? AND realm_id = ? AND parent_id = ? AND type_code = ?
```
params: `1893966347987449989, 0, POLARIS, 1893966347987449989, 5`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
### `mgmt.assign_catalog_role`

- `PUT /v1/principal-roles/{r}/catalog-roles/{cat}` → **404**
- wall 24 ms · 8 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `root, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 2, 2259294436813395972, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `0, POLARIS, 2259294436813395972`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 5.45 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 2259294436813395972, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 3, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `apiprofile1788334618_pr, POLARIS, 3, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4 · est. 1 row · cost 32.13
### `mgmt.grant_privilege`

- `PUT /v1/catalogs/{cat}/catalog-roles/{cr}/grants` → **201**
- wall 91 ms · 24 statements · 0 object ops · entity access: MIXED (batched 25% of 16 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.09 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `root, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 2, 2259294436813395972, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `0, POLARIS, 2259294436813395972`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 10.10 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 2259294436813395972, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.12 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 3, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `apiprofile1788334618_cr, POLARIS, 5, 1893966347987449989, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `grant_records` · SELECT · 4.21 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 5724903075050792902, 1893966347987449989`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[8]** `grant_records` · SELECT · 0.02 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND securable_catalog_id = ? AND securable_id = ?
```
params: `POLARIS, 1893966347987449989, 5724903075050792902`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 1 row · cost 8.44
**[9]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities · est. 2 rows · cost 40.02
**[10]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `1893966347987449989, POLARIS, 5724903075050792902`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[11]** `grant_records` · SELECT · 4.73 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 5724903075050792902, 1893966347987449989`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[12]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `root, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[13]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 2, 2259294436813395972, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[14]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `0, POLARIS, 2259294436813395972`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[15]** `grant_records` · SELECT · 4.74 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 2259294436813395972, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[16]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[17]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 3, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[18]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 0, 0, 1893966347987449989, 5724903075050792902, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5, idx_entities · est. 2 rows · cost 47.86
**[19]** `grant_records` · INSERT · 0.04 ms

```sql
INSERT INTO POLARIS_SCHEMA.GRANT_RECORDS (securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code, realm_id) VALUES (?, ?, ?, ?, ?, ?)
```
params: `0, 1893966347987449989, 1893966347987449989, 5724903075050792902, 20, POLARIS`

EXPLAIN (index absent) — ModifyTable, Result · est. 0 rows · cost 0.01
**[20]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `1893966347987449989, 5, 5724903075050792902, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[21]** `entities` · UPDATE · 0.04 ms

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE realm_id = ? AND catalog_id = ? AND id = ? AND entity_version = ?
```
params: `5724903075050792902, 1893966347987449989, 1893966347987449989, 5, apiprofile1788334618_cr, 1, 0, 1788337593052, 0, 0, 0, 1788337593052, {}, {}, 2, NULL, POLARIS, 1893966347987449989, 5724903075050792902, 1`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[22]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 4, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[23]** `entities` · UPDATE · 0.06 ms

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE realm_id = ? AND catalog_id = ? AND id = ? AND entity_version = ?
```
params: `1893966347987449989, 0, 0, 4, apiprofile1788334618_cat, 1, 0, 1788334618325, 0, 0, 0, 1788334618325, {"default-base-location": "s3a://data-catalog-bucket/apiprofile1788334618_cat/", "polaris.config.drop-with-purge.enabled": "true"}, {"catalogType": "INTERNAL", "storage_configuration_info": "{\"@type\":\"AwsStorageConfigurationInfo\",\"allowedLocations\":[\"s3a://data-catalog-bucket/apiprofile1788334618_cat/\",\"s3a://data-catalog-bucket/\"],\"endpoint\":\"http://192.168.139.2:9000\",\"endpointInternal\":\"http://192.168.139.2:9000\",\"pathStyleAccess\":true,\"storageType\":\"S3\",\"fileIoImplClassName\":\"org.apache.iceberg.aws.s3.S3FileIO\"}"}, 32, NULL, POLARIS, 0, 1893966347987449989, 1`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
### `mgmt.list_grants`

- `GET /v1/catalogs/{cat}/catalog-roles/{cr}/grants` → **200**
- wall 41 ms · 15 statements · 0 object ops · entity access: MIXED (batched 50% of 10 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `root, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 2, 2259294436813395972, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `0, POLARIS, 2259294436813395972`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 7.06 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 2259294436813395972, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 3, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 0, 0, 1893966347987449989, 5724903075050792902, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5, idx_entities · est. 2 rows · cost 47.86
**[7]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[8]** `grant_records` · SELECT · 0.04 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND securable_catalog_id = ? AND securable_id = ?
```
params: `POLARIS, 0, 1893966347987449989`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 20 rows · cost 14.11
**[9]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `1893966347987449989, 5724903075050792902, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[10]** `grant_records` · SELECT · 3.44 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 5724903075050792902, 1893966347987449989`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[11]** `grant_records` · SELECT · 0.04 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND securable_catalog_id = ? AND securable_id = ?
```
params: `POLARIS, 1893966347987449989, 5724903075050792902`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 1 row · cost 8.44
**[12]** `entities` · SELECT · 1.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `1893966347987449989, POLARIS, 5724903075050792902`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[13]** `grant_records` · SELECT · 3.46 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 5724903075050792902, 1893966347987449989`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[14]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
### `mgmt.list_principals_for_principal_role`

- `GET /v1/principal-roles/{r}/principals` → **404**
- wall 44 ms · 8 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.09 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `root, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.13 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 2, 2259294436813395972, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `0, POLARIS, 2259294436813395972`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 7.20 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 2259294436813395972, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 3, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `apiprofile1788334618_pr, POLARIS, 3, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.09 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×2 · est. 1 row · cost 16.21
### `mgmt.reset_principal_credentials`

- `POST /v1/principals/{p}/reset` → **404**
- wall 23 ms · 8 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `root, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 2, 2259294436813395972, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `0, POLARIS, 2259294436813395972`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 3.33 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 2259294436813395972, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 3, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `apiprofile1788334618_p, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×2, idx_entities · est. 1 row · cost 24.19
### `mgmt.delete_catalog_role`

- `DELETE /v1/catalogs/{cat}/catalog-roles/{cr}` → **204**
- wall 82 ms · 16 statements · 0 object ops · entity access: MIXED (batched 38% of 8 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.16 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `root, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.13 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 2, 2259294436813395972, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `0, POLARIS, 2259294436813395972`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 9.57 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 2259294436813395972, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 3, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.08 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 1893966347987449989, 1893966347987449989, 4852528578484813362, 0, 0, 1893966347987449989, 5724903075050792902, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5, idx_entities · est. 2 rows · cost 47.86
**[7]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `1893966347987449989, 5, 5724903075050792902, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[8]** `entities` · DELETE · 0.05 ms

```sql
DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `1893966347987449989, POLARIS, 5724903075050792902`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[9]** `grant_records` · SELECT · 5.51 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 5724903075050792902, 1893966347987449989`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[10]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND securable_catalog_id = ? AND securable_id = ?
```
params: `POLARIS, 1893966347987449989, 5724903075050792902`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 1 row · cost 8.44
**[11]** `grant_records` · DELETE · 5.04 ms

```sql
DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (
    (grantee_id = ? AND grantee_catalog_id = ?) OR
    (securable_id = ? AND securable_catalog_id = ?)
) AND realm_id = ?
```
params: `5724903075050792902, 1893966347987449989, 5724903075050792902, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1941.34
**[12]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[13]** `entities` · UPDATE · 0.06 ms

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE realm_id = ? AND catalog_id = ? AND id = ? AND entity_version = ?
```
params: `1893966347987449989, 0, 0, 4, apiprofile1788334618_cat, 1, 0, 1788334618325, 0, 0, 0, 1788334618325, {"default-base-location": "s3a://data-catalog-bucket/apiprofile1788334618_cat/", "polaris.config.drop-with-purge.enabled": "true"}, {"catalogType": "INTERNAL", "storage_configuration_info": "{\"@type\":\"AwsStorageConfigurationInfo\",\"allowedLocations\":[\"s3a://data-catalog-bucket/apiprofile1788334618_cat/\",\"s3a://data-catalog-bucket/\"],\"endpoint\":\"http://192.168.139.2:9000\",\"endpointInternal\":\"http://192.168.139.2:9000\",\"pathStyleAccess\":true,\"storageType\":\"S3\",\"fileIoImplClassName\":\"org.apache.iceberg.aws.s3.S3FileIO\"}"}, 33, NULL, POLARIS, 0, 1893966347987449989, 1`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[14]** `entities` · INSERT · 0.09 ms

```sql
INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme, realm_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```
params: `5913900384225885460, 0, 0, 8, entityCleanup_5724903075050792902, 1, 0, 1788337595240, 0, 0, 0, 1788337595240, {"taskType":"1","data":"{\"catalogId\":1893966347987449989,\"id\":5724903075050792902,\"parentId\":1893966347987449989,\"typeCode\":5,\"name\":\"apiprofile1788334618_cr\",\"entityVersion\":1,\"subTypeCode\":0,\"createTimestamp\":1788337593052,\"dropTimestamp\":0,\"purgeTimestamp\":0,\"toPurgeTimestamp\":0,\"lastUpdateTimestamp\":1788337593052,\"properties\":\"{}\",\"internalProperties\":\"{}\",\"grantRecordsVersion\":2}"}, {}, 1, NULL, POLARIS`

EXPLAIN (index absent) — ModifyTable, Result · est. 0 rows · cost 0.01
**[15]** `grant_records` · SELECT · 0.02 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = $1 AND securable_catalog_id = $2 AND securable_id = $3 (grantee_id = $1 AND grantee_catalog_id = $2) OR (securable_id = $3 AND securable_catalog_id = $4) ) AND realm_id = $5 (grantee_id = $1 AND grantee_catalog_id = $2) OR (securable_id = $3 AND securable_catalog_id = $4) ) AND realm_id = $5
```

EXPLAIN (index absent) — not planned: parameters were redacted at capture (secret table); replay would need them reconstructed from the metastore
### `mgmt.delete_principal_role`

- `DELETE /v1/principal-roles/{r}` → **404**
- wall 39 ms · 8 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.12 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `root, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 2, 2259294436813395972, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `0, POLARIS, 2259294436813395972`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 8.00 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 2259294436813395972, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 3, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `apiprofile1788334618_pr, POLARIS, 3, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×2 · est. 1 row · cost 16.21
### `mgmt.delete_principal`

- `DELETE /v1/principals/{p}` → **404**
- wall 46 ms · 8 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.15 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `root, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.08 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 2, 2259294436813395972, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND realm_id = ? AND id = ?
```
params: `0, POLARIS, 2259294436813395972`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 9.32 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE realm_id = ? AND grantee_id = ? AND grantee_catalog_id = ?
```
params: `POLARIS, 2259294436813395972, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND type_code = ? AND id = ? AND realm_id = ?
```
params: `0, 3, 2582725999201653854, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE name = ? AND realm_id = ? AND type_code = ? AND parent_id = ? AND catalog_id = ?
```
params: `apiprofile1788334618_p, POLARIS, 2, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2259294436813395972, 0, 2582725999201653854, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×2, idx_entities · est. 1 row · cost 24.19
