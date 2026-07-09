SET search_path TO polaris_schema;

-- set TIMESTAMP extract(epoch from now())::bigint * 1000

-- -- Bootstrap Data 추가
-- -- Root Container (type_code=1, id=0)
INSERT INTO entities (realm_id, catalog_id, id, parent_id,
name, entity_version, type_code, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp,
last_update_timestamp, properties, internal_properties, grant_records_version)
VALUES ('POLARIS', 0, 0, 0, 'root_container', 1, 1, 0, now(), 0, 0, 0, ${TIMESTAMP}, '{}'::JSONB, '{}'::JSONB,1);

-- -- Root Principal (type_code=2, id=1)
INSERT INTO entities (realm_id, catalog_id, id, parent_id,
name, entity_version, type_code, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp,
last_update_timestamp, properties, internal_properties, grant_records_version)
VALUES ('POLARIS', 0, 1, 0, 'root', 1, 2, 0, ${TIMESTAMP},
0, 0, 0, ${TIMESTAMP}, '{}'::JSONB, '{\"client_id\":\"root\"}'::JSONB, 1);

-- -- Service Admin Principal Role (type_code=3, id=2)
INSERT INTO entities (realm_id, catalog_id, id, parent_id,
name, entity_version, type_code, sub_type_code, create_timestamp, drop_timestamp, purge_timestamp, to_purge_timestamp,
last_update_timestamp, properties, internal_properties, grant_records_version)
VALUES ('POLARIS', 0, 2, 0, 'service_admin', 1, 3, 0, ${TIMESTAMP}, 0, 0, 0, ${TIMESTAMP}, '{}'::JSONB, '{}'::JSONB, 1);

-- Grant: root(1) gets PRINCIPAL_ROLE_USAGE(12) on service_admin(2)
INSERT INTO grant_records (realm_id, securable_catalog_id,
securable_id, grantee_catalog_id, grantee_id, privilege_code)
VALUES ('POLARIS', 0, 2, 0, 1, 12);

-- Grant: service_admin(2) gets SERVICE_MANAGE_ACCESS(11) on root_container(0)
INSERT INTO grant_records (realm_id, securable_catalog_id,
securable_id, grantee_catalog_id, grantee_id, privilege_code)
VALUES ('POLARIS', 0, 0, 0, 2, 11);

-- Authentication Data for root (hash algorithm: SHA256(secret + ':' + salt))
INSERT INTO principal_authentication_data (realm_id, principal_id, principal_client_id, main_secret_hash, secondary_secret_hash, secret_salt)
VALUES ('POLARIS', 1, 'root', '${MAIN_HASH}', '${MAIN_HASH}', '${SALT}');

-- Grant: root(1) gets PRINCIPAL_ROLE_USAGE(12) on service_admin(2)
INSERT INTO grant_records (realm_id, securable_catalog_id,
securable_id, grantee_catalog_id, grantee_id, privilege_code)
VALUES ('DATACORP-PROD', 0, 2, 0, 1, 12);

-- Grant: service_admin(2) gets SERVICE_MANAGE_ACCESS(11) on root_container(0)
INSERT INTO grant_records (realm_id, securable_catalog_id,
securable_id, grantee_catalog_id, grantee_id, privilege_code)
VALUES ('DATACORP-PROD', 0, 0, 0, 2, 11);

-- Authentication Data for root (hash algorithm: SHA256(secret + ':' + salt))
INSERT INTO principal_authentication_data (realm_id, principal_id, principal_client_id, main_secret_hash, secondary_secret_hash, secret_salt)
VALUES ('DATACORP-PROD', 1, 'root', '${MAIN_HASH}', '${MAIN_HASH}', '${SALT}');