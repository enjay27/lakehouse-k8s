"""The 43-operation API surface, as an ordered catalogue that any identity can drive.

WHY THIS IS A MODULE AND NOT A NOTEBOOK CELL
--------------------------------------------
`01_api_access_map.ipynb` drives this surface as a flat run of `probe(...)`
calls bound to module-level names and a single root-credentialled client. That
worked while there was one identity. It cannot answer the question this audit
now asks -- *does the plan change with the caller's grant footprint* -- because
two of the three identities cannot run the notebook's flow at all:

  * an **unauthorized** principal 403s on the probe-fixture setup itself;
  * a **catalog-scoped** principal cannot create a catalog, since Polaris 1.3.0
    has no service-level grant type and catalog creation needs `service_admin`.

So setup and driving have to be separable, which means the operation list has
to be a value rather than a script. Splitting it out also puts it where
CLAUDE.md says it belongs: notebooks hold visualization, `src/` holds logic
that wants a test.

THE ONE INVARIANT THAT MATTERS
------------------------------
**Setup and teardown use `ctx.adm`. Every operation uses `ctx.ic` / `ctx.pc`.**
If an operation reached for the admin client, its 403 would never happen and
the unauthorized case would quietly report a successful sweep -- the fixture
would look like a finding about Polaris when it was a finding about which
token got used. `test_no_operation_touches_the_admin_client` asserts it, with
a client that raises on any attribute access.

A REFUSAL IS DATA
-----------------
`drive()` records the outcome and continues, exactly as the notebook's `probe()
did: "a 403 or 404 still tells you which tables the authorization path
touched." Measured 2026-08-31 -- a 403 pays the FULL authorization prelude,
same statement shapes, one `grant_records` grantee lookup each, before the
decision is made. The denial path is a measurement, not a gap.
"""

from dataclasses import dataclass, field

#: HTTP methods that only read. Everything else mutates, which is what decides
#: whether a statement may be EXPLAINed with ANALYZE -- `EXPLAIN ANALYZE` on an
#: INSERT/UPDATE/DELETE really performs it.
READ_METHODS = ("GET", "HEAD")


@dataclass
class Operation:
    """One API call, its shape, and how to issue it.

    `fn` takes the context and returns a response. `prepare` runs OUTSIDE the
    trace when an operation needs a value read back from the cluster first --
    the notebook did this for `report_metrics`, whose ScanReport needs a real
    `snapshot-id`, and keeping it outside matters: a read-back attributed to
    the operation would add statements the operation does not issue.
    """

    label: str
    method: str
    path: str
    fn: object = None
    core: bool = False
    prepare: object = None

    @property
    def kind(self):
        return "read" if self.method in READ_METHODS else "write"


@dataclass
class SurfaceContext:
    """Clients and fixture names for one drive.

    `adm` is the ADMIN client and is used by setup and teardown only. `ic` and
    `pc` are the DRIVE clients -- whichever identity's authorization is being
    measured. They are the same object only when driving as admin.
    """

    ic: object = None
    pc: object = None
    adm: object = None
    cat: str = None
    ns: str = None
    tbl: str = None
    view: str = None
    principal: str = None
    prole: str = None
    crole: str = None
    schema: object = None
    #: Values one operation reads back for a later one. Kept explicit rather
    #: than as module state, which is what made the notebook version
    #: un-runnable twice over.
    scratch: dict = field(default_factory=dict)

    def view_payload(self, name=None):
        return {
            "name": name or self.view,
            "schema": self.schema,
            "view-version": {
                "version-id": 1,
                "schema-id": 0,
                "timestamp-ms": 0,
                "summary": {"operation": "create"},
                "representations": [
                    {"type": "sql", "sql": "SELECT 1", "dialect": "spark"}
                ],
                "default-namespace": [self.ns],
            },
            "properties": {},
        }


def _snapshot_prepare(ctx):
    """Read the probe table's current snapshot id, untraced.

    A ScanReport needs all seven required fields and a REAL `snapshot-id`; the
    probe table has been committed to by this point, so read it back rather
    than inventing one. An invented id was a 400, which would then have been
    filed as an API outcome rather than a payload mistake.
    """
    try:
        meta = ctx.ic.load_table(ctx.cat, ctx.ns, ctx.tbl).json().get("metadata", {})
        ctx.scratch["snapshot"] = meta.get("current-snapshot-id", -1)
    except Exception:  # noqa: BLE001 - an identity that cannot read it still drives
        ctx.scratch["snapshot"] = -1


def operations(ctx, payload_builder=None, scan_report_builder=None):
    """The 43 operations, in issue order.

    ORDER IS LOAD-BEARING and is why this returns a list rather than a dict.
    Three chains depend on it -- create_namespace before drop_namespace,
    create_table -> rename_table -> drop_table, create_view -> rename_view ->
    drop_view -- and the management block creates a principal, a principal-role
    and a catalog-role before granting on them and deleting them. Reordering
    turns later operations into 404s that look like refusals.

    Args:
        ctx: a `SurfaceContext`.
        payload_builder: `iceberg_rest.build_create_table_payload`.
        scan_report_builder: `iceberg_rest.build_scan_report`.

    Returns:
        list[Operation], 43 long, matching the API labels in a
        `doc-api-sql-matrix-*.md` report exactly.
    """
    tbl = payload_builder
    scan = scan_report_builder
    ops = [
        # ---- Iceberg REST: config & namespaces ----
        Operation(
            "iceberg.get_config",
            "GET",
            "/v1/config",
            core=True,
            fn=lambda c: c.ic.get_config(warehouse=c.cat),
        ),
        Operation(
            "iceberg.list_namespaces",
            "GET",
            "/v1/{cat}/namespaces",
            core=True,
            fn=lambda c: c.ic.list_namespaces(c.cat),
        ),
        Operation(
            "iceberg.load_namespace",
            "GET",
            "/v1/{cat}/namespaces/{ns}",
            core=True,
            fn=lambda c: c.ic.load_namespace(c.cat, c.ns),
        ),
        Operation(
            "iceberg.head_namespace",
            "HEAD",
            "/v1/{cat}/namespaces/{ns}",
            fn=lambda c: c.ic.head_namespace(c.cat, c.ns),
        ),
        Operation(
            "iceberg.update_namespace_properties",
            "POST",
            "/v1/{cat}/namespaces/{ns}/properties",
            fn=lambda c: c.ic.update_namespace_properties(
                c.cat, c.ns, updates={"k": "v"}
            ),
        ),
        Operation(
            "iceberg.create_namespace",
            "POST",
            "/v1/{cat}/namespaces",
            core=True,
            fn=lambda c: c.ic.create_namespace(c.cat, "probe_ns_tmp"),
        ),
        Operation(
            "iceberg.drop_namespace",
            "DELETE",
            "/v1/{cat}/namespaces/{ns}",
            core=True,
            fn=lambda c: c.ic.drop_namespace(c.cat, "probe_ns_tmp"),
        ),
        # ---- Iceberg REST: tables ----
        Operation(
            "iceberg.list_tables",
            "GET",
            "/v1/{cat}/namespaces/{ns}/tables",
            core=True,
            fn=lambda c: c.ic.list_tables(c.cat, c.ns),
        ),
        Operation(
            "iceberg.load_table",
            "GET",
            "/v1/{cat}/namespaces/{ns}/tables/{tbl}",
            core=True,
            fn=lambda c: c.ic.load_table(c.cat, c.ns, c.tbl),
        ),
        Operation(
            "iceberg.load_table[snapshots=refs]",
            "GET",
            "/v1/{cat}/.../tables/{tbl}?snapshots=refs",
            fn=lambda c: c.ic.load_table(c.cat, c.ns, c.tbl, snapshots="refs"),
        ),
        Operation(
            "iceberg.head_table",
            "HEAD",
            "/v1/{cat}/namespaces/{ns}/tables/{tbl}",
            fn=lambda c: c.ic.head_table(c.cat, c.ns, c.tbl),
        ),
        Operation(
            "iceberg.create_table",
            "POST",
            "/v1/{cat}/namespaces/{ns}/tables",
            core=True,
            fn=lambda c: c.ic.create_table(c.cat, c.ns, tbl("probe_tbl2", c.schema)),
        ),
        Operation(
            "iceberg.stage_create_table",
            "POST",
            "/v1/{cat}/namespaces/{ns}/tables[stage]",
            fn=lambda c: c.ic.stage_create_table(
                c.cat, c.ns, tbl("probe_staged", c.schema)
            ),
        ),
        Operation(
            "iceberg.commit_table",
            "POST",
            "/v1/{cat}/namespaces/{ns}/tables/{tbl}",
            core=True,
            fn=lambda c: c.ic.commit_table(
                c.cat,
                c.ns,
                c.tbl,
                [{"action": "set-properties", "updates": {"p": "1"}}],
            ),
        ),
        Operation(
            "iceberg.rename_table",
            "POST",
            "/v1/{cat}/tables/rename",
            fn=lambda c: c.ic.rename_table(
                c.cat, c.ns, "probe_tbl2", c.ns, "probe_tbl3"
            ),
        ),
        Operation(
            "iceberg.report_metrics",
            "POST",
            "/v1/{cat}/.../tables/{tbl}/metrics",
            prepare=_snapshot_prepare,
            fn=lambda c: c.ic.report_metrics(
                c.cat, c.ns, c.tbl, scan(c.tbl, c.scratch.get("snapshot", -1))
            ),
        ),
        Operation(
            "iceberg.load_table[missing]",
            "GET",
            "/v1/{cat}/.../tables/{missing}",
            fn=lambda c: c.ic.load_table(c.cat, c.ns, "does_not_exist"),
        ),
        Operation(
            "iceberg.drop_table",
            "DELETE",
            "/v1/{cat}/namespaces/{ns}/tables/{tbl}",
            core=True,
            fn=lambda c: c.ic.drop_table(c.cat, c.ns, "probe_tbl3"),
        ),
        # ---- Iceberg REST: views ----
        Operation(
            "iceberg.create_view",
            "POST",
            "/v1/{cat}/namespaces/{ns}/views",
            fn=lambda c: c.ic.create_view(c.cat, c.ns, c.view_payload()),
        ),
        Operation(
            "iceberg.list_views",
            "GET",
            "/v1/{cat}/namespaces/{ns}/views",
            fn=lambda c: c.ic.list_views(c.cat, c.ns),
        ),
        Operation(
            "iceberg.load_view",
            "GET",
            "/v1/{cat}/namespaces/{ns}/views/{view}",
            fn=lambda c: c.ic.load_view(c.cat, c.ns, c.view),
        ),
        Operation(
            "iceberg.head_view",
            "HEAD",
            "/v1/{cat}/namespaces/{ns}/views/{view}",
            fn=lambda c: c.ic.head_view(c.cat, c.ns, c.view),
        ),
        Operation(
            "iceberg.rename_view",
            "POST",
            "/v1/{cat}/views/rename",
            fn=lambda c: c.ic.rename_view(c.cat, c.ns, c.view, c.ns, "probe_view2"),
        ),
        Operation(
            "iceberg.drop_view",
            "DELETE",
            "/v1/{cat}/namespaces/{ns}/views/{view}",
            fn=lambda c: c.ic.drop_view(c.cat, c.ns, "probe_view2"),
        ),
        # ---- Management API ----
        Operation(
            "mgmt.list_catalogs",
            "GET",
            "/v1/catalogs",
            core=True,
            fn=lambda c: c.pc.list_catalogs(),
        ),
        Operation(
            "mgmt.get_catalog",
            "GET",
            "/v1/catalogs/{cat}",
            core=True,
            fn=lambda c: c.pc.get_catalog(c.cat),
        ),
        Operation(
            "mgmt.create_principal",
            "POST",
            "/v1/principals",
            core=True,
            fn=lambda c: c.pc.create_principal(c.principal),
        ),
        Operation(
            "mgmt.get_principal",
            "GET",
            "/v1/principals/{p}",
            fn=lambda c: c.pc.get_principal(c.principal),
        ),
        Operation(
            "mgmt.list_principals",
            "GET",
            "/v1/principals",
            fn=lambda c: c.pc.list_principals(),
        ),
        Operation(
            "mgmt.create_principal_role",
            "POST",
            "/v1/principal-roles",
            fn=lambda c: c.pc.create_principal_role(c.prole),
        ),
        Operation(
            "mgmt.get_principal_role",
            "GET",
            "/v1/principal-roles/{r}",
            fn=lambda c: c.pc.get_principal_role(c.prole),
        ),
        Operation(
            "mgmt.list_principal_roles",
            "GET",
            "/v1/principal-roles",
            fn=lambda c: c.pc.list_principal_roles(),
        ),
        Operation(
            "mgmt.assign_principal_role",
            "PUT",
            "/v1/principals/{p}/principal-roles",
            fn=lambda c: c.pc.assign_principal_role_to_principal(c.principal, c.prole),
        ),
        Operation(
            "mgmt.create_catalog_role",
            "POST",
            "/v1/catalogs/{cat}/catalog-roles",
            fn=lambda c: c.pc.create_catalog_role(c.cat, c.crole),
        ),
        Operation(
            "mgmt.list_catalog_roles",
            "GET",
            "/v1/catalogs/{cat}/catalog-roles",
            fn=lambda c: c.pc.list_catalog_roles(c.cat),
        ),
        Operation(
            "mgmt.assign_catalog_role",
            "PUT",
            "/v1/principal-roles/{r}/catalog-roles/{cat}",
            fn=lambda c: c.pc.assign_catalog_role_to_principal_role(
                c.cat, c.prole, c.crole
            ),
        ),
        Operation(
            "mgmt.grant_privilege",
            "PUT",
            "/v1/catalogs/{cat}/catalog-roles/{cr}/grants",
            core=True,
            fn=lambda c: c.pc.grant_privilege(c.cat, c.crole, "TABLE_READ_DATA"),
        ),
        Operation(
            "mgmt.list_grants",
            "GET",
            "/v1/catalogs/{cat}/catalog-roles/{cr}/grants",
            core=True,
            fn=lambda c: c.pc.list_grants(c.cat, c.crole),
        ),
        Operation(
            "mgmt.list_principals_for_principal_role",
            "GET",
            "/v1/principal-roles/{r}/principals",
            fn=lambda c: c.pc.list_principals_for_principal_role(c.prole),
        ),
        Operation(
            "mgmt.reset_principal_credentials",
            "POST",
            "/v1/principals/{p}/reset",
            fn=lambda c: c.pc.reset_principal_credentials(c.principal),
        ),
        Operation(
            "mgmt.delete_catalog_role",
            "DELETE",
            "/v1/catalogs/{cat}/catalog-roles/{cr}",
            fn=lambda c: c.pc.delete_catalog_role(c.cat, c.crole),
        ),
        Operation(
            "mgmt.delete_principal_role",
            "DELETE",
            "/v1/principal-roles/{r}",
            fn=lambda c: c.pc.delete_principal_role(c.prole),
        ),
        Operation(
            "mgmt.delete_principal",
            "DELETE",
            "/v1/principals/{p}",
            core=True,
            fn=lambda c: c.pc.delete_principal(c.principal),
        ),
    ]
    return ops


@dataclass
class DriveResult:
    """What a drive produced, including what it could not do.

    `errors` is separate from `refused` on purpose. A 403 is an authorization
    outcome and belongs in the measurement; a raised exception is the harness
    failing and must never be counted as one. Collapsing them is how a broken
    client reads as a restrictive cluster.
    """

    records: list = field(default_factory=list)
    statuses: dict = field(default_factory=dict)
    errors: dict = field(default_factory=dict)

    @property
    def refused(self):
        return sorted(k for k, v in self.statuses.items() if v in (401, 403))

    @property
    def permitted(self):
        return sorted(
            k for k, v in self.statuses.items() if v is not None and 200 <= v < 300
        )

    @property
    def driven(self):
        return len(self.statuses) + len(self.errors)


def drive(tracer, ops, ctx, on_record=None):
    """Issue every operation in order, recording outcomes, never stopping.

    A refusal is the measurement, not a failure: a 403 still pays the full
    authorization prelude and still says which tables the authorization path
    touched. An EXCEPTION is different -- the harness failed, and it is kept in
    `errors` so it can never be mistaken for a refusal.
    """
    result = DriveResult()
    for op in ops:
        if op.prepare:
            op.prepare(ctx)
        try:
            with tracer.trace(op.label, op.method, op.path) as rec:
                resp = op.fn(ctx)
                rec.status = getattr(resp, "status_code", None)
        except Exception as exc:  # noqa: BLE001
            result.errors[op.label] = f"{type(exc).__name__}: {exc}"
            continue
        rec.core = op.core
        result.records.append(rec)
        result.statuses[op.label] = rec.status
        if on_record:
            on_record(op, rec)
    return result
