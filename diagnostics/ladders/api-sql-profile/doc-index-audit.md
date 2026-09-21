# Index Audit

Generated 2026-08-20 12:05. Schema version 3, verdict **DRIFT**.

## Schema drift

- Schema version is 3, expected 2. Every expectation in this module is written for schema-v2 (Polaris 1.3.0); treat index findings as unverified until the expected set is updated for the deployed version.
- ['events'] present — created by the persistence event listener (eventListener.type: persistence-in-memory-buffer), which is configuration, not schema drift. Note its writes are flushed on a timer, so they are attributed separately during tracing.

## Hypotheses

### grant_records_by_grantee — **INCONCLUSIVE** (severity high)

- Source: `loadAllGrantRecordsOnGrantee` on `grant_records`
- Claim: grant_records has exactly one index (its PK), which leads with realm_id then the SECURABLE columns. A lookup by GRANTEE cannot use it selectively -- grantee columns sit at positions 4-5 with the securable columns unconstrained in front of them.
- Impact: loadAllGrantRecordsOnGrantee runs on the authorization path of EVERY authenticated request, so per-request auth cost would grow with the total number of grants in the realm. Invisible with a handful of grants; steadily worse in a shared realm.
- Remedy: `CREATE INDEX idx_grant_records_grantee ON grant_records (realm_id, grantee_catalog_id, grantee_id);`

### grant_records_delete_or — **INCONCLUSIVE** (severity medium)

- Source: `deleteAllEntityGrantRecords` on `grant_records`
- Claim: The delete predicate ORs two disjoint column sets ((grantee_id, grantee_catalog_id) OR (securable_id, securable_catalog_id)), which typically cannot be served by a single index scan.
- Impact: Runs on every entity deletion, so it shows up in teardown and in any drop-heavy workload rather than on the read path.
- Remedy: `Covered by the grantee index above plus the existing PK prefix; confirm the planner uses a BitmapOr rather than a Seq Scan.`

### entities_row_constructor_in — **INCONCLUSIVE** (severity high)

- Source: `loadEntitiesChangeTracking` on `entities`
- Claim: The entity-cache validation query uses a row-constructor IN list. PostgreSQL does not always turn this into an efficient index scan on idx_entities(realm_id, catalog_id, id).
- Impact: This is the single hottest query in the system -- every cached request runs exactly one of these. A poor plan here taxes everything, including the requests the cache was supposed to make cheap.
- Remedy: `No new index needed if the planner handles it; if not, the fix is upstream (rewrite as an OR-of-equalities or a VALUES join).`


## Statement verdicts

| Verdict | Table | Verb | Calls | Rows | ms | Detail |
|---|---|---|---|---|---|---|
| ERROR | grant_records | DELETE | 6 | 30013 | — |  |
| ERROR | — | — | 504 | None | — |  |
| ERROR | nodes | SELECT | 3 | 0 | — |  |
| ERROR | — | SET | 35 | None | — |  |
| ERROR | — | SELECT | 14 | None | — |  |
| ERROR | nodes | SELECT | 12 | 0 | — |  |
| ERROR | nodes | SELECT | 12 | 0 | — |  |
| ERROR | nodes | SELECT | 4 | 0 | — |  |
| ERROR | — | SELECT | 15 | None | — |  |
| ERROR | nodes | SELECT | 5 | 0 | — |  |
| ERROR | nodes | SELECT | 4 | 0 | — |  |
| ERROR | nodes | SELECT | 3 | 0 | — |  |
| ERROR | — | SET | 12 | None | — |  |
| ERROR | — | — | 12 | None | — |  |
| ERROR | nodes | SELECT | 7 | 0 | — |  |
| ERROR | — | SELECT | 12 | None | — |  |
| ERROR | — | SELECT | 12 | None | — |  |
| ERROR | — | SELECT | 12 | None | — |  |
| ERROR | — | SELECT | 12 | None | — |  |
| INDEX_SCAN | — | SELECT | 83 | None | 0.02 | Index scan via []. |
| INDEX_SCAN | — | SELECT | 24 | None | 0.01 | Index scan via []. |
| INDEX_SCAN | — | SELECT | 11 | None | 0.00 | Index scan via []. |
| INDEX_SCAN | — | SELECT | 16 | None | 0.01 | Index scan via []. |
| INDEX_SCAN | — | SELECT | 4 | None | 0.03 | Index scan via []. |
| INDEX_SCAN | — | SELECT | 2 | None | 0.01 | Index scan via []. |
| NO_PARAMS | grant_records | SELECT | 59 | 30013 | — | Statement has placeholders but no usable parameters (absent, or redacted because it touches secret material). Supply representative paramete |
| NO_PARAMS | entities | SELECT | 1 | 7256 | — | Statement has placeholders but no usable parameters (absent, or redacted because it touches secret material). Supply representative paramete |
| NO_PARAMS | entities | SELECT | 129 | 7256 | — | Statement has placeholders but no usable parameters (absent, or redacted because it touches secret material). Supply representative paramete |
| NO_PARAMS | entities | SELECT | 112 | 7256 | — | Statement has placeholders but no usable parameters (absent, or redacted because it touches secret material). Supply representative paramete |
| NO_PARAMS | entities | SELECT | 70 | 7256 | — | Statement has placeholders but no usable parameters (absent, or redacted because it touches secret material). Supply representative paramete |
| NO_PARAMS | entities | SELECT | 3 | 7256 | — | Statement has placeholders but no usable parameters (absent, or redacted because it touches secret material). Supply representative paramete |
| NO_PARAMS | entities | SELECT | 47 | 7256 | — | Statement has placeholders but no usable parameters (absent, or redacted because it touches secret material). Supply representative paramete |
| NO_PARAMS | entities | UPDATE | 13 | 7256 | — | Statement has placeholders but no usable parameters (absent, or redacted because it touches secret material). Supply representative paramete |
| NO_PARAMS | entities | INSERT | 9 | 7256 | — | Statement has placeholders but no usable parameters (absent, or redacted because it touches secret material). Supply representative paramete |
| NO_PARAMS | grant_records | SELECT | 23 | 30013 | — | Statement has placeholders but no usable parameters (absent, or redacted because it touches secret material). Supply representative paramete |
| NO_PARAMS | entities | DELETE | 6 | 7256 | — | Statement has placeholders but no usable parameters (absent, or redacted because it touches secret material). Supply representative paramete |
| NO_PARAMS | entities | SELECT | 6 | 7256 | — | Statement has placeholders but no usable parameters (absent, or redacted because it touches secret material). Supply representative paramete |
| NO_PARAMS | grant_records | INSERT | 3 | 30013 | — | Statement has placeholders but no usable parameters (absent, or redacted because it touches secret material). Supply representative paramete |
| NO_PARAMS | principal_authentication_data | DELETE | 2 | 1002 | — | Statement has placeholders but no usable parameters (absent, or redacted because it touches secret material). Supply representative paramete |
| NO_PARAMS | principal_authentication_data | INSERT | 2 | 1002 | — | Statement has placeholders but no usable parameters (absent, or redacted because it touches secret material). Supply representative paramete |
| NO_PARAMS | entities | SELECT | 3 | 7256 | — | Statement has placeholders but no usable parameters (absent, or redacted because it touches secret material). Supply representative paramete |
| NO_PARAMS | principal_authentication_data | SELECT | 2 | 1002 | — | Statement has placeholders but no usable parameters (absent, or redacted because it touches secret material). Supply representative paramete |
| NO_PARAMS | policy_mapping_record | DELETE | 2 | 0 | — | Statement has placeholders but no usable parameters (absent, or redacted because it touches secret material). Supply representative paramete |
| NO_PARAMS | policy_mapping_record | SELECT | 2 | 0 | — | Statement has placeholders but no usable parameters (absent, or redacted because it touches secret material). Supply representative paramete |
| NO_PARAMS | entities | SELECT | 1 | 7256 | — | Statement has placeholders but no usable parameters (absent, or redacted because it touches secret material). Supply representative paramete |
| TOO_SMALL | pg_stat_replication | SELECT | 4 | 0 | 0.53 | pg_stat_replication holds ~0 rows (< 5000). PostgreSQL prefers a sequential scan on small tables because it is genuinely cheaper — no conclu |
| TOO_SMALL | pg_stat_replication | SELECT | 5 | 0 | 0.16 | pg_stat_replication holds ~0 rows (< 5000). PostgreSQL prefers a sequential scan on small tables because it is genuinely cheaper — no conclu |
| TOO_SMALL | pg_stat_replication | SELECT | 9 | 0 | 0.47 | pg_stat_replication holds ~0 rows (< 5000). PostgreSQL prefers a sequential scan on small tables because it is genuinely cheaper — no conclu |
| TOO_SMALL | replay_lag | SELECT | 2 | 0 | 0.08 | replay_lag holds ~0 rows (< 5000). PostgreSQL prefers a sequential scan on small tables because it is genuinely cheaper — no conclusion can  |