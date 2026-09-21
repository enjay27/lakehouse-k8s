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


def build_view_payload(name, namespace, schema):
    """A minimal CreateViewRequest. One shape, used by the fixture and by the
    sweep, because two spellings of it is how `probe_view` came to exist in
    one path and not the other."""
    return {
        "name": name,
        "schema": schema,
        "view-version": {
            "version-id": 1,
            "schema-id": 0,
            "timestamp-ms": 0,
            "summary": {"operation": "create"},
            "representations": [{"type": "sql", "sql": "SELECT 1", "dialect": "spark"}],
            "default-namespace": [namespace],
        },
        "properties": {},
    }


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
        return build_view_payload(name or self.view, self.ns, self.schema)


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
            # DISPOSABLE, like `probe_tbl2` beside it. It used to create
            # `c.view` itself, which is why `setup_fixture` did not build one
            # -- and why the grid, which does not run this sweep, drove eleven
            # cells against a view that never existed.
            fn=lambda c: c.ic.create_view(
                c.cat, c.ns, build_view_payload("probe_view2", c.ns, c.schema)
            ),
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
            fn=lambda c: c.ic.rename_view(
                c.cat, c.ns, "probe_view2", c.ns, "probe_view3"
            ),
        ),
        Operation(
            "iceberg.drop_view",
            "DELETE",
            "/v1/{cat}/namespaces/{ns}/views/{view}",
            fn=lambda c: c.ic.drop_view(c.cat, c.ns, "probe_view3"),
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
    def other(self):
        """Statuses that are NEITHER 2xx nor 401/403, with their codes.

        This property exists because the summary line lied. A run reporting
        "driven 43/43  permitted 2  refused 22  errors 0" reads as complete and
        omits 19 operations -- every one of them a 404, and every one of them
        carrying statements the audit wants. Same failure as the reconciliation
        that survived because two errors netted out: a total that looks right
        while its composition is wrong.
        """
        return {
            k: v
            for k, v in self.statuses.items()
            if v is None or (not (200 <= v < 300) and v not in (401, 403))
        }

    @property
    def distribution(self):
        """Every status code and how many operations returned it."""
        import collections

        return dict(
            sorted(
                collections.Counter(self.statuses.values()).items(),
                key=lambda kv: -kv[1],
            )
        )

    @property
    def driven(self):
        return len(self.statuses) + len(self.errors)


class CaptureNotRecording(RuntimeError):
    """The tracer read no SQL for operations that certainly issued some.

    Raised by `drive` rather than returned, because there is nothing useful to
    do with the remaining operations: every one of them will produce an empty
    row, and a report of 43 empty rows is indistinguishable from a report of a
    cluster that issued no SQL.
    """


def drive(tracer, ops, ctx, on_record=None, assert_recording_within=3):
    """Issue every operation in order, recording outcomes, never stopping.

    A refusal is the measurement, not a failure: a 403 still pays the full
    authorization prelude and still says which tables the authorization path
    touched. An EXCEPTION is different -- the harness failed, and it is kept in
    `errors` so it can never be mistaken for a refusal.

    WHY THE RECORDING CHECK IS PER-OPERATION AND NOT A PREFLIGHT (2026-09-02).
    Three drives completed cleanly and captured nothing: 43/43 operations, zero
    errors, and `0 statements` on every row. The gate that should have caught it
    ran ONCE before the sweep, and a gate that passes once cannot notice a
    stream that stops afterwards -- which is exactly what happened, and is still
    unexplained. A preflight is also weak in a subtler way: the natural probe
    call is `list_catalogs`, and that is the one call the broken captures DID
    record, so a preflight built on it goes green on a capture that records
    nothing else.

    So the check runs inside the loop, on the operations actually being
    measured. It is deliberately NOT "every 2xx must issue SQL" -- some
    operations legitimately issue none, and a rule that fires on one of those
    would be turned off within a week. It is: if the first
    `assert_recording_within` records hold zero statements BETWEEN them, the
    capture is not recording. Every authorized call here pays an authorization
    prelude that touches `entities` and `grant_records`, so three consecutive
    empty records is not a quiet cluster.

    Costs one comparison per operation, fails in about five seconds rather than
    after the 43rd, and the three wasted drives that motivated it each cost a
    Polaris restart plus a capture.

    Args:
        assert_recording_within: how many leading records may hold zero
            statements between them before `CaptureNotRecording` is raised.
            Ignored when the tracer has no `polaris_log` stream, since nothing
            is claiming to record. `None` disables it outright.
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

        #: `polaris_log` guards the guard. A `Tracer` with no streams is a
        #: documented, legitimate degradation -- it still yields wall-clock
        #: timings -- and it is what every unit test of this function uses.
        #: Firing on it would be an assertion about a capture nobody attached.
        #: The fault this catches is narrower and worse: a stream IS attached
        #: and reads nothing.
        if (
            assert_recording_within
            and getattr(tracer, "polaris_log", None)
            and len(result.records) == assert_recording_within
            and not any(r.sql_count for r in result.records)
        ):
            raise CaptureNotRecording(
                f"the tracer read NO SQL across the first {assert_recording_within} "
                f"operations ({', '.join(r.api for r in result.records)}). Every "
                "authorized call here pays an authorization prelude that touches "
                "entities and grant_records, so this is the capture, not the "
                "cluster.\n"
                "  Check, in this order:\n"
                "   1. is the capture directory the one being WRITTEN? Pass "
                "--capture explicitly; find_capture_dir() needs a NON-EMPTY "
                "polaris.log and will otherwise pick a stale directory.\n"
                "   2. are the tails still alive?  kill -0 $(awk '{print $1}' "
                "<capture>/.pids)\n"
                "   3. is SQL logging on?  ./capture.sh preflight  (rotate does "
                "NOT enable it; pgon is separate)\n"
                "  Do NOT read a 43/43 pass as evidence -- three of them have "
                "already produced empty reports."
            )
    return result


# ----------------------------------------------------------------------
# the probe fixture — created ONCE, as admin, and driven by every identity
# ----------------------------------------------------------------------
@dataclass
class ProbeFixture:
    """The entities the surface is driven against, and their names.

    Created and destroyed by the ADMIN identity. That is not a convenience: a
    catalog-scoped principal cannot create a catalog at all (Polaris 1.3.0 has
    no service-level grant type), and an unauthorized one cannot create
    anything -- so a fixture built by the identity under test would restrict
    the experiment to identities that do not need testing.

    ONE FIXTURE, THREE DRIVES. Reusing it across the cases is what isolates the
    variable: the parameters an operation binds are then identical between
    cases except for the caller's own identity, which is the whole comparison.
    The sweep is self-cleaning by construction -- every entity it creates
    (`probe_ns_tmp`, `probe_tbl2`->`probe_tbl3`, the view, the principal and
    roles) is dropped by a later operation in the same list.

    DRIVE ORDER: the two refused cases first, admin LAST. Only the admin drive
    mutates -- the others 403 before touching anything -- so running admin last
    leaves the fixture pristine for the cases that must see it unchanged.
    """

    prefix: str
    cat: str = None
    ns: str = "probe_ns"
    ns2: str = "probe_ns2"
    tbl: str = "probe_tbl"
    view: str = "probe_view"
    principal: str = None
    prole: str = None
    crole: str = None

    def __post_init__(self):
        self.cat = self.cat or f"{self.prefix}_cat"
        self.principal = self.principal or f"{self.prefix}_p"
        self.prole = self.prole or f"{self.prefix}_pr"
        self.crole = self.crole or f"{self.prefix}_cr"

    @classmethod
    def stamped(cls, now=None):
        """A fresh prefix. `apiprofile*` is swept by teardown, so keep the stem."""
        from datetime import datetime

        ts = int((now or datetime.now()).timestamp())
        return cls(prefix=f"apiprofile{ts}")

    def context(self, ic, pc, adm, schema):
        """A `SurfaceContext` pointing the DRIVE clients at this fixture."""
        return SurfaceContext(
            ic=ic,
            pc=pc,
            adm=adm,
            cat=self.cat,
            ns=self.ns,
            tbl=self.tbl,
            view=self.view,
            principal=self.principal,
            prole=self.prole,
            crole=self.crole,
            schema=schema,
        )


def setup_fixture(
    fx,
    adm_pc,
    adm_ic,
    bucket,
    endpoint,
    schema,
    payload_builder,
    ensure_catalog=None,
    attempt=None,
    result=None,
):
    """Build the probe fixture as admin. Tolerates replication lag; fails loudly.

    Reuses the seeder's `_attempt`/`_ensure_catalog` rather than writing a third
    variant of lag handling. `_attempt` encodes what a thousand-user seed
    taught: on 5xx/403/404 the prerequisite may simply not have replicated yet,
    so verify existence and retry with backoff; a duplicate-key body means the
    write already landed; any other 4xx is real and must not be retried.

    `_ensure_catalog` rather than a bare create, because a catalog whose entity
    commits while its grant bootstrap does not is permanently unusable -- it
    verifies `catalog_admin` is really there instead of trusting a 200 from
    `get_catalog`.

    Creating a catalog does NOT grant rights inside it. `service_admin` covers
    CATALOG_CREATE/CATALOG_LIST at the ROOT container, but namespace and table
    operations are CATALOG-scoped and authorize against `grant_records`, so the
    explicit CATALOG_MANAGE_CONTENT grant is load-bearing.
    """
    if ensure_catalog is None or attempt is None or result is None:
        from polaris_seed import SeedResult, _attempt, _ensure_catalog

        ensure_catalog = ensure_catalog or _ensure_catalog
        attempt = attempt or _attempt
        result = result if result is not None else SeedResult()

    def ck(call, what, exists=None):
        #: `call` is a CALLABLE, not an already-made response. The earlier
        #: version asserted on a response it had been handed, so a 500 that had
        #: in fact committed -- or would have succeeded a moment later --
        #: aborted the whole run.
        ok, r = attempt(call, what, result, exists=exists)
        if not ok:
            raise AssertionError(f"{what} -> [{r.status_code}] {r.text[:300]}")
        return r

    ensure_catalog(adm_pc, fx.cat, bucket, endpoint, result)
    ck(
        lambda: adm_pc.grant_privilege(
            fx.cat, "catalog_admin", "CATALOG_MANAGE_CONTENT"
        ),
        "grant CATALOG_MANAGE_CONTENT",
    )
    for ns in (fx.ns, fx.ns2):
        ck(
            lambda ns=ns: adm_ic.create_namespace(fx.cat, ns),
            f"create namespace {ns}",
            lambda ns=ns: adm_ic.namespace_exists(fx.cat, ns),
        )
    ck(
        lambda: adm_ic.create_table(fx.cat, fx.ns, payload_builder(fx.tbl, schema)),
        f"create table {fx.tbl}",
        lambda: adm_ic.table_exists(fx.cat, fx.ns, fx.tbl),
    )
    # THE VIEW. `fx.view` is bound into eleven cells of the status grid and
    # nothing created it: `api_status_matrix.REBIND` states that the fixture
    # "catalog / namespace / table / view" is read by the happy cells and by
    # every 401/403/404 cell and is never destroyed by one -- true, and it was
    # never BUILT either. Run 1789950539 reported loadView, viewExists and
    # replaceView as MISSED with 404 at their 2xx and 403 cells, and
    # replaceView again at 409 and 400: eight misses on three operations,
    # every one of them read as a fact about Polaris. The teardown said so in
    # the same run -- `drop view probe_view 404`.
    ck(
        lambda: adm_ic.create_view(
            fx.cat, fx.ns, build_view_payload(fx.view, fx.ns, schema)
        ),
        f"create view {fx.view}",
        lambda: adm_ic.head_view(fx.cat, fx.ns, fx.view),
    )
    return result


def authorize_on_fixture(fx, adm_pc, principal_role, privileges=None, role_name=None):
    """Grant a principal-role rights ON the probe catalog. Admin only.

    WHY THIS IS NEEDED, and it is a correction to the plan rather than a
    convenience (2026-09-01). "One fixture, three drives" isolates the variable
    only for identities that can ACT on that fixture. A catalog-scoped principal
    cannot: Polaris authorizes catalog operations against `grant_records` for
    the TARGET catalog, and `authz1_principal` holds `owner_principal` on
    `authz1_catalog`, not on the probe catalog. Driven against the probe
    fixture it was refused on all 43 operations and produced a status
    distribution byte-identical to the zero-grant case -- a second unauthorized
    run wearing the authorized label, and nothing in either output said so.

    Only `service_admin` can act on an arbitrary catalog, which is why the admin
    case would have worked and hidden the problem entirely.

    So the authorized tier is granted access to the shared fixture, as admin,
    before it drives. That is a realistic shape -- a principal given rights on a
    catalog it does not own -- and it keeps all three cases on ONE fixture,
    which is what makes their parameters differ by the identity alone.

    Catalog-scoped only, deliberately. The management operations still 403,
    because that contrast with the admin case is the finding: administrative
    authority and DATA authority are separate in Polaris.
    """
    if privileges is None:
        try:
            from polaris_seed import CORE_CATALOG_PRIVILEGES

            privileges = list(CORE_CATALOG_PRIVILEGES)
        except Exception:  # noqa: BLE001
            privileges = ["CATALOG_MANAGE_CONTENT"]
    role = role_name or f"{fx.prefix}_shared"

    out = {"catalog_role": role, "granted": [], "failed": {}}
    r = adm_pc.create_catalog_role(fx.cat, role)
    out["create_catalog_role"] = r.status_code
    for priv in privileges:
        g = adm_pc.grant_privilege(fx.cat, role, priv)
        if 200 <= g.status_code < 300:
            out["granted"].append(priv)
        else:
            out["failed"][priv] = g.status_code
    a = adm_pc.assign_catalog_role_to_principal_role(fx.cat, principal_role, role)
    out["assign"] = a.status_code
    return out


#: The catalog-role Polaris creates with every catalog. It cannot be deleted
#: on its own (400, measured on two catalogs 2026-09-02) and does not need to
#: be -- deleting the catalog removes it. Named here so teardown can skip it
#: without burying the constant in a conditional.
BUILTIN_CATALOG_ROLE = "catalog_admin"


def walk_namespaces(catalog, adm_ic, max_depth=8):
    """Every namespace in a catalog, DEEPEST FIRST, as full level tuples.

    `GET /namespaces` returns only the TOP level; children come from the same
    endpoint with `?parent=`. The previous teardown listed once and then did
    `ns[0] if isinstance(ns, list) else ns`, which is wrong twice over: it never
    descended, and for a multi-level namespace `["a", "b"]` it took `"a"` and
    tried to drop the PARENT -- refused, because the child still existed, and
    the refusal was discarded.

    Deepest first is what makes the result directly drop-ordered: a namespace
    cannot be dropped while it holds children.

    Args:
        max_depth: recursion bound. Polaris does not limit namespace nesting,
            and a cycle here would be a server bug rather than a fixture, but
            an unbounded walk in a teardown is not worth the risk.

    Returns:
        list[tuple[str, ...]] -- deepest first, then arbitrary.
    """
    found = []

    def descend(parent, depth):
        if depth > max_depth:
            return
        r = adm_ic.list_namespaces(catalog, parent=list(parent) if parent else None)
        if r.status_code >= 300:
            return
        for ns in r.json().get("namespaces", []):
            levels = tuple(ns) if isinstance(ns, (list, tuple)) else (ns,)
            found.append((depth, levels))
            descend(levels, depth + 1)

    descend((), 0)
    found.sort(key=lambda dl: -dl[0])
    return [levels for _, levels in found]


def drop_catalog_tree(catalog, adm_pc, adm_ic):
    """Empty a catalog from the LEAVES UP, then delete it.

    Polaris refuses `DELETE /catalogs/{name}` while the catalog still holds
    content -- it answers **400**, not a cascade, and `purgeRequested` does not
    cascade either. So: tables and views, then namespaces deepest-first, then
    catalog-roles, then the catalog.

    THREE FAULTS THIS FIXES, all of which bit on 2026-09-02 when teardown
    reported `{"tables": 1, "views": 0, "namespaces": 2, "catalog": 400,
    "error": "... cannot be dropped, it is not empty"}`:

    1. **Catalog-roles were never dropped.** `authorize_on_fixture` creates
       `{prefix}_shared` on the probe catalog so the authorized tier can drive
       it, and teardown had no idea it existed.
    2. **The counts were ATTEMPTS, not successes.** Every drop's status was
       discarded and the counter incremented unconditionally, so `"namespaces":
       2` could mean "two tried, both refused". A teardown that cannot
       distinguish those is a teardown whose report cannot be read -- which is
       why the 400 arrived as a surprise rather than as the obvious consequence
       of the line above it.
    3. **Nested namespaces were invisible.** See `walk_namespaces`.

    And when the catalog delete still fails, the report now says WHAT REMAINS
    rather than only that something does. A failure that does not name its own
    cause costs a session; this one costs a glance.

    Returns:
        dict with counts of what was successfully dropped, a `failed` map of
        what refused and why, and on a failed catalog delete a `remaining`
        listing.
    """
    report = {
        "tables": 0,
        "views": 0,
        "namespaces": 0,
        "catalog_roles": 0,
        "catalog": None,
        "failed": {},
    }

    def _drop(kind, key, call):
        """Run a drop and record its OUTCOME. Never counts an attempt."""
        try:
            r = call()
        except Exception as exc:  # noqa: BLE001
            report["failed"][f"{kind}:{key}"] = f"{type(exc).__name__}: {exc}"
            return False
        if r is not None and getattr(r, "status_code", 200) >= 300:
            report["failed"][f"{kind}:{key}"] = getattr(r, "status_code", "?")
            return False
        report[kind] += 1
        return True

    probe = adm_ic.list_namespaces(catalog)
    if probe.status_code == 404:
        report["catalog"] = "absent"
        return report

    for levels in walk_namespaces(catalog, adm_ic):
        ns = list(levels)
        label = ".".join(levels)
        r = adm_ic.list_tables(catalog, ns)
        if r.status_code < 300:
            for tbl in r.json().get("identifiers", []):
                _drop(
                    "tables",
                    f"{label}.{tbl['name']}",
                    lambda n=tbl["name"], s=ns: adm_ic.drop_table(
                        catalog, s, n, purge=True
                    ),
                )
        r = adm_ic.list_views(catalog, ns)
        if r.status_code < 300:
            for vw in r.json().get("identifiers", []):
                _drop(
                    "views",
                    f"{label}.{vw['name']}",
                    lambda n=vw["name"], s=ns: adm_ic.drop_view(catalog, s, n),
                )
        _drop("namespaces", label, lambda s=ns: adm_ic.drop_namespace(catalog, s))

    #: Catalog-roles last among the contents, and `catalog_admin` is SKIPPED.
    #: Polaris creates it with every catalog and refuses to delete it -- 400,
    #: measured on two separate catalogs 2026-09-02 -- and removes it with the
    #: catalog itself, which both of those then deleted 204. So attempting it
    #: puts a permanent `catalog_roles:catalog_admin: 400` in every clean
    #: teardown's `failed` map, and a failure map that is never empty is a
    #: failure map nobody reads. Skipped by NAME and only this name: any other
    #: role that refuses is a real fault and still lands in `failed`.
    r = adm_pc.list_catalog_roles(catalog)
    if r.status_code < 300:
        for role in r.json().get("roles", []):
            name = role["name"] if isinstance(role, dict) else role
            if name == BUILTIN_CATALOG_ROLE:
                report["builtin_role_skipped"] = name
                continue
            _drop(
                "catalog_roles",
                name,
                lambda n=name: adm_pc.delete_catalog_role(catalog, n),
            )

    d = adm_pc.delete_catalog(catalog, purge=True)
    report["catalog"] = d.status_code
    if d.status_code >= 300:
        report["error"] = d.text[:200]
        #: Say what is still there. "Not empty" without an inventory is the
        #: message that sent 2026-09-02 looking for the residue by hand.
        left = {}
        try:
            left["namespaces"] = [".".join(x) for x in walk_namespaces(catalog, adm_ic)]
            rr = adm_pc.list_catalog_roles(catalog)
            if rr.status_code < 300:
                left["catalog_roles"] = [
                    x["name"] if isinstance(x, dict) else x
                    for x in rr.json().get("roles", [])
                ]
        except Exception as exc:  # noqa: BLE001
            left["inventory_error"] = f"{type(exc).__name__}: {exc}"
        report["remaining"] = left
    return report


def teardown_fixture(fx, adm_pc, adm_ic, sweep_stale=True):
    """Remove the fixture, and any probe catalog an earlier aborted run left.

    The sweep exists because a run that dies during setup never reaches
    teardown, and its catalog stays. Every `apiprofile*` catalog is this
    harness's own fixture, so sweeping them is safe and keeps `find_strays`
    meaningful -- an assertion that is routinely violated by known residue is
    an assertion nobody reads.
    """
    out = {"fixture": drop_catalog_tree(fx.cat, adm_pc, adm_ic), "swept": {}}
    for call in (
        lambda: adm_pc.delete_principal_role(fx.prole),
        lambda: adm_pc.delete_principal(fx.principal),
    ):
        try:
            call()
        except Exception as exc:  # noqa: BLE001
            out.setdefault("errors", []).append(f"{type(exc).__name__}: {exc}")
    if sweep_stale:
        for c in adm_pc.list_catalogs().json().get("catalogs", []):
            name = c["name"] if isinstance(c, dict) else c
            if name.startswith("apiprofile") and name != fx.cat:
                out["swept"][name] = drop_catalog_tree(name, adm_pc, adm_ic)
    return out
