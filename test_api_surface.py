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
    def __init__(self, status=200, payload=None):
        self.status_code = status
        self._payload = payload or {}

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
