-- Repair the two bootstrap grants in place. No re-drop, no re-bootstrap.
--
--   psql -U polaris -d polaris -v ON_ERROR_STOP=1 -f repair_bootstrap_grants.sql
--   kubectl rollout restart deploy/benchmarks-polaris -n datahub-hynix
--
-- WHY: the hand-rolled bootstrap wrote privilege codes 11 and 12. Verified
-- against PolarisPrivilege.java at tag apache-polaris-1.3.0-incubating, the
-- correct codes are 1 and 4. What 11 and 12 actually mean there:
--
--     1  SERVICE_MANAGE_ACCESS   <- what service_admin needs   (ROOT scope)
--     4  PRINCIPAL_ROLE_USAGE    <- what links root -> service_admin
--    11  NAMESPACE_LIST          <- what was written instead of 1
--    12  TABLE_LIST              <- what was written instead of 4
--
-- So service_admin held "may list namespaces" on the root container. That is
-- why root authenticated fine, service_admin activated, its grants loaded --
-- and CREATE_PRINCIPAL was still refused. The 403 even says so: "activated
-- grants via '[service_admin]' is not authorized". The role was never the
-- problem; the privilege it carried was.
--
-- SERVICE_MANAGE_ACCESS is a SUPER-privilege: PolarisAuthorizerImpl's
-- SUPER_PRIVILEGES map lists it as sufficient for PRINCIPAL_CREATE,
-- CATALOG_CREATE and the rest, which is why one grant is all service_admin
-- needs. That part of the bootstrap's design was right.

SET search_path TO polaris_schema;

BEGIN;

-- Refuse to run if the rows are not in the shape this script expects, rather
-- than silently updating nothing and reporting success.
DO $$
DECLARE n int;
BEGIN
    SELECT count(*) INTO n FROM grant_records
     WHERE (securable_id = 0 AND grantee_id = 2 AND privilege_code = 11)
        OR (securable_id = 2 AND grantee_id = 1 AND privilege_code = 12);
    IF n = 0 THEN
        RAISE EXCEPTION 'no rows with the broken codes (11/12) found. Either '
            'this is already repaired, or the bootstrap wrote something else '
            'again -- run triage_realm.py before guessing.';
    END IF;
    RAISE NOTICE 'repairing % grant row(s)', n;
END $$;

-- service_admin(2) -> SERVICE_MANAGE_ACCESS on root_container(0)
UPDATE grant_records SET privilege_code = 1
 WHERE securable_catalog_id = 0 AND securable_id = 0
   AND grantee_catalog_id = 0 AND grantee_id = 2
   AND privilege_code = 11;

-- root(1) -> PRINCIPAL_ROLE_USAGE on service_admin(2)
UPDATE grant_records SET privilege_code = 4
 WHERE securable_catalog_id = 0 AND securable_id = 2
   AND grantee_catalog_id = 0 AND grantee_id = 1
   AND privilege_code = 12;

COMMIT;

SELECT realm_id, securable_id, grantee_id, privilege_code,
       CASE privilege_code
           WHEN 1 THEN 'SERVICE_MANAGE_ACCESS'
           WHEN 4 THEN 'PRINCIPAL_ROLE_USAGE'
           ELSE 'UNEXPECTED -- see PolarisPrivilege.java'
       END AS privilege
  FROM grant_records
 WHERE grantee_id IN (1, 2)
 ORDER BY realm_id, grantee_id;

-- RESTART POLARIS after this. InMemoryEntityCache holds an entity together
-- with its grant_records for up to an hour, so a running instance will keep
-- enforcing the codes it already read.
