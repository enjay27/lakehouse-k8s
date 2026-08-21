# Index Audit

Generated 2026-08-20 17:30. Schema version 3, verdict **OK**.

## Schema drift

- ['events'] present — created by the persistence event listener (eventListener.type: persistence-in-memory-buffer), which is configuration, not schema drift. Note its writes are flushed on a timer, so they are attributed separately during tracing.

## Hypotheses

### grant_records_by_grantee — **REMEDIED** (severity high)

- Source: `loadAllGrantRecordsOnGrantee` on `grant_records`
- Claim: grant_records has exactly one index (its PK), which leads with realm_id then the SECURABLE columns. A lookup by GRANTEE cannot use it selectively -- grantee columns sit at positions 4-5 with the securable columns unconstrained in front of them.
- Impact: loadAllGrantRecordsOnGrantee runs on the authorization path of EVERY authenticated request, so per-request auth cost would grow with the total number of grants in the realm. Invisible with a handful of grants; steadily worse in a shared realm.
- Remedy: `CREATE INDEX idx_grant_records_grantee ON grant_records (realm_id, grantee_catalog_id, grantee_id);`

> The claim STANDS and the proposed fix is already on this cluster: the winning plan uses idx_grant_records_grantee, which this hypothesis itself proposes. That makes the 'before' state unobservable here — take the verdict from a run where the index is absent (02's section 5 measures exactly that). This is NOT a refutation.

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```

### grant_records_delete_or — **REMEDIED** (severity medium)

- Source: `deleteAllEntityGrantRecords` on `grant_records`
- Claim: The delete predicate ORs two disjoint column sets ((grantee_id, grantee_catalog_id) OR (securable_id, securable_catalog_id)), which typically cannot be served by a single index scan.
- Impact: Runs on every entity deletion, so it shows up in teardown and in any drop-heavy workload rather than on the read path.
- Remedy: `Covered by the grantee index above plus the existing PK prefix; confirm the planner uses a BitmapOr rather than a Seq Scan.`

> The claim STANDS and the proposed fix is already on this cluster: the winning plan uses idx_grant_records_grantee, which this hypothesis itself proposes. That makes the 'before' state unobservable here — take the verdict from a run where the index is absent (02's section 5 measures exactly that). This is NOT a refutation.

```sql
DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE ( (grantee_id = ? AND grantee_catalog_id = ?) OR (securable_id = ? AND securable_catalog_id = ?) ) AND realm_id = ?
```

### entities_row_constructor_in — **REFUTED** (severity high)

- Source: `loadEntitiesChangeTracking` on `entities`
- Claim: The entity-cache validation query uses a row-constructor IN list. PostgreSQL does not always turn this into an efficient index scan on idx_entities(realm_id, catalog_id, id).
- Impact: This is the single hottest query in the system -- every cached request runs exactly one of these. A poor plan here taxes everything, including the requests the cache was supposed to make cheap.
- Remedy: `No new index needed if the planner handles it; if not, the fix is upstream (rewrite as an OR-of-equalities or a VALUES join).`

> Served by a pre-existing access path, not by anything this hypothesis proposes (indexes used: n/a).

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN (<rows>) AND realm_id = ?
```


## Statement verdicts

| # | Verdict | Table | Verb | Calls | Rows | ms |
|---|---|---|---|---|---|---|
| [1](#stmt-1) | INDEX_SCAN | entities | SELECT | 130 | 7289 | — |
| [2](#stmt-2) | INDEX_SCAN | entities | SELECT | 113 | 7289 | 0.02 |
| [3](#stmt-3) | INDEX_SCAN | entities | SELECT | 76 | 7289 | 0.02 |
| [4](#stmt-4) | INDEX_SCAN | grant_records | SELECT | 60 | 30013 | 0.03 |
| [5](#stmt-5) | INDEX_SCAN | entities | SELECT | 48 | 7289 | 0.01 |
| [6](#stmt-6) | INDEX_SCAN | grant_records | SELECT | 24 | 30013 | 0.03 |
| [7](#stmt-7) | INDEX_SCAN | entities | INSERT | 9 | 7289 | — |
| [8](#stmt-8) | INDEX_SCAN | entities | SELECT | 6 | 7289 | 0.01 |
| [9](#stmt-9) | INDEX_SCAN | entities | DELETE | 6 | 7289 | — |
| [10](#stmt-10) | INDEX_SCAN | grant_records | DELETE | 6 | 30013 | — |
| [11](#stmt-11) | INDEX_SCAN | entities | SELECT | 3 | 7289 | 0.01 |
| [12](#stmt-12) | INDEX_SCAN | entities | SELECT | 3 | 7289 | 0.56 |
| [13](#stmt-13) | INDEX_SCAN | grant_records | INSERT | 3 | 30013 | — |
| [14](#stmt-14) | INDEX_SCAN | entities | SELECT | 2 | 7289 | 0.59 |
| [15](#stmt-15) | INDEX_SCAN | entities | SELECT | 1 | 7289 | 0.01 |
| [16](#stmt-16) | NO_PARAMS | entities | UPDATE | 13 | 7289 | — |
| [17](#stmt-17) | NO_PARAMS | principal_authentication_data | INSERT | 2 | 1002 | — |
| [18](#stmt-18) | TOO_SMALL | policy_mapping_record | SELECT | 2 | 0 | 0.00 |
| [19](#stmt-19) | TOO_SMALL | policy_mapping_record | DELETE | 2 | 0 | — |
| [20](#stmt-20) | TOO_SMALL | principal_authentication_data | SELECT | 2 | 1002 | 0.01 |
| [21](#stmt-21) | TOO_SMALL | principal_authentication_data | DELETE | 2 | 1002 | — |

## Statement catalogue

Every audited statement in full — SQL as Polaris emitted it, with the complete verdict rationale. Nothing here is abbreviated.

<a id="stmt-1"></a>

### 1. `entities` · SELECT · **INDEX_SCAN**

- calls in capture: **130** · table rows: 7289 · no plan timing
- issued by: `iceberg.commit_table`, `iceberg.create_namespace`, `iceberg.create_table`, `iceberg.create_view`, `iceberg.drop_namespace`, `iceberg.drop_table`, `iceberg.drop_view`, `iceberg.get_config`, `iceberg.head_namespace`, `iceberg.head_table`, `iceberg.head_view`, `iceberg.list_namespaces`, `iceberg.list_tables`, `iceberg.list_views`, `iceberg.load_namespace`, `iceberg.load_table`, `iceberg.load_table[missing]`, `iceberg.load_table[snapshots=refs]`, `iceberg.load_view`, `iceberg.rename_table`, `iceberg.rename_view`, `iceberg.report_metrics`, `iceberg.stage_create_table`, `iceberg.update_namespace_properties`, `mgmt.assign_catalog_role`, `mgmt.assign_principal_role`, `mgmt.create_catalog_role`, `mgmt.create_principal`, `mgmt.create_principal_role`, `mgmt.delete_catalog_role`, `mgmt.delete_principal`, `mgmt.delete_principal_role`, `mgmt.get_catalog`, `mgmt.get_principal`, `mgmt.get_principal_role`, `mgmt.grant_privilege`, `mgmt.list_catalog_roles`, `mgmt.list_catalogs`, `mgmt.list_grants`, `mgmt.list_principal_roles`, `mgmt.list_principals`, `mgmt.list_principals_for_principal_role`, `mgmt.reset_principal_credentials`, `preflight`

row-constructor IN measured at sizes 1, 10, 50, 200, 500; worst plan INDEX_SCAN

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE (catalog_id, id) IN (<rows>) AND realm_id = ?
```

<a id="stmt-2"></a>

### 2. `entities` · SELECT · **INDEX_SCAN**

- calls in capture: **113** · table rows: 7289 · 0.02 ms
- issued by: `iceberg.commit_table`, `iceberg.create_namespace`, `iceberg.create_table`, `iceberg.create_view`, `iceberg.drop_namespace`, `iceberg.drop_table`, `iceberg.drop_view`, `iceberg.get_config`, `iceberg.head_namespace`, `iceberg.head_table`, `iceberg.head_view`, `iceberg.list_namespaces`, `iceberg.list_tables`, `iceberg.list_views`, `iceberg.load_namespace`, `iceberg.load_table`, `iceberg.load_table[missing]`, `iceberg.load_table[snapshots=refs]`, `iceberg.load_view`, `iceberg.rename_table`, `iceberg.rename_view`, `iceberg.report_metrics`, `iceberg.stage_create_table`, `iceberg.update_namespace_properties`, `mgmt.assign_catalog_role`, `mgmt.assign_principal_role`, `mgmt.create_catalog_role`, `mgmt.create_principal`, `mgmt.create_principal_role`, `mgmt.delete_catalog_role`, `mgmt.delete_principal`, `mgmt.delete_principal_role`, `mgmt.get_catalog`, `mgmt.get_principal`, `mgmt.get_principal_role`, `mgmt.grant_privilege`, `mgmt.list_catalog_roles`, `mgmt.list_catalogs`, `mgmt.list_grants`, `mgmt.list_principal_roles`, `mgmt.list_principals`, `mgmt.list_principals_for_principal_role`, `mgmt.reset_principal_credentials`, `preflight`
- index scans: ['idx_entities']

Index scan via ['idx_entities'].

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND id = ? AND type_code = ? AND catalog_id = ?
```

<a id="stmt-3"></a>

### 3. `entities` · SELECT · **INDEX_SCAN**

- calls in capture: **76** · table rows: 7289 · 0.02 ms
- issued by: `iceberg.commit_table`, `iceberg.create_namespace`, `iceberg.create_table`, `iceberg.create_view`, `iceberg.drop_namespace`, `iceberg.drop_table`, `iceberg.drop_view`, `iceberg.get_config`, `iceberg.head_namespace`, `iceberg.head_table`, `iceberg.head_view`, `iceberg.list_namespaces`, `iceberg.list_tables`, `iceberg.list_views`, `iceberg.load_namespace`, `iceberg.load_table`, `iceberg.load_table[missing]`, `iceberg.load_table[snapshots=refs]`, `iceberg.load_view`, `iceberg.rename_table`, `iceberg.rename_view`, `iceberg.report_metrics`, `iceberg.stage_create_table`, `iceberg.update_namespace_properties`, `mgmt.assign_catalog_role`, `mgmt.assign_principal_role`, `mgmt.create_catalog_role`, `mgmt.create_principal`, `mgmt.create_principal_role`, `mgmt.delete_catalog_role`, `mgmt.delete_principal`, `mgmt.delete_principal_role`, `mgmt.get_catalog`, `mgmt.get_principal`, `mgmt.get_principal_role`, `mgmt.grant_privilege`, `mgmt.list_catalog_roles`, `mgmt.list_catalogs`, `mgmt.list_grants`, `mgmt.list_principal_roles`, `mgmt.list_principals`, `mgmt.list_principals_for_principal_role`, `mgmt.reset_principal_credentials`, `preflight`
- index scans: ['constraint_name']

Index scan via ['constraint_name'].

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND name = ? AND catalog_id = ? AND parent_id = ? AND type_code = ?
```

<a id="stmt-4"></a>

### 4. `grant_records` · SELECT · **INDEX_SCAN**

- calls in capture: **60** · table rows: 30013 · 0.03 ms
- issued by: `iceberg.commit_table`, `iceberg.create_namespace`, `iceberg.create_table`, `iceberg.create_view`, `iceberg.drop_namespace`, `iceberg.drop_table`, `iceberg.drop_view`, `iceberg.get_config`, `iceberg.head_namespace`, `iceberg.head_table`, `iceberg.head_view`, `iceberg.list_namespaces`, `iceberg.list_tables`, `iceberg.list_views`, `iceberg.load_namespace`, `iceberg.load_table`, `iceberg.load_table[missing]`, `iceberg.load_table[snapshots=refs]`, `iceberg.load_view`, `iceberg.rename_table`, `iceberg.rename_view`, `iceberg.report_metrics`, `iceberg.stage_create_table`, `iceberg.update_namespace_properties`, `mgmt.assign_catalog_role`, `mgmt.assign_principal_role`, `mgmt.create_catalog_role`, `mgmt.create_principal`, `mgmt.create_principal_role`, `mgmt.delete_catalog_role`, `mgmt.delete_principal`, `mgmt.delete_principal_role`, `mgmt.get_catalog`, `mgmt.get_principal`, `mgmt.get_principal_role`, `mgmt.grant_privilege`, `mgmt.list_catalog_roles`, `mgmt.list_catalogs`, `mgmt.list_grants`, `mgmt.list_principal_roles`, `mgmt.list_principals`, `mgmt.list_principals_for_principal_role`, `mgmt.reset_principal_credentials`, `preflight`
- index scans: ['idx_grant_records_grantee']

Index scan via ['idx_grant_records_grantee'].

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```

<a id="stmt-5"></a>

### 5. `entities` · SELECT · **INDEX_SCAN**

- calls in capture: **48** · table rows: 7289 · 0.01 ms
- issued by: `iceberg.commit_table`, `iceberg.create_namespace`, `iceberg.create_table`, `iceberg.create_view`, `iceberg.drop_namespace`, `iceberg.drop_table`, `iceberg.drop_view`, `iceberg.get_config`, `iceberg.head_namespace`, `iceberg.head_table`, `iceberg.head_view`, `iceberg.list_namespaces`, `iceberg.list_tables`, `iceberg.list_views`, `iceberg.load_namespace`, `iceberg.load_table`, `iceberg.load_table[missing]`, `iceberg.load_table[snapshots=refs]`, `iceberg.load_view`, `iceberg.rename_table`, `iceberg.rename_view`, `iceberg.report_metrics`, `iceberg.stage_create_table`, `iceberg.update_namespace_properties`, `mgmt.assign_catalog_role`, `mgmt.assign_principal_role`, `mgmt.create_catalog_role`, `mgmt.create_principal`, `mgmt.create_principal_role`, `mgmt.delete_catalog_role`, `mgmt.delete_principal`, `mgmt.delete_principal_role`, `mgmt.get_catalog`, `mgmt.get_principal`, `mgmt.get_principal_role`, `mgmt.grant_privilege`, `mgmt.list_catalog_roles`, `mgmt.list_catalogs`, `mgmt.list_grants`, `mgmt.list_principal_roles`, `mgmt.list_principals`, `mgmt.list_principals_for_principal_role`, `mgmt.reset_principal_credentials`, `preflight`
- index scans: ['idx_entities']

Index scan via ['idx_entities'].

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```

<a id="stmt-6"></a>

### 6. `grant_records` · SELECT · **INDEX_SCAN**

- calls in capture: **24** · table rows: 30013 · 0.03 ms
- issued by: `iceberg.drop_namespace`, `iceberg.drop_table`, `iceberg.drop_view`, `iceberg.load_table`, `iceberg.load_view`, `iceberg.rename_table`, `mgmt.assign_catalog_role`, `mgmt.delete_catalog_role`, `mgmt.delete_principal`, `mgmt.delete_principal_role`, `mgmt.get_principal`, `mgmt.get_principal_role`, `mgmt.grant_privilege`, `mgmt.list_grants`, `mgmt.list_principals_for_principal_role`, `mgmt.reset_principal_credentials`
- index scans: ['grant_records_pkey']

Index scan via ['grant_records_pkey'].

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_catalog_id = ? AND realm_id = ? AND securable_id = ?
```

<a id="stmt-7"></a>

### 7. `entities` · INSERT · **INDEX_SCAN**

- calls in capture: **9** · table rows: 7289 · no plan timing
- issued by: `iceberg.create_namespace`, `iceberg.create_table`, `iceberg.create_view`, `iceberg.drop_view`, `mgmt.create_catalog_role`, `mgmt.create_principal`, `mgmt.create_principal_role`, `mgmt.delete_catalog_role`, `mgmt.delete_principal_role`

Index scan via [].

```sql
INSERT INTO POLARIS_SCHEMA.ENTITIES (id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme, realm_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```

<a id="stmt-8"></a>

### 8. `entities` · SELECT · **INDEX_SCAN**

- calls in capture: **6** · table rows: 7289 · 0.01 ms
- issued by: `iceberg.create_namespace`, `iceberg.create_table`, `iceberg.create_view`, `iceberg.update_namespace_properties`
- index scans: ['constraint_name']

Index scan via ['constraint_name'].

```sql
SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND realm_id = ? AND type_code = ? AND catalog_id = ?
```

<a id="stmt-9"></a>

### 9. `entities` · DELETE · **INDEX_SCAN**

- calls in capture: **6** · table rows: 7289 · no plan timing
- issued by: `iceberg.drop_namespace`, `iceberg.drop_table`, `iceberg.drop_view`, `mgmt.delete_catalog_role`, `mgmt.delete_principal`, `mgmt.delete_principal_role`
- index scans: ['idx_entities']

Index scan via ['idx_entities'].

```sql
DELETE FROM POLARIS_SCHEMA.ENTITIES WHERE realm_id = ? AND catalog_id = ? AND id = ?
```

<a id="stmt-10"></a>

### 10. `grant_records` · DELETE · **INDEX_SCAN**

- calls in capture: **6** · table rows: 30013 · no plan timing
- issued by: `iceberg.drop_namespace`, `iceberg.drop_table`, `iceberg.drop_view`, `mgmt.delete_catalog_role`, `mgmt.delete_principal`, `mgmt.delete_principal_role`
- index scans: ['idx_grant_records_grantee', 'grant_records_pkey']

Index scan via ['idx_grant_records_grantee', 'grant_records_pkey'].

```sql
DELETE FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE ( (grantee_id = ? AND grantee_catalog_id = ?) OR (securable_id = ? AND securable_catalog_id = ?) ) AND realm_id = ?
```

<a id="stmt-11"></a>

### 11. `entities` · SELECT · **INDEX_SCAN**

- calls in capture: **3** · table rows: 7289 · 0.01 ms
- issued by: `iceberg.list_namespaces`, `iceberg.list_tables`, `iceberg.list_views`
- index scans: ['constraint_name']

Index scan via ['constraint_name'].

```sql
SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND sub_type_code = ? AND realm_id = ? AND parent_id = ? AND type_code = ?
```

<a id="stmt-12"></a>

### 12. `entities` · SELECT · **INDEX_SCAN**

- calls in capture: **3** · table rows: 7289 · 0.56 ms
- issued by: `mgmt.list_catalog_roles`, `mgmt.list_principal_roles`, `mgmt.list_principals`
- index scans: ['constraint_name']

Index scan via ['constraint_name'].

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND sub_type_code = ? AND realm_id = ? AND parent_id = ? AND type_code = ?
```

<a id="stmt-13"></a>

### 13. `grant_records` · INSERT · **INDEX_SCAN**

- calls in capture: **3** · table rows: 30013 · no plan timing
- issued by: `mgmt.assign_catalog_role`, `mgmt.assign_principal_role`, `mgmt.grant_privilege`

Index scan via [].

```sql
INSERT INTO POLARIS_SCHEMA.GRANT_RECORDS (securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code, realm_id) VALUES (?, ?, ?, ?, ?, ?)
```

<a id="stmt-14"></a>

### 14. `entities` · SELECT · **INDEX_SCAN**

- calls in capture: **2** · table rows: 7289 · 0.59 ms
- issued by: `mgmt.list_catalogs`, `preflight`
- index scans: ['constraint_name']

Index scan via ['constraint_name'].

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE parent_id = ? AND realm_id = ? AND type_code = ? AND catalog_id = ?
```

<a id="stmt-15"></a>

### 15. `entities` · SELECT · **INDEX_SCAN**

- calls in capture: **1** · table rows: 7289 · 0.01 ms
- issued by: `iceberg.drop_namespace`
- index scans: ['constraint_name']

Index scan via ['constraint_name'].

```sql
SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_update_timestamp, properties, internal_properties, grant_records_version, location_without_scheme FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND parent_id = ? AND realm_id = ?
```

<a id="stmt-16"></a>

### 16. `entities` · UPDATE · **NO_PARAMS**

- calls in capture: **13** · table rows: 7289 · no plan timing
- issued by: `iceberg.commit_table`, `iceberg.rename_table`, `iceberg.rename_view`, `iceberg.update_namespace_properties`, `mgmt.assign_catalog_role`, `mgmt.assign_principal_role`, `mgmt.delete_catalog_role`, `mgmt.delete_principal_role`, `mgmt.grant_privilege`

Statement has placeholders but no usable parameters (absent, or redacted because it touches secret material). Supply representative parameters to audit this one.

```sql
UPDATE POLARIS_SCHEMA.ENTITIES SET id = ?, catalog_id = ?, parent_id = ?, type_code = ?, name = ?, entity_version = ?, sub_type_code = ?, create_timestamp = ?, drop_timestamp = ?, purge_timestamp = ?, to_purge_timestamp = ?, last_update_timestamp = ?, properties = ?, internal_properties = ?, grant_records_version = ?, location_without_scheme = ? WHERE realm_id = ? AND entity_version = ? AND id = ? AND catalog_id = ?
```

<a id="stmt-17"></a>

### 17. `principal_authentication_data` · INSERT · **NO_PARAMS**

- calls in capture: **2** · table rows: 1002 · no plan timing
- issued by: `mgmt.create_principal`, `mgmt.reset_principal_credentials`

Statement has placeholders but no usable parameters (absent, or redacted because it touches secret material). Supply representative parameters to audit this one.

```sql
INSERT INTO POLARIS_SCHEMA.PRINCIPAL_AUTHENTICATION_DATA (principal_id, principal_client_id, main_secret_hash, secondary_secret_hash, secret_salt, realm_id) VALUES (?, ?, ?, ?, ?, ?)
```

<a id="stmt-18"></a>

### 18. `policy_mapping_record` · SELECT · **TOO_SMALL**

- calls in capture: **2** · table rows: 0 · 0.00 ms
- issued by: `iceberg.drop_namespace`, `iceberg.drop_table`
- seq scans: ['policy_mapping_record']

policy_mapping_record holds ~0 rows (< 5000). PostgreSQL prefers a sequential scan on small tables because it is genuinely cheaper — no conclusion can be drawn. Seed more data before trusting an index verdict here.

```sql
SELECT target_catalog_id, target_id, policy_type_code, policy_catalog_id, policy_id, parameters FROM POLARIS_SCHEMA.POLICY_MAPPING_RECORD WHERE realm_id = ? AND target_id = ? AND target_catalog_id = ?
```

<a id="stmt-19"></a>

### 19. `policy_mapping_record` · DELETE · **TOO_SMALL**

- calls in capture: **2** · table rows: 0 · no plan timing
- issued by: `iceberg.drop_namespace`, `iceberg.drop_table`
- seq scans: ['policy_mapping_record']

policy_mapping_record holds ~0 rows (< 5000). PostgreSQL prefers a sequential scan on small tables because it is genuinely cheaper — no conclusion can be drawn. Seed more data before trusting an index verdict here.

```sql
DELETE FROM POLARIS_SCHEMA.POLICY_MAPPING_RECORD WHERE target_catalog_id = ? AND target_id = ? AND realm_id = ?
```

<a id="stmt-20"></a>

### 20. `principal_authentication_data` · SELECT · **TOO_SMALL**

- calls in capture: **2** · table rows: 1002 · 0.01 ms
- issued by: `mgmt.create_principal`, `mgmt.reset_principal_credentials`
- index scans: ['principal_authentication_data_pkey']

principal_authentication_data holds ~1002 rows (< 5000). PostgreSQL prefers a sequential scan on small tables because it is genuinely cheaper — no conclusion can be drawn. Seed more data before trusting an index verdict here.

```sql
SELECT principal_id, principal_client_id, main_secret_hash, secondary_secret_hash, secret_salt FROM POLARIS_SCHEMA.PRINCIPAL_AUTHENTICATION_DATA WHERE realm_id = ? AND principal_client_id = ?
```

<a id="stmt-21"></a>

### 21. `principal_authentication_data` · DELETE · **TOO_SMALL**

- calls in capture: **2** · table rows: 1002 · no plan timing
- issued by: `mgmt.delete_principal`, `mgmt.reset_principal_credentials`
- index scans: ['principal_authentication_data_pkey']

principal_authentication_data holds ~1002 rows (< 5000). PostgreSQL prefers a sequential scan on small tables because it is genuinely cheaper — no conclusion can be drawn. Seed more data before trusting an index verdict here.

```sql
DELETE FROM POLARIS_SCHEMA.PRINCIPAL_AUTHENTICATION_DATA WHERE realm_id = ? AND principal_id = ? AND principal_client_id = ?
```
