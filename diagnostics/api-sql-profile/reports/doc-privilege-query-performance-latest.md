# Privilege query performance — Pass A, index ABSENT

Generated 2026-08-24 15:12:05 from capture `capture-scan-noindex-2` and run `20260824-123408`. Volume, index state and request counts below are **measured**, not carried over from a plan document.

## What was measured

- realm `POLARIS`, prefix `user`
- **1000 identities**, 1000 authenticated, **15000 requests** in 138.3 s (the drive's own clock, discarded — logging on)
- capture window `2026-08-24T03:31:47.991611585Z` → `2026-08-24T03:34:08.284467254Z`
- `polaris_schema.grant_records`: **55,004 rows** at EXPLAIN time
- index state on `grant_records`: index ABSENT
  - `grant_records_pkey`
- provenance: 1,000 real API-seeded principals. Nothing synthetic, nothing to disclose.

## Capture integrity

- access-log requests correlated: **15002**
- statements parsed: **109010**
- every parsed statement mapped to a request. No orphans.
- every request matched a known op template.

| op | run JSON | capture | delta |
|---|---:|---:|---:|
| `GET  /catalog-roles/{r}/grants` | 1000 | 1000 | +0 |
| `GET  /catalogs` | 1000 | 1000 | +0 |
| `GET  /catalogs/{c}/catalog-roles` | 1000 | 1000 | +0 |
| `GET  /catalogs/{name}` | 1000 | 1001 | +1 |
| `GET  /namespaces`  *(incl. ns-resolve)* | 2000 | 2000 | +0 |
| `GET  /namespaces/{ns}` | 1000 | 1000 | +0 |
| `GET  /namespaces/{ns}/tables` | 1000 | 1000 | +0 |
| `GET  /namespaces/{ns}/views` | 1000 | 1000 | +0 |
| `GET  /principal-roles` | 1000 | 1000 | +0 |
| `GET  /principal-roles/{name}` | 1000 | 1000 | +0 |
| `GET  /principal-roles/{n}/principals` | 1000 | 1000 | +0 |
| `GET  /principals` | 1000 | 1000 | +0 |
| `GET  /principals/{name}` | 1000 | 1000 | +0 |
| `POST /oauth/tokens` | 1000 | 1001 | +1 |
| **total** | **15000** | **15002** | **+2** |

**The capture and the run disagree by +2 requests.** Every figure below describes what the capture holds, which is not what the drive issued. Resolve this before quoting anything from it.

## Does a refused request pay the authorization prelude?

`scan_privileges.py` asserts that it does. This pass drove the refused operations for **every** identity, so the question is answered from the capture instead:

| request class | requests | stmts/req | min | median | max | grant_records/req |
|---|---:|---:|---:|---:|---:|---:|
| auth (token) | 1001 | 3.00 | 3 | 3 | 3 | 0.00 |
| permitted (2xx) | 8001 | 8.00 | 7 | 8 | 10 | 1.12 |
| refused (403) | 6000 | 7.00 | 7 | 7 | 7 | 1.00 |

Statement shapes on the permitted path only (2):
  - `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestam`
  - `SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND sub_type_code = ? AND realm_id `

## Per-API SQL and statement volume

| op | surface | requests | statuses | stmts | stmts/req | grant_records/req |
|---|---|---:|---|---:|---:|---:|
| `GET  /catalog-roles/{r}/grants` | mgmt | 1000 | 200×1000 | 10000 | 10.00 | 2.00 |
| `GET  /catalogs/{c}/catalog-roles` | mgmt | 1000 | 200×1000 | 8000 | 8.00 | 1.00 |
| `GET  /namespaces` | iceberg | 2000 | 200×2000 | 16000 | 8.00 | 1.00 |
| `GET  /namespaces/{ns}/tables` | iceberg | 1000 | 200×1000 | 8000 | 8.00 | 1.00 |
| `GET  /namespaces/{ns}/views` | iceberg | 1000 | 200×1000 | 8000 | 8.00 | 1.00 |
| `GET  /catalogs` | mgmt | 1000 | 403×1000 | 7000 | 7.00 | 1.00 |
| `GET  /catalogs/{name}` | mgmt | 1001 | 200×1001 | 7007 | 7.00 | 1.00 |
| `GET  /namespaces/{ns}` | iceberg | 1000 | 200×1000 | 7000 | 7.00 | 1.00 |
| `GET  /principal-roles` | mgmt | 1000 | 403×1000 | 7000 | 7.00 | 1.00 |
| `GET  /principal-roles/{name}` | mgmt | 1000 | 403×1000 | 7000 | 7.00 | 1.00 |
| `GET  /principal-roles/{n}/principals` | mgmt | 1000 | 403×1000 | 7000 | 7.00 | 1.00 |
| `GET  /principals` | mgmt | 1000 | 403×1000 | 7000 | 7.00 | 1.00 |
| `GET  /principals/{name}` | mgmt | 1000 | 403×1000 | 7000 | 7.00 | 1.00 |
| `POST /oauth/tokens` | auth | 1001 | 200×1001 | 3003 | 3.00 | 0.00 |

## Distinct statements

| n | reqs | /req | table | verb | params | statement |
|---:|---:|---:|---|---|---|---|
| 29003 | 15002 | 1.93 | entities | SELECT | observed | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_u…` |
| 29002 | 14001 | 2.07 | entities | SELECT | observed | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_u…` |
| 15002 | 15002 | 1.00 | entities | SELECT | observed | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_u…` |
| 15001 | 14001 | 1.07 | entities | SELECT | observed | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_u…` |
| 15001 | 14001 | 1.07 | grant_records | SELECT | observed | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id =…` |
| 4000 | 4000 | 1.00 | entities | SELECT | observed | `SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND sub_type_code = ? AND realm_id = ? AND p…` |
| 1001 | 1001 | 1.00 | principal_authentication_data | SELECT | redacted | `SELECT principal_id, principal_client_id, main_secret_hash, secondary_secret_hash, secret_salt FROM POLARIS_SCHEMA.PRINCIPAL_AUTHENTICATION_DATA WHERE realm_id…` |
| 1000 | 1000 | 1.00 | entities | SELECT | observed | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_u…` |

## Access path per statement

EXPLAIN (ANALYZE, BUFFERS) on the primary at `192.168.194.37`, `/*NO LOAD BALANCE*/`, `pg_is_in_recovery() = false` asserted, `max_parallel_workers_per_gather = 0` pinned session-scoped.

| n | table | scan | index | buffers | rows removed by filter | rows out |
|---:|---|---|---|---|---:|---:|
| 29003 | entities | Index Scan | idx_entities | hit=3 read=0 | 0 | 1 |
| 29002 | entities | Index Scan | idx_entities | hit=3 read=0 | — | 1 |
| 15002 | entities | Index Scan | constraint_name | hit=3 read=0 | — | 1 |
| 15001 | entities | Index Scan | idx_entities | hit=3 read=0 | — | 1 |
| 15001 | grant_records | Seq Scan | — | hit=516 read=0 | 55,003 | 1 |
| 4000 | entities | Index Scan | constraint_name | hit=3 read=0 | 0 | 2 |
| 1001 | principal_authentication_data | *not replayed* | — | — | — | parameters were redacted at capture (secret table); replay would need them reconstructed from the metastore |
| 1000 | entities | Index Scan | constraint_name | hit=3 read=0 | 0 | 2 |

### The grant_records lookup

Issued **15001 times** across 14001 requests (1.071 per request).

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```

```json
{
  "Plan": {
    "Node Type": "Seq Scan",
    "Parallel Aware": false,
    "Async Capable": false,
    "Relation Name": "grant_records",
    "Alias": "grant_records",
    "Startup Cost": 0.0,
    "Total Cost": 1478.57,
    "Plan Rows": 1,
    "Plan Width": 36,
    "Actual Startup Time": 0.004,
    "Actual Total Time": 4.055,
    "Actual Rows": 1,
    "Actual Loops": 1,
    "Filter": "((grantee_id = '2761039760315785594'::bigint) AND (realm_id = 'POLARIS'::text) AND (grantee_catalog_id = '0'::bigint))",
    "Rows Removed by Filter": 55003,
    "Shared Hit Blocks": 516,
    "Shared Read Blocks": 0,
    "Shared Dirtied Blocks": 0,
    "Shared Written Blocks": 0,
    "Local Hit Blocks": 0,
    "Local Read Blocks": 0,
    "Local Dirtied Blocks": 0,
    "Local Written Blocks": 0,
    "Temp Read Blocks": 0,
    "Temp Written Blocks": 0
  },
  "Planning": {
    "Shared Hit Blocks": 0,
    "Shared Read Blocks": 0,
    "Shared Dirtied Blocks": 0,
    "Shared Written Blocks": 0,
    "Local Hit Blocks": 0,
    "Local Read Blocks": 0,
    "Local Dirtied Blocks": 0,
    "Local Written Blocks": 0,
    "Temp Read Blocks": 0,
    "Temp Written Blocks": 0
  },
  "Planning Time": 0.026,
  "Triggers": [],
  "Execution Time": 4.06
}
```

The scan returned **1** rows and discarded **55,003** to get them. That ratio, and the buffer count beside it, are identical across reruns; the milliseconds are not.

## What this pass does not establish

- **It covers 13 of the 29 GET/HEAD operations the 1.3.0 spec defines — 45% of the readable surface.** The omissions are not evenly spread: the four missing MANAGEMENT reads are exactly the role-graph traversals (`listPrincipalRolesAssigned`, `listCatalogRolesForPrincipalRole`, `getCatalogRole`, `listAssigneePrincipalRolesForCatalogRole`), which is the authorization model itself and therefore the part of the surface most likely to touch `grant_records` more than once. Also absent: `getConfig`, `loadTable`, `loadView`, `loadCredentials`, all three HEAD existence checks, and all five Polaris extension GETs. See `PLAN-authorized-get-surface.md`.
- **`listTables` and `listViews` were driven against an EMPTY collection.** `capture/seed_ledger.json` records `create_tables: False`: this fixture has 1,000 catalogs x 2 namespaces and zero tables, zero views. Their measured 8.00 statements/request is the cost of listing NOTHING. A listing that returns rows may issue more; it certainly does not issue fewer. The entity-level reads are not merely untested here but undriveable — there is no table to load.
- **The index-present contrast.** This is the index ABSENT half. The Seq→Index comparison needs the same drive re-run with `idx_grant_records_grantee` created and `ANALYZE` done, into a rotated capture.
- **Latency.** Statement logging was on for this pass, a measured 4.6x inflation. Any millisecond figure here is illustration beside the buffer evidence, never a number to quote. Real latency is Pass B, logging off.
- **Write paths.** The drive is read-only by construction; four write statements remain `NO_PARAMS` and unmeasured (MEMORY, Active Issues).
- **Generic vs custom plans.** These statements are replayed verbatim from the capture — the same SQL Polaris executed — but psycopg2 interpolates the bound values as literals, so the planner sees constants and produces a CUSTOM plan. Polaris issues them through JDBC as server-side prepared statements, which PostgreSQL may switch to a GENERIC plan after five executions. For an unindexed scan at this volume both are the same shape, so the finding holds either way — but the plans here are not proof about which one the server chose at runtime, and this report does not claim they are.
