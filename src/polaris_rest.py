"""
polaris_rest.py
================
Apache Polaris REST client (Management API v1 + Catalog API v1) via pure
`requests`. Wraps the handful of operations exercised repeatedly across the
test suite (catalogs, namespaces, tables/views, principals/roles, grants) in
one class — the same pattern `minio_rest.MinioREST` already uses for the S3
REST API (one class, sign/auth once, one method per operation).

This module is ADDITIVE. It does not replace or modify anything in
`polaris_test_utils.py`; none of its call sites are touched. The two modules
can be imported side by side — `PolarisREST` takes `base_url` / `realm` /
`token` as explicit constructor args rather than reading
`polaris_test_utils`' module globals, so it has no import-order dependency on
`init_env()`.

Usage:
    from polaris_rest import PolarisREST
    # token from polaris_test_utils.root_token() / get_token(), or your own OAuth call
    pc = PolarisREST(POLARIS_URL, REALM, token=root_token())

    pc.create_catalog("mycat", bucket=BUCKET, minio_endpoint=MINIO_ENDPOINT)
    pc.create_namespace("mycat", "myns")
    pc.create_principal("mycat-worker")
    pc.create_principal_role("mycat-worker-role")
    pc.create_catalog_role("mycat", "mycat-worker-cr")
    pc.assign_catalog_role_to_principal_role("mycat", "mycat-worker-role", "mycat-worker-cr")
    pc.assign_principal_role_to_principal("mycat-worker", "mycat-worker-role")
    pc.grant_privilege("mycat", "mycat-worker-cr", "TABLE_DROP")
    ...
    pc.delete_catalog("mycat", purge=True)

Notes:
    * Every method returns the raw `requests.Response` (matches
      `polaris_test_utils`' existing create_*/delete_* functions) so callers
      keep their familiar `.status_code` / `.json()` assertions — this is a
      drop-in HTTP layer, not a new response contract.
    * `token` can be fixed at construction time and/or overridden per call via
      the `token=` kwarg on any method (e.g. root token vs. a worker
      principal's token for a privilege-matrix challenge).
    * Namespaces may be multi-level (Iceberg REST unions), e.g. ["a", "b"].
      Pass either a bare string or a list/tuple — the client joins levels with
      the required `\\x1f` (unit separator) internally.
    * No credentials are hardcoded anywhere in this module. Callers supply a
      bearer token obtained via `polaris_test_utils.get_token()`/`root_token()`
      or `PolarisREST.get_token()` below.
    * `create_table`/`create_view`/`commit_table` are thin PASSTHROUGHS: you
      build the full Iceberg REST payload (schema, partition spec, sort
      order, or requirements/updates) yourself and hand it in as a dict —
      these payloads vary too much per test to generalize, so the method
      just owns the URL/headers/POST mechanics, not the body.
    * `grant_privilege` preserves two hard-won, measured fixes from
      `polaris_test_utils.grant_privilege` (skip-if-already-granted to dodge a
      ~5s duplicate-key retry storm; retry-on-404 to ride out catalog-role
      read-after-write lag under PG-HA/PgBouncer). Do not simplify these away.
"""

import time

import requests


class PolarisREST:
    """Thin client for the Apache Polaris REST API (Management v1 + Catalog v1).

    One instance = one (base_url, realm) pair. Every method issues a single
    `requests` call and returns the raw `requests.Response` — call sites keep
    doing their own `.status_code` / `.json()` checks, same as before.
    """

    def __init__(self, base_url, realm, token=None):
        """
        Args:
            base_url: Polaris server root, e.g. "http://192.168.139.2:8181"
                (no trailing path — the client appends /api/management/v1 and
                /api/catalog/v1 itself).
            realm: value sent as the `Polaris-Realm` header on every request
                (e.g. "POLARIS", or "DATACORP-PROD" for that realm).
            token: bearer token to use by default on every call. Optional at
                construction time — pass `token=` per-method instead if you're
                juggling multiple principals (e.g. root vs. a worker
                principal in a privilege test), or leave unset and populate
                `self.token` after calling `get_token()`.
        """
        self.base_url = base_url.rstrip("/")
        self.realm = realm
        self.token = token
        self.base_mgmt = f"{self.base_url}/api/management/v1"
        self.base_cat = f"{self.base_url}/api/catalog/v1"

    # ---- auth / headers ----
    def get_token(self, client_id, client_secret, scope="PRINCIPAL_ROLE:ALL"):
        """OAuth client-credentials token request. Does NOT mutate self.token —
        callers decide whether to adopt it, e.g.:
            r = pc.get_token(cid, secret)
            pc.token = r.json()["access_token"]
        """
        return requests.post(
            f"{self.base_cat}/oauth/tokens",
            headers={"Polaris-Realm": self.realm},
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": scope,
            },
        )

    def _h(self, token=None):
        """Build the standard request headers (Authorization + Polaris-Realm +
        Content-Type). Internal helper — every public method calls this.
        `token` overrides `self.token` for a single call if given."""
        tok = token if token is not None else self.token
        if not tok:
            raise ValueError(
                "PolarisREST: no token available (pass token= at construction, "
                "on the call, or set pc.token after an OAuth exchange)."
            )
        return {
            "Authorization": f"Bearer {tok}",
            "Polaris-Realm": self.realm,
            "Content-Type": "application/json",
        }

    @staticmethod
    def _ns_path(ns):
        """Multi-level namespaces are Iceberg REST unions, e.g. ["a", "b"];
        join with the required \x1f (unit separator) for a single URL path
        segment. A bare string passes through unchanged."""
        return "\x1f".join(ns) if isinstance(ns, (list, tuple)) else ns

    # ---- catalogs ----
    def create_catalog(
        self,
        name,
        bucket,
        minio_endpoint,
        minio_endpoint_internal=None,
        properties=None,
        token=None,
    ):
        """Create an INTERNAL S3-backed catalog (POST /catalogs).

        Args:
            name: catalog name.
            bucket: S3/MinIO bucket name (no s3a:// prefix). Used to build
                both `default-base-location` and `allowedLocations`.
            minio_endpoint: S3-compatible endpoint reachable by whoever calls
                the REST API from outside the cluster (e.g. your host).
            minio_endpoint_internal: endpoint Polaris itself should use
                in-cluster, if different from `minio_endpoint` (defaults to
                the same value when omitted).
            properties: extra/override catalog properties merged on top of
                the defaults (base-location + drop-with-purge enabled).
            token: bearer token override for this call.

        Returns:
            requests.Response — 201 on success.
        """
        props = {
            "default-base-location": f"s3a://{bucket}/{name}/",
            "polaris.config.drop-with-purge.enabled": "true",
        }
        if properties:
            props.update(properties)
        return requests.post(
            f"{self.base_mgmt}/catalogs",
            headers=self._h(token),
            json={
                "catalog": {
                    "name": name,
                    "type": "INTERNAL",
                    "properties": props,
                    "storageConfigInfo": {
                        "storageType": "S3",
                        "allowedLocations": [f"s3a://{bucket}/"],
                        "pathStyleAccess": True,
                        "endpoint": minio_endpoint,
                        "endpointInternal": minio_endpoint_internal or minio_endpoint,
                    },
                }
            },
        )

    def get_catalog(self, name, token=None):
        """GET a single catalog's definition. Returns 404 if it doesn't exist —
        handy as a cheap existence check (see `_teardown_catalog_selfcontained`
        in polaris_test_utils.py for the pattern)."""
        return requests.get(f"{self.base_mgmt}/catalogs/{name}", headers=self._h(token))

    def list_catalogs(self, token=None):
        """GET all catalogs visible to the caller's principal. Response JSON
        has a top-level `catalogs` list."""
        return requests.get(f"{self.base_mgmt}/catalogs", headers=self._h(token))

    def delete_catalog(self, name, purge=False, token=None):
        """Delete a catalog. `purge=True` appends `?purgeRequested=true`,
        which asks Polaris to also delete the underlying data files — note
        this requires the `CATALOG_MANAGE_CONTENT` privilege even for
        principals that can otherwise drop the catalog outright (measured
        behavior, see purge/doc-purge-troubleshooting.md)."""
        url = f"{self.base_mgmt}/catalogs/{name}"
        if purge:
            url += "?purgeRequested=true"
        return requests.delete(url, headers=self._h(token))

    # ---- namespaces ----
    def create_namespace(self, catalog, ns, properties=None, token=None):
        """Create a namespace. `ns` is a bare string ("myns") for a top-level
        namespace, or a list/tuple (["a", "b"]) for a nested one — either way
        it's normalized to the Iceberg REST `namespace` array in the request
        body. `properties` is an optional dict of namespace properties."""
        ns_body = list(ns) if isinstance(ns, (list, tuple)) else [ns]
        return requests.post(
            f"{self.base_cat}/{catalog}/namespaces",
            headers=self._h(token),
            json={"namespace": ns_body, "properties": properties or {}},
        )

    def list_namespaces(self, catalog, parent=None, token=None):
        """GET namespaces in a catalog. Pass `parent` (string or list) to
        list only the direct children of that namespace; omit it to list
        top-level namespaces. Response JSON has a top-level `namespaces` list
        (each entry itself a list of levels, e.g. `["a", "b"]`)."""
        params = {"parent": self._ns_path(parent)} if parent else {}
        return requests.get(
            f"{self.base_cat}/{catalog}/namespaces",
            headers=self._h(token),
            params=params,
        )

    def get_namespace(self, catalog, ns, token=None):
        """GET a single namespace's metadata/properties (distinct from
        `list_namespaces`, which enumerates children). Returns 404 if the
        namespace doesn't exist — useful as an existence check, e.g. after a
        create to confirm it's visible past any PG-HA read-after-write lag."""
        return requests.get(
            f"{self.base_cat}/{catalog}/namespaces/{self._ns_path(ns)}",
            headers=self._h(token),
        )

    def delete_namespace(self, catalog, ns, token=None):
        """Delete a namespace. Polaris requires it to be empty first (no
        tables/views) — delete those individually beforehand, deepest
        namespace first for nested ones."""
        return requests.delete(
            f"{self.base_cat}/{catalog}/namespaces/{self._ns_path(ns)}",
            headers=self._h(token),
        )

    # ---- tables ----
    def list_tables(self, catalog, ns, token=None):
        """GET table identifiers in a namespace. Response JSON has a
        top-level `identifiers` list (each entry `{"namespace": [...],
        "name": "..."}`)."""
        return requests.get(
            f"{self.base_cat}/{catalog}/namespaces/{self._ns_path(ns)}/tables",
            headers=self._h(token),
        )

    def create_table(self, catalog, ns, payload, token=None):
        """POST a CreateTableRequest to a namespace. `payload` is the FULL
        Iceberg REST body you build yourself, e.g.:
            {
              "name": "t1",
              "schema": {"type": "struct", "schema-id": 0, "fields": [...]},
              "partition-spec": {"spec-id": 0, "fields": []},
              "write-order": {"order-id": 0, "fields": []},
              "stage-create": False,
              "properties": {},
            }
        This method does not validate or construct the schema — it's a thin
        passthrough (URL/headers/POST only), since real payloads vary too
        much per test to generalize. 409 if a table with that name already
        exists in the namespace; 404 if the namespace doesn't exist."""
        return requests.post(
            f"{self.base_cat}/{catalog}/namespaces/{self._ns_path(ns)}/tables",
            headers=self._h(token),
            json=payload,
        )

    def commit_table(self, catalog, ns, table, updates, requirements=None, token=None):
        """POST a CommitTableRequest to an EXISTING table — the Iceberg
        "update table" call used for adding snapshots, evolving the schema,
        moving branch refs, etc. `updates` is the list of update-action
        dicts (e.g. `{"action": "add-snapshot", "snapshot": {...}}` or
        `{"action": "set-snapshot-ref", "ref-name": "main", "type": "branch",
        "snapshot-id": ...}`); `requirements` defaults to `[]` (no
        preconditions — pass e.g. `[{"type": "assert-ref-snapshot-id", ...}]`
        for optimistic-concurrency checks). See
        lifecycle/polaris_lifecycle_practice.ipynb for real add-snapshot /
        set-snapshot-ref / schema-evolution payloads this wraps."""
        ns_body = list(ns) if isinstance(ns, (list, tuple)) else [ns]
        return requests.post(
            f"{self.base_cat}/{catalog}/namespaces/{self._ns_path(ns)}/tables/{table}",
            headers=self._h(token),
            json={
                "identifier": {"namespace": ns_body, "name": table},
                "requirements": requirements or [],
                "updates": updates,
            },
        )

    def load_table(self, catalog, ns, table, token=None):
        """GET a table's Iceberg metadata (schema, current snapshot,
        metadata-location, etc.) — the standard Iceberg REST catalog
        "load table" call."""
        return requests.get(
            f"{self.base_cat}/{catalog}/namespaces/{self._ns_path(ns)}/tables/{table}",
            headers=self._h(token),
        )

    def delete_table(self, catalog, ns, table, purge=False, token=None):
        """Drop a table. `purge=True` appends `?purgeRequested=true` to also
        delete the underlying Parquet/manifest/snapshot files — this is
        gated by the `DROP_TABLE_WITH_PURGE` op, which even
        root/service_admin does NOT bypass by default; the calling
        principal/catalog-role needs `CATALOG_MANAGE_CONTENT` (measured in
        purge/table_purge_privilege_test.ipynb). A plain drop (purge=False)
        only needs `TABLE_DROP`."""
        url = f"{self.base_cat}/{catalog}/namespaces/{self._ns_path(ns)}/tables/{table}"
        if purge:
            url += "?purgeRequested=true"
        return requests.delete(url, headers=self._h(token))

    # ---- views ----
    def list_views(self, catalog, ns, token=None):
        """GET view identifiers in a namespace (same `identifiers` shape as
        `list_tables`)."""
        return requests.get(
            f"{self.base_cat}/{catalog}/namespaces/{self._ns_path(ns)}/views",
            headers=self._h(token),
        )

    def create_view(self, catalog, ns, payload, token=None):
        """POST a CreateViewRequest to a namespace. `payload` is the FULL
        Iceberg REST body you build yourself, e.g.:
            {
              "name": "v1",
              "schema": {"type": "struct", "schema-id": 0, "fields": [...]},
              "view-version": {
                  "version-id": 1, "schema-id": 0, "timestamp-ms": 0,
                  "summary": {"engine-name": "spark"},
                  "default-namespace": ["myns"],
                  "representations": [{"type": "sql", "sql": "SELECT ...",
                                        "dialect": "spark"}],
              },
              "properties": {},
            }
        Thin passthrough, same rationale as `create_table` — Polaris does
        NOT validate the SQL in `representations`; an invalid query is
        stored as-is and only fails later when something tries to resolve
        it (measured, see diagnostics/polaris_api_dependency_test.ipynb)."""
        return requests.post(
            f"{self.base_cat}/{catalog}/namespaces/{self._ns_path(ns)}/views",
            headers=self._h(token),
            json=payload,
        )

    def load_view(self, catalog, ns, view, token=None):
        """GET a view's metadata (its SQL representations + schema) —
        requires `VIEW_READ_PROPERTIES`; note `VIEW_LIST` alone is NOT
        sufficient for a single-view GET (measured, see
        privilege/doc-privilege-results.md)."""
        return requests.get(
            f"{self.base_cat}/{catalog}/namespaces/{self._ns_path(ns)}/views/{view}",
            headers=self._h(token),
        )

    def delete_view(self, catalog, ns, view, purge=False, token=None):
        """Drop a view. Unlike table purge, view drops (with or without
        `purge=True`) ARE bypassed by root/service_admin and generally just
        need `VIEW_DROP` — see purge/view_purge_behavior_test.ipynb (the
        source of truth for view purge semantics; not superseded by the
        table-purge findings above)."""
        url = f"{self.base_cat}/{catalog}/namespaces/{self._ns_path(ns)}/views/{view}"
        if purge:
            url += "?purgeRequested=true"
        return requests.delete(url, headers=self._h(token))

    # ---- principals ----
    def create_principal(
        self,
        name,
        principal_type="SERVICE",
        credential_rotation_required=False,
        token=None,
    ):
        """Create a principal (a service identity you can mint OAuth
        credentials for). `principal_type` is "SERVICE" for all current use
        cases. `credential_rotation_required=True` forces a rotation on
        first use — see admin/polaris_rotate_credential.ipynb."""
        return requests.post(
            f"{self.base_mgmt}/principals",
            headers=self._h(token),
            json={
                "principal": {"name": name, "type": principal_type},
                "credentialRotationRequired": credential_rotation_required,
            },
        )

    def get_principal(self, name, token=None):
        """GET a single principal's definition. Returns 404 if it doesn't
        exist — handy as a cheap existence check before a scoped teardown
        (see admin/polaris_reset_principal.ipynb)."""
        return requests.get(
            f"{self.base_mgmt}/principals/{name}", headers=self._h(token)
        )

    def list_principals(self, token=None):
        """GET all principals. Response JSON has a top-level `principals`
        list. Useful for a sweep/cleanup pass (see
        `sweep_instance_principals` in polaris_test_utils.py)."""
        return requests.get(f"{self.base_mgmt}/principals", headers=self._h(token))

    def delete_principal(self, name, token=None):
        """Delete a principal by name. Idempotent-ish in practice (404 if
        already gone) — safe to call in a best-effort teardown."""
        return requests.delete(
            f"{self.base_mgmt}/principals/{name}", headers=self._h(token)
        )

    def reset_principal_credentials(self, name, token=None):
        """Admin-callable credential reset for `name` — added in Polaris
        1.2+ specifically so root/service_admin can rotate ANOTHER
        principal's credentials WITHOUT deleting it (closes
        github.com/apache/polaris/issues/624). Unlike `rotate_credentials`
        (self-service only, below), this is callable with the caller's OWN
        admin token — no grant is needed, because Principal isn't a
        securable object in Polaris's RBAC model at all (grantable
        privileges only cover Catalog/Namespace/Table/View/Policy), so
        there's no privilege string to hand out here even if you wanted to.
        Gated server-side by the `ENABLE_CREDENTIAL_RESET` feature flag
        (default true — see polaris.features."ENABLE_CREDENTIAL_RESET").
        NOT idempotent: every call issues a brand-new secret.

        MEASURED (2026-07-08 live run): unlike a plain `rotate_credentials`
        call (below), a reset FULLY evicts the previous secret in one shot
        — it does not linger as a valid "secondary" secret. Internally
        Polaris stores two secret slots per principal (main + secondary,
        see `PolarisPrincipalSecrets.matchesSecret` — it accepts either
        hash) and a normal rotation only demotes the old main secret to
        secondary (still valid!); `reset` forces a SECOND internal
        rotation on top of that, which pushes the old secret out of both
        slots. So the secret in effect right before a `reset` call stops
        working immediately; that guarantee does NOT extend to secrets
        from further back, and does NOT hold for `rotate_credentials`.
        The response JSON's `credentials.clientSecret` is shown ONLY in
        this response — capture it immediately, it cannot be retrieved
        again. Role wiring (principal-role assignment, catalog-roles) is
        left untouched — this is the key difference from a delete+recreate
        reset (see admin/polaris_reset_principal.ipynb)."""
        return requests.post(
            f"{self.base_mgmt}/principals/{name}/reset",
            headers=self._h(token),
            json={},
        )

    def rotate_credentials(self, name, token=None):
        """SELF-SERVICE ONLY credential rotation — `token` must belong to
        `name` itself. root/service_admin gets a 403
        ("... is not authorized for op ROTATE_CREDENTIALS") even with full
        admin grants, BY DESIGN — a Polaris maintainer confirmed on
        github.com/apache/polaris/issues/624 that "users can rotate their
        own credentials but root cannot change them". There is no grantable
        privilege that closes this gap: Principal is not a securable object
        in Polaris's RBAC model (only Catalog/Namespace/Table/View/Policy
        are), so `PRINCIPAL_ROTATE_CREDENTIALS` cannot be granted to any
        role via the normal grants API — attempting it 404s ("Unable to
        find matching target resource method"), not 403. There's also no
        token-exchange/impersonation grant type on Polaris's OAuth endpoint
        that would let root obtain a token "as" `name` to route around this
        (and root can't read `name`'s existing secret to fake it either —
        secrets are shown once, never again). For an admin-driven
        equivalent that works today, use `reset_principal_credentials`.

        ⚠️ MEASURED (2026-07-08 live run): a single call here does NOT
        invalidate the caller's previous secret — it only demotes it to a
        "secondary" secret, which Polaris continues to accept (source:
        `PolarisPrincipalSecrets.matchesSecret` checks main OR secondary
        hash; a plain rotation only shifts main→secondary and mints a new
        main — see `JdbcBasePersistenceImpl.rotatePrincipalSecrets`). The
        secret from ONE generation back keeps working after a rotate; it
        takes a SECOND `rotate_credentials` call (or a `reset_principal_
        credentials` call, which double-rotates internally) to fully evict
        a given secret. Do not assert immediate invalidation after a
        single rotate — assert it after two. See
        admin/polaris_reset_vs_rotate_test.ipynb for a live side-by-side
        proof of this exact timing difference."""
        return requests.post(
            f"{self.base_mgmt}/principals/{name}/rotate", headers=self._h(token)
        )

    # ---- principal roles ----
    def create_principal_role(self, name, token=None):
        """Create a principal-role (the thing a principal is assigned, which
        in turn is granted one or more catalog-roles)."""
        return requests.post(
            f"{self.base_mgmt}/principal-roles",
            headers=self._h(token),
            json={"principalRole": {"name": name}},
        )

    def get_principal_role(self, name, token=None):
        """GET a single principal-role's definition. Returns 404 if it
        doesn't exist — handy as a cheap existence check before a scoped
        teardown (see admin/polaris_reset_principal.ipynb)."""
        return requests.get(
            f"{self.base_mgmt}/principal-roles/{name}", headers=self._h(token)
        )

    def list_principal_roles(self, token=None):
        """GET all principal-roles. Response JSON has a top-level `roles`
        list (note: NOT `principalRoles` — Polaris uses `roles` for both
        this and catalog-roles' list response)."""
        return requests.get(f"{self.base_mgmt}/principal-roles", headers=self._h(token))

    def delete_principal_role(self, name, token=None):
        """Delete a principal-role by name."""
        return requests.delete(
            f"{self.base_mgmt}/principal-roles/{name}", headers=self._h(token)
        )

    def list_principals_for_principal_role(self, principal_role, token=None):
        """Reverse lookup: GET all principals currently assigned a given
        principal-role. Response JSON has a top-level `principals` list.
        Handy for "who can do X" audits (e.g. admin/polaris_rotate_credential
        .ipynb uses this to find who holds `ops-admin` before rotating)."""
        return requests.get(
            f"{self.base_mgmt}/principal-roles/{principal_role}/principals",
            headers=self._h(token),
        )

    # ---- catalog roles ----
    def create_catalog_role(self, catalog, name, token=None):
        """Create a catalog-role scoped to `catalog`. Catalog-roles are what
        grants actually attach to; a principal-role gets access by being
        assigned a catalog-role (see `assign_catalog_role_to_principal_role`)."""
        return requests.post(
            f"{self.base_mgmt}/catalogs/{catalog}/catalog-roles",
            headers=self._h(token),
            json={"catalogRole": {"name": name}},
        )

    def list_catalog_roles(self, catalog, token=None):
        """GET catalog-roles defined on `catalog`. Response JSON has a
        top-level `roles` list; the built-in `catalog_admin` role is always
        present and should not be deleted during cleanup."""
        return requests.get(
            f"{self.base_mgmt}/catalogs/{catalog}/catalog-roles", headers=self._h(token)
        )

    def delete_catalog_role(self, catalog, name, token=None):
        """Delete a catalog-role by name. Do not call this on the built-in
        `catalog_admin` role."""
        return requests.delete(
            f"{self.base_mgmt}/catalogs/{catalog}/catalog-roles/{name}",
            headers=self._h(token),
        )

    # ---- role wiring ----
    def assign_catalog_role_to_principal_role(
        self, catalog, principal_role, catalog_role, token=None
    ):
        """Wire a catalog-role onto a principal-role, so any principal
        holding `principal_role` inherits whatever `catalog_role` has been
        granted. NOTE: if `catalog_role` was just created moments ago, this
        PUT can 404 due to PG-HA read-after-write lag — the same class of
        issue `grant_privilege` retries around; if you see intermittent
        404s here immediately after `create_catalog_role`, add a short
        retry/backoff at the call site."""
        return requests.put(
            f"{self.base_mgmt}/principal-roles/{principal_role}/catalog-roles/{catalog}",
            headers=self._h(token),
            json={"catalogRole": {"name": catalog_role}},
        )

    def assign_principal_role_to_principal(self, principal, principal_role, token=None):
        """Wire a principal-role onto a principal, so that principal can
        request an OAuth token scoped to `PRINCIPAL_ROLE:{principal_role}`
        and inherit its catalog-role grants."""
        return requests.put(
            f"{self.base_mgmt}/principals/{principal}/principal-roles",
            headers=self._h(token),
            json={"principalRole": {"name": principal_role}},
        )

    # ---- grants ----
    def list_grants(self, catalog, catalog_role, token=None):
        """GET the privileges currently granted to a catalog-role. Response
        JSON has a top-level `grants` list (each entry has `privilege` and
        `type`, e.g. `{"type": "catalog", "privilege": "TABLE_DROP"}`). Used
        by `grant_privilege` below to skip redundant grants."""
        return requests.get(
            f"{self.base_mgmt}/catalogs/{catalog}/catalog-roles/{catalog_role}/grants",
            headers=self._h(token),
        )

    def grant_privilege(
        self,
        catalog,
        catalog_role,
        privilege,
        token=None,
        skip_if_present=True,
        max_retries=7,
    ):
        """Grant a catalog privilege to a catalog-role, idempotently and cheaply.

        Preserves two hard-won, MEASURED fixes from
        `polaris_test_utils.grant_privilege` verbatim — do not simplify away:
          1. Polaris implements the grant PUT as an INSERT with no no-op path;
             a duplicate grant retries against the metastore for ~5s before a
             23505 duplicate-key error. `skip_if_present` avoids that entirely
             by checking existing grants first (a cheap GET) and skipping the
             PUT if the privilege is already held.
          2. A catalog-role created moments earlier can 404 on the grant PUT
             due to read-after-write lag on a PG-HA read replica. On a 404
             "...not found" we back off (capped) and retry up to `max_retries`
             times (~9s cumulative) rather than misreporting a valid grant as
             GRANT_INVALID.
        """
        grants_url = (
            f"{self.base_mgmt}/catalogs/{catalog}/catalog-roles/{catalog_role}/grants"
        )
        hdr = self._h(token)
        if skip_if_present:
            try:
                existing = requests.get(grants_url, headers=hdr)
                if existing.status_code == 200:
                    for g in existing.json().get("grants", []):
                        if (
                            g.get("privilege") == privilege
                            and g.get("type", "catalog") == "catalog"
                        ):
                            return existing  # already granted -> no write, no 5s wait
            except Exception:
                pass  # if the check fails, fall through to the PUT (still safe)

        r = None
        for attempt in range(max_retries):
            r = requests.put(
                grants_url,
                headers=hdr,
                json={"grant": {"type": "catalog", "privilege": privilege}},
            )
            if r.status_code < 400:
                return r
            body = r.text.lower()
            if (
                "already exists" in body
                or "23505" in body
                or "duplicate key" in body
                or "grant_records_pkey" in body
            ):
                return r  # grant already present -> treat as success (idempotent)
            if (
                r.status_code == 404
                and "not found" in body
                and attempt < max_retries - 1
            ):
                time.sleep(min(0.5 * (attempt + 1), 2.0))
                continue
            return r  # genuine error (e.g. 400 invalid privilege name) -> surface, stop
        return r
