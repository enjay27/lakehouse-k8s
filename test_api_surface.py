"""Tests for `api_surface` — the 43-operation catalogue any identity can drive.

WHY THIS FILE EXISTS. The surface used to be a flat run of `probe(...)` calls in
a notebook cell, bound to module-level names and one root-credentialled client.
Extracting it is only worth doing if the extraction is faithful, and "faithful"
has three separate meanings here, each with its own silent failure:

  * **the same 43 operations** — a transcription that drops one produces a
    report that is complete-looking and short, and nothing downstream compares
    it against the API list it claims to cover;
  * **the same order** — three create→rename→drop chains depend on it, and
    reordering turns later operations into 404s that read as refusals;
  * **the drive identity, on every operation** — an operation that reached for
    the admin client would never 403, so the unauthorized case would report a
    successful sweep and the fixture would look like a finding about Polaris.

The third is the one this whole design rests on, so its test uses a client that
raises on ANY attribute access rather than one that merely records.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
import api_surface as surf  # noqa: E402
import query_profile as qp  # noqa: E402


class Resp:
    def __init__(self, status=200, payload=None, text=""):
        self.status_code = status
        self._payload = payload or {}
        #: real responses carry it, and the setup failure path reads it — a
        #: stub without it turns a legitimate assertion into an AttributeError
        self.text = text

    def json(self):
        return self._payload


class Recorder:
    """A client that answers everything and remembers what it was asked."""

    def __init__(self, name, status=200, payload=None):
        self.name = name
        self.calls = []
        self._status = status
        self._payload = payload or {}

    def __getattr__(self, meth):
        def go(*a, **kw):
            self.calls.append((meth, a, kw))
            return Resp(self._status, self._payload)

        return go


class Forbidden:
    """A client that must never be touched. Any access is the bug."""

    def __init__(self, label="admin"):
        self.label = label

    def __getattr__(self, meth):
        raise AssertionError(
            f"an operation reached for the {self.label} client (.{meth}) — "
            "it would never 403, and the unauthorized case would report success"
        )


class Rec:
    def __init__(self):
        self.status = None
        self.core = False


class Tracer:
    def __init__(self):
        self.traced = []

    def trace(self, label, method, path):
        self.traced.append((label, method, path))
        rec = Rec()
        tr = self

        class _Ctx:
            def __enter__(self):
                return rec

            def __exit__(self, *a):
                tr.last = rec
                return False

        return _Ctx()


def _ctx(ic=None, pc=None, adm=None):
    return surf.SurfaceContext(
        ic=ic if ic is not None else Recorder("ic"),
        pc=pc if pc is not None else Recorder("pc"),
        adm=adm if adm is not None else Forbidden(),
        cat="probe_cat",
        ns="probe_ns",
        tbl="probe_tbl",
        view="probe_view",
        principal="probe_principal",
        prole="probe_prole",
        crole="probe_crole",
        schema={"type": "struct", "fields": []},
    )


def _ops(ctx):
    return surf.operations(
        ctx,
        payload_builder=lambda name, schema: {"name": name},
        scan_report_builder=lambda t, snap: {"table-name": t, "snapshot-id": snap},
    )


# ----------------------------------------------------------------------
def test_the_catalogue_is_the_43_apis_the_matrix_report_names():
    """Ties the extraction to the artifact, not to a number I typed.

    If a transcription dropped or renamed an operation, this fails with the
    exact label rather than with a count that someone re-baselines.
    """
    doc = ROOT / "diagnostics/api-sql-profile/reports/doc-api-sql-matrix-latest.md"
    if not doc.exists():  # pragma: no cover
        pytest.skip("matrix report not present")
    reported = set(qp.parse_api_statements(doc.read_text()).apis)
    ours = {op.label for op in _ops(_ctx())}
    assert ours == reported, (
        f"missing from catalogue: {sorted(reported - ours)}; "
        f"not in the report: {sorted(ours - reported)}"
    )
    assert len(ours) == 43


def test_no_operation_touches_the_admin_client():
    """THE invariant. Setup and teardown are admin; the sweep never is."""
    ctx = _ctx(adm=Forbidden())
    for op in _ops(ctx):
        if op.prepare:
            op.prepare(ctx)
        op.fn(ctx)  # raises via Forbidden if any op reaches for ctx.adm


def test_the_create_rename_drop_chains_keep_their_order():
    """Order is load-bearing: reordering makes later ops 404 and read as refusals."""
    labels = [op.label for op in _ops(_ctx())]
    for chain in (
        ["iceberg.create_namespace", "iceberg.drop_namespace"],
        ["iceberg.create_table", "iceberg.rename_table", "iceberg.drop_table"],
        ["iceberg.create_view", "iceberg.rename_view", "iceberg.drop_view"],
        [
            "mgmt.create_catalog_role",
            "mgmt.grant_privilege",
            "mgmt.list_grants",
            "mgmt.delete_catalog_role",
        ],
        ["mgmt.create_principal", "mgmt.get_principal", "mgmt.delete_principal"],
    ):
        idx = [labels.index(x) for x in chain]
        assert idx == sorted(idx), f"{chain} is out of order"


def test_read_and_write_split_follows_the_http_method():
    """Decides whether a statement may be EXPLAINed with ANALYZE, so it must
    not be a hand-maintained list that drifts from the method."""
    ops = _ops(_ctx())
    reads = {o.label for o in ops if o.kind == "read"}
    assert "iceberg.head_table" in reads, "HEAD reads"
    assert "iceberg.create_table" not in reads
    assert {o.kind for o in ops} == {"read", "write"}

    #: 21 read OPERATIONS, 19 distinct ENDPOINTS. `load_table` is driven three
    #: ways -- plain, `?snapshots=refs`, and against a missing table -- and the
    #: bracketed variants are the same endpoint exercised differently.
    #: `parse_api_matrix` folds them, which is why it reports 19 where the
    #: catalogue holds 21. Both numbers are correct and they answer different
    #: questions; asserting only one of them is how the fold gets forgotten and
    #: a coverage comparison silently comes out two short.
    assert len(reads) == 21
    assert len({r.split("[", 1)[0] for r in reads}) == 19


def test_report_metrics_reads_its_snapshot_outside_the_trace():
    """A read-back attributed to the operation would add statements it does not
    issue. The notebook did it outside `probe()`; `prepare` preserves that."""
    ctx = _ctx(ic=Recorder("ic", payload={"metadata": {"current-snapshot-id": 77}}))
    op = next(o for o in _ops(ctx) if o.label == "iceberg.report_metrics")
    assert op.prepare is not None
    op.prepare(ctx)
    assert ctx.scratch["snapshot"] == 77
    tracer = Tracer()
    surf.drive(tracer, [op], ctx)
    assert [t[0] for t in tracer.traced] == ["iceberg.report_metrics"]


def test_a_refusal_is_recorded_and_the_sweep_continues():
    """403 is the measurement. It still pays the full authorization prelude."""
    ctx = _ctx(ic=Recorder("ic", status=403), pc=Recorder("pc", status=403))
    res = surf.drive(Tracer(), _ops(ctx), ctx)
    assert res.driven == 43, "every operation attempted"
    assert len(res.refused) == 43
    assert res.permitted == []
    assert res.errors == {}, "a 403 is not an error"


def test_a_raised_exception_is_an_error_not_a_refusal():
    """Collapsing the two is how a broken client reads as a restrictive cluster."""

    class Broken:
        def __getattr__(self, m):
            def go(*a, **kw):
                raise ConnectionError("no route to host")

            return go

    ctx = _ctx(ic=Broken(), pc=Recorder("pc"))
    res = surf.drive(Tracer(), _ops(ctx), ctx)
    assert res.errors, "the harness failing must be visible"
    assert all("ConnectionError" in v for v in res.errors.values())
    assert res.refused == [], "an exception must never count as a refusal"
    assert res.permitted, "the mgmt half still drove"


def test_an_admin_drive_is_the_same_object_for_both_clients():
    """Driving as admin is the degenerate case, not a special path."""
    both = Recorder("adm")
    ctx = _ctx(ic=both, pc=both, adm=both)
    res = surf.drive(Tracer(), _ops(ctx), ctx)
    assert res.driven == 43 and len(res.permitted) == 43


# ----------------------------------------------------------------------
# the probe fixture — built as admin, driven by everyone
# ----------------------------------------------------------------------
class FakeCatalogs:
    """A management client that remembers catalogs and answers list_catalogs."""

    def __init__(self, names=()):
        self.names = list(names)
        self.deleted = []
        self.granted = []
        self.calls = []

    def list_catalogs(self):
        return Resp(200, {"catalogs": [{"name": n} for n in self.names]})

    def delete_catalog(self, name, purge=False):
        self.deleted.append(name)
        if name in self.names:
            self.names.remove(name)
        return Resp(204)

    def grant_privilege(self, cat, role, priv):
        self.granted.append((cat, role, priv))
        return Resp(200)

    def __getattr__(self, meth):
        def go(*a, **kw):
            self.calls.append((meth, a, kw))
            return Resp(200)

        return go


class FakeTree:
    """An Iceberg client over a {namespace: (tables, views)} tree."""

    def __init__(self, tree=None, missing=()):
        self.tree = tree if tree is not None else {}
        self.missing = set(missing)
        self.dropped = []
        self.created = []

    def list_namespaces(self, cat):
        if cat in self.missing:
            return Resp(404, {})
        return Resp(200, {"namespaces": [[n] for n in self.tree]})

    def list_tables(self, cat, ns):
        return Resp(
            200, {"identifiers": [{"name": t} for t in self.tree.get(ns, ([], []))[0]]}
        )

    def list_views(self, cat, ns):
        return Resp(
            200, {"identifiers": [{"name": v} for v in self.tree.get(ns, ([], []))[1]]}
        )

    def drop_table(self, cat, ns, name, purge=False):
        self.dropped.append(("table", ns, name))
        return Resp(204)

    def drop_view(self, cat, ns, name):
        self.dropped.append(("view", ns, name))
        return Resp(204)

    def drop_namespace(self, cat, ns):
        self.dropped.append(("namespace", ns, None))
        return Resp(204)

    def create_namespace(self, cat, ns):
        self.created.append(("namespace", ns))
        return Resp(200)

    def create_table(self, cat, ns, payload):
        self.created.append(("table", payload.get("name")))
        return Resp(200)

    def namespace_exists(self, cat, ns):
        return Resp(200)

    def table_exists(self, cat, ns, t):
        return Resp(200)


def test_setup_grants_catalog_manage_content_because_creating_a_catalog_does_not():
    """`service_admin` covers CATALOG_CREATE at the ROOT container, but namespace
    and table work is CATALOG-scoped and authorizes against grant_records. Drop
    this grant and the fixture builds a catalog nobody can use."""
    fx = surf.ProbeFixture(prefix="apiprofileTEST")
    pc, ic = FakeCatalogs(), FakeTree()
    seen = []
    surf.setup_fixture(
        fx,
        pc,
        ic,
        "bucket",
        "http://minio",
        {"fields": []},
        payload_builder=lambda name, schema: {"name": name},
        ensure_catalog=lambda *a, **k: seen.append(a[1]),
        attempt=lambda call, what, res, exists=None: (True, call()),
        result=object(),
    )
    assert seen == [fx.cat], "the catalog is ensured, not bare-created"
    assert (fx.cat, "catalog_admin", "CATALOG_MANAGE_CONTENT") in pc.granted
    assert ("namespace", "probe_ns") in ic.created
    assert ("namespace", "probe_ns2") in ic.created
    assert ("table", "probe_tbl") in ic.created


def test_setup_raises_loudly_when_a_call_really_failed():
    """Lag is retried; a real failure must abort rather than leave a half fixture."""
    fx = surf.ProbeFixture(prefix="apiprofileTEST")
    with pytest.raises(AssertionError, match="grant CATALOG_MANAGE_CONTENT"):
        surf.setup_fixture(
            fx,
            FakeCatalogs(),
            FakeTree(),
            "b",
            "e",
            {},
            payload_builder=lambda n, s: {"name": n},
            ensure_catalog=lambda *a, **k: None,
            attempt=lambda call, what, res, exists=None: (False, Resp(500)),
            result=object(),
        )


def test_teardown_empties_the_catalog_from_the_leaves_up():
    """Polaris answers 400 on deleting a catalog that still holds namespaces, and
    purge does NOT cascade. Order here is the whole point."""
    fx = surf.ProbeFixture(prefix="apiprofileTEST")
    ic = FakeTree({"probe_ns": (["probe_tbl"], ["probe_view"]), "probe_ns2": ([], [])})
    pc = FakeCatalogs([fx.cat])
    out = surf.teardown_fixture(fx, pc, ic, sweep_stale=False)
    kinds = [k for k, _ns, _n in ic.dropped]
    assert kinds.index("table") < kinds.index("namespace")
    assert kinds.index("view") < kinds.index("namespace")
    assert pc.deleted == [fx.cat], "the catalog goes last"
    assert out["fixture"] == {"tables": 1, "views": 1, "namespaces": 2, "catalog": 204}


def test_teardown_sweeps_probe_catalogs_an_aborted_run_left_behind():
    """A run that dies during setup never reaches teardown and its catalog stays.
    Residue that routinely violates find_strays is residue that trains people to
    ignore the assertion."""
    fx = surf.ProbeFixture(prefix="apiprofile999")
    pc = FakeCatalogs([fx.cat, "apiprofile111_cat", "someone_elses_cat"])
    out = surf.teardown_fixture(fx, pc, FakeTree(), sweep_stale=True)
    assert set(out["swept"]) == {"apiprofile111_cat"}
    assert "someone_elses_cat" not in pc.deleted, "only this harness's own prefix"


def test_a_missing_catalog_is_reported_absent_not_treated_as_an_error():
    fx = surf.ProbeFixture(prefix="apiprofileTEST")
    ic = FakeTree(missing={fx.cat})
    out = surf.teardown_fixture(fx, FakeCatalogs(), ic, sweep_stale=False)
    assert out["fixture"]["catalog"] == "absent"
    assert ic.dropped == []


def test_the_fixture_hands_the_drive_clients_to_the_context_and_keeps_adm_apart():
    fx = surf.ProbeFixture(prefix="apiprofileTEST")
    ic, pc, adm = Recorder("ic"), Recorder("pc"), Forbidden()
    ctx = fx.context(ic, pc, adm, schema={"fields": []})
    assert ctx.ic is ic and ctx.pc is pc and ctx.adm is adm
    assert ctx.cat == fx.cat and ctx.tbl == "probe_tbl"
    #: and the operations built from it still never touch adm
    for op in surf.operations(ctx, lambda n, s: {"name": n}, lambda t, s: {}):
        if op.prepare:
            op.prepare(ctx)
        op.fn(ctx)


def test_the_summary_accounts_for_every_operation_not_just_the_tidy_ones():
    """The line "driven 43/43 permitted 2 refused 22 errors 0" omitted 19 ops.

    Every one of them a 404, and every one carrying statements the audit wants.
    A total that looks right while its composition is wrong is the same failure
    as the reconciliation that survived because two errors netted out.
    """
    res = surf.DriveResult()
    res.statuses = {"a": 200, "b": 403, "c": 404, "d": 500, "e": None}
    assert res.permitted == ["a"]
    assert res.refused == ["b"]
    assert set(res.other) == {"c", "d", "e"}, "404/500/None are none of the above"
    assert len(res.permitted) + len(res.refused) + len(res.other) == len(res.statuses)
    assert res.distribution[404] == 1


def test_a_none_status_counts_as_other_not_as_success():
    """A request whose status never came back is not a 2xx."""
    res = surf.DriveResult()
    res.statuses = {"x": None}
    assert res.permitted == [] and res.refused == []
    assert list(res.other) == ["x"]


def test_authorizing_a_role_on_the_fixture_grants_and_assigns_on_that_catalog():
    """The correction that made the authorized case mean something.

    A catalog-scoped principal holds owner_principal on its OWN catalog, and
    Polaris authorizes against grant_records for the TARGET catalog — so driven
    against the shared probe fixture it was refused on all 43 operations and
    produced a status distribution byte-identical to the zero-grant case.
    """
    fx = surf.ProbeFixture(prefix="apiprofileTEST")
    pc = FakeCatalogs()
    out = surf.authorize_on_fixture(
        fx, pc, "authz1_principal_role", privileges=["CATALOG_MANAGE_CONTENT", "X"]
    )
    assert out["catalog_role"] == "apiprofileTEST_shared"
    #: granted on the PROBE catalog, not on the principal's own
    assert all(c == fx.cat for c, _r, _p in pc.granted)
    assert out["granted"] == ["CATALOG_MANAGE_CONTENT", "X"]
    assert ("create_catalog_role", (fx.cat, "apiprofileTEST_shared"), {}) in [
        (m, a, k) for m, a, k in pc.calls
    ]


def test_a_refused_privilege_is_reported_not_swallowed():
    """Granting nothing and reporting success would send the operator to drive a
    case that is still refused everywhere — the exact failure this fixes."""

    class Refuses(FakeCatalogs):
        def grant_privilege(self, cat, role, priv):
            return Resp(403, text="nope")

    out = surf.authorize_on_fixture(
        surf.ProbeFixture(prefix="p"), Refuses(), "r", privileges=["A", "B"]
    )
    assert out["granted"] == []
    assert out["failed"] == {"A": 403, "B": 403}
