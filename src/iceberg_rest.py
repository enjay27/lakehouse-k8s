"""
iceberg_rest.py
===============
Apache Iceberg REST Catalog client (spec v1) against Apache Polaris, via pure
`requests`. Companion to `polaris_rest.PolarisREST` and `minio_rest.MinioREST`
— same shape (one class, one method per operation, raw `requests.Response`
returned), so the three can be used side by side without a new response
contract to learn.

WHY A SEPARATE MODULE (and not more methods on PolarisREST)
-----------------------------------------------------------
`polaris_rest.PolarisREST` covers the operations this test suite already
exercised: it reaches into the Iceberg Catalog API only where the Polaris
suites happened to need it (create/load/commit/delete table and view). That
made sense as an incremental addition; it does not make sense as the home for
a *complete* Iceberg REST client.

This module is the complete client, organised by the Iceberg REST spec rather
than by what Polaris tests happen to call:

    * config
    * namespaces  (incl. HEAD-exists and the properties-update endpoint)
    * tables      (incl. HEAD-exists, stage-create, register, rename, metrics)
    * views       (incl. HEAD-exists, rename)
    * transactions (multi-table commit)
    * credential delegation (the `X-Iceberg-Access-Delegation` header)

It is ADDITIVE and standalone: it imports nothing from `polaris_rest.py` or
`polaris_test_utils.py`, modifies neither, and duplicates only the two tiny
helpers it needs (`_h`, `_ns_path`) rather than creating a cross-module
dependency between two clients that should stay independently usable.

ICEBERG REST vs. POLARIS MANAGEMENT — WHICH CLIENT DO I WANT?
-------------------------------------------------------------
    Polaris Management API   /api/management/v1/...   -> polaris_rest.py
        catalogs, principals, principal-roles, catalog-roles, grants
    Iceberg REST Catalog API /api/catalog/v1/...      -> THIS MODULE
        config, namespaces, tables, views, transactions

Namespaces and tables/views exist in both because Polaris serves the Iceberg
Catalog API for them. Where the two overlap, prefer this module for anything
that speaks Iceberg semantics (metadata, snapshots, commits) and
`polaris_rest.py` for Polaris-specific administration.

THE `prefix` PATH PARAMETER
---------------------------
The Iceberg REST spec puts a `{prefix}` segment before every resource so one
server can host many catalogs. **In Polaris the prefix is the catalog name.**
Every method here takes `catalog` and places it in that slot, so callers never
have to think about it.

MULTI-LEVEL NAMESPACES
----------------------
Iceberg namespaces are multi-level (e.g. `["a", "b"]`). In a URL path segment
the levels are joined with `\\x1f` (ASCII unit separator). Pass a bare string
for a single level or a list/tuple for several — `_ns_path` handles it.

Usage:
    from iceberg_rest import IcebergREST
    ic = IcebergREST(POLARIS_URL, REALM, token=root_token())

    ic.get_config(warehouse="mycat")
    ic.create_namespace("mycat", "myns")
    ic.namespace_exists("mycat", "myns")            # HEAD -> 204 / 404
    ic.list_tables("mycat", "myns")
    ic.load_table("mycat", "myns", "mytbl")
    ic.table_exists("mycat", "myns", "mytbl")       # HEAD -> 204 / 404
    ic.drop_table("mycat", "myns", "mytbl", purge=True)

Notes:
    * Every method returns the raw `requests.Response`. Callers keep their
      familiar `.status_code` / `.json()` assertions.
    * `token` may be fixed at construction and/or overridden per call via the
      `token=` kwarg — same convention as `PolarisREST`.
    * No credentials are hardcoded here. Callers supply a bearer token from
      `polaris_test_utils.get_token()` / `root_token()` or
      `PolarisREST.get_token()`.
    * Payload-heavy operations (`create_table`, `commit_table`, `create_view`,
      `commit_transaction`) are PASSTHROUGHS: you build the Iceberg REST body
      (schema / partition spec / requirements / updates) and hand it in as a
      dict. Those bodies vary far too much per test to generalise; the method
      owns URL, headers and verb, not the body. `build_*` helpers at the
      bottom of this module cover the common shapes if you want them.
    * HEAD endpoints return NO body. Check `.status_code` (204 exists,
      404 absent) — `.json()` will raise. `*_exists()` wrappers returning a
      bool are provided alongside the raw HEAD methods.
    * `X-Iceberg-Access-Delegation` (credential vending) is opt-in per call via
      `delegation=`. Polaris only honours it where storage credentials are
      configured; with static MinIO keys and no STS it is expected to be a
      no-op, which is itself worth asserting in a test.
"""

import requests

# Iceberg REST spec values for the X-Iceberg-Access-Delegation header.
DELEGATION_VENDED_CREDENTIALS = "vended-credentials"
DELEGATION_REMOTE_SIGNING = "remote-signing"


class IcebergREST:
    """Thin client for the Iceberg REST Catalog API (spec v1) as served by Polaris.

    One instance = one (base_url, realm) pair. Every method issues a single
    `requests` call and returns the raw `requests.Response`.
    """

    def __init__(self, base_url, realm, token=None):
        """
        Args:
            base_url: Polaris server root, e.g. "http://192.168.139.2:8181"
                (no trailing path — the client appends /api/catalog/v1 itself).
            realm: value sent as the `Polaris-Realm` header on every request.
            token: bearer token used by default on every call. Optional here —
                pass `token=` per method instead when juggling principals, or
                set `self.token` after an OAuth exchange.
        """
        self.base_url = base_url.rstrip("/")
        self.realm = realm
        self.token = token
        self.base_cat = f"{self.base_url}/api/catalog/v1"

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------
    def _h(self, token=None, delegation=None):
        """Build standard request headers (Authorization + Polaris-Realm +
        Content-Type), optionally adding `X-Iceberg-Access-Delegation`.

        Args:
            token: overrides `self.token` for a single call.
            delegation: value for the `X-Iceberg-Access-Delegation` header —
                use the DELEGATION_* constants. Omitted entirely when None,
                which is the default and the correct behaviour for a server
                without STS.

        Raises:
            ValueError: if no token is available from either source. Fails
                loudly rather than sending an unauthenticated request that
                would come back as a confusing 401.
        """
        tok = token if token is not None else self.token
        if not tok:
            raise ValueError(
                "IcebergREST: no token available (pass token= at construction, "
                "on the call, or set ic.token after an OAuth exchange)."
            )
        h = {
            "Authorization": f"Bearer {tok}",
            "Polaris-Realm": self.realm,
            "Content-Type": "application/json",
        }
        if delegation:
            h["X-Iceberg-Access-Delegation"] = delegation
        return h

    @staticmethod
    def _ns_path(ns):
        """Join a multi-level namespace into one URL path segment.

        Iceberg namespaces are unions, e.g. ["a", "b"]; the REST spec joins the
        levels with \\x1f (ASCII unit separator). A bare string passes through
        unchanged.
        """
        return "\x1f".join(ns) if isinstance(ns, (list, tuple)) else ns

    def _cat(self, catalog):
        """Base URL for one catalog — the spec's `{prefix}` slot, which Polaris
        fills with the catalog name."""
        return f"{self.base_cat}/{catalog}"

    # ------------------------------------------------------------------
    # config
    # ------------------------------------------------------------------
    def get_config(self, warehouse=None, token=None):
        """GET /v1/config — catalog configuration for a client.

        The first call any Iceberg client makes. Returns `defaults` and
        `overrides` property maps plus, in newer specs, the list of endpoints
        the server supports. Cheap, and hit on every engine session start —
        which makes it a useful lower bound when profiling: whatever this
        costs is the floor for any other API.

        Args:
            warehouse: optional `?warehouse=` query param. In Polaris this is
                the catalog name; the server uses it to resolve which catalog's
                defaults to return.
            token: per-call token override.

        Returns:
            requests.Response — 200 with {"defaults": {...}, "overrides": {...}}.
        """
        params = {"warehouse": warehouse} if warehouse else None
        return requests.get(
            f"{self.base_cat}/config", headers=self._h(token), params=params
        )

    # ------------------------------------------------------------------
    # namespaces
    # ------------------------------------------------------------------
    def create_namespace(self, catalog, ns, properties=None, token=None):
        """POST /v1/{catalog}/namespaces — create a namespace.

        Args:
            catalog: catalog name (the spec's `prefix`).
            ns: namespace, bare string or list of levels.
            properties: optional property map stored on the namespace. Lands in
                the `properties` JSONB column of the `entities` row.
            token: per-call token override.

        Returns:
            requests.Response — 200 on success, 409 if it already exists.
        """
        levels = list(ns) if isinstance(ns, (list, tuple)) else [ns]
        payload = {"namespace": levels, "properties": properties or {}}
        return requests.post(
            f"{self._cat(catalog)}/namespaces", headers=self._h(token), json=payload
        )

    def list_namespaces(
        self, catalog, parent=None, page_token=None, page_size=None, token=None
    ):
        """GET /v1/{catalog}/namespaces — list child namespaces.

        Args:
            catalog: catalog name.
            parent: optional parent namespace to list children of. Omit for
                top-level namespaces. Bare string or list of levels.
            page_token: opaque continuation token from a previous response's
                `next-page-token`.
            page_size: max results per page. Worth exercising when profiling —
                paging changes the SQL's LIMIT and therefore the row count.
            token: per-call token override.

        Returns:
            requests.Response — 200 with {"namespaces": [[level, ...], ...]}.
        """
        params = {}
        if parent is not None:
            params["parent"] = self._ns_path(parent)
        if page_token is not None:
            params["pageToken"] = page_token
        if page_size is not None:
            params["pageSize"] = page_size
        return requests.get(
            f"{self._cat(catalog)}/namespaces",
            headers=self._h(token),
            params=params or None,
        )

    def load_namespace(self, catalog, ns, token=None):
        """GET /v1/{catalog}/namespaces/{ns} — load one namespace's metadata.

        Distinct from `list_namespaces`, which lists *children*. Returns the
        namespace's own properties.

        Returns:
            requests.Response — 200 with {"namespace": [...], "properties": {...}},
            404 if absent.
        """
        return requests.get(
            f"{self._cat(catalog)}/namespaces/{self._ns_path(ns)}",
            headers=self._h(token),
        )

    def head_namespace(self, catalog, ns, token=None):
        """HEAD /v1/{catalog}/namespaces/{ns} — existence check, NO BODY.

        Returns:
            requests.Response — 204 exists, 404 absent. Do NOT call `.json()`.

        Note:
            Worth profiling separately from `load_namespace`: if HEAD costs the
            same SQL as a full GET then it is not the cheap probe clients
            assume it is, which is a finding.
        """
        return requests.head(
            f"{self._cat(catalog)}/namespaces/{self._ns_path(ns)}",
            headers=self._h(token),
        )

    def namespace_exists(self, catalog, ns, token=None):
        """Convenience bool wrapper over `head_namespace`. True on 2xx."""
        return self.head_namespace(catalog, ns, token=token).ok

    def update_namespace_properties(
        self, catalog, ns, updates=None, removals=None, token=None
    ):
        """POST /v1/{catalog}/namespaces/{ns}/properties — set/remove properties.

        Args:
            catalog: catalog name.
            ns: namespace, bare string or list of levels.
            updates: dict of properties to set/overwrite.
            removals: list of property keys to delete.
            token: per-call token override.

        Returns:
            requests.Response — 200 with {"updated": [...], "removed": [...],
            "missing": [...]}.

        Note:
            This is a WRITE to the `entities` row's JSONB `properties` column
            and bumps `entity_version` — i.e. it self-invalidates the entity
            cache for that namespace. Useful precisely because of that: it is
            the cheapest way to force a cache invalidation in a test.
        """
        payload = {"updates": updates or {}, "removals": removals or []}
        return requests.post(
            f"{self._cat(catalog)}/namespaces/{self._ns_path(ns)}/properties",
            headers=self._h(token),
            json=payload,
        )

    def drop_namespace(self, catalog, ns, token=None):
        """DELETE /v1/{catalog}/namespaces/{ns} — drop an (empty) namespace.

        Returns:
            requests.Response — 204 on success, 404 if absent, 409 if it still
            has children.
        """
        return requests.delete(
            f"{self._cat(catalog)}/namespaces/{self._ns_path(ns)}",
            headers=self._h(token),
        )

    # ------------------------------------------------------------------
    # tables
    # ------------------------------------------------------------------
    def list_tables(self, catalog, ns, page_token=None, page_size=None, token=None):
        """GET /v1/{catalog}/namespaces/{ns}/tables — list table identifiers.

        Metadata-only: returns identifiers, does not read any metadata.json.
        The natural control when measuring whether `load_table` touches object
        storage — same entity resolution, no file I/O.

        Returns:
            requests.Response — 200 with {"identifiers": [{"namespace": [...],
            "name": "..."}, ...]}.
        """
        params = {}
        if page_token is not None:
            params["pageToken"] = page_token
        if page_size is not None:
            params["pageSize"] = page_size
        return requests.get(
            f"{self._cat(catalog)}/namespaces/{self._ns_path(ns)}/tables",
            headers=self._h(token),
            params=params or None,
        )

    def create_table(self, catalog, ns, payload, delegation=None, token=None):
        """POST /v1/{catalog}/namespaces/{ns}/tables — create a table.

        PASSTHROUGH: build the CreateTableRequest yourself. See
        `build_create_table_payload` below for the common shape.

        Args:
            payload: dict — at minimum {"name": ..., "schema": {...}}. Include
                `"stage-create": True` for a staged create (see
                `stage_create_table`).
            delegation: optional `X-Iceberg-Access-Delegation` value.

        Returns:
            requests.Response — 200 with a LoadTableResult, 409 if it exists.

        Note:
            A non-staged create WRITES the first metadata.json to object
            storage server-side, so this is one of the few Polaris APIs that
            does its own S3/MinIO I/O. Expect a PUT in the MinIO trace.
        """
        return requests.post(
            f"{self._cat(catalog)}/namespaces/{self._ns_path(ns)}/tables",
            headers=self._h(token, delegation),
            json=payload,
        )

    def stage_create_table(self, catalog, ns, payload, token=None):
        """POST .../tables with `stage-create: true` — reserve without committing.

        Convenience over `create_table`: copies the payload and forces the
        `stage-create` flag rather than relying on the caller to remember it.

        A staged create returns metadata WITHOUT persisting the table, so no
        metadata.json is written and no `entities` row is created — which makes
        it the cleanest way to isolate "what does create cost *before* any
        storage I/O". Well worth a row of its own in the access matrix.

        Returns:
            requests.Response — 200 with a LoadTableResult whose
            `metadata-location` is absent.
        """
        staged = dict(payload)
        staged["stage-create"] = True
        return requests.post(
            f"{self._cat(catalog)}/namespaces/{self._ns_path(ns)}/tables",
            headers=self._h(token),
            json=staged,
        )

    def register_table(self, catalog, ns, name, metadata_location, token=None):
        """POST /v1/{catalog}/namespaces/{ns}/register — adopt an existing table.

        Registers a table whose metadata.json already exists in storage, e.g.
        one written by another engine or recovered after a drop. Creates the
        catalog entry without writing new metadata.

        Args:
            name: table name to register under.
            metadata_location: full URI of the existing metadata.json.

        Returns:
            requests.Response — 200 with a LoadTableResult, 409 if the name is
            taken.

        Note:
            Interesting to profile: an `entities` INSERT with (probably) a
            metadata READ but no WRITE — the inverse of `create_table`.
        """
        payload = {"name": name, "metadata-location": metadata_location}
        return requests.post(
            f"{self._cat(catalog)}/namespaces/{self._ns_path(ns)}/register",
            headers=self._h(token),
            json=payload,
        )

    def load_table(
        self, catalog, ns, table, snapshots=None, delegation=None, token=None
    ):
        """GET /v1/{catalog}/namespaces/{ns}/tables/{table} — load table metadata.

        The hottest path in the whole API surface: every engine planning a
        query calls it. Returns the FULL TableMetadata as JSON, which for a
        wide schema with long snapshot history can be megabytes — so this is
        also the API most likely to be dominated by serialization and transfer
        rather than by SQL.

        Args:
            snapshots: optional `?snapshots=` — "all" or "refs". "refs" returns
                only referenced snapshots and can shrink the response
                dramatically. Worth measuring both: the delta is the cost of
                snapshot history.
            delegation: optional `X-Iceberg-Access-Delegation` value.

        Returns:
            requests.Response — 200 with a LoadTableResult, 404 if absent.

        Note:
            Expected to read metadata.json from object storage server-side,
            since Polaris must return the parsed metadata rather than just a
            pointer. Confirm in the MinIO trace — if true, every table load is
            a PG read PLUS an object read, and MinIO latency (not Postgres)
            sets the floor for query planning.
        """
        params = {"snapshots": snapshots} if snapshots else None
        return requests.get(
            f"{self._cat(catalog)}/namespaces/{self._ns_path(ns)}/tables/{table}",
            headers=self._h(token, delegation),
            params=params,
        )

    def head_table(self, catalog, ns, table, token=None):
        """HEAD /v1/{catalog}/namespaces/{ns}/tables/{table} — exists, NO BODY.

        Returns:
            requests.Response — 204 exists, 404 absent. Do NOT call `.json()`.

        Note:
            The interesting comparison in the whole sweep. If HEAD skips the
            metadata.json read that `load_table` performs, it is genuinely
            cheap and engines should prefer it. If it does not, that is a
            performance bug worth reporting upstream.
        """
        return requests.head(
            f"{self._cat(catalog)}/namespaces/{self._ns_path(ns)}/tables/{table}",
            headers=self._h(token),
        )

    def table_exists(self, catalog, ns, table, token=None):
        """Convenience bool wrapper over `head_table`. True on 2xx."""
        return self.head_table(catalog, ns, table, token=token).ok

    def commit_table(self, catalog, ns, table, updates, requirements=None, token=None):
        """POST /v1/{catalog}/namespaces/{ns}/tables/{table} — commit changes.

        The Iceberg CommitTableRequest: `requirements` are the optimistic-
        concurrency preconditions, `updates` the metadata mutations
        (add-snapshot, set-current-schema, set-ref, ...).

        Args:
            updates: list of update dicts, each with an "action" key.
            requirements: list of requirement dicts. Defaults to [] — an
                unconditional commit. Real engines always send requirements;
                pass them explicitly when testing conflict behaviour.

        Returns:
            requests.Response — 200 with the new metadata, 409 on a failed
            requirement (a commit conflict).

        Note:
            Self-invalidating: every commit bumps `entity_version`, so a table
            can never be commit-cached. Also writes a NEW metadata.json each
            time, so metadata grows with commit count — which is why commit
            latency should be swept against snapshot count rather than
            measured once.
        """
        payload = {"requirements": requirements or [], "updates": updates}
        return requests.post(
            f"{self._cat(catalog)}/namespaces/{self._ns_path(ns)}/tables/{table}",
            headers=self._h(token),
            json=payload,
        )

    def rename_table(
        self, catalog, source_ns, source_name, dest_ns, dest_name, token=None
    ):
        """POST /v1/{catalog}/tables/rename — rename or move a table.

        Note the URL: rename is catalog-scoped, NOT namespace-scoped, because
        source and destination namespaces may differ.

        Returns:
            requests.Response — 204 on success, 404 if source absent, 409 if
            destination taken.

        Note:
            A pure metadata operation — an `entities` UPDATE of `name` and
            possibly `parent_id`, with no object-storage I/O (the data does not
            move). Good contrast case against `commit_table`.
        """
        payload = {
            "source": {
                "namespace": (
                    list(source_ns)
                    if isinstance(source_ns, (list, tuple))
                    else [source_ns]
                ),
                "name": source_name,
            },
            "destination": {
                "namespace": (
                    list(dest_ns) if isinstance(dest_ns, (list, tuple)) else [dest_ns]
                ),
                "name": dest_name,
            },
        }
        return requests.post(
            f"{self._cat(catalog)}/tables/rename", headers=self._h(token), json=payload
        )

    def drop_table(self, catalog, ns, table, purge=False, token=None):
        """DELETE /v1/{catalog}/namespaces/{ns}/tables/{table} — drop a table.

        Args:
            purge: sets `?purgeRequested=true`, asking Polaris to delete the
                underlying data files as well as the catalog entry.

        Returns:
            requests.Response — 204 on success, 404 if absent, 403 if the
            purge variant is not authorized.

        Note (two measured behaviours worth remembering):
            * Purge is gated by a DISTINCT operation, `DROP_TABLE_WITH_PURGE`,
              which root/service_admin does NOT bypass — `TABLE_DROP` alone is
              insufficient, `CATALOG_MANAGE_CONTENT` is required. Measured
              live 2026-07-06.
            * File deletion runs on an ASYNC background task after the response
              returns, so client-observed latency says nothing about its real
              cost. Poll object storage to measure it — and note that on this
              build purge orphans files (issue #379), so the prefix may never
              empty.
        """
        params = {"purgeRequested": "true"} if purge else None
        return requests.delete(
            f"{self._cat(catalog)}/namespaces/{self._ns_path(ns)}/tables/{table}",
            headers=self._h(token),
            params=params,
        )

    def report_metrics(self, catalog, ns, table, report, token=None):
        """POST /v1/{catalog}/namespaces/{ns}/tables/{table}/metrics — metrics report.

        Iceberg clients POST scan/commit reports here routinely after queries.
        Easy to forget when inventorying the API surface, and it runs on the
        hot path of every engine query, so it belongs in the sweep.

        Args:
            report: a ReportMetricsRequest dict (`report-type` of "scan-report"
                or "commit-report" plus its fields).

        Returns:
            requests.Response — 204 on success.

        Note:
            Polaris may accept and discard these. If so it should be nearly
            free and touch no tables — worth confirming, because a metrics
            endpoint that resolves the full entity path would add hidden cost
            to every engine query.
        """
        return requests.post(
            f"{self._cat(catalog)}/namespaces/{self._ns_path(ns)}/tables/{table}/metrics",
            headers=self._h(token),
            json=report,
        )

    # ------------------------------------------------------------------
    # views
    # ------------------------------------------------------------------
    def list_views(self, catalog, ns, page_token=None, page_size=None, token=None):
        """GET /v1/{catalog}/namespaces/{ns}/views — list view identifiers.

        Returns:
            requests.Response — 200 with {"identifiers": [...]}.
        """
        params = {}
        if page_token is not None:
            params["pageToken"] = page_token
        if page_size is not None:
            params["pageSize"] = page_size
        return requests.get(
            f"{self._cat(catalog)}/namespaces/{self._ns_path(ns)}/views",
            headers=self._h(token),
            params=params or None,
        )

    def create_view(self, catalog, ns, payload, token=None):
        """POST /v1/{catalog}/namespaces/{ns}/views — create a view.

        PASSTHROUGH: build the CreateViewRequest yourself (name, schema,
        view-version, properties).

        Returns:
            requests.Response — 200 with a LoadViewResult, 409 if it exists.
        """
        return requests.post(
            f"{self._cat(catalog)}/namespaces/{self._ns_path(ns)}/views",
            headers=self._h(token),
            json=payload,
        )

    def load_view(self, catalog, ns, view, token=None):
        """GET /v1/{catalog}/namespaces/{ns}/views/{view} — load view metadata.

        Returns:
            requests.Response — 200 with a LoadViewResult, 404 if absent.

        Note:
            Measured 2026-07-02: a single-view GET requires
            `VIEW_READ_PROPERTIES`, NOT `VIEW_LIST` — `VIEW_LIST` returns 403
            here. Relevant when running this as a non-root principal.
        """
        return requests.get(
            f"{self._cat(catalog)}/namespaces/{self._ns_path(ns)}/views/{view}",
            headers=self._h(token),
        )

    def head_view(self, catalog, ns, view, token=None):
        """HEAD /v1/{catalog}/namespaces/{ns}/views/{view} — exists, NO BODY.

        Returns:
            requests.Response — 204 exists, 404 absent. Do NOT call `.json()`.
        """
        return requests.head(
            f"{self._cat(catalog)}/namespaces/{self._ns_path(ns)}/views/{view}",
            headers=self._h(token),
        )

    def view_exists(self, catalog, ns, view, token=None):
        """Convenience bool wrapper over `head_view`. True on 2xx."""
        return self.head_view(catalog, ns, view, token=token).ok

    def commit_view(self, catalog, ns, view, updates, requirements=None, token=None):
        """POST /v1/{catalog}/namespaces/{ns}/views/{view} — replace/update a view.

        Args:
            updates: list of update dicts, each with an "action" key.
            requirements: optimistic-concurrency preconditions; defaults to [].

        Returns:
            requests.Response — 200 with the new view metadata, 409 on a failed
            requirement.
        """
        payload = {"requirements": requirements or [], "updates": updates}
        return requests.post(
            f"{self._cat(catalog)}/namespaces/{self._ns_path(ns)}/views/{view}",
            headers=self._h(token),
            json=payload,
        )

    def rename_view(
        self, catalog, source_ns, source_name, dest_ns, dest_name, token=None
    ):
        """POST /v1/{catalog}/views/rename — rename or move a view.

        Catalog-scoped like `rename_table`, for the same reason.

        Returns:
            requests.Response — 204 on success, 404 if source absent, 409 if
            destination taken.
        """
        payload = {
            "source": {
                "namespace": (
                    list(source_ns)
                    if isinstance(source_ns, (list, tuple))
                    else [source_ns]
                ),
                "name": source_name,
            },
            "destination": {
                "namespace": (
                    list(dest_ns) if isinstance(dest_ns, (list, tuple)) else [dest_ns]
                ),
                "name": dest_name,
            },
        }
        return requests.post(
            f"{self._cat(catalog)}/views/rename", headers=self._h(token), json=payload
        )

    def drop_view(self, catalog, ns, view, purge=False, token=None):
        """DELETE /v1/{catalog}/namespaces/{ns}/views/{view} — drop a view.

        Args:
            purge: sets `?purgeRequested=true`. Views have no data files, so
                unlike tables this is largely a no-op — kept for symmetry and
                because the parameter's effect on the authorization path is
                itself worth measuring.

        Returns:
            requests.Response — 204 on success, 404 if absent.
        """
        params = {"purgeRequested": "true"} if purge else None
        return requests.delete(
            f"{self._cat(catalog)}/namespaces/{self._ns_path(ns)}/views/{view}",
            headers=self._h(token),
            params=params,
        )

    # ------------------------------------------------------------------
    # transactions
    # ------------------------------------------------------------------
    def commit_transaction(self, catalog, table_changes, token=None):
        """POST /v1/{catalog}/transactions/commit — multi-table atomic commit.

        Args:
            table_changes: list of CommitTableRequest dicts, each carrying its
                own `identifier`, `requirements` and `updates`.

        Returns:
            requests.Response — 204 on success, 409 if ANY table's requirements
            fail (the whole transaction is rejected).

        Note:
            The one API where a single HTTP call resolves and locks N tables,
            so its cost should scale with N. Sweeping N is the cleanest way to
            see whether entity resolution is batched or sequential — and given
            QueryGenerator emits no JOINs, sequential is the likely answer.
        """
        payload = {"table-changes": table_changes}
        return requests.post(
            f"{self._cat(catalog)}/transactions/commit",
            headers=self._h(token),
            json=payload,
        )


# ----------------------------------------------------------------------
# payload builders — optional conveniences for the common shapes
# ----------------------------------------------------------------------
def build_schema(fields, schema_id=0):
    """Build a minimal Iceberg schema dict.

    Args:
        fields: list of (id, name, type, required) tuples, e.g.
            [(1, "id", "long", True), (2, "name", "string", False)].
        schema_id: schema id, default 0.

    Returns:
        dict — an Iceberg `struct` schema suitable for a CreateTableRequest.

    Note:
        Field count drives the size of the `properties` JSONB and of the
        metadata.json, so this is the knob to turn when sweeping create/commit
        cost against schema width.
    """
    return {
        "type": "struct",
        "schema-id": schema_id,
        "fields": [
            {"id": fid, "name": fname, "required": bool(req), "type": ftype}
            for (fid, fname, ftype, req) in fields
        ],
    }


def build_create_table_payload(
    name,
    schema,
    location=None,
    properties=None,
    partition_spec=None,
    write_order=None,
    stage_create=False,
):
    """Build a CreateTableRequest body.

    Args:
        name: table name.
        schema: schema dict, e.g. from `build_schema`.
        location: optional explicit table base location. Omit to let Polaris
            derive it from the namespace/catalog default.
        properties: optional table property map.
        partition_spec: optional PartitionSpec dict.
        write_order: optional SortOrder dict.
        stage_create: when True, reserve without persisting (see
            `IcebergREST.stage_create_table`).

    Returns:
        dict ready to pass to `IcebergREST.create_table`.
    """
    payload = {"name": name, "schema": schema}
    if location:
        payload["location"] = location
    if properties:
        payload["properties"] = properties
    if partition_spec:
        payload["partition-spec"] = partition_spec
    if write_order:
        payload["write-order"] = write_order
    if stage_create:
        payload["stage-create"] = True
    return payload


def build_set_properties_update(updates):
    """Build a `set-properties` update entry for a commit request.

    The cheapest possible real commit — no snapshot, no schema change — which
    makes it the right probe for isolating commit *overhead* from the cost of
    the metadata change itself.

    Args:
        updates: dict of properties to set.

    Returns:
        dict — one entry for a CommitTableRequest's `updates` list.
    """
    return {"action": "set-properties", "updates": updates}


def build_assert_table_uuid_requirement(uuid):
    """Build an `assert-table-uuid` requirement entry.

    The standard precondition every real engine sends. Include it when
    measuring commits so the measured path matches production, where the
    server must verify the requirement before applying updates.

    Args:
        uuid: the table's UUID, from a prior `load_table` response.

    Returns:
        dict — one entry for a CommitTableRequest's `requirements` list.
    """
    return {"type": "assert-table-uuid", "uuid": uuid}
