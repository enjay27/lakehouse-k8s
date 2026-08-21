-- Polaris bootstrap  --  pure server-side SQL, no psql meta-commands.
--
-- Run with:
--   psql -U polaris -d polaris -v ON_ERROR_STOP=1 -f bootstrap.sql
--
-- There are deliberately NO backslash commands in this file, so it survives
-- copy/paste, heredocs and anything else that eats backslashes.  Configure it
-- by editing the _cfg / _realms rows below.
--
-- ---------------------------------------------------------------------------
-- CORRECTED 2026-08-21.  Read this before editing the privilege codes.
-- ---------------------------------------------------------------------------
-- The previous version granted privilege codes 11 and 12.  Verified against
-- PolarisPrivilege.java at tag apache-polaris-1.3.0-incubating, those are:
--
--     11  NAMESPACE_LIST
--     12  TABLE_LIST
--
-- and the codes actually wanted are:
--
--      1  SERVICE_MANAGE_ACCESS
--      4  PRINCIPAL_ROLE_USAGE
--
-- The symptom was not a login failure, which is what made it confusing.  Root
-- authenticated, service_admin activated, its grants loaded -- and every write
-- came back 403: "Principal 'root' with activated PrincipalRoles
-- '[service_admin]' and activated grants via '[service_admin]' is not
-- authorized for op CREATE_PRINCIPAL".  The role was fine.  The privilege it
-- carried was "may list namespaces".
--
-- One grant is enough for service_admin because SERVICE_MANAGE_ACCESS is a
-- SUPER-privilege: PolarisAuthorizerImpl's SUPER_PRIVILEGES map lists it as
-- sufficient for PRINCIPAL_CREATE, CATALOG_CREATE and the rest.  That part of
-- the original design was right.
--
-- THESE NUMBERS ARE A HYPOTHESIS UNTIL AN API CALL SUCCEEDS.  This repo has now
-- been bitten three times by a constant transcribed from a spec -- the
-- 25-privilege catalog list, a catalog's own catalog_id, and these codes.  The
-- sanity check at the bottom proves the ROWS exist; only
-- `seed_polaris.py --users 1` proves they WORK.  Run it before trusting this.

SET search_path TO polaris_schema;

BEGIN;

-- ---------------------------------------------------------------------------
-- Configuration.  Edit these two blocks; everything below is derived.
-- ---------------------------------------------------------------------------
CREATE TEMP TABLE _cfg ON COMMIT DROP AS
SELECT 'f7ae9aa1a24c508fb6435b3d5cbf5677a235b400f854e0db3fdf9a4bdbf02b25'::text AS main_hash,
       'sktelecomhynix20260129'::text                                    AS salt,
       (extract(epoch FROM now()) * 1000)::bigint                        AS ts;

CREATE TEMP TABLE _realms(realm_id TEXT) ON COMMIT DROP;
INSERT INTO _realms VALUES ('POLARIS'), ('DATACORP-PROD');

-- ---------------------------------------------------------------------------
-- Entities: root_container (type 1, id 0), root principal (type 2, id 1),
--           service_admin principal role (type 3, id 2)
-- ---------------------------------------------------------------------------
INSERT INTO entities (
    realm_id, catalog_id, id, parent_id, name, entity_version,
    type_code, sub_type_code, create_timestamp, drop_timestamp,
    purge_timestamp, to_purge_timestamp, last_update_timestamp,
    properties, internal_properties, grant_records_version)
SELECT r.realm_id, 0, e.id, e.parent_id, e.name, 1,
       e.type_code, 0, c.ts, 0,
       0, 0, c.ts,
       '{}'::jsonb, e.internal_properties::jsonb, 1
FROM _realms r
         CROSS JOIN _cfg c
         CROSS JOIN (VALUES
                         (0::bigint, 0::bigint, 'root_container', 1, '{}'),
                         (1,         0,         'root',           2, '{"client_id":"root"}'),
                         (2,         0,         'service_admin',  3, '{}')
) AS e(id, parent_id, name, type_code, internal_properties);

-- ---------------------------------------------------------------------------
-- Grants.  Codes from PolarisPrivilege.java, 1.3.0-incubating -- see header.
--   root(1)          -> PRINCIPAL_ROLE_USAGE(4)   on service_admin(2)
--   service_admin(2) -> SERVICE_MANAGE_ACCESS(1)  on root_container(0)
-- ---------------------------------------------------------------------------
INSERT INTO grant_records (
    realm_id, securable_catalog_id, securable_id,
    grantee_catalog_id, grantee_id, privilege_code)
SELECT r.realm_id, 0, g.securable_id, 0, g.grantee_id, g.privilege_code
FROM _realms r
         CROSS JOIN (VALUES
                         (2::bigint, 1::bigint, 4),
                         (0,         2,         1)
) AS g(securable_id, grantee_id, privilege_code);

-- ---------------------------------------------------------------------------
-- Credentials for the root principal.
-- Hash algorithm: SHA256(secret + ':' + salt)
-- ---------------------------------------------------------------------------
INSERT INTO principal_authentication_data (
    realm_id, principal_id, principal_client_id,
    main_secret_hash, secondary_secret_hash, secret_salt)
SELECT r.realm_id, 1, 'root', c.main_hash, c.main_hash, c.salt
FROM _realms r CROSS JOIN _cfg c;

COMMIT;

-- ---------------------------------------------------------------------------
-- Sanity check.  Counts rows AND names the privileges, because counting alone
-- is exactly what let the 11/12 mistake through: "service_admin has 1 grant"
-- was true, and useless.
-- ---------------------------------------------------------------------------
SELECT realm_id, count(*) AS entities FROM entities GROUP BY 1 ORDER BY 1;

SELECT realm_id,
       grantee_id,
       privilege_code,
       CASE privilege_code
           WHEN 1 THEN 'SERVICE_MANAGE_ACCESS  (service_admin: correct)'
           WHEN 4 THEN 'PRINCIPAL_ROLE_USAGE   (root: correct)'
           WHEN 11 THEN 'NAMESPACE_LIST        <- WRONG, expected 1'
           WHEN 12 THEN 'TABLE_LIST            <- WRONG, expected 4'
           ELSE 'unexpected -- check PolarisPrivilege.java'
       END AS privilege
  FROM grant_records
 WHERE grantee_id IN (1, 2)
 ORDER BY realm_id, grantee_id;
