# Index Audit

Generated 2026-08-20 13:53. Schema version 3, verdict **OK**.

## Schema drift

- ['events'] present — created by the persistence event listener (eventListener.type: persistence-in-memory-buffer), which is configuration, not schema drift. Note its writes are flushed on a timer, so they are attributed separately during tracing.

## Hypotheses

### grant_records_by_grantee — **CONFIRMED** (severity high)

- Source: `loadAllGrantRecordsOnGrantee` on `grant_records`
- Claim: grant_records has exactly one index (its PK), which leads with realm_id then the SECURABLE columns. A lookup by GRANTEE cannot use it selectively -- grantee columns sit at positions 4-5 with the securable columns unconstrained in front of them.
- Impact: loadAllGrantRecordsOnGrantee runs on the authorization path of EVERY authenticated request, so per-request auth cost would grow with the total number of grants in the realm. Invisible with a handful of grants; steadily worse in a shared realm.
- Remedy: `CREATE INDEX idx_grant_records_grantee ON grant_records (realm_id, grantee_catalog_id, grantee_id);`

### grant_records_delete_or — **CONFIRMED** (severity medium)

- Source: `deleteAllEntityGrantRecords` on `grant_records`
- Claim: The delete predicate ORs two disjoint column sets ((grantee_id, grantee_catalog_id) OR (securable_id, securable_catalog_id)), which typically cannot be served by a single index scan.
- Impact: Runs on every entity deletion, so it shows up in teardown and in any drop-heavy workload rather than on the read path.
- Remedy: `Covered by the grantee index above plus the existing PK prefix; confirm the planner uses a BitmapOr rather than a Seq Scan.`

### entities_row_constructor_in — **REFUTED** (severity high)

- Source: `loadEntitiesChangeTracking` on `entities`
- Claim: The entity-cache validation query uses a row-constructor IN list. PostgreSQL does not always turn this into an efficient index scan on idx_entities(realm_id, catalog_id, id).
- Impact: This is the single hottest query in the system -- every cached request runs exactly one of these. A poor plan here taxes everything, including the requests the cache was supposed to make cheap.
- Remedy: `No new index needed if the planner handles it; if not, the fix is upstream (rewrite as an OR-of-equalities or a VALUES join).`


## Statement verdicts

| Verdict | Table | Verb | Calls | Rows | ms | Detail |
|---|---|---|---|---|---|---|
| INDEX_SCAN | entities | SELECT | 128 | 7277 | — | row-constructor IN measured at sizes 1, 10, 50, 200, 500; worst plan INDEX_SCAN |
| INDEX_SCAN | entities | SELECT | 3 | 7277 | 1.31 | Index scan via ['constraint_name']. |
| INDEX_SCAN | entities | SELECT | 111 | 7277 | 0.06 | Index scan via ['idx_entities']. |
| INDEX_SCAN | entities | SELECT | 74 | 7277 | 0.04 | Index scan via ['constraint_name']. |
| INDEX_SCAN | entities | SELECT | 47 | 7277 | 0.23 | Index scan via ['idx_entities']. |
| INDEX_SCAN | entities | SELECT | 1 | 7277 | 2.25 | Index scan via ['constraint_name']. |
| INDEX_SCAN | entities | INSERT | 9 | 7277 | — | Index scan via []. |
| INDEX_SCAN | grant_records | SELECT | 24 | 30013 | 0.07 | Index scan via ['grant_records_pkey']. |
| INDEX_SCAN | grant_records | INSERT | 3 | 30013 | — | Index scan via []. |
| INDEX_SCAN | entities | SELECT | 6 | 7277 | 0.09 | Index scan via ['constraint_name']. |
| INDEX_SCAN | entities | SELECT | 3 | 7277 | 0.07 | Index scan via ['constraint_name']. |
| INDEX_SCAN | entities | SELECT | 1 | 7277 | 0.04 | Index scan via ['constraint_name']. |
| INDEX_SCAN | entities | DELETE | 6 | 7277 | — | Index scan via ['idx_entities']. |
| NO_PARAMS | entities | UPDATE | 13 | 7277 | — | Statement has placeholders but no usable parameters (absent, or redacted because it touches secret material). Supply representative paramete |
| NO_PARAMS | entities | DELETE | 5 | 7277 | — | Statement has placeholders but no usable parameters (absent, or redacted because it touches secret material). Supply representative paramete |
| NO_PARAMS | principal_authentication_data | INSERT | 2 | 1002 | — | Statement has placeholders but no usable parameters (absent, or redacted because it touches secret material). Supply representative paramete |
| NO_PARAMS | entities | DELETE | 1 | 7277 | — | Statement has placeholders but no usable parameters (absent, or redacted because it touches secret material). Supply representative paramete |
| SEQ_SCAN | grant_records | SELECT | 59 | 30013 | 2.95 | Sequential scan on ['grant_records'] at ~30013 rows — no selective access path. |
| SEQ_SCAN | grant_records | DELETE | 6 | 30013 | — | Sequential scan on ['grant_records'] at ~30013 rows — no selective access path. |
| TOO_SMALL | principal_authentication_data | DELETE | 2 | 1002 | — | principal_authentication_data holds ~1002 rows (< 5000). PostgreSQL prefers a sequential scan on small tables because it is genuinely cheape |
| TOO_SMALL | policy_mapping_record | DELETE | 2 | 0 | — | policy_mapping_record holds ~0 rows (< 5000). PostgreSQL prefers a sequential scan on small tables because it is genuinely cheaper — no conc |
| TOO_SMALL | principal_authentication_data | SELECT | 2 | 1002 | 0.03 | principal_authentication_data holds ~1002 rows (< 5000). PostgreSQL prefers a sequential scan on small tables because it is genuinely cheape |
| TOO_SMALL | policy_mapping_record | SELECT | 2 | 0 | 0.02 | policy_mapping_record holds ~0 rows (< 5000). PostgreSQL prefers a sequential scan on small tables because it is genuinely cheaper — no conc |