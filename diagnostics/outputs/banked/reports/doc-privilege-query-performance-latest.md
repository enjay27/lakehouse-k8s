# Privilege query performance — Pass A, index ABSENT

Generated 2026-08-31 11:18:29 from capture `capture-admin-noindex` and run `20260831-105456`. Volume, index state and request counts below are **measured**, not carried over from a plan document.

## What was measured

- realm `POLARIS`, prefix `admin`
- **5 identities**, 5 authenticated, **160 requests** in 2.6 s (the drive's own clock, discarded — logging on)
- capture window `2026-08-31T01:54:52.218848009Z` → `2026-08-31T01:54:56.867430273Z`
- `polaris_schema.grant_records`: **60,784 rows** at EXPLAIN time
- index state on `grant_records`: index ABSENT
  - `grant_records_pkey`
- provenance: 1,000 real API-seeded principals. Nothing synthetic, nothing to disclose.

## Capture integrity

- access-log requests correlated: **162**
- statements parsed: **1556**
- every parsed statement mapped to a request. No orphans.
- **61 path shapes did not match the op surface** — reported under their raw path, never silently dropped:
  - `GET /api/catalog/v1/config` ×5
  - `GET /api/catalog/polaris/v1/admin1_catalog/namespaces/ns1/generic-tables` ×2
  - `GET /api/catalog/polaris/v1/admin1_catalog/namespaces/ns1/policies` ×2
  - `GET /api/catalog/polaris/v1/admin2_catalog/namespaces/ns1/generic-tables` ×2
  - `GET /api/catalog/polaris/v1/admin2_catalog/namespaces/ns1/policies` ×2
  - `GET /api/catalog/polaris/v1/admin3_catalog/namespaces/ns1/generic-tables` ×2
  - `GET /api/catalog/polaris/v1/admin3_catalog/namespaces/ns1/policies` ×2
  - `GET /api/catalog/polaris/v1/admin4_catalog/namespaces/ns1/generic-tables` ×2
  - `GET /api/catalog/polaris/v1/admin4_catalog/namespaces/ns1/policies` ×2
  - `GET /api/catalog/polaris/v1/admin5_catalog/namespaces/ns1/generic-tables` ×2

| op | run JSON | capture | delta |
|---|---:|---:|---:|
| `GET  /applicable-policies` | 5 | 0 | -5 |
| `GET  /catalog-roles/{r}/grants` | 5 | 5 | +0 |
| `GET  /catalog-roles/{r}/principal-roles` | 5 | 0 | -5 |
| `GET  /catalogs` | 5 | 5 | +0 |
| `GET  /catalogs/{c}/catalog-roles` | 5 | 5 | +0 |
| `GET  /catalogs/{c}/catalog-roles/{r}` | 5 | 0 | -5 |
| `GET  /catalogs/{name}` | 5 | 6 | +1 |
| `GET  /config` | 5 | 0 | -5 |
| `GET  /generic-tables`  *(incl. harness resolve calls)* | 10 | 0 | -10 |
| `GET  /generic-tables/{gt}` | 0 | 0 | +0 |
| `GET  /namespaces`  *(incl. harness resolve calls)* | 10 | 10 | +0 |
| `GET  /namespaces/{ns}` | 5 | 5 | +0 |
| `GET  /namespaces/{ns}/tables`  *(incl. harness resolve calls)* | 10 | 10 | +0 |
| `GET  /namespaces/{ns}/tables/{t}` | 5 | 0 | -5 |
| `GET  /namespaces/{ns}/tables/{t}/credentials` | 0 | 0 | +0 |
| `GET  /namespaces/{ns}/views`  *(incl. harness resolve calls)* | 10 | 10 | +0 |
| `GET  /namespaces/{ns}/views/{v}` | 5 | 0 | -5 |
| `GET  /policies`  *(incl. harness resolve calls)* | 10 | 0 | -10 |
| `GET  /policies/{p}` | 0 | 0 | +0 |
| `GET  /principal-roles` | 5 | 5 | +0 |
| `GET  /principal-roles/{name}` | 5 | 5 | +0 |
| `GET  /principal-roles/{n}/catalog-roles/{c}` | 5 | 0 | -5 |
| `GET  /principal-roles/{n}/principals` | 5 | 5 | +0 |
| `GET  /principals` | 5 | 5 | +0 |
| `GET  /principals/{name}` | 5 | 5 | +0 |
| `GET  /principals/{p}/principal-roles` | 5 | 0 | -5 |
| `GET /api/catalog/polaris/v1/admin1_catalog/applicable-policies` | 0 | 1 | +1 |
| `GET /api/catalog/polaris/v1/admin1_catalog/namespaces/ns1/generic-tables` | 0 | 2 | +2 |
| `GET /api/catalog/polaris/v1/admin1_catalog/namespaces/ns1/policies` | 0 | 2 | +2 |
| `GET /api/catalog/polaris/v1/admin2_catalog/applicable-policies` | 0 | 1 | +1 |
| `GET /api/catalog/polaris/v1/admin2_catalog/namespaces/ns1/generic-tables` | 0 | 2 | +2 |
| `GET /api/catalog/polaris/v1/admin2_catalog/namespaces/ns1/policies` | 0 | 2 | +2 |
| `GET /api/catalog/polaris/v1/admin3_catalog/applicable-policies` | 0 | 1 | +1 |
| `GET /api/catalog/polaris/v1/admin3_catalog/namespaces/ns1/generic-tables` | 0 | 2 | +2 |
| `GET /api/catalog/polaris/v1/admin3_catalog/namespaces/ns1/policies` | 0 | 2 | +2 |
| `GET /api/catalog/polaris/v1/admin4_catalog/applicable-policies` | 0 | 1 | +1 |
| `GET /api/catalog/polaris/v1/admin4_catalog/namespaces/ns1/generic-tables` | 0 | 2 | +2 |
| `GET /api/catalog/polaris/v1/admin4_catalog/namespaces/ns1/policies` | 0 | 2 | +2 |
| `GET /api/catalog/polaris/v1/admin5_catalog/applicable-policies` | 0 | 1 | +1 |
| `GET /api/catalog/polaris/v1/admin5_catalog/namespaces/ns1/generic-tables` | 0 | 2 | +2 |
| `GET /api/catalog/polaris/v1/admin5_catalog/namespaces/ns1/policies` | 0 | 2 | +2 |
| `GET /api/catalog/v1/admin1_catalog/namespaces/ns1/tables/tbl1` | 0 | 1 | +1 |
| `GET /api/catalog/v1/admin1_catalog/namespaces/ns1/views/vw1` | 0 | 1 | +1 |
| `GET /api/catalog/v1/admin2_catalog/namespaces/ns1/tables/tbl1` | 0 | 1 | +1 |
| `GET /api/catalog/v1/admin2_catalog/namespaces/ns1/views/vw1` | 0 | 1 | +1 |
| `GET /api/catalog/v1/admin3_catalog/namespaces/ns1/tables/tbl1` | 0 | 1 | +1 |
| `GET /api/catalog/v1/admin3_catalog/namespaces/ns1/views/vw1` | 0 | 1 | +1 |
| `GET /api/catalog/v1/admin4_catalog/namespaces/ns1/tables/tbl1` | 0 | 1 | +1 |
| `GET /api/catalog/v1/admin4_catalog/namespaces/ns1/views/vw1` | 0 | 1 | +1 |
| `GET /api/catalog/v1/admin5_catalog/namespaces/ns1/tables/tbl1` | 0 | 1 | +1 |
| `GET /api/catalog/v1/admin5_catalog/namespaces/ns1/views/vw1` | 0 | 1 | +1 |
| `GET /api/catalog/v1/config` | 0 | 5 | +5 |
| `GET /api/management/v1/catalogs/admin1_catalog/catalog-roles/owner_principal` | 0 | 1 | +1 |
| `GET /api/management/v1/catalogs/admin1_catalog/catalog-roles/owner_principal/principal-roles` | 0 | 1 | +1 |
| `GET /api/management/v1/catalogs/admin2_catalog/catalog-roles/owner_principal` | 0 | 1 | +1 |
| `GET /api/management/v1/catalogs/admin2_catalog/catalog-roles/owner_principal/principal-roles` | 0 | 1 | +1 |
| `GET /api/management/v1/catalogs/admin3_catalog/catalog-roles/owner_principal` | 0 | 1 | +1 |
| `GET /api/management/v1/catalogs/admin3_catalog/catalog-roles/owner_principal/principal-roles` | 0 | 1 | +1 |
| `GET /api/management/v1/catalogs/admin4_catalog/catalog-roles/owner_principal` | 0 | 1 | +1 |
| `GET /api/management/v1/catalogs/admin4_catalog/catalog-roles/owner_principal/principal-roles` | 0 | 1 | +1 |
| `GET /api/management/v1/catalogs/admin5_catalog/catalog-roles/owner_principal` | 0 | 1 | +1 |
| `GET /api/management/v1/catalogs/admin5_catalog/catalog-roles/owner_principal/principal-roles` | 0 | 1 | +1 |
| `GET /api/management/v1/principal-roles/admin1_principal_role/catalog-roles/admin1_catalog` | 0 | 1 | +1 |
| `GET /api/management/v1/principal-roles/admin2_principal_role/catalog-roles/admin2_catalog` | 0 | 1 | +1 |
| `GET /api/management/v1/principal-roles/admin3_principal_role/catalog-roles/admin3_catalog` | 0 | 1 | +1 |
| `GET /api/management/v1/principal-roles/admin4_principal_role/catalog-roles/admin4_catalog` | 0 | 1 | +1 |
| `GET /api/management/v1/principal-roles/admin5_principal_role/catalog-roles/admin5_catalog` | 0 | 1 | +1 |
| `GET /api/management/v1/principals/admin1_principal/principal-roles` | 0 | 1 | +1 |
| `GET /api/management/v1/principals/admin2_principal/principal-roles` | 0 | 1 | +1 |
| `GET /api/management/v1/principals/admin3_principal/principal-roles` | 0 | 1 | +1 |
| `GET /api/management/v1/principals/admin4_principal/principal-roles` | 0 | 1 | +1 |
| `GET /api/management/v1/principals/admin5_principal/principal-roles` | 0 | 1 | +1 |
| `HEAD /api/catalog/v1/admin1_catalog/namespaces/ns1` | 0 | 1 | +1 |
| `HEAD /api/catalog/v1/admin1_catalog/namespaces/ns1/tables/tbl1` | 0 | 1 | +1 |
| `HEAD /api/catalog/v1/admin1_catalog/namespaces/ns1/views/vw1` | 0 | 1 | +1 |
| `HEAD /api/catalog/v1/admin2_catalog/namespaces/ns1` | 0 | 1 | +1 |
| `HEAD /api/catalog/v1/admin2_catalog/namespaces/ns1/tables/tbl1` | 0 | 1 | +1 |
| `HEAD /api/catalog/v1/admin2_catalog/namespaces/ns1/views/vw1` | 0 | 1 | +1 |
| `HEAD /api/catalog/v1/admin3_catalog/namespaces/ns1` | 0 | 1 | +1 |
| `HEAD /api/catalog/v1/admin3_catalog/namespaces/ns1/tables/tbl1` | 0 | 1 | +1 |
| `HEAD /api/catalog/v1/admin3_catalog/namespaces/ns1/views/vw1` | 0 | 1 | +1 |
| `HEAD /api/catalog/v1/admin4_catalog/namespaces/ns1` | 0 | 1 | +1 |
| `HEAD /api/catalog/v1/admin4_catalog/namespaces/ns1/tables/tbl1` | 0 | 1 | +1 |
| `HEAD /api/catalog/v1/admin4_catalog/namespaces/ns1/views/vw1` | 0 | 1 | +1 |
| `HEAD /api/catalog/v1/admin5_catalog/namespaces/ns1` | 0 | 1 | +1 |
| `HEAD /api/catalog/v1/admin5_catalog/namespaces/ns1/tables/tbl1` | 0 | 1 | +1 |
| `HEAD /api/catalog/v1/admin5_catalog/namespaces/ns1/views/vw1` | 0 | 1 | +1 |
| `HEAD /namespaces/{ns}` | 5 | 0 | -5 |
| `HEAD /namespaces/{ns}/tables/{t}` | 5 | 0 | -5 |
| `HEAD /namespaces/{ns}/views/{v}` | 5 | 0 | -5 |
| `POST /oauth/tokens` | 5 | 6 | +1 |
| **total** | **160** | **162** | **+2** |

**The capture and the run disagree by +2 requests.** Every figure below describes what the capture holds, which is not what the drive issued. Resolve this before quoting anything from it.

## Does a refused request pay the authorization prelude?

`scan_privileges.py` asserts that it does. This pass drove the refused operations for **every** identity, so the question is answered from the capture instead:

| request class | requests | stmts/req | min | median | max | grant_records/req |
|---|---:|---:|---:|---:|---:|---:|
| auth (token) | 6 | 3.00 | 3 | 3 | 3 | 0.00 |
| permitted (2xx) | 81 | 9.63 | 8 | 9 | 17 | 1.52 |
| unclassified (not an op) | 75 | 10.11 | 8 | 10 | 13 | 1.41 |

Statement shapes on the permitted path only (9):
  - `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestam`
  - `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestam`
  - `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestam`
  - `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestam`
  - `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestam`
  - `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestam`
  - `SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND sub_type_code = ? AND realm_id `
  - `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id =`
  - `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_id = ? AND`

## Per-API SQL and statement volume

| op | surface | requests | statuses | stmts | stmts/req | grant_records/req |
|---|---|---:|---|---:|---:|---:|
| `GET /api/catalog/v1/admin2_catalog/namespaces/ns1/tables/tbl1` | unclassified | 1 | 200×1 | 13 | 13.00 | 2.00 |
| `GET /api/catalog/v1/admin2_catalog/namespaces/ns1/views/vw1` | unclassified | 1 | 200×1 | 13 | 13.00 | 2.00 |
| `GET /api/catalog/v1/admin3_catalog/namespaces/ns1/tables/tbl1` | unclassified | 1 | 200×1 | 13 | 13.00 | 2.00 |
| `GET /api/catalog/v1/admin3_catalog/namespaces/ns1/views/vw1` | unclassified | 1 | 200×1 | 13 | 13.00 | 2.00 |
| `GET /api/catalog/v1/admin4_catalog/namespaces/ns1/tables/tbl1` | unclassified | 1 | 200×1 | 13 | 13.00 | 2.00 |
| `GET /api/catalog/v1/admin4_catalog/namespaces/ns1/views/vw1` | unclassified | 1 | 200×1 | 13 | 13.00 | 2.00 |
| `GET /api/catalog/v1/admin5_catalog/namespaces/ns1/tables/tbl1` | unclassified | 1 | 200×1 | 13 | 13.00 | 2.00 |
| `GET /api/catalog/v1/admin5_catalog/namespaces/ns1/views/vw1` | unclassified | 1 | 200×1 | 13 | 13.00 | 2.00 |
| `GET  /namespaces` | iceberg | 10 | 200×10 | 122 | 12.20 | 3.00 |
| `GET /api/catalog/polaris/v1/admin1_catalog/applicable-policies` | unclassified | 1 | 200×1 | 12 | 12.00 | 1.00 |
| `GET /api/catalog/polaris/v1/admin2_catalog/applicable-policies` | unclassified | 1 | 200×1 | 12 | 12.00 | 1.00 |
| `GET /api/catalog/polaris/v1/admin3_catalog/applicable-policies` | unclassified | 1 | 200×1 | 12 | 12.00 | 1.00 |
| `GET /api/catalog/polaris/v1/admin4_catalog/applicable-policies` | unclassified | 1 | 200×1 | 12 | 12.00 | 1.00 |
| `GET /api/catalog/polaris/v1/admin5_catalog/applicable-policies` | unclassified | 1 | 200×1 | 12 | 12.00 | 1.00 |
| `GET  /catalog-roles/{r}/grants` | mgmt | 5 | 200×5 | 55 | 11.00 | 2.00 |
| `GET  /principal-roles/{n}/principals` | mgmt | 5 | 200×5 | 55 | 11.00 | 2.00 |
| `GET /api/catalog/v1/admin1_catalog/namespaces/ns1/tables/tbl1` | unclassified | 1 | 200×1 | 11 | 11.00 | 1.00 |
| `GET /api/catalog/v1/admin1_catalog/namespaces/ns1/views/vw1` | unclassified | 1 | 200×1 | 11 | 11.00 | 1.00 |
| `GET /api/management/v1/catalogs/admin1_catalog/catalog-roles/owner_principal/principal-roles` | unclassified | 1 | 200×1 | 11 | 11.00 | 2.00 |
| `GET /api/management/v1/catalogs/admin2_catalog/catalog-roles/owner_principal` | unclassified | 1 | 200×1 | 11 | 11.00 | 3.00 |
| `GET /api/management/v1/catalogs/admin2_catalog/catalog-roles/owner_principal/principal-roles` | unclassified | 1 | 200×1 | 11 | 11.00 | 2.00 |
| `GET /api/management/v1/catalogs/admin3_catalog/catalog-roles/owner_principal` | unclassified | 1 | 200×1 | 11 | 11.00 | 3.00 |
| `GET /api/management/v1/catalogs/admin3_catalog/catalog-roles/owner_principal/principal-roles` | unclassified | 1 | 200×1 | 11 | 11.00 | 2.00 |
| `GET /api/management/v1/catalogs/admin4_catalog/catalog-roles/owner_principal` | unclassified | 1 | 200×1 | 11 | 11.00 | 3.00 |
| `GET /api/management/v1/catalogs/admin4_catalog/catalog-roles/owner_principal/principal-roles` | unclassified | 1 | 200×1 | 11 | 11.00 | 2.00 |
| `GET /api/management/v1/catalogs/admin5_catalog/catalog-roles/owner_principal` | unclassified | 1 | 200×1 | 11 | 11.00 | 3.00 |
| `GET /api/management/v1/catalogs/admin5_catalog/catalog-roles/owner_principal/principal-roles` | unclassified | 1 | 200×1 | 11 | 11.00 | 2.00 |
| `GET /api/management/v1/principal-roles/admin1_principal_role/catalog-roles/admin1_catalog` | unclassified | 1 | 200×1 | 11 | 11.00 | 2.00 |
| `GET /api/management/v1/principal-roles/admin2_principal_role/catalog-roles/admin2_catalog` | unclassified | 1 | 200×1 | 11 | 11.00 | 2.00 |
| `GET /api/management/v1/principal-roles/admin3_principal_role/catalog-roles/admin3_catalog` | unclassified | 1 | 200×1 | 11 | 11.00 | 2.00 |
| `GET /api/management/v1/principal-roles/admin4_principal_role/catalog-roles/admin4_catalog` | unclassified | 1 | 200×1 | 11 | 11.00 | 2.00 |
| `GET /api/management/v1/principal-roles/admin5_principal_role/catalog-roles/admin5_catalog` | unclassified | 1 | 200×1 | 11 | 11.00 | 2.00 |
| `GET /api/management/v1/principals/admin1_principal/principal-roles` | unclassified | 1 | 200×1 | 11 | 11.00 | 2.00 |
| `GET /api/management/v1/principals/admin2_principal/principal-roles` | unclassified | 1 | 200×1 | 11 | 11.00 | 2.00 |
| `GET /api/management/v1/principals/admin3_principal/principal-roles` | unclassified | 1 | 200×1 | 11 | 11.00 | 2.00 |
| `GET /api/management/v1/principals/admin4_principal/principal-roles` | unclassified | 1 | 200×1 | 11 | 11.00 | 2.00 |
| `GET /api/management/v1/principals/admin5_principal/principal-roles` | unclassified | 1 | 200×1 | 11 | 11.00 | 2.00 |
| `GET  /principal-roles/{name}` | mgmt | 5 | 200×5 | 52 | 10.40 | 2.60 |
| `HEAD /api/catalog/v1/admin1_catalog/namespaces/ns1/views/vw1` | unclassified | 1 | 204×1 | 10 | 10.00 | 1.00 |
| `HEAD /api/catalog/v1/admin2_catalog/namespaces/ns1/views/vw1` | unclassified | 1 | 204×1 | 10 | 10.00 | 1.00 |
| `HEAD /api/catalog/v1/admin3_catalog/namespaces/ns1/views/vw1` | unclassified | 1 | 204×1 | 10 | 10.00 | 1.00 |
| `HEAD /api/catalog/v1/admin4_catalog/namespaces/ns1/views/vw1` | unclassified | 1 | 204×1 | 10 | 10.00 | 1.00 |
| `HEAD /api/catalog/v1/admin5_catalog/namespaces/ns1/views/vw1` | unclassified | 1 | 204×1 | 10 | 10.00 | 1.00 |
| `GET  /namespaces/{ns}/tables` | iceberg | 10 | 200×10 | 98 | 9.80 | 1.40 |
| `GET  /catalogs` | mgmt | 5 | 200×5 | 45 | 9.00 | 1.00 |
| `GET  /catalogs/{c}/catalog-roles` | mgmt | 5 | 200×5 | 45 | 9.00 | 1.00 |
| `GET  /namespaces/{ns}/views` | iceberg | 10 | 200×10 | 90 | 9.00 | 1.00 |
| `GET  /principal-roles` | mgmt | 5 | 200×5 | 45 | 9.00 | 1.00 |
| `GET  /principals` | mgmt | 5 | 200×5 | 45 | 9.00 | 1.00 |
| `GET /api/catalog/polaris/v1/admin1_catalog/namespaces/ns1/generic-tables` | unclassified | 2 | 200×2 | 18 | 9.00 | 1.00 |
| `GET /api/catalog/polaris/v1/admin1_catalog/namespaces/ns1/policies` | unclassified | 2 | 200×2 | 18 | 9.00 | 1.00 |
| `GET /api/catalog/polaris/v1/admin2_catalog/namespaces/ns1/generic-tables` | unclassified | 2 | 200×2 | 18 | 9.00 | 1.00 |
| `GET /api/catalog/polaris/v1/admin2_catalog/namespaces/ns1/policies` | unclassified | 2 | 200×2 | 18 | 9.00 | 1.00 |
| `GET /api/catalog/polaris/v1/admin3_catalog/namespaces/ns1/generic-tables` | unclassified | 2 | 200×2 | 18 | 9.00 | 1.00 |
| `GET /api/catalog/polaris/v1/admin3_catalog/namespaces/ns1/policies` | unclassified | 2 | 200×2 | 18 | 9.00 | 1.00 |
| `GET /api/catalog/polaris/v1/admin4_catalog/namespaces/ns1/generic-tables` | unclassified | 2 | 200×2 | 18 | 9.00 | 1.00 |
| `GET /api/catalog/polaris/v1/admin4_catalog/namespaces/ns1/policies` | unclassified | 2 | 200×2 | 18 | 9.00 | 1.00 |
| `GET /api/catalog/polaris/v1/admin5_catalog/namespaces/ns1/generic-tables` | unclassified | 2 | 200×2 | 18 | 9.00 | 1.00 |
| `GET /api/catalog/polaris/v1/admin5_catalog/namespaces/ns1/policies` | unclassified | 2 | 200×2 | 18 | 9.00 | 1.00 |
| `HEAD /api/catalog/v1/admin1_catalog/namespaces/ns1/tables/tbl1` | unclassified | 1 | 204×1 | 9 | 9.00 | 1.00 |
| `HEAD /api/catalog/v1/admin2_catalog/namespaces/ns1/tables/tbl1` | unclassified | 1 | 204×1 | 9 | 9.00 | 1.00 |
| `HEAD /api/catalog/v1/admin3_catalog/namespaces/ns1/tables/tbl1` | unclassified | 1 | 204×1 | 9 | 9.00 | 1.00 |
| `HEAD /api/catalog/v1/admin4_catalog/namespaces/ns1/tables/tbl1` | unclassified | 1 | 204×1 | 9 | 9.00 | 1.00 |
| `HEAD /api/catalog/v1/admin5_catalog/namespaces/ns1/tables/tbl1` | unclassified | 1 | 204×1 | 9 | 9.00 | 1.00 |
| `GET  /catalogs/{name}` | mgmt | 6 | 200×6 | 48 | 8.00 | 1.00 |
| `GET  /namespaces/{ns}` | iceberg | 5 | 200×5 | 40 | 8.00 | 1.00 |
| `GET  /principals/{name}` | mgmt | 5 | 200×5 | 40 | 8.00 | 1.00 |
| `GET /api/catalog/v1/config` | unclassified | 5 | 200×5 | 40 | 8.00 | 1.00 |
| `GET /api/management/v1/catalogs/admin1_catalog/catalog-roles/owner_principal` | unclassified | 1 | 200×1 | 8 | 8.00 | 1.00 |
| `HEAD /api/catalog/v1/admin1_catalog/namespaces/ns1` | unclassified | 1 | 204×1 | 8 | 8.00 | 1.00 |
| `HEAD /api/catalog/v1/admin2_catalog/namespaces/ns1` | unclassified | 1 | 204×1 | 8 | 8.00 | 1.00 |
| `HEAD /api/catalog/v1/admin3_catalog/namespaces/ns1` | unclassified | 1 | 204×1 | 8 | 8.00 | 1.00 |
| `HEAD /api/catalog/v1/admin4_catalog/namespaces/ns1` | unclassified | 1 | 204×1 | 8 | 8.00 | 1.00 |
| `HEAD /api/catalog/v1/admin5_catalog/namespaces/ns1` | unclassified | 1 | 204×1 | 8 | 8.00 | 1.00 |
| `POST /oauth/tokens` | auth | 6 | 200×6 | 18 | 3.00 | 0.00 |

## Distinct statements

| n | reqs | /req | table | verb | params | statement |
|---:|---:|---:|---|---|---|---|
| 503 | 162 | 3.10 | entities | SELECT | observed | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_u…` |
| 367 | 156 | 2.35 | entities | SELECT | observed | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_u…` |
| 190 | 162 | 1.17 | entities | SELECT | observed | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_u…` |
| 187 | 156 | 1.20 | grant_records | SELECT | observed | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND gr…` |
| 181 | 156 | 1.16 | entities | SELECT | observed | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_u…` |
| 50 | 50 | 1.00 | entities | SELECT | observed | `SELECT id, catalog_id, parent_id, type_code, name, sub_type_code FROM POLARIS_SCHEMA.ENTITIES WHERE catalog_id = ? AND sub_type_code = ? AND realm_id = ? AND p…` |
| 42 | 34 | 1.24 | grant_records | SELECT | observed | `SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_id = ? AND securabl…` |
| 15 | 15 | 1.00 | entities | SELECT | observed | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_u…` |
| 10 | 5 | 2.00 | policy_mapping_record | SELECT | observed | `SELECT target_catalog_id, target_id, policy_type_code, policy_catalog_id, policy_id, parameters FROM POLARIS_SCHEMA.POLICY_MAPPING_RECORD WHERE target_id = ? A…` |
| 6 | 6 | 1.00 | principal_authentication_data | SELECT | redacted | `SELECT principal_id, principal_client_id, main_secret_hash, secondary_secret_hash, secret_salt FROM POLARIS_SCHEMA.PRINCIPAL_AUTHENTICATION_DATA WHERE principa…` |
| 5 | 5 | 1.00 | entities | SELECT | observed | `SELECT id, catalog_id, parent_id, type_code, name, entity_version, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp, last_u…` |

## Access path per statement

EXPLAIN (ANALYZE, BUFFERS) on the primary at `192.168.194.103`, `/*NO LOAD BALANCE*/`, `pg_is_in_recovery() = false` asserted, `max_parallel_workers_per_gather = 0` pinned session-scoped.

| n | table | scan | index | buffers | rows removed by filter | rows out |
|---:|---|---|---|---|---:|---:|
| 503 | entities | Index Scan | idx_entities | hit=3 read=0 | 0 | 1 |
| 367 | entities | Bitmap Heap Scan | — | hit=7 read=0 | 0 | 2 |
| 190 | entities | Index Scan | constraint_name | hit=3 read=0 | — | 1 |
| 187 | grant_records | Seq Scan | — | hit=572 read=0 | 60,782 | 2 |
| 181 | entities | Index Scan | idx_entities | hit=3 read=0 | — | 1 |
| 50 | entities | Index Scan | constraint_name | hit=4 read=0 | 0 | 2 |
| 42 | grant_records | Index Only Scan | grant_records_pkey | hit=5 read=0 | — | 1 |
| 15 | entities | Index Scan | constraint_name | hit=763 read=0 | 0 | 1,106 |
| 10 | policy_mapping_record | Index Scan | policy_mapping_record_pkey | hit=2 read=0 | — | 0 |
| 6 | principal_authentication_data | *not replayed* | — | — | — | parameters were redacted at capture (secret table); replay would need them reconstructed from the metastore |
| 5 | entities | Index Scan | constraint_name | hit=780 read=0 | — | 1,105 |

### The grant_records lookup

Issued **187 times** across 156 requests (1.199 per request).

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
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
    "Total Cost": 1635.72,
    "Plan Rows": 1,
    "Plan Width": 36,
    "Actual Startup Time": 2.104,
    "Actual Total Time": 2.122,
    "Actual Rows": 2,
    "Actual Loops": 1,
    "Filter": "((grantee_catalog_id = '0'::bigint) AND (grantee_id = '9118527594773052894'::bigint) AND (realm_id = 'POLARIS'::text))",
    "Rows Removed by Filter": 60782,
    "Shared Hit Blocks": 572,
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
  "Planning Time": 0.024,
  "Triggers": [],
  "Execution Time": 2.127
}
```

The scan returned **2** rows and discarded **60,782** to get them. That ratio, and the buffer count beside it, are identical across reruns; the milliseconds are not.

Issued **42 times** across 34 requests (1.235 per request).

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE securable_id = ? AND securable_catalog_id = ? AND realm_id = ?
```

```json
{
  "Plan": {
    "Node Type": "Index Only Scan",
    "Parallel Aware": false,
    "Async Capable": false,
    "Scan Direction": "Forward",
    "Index Name": "grant_records_pkey",
    "Relation Name": "grant_records",
    "Alias": "grant_records",
    "Startup Cost": 0.41,
    "Total Cost": 12.34,
    "Plan Rows": 19,
    "Plan Width": 36,
    "Actual Startup Time": 0.005,
    "Actual Total Time": 0.005,
    "Actual Rows": 1,
    "Actual Loops": 1,
    "Index Cond": "((realm_id = 'POLARIS'::text) AND (securable_catalog_id = '0'::bigint) AND (securable_id = '3340119121637991836'::bigint))",
    "Rows Removed by Index Recheck": 0,
    "Heap Fetches": 1,
    "Shared Hit Blocks": 5,
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
  "Planning Time": 0.016,
  "Triggers": [],
  "Execution Time": 0.009
}
```

## What this pass does not establish

- **The index-present contrast.** This is the index ABSENT half. The Seq→Index comparison needs the same drive re-run with `idx_grant_records_grantee` created and `ANALYZE` done, into a rotated capture.
- **Latency.** Statement logging was on for this pass, a measured 4.6x inflation. Any millisecond figure here is illustration beside the buffer evidence, never a number to quote. Real latency is Pass B, logging off.
- **Write paths.** The drive is read-only by construction; four write statements remain `NO_PARAMS` and unmeasured (MEMORY, Active Issues).
- **Generic vs custom plans.** These statements are replayed verbatim from the capture — the same SQL Polaris executed — but psycopg2 interpolates the bound values as literals, so the planner sees constants and produces a CUSTOM plan. Polaris issues them through JDBC as server-side prepared statements, which PostgreSQL may switch to a GENERIC plan after five executions. For an unindexed scan at this volume both are the same shape, so the finding holds either way — but the plans here are not proof about which one the server chose at runtime, and this report does not claim they are.
