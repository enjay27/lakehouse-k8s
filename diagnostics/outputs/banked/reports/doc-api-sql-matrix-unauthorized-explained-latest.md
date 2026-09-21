# API → SQL → MinIO Access Matrix

Generated 2026-09-02 17:18 from a live local run — Polaris 1.3.0-incubating, realm POLARIS.

**Identity case: `unauthorized`**.

Every plan and every refusal below is a statement about THIS caller. A 403 here is a measurement, not a gap: it still pays the full authorization prelude, including the `grant_records` grantee lookup, before the decision is made.

R = read, W = write, RW = both.

## API → PostgreSQL tables

| API | entities | grant_records |
|---|---|---|
| `iceberg.commit_table` | R | R |
| `iceberg.create_namespace` | R | R |
| `iceberg.create_table` | R | R |
| `iceberg.create_view` | R | R |
| `iceberg.drop_namespace` | R | R |
| `iceberg.drop_table` | R | R |
| `iceberg.drop_view` | R | R |
| `iceberg.get_config` | R | R |
| `iceberg.head_namespace` | R | R |
| `iceberg.head_table` | R | R |
| `iceberg.head_view` | R | R |
| `iceberg.list_namespaces` | R | R |
| `iceberg.list_tables` | R | R |
| `iceberg.list_views` | R | R |
| `iceberg.load_namespace` | R | R |
| `iceberg.load_table` | R | R |
| `iceberg.load_table[missing]` | R | R |
| `iceberg.load_table[snapshots=refs]` | R | R |
| `iceberg.load_view` | R | R |
| `iceberg.rename_table` | R | R |
| `iceberg.rename_view` | R | R |
| `iceberg.report_metrics` | R | R |
| `iceberg.stage_create_table` | R | R |
| `iceberg.update_namespace_properties` | R | R |
| `mgmt.assign_catalog_role` | R | R |
| `mgmt.assign_principal_role` | R | R |
| `mgmt.create_catalog_role` | R | R |
| `mgmt.create_principal` | R | R |
| `mgmt.create_principal_role` | R | R |
| `mgmt.delete_catalog_role` | R | R |
| `mgmt.delete_principal` | R | R |
| `mgmt.delete_principal_role` | R | R |
| `mgmt.get_catalog` | R | R |
| `mgmt.get_principal` | R | R |
| `mgmt.get_principal_role` | R | R |
| `mgmt.grant_privilege` | R | R |
| `mgmt.list_catalog_roles` | R | R |
| `mgmt.list_catalogs` | R | R |
| `mgmt.list_grants` | R | R |
| `mgmt.list_principal_roles` | R | R |
| `mgmt.list_principals` | R | R |
| `mgmt.list_principals_for_principal_role` | R | R |
| `mgmt.reset_principal_credentials` | R | R |

## Per-API detail

### `iceberg.get_config`

- `GET /v1/config` → **200**
- wall 101 ms · 14 statements · 0 object ops · entity access: MIXED (batched 12% of 8 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 4.84 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, zerograve_principal, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `grant_records` · SELECT · 2.41 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[8]** `grant_records` · SELECT · 0.02 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 20 rows · cost 14.11
**[9]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `3, POLARIS, zerograve_principal_role, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[10]** `grant_records` · SELECT · 2.32 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `3100973897112954937, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[11]** `grant_records` · SELECT · 0.04 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 20 rows · cost 14.11
**[12]** `entities` · SELECT · 1.56 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `4, POLARIS, apiprofile1788334618_cat, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[13]** `grant_records` · SELECT · 0.03 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `0, POLARIS, 1893966347987449989`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 20 rows · cost 14.11
### `iceberg.list_namespaces`

- `GET /v1/{cat}/namespaces` → **403**
- wall 57 ms · 7 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 3.11 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, 0, 1893966347987449989, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×3, idx_entities · est. 2 rows · cost 32.10
### `iceberg.load_namespace`

- `GET /v1/{cat}/namespaces/{ns}` → **403**
- wall 55 ms · 9 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.09 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.09 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 4.54 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `6, POLARIS, probe_ns, 1893966347987449989, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `grant_records` · SELECT · 0.03 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `1893966347987449989, POLARIS, 5184606887867710024`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 1 row · cost 8.44
**[8]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, 0, 1893966347987449989, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×3, idx_entities · est. 2 rows · cost 32.10
### `iceberg.head_namespace`

- `HEAD /v1/{cat}/namespaces/{ns}` → **403**
- wall 42 ms · 7 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.08 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.13 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 5.06 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, 0, 1893966347987449989, 0, 0, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities · est. 2 rows · cost 40.02
### `iceberg.update_namespace_properties`

- `POST /v1/{cat}/namespaces/{ns}/properties` → **403**
- wall 69 ms · 7 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.21 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.11 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.10 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 6.25 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.08 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, 0, 1893966347987449989, 0, 0, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities · est. 2 rows · cost 40.02
### `iceberg.create_namespace`

- `POST /v1/{cat}/namespaces` → **403**
- wall 56 ms · 8 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.17 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.14 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.11 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 5.80 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `6, POLARIS, probe_ns_tmp, 1893966347987449989, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, 0, 1893966347987449989, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×3, idx_entities · est. 2 rows · cost 32.10
### `iceberg.drop_namespace`

- `DELETE /v1/{cat}/namespaces/{ns}` → **404**
- wall 28 ms · 8 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 3.63 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `6, POLARIS, probe_ns_tmp, 1893966347987449989, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, 0, 1893966347987449989, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×3, idx_entities · est. 2 rows · cost 32.10
### `iceberg.list_tables`

- `GET /v1/{cat}/namespaces/{ns}/tables` → **403**
- wall 55 ms · 7 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.14 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.19 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.09 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 5.93 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, 0, 1893966347987449989, 0, 0, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities · est. 2 rows · cost 40.02
### `iceberg.load_table`

- `GET /v1/{cat}/namespaces/{ns}/tables/{tbl}` → **403**
- wall 57 ms · 9 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.19 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.08 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.10 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 5.48 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `7, POLARIS, probe_tbl, 1893966347987449989, 5184606887867710024`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `grant_records` · SELECT · 0.04 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```
params: `1893966347987449989, POLARIS, 3861358557659396986`

EXPLAIN (index absent) — Index Only Scan on grant_records using grant_records_pkey · est. 1 row · cost 8.44
**[8]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, 0, 1893966347987449989, 0, 0, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities · est. 2 rows · cost 40.02
### `iceberg.load_table[snapshots=refs]`

- `GET /v1/{cat}/.../tables/{tbl}?snapshots=refs` → **403**
- wall 34 ms · 7 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.10 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 5.58 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, 0, 1893966347987449989, 0, 0, 1893966347987449989, 5184606887867710024, 1893966347987449989, 3861358557659396986, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5, idx_entities · est. 2 rows · cost 47.86
### `iceberg.head_table`

- `HEAD /v1/{cat}/namespaces/{ns}/tables/{tbl}` → **403**
- wall 48 ms · 7 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.14 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.39 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.10 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 6.03 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.09 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, 0, 1893966347987449989, 0, 0, 1893966347987449989, 5184606887867710024, 1893966347987449989, 3861358557659396986, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5, idx_entities · est. 2 rows · cost 47.86
### `iceberg.create_table`

- `POST /v1/{cat}/namespaces/{ns}/tables` → **403**
- wall 30 ms · 8 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 2.96 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `7, POLARIS, probe_tbl2, 1893966347987449989, 5184606887867710024`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, 0, 1893966347987449989, 0, 0, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities · est. 2 rows · cost 40.02
### `iceberg.stage_create_table`

- `POST /v1/{cat}/namespaces/{ns}/tables[stage]` → **403**
- wall 31 ms · 8 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 2.89 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `7, POLARIS, probe_staged, 1893966347987449989, 5184606887867710024`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, 0, 1893966347987449989, 0, 0, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities · est. 2 rows · cost 40.02
### `iceberg.commit_table`

- `POST /v1/{cat}/namespaces/{ns}/tables/{tbl}` → **403**
- wall 42 ms · 7 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.13 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 3.57 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, 0, 1893966347987449989, 0, 0, 1893966347987449989, 5184606887867710024, 1893966347987449989, 3861358557659396986, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×5, idx_entities · est. 2 rows · cost 47.86
### `iceberg.rename_table`

- `POST /v1/{cat}/tables/rename` → **404**
- wall 45 ms · 8 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.09 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.09 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 5.11 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `7, POLARIS, probe_tbl2, 1893966347987449989, 5184606887867710024`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, 0, 1893966347987449989, 0, 0, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities · est. 2 rows · cost 40.02
### `iceberg.report_metrics`

- `POST /v1/{cat}/.../tables/{tbl}/metrics` → **204**
- wall 36 ms · 6 statements · 0 object ops · entity access: MIXED (batched 20% of 5 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 3.82 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
### `iceberg.load_table[missing]`

- `GET /v1/{cat}/.../tables/{missing}` → **404**
- wall 66 ms · 8 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 45.37 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `7, POLARIS, does_not_exist, 1893966347987449989, 5184606887867710024`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, 0, 1893966347987449989, 0, 0, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities · est. 2 rows · cost 40.02
### `iceberg.drop_table`

- `DELETE /v1/{cat}/namespaces/{ns}/tables/{tbl}` → **404**
- wall 27 ms · 8 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 4.37 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `7, POLARIS, probe_tbl3, 1893966347987449989, 5184606887867710024`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, 0, 1893966347987449989, 0, 0, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities · est. 2 rows · cost 40.02
### `iceberg.create_view`

- `POST /v1/{cat}/namespaces/{ns}/views` → **403**
- wall 58 ms · 8 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.29 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.27 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 5.54 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `7, POLARIS, probe_view, 1893966347987449989, 5184606887867710024`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, 0, 1893966347987449989, 0, 0, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities · est. 2 rows · cost 40.02
### `iceberg.list_views`

- `GET /v1/{cat}/namespaces/{ns}/views` → **403**
- wall 36 ms · 7 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.20 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 4.55 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, 0, 1893966347987449989, 0, 0, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities · est. 2 rows · cost 40.02
### `iceberg.load_view`

- `GET /v1/{cat}/namespaces/{ns}/views/{view}` → **404**
- wall 35 ms · 8 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.10 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 5.38 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `7, POLARIS, probe_view, 1893966347987449989, 5184606887867710024`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, 0, 1893966347987449989, 0, 0, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities · est. 2 rows · cost 40.02
### `iceberg.head_view`

- `HEAD /v1/{cat}/namespaces/{ns}/views/{view}` → **404**
- wall 18 ms · 8 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 2.52 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `7, POLARIS, probe_view, 1893966347987449989, 5184606887867710024`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, 0, 1893966347987449989, 0, 0, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities · est. 2 rows · cost 40.02
### `iceberg.rename_view`

- `POST /v1/{cat}/views/rename` → **404**
- wall 17 ms · 8 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 2.55 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `7, POLARIS, probe_view, 1893966347987449989, 5184606887867710024`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, 0, 1893966347987449989, 0, 0, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities · est. 2 rows · cost 40.02
### `iceberg.drop_view`

- `DELETE /v1/{cat}/namespaces/{ns}/views/{view}` → **404**
- wall 27 ms · 8 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 4.69 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.09 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `7, POLARIS, probe_view2, 1893966347987449989, 5184606887867710024`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, 0, 1893966347987449989, 0, 0, 1893966347987449989, 5184606887867710024, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×4, idx_entities · est. 2 rows · cost 40.02
### `mgmt.list_catalogs`

- `GET /v1/catalogs` → **403**
- wall 48 ms · 7 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.14 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.18 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 5.41 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×2, idx_entities · est. 1 row · cost 24.19
### `mgmt.get_catalog`

- `GET /v1/catalogs/{cat}` → **403**
- wall 52 ms · 7 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.17 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.12 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 6.64 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, 0, 1893966347987449989, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×3, idx_entities · est. 2 rows · cost 32.10
### `mgmt.create_principal`

- `POST /v1/principals` → **403**
- wall 77 ms · 7 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 2.89 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×2, idx_entities · est. 1 row · cost 24.19
### `mgmt.get_principal`

- `GET /v1/principals/{p}` → **404**
- wall 21 ms · 8 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.08 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 2.45 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, apiprofile1788334618_p, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×2, idx_entities · est. 1 row · cost 24.19
### `mgmt.list_principals`

- `GET /v1/principals` → **403**
- wall 29 ms · 7 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.08 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 5.67 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×2, idx_entities · est. 1 row · cost 24.19
### `mgmt.create_principal_role`

- `POST /v1/principal-roles` → **403**
- wall 40 ms · 7 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.80 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 5.81 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.10 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×2, idx_entities · est. 1 row · cost 24.19
### `mgmt.get_principal_role`

- `GET /v1/principal-roles/{r}` → **404**
- wall 35 ms · 8 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 6.04 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `3, POLARIS, apiprofile1788334618_pr, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×2 · est. 1 row · cost 16.21
### `mgmt.list_principal_roles`

- `GET /v1/principal-roles` → **403**
- wall 35 ms · 7 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.08 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 9.10 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.12 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×2, idx_entities · est. 1 row · cost 24.19
### `mgmt.assign_principal_role`

- `PUT /v1/principals/{p}/principal-roles` → **404**
- wall 39 ms · 8 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.24 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.11 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 6.88 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `3, POLARIS, apiprofile1788334618_pr, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×2 · est. 1 row · cost 16.21
### `mgmt.create_catalog_role`

- `POST /v1/catalogs/{cat}/catalog-roles` → **403**
- wall 33 ms · 7 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.08 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 6.14 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, 0, 1893966347987449989, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×3, idx_entities · est. 2 rows · cost 32.10
### `mgmt.list_catalog_roles`

- `GET /v1/catalogs/{cat}/catalog-roles` → **403**
- wall 48 ms · 7 statements · 0 object ops · entity access: MIXED (batched 33% of 6 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 4.28 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.10 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, 0, 1893966347987449989, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×3, idx_entities · est. 2 rows · cost 32.10
### `mgmt.assign_catalog_role`

- `PUT /v1/principal-roles/{r}/catalog-roles/{cat}` → **404**
- wall 39 ms · 8 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.08 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.28 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 9.94 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `3, POLARIS, apiprofile1788334618_pr, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, 0, 1893966347987449989, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×3 · est. 1 row · cost 24.19
### `mgmt.grant_privilege`

- `PUT /v1/catalogs/{cat}/catalog-roles/{cr}/grants` → **404**
- wall 9411 ms · 64 statements · 0 object ops · entity access: MIXED (batched 29% of 56 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.08 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 6.05 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `5, POLARIS, apiprofile1788334618_cr, 1893966347987449989, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.12 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, 0, 1893966347987449989, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×3, idx_entities · est. 2 rows · cost 32.10
**[8]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[9]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[10]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[11]** `grant_records` · SELECT · 4.88 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[12]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[13]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[14]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `5, POLARIS, apiprofile1788334618_cr, 1893966347987449989, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[15]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, 0, 1893966347987449989, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×3, idx_entities · est. 2 rows · cost 32.10
**[16]** `entities` · SELECT · 0.08 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[17]** `entities` · SELECT · 0.21 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[18]** `entities` · SELECT · 0.15 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[19]** `grant_records` · SELECT · 6.17 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[20]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[21]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[22]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `5, POLARIS, apiprofile1788334618_cr, 1893966347987449989, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[23]** `entities` · SELECT · 0.09 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, 0, 1893966347987449989, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×3, idx_entities · est. 2 rows · cost 32.10
**[24]** `entities` · SELECT · 0.09 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[25]** `entities` · SELECT · 0.08 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[26]** `entities` · SELECT · 0.12 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[27]** `grant_records` · SELECT · 6.51 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[28]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[29]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[30]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `5, POLARIS, apiprofile1788334618_cr, 1893966347987449989, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[31]** `entities` · SELECT · 0.10 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, 0, 1893966347987449989, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×3, idx_entities · est. 2 rows · cost 32.10
**[32]** `entities` · SELECT · 0.10 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[33]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[34]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[35]** `grant_records` · SELECT · 3.95 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[36]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[37]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[38]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `5, POLARIS, apiprofile1788334618_cr, 1893966347987449989, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[39]** `entities` · SELECT · 0.09 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, 0, 1893966347987449989, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×3, idx_entities · est. 2 rows · cost 32.10
**[40]** `entities` · SELECT · 0.09 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[41]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[42]** `entities` · SELECT · 0.08 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[43]** `grant_records` · SELECT · 5.89 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[44]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[45]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[46]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `5, POLARIS, apiprofile1788334618_cr, 1893966347987449989, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[47]** `entities` · SELECT · 0.22 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, 0, 1893966347987449989, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×3, idx_entities · est. 2 rows · cost 32.10
**[48]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[49]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[50]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[51]** `grant_records` · SELECT · 3.12 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[52]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[53]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[54]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `5, POLARIS, apiprofile1788334618_cr, 1893966347987449989, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[55]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, 0, 1893966347987449989, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×3, idx_entities · est. 2 rows · cost 32.10
**[56]** `entities` · SELECT · 0.16 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[57]** `entities` · SELECT · 0.10 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[58]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[59]** `grant_records` · SELECT · 8.15 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[60]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[61]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[62]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `5, POLARIS, apiprofile1788334618_cr, 1893966347987449989, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[63]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, 0, 1893966347987449989, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×3, idx_entities · est. 2 rows · cost 32.10
### `mgmt.list_grants`

- `GET /v1/catalogs/{cat}/catalog-roles/{cr}/grants` → **404**
- wall 40 ms · 8 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.08 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.14 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 6.45 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 1.00 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.17 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `5, POLARIS, apiprofile1788334618_cr, 1893966347987449989, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, 0, 1893966347987449989, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×3, idx_entities · est. 2 rows · cost 32.10
### `mgmt.list_principals_for_principal_role`

- `GET /v1/principal-roles/{r}/principals` → **404**
- wall 49 ms · 8 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.13 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.08 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 5.53 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `3, POLARIS, apiprofile1788334618_pr, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×2 · est. 1 row · cost 16.21
### `mgmt.reset_principal_credentials`

- `POST /v1/principals/{p}/reset` → **404**
- wall 31 ms · 8 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 5.52 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, apiprofile1788334618_p, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.06 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×2, idx_entities · est. 1 row · cost 24.19
### `mgmt.delete_catalog_role`

- `DELETE /v1/catalogs/{cat}/catalog-roles/{cr}` → **404**
- wall 40 ms · 8 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.14 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.09 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 6.41 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `5, POLARIS, apiprofile1788334618_cr, 1893966347987449989, 1893966347987449989`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.07 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, 0, 1893966347987449989, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×3, idx_entities · est. 2 rows · cost 32.10
### `mgmt.delete_principal_role`

- `DELETE /v1/principal-roles/{r}` → **404**
- wall 31 ms · 8 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.14 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.11 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.08 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 4.99 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.05 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `3, POLARIS, apiprofile1788334618_pr, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×2 · est. 1 row · cost 16.21
### `mgmt.delete_principal`

- `DELETE /v1/principals/{p}` → **404**
- wall 18 ms · 8 statements · 0 object ops · entity access: MIXED (batched 29% of 7 reads)
- tables: entities, grant_records

**[0]** `entities` · SELECT · 0.04 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, root, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[1]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `2, 0, POLARIS, 5557509405261405641`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[2]** `entities` · SELECT · 0.01 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE id = ? AND realm_id = ? AND catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[3]** `grant_records` · SELECT · 2.94 ms

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `5557509405261405641, POLARIS, 0`

EXPLAIN (index absent) — Seq Scan on grant_records · est. 1 row · cost 1637.26
**[4]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?)) AND realm_id = ?
```
params: `0, 3100973897112954937, POLARIS`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[5]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND catalog_id = ? AND realm_id = ? AND id = ?
```
params: `3, 0, POLARIS, 3100973897112954937`

EXPLAIN (index absent) — Index Scan on entities using idx_entities · est. 1 row · cost 8.31
**[6]** `entities` · SELECT · 0.02 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE type_code = ? AND realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ?
```
params: `2, POLARIS, apiprofile1788334618_p, 0, 0`

EXPLAIN (index absent) — Index Scan on entities using constraint_name · est. 1 row · cost 8.31
**[7]** `entities` · SELECT · 0.03 ms

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN ((?, ?), (?, ?), (?, ?)) AND realm_id = ?
```
params: `0, 5557509405261405641, 0, 3100973897112954937, 0, 0, POLARIS`

EXPLAIN (index absent) — Bitmap Heap Scan on entities using entities_pkey ×2, idx_entities · est. 1 row · cost 24.19
