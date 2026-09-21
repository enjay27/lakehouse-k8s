# API → SQL → MinIO Access Matrix

Generated 2026-09-03 09:41 from a live local run — Polaris 1.3.0-incubating, realm POLARIS.

**Identity case: `admin`**.

Every plan and every refusal below is a statement about THIS caller. A 403 here is a measurement, not a gap: it still pays the full authorization prelude, including the `grant_records` grantee lookup, before the decision is made.

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
| `mgmt.reset_principal_credentials` | R | R | · | · |

## Per-API detail

### `iceberg.get_config`

- `GET /v1/config` → **200**
- wall 141 ms · 16 statements · 0 object ops · entity access: MIXED (batched 20% of 10 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, root`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9118527594773052894, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `9118527594773052894, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 2.69 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 9118527594773052894, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.44 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2, 0, 3340119121637991836, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using idx_entities, entities_pkey · est. 1 row · cost 16.22
**[5]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3340119121637991836, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, admin1_principal`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[8]** `grant_records` · SELECT · 3.36 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 9118527594773052894, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[9]** `grant_records` · SELECT · 0.82 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_id = ? AND securable_catalog_id = ? AND realm_id = ?
```
params: `9118527594773052894, 0, POLARIS`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 20 rows · cost 14.11
**[10]** `entities` · SELECT · 4.81 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 4, POLARIS, apiprofile1788334618_cat`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[11]** `grant_records` · SELECT · 0.26 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_id = ? AND securable_catalog_id = ? AND realm_id = ?
```
params: `1893966347987449989, 0, POLARIS`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 20 rows · cost 14.11
**[12]** `entities` · SELECT · 0.81 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 5184463786878295939, 5, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[13]** `grant_records` · SELECT · 3.16 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `1893966347987449989, 5184463786878295939, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[14]** `grant_records` · SELECT · 0.25 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_id = ? AND securable_catalog_id = ? AND realm_id = ?
```
params: `5184463786878295939, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 1 row · cost 8.44
**[15]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 2, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
### `iceberg.list_namespaces`

- `GET /v1/{cat}/namespaces` → **200**
- wall 217 ms · 9 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, root`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9118527594773052894, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `9118527594773052894, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 2.31 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 9118527594773052894, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2, 0, 3340119121637991836, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using idx_entities, entities_pkey · est. 1 row · cost 16.22
**[5]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3340119121637991836, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 50.75 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×3, idx_entities ×2 · est. 2 rows · cost 36.45
**[8]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND sub_type_code = ? AND realm_id = ? AND parent_id = ? AND type_code = ?
```
params: `1893966347987449989, 0, POLARIS, 1893966347987449989, 6`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
### `iceberg.load_namespace`

- `GET /v1/{cat}/namespaces/{ns}` → **200**
- wall 62 ms · 10 statements · 0 object ops · entity access: MIXED (batched 25% of 8 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, root`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.17 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9118527594773052894, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `9118527594773052894, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 2.95 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 9118527594773052894, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2, 0, 3340119121637991836, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using idx_entities, entities_pkey · est. 1 row · cost 16.22
**[5]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3340119121637991836, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `1893966347987449989, 1893966347987449989, 6, POLARIS, probe_ns`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[8]** `grant_records` · SELECT · 0.01 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_id = ? AND securable_catalog_id = ? AND realm_id = ?
```
params: `5184606887867710024, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 1 row · cost 8.44
**[9]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×3, idx_entities ×2 · est. 2 rows · cost 36.45
### `iceberg.head_namespace`

- `HEAD /v1/{cat}/namespaces/{ns}` → **204**
- wall 23 ms · 8 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, root`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9118527594773052894, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `9118527594773052894, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 2.52 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 9118527594773052894, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2, 0, 3340119121637991836, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using idx_entities, entities_pkey · est. 1 row · cost 16.22
**[5]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3340119121637991836, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 0, 0, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities ×2 · est. 2 rows · cost 44.34
### `iceberg.update_namespace_properties`

- `POST /v1/{cat}/namespaces/{ns}/properties` → **200**
- wall 137 ms · 13 statements · 0 object ops · entity access: MIXED (batched 33% of 9 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, root`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9118527594773052894, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `9118527594773052894, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 3.49 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 9118527594773052894, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2, 0, 3340119121637991836, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using idx_entities, entities_pkey · est. 1 row · cost 16.22
**[5]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3340119121637991836, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 0, 0, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities ×2 · est. 2 rows · cost 44.34
**[8]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND type_code = ? AND catalog_id = ? AND parent_id = ?
```
params: `POLARIS, 6, 1893966347987449989, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[9]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `1893966347987449989, 1893966347987449989, 6, POLARIS, probe_ns2`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[10]** `grant_records` · SELECT · 0.02 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_id = ? AND securable_catalog_id = ? AND realm_id = ?
```
params: `5976012681773110171, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 1 row · cost 8.44
**[11]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 0, 0, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities ×2 · est. 2 rows · cost 44.34
**[12]** `entities` · UPDATE · 2.07 ms

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE entity_version = ? AND id = ? AND catalog_id = ? AND realm_id = ?
```
params: `5184606887867710024, 1893966347987449989, 1893966347987449989, 6, probe_ns, 4, 0, 1788334618893, 0, 0, 0, 1788396083314, {"location":"s3a://data-catalog-bucket/apiprofile1788334618_cat/probe_ns/","k":"v"}, {}, 1, //data-catalog-bucket/apiprofile1788334618_cat/probe_ns/, 3, 5184606887867710024, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
### `iceberg.create_namespace`

- `POST /v1/{cat}/namespaces` → **200**
- wall 57 ms · 17 statements · 0 object ops · entity access: MIXED (batched 38% of 13 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, root`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9118527594773052894, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `9118527594773052894, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 2.54 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 9118527594773052894, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2, 0, 3340119121637991836, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using idx_entities, entities_pkey · est. 1 row · cost 16.22
**[5]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3340119121637991836, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `1893966347987449989, 1893966347987449989, 6, POLARIS, probe_ns_tmp`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[8]** `entities` · SELECT · 0.08 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×3, idx_entities ×2 · est. 2 rows · cost 36.45
**[9]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND type_code = ? AND catalog_id = ? AND parent_id = ?
```
params: `POLARIS, 6, 1893966347987449989, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[10]** `entities` · SELECT · 0.50 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 0, 0, 1893966347987449989, 5184606887867710024, 1893966347987449989, 5976012681773110171, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5, idx_entities ×2 · est. 2 rows · cost 52.19
**[11]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[12]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 5184606887867710024, 6, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[13]** `entities` · INSERT · 4.90 ms

```sql
INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme, realm_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```
params: `6485278696849335094, 1893966347987449989, 1893966347987449989, 6, probe_ns_tmp, 1, 0, 1788396083697, 0, 0, 0, 1788396083697, {"location":"s3a://data-catalog-bucket/apiprofile1788334618_cat/probe_ns_tmp/"}, {}, 1, //data-catalog-bucket/apiprofile1788334618_cat/probe_ns_tmp/, POLARIS`

EXPLAIN (index absent) — ModifyTable, Result · est. 0 rows · cost 0.01
**[14]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `1893966347987449989, 1893966347987449989, 6, POLARIS, probe_ns_tmp`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[15]** `grant_records` · SELECT · 0.01 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_id = ? AND securable_catalog_id = ? AND realm_id = ?
```
params: `6485278696849335094, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 1 row · cost 8.44
**[16]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×3, idx_entities · est. 1 row · cost 32.13
### `iceberg.drop_namespace`

- `DELETE /v1/{cat}/namespaces/{ns}` → **204**
- wall 98 ms · 16 statements · 0 object ops · entity access: MIXED (batched 25% of 8 reads)
- tables: entities, grant_records, policy_mapping_record

**[0]** `entities` · SELECT · 0.11 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, root`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9118527594773052894, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `9118527594773052894, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 2.32 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 9118527594773052894, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2, 0, 3340119121637991836, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using idx_entities, entities_pkey · est. 1 row · cost 16.22
**[5]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3340119121637991836, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.21 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 0, 0, 1893966347987449989, 6485278696849335094, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities ×2 · est. 2 rows · cost 44.34
**[8]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 6485278696849335094, 6, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[9]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND realm_id = ?
```
params: `1893966347987449989, 6485278696849335094, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[10]** `entities` · DELETE · 0.07 ms

```sql
DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `6485278696849335094, POLARIS, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[11]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_id = ? AND securable_catalog_id = ? AND realm_id = ?
```
params: `6485278696849335094, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 1 row · cost 8.44
**[12]** `grant_records` · DELETE · 8.70 ms

```sql
DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (
    (grantee_id = ? AND grantee_catalog_id = ?) OR
    (securable_id = ? AND securable_catalog_id = ?)
) AND realm_id = ?
```
params: `6485278696849335094, 1893966347987449989, 6485278696849335094, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1941.34
**[13]** `policy_mapping_record` · SELECT · 0.01 ms

```sql
SELECT target_catalog_id, target_id, policy_type_code, policy_catalog_id, policy_id, parameters FROM POLARIS_SCHEMA.POLICY_MAPPING_RECORD WHERE target_id = ? AND target_catalog_id = ? AND realm_id = ?
```
params: `6485278696849335094, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Index Scan on policy_mapping_record using policy_mapping_record_pkey · est. 1 row · cost 8.17
**[14]** `policy_mapping_record` · DELETE · 0.07 ms

```sql
DELETE FROM POLARIS_SCHEMA.POLICY_MAPPING_RECORD WHERE target_catalog_id = ? AND target_id = ? AND realm_id = ?
```
params: `1893966347987449989, 6485278696849335094, POLARIS`

EXPLAIN (index absent) — Index Scan on policy_mapping_record using policy_mapping_record_pkey · est. 1 row · cost 8.17
**[15]** `grant_records` · SELECT · 0.05 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_id = $1 AND securable_catalog_id = $2 AND realm_id = $3 (grantee_id = $1 AND grantee_catalog_id = $2) OR (securable_id = $3 AND securable_catalog_id = $4) ) AND realm_id = $5 (grantee_id = $1 AND grantee_catalog_id = $2) OR (securable_id = $3 AND securable_catalog_id = $4) ) AND realm_id = $5
```
params: `$1 = '6485278696849335094', $2 = '1893966347987449989', $3 = '6485278696849335094', $4 = '1893966347987449989', $5 = 'POLARIS'`

EXPLAIN (index absent) — not planned: placeholder/parameter mismatch: SQL has 0 placeholders, 5 values captured
### `iceberg.list_tables`

- `GET /v1/{cat}/namespaces/{ns}/tables` → **200**
- wall 23 ms · 9 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, root`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9118527594773052894, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `9118527594773052894, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 2.35 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 9118527594773052894, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2, 0, 3340119121637991836, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using idx_entities, entities_pkey · est. 1 row · cost 16.22
**[5]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3340119121637991836, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 0, 0, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities ×2 · est. 2 rows · cost 44.34
**[8]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND sub_type_code = ? AND realm_id = ? AND parent_id = ? AND type_code = ?
```
params: `1893966347987449989, 2, POLARIS, 5184606887867710024, 7`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
### `iceberg.load_table`

- `GET /v1/{cat}/namespaces/{ns}/tables/{tbl}` → **200**
- wall 1114 ms · 13 statements · 0 object ops · entity access: MIXED (batched 27% of 11 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, root`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9118527594773052894, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `9118527594773052894, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 6.19 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 9118527594773052894, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2, 0, 3340119121637991836, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using idx_entities, entities_pkey · est. 1 row · cost 16.22
**[5]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3340119121637991836, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `1893966347987449989, 5184606887867710024, 7, POLARIS, probe_tbl`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[8]** `grant_records` · SELECT · 0.02 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_id = ? AND securable_catalog_id = ? AND realm_id = ?
```
params: `3861358557659396986, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 1 row · cost 8.44
**[9]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 0, 0, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities ×2 · est. 2 rows · cost 44.34
**[10]** `entities` · SELECT · 1.49 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 1893966347987449989, 5184606887867710024, 1893966347987449989, 3861358557659396986, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5, idx_entities · est. 1 row · cost 47.86
**[11]** `entities` · SELECT · 0.40 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1893966347987449989, 4, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[12]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1893966347987449989, 4, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
### `iceberg.load_table[snapshots=refs]`

- `GET /v1/{cat}/.../tables/{tbl}?snapshots=refs` → **200**
- wall 68 ms · 9 statements · 0 object ops · entity access: MIXED (batched 38% of 8 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.08 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, root`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.08 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9118527594773052894, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `9118527594773052894, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 7.83 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 9118527594773052894, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 3.33 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2, 0, 3340119121637991836, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using idx_entities, entities_pkey · est. 1 row · cost 16.22
**[5]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3340119121637991836, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.10 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 0, 0, 1893966347987449989, 5184606887867710024, 1893966347987449989, 3861358557659396986, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5, idx_entities ×2 · est. 2 rows · cost 52.19
**[8]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 1893966347987449989, 5184606887867710024, 1893966347987449989, 3861358557659396986, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5, idx_entities · est. 1 row · cost 47.86
### `iceberg.head_table`

- `HEAD /v1/{cat}/namespaces/{ns}/tables/{tbl}` → **204**
- wall 51 ms · 9 statements · 0 object ops · entity access: MIXED (batched 38% of 8 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, root`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9118527594773052894, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `9118527594773052894, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 4.63 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 9118527594773052894, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2, 0, 3340119121637991836, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using idx_entities, entities_pkey · est. 1 row · cost 16.22
**[5]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3340119121637991836, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 0, 0, 1893966347987449989, 5184606887867710024, 1893966347987449989, 3861358557659396986, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5, idx_entities ×2 · est. 2 rows · cost 52.19
**[8]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 1893966347987449989, 5184606887867710024, 1893966347987449989, 3861358557659396986, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5, idx_entities · est. 1 row · cost 47.86
### `iceberg.create_table`

- `POST /v1/{cat}/namespaces/{ns}/tables` → **200**
- wall 276 ms · 25 statements · 0 object ops · entity access: MIXED (batched 40% of 20 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.08 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, root`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.12 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9118527594773052894, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `9118527594773052894, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 5.95 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 9118527594773052894, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2, 0, 3340119121637991836, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using idx_entities, entities_pkey · est. 1 row · cost 16.22
**[5]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3340119121637991836, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `1893966347987449989, 5184606887867710024, 7, POLARIS, probe_tbl2`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[8]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 0, 0, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities ×2 · est. 2 rows · cost 44.34
**[9]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `1893966347987449989, 5184606887867710024, 7, POLARIS, probe_tbl2`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[10]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities · est. 1 row · cost 40.02
**[11]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `1893966347987449989, 5184606887867710024, 7, POLARIS, probe_tbl2`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[12]** `entities` · SELECT · 0.08 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities · est. 1 row · cost 40.02
**[13]** `entities` · SELECT · 0.10 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `1893966347987449989, 5184606887867710024, 7, POLARIS, probe_tbl2`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[14]** `entities` · SELECT · 0.08 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities · est. 1 row · cost 40.02
**[15]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1893966347987449989, 4, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[16]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND type_code = ? AND catalog_id = ? AND parent_id = ?
```
params: `POLARIS, 6, 1893966347987449989, 5184606887867710024`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[17]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND type_code = ? AND catalog_id = ? AND parent_id = ?
```
params: `POLARIS, 7, 1893966347987449989, 5184606887867710024`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[18]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 0, 0, 1893966347987449989, 5184606887867710024, 1893966347987449989, 3861358557659396986, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5, idx_entities ×2 · est. 2 rows · cost 52.19
**[19]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `1893966347987449989, 5184606887867710024, 7, POLARIS, probe_tbl2`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[20]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities · est. 1 row · cost 40.02
**[21]** `entities` · INSERT · 0.42 ms

```sql
INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme, realm_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```
params: `8260655206039764610, 1893966347987449989, 5184606887867710024, 7, probe_tbl2, 1, 2, 1788396086817, 0, 0, 0, 1788396086817, {"location":"s3a://data-catalog-bucket/apiprofile1788334618_cat/probe_ns/probe_tbl2/"}, {"last-sequence-number":"0","last-updated-ms":"1788396086710","next-row-id":"0","format-version":"2","metadata-location":"s3a://data-catalog-bucket/apiprofile1788334618_cat/probe_ns/probe_tbl2/metadata/00000-581ad81c-1621-4780-9277-a69b4dbd92dc.metadata.json","table-uuid":"f30d285d-e4d6-4faf-a293-fd7b79112833","default-sort-order-id":"0","last-partition-id":"999","parent-namespace":"probe_ns","current-schema-id":"0","location":"s3a://data-catalog-bucket/apiprofile1788334618_cat/probe_ns/probe_tbl2","last-column-id":"2","default-spec-id":"0"}, 1, //data-catalog-bucket/apiprofile1788334618_cat/probe_ns/probe_tbl2/, POLARIS`

EXPLAIN (index absent) — ModifyTable, Result · est. 0 rows · cost 0.01
**[22]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `1893966347987449989, 5184606887867710024, 7, POLARIS, probe_tbl2`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[23]** `grant_records` · SELECT · 0.01 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_id = ? AND securable_catalog_id = ? AND realm_id = ?
```
params: `8260655206039764610, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 1 row · cost 8.44
**[24]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities · est. 1 row · cost 40.02
### `iceberg.stage_create_table`

- `POST /v1/{cat}/namespaces/{ns}/tables[stage]` → **200**
- wall 38 ms · 14 statements · 0 object ops · entity access: MIXED (batched 31% of 13 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, root`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9118527594773052894, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `9118527594773052894, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 2.47 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 9118527594773052894, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2, 0, 3340119121637991836, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using idx_entities, entities_pkey · est. 1 row · cost 16.22
**[5]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3340119121637991836, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `1893966347987449989, 5184606887867710024, 7, POLARIS, probe_staged`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[8]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 0, 0, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities ×2 · est. 2 rows · cost 44.34
**[9]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `1893966347987449989, 5184606887867710024, 7, POLARIS, probe_staged`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[10]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities · est. 1 row · cost 40.02
**[11]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `1893966347987449989, 5184606887867710024, 7, POLARIS, probe_staged`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[12]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities · est. 1 row · cost 40.02
**[13]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1893966347987449989, 4, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
### `iceberg.commit_table`

- `POST /v1/{cat}/namespaces/{ns}/tables/{tbl}` → **200**
- wall 86 ms · 16 statements · 0 object ops · entity access: MIXED (batched 50% of 14 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.11 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, root`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9118527594773052894, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `9118527594773052894, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 3.33 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 9118527594773052894, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2, 0, 3340119121637991836, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using idx_entities, entities_pkey · est. 1 row · cost 16.22
**[5]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3340119121637991836, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.08 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 0, 0, 1893966347987449989, 5184606887867710024, 1893966347987449989, 3861358557659396986, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5, idx_entities ×2 · est. 2 rows · cost 52.19
**[8]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 1893966347987449989, 5184606887867710024, 1893966347987449989, 3861358557659396986, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5, idx_entities · est. 1 row · cost 47.86
**[9]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 1893966347987449989, 5184606887867710024, 1893966347987449989, 3861358557659396986, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5, idx_entities · est. 1 row · cost 47.86
**[10]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1893966347987449989, 4, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[11]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 1893966347987449989, 5184606887867710024, 1893966347987449989, 3861358557659396986, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5, idx_entities · est. 1 row · cost 47.86
**[12]** `entities` · UPDATE · 0.06 ms

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE entity_version = ? AND id = ? AND catalog_id = ? AND realm_id = ?
```
params: `3861358557659396986, 1893966347987449989, 5184606887867710024, 7, probe_tbl, 4, 2, 1788334618980, 0, 0, 0, 1788396087532, {"location":"s3a://data-catalog-bucket/apiprofile1788334618_cat/probe_ns/probe_tbl/"}, {"last-sequence-number":"0","last-updated-ms":"1788396087510","next-row-id":"0","format-version":"2","metadata-location":"s3a://data-catalog-bucket/apiprofile1788334618_cat/probe_ns/probe_tbl/metadata/00003-d6fc32a8-4554-4198-bd45-7ab04f8d2fe7.metadata.json","table-uuid":"16534a69-4a1e-43ea-9d50-f60be0305a0a","default-sort-order-id":"0","last-partition-id":"999","parent-namespace":"probe_ns","current-schema-id":"0","location":"s3a://data-catalog-bucket/apiprofile1788334618_cat/probe_ns/probe_tbl","last-column-id":"2","default-spec-id":"0"}, 1, //data-catalog-bucket/apiprofile1788334618_cat/probe_ns/probe_tbl/, 3, 3861358557659396986, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[13]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 1893966347987449989, 5184606887867710024, 1893966347987449989, 3861358557659396986, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5, idx_entities · est. 1 row · cost 47.86
**[14]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `1893966347987449989, 3861358557659396986, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[15]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3861358557659396986, 7, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
### `iceberg.rename_table`

- `POST /v1/{cat}/tables/rename` → **200**
- wall 95 ms · 12 statements · 0 object ops · entity access: MIXED (batched 20% of 10 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, root`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.09 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9118527594773052894, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `9118527594773052894, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 4.88 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 9118527594773052894, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2, 0, 3340119121637991836, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using idx_entities, entities_pkey · est. 1 row · cost 16.22
**[5]** `entities` · SELECT · 0.10 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3340119121637991836, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `1893966347987449989, 5184606887867710024, 7, POLARIS, probe_tbl3`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[8]** `entities` · SELECT · 0.16 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 0, 0, 1893966347987449989, 5184606887867710024, 1893966347987449989, 8260655206039764610, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5, idx_entities ×2 · est. 2 rows · cost 52.19
**[9]** `entities` · SELECT · 0.11 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 8260655206039764610, 7, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[10]** `entities` · SELECT · 0.10 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `1893966347987449989, 5184606887867710024, 7, POLARIS, probe_tbl3`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[11]** `entities` · UPDATE · 0.14 ms

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE entity_version = ? AND id = ? AND catalog_id = ? AND realm_id = ?
```
params: `8260655206039764610, 1893966347987449989, 5184606887867710024, 7, probe_tbl3, 2, 2, 1788396086817, 0, 0, 0, 1788396087878, {"location":"s3a://data-catalog-bucket/apiprofile1788334618_cat/probe_ns/probe_tbl2/"}, {"last-updated-ms":"1788396086710","last-sequence-number":"0","next-row-id":"0","format-version":"2","metadata-location":"s3a://data-catalog-bucket/apiprofile1788334618_cat/probe_ns/probe_tbl2/metadata/00000-581ad81c-1621-4780-9277-a69b4dbd92dc.metadata.json","table-uuid":"f30d285d-e4d6-4faf-a293-fd7b79112833","default-sort-order-id":"0","last-partition-id":"999","parent-namespace":"probe_ns","current-schema-id":"0","location":"s3a://data-catalog-bucket/apiprofile1788334618_cat/probe_ns/probe_tbl2","last-column-id":"2","default-spec-id":"0"}, 1, //data-catalog-bucket/apiprofile1788334618_cat/probe_ns/probe_tbl2/, 1, 8260655206039764610, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
### `iceberg.report_metrics`

- `POST /v1/{cat}/.../tables/{tbl}/metrics` → **204**
- wall 33 ms · 7 statements · 0 object ops · entity access: MIXED (batched 17% of 6 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, root`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9118527594773052894, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `9118527594773052894, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 2.84 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 9118527594773052894, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2, 0, 3340119121637991836, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using idx_entities, entities_pkey · est. 1 row · cost 16.22
**[5]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3340119121637991836, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
### `iceberg.load_table[missing]`

- `GET /v1/{cat}/.../tables/{missing}` → **404**
- wall 50 ms · 9 statements · 0 object ops · entity access: MIXED (batched 25% of 8 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, root`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9118527594773052894, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `9118527594773052894, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 3.90 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 9118527594773052894, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2, 0, 3340119121637991836, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using idx_entities, entities_pkey · est. 1 row · cost 16.22
**[5]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3340119121637991836, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `1893966347987449989, 5184606887867710024, 7, POLARIS, does_not_exist`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[8]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 0, 0, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities ×2 · est. 2 rows · cost 44.34
### `iceberg.drop_table`

- `DELETE /v1/{cat}/namespaces/{ns}/tables/{tbl}` → **204**
- wall 78 ms · 17 statements · 0 object ops · entity access: MIXED (batched 22% of 9 reads)
- tables: entities, grant_records, policy_mapping_record

**[0]** `entities` · SELECT · 0.08 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, root`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9118527594773052894, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `9118527594773052894, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 5.16 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 9118527594773052894, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.10 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2, 0, 3340119121637991836, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using idx_entities, entities_pkey · est. 1 row · cost 16.22
**[5]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3340119121637991836, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `1893966347987449989, 5184606887867710024, 7, POLARIS, probe_tbl3`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[8]** `grant_records` · SELECT · 0.05 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_id = ? AND securable_catalog_id = ? AND realm_id = ?
```
params: `8260655206039764610, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 1 row · cost 8.44
**[9]** `entities` · SELECT · 0.17 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 0, 0, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities ×2 · est. 2 rows · cost 44.34
**[10]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 8260655206039764610, 7, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[11]** `entities` · DELETE · 0.05 ms

```sql
DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `8260655206039764610, POLARIS, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[12]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_id = ? AND securable_catalog_id = ? AND realm_id = ?
```
params: `8260655206039764610, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 1 row · cost 8.44
**[13]** `grant_records` · DELETE · 4.59 ms

```sql
DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (
    (grantee_id = ? AND grantee_catalog_id = ?) OR
    (securable_id = ? AND securable_catalog_id = ?)
) AND realm_id = ?
```
params: `8260655206039764610, 1893966347987449989, 8260655206039764610, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1941.34
**[14]** `policy_mapping_record` · SELECT · 0.02 ms

```sql
SELECT target_catalog_id, target_id, policy_type_code, policy_catalog_id, policy_id, parameters FROM POLARIS_SCHEMA.POLICY_MAPPING_RECORD WHERE target_id = ? AND target_catalog_id = ? AND realm_id = ?
```
params: `8260655206039764610, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Index Scan on policy_mapping_record using policy_mapping_record_pkey · est. 1 row · cost 8.17
**[15]** `policy_mapping_record` · DELETE · 0.01 ms

```sql
DELETE FROM POLARIS_SCHEMA.POLICY_MAPPING_RECORD WHERE target_catalog_id = ? AND target_id = ? AND realm_id = ?
```
params: `1893966347987449989, 8260655206039764610, POLARIS`

EXPLAIN (index absent) — Index Scan on policy_mapping_record using policy_mapping_record_pkey · est. 1 row · cost 8.17
**[16]** `grant_records` · SELECT · 0.04 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_id = $1 AND securable_catalog_id = $2 AND realm_id = $3 (grantee_id = $1 AND grantee_catalog_id = $2) OR (securable_id = $3 AND securable_catalog_id = $4) ) AND realm_id = $5 (grantee_id = $1 AND grantee_catalog_id = $2) OR (securable_id = $3 AND securable_catalog_id = $4) ) AND realm_id = $5
```
params: `$1 = '8260655206039764610', $2 = '1893966347987449989', $3 = '8260655206039764610', $4 = '1893966347987449989', $5 = 'POLARIS'`

EXPLAIN (index absent) — not planned: placeholder/parameter mismatch: SQL has 0 placeholders, 5 values captured
### `iceberg.create_view`

- `POST /v1/{cat}/namespaces/{ns}/views` → **200**
- wall 159 ms · 24 statements · 0 object ops · entity access: MIXED (batched 37% of 19 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.12 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, root`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9118527594773052894, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `9118527594773052894, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 4.10 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 9118527594773052894, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2, 0, 3340119121637991836, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using idx_entities, entities_pkey · est. 1 row · cost 16.22
**[5]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3340119121637991836, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `1893966347987449989, 5184606887867710024, 7, POLARIS, probe_view`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[8]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 0, 0, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities ×2 · est. 2 rows · cost 44.34
**[9]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `1893966347987449989, 5184606887867710024, 7, POLARIS, probe_view`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[10]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities · est. 1 row · cost 40.02
**[11]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `1893966347987449989, 5184606887867710024, 7, POLARIS, probe_view`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[12]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities · est. 1 row · cost 40.02
**[13]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `1893966347987449989, 5184606887867710024, 7, POLARIS, probe_view`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[14]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities · est. 1 row · cost 40.02
**[15]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND type_code = ? AND catalog_id = ? AND parent_id = ?
```
params: `POLARIS, 6, 1893966347987449989, 5184606887867710024`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[16]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND type_code = ? AND catalog_id = ? AND parent_id = ?
```
params: `POLARIS, 7, 1893966347987449989, 5184606887867710024`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[17]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 0, 0, 1893966347987449989, 5184606887867710024, 1893966347987449989, 3861358557659396986, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5, idx_entities ×2 · est. 2 rows · cost 52.19
**[18]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1893966347987449989, 4, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[19]** `entities` · INSERT · 0.10 ms

```sql
INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme, realm_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```
params: `2066276938509256129, 1893966347987449989, 5184606887867710024, 7, probe_view, 1, 3, 1788396089251, 0, 0, 0, 1788396089251, {}, {"metadata-location":"s3a://data-catalog-bucket/apiprofile1788334618_cat/probe_ns/probe_view/metadata/00000-1199dbe3-2373-494d-97ff-f53eb43da9a9.gz.metadata.json","parent-namespace":"probe_ns"}, 1, NULL, POLARIS`

EXPLAIN (index absent) — ModifyTable, Result · est. 0 rows · cost 0.01
**[20]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `1893966347987449989, 5184606887867710024, 7, POLARIS, probe_view`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[21]** `grant_records` · SELECT · 0.01 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_id = ? AND securable_catalog_id = ? AND realm_id = ?
```
params: `2066276938509256129, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 1 row · cost 8.44
**[22]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities · est. 1 row · cost 40.02
**[23]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1893966347987449989, 4, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
### `iceberg.list_views`

- `GET /v1/{cat}/namespaces/{ns}/views` → **200**
- wall 33 ms · 9 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, root`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9118527594773052894, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `9118527594773052894, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 4.38 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 9118527594773052894, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2, 0, 3340119121637991836, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using idx_entities, entities_pkey · est. 1 row · cost 16.22
**[5]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3340119121637991836, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.10 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 0, 0, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities ×2 · est. 2 rows · cost 44.34
**[8]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND sub_type_code = ? AND realm_id = ? AND parent_id = ? AND type_code = ?
```
params: `1893966347987449989, 3, POLARIS, 5184606887867710024, 7`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
### `iceberg.load_view`

- `GET /v1/{cat}/namespaces/{ns}/views/{view}` → **200**
- wall 73 ms · 10 statements · 0 object ops · entity access: MIXED (batched 44% of 9 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, root`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9118527594773052894, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `9118527594773052894, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 5.43 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 9118527594773052894, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.10 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2, 0, 3340119121637991836, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using idx_entities, entities_pkey · est. 1 row · cost 16.22
**[5]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3340119121637991836, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.08 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 0, 0, 1893966347987449989, 5184606887867710024, 1893966347987449989, 2066276938509256129, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5, idx_entities ×2 · est. 2 rows · cost 52.19
**[8]** `entities` · SELECT · 0.10 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 1893966347987449989, 5184606887867710024, 1893966347987449989, 2066276938509256129, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5, idx_entities · est. 1 row · cost 47.86
**[9]** `entities` · SELECT · 0.12 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 1893966347987449989, 5184606887867710024, 1893966347987449989, 2066276938509256129, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5, idx_entities · est. 1 row · cost 47.86
### `iceberg.head_view`

- `HEAD /v1/{cat}/namespaces/{ns}/views/{view}` → **204**
- wall 53 ms · 10 statements · 0 object ops · entity access: MIXED (batched 44% of 9 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.13 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, root`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9118527594773052894, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `9118527594773052894, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 3.60 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 9118527594773052894, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2, 0, 3340119121637991836, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using idx_entities, entities_pkey · est. 1 row · cost 16.22
**[5]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3340119121637991836, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 0, 0, 1893966347987449989, 5184606887867710024, 1893966347987449989, 2066276938509256129, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5, idx_entities ×2 · est. 2 rows · cost 52.19
**[8]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 1893966347987449989, 5184606887867710024, 1893966347987449989, 2066276938509256129, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5, idx_entities · est. 1 row · cost 47.86
**[9]** `entities` · SELECT · 0.10 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 1893966347987449989, 5184606887867710024, 1893966347987449989, 2066276938509256129, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5, idx_entities · est. 1 row · cost 47.86
### `iceberg.rename_view`

- `POST /v1/{cat}/views/rename` → **204**
- wall 53 ms · 12 statements · 0 object ops · entity access: MIXED (batched 20% of 10 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, root`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.13 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9118527594773052894, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `9118527594773052894, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 4.73 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 9118527594773052894, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2, 0, 3340119121637991836, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using idx_entities, entities_pkey · est. 1 row · cost 16.22
**[5]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3340119121637991836, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `1893966347987449989, 5184606887867710024, 7, POLARIS, probe_view2`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[8]** `entities` · SELECT · 0.08 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 0, 0, 1893966347987449989, 5184606887867710024, 1893966347987449989, 2066276938509256129, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5, idx_entities ×2 · est. 2 rows · cost 52.19
**[9]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2066276938509256129, 7, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[10]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `1893966347987449989, 5184606887867710024, 7, POLARIS, probe_view2`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[11]** `entities` · UPDATE · 0.10 ms

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE entity_version = ? AND id = ? AND catalog_id = ? AND realm_id = ?
```
params: `2066276938509256129, 1893966347987449989, 5184606887867710024, 7, probe_view2, 2, 3, 1788396089251, 0, 0, 0, 1788396090529, {}, {"metadata-location":"s3a://data-catalog-bucket/apiprofile1788334618_cat/probe_ns/probe_view/metadata/00000-1199dbe3-2373-494d-97ff-f53eb43da9a9.gz.metadata.json","parent-namespace":"probe_ns"}, 1, NULL, 1, 2066276938509256129, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
### `iceberg.drop_view`

- `DELETE /v1/{cat}/namespaces/{ns}/views/{view}` → **204**
- wall 98 ms · 16 statements · 0 object ops · entity access: MIXED (batched 22% of 9 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.15 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, root`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.11 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9118527594773052894, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `9118527594773052894, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 5.32 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 9118527594773052894, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2, 0, 3340119121637991836, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using idx_entities, entities_pkey · est. 1 row · cost 16.22
**[5]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.09 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3340119121637991836, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `1893966347987449989, 5184606887867710024, 7, POLARIS, probe_view2`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[8]** `grant_records` · SELECT · 0.03 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_id = ? AND securable_catalog_id = ? AND realm_id = ?
```
params: `2066276938509256129, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 1 row · cost 8.44
**[9]** `entities` · SELECT · 0.10 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 0, 0, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities ×2 · est. 2 rows · cost 44.34
**[10]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2066276938509256129, 7, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[11]** `entities` · DELETE · 0.10 ms

```sql
DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `2066276938509256129, POLARIS, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[12]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_id = ? AND securable_catalog_id = ? AND realm_id = ?
```
params: `2066276938509256129, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 1 row · cost 8.44
**[13]** `grant_records` · DELETE · 3.87 ms

```sql
DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (
    (grantee_id = ? AND grantee_catalog_id = ?) OR
    (securable_id = ? AND securable_catalog_id = ?)
) AND realm_id = ?
```
params: `2066276938509256129, 1893966347987449989, 2066276938509256129, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1941.34
**[14]** `entities` · INSERT · 0.13 ms

```sql
INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme, realm_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```
params: `3504843126461819587, 0, 0, 8, entityCleanup_2066276938509256129, 1, 0, 1788396090888, 0, 0, 0, 1788396090888, {"taskType":"1","data":"{\"catalogId\":1893966347987449989,\"id\":2066276938509256129,\"parentId\":5184606887867710024,\"typeCode\":7,\"name\":\"probe_view2\",\"entityVersion\":2,\"subTypeCode\":3,\"createTimestamp\":1788396089251,\"dropTimestamp\":0,\"purgeTimestamp\":0,\"toPurgeTimestamp\":0,\"lastUpdateTimestamp\":1788396090529,\"properties\":\"{}\",\"internalProperties\":\"{\\\"parent-namespace\\\": \\\"probe_ns\\\", \\\"metadata-location\\\": \\\"s3a://data-catalog-bucket/apiprofile1788334618_cat/probe_ns/probe_view/metadata/00000-1199dbe3-2373-494d-97ff-f53eb43da9a9.gz.metadata.json\\\"}\",\"grantRecordsVersion\":1}"}, {}, 1, NULL, POLARIS`

EXPLAIN (index absent) — ModifyTable, Result · est. 0 rows · cost 0.01
**[15]** `grant_records` · SELECT · 0.03 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_id = $1 AND securable_catalog_id = $2 AND realm_id = $3 (grantee_id = $1 AND grantee_catalog_id = $2) OR (securable_id = $3 AND securable_catalog_id = $4) ) AND realm_id = $5 (grantee_id = $1 AND grantee_catalog_id = $2) OR (securable_id = $3 AND securable_catalog_id = $4) ) AND realm_id = $5
```
params: `$1 = '2066276938509256129', $2 = '1893966347987449989', $3 = '2066276938509256129', $4 = '1893966347987449989', $5 = 'POLARIS'`

EXPLAIN (index absent) — not planned: placeholder/parameter mismatch: SQL has 0 placeholders, 5 values captured
### `mgmt.list_catalogs`

- `GET /v1/catalogs` → **200**
- wall 149 ms · 9 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, root`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9118527594773052894, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `9118527594773052894, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 4.31 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 9118527594773052894, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2, 0, 3340119121637991836, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using idx_entities, entities_pkey · est. 1 row · cost 16.22
**[5]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3340119121637991836, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey, idx_entities ×2 · est. 2 rows · cost 20.52
**[8]** `entities` · SELECT · 5.91 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND type_code = ? AND catalog_id = ? AND parent_id = ?
```
params: `POLARIS, 4, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 134 rows · cost 219.70
### `mgmt.get_catalog`

- `GET /v1/catalogs/{cat}` → **200**
- wall 41 ms · 8 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.10 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, root`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9118527594773052894, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `9118527594773052894, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 4.15 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 9118527594773052894, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2, 0, 3340119121637991836, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using idx_entities, entities_pkey · est. 1 row · cost 16.22
**[5]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3340119121637991836, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.09 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×3, idx_entities ×2 · est. 2 rows · cost 36.45
### `mgmt.create_principal`

- `POST /v1/principals` → **201**
- wall 141 ms · 14 statements · 0 object ops · entity access: MIXED (batched 22% of 9 reads)
- tables: entities, grant_records, principal_authentication_data

**[0]** `entities` · SELECT · 0.17 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, root`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9118527594773052894, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `9118527594773052894, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 3.42 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 9118527594773052894, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2, 0, 3340119121637991836, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using idx_entities, entities_pkey · est. 1 row · cost 16.22
**[5]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3340119121637991836, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, root`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[8]** `entities` · SELECT · 0.08 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey, idx_entities ×2 · est. 2 rows · cost 20.52
**[9]** `entities` · SELECT · 0.48 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 6455211835363501346, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[10]** `principal_authentication_data` · SELECT · 0.03 ms

```sql
SELECT principal_id, principal_client_id, main_secret_hash, secondary_secret_hash, secret_salt FROM POLARIS_SCHEMA.PRINCIPAL_AUTHENTICATION_DATA WHERE realm_id = ? AND principal_client_id = ?
```
params: `<redacted>`

_No EXPLAIN: parameters were redacted at capture (secret table), so this statement can never be replayed._
**[11]** `principal_authentication_data` · INSERT · 0.55 ms

```sql
INSERT INTO POLARIS_SCHEMA.PRINCIPAL_AUTHENTICATION_DATA (principal_id, principal_client_id, main_secret_hash, secondary_secret_hash, secret_salt, realm_id) VALUES (?, ?, ?, ?, ?, ?)
```
params: `<redacted>`

_No EXPLAIN: parameters were redacted at capture (secret table), so this statement can never be replayed._
**[12]** `entities` · INSERT · 0.15 ms

```sql
INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme, realm_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```
params: `6455211835363501346, 0, 0, 2, apiprofile1788334618_p, 1, 0, 1788396091985, 0, 0, 0, 1788396091985, {}, {"client_id":"1e797849c73dccdd"}, 1, NULL, POLARIS`

EXPLAIN (index absent) — ModifyTable, Result · est. 0 rows · cost 0.01
**[13]** `events` · INSERT · 2.69 ms

```sql
INSERT INTO POLARIS_SCHEMA.EVENTS (catalog_id, event_id, request_id, event_type, timestamp_ms, principal_name, resource_type, resource_identifier, additional_properties, realm_id) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
```
params: `$1 = 'apiprofile1788334618_cat', $2 = '40242e3a-8699-45cc-b53c-eeef3f258ed8', $3 = '560e5975-212b-490d-b4e4-fec6d57def61_0000000000000000016', $4 = 'AfterCreateTableEvent', $5 = '1788396086829', $6 = 'admin1_principal', $7 = 'TABLE', $8 = 'probe_ns.probe_tbl2', $9 = '{"metadata": "{\"format-version\":2,\"table-uuid\":\"f30d285d-e4d6-4faf-a293-fd7b79112833\",\"location\":\"s3a://data-catalog-bucket/apiprofile1788334618_cat/probe_ns/probe_tbl2\",\"last-sequence-number\":0,\"last-updated-ms\":1788396086710,\"last-column-id\":2,\"current-schema-id\":0,\"schemas\":[{\"type\":\"struct\",\"schema-id\":0,\"fields\":[{\"id\":1,\"name\":\"id\",\"required\":true,\"type\":\"long\"},{\"id\":2,\"name\":\"val\",\"required\":false,\"type\":\"string\"}]}],\"default-spec-id\":0,\"partition-specs\":[{\"spec-id\":0,\"fields\":[]}],\"last-partition-id\":999,\"default-sort-order-id\":0,\"sort-orders\":[{\"order-id\":0,\"fields\":[]}],\"properties\":{\"created-at\":\"2026-09-03T00:41:26.686067927Z\",\"write.parquet.compression-codec\":\"zstd\"},\"current-snapshot-id\":-1,\"refs\":{},\"snapshots\":[],\"statistics\":[],\"partition-statistics\":[],\"snapshot-log\":[],\"metadata-log\":[]}", "table-uuid": "f30d285d-e4d6-4faf-a293-fd7b79112833"}', $10 = 'POLARIS'`

EXPLAIN (index absent) — not planned: placeholder/parameter mismatch: SQL has 0 placeholders, 10 values captured
### `mgmt.get_principal`

- `GET /v1/principals/{p}` → **200**
- wall 33 ms · 11 statements · 0 object ops · entity access: MIXED (batched 25% of 8 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, root`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9118527594773052894, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `9118527594773052894, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 6.09 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 9118527594773052894, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2, 0, 3340119121637991836, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using idx_entities, entities_pkey · est. 1 row · cost 16.22
**[5]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3340119121637991836, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, apiprofile1788334618_p`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[8]** `grant_records` · SELECT · 2.51 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 6455211835363501346, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[9]** `grant_records` · SELECT · 4.10 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_id = ? AND securable_catalog_id = ? AND realm_id = ?
```
params: `6455211835363501346, 0, POLARIS`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 20 rows · cost 14.11
**[10]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey, idx_entities ×2 · est. 2 rows · cost 20.52
### `mgmt.list_principals`

- `GET /v1/principals` → **200**
- wall 42 ms · 9 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, root`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9118527594773052894, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `9118527594773052894, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 3.54 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 9118527594773052894, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2, 0, 3340119121637991836, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using idx_entities, entities_pkey · est. 1 row · cost 16.22
**[5]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3340119121637991836, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey, idx_entities ×2 · est. 2 rows · cost 20.52
**[8]** `entities` · SELECT · 1.76 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND sub_type_code = ? AND realm_id = ? AND parent_id = ? AND type_code = ?
```
params: `0, 0, POLARIS, 0, 2`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 111 rows · cost 220.03
### `mgmt.create_principal_role`

- `POST /v1/principal-roles` → **201**
- wall 73 ms · 9 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.15 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, root`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.11 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9118527594773052894, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `9118527594773052894, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 5.38 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 9118527594773052894, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.08 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2, 0, 3340119121637991836, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using idx_entities, entities_pkey · est. 1 row · cost 16.22
**[5]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3340119121637991836, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey, idx_entities ×2 · est. 2 rows · cost 20.52
**[8]** `entities` · INSERT · 0.24 ms

```sql
INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme, realm_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```
params: `4364022827039256756, 0, 0, 3, apiprofile1788334618_pr, 1, 0, 1788396092916, 0, 0, 0, 1788396092916, {}, {}, 1, NULL, POLARIS`

EXPLAIN (index absent) — ModifyTable, Result · est. 0 rows · cost 0.01
### `mgmt.get_principal_role`

- `GET /v1/principal-roles/{r}` → **200**
- wall 99 ms · 11 statements · 0 object ops · entity access: MIXED (batched 25% of 8 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.09 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, root`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9118527594773052894, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `9118527594773052894, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 61.17 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 9118527594773052894, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 1.09 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2, 0, 3340119121637991836, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using idx_entities, entities_pkey · est. 1 row · cost 16.22
**[5]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3340119121637991836, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 3, POLARIS, apiprofile1788334618_pr`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[8]** `grant_records` · SELECT · 2.68 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 4364022827039256756, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[9]** `grant_records` · SELECT · 0.80 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_id = ? AND securable_catalog_id = ? AND realm_id = ?
```
params: `4364022827039256756, 0, POLARIS`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 20 rows · cost 14.11
**[10]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey, idx_entities ×2 · est. 2 rows · cost 20.52
### `mgmt.list_principal_roles`

- `GET /v1/principal-roles` → **200**
- wall 35 ms · 9 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, root`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9118527594773052894, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `9118527594773052894, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 2.63 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 9118527594773052894, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2, 0, 3340119121637991836, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using idx_entities, entities_pkey · est. 1 row · cost 16.22
**[5]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3340119121637991836, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey, idx_entities ×2 · est. 2 rows · cost 20.52
**[8]** `entities` · SELECT · 0.97 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND sub_type_code = ? AND realm_id = ? AND parent_id = ? AND type_code = ?
```
params: `0, 0, POLARIS, 0, 3`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 111 rows · cost 220.03
### `mgmt.assign_principal_role`

- `PUT /v1/principals/{p}/principal-roles` → **201**
- wall 74 ms · 13 statements · 0 object ops · entity access: MIXED (batched 22% of 9 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.17 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, root`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.08 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9118527594773052894, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `9118527594773052894, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 3.34 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 9118527594773052894, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2, 0, 3340119121637991836, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using idx_entities, entities_pkey · est. 1 row · cost 16.22
**[5]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3340119121637991836, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.09 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 4364022827039256756, 0, 6455211835363501346, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×3, idx_entities ×2 · est. 2 rows · cost 36.41
**[8]** `grant_records` · INSERT · 0.68 ms

```sql
INSERT INTO POLARIS_SCHEMA.GRANT_RECORDS (securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code, realm_id) VALUES (?, ?, ?, ?, ?, ?)
```
params: `0, 4364022827039256756, 0, 6455211835363501346, 4, POLARIS`

EXPLAIN (index absent) — ModifyTable, Result · est. 0 rows · cost 0.01
**[9]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 6455211835363501346, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[10]** `entities` · UPDATE · 0.11 ms

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE entity_version = ? AND id = ? AND catalog_id = ? AND realm_id = ?
```
params: `6455211835363501346, 0, 0, 2, apiprofile1788334618_p, 1, 0, 1788396091985, 0, 0, 0, 1788396091985, {}, {"client_id": "1e797849c73dccdd"}, 2, NULL, 1, 6455211835363501346, 0, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[11]** `entities` · SELECT · 0.14 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 4364022827039256756, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[12]** `entities` · UPDATE · 0.07 ms

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE entity_version = ? AND id = ? AND catalog_id = ? AND realm_id = ?
```
params: `4364022827039256756, 0, 0, 3, apiprofile1788334618_pr, 1, 0, 1788396092916, 0, 0, 0, 1788396092916, {}, {}, 2, NULL, 1, 4364022827039256756, 0, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
### `mgmt.create_catalog_role`

- `POST /v1/catalogs/{cat}/catalog-roles` → **201**
- wall 59 ms · 9 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, root`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9118527594773052894, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `9118527594773052894, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 4.37 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 9118527594773052894, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2, 0, 3340119121637991836, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using idx_entities, entities_pkey · est. 1 row · cost 16.22
**[5]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3340119121637991836, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.09 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×3, idx_entities ×2 · est. 2 rows · cost 36.45
**[8]** `entities` · INSERT · 0.10 ms

```sql
INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme, realm_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```
params: `1939194019676480001, 1893966347987449989, 1893966347987449989, 5, apiprofile1788334618_cr, 1, 0, 1788396094228, 0, 0, 0, 1788396094228, {}, {}, 1, NULL, POLARIS`

EXPLAIN (index absent) — ModifyTable, Result · est. 0 rows · cost 0.01
### `mgmt.list_catalog_roles`

- `GET /v1/catalogs/{cat}/catalog-roles` → **200**
- wall 27 ms · 9 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, root`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9118527594773052894, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `9118527594773052894, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 3.38 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 9118527594773052894, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2, 0, 3340119121637991836, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using idx_entities, entities_pkey · est. 1 row · cost 16.22
**[5]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3340119121637991836, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×3, idx_entities ×2 · est. 2 rows · cost 36.45
**[8]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND sub_type_code = ? AND realm_id = ? AND parent_id = ? AND type_code = ?
```
params: `1893966347987449989, 0, POLARIS, 1893966347987449989, 5`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
### `mgmt.assign_catalog_role`

- `PUT /v1/principal-roles/{r}/catalog-roles/{cat}` → **201**
- wall 87 ms · 20 statements · 0 object ops · entity access: MIXED (batched 33% of 12 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.16 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, root`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.08 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9118527594773052894, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `9118527594773052894, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 4.79 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 9118527594773052894, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2, 0, 3340119121637991836, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using idx_entities, entities_pkey · est. 1 row · cost 16.22
**[5]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3340119121637991836, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `1893966347987449989, 1893966347987449989, 5, POLARIS, apiprofile1788334618_cr`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[8]** `grant_records` · SELECT · 4.74 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `1893966347987449989, 1939194019676480001, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[9]** `grant_records` · SELECT · 0.04 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_id = ? AND securable_catalog_id = ? AND realm_id = ?
```
params: `1939194019676480001, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 1 row · cost 8.44
**[10]** `entities` · SELECT · 0.11 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 0, 4364022827039256756, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities ×2 · est. 2 rows · cost 44.34
**[11]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 4364022827039256756, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[12]** `grant_records` · SELECT · 4.30 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 4364022827039256756, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[13]** `grant_records` · SELECT · 0.03 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_id = ? AND securable_catalog_id = ? AND realm_id = ?
```
params: `4364022827039256756, 0, POLARIS`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 20 rows · cost 14.11
**[14]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `1893966347987449989, 5184463786878295939, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[15]** `grant_records` · INSERT · 0.12 ms

```sql
INSERT INTO POLARIS_SCHEMA.GRANT_RECORDS (securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code, realm_id) VALUES (?, ?, ?, ?, ?, ?)
```
params: `1893966347987449989, 1939194019676480001, 0, 4364022827039256756, 3, POLARIS`

EXPLAIN (index absent) — ModifyTable, Result · est. 0 rows · cost 0.01
**[16]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 4364022827039256756, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[17]** `entities` · UPDATE · 0.09 ms

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE entity_version = ? AND id = ? AND catalog_id = ? AND realm_id = ?
```
params: `4364022827039256756, 0, 0, 3, apiprofile1788334618_pr, 1, 0, 1788396092916, 0, 0, 0, 1788396092916, {}, {}, 3, NULL, 1, 4364022827039256756, 0, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[18]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1939194019676480001, 5, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[19]** `entities` · UPDATE · 0.05 ms

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE entity_version = ? AND id = ? AND catalog_id = ? AND realm_id = ?
```
params: `1939194019676480001, 1893966347987449989, 1893966347987449989, 5, apiprofile1788334618_cr, 1, 0, 1788396094228, 0, 0, 0, 1788396094228, {}, {}, 2, NULL, 1, 1939194019676480001, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
### `mgmt.grant_privilege`

- `PUT /v1/catalogs/{cat}/catalog-roles/{cr}/grants` → **201**
- wall 204 ms · 26 statements · 0 object ops · entity access: MIXED (batched 28% of 18 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, root`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.13 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9118527594773052894, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `9118527594773052894, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 3.90 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 9118527594773052894, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.09 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2, 0, 3340119121637991836, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using idx_entities, entities_pkey · est. 1 row · cost 16.22
**[5]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3340119121637991836, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.15 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 0, 0, 1893966347987449989, 1939194019676480001, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities ×2 · est. 2 rows · cost 44.34
**[8]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `1893966347987449989, 1939194019676480001, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[9]** `grant_records` · SELECT · 4.23 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `1893966347987449989, 1939194019676480001, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[10]** `grant_records` · SELECT · 0.04 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_id = ? AND securable_catalog_id = ? AND realm_id = ?
```
params: `1939194019676480001, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 1 row · cost 8.44
**[11]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `1939194019676480001, POLARIS, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[12]** `grant_records` · SELECT · 3.69 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `1893966347987449989, 1939194019676480001, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[13]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, root`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[14]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9118527594773052894, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[15]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `9118527594773052894, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[16]** `grant_records` · SELECT · 3.02 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 9118527594773052894, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[17]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2, 0, 3340119121637991836, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using idx_entities, entities_pkey · est. 1 row · cost 16.22
**[18]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[19]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3340119121637991836, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[20]** `entities` · SELECT · 0.15 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 0, 0, 1893966347987449989, 1939194019676480001, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities ×2 · est. 2 rows · cost 44.34
**[21]** `grant_records` · INSERT · 0.11 ms

```sql
INSERT INTO POLARIS_SCHEMA.GRANT_RECORDS (securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code, realm_id) VALUES (?, ?, ?, ?, ?, ?)
```
params: `0, 1893966347987449989, 1893966347987449989, 1939194019676480001, 20, POLARIS`

EXPLAIN (index absent) — ModifyTable, Result · est. 0 rows · cost 0.01
**[22]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1939194019676480001, 5, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[23]** `entities` · UPDATE · 0.08 ms

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE entity_version = ? AND id = ? AND catalog_id = ? AND realm_id = ?
```
params: `1939194019676480001, 1893966347987449989, 1893966347987449989, 5, apiprofile1788334618_cr, 1, 0, 1788396094228, 0, 0, 0, 1788396094228, {}, {}, 3, NULL, 1, 1939194019676480001, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[24]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1893966347987449989, 4, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[25]** `entities` · UPDATE · 0.08 ms

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE entity_version = ? AND id = ? AND catalog_id = ? AND realm_id = ?
```
params: `1893966347987449989, 0, 0, 4, apiprofile1788334618_cat, 1, 0, 1788334618325, 0, 0, 0, 1788334618325, {"default-base-location": "s3a://data-catalog-bucket/apiprofile1788334618_cat/", "polaris.config.drop-with-purge.enabled": "true"}, {"catalogType": "INTERNAL", "storage_configuration_info": "{\"@type\":\"AwsStorageConfigurationInfo\",\"allowedLocations\":[\"s3a://data-catalog-bucket/apiprofile1788334618_cat/\",\"s3a://data-catalog-bucket/\"],\"endpoint\":\"http://192.168.139.2:9000\",\"endpointInternal\":\"http://192.168.139.2:9000\",\"pathStyleAccess\":true,\"storageType\":\"S3\",\"fileIoImplClassName\":\"org.apache.iceberg.aws.s3.S3FileIO\"}"}, 34, NULL, 1, 1893966347987449989, 0, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
### `mgmt.list_grants`

- `GET /v1/catalogs/{cat}/catalog-roles/{cr}/grants` → **200**
- wall 57 ms · 16 statements · 0 object ops · entity access: MIXED (batched 45% of 11 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, root`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9118527594773052894, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `9118527594773052894, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 5.22 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 9118527594773052894, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.09 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2, 0, 3340119121637991836, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using idx_entities, entities_pkey · est. 1 row · cost 16.22
**[5]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3340119121637991836, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.11 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 0, 0, 1893966347987449989, 1939194019676480001, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities ×2 · est. 2 rows · cost 44.34
**[8]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[9]** `grant_records` · SELECT · 0.05 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_id = ? AND securable_catalog_id = ? AND realm_id = ?
```
params: `1893966347987449989, 0, POLARIS`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 20 rows · cost 14.11
**[10]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `1893966347987449989, 1939194019676480001, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[11]** `grant_records` · SELECT · 3.51 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `1893966347987449989, 1939194019676480001, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[12]** `grant_records` · SELECT · 0.03 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_id = ? AND securable_catalog_id = ? AND realm_id = ?
```
params: `1939194019676480001, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 1 row · cost 8.44
**[13]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `1939194019676480001, POLARIS, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[14]** `grant_records` · SELECT · 3.15 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `1893966347987449989, 1939194019676480001, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[15]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
### `mgmt.list_principals_for_principal_role`

- `GET /v1/principal-roles/{r}/principals` → **200**
- wall 74 ms · 14 statements · 0 object ops · entity access: MIXED (batched 40% of 10 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 1.30 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, root`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.08 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9118527594773052894, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `9118527594773052894, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 5.14 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 9118527594773052894, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.08 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2, 0, 3340119121637991836, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using idx_entities, entities_pkey · est. 1 row · cost 16.22
**[5]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3340119121637991836, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.08 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 4364022827039256756, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×2, idx_entities ×2 · est. 2 rows · cost 28.49
**[8]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 4364022827039256756, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[9]** `grant_records` · SELECT · 4.00 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 4364022827039256756, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[10]** `grant_records` · SELECT · 0.04 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_id = ? AND securable_catalog_id = ? AND realm_id = ?
```
params: `4364022827039256756, 0, POLARIS`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 20 rows · cost 14.11
**[11]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `4364022827039256756, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[12]** `grant_records` · SELECT · 0.02 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_id = ? AND securable_catalog_id = ? AND realm_id = ?
```
params: `4364022827039256756, 0, POLARIS`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 20 rows · cost 14.11
**[13]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 6455211835363501346, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
### `mgmt.reset_principal_credentials`

- `POST /v1/principals/{p}/reset` → **403**
- wall 31 ms · 11 statements · 0 object ops · entity access: MIXED (batched 38% of 8 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, root`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9118527594773052894, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `9118527594773052894, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 2.63 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 9118527594773052894, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2, 0, 3340119121637991836, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using idx_entities, entities_pkey · est. 1 row · cost 16.22
**[5]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3340119121637991836, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 6455211835363501346, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×2, idx_entities ×2 · est. 2 rows · cost 28.49
**[8]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 6455211835363501346, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[9]** `grant_records` · SELECT · 2.65 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 6455211835363501346, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[10]** `grant_records` · SELECT · 0.02 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_id = ? AND securable_catalog_id = ? AND realm_id = ?
```
params: `6455211835363501346, 0, POLARIS`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 20 rows · cost 14.11
### `mgmt.delete_catalog_role`

- `DELETE /v1/catalogs/{cat}/catalog-roles/{cr}` → **204**
- wall 82 ms · 18 statements · 0 object ops · entity access: MIXED (batched 33% of 9 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.12 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, root`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9118527594773052894, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `9118527594773052894, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 5.39 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 9118527594773052894, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2, 0, 3340119121637991836, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using idx_entities, entities_pkey · est. 1 row · cost 16.22
**[5]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3340119121637991836, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.10 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 1893966347987449989, 1893966347987449989, 5184463786878295939, 0, 0, 1893966347987449989, 1939194019676480001, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities ×2 · est. 2 rows · cost 44.34
**[8]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 1939194019676480001, 5, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[9]** `entities` · DELETE · 0.06 ms

```sql
DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `1939194019676480001, POLARIS, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[10]** `grant_records` · SELECT · 3.92 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `1893966347987449989, 1939194019676480001, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[11]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_id = ? AND securable_catalog_id = ? AND realm_id = ?
```
params: `1939194019676480001, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 1 row · cost 8.44
**[12]** `grant_records` · DELETE · 5.39 ms

```sql
DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (
    (grantee_id = ? AND grantee_catalog_id = ?) OR
    (securable_id = ? AND securable_catalog_id = ?)
) AND realm_id = ?
```
params: `1939194019676480001, 1893966347987449989, 1939194019676480001, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1941.34
**[13]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 1893966347987449989, 0, 4364022827039256756, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×2 · est. 1 row · cost 16.21
**[14]** `entities` · UPDATE · 0.08 ms

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE entity_version = ? AND id = ? AND catalog_id = ? AND realm_id = ?
```
params: `1893966347987449989, 0, 0, 4, apiprofile1788334618_cat, 1, 0, 1788334618325, 0, 0, 0, 1788334618325, {"default-base-location": "s3a://data-catalog-bucket/apiprofile1788334618_cat/", "polaris.config.drop-with-purge.enabled": "true"}, {"catalogType": "INTERNAL", "storage_configuration_info": "{\"@type\":\"AwsStorageConfigurationInfo\",\"allowedLocations\":[\"s3a://data-catalog-bucket/apiprofile1788334618_cat/\",\"s3a://data-catalog-bucket/\"],\"endpoint\":\"http://192.168.139.2:9000\",\"endpointInternal\":\"http://192.168.139.2:9000\",\"pathStyleAccess\":true,\"storageType\":\"S3\",\"fileIoImplClassName\":\"org.apache.iceberg.aws.s3.S3FileIO\"}"}, 35, NULL, 1, 1893966347987449989, 0, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[15]** `entities` · UPDATE · 0.05 ms

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE entity_version = ? AND id = ? AND catalog_id = ? AND realm_id = ?
```
params: `4364022827039256756, 0, 0, 3, apiprofile1788334618_pr, 1, 0, 1788396092916, 0, 0, 0, 1788396092916, {}, {}, 4, NULL, 1, 4364022827039256756, 0, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[16]** `entities` · INSERT · 0.14 ms

```sql
INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme, realm_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```
params: `3562748079199653196, 0, 0, 8, entityCleanup_1939194019676480001, 1, 0, 1788396096606, 0, 0, 0, 1788396096606, {"taskType":"1","data":"{\"catalogId\":1893966347987449989,\"id\":1939194019676480001,\"parentId\":1893966347987449989,\"typeCode\":5,\"name\":\"apiprofile1788334618_cr\",\"entityVersion\":1,\"subTypeCode\":0,\"createTimestamp\":1788396094228,\"dropTimestamp\":0,\"purgeTimestamp\":0,\"toPurgeTimestamp\":0,\"lastUpdateTimestamp\":1788396094228,\"properties\":\"{}\",\"internalProperties\":\"{}\",\"grantRecordsVersion\":3}"}, {}, 1, NULL, POLARIS`

EXPLAIN (index absent) — ModifyTable, Result · est. 0 rows · cost 0.01
**[17]** `grant_records` · SELECT · 0.03 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_id = $1 AND securable_catalog_id = $2 AND realm_id = $3 (grantee_id = $1 AND grantee_catalog_id = $2) OR (securable_id = $3 AND securable_catalog_id = $4) ) AND realm_id = $5 (grantee_id = $1 AND grantee_catalog_id = $2) OR (securable_id = $3 AND securable_catalog_id = $4) ) AND realm_id = $5
```
params: `$1 = '1939194019676480001', $2 = '1893966347987449989', $3 = '1939194019676480001', $4 = '1893966347987449989', $5 = 'POLARIS'`

EXPLAIN (index absent) — not planned: placeholder/parameter mismatch: SQL has 0 placeholders, 5 values captured
### `mgmt.delete_principal_role`

- `DELETE /v1/principal-roles/{r}` → **204**
- wall 89 ms · 20 statements · 0 object ops · entity access: MIXED (batched 40% of 10 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.52 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, root`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.14 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9118527594773052894, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `9118527594773052894, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 4.78 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 9118527594773052894, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2, 0, 3340119121637991836, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using idx_entities, entities_pkey · est. 1 row · cost 16.22
**[5]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3340119121637991836, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 4364022827039256756, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×2, idx_entities ×2 · est. 2 rows · cost 28.49
**[8]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 4364022827039256756, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[9]** `grant_records` · SELECT · 4.62 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 4364022827039256756, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[10]** `grant_records` · SELECT · 0.04 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_id = ? AND securable_catalog_id = ? AND realm_id = ?
```
params: `4364022827039256756, 0, POLARIS`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 20 rows · cost 14.11
**[11]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 4364022827039256756, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[12]** `entities` · DELETE · 0.05 ms

```sql
DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `4364022827039256756, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[13]** `grant_records` · SELECT · 3.59 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 4364022827039256756, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[14]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_id = ? AND securable_catalog_id = ? AND realm_id = ?
```
params: `4364022827039256756, 0, POLARIS`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 20 rows · cost 14.11
**[15]** `grant_records` · DELETE · 3.81 ms

```sql
DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (
    (grantee_id = ? AND grantee_catalog_id = ?) OR
    (securable_id = ? AND securable_catalog_id = ?)
) AND realm_id = ?
```
params: `4364022827039256756, 0, 4364022827039256756, 0, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 21 rows · cost 1941.34
**[16]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 6455211835363501346, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[17]** `entities` · UPDATE · 0.04 ms

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE entity_version = ? AND id = ? AND catalog_id = ? AND realm_id = ?
```
params: `6455211835363501346, 0, 0, 2, apiprofile1788334618_p, 1, 0, 1788396091985, 0, 0, 0, 1788396091985, {}, {"client_id": "1e797849c73dccdd"}, 3, NULL, 1, 6455211835363501346, 0, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[18]** `entities` · INSERT · 1.07 ms

```sql
INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme, realm_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```
params: `2945024548552292786, 0, 0, 8, entityCleanup_4364022827039256756, 1, 0, 1788396096956, 0, 0, 0, 1788396096956, {"taskType":"1","data":"{\"catalogId\":0,\"id\":4364022827039256756,\"parentId\":0,\"typeCode\":3,\"name\":\"apiprofile1788334618_pr\",\"entityVersion\":1,\"subTypeCode\":0,\"createTimestamp\":1788396092916,\"dropTimestamp\":0,\"purgeTimestamp\":0,\"toPurgeTimestamp\":0,\"lastUpdateTimestamp\":1788396092916,\"properties\":\"{}\",\"internalProperties\":\"{}\",\"grantRecordsVersion\":4}"}, {}, 1, NULL, POLARIS`

EXPLAIN (index absent) — ModifyTable, Result · est. 0 rows · cost 0.01
**[19]** `grant_records` · SELECT · 0.06 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_id = $1 AND securable_catalog_id = $2 AND realm_id = $3 (grantee_id = $1 AND grantee_catalog_id = $2) OR (securable_id = $3 AND securable_catalog_id = $4) ) AND realm_id = $5 (grantee_id = $1 AND grantee_catalog_id = $2) OR (securable_id = $3 AND securable_catalog_id = $4) ) AND realm_id = $5
```
params: `$1 = '4364022827039256756', $2 = '0', $3 = '4364022827039256756', $4 = '0', $5 = 'POLARIS'`

EXPLAIN (index absent) — not planned: placeholder/parameter mismatch: SQL has 0 placeholders, 5 values captured
### `mgmt.delete_principal`

- `DELETE /v1/principals/{p}` → **204**
- wall 41 ms · 18 statements · 0 object ops · entity access: MIXED (batched 33% of 9 reads)
- tables: entities, grant_records, principal_authentication_data

**[0]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND type_code = ? AND realm_id = ? AND name = ?
```
params: `0, 0, 2, POLARIS, root`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 9118527594773052894, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `9118527594773052894, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 2.71 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 9118527594773052894, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 2, 0, 3340119121637991836, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using idx_entities, entities_pkey · est. 1 row · cost 16.22
**[5]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 2, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 3340119121637991836, 3, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 9118527594773052894, 0, 2, 0, 6455211835363501346, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×2, idx_entities ×2 · est. 2 rows · cost 28.49
**[8]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 6455211835363501346, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[9]** `grant_records` · SELECT · 2.39 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 6455211835363501346, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[10]** `grant_records` · SELECT · 0.01 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_id = ? AND securable_catalog_id = ? AND realm_id = ?
```
params: `6455211835363501346, 0, POLARIS`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 20 rows · cost 14.11
**[11]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```
params: `POLARIS, 6455211835363501346, 2, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[12]** `entities` · DELETE · 0.03 ms

```sql
DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `6455211835363501346, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[13]** `grant_records` · SELECT · 2.31 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```
params: `0, 6455211835363501346, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[14]** `grant_records` · SELECT · no timing

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_id = ? AND securable_catalog_id = ? AND realm_id = ?
```
params: `6455211835363501346, 0, POLARIS`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 20 rows · cost 14.11
**[15]** `grant_records` · DELETE · 3.61 ms

```sql
DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE (
    (grantee_id = ? AND grantee_catalog_id = ?) OR
    (securable_id = ? AND securable_catalog_id = ?)
) AND realm_id = ?
```
params: `6455211835363501346, 0, 6455211835363501346, 0, POLARIS`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 21 rows · cost 1941.34
**[16]** `principal_authentication_data` · DELETE · 0.11 ms

```sql
DELETE FROM POLARIS_SCHEMA.PRINCIPAL_AUTHENTICATION_DATA WHERE principal_id = ? AND principal_client_id = ? AND realm_id = ?
```
params: `<redacted>`

_No EXPLAIN: parameters were redacted at capture (secret table), so this statement can never be replayed._
**[17]** `grant_records` · SELECT · 0.02 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_id = $1 AND securable_catalog_id = $2 AND realm_id = $3 (grantee_id = $1 AND grantee_catalog_id = $2) OR (securable_id = $3 AND securable_catalog_id = $4) ) AND realm_id = $5
```
params: `$1 = '6455211835363501346', $2 = '0', $3 = '6455211835363501346', $4 = '0', $5 = 'POLARIS'`

EXPLAIN (index absent) — not planned: placeholder/parameter mismatch: SQL has 0 placeholders, 5 values captured
