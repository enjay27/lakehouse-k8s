"""
Pytest suite for src/privilege_scan.py.

Runs the scan against a stateful in-memory fake — a fake metastore cursor and a
fake Polaris that models the two things that actually bite here: a non-root
principal only sees its OWN catalog, and a token requested at the wrong scope
comes back 200 and then 403s on every call.

Run: pytest test_privilege_scan.py
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent / "src"))
from privilege_scan import authenticate  # noqa: E402
from privilege_scan import (
    Identity,
    OpStatus,
    authorized_ops,
    capture_snapshot,
    capture_verdict,
    drive,
    load_identities,
    probe_surface,
    render_probe_table,
    render_scan_report,
    resolve_namespace,
    status_matrix,
    tail_lines,
)

REALM = "POLARIS"
SCHEMA = "polaris_schema"
SECRET = "user_secret"


class Resp:
    def __init__(self, status=200, body=None, text=None):
        self.status_code = status
        self._body = body if body is not None else {}
        self.text = text if text is not None else "{}"

    def json(self):
        return self._body


# ----------------------------------------------------------------------
# fake metastore
# ----------------------------------------------------------------------
class FakeCursor:
    def __init__(self, db):
        self.db = db
        self._rows = []

    def execute(self, sql, params):
        if "principal_authentication_data" in sql:
            self._rows = [(pid, cid) for pid, cid in self.db["auth"].items()]
        else:
            _realm, types, like = params
            prefix = like.rstrip("%")
            self._rows = [
                (i, n, t)
                for (i, n, t) in self.db["entities"]
                if t in types and n.startswith(prefix)
            ]

    def fetchall(self):
        return list(self._rows)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class FakeConn:
    def __init__(self, db):
        self.db = db

    def cursor(self):
        return FakeCursor(self.db)


def metastore(n_users=3, missing_credential=(), missing_catalog=()):
    """A seeded realm as rows: principals, catalogs, credential entries."""
    entities, auth = [], {}
    # Bootstrap rows that must NOT be mistaken for seeded users.
    entities += [(1, "root", 2), (2, "service_admin", 3)]
    for i in range(1, n_users + 1):
        pid = 100 + i
        entities.append((pid, f"user{i}_principal", 2))
        if i not in missing_catalog:
            entities.append((200 + i, f"user{i}_catalog", 4))
        if i not in missing_credential:
            auth[pid] = f"user{i}_client"
    return FakeConn({"entities": entities, "auth": auth})


# ----------------------------------------------------------------------
# fake Polaris
# ----------------------------------------------------------------------
class FakePolaris:
    """Models scope-dependent authorization, which is the trap under test."""

    def __init__(self, world):
        self.world = world
        self.token = None
        self.calls = []

    # -- auth ----------------------------------------------------------
    def get_token(self, client_id, secret, scope="PRINCIPAL_ROLE:ALL"):
        self.calls.append(("get_token", client_id, scope))
        if client_id not in self.world["clients"]:
            return Resp(401, text="unknown client")
        if secret != self.world["secret"]:
            return Resp(401, text="bad secret")
        # A wrong scope is NOT refused -- it yields a token with no role, which
        # is the whole reason `authenticate` defaults to the specific role.
        role = self.world["clients"][client_id]
        effective = role if scope == f"PRINCIPAL_ROLE:{role}" else None
        return Resp(200, {"access_token": f"tok:{client_id}:{effective}"})

    def _role(self):
        if not self.token:
            return None
        role = self.token.rsplit(":", 1)[-1]
        return None if role == "None" else role

    def _owns(self, catalog):
        role = self._role()
        return role is not None and self.world["owns"].get(role) == catalog

    # -- the GET surface ----------------------------------------------
    def list_principals(self):
        return Resp(403, text="service scoped")

    def list_principal_roles(self):
        return Resp(403, text="service scoped")

    def list_catalogs(self):
        return Resp(403, text="service scoped")

    def get_catalog(self, name):
        return Resp(200, {"name": name}) if self._owns(name) else Resp(403)

    def list_catalog_roles(self, catalog):
        return Resp(200, {"roles": []}) if self._owns(catalog) else Resp(403)

    def list_grants(self, catalog, role):
        return Resp(200, {"grants": []}) if self._owns(catalog) else Resp(403)

    def list_namespaces(self, catalog):
        if not self._owns(catalog):
            return Resp(403)
        return Resp(200, {"namespaces": self.world["namespaces"].get(catalog, [])})

    def get_namespace(self, catalog, ns):
        return Resp(200, {"namespace": [ns]}) if self._owns(catalog) else Resp(403)

    def list_tables(self, catalog, ns):
        return Resp(200, {"identifiers": []}) if self._owns(catalog) else Resp(403)


def world(n_users=3, namespaces=None):
    clients, owns, ns = {}, {}, {}
    for i in range(1, n_users + 1):
        role = f"user{i}_principal_role"
        clients[f"user{i}_client"] = role
        owns[role] = f"user{i}_catalog"
        ns[f"user{i}_catalog"] = (
            namespaces if namespaces is not None else [["ns1"], ["ns2"]]
        )
    return {"clients": clients, "secret": SECRET, "owns": owns, "namespaces": ns}


def ops_for_fixture(fx):
    """A small stand-in for `api_sweep.read_operations`: 3 allowed, 2 refused."""
    c, ns = fx["catalog"], fx["namespace"]
    return [
        ("GET  /principals", "mgmt", lambda pc: pc.list_principals()),
        ("GET  /catalogs", "mgmt", lambda pc: pc.list_catalogs()),
        ("GET  /catalogs/{name}", "mgmt", lambda pc: pc.get_catalog(c)),
        ("GET  /namespaces", "iceberg", lambda pc: pc.list_namespaces(c)),
        ("GET  /namespaces/{ns}", "iceberg", lambda pc: pc.get_namespace(c, ns)),
    ]


@pytest.fixture
def ident():
    return Identity(
        index=1,
        principal="user1_principal",
        principal_role="user1_principal_role",
        client_id="user1_client",
        catalog="user1_catalog",
        namespace="ns1",
    )


# ----------------------------------------------------------------------
# load_identities
# ----------------------------------------------------------------------
def test_client_ids_come_from_the_metastore_not_a_format_string():
    conn = metastore(3)
    identities, problems = load_identities(conn, SCHEMA, REALM)

    assert [i.index for i in identities] == [1, 2, 3]
    assert [i.client_id for i in identities] == [
        "user1_client",
        "user2_client",
        "user3_client",
    ]
    assert problems == {"no_credential": [], "no_catalog": []}


def test_bootstrap_principals_are_not_driven_as_seeded_users():
    """`root` and `service_admin` are type_code 2 too. They are not the fixture."""
    identities, _ = load_identities(metastore(2), SCHEMA, REALM)
    assert {i.principal for i in identities} == {"user1_principal", "user2_principal"}


def test_a_principal_without_credentials_is_reported_not_returned():
    identities, problems = load_identities(
        metastore(3, missing_credential={2}), SCHEMA, REALM
    )
    assert [i.index for i in identities] == [1, 3]
    assert problems["no_credential"] == ["user2_principal"]


def test_a_principal_without_its_catalog_is_reported_not_returned():
    identities, problems = load_identities(
        metastore(3, missing_catalog={3}), SCHEMA, REALM
    )
    assert [i.index for i in identities] == [1, 2]
    assert problems["no_catalog"] == ["user3_principal"]


def test_limit_stops_early_for_a_trial_run():
    identities, _ = load_identities(metastore(10), SCHEMA, REALM, limit=4)
    assert len(identities) == 4


# ----------------------------------------------------------------------
# authenticate -- the scope trap
# ----------------------------------------------------------------------
def test_default_scope_is_the_identitys_own_principal_role(ident):
    pc = FakePolaris(world())
    token, scope, detail = authenticate(pc, ident, SECRET)

    assert scope == "PRINCIPAL_ROLE:user1_principal_role"
    assert token == "tok:user1_client:user1_principal_role"
    assert detail == ""


def test_principal_role_all_yields_a_token_that_authorizes_nothing(ident):
    """The measured trap: 200 + a token, then 403 on every call.

    Pinned so nobody 'simplifies' the default scope back to ALL and reads the
    resulting wall of 403s as an authorization finding.
    """
    pc = FakePolaris(world())
    token, _scope, _d = authenticate(pc, ident, SECRET, scope="PRINCIPAL_ROLE:ALL")
    assert token is not None  # the exchange SUCCEEDS

    pc.token = token
    assert pc.get_catalog("user1_catalog").status_code == 403


def test_a_wrong_shared_secret_is_reported_not_raised(ident):
    pc = FakePolaris(world())
    token, _scope, detail = authenticate(pc, ident, "not-the-secret")
    assert token is None
    assert "401" in detail


# ----------------------------------------------------------------------
# namespace resolution
# ----------------------------------------------------------------------
def test_namespace_is_resolved_from_the_api_not_assumed(ident):
    pc = FakePolaris(world())
    pc.token = f"tok:user1_client:{ident.principal_role}"
    name, detail = resolve_namespace(pc, ident)
    assert (name, detail) == ("ns1", "")


def test_a_catalog_with_no_namespaces_is_a_reason_not_a_crash(ident):
    pc = FakePolaris(world(namespaces=[]))
    pc.token = f"tok:user1_client:{ident.principal_role}"
    name, detail = resolve_namespace(pc, ident)
    assert name is None and "no namespaces" in detail


# ----------------------------------------------------------------------
# the pre-flight probe
# ----------------------------------------------------------------------
def test_probe_records_refusals_as_data(ident):
    pc = FakePolaris(world())
    pc.token = f"tok:user1_client:{ident.principal_role}"
    ops = ops_for_fixture(ident.fixture())

    statuses = probe_surface(pc, ident, ops)
    assert [s.status for s in statuses] == [403, 403, 200, 200, 200]

    allowed = authorized_ops(ops, statuses)
    assert [label for label, _s, _f in allowed] == [
        "GET  /catalogs/{name}",
        "GET  /namespaces",
        "GET  /namespaces/{ns}",
    ]


def test_probe_survives_a_raising_client(ident):
    class Boom(FakePolaris):
        def get_catalog(self, name):
            raise ConnectionError("reset by peer")

    pc = Boom(world())
    pc.token = f"tok:user1_client:{ident.principal_role}"
    statuses = probe_surface(pc, ident, ops_for_fixture(ident.fixture()))
    bad = [s for s in statuses if s.status == 0]
    assert len(bad) == 1 and "ConnectionError" in bad[0].detail


def test_probe_table_names_the_refusals():
    """The 403 is the measurement, so it has to be legible in the rendered row.

    THIS TEST WAS RED FOR TEN DAYS and the reason is worth keeping. It asserted
    `| NO |` and "1 of 2 GET operations are authorized" -- the vocabulary
    `render_probe_table` used before 2026-08-31, when `e20fb22` replaced a
    YES/NO column with `OpStatus.verdict` because YES/NO could not tell a
    refusal from a harness fault. The renderer was improved and its test was
    not, so the assertion went on describing a document nobody prints.
    """
    table = render_probe_table(
        [OpStatus("GET  /catalogs", "mgmt", 403), OpStatus("GET  /x", "mgmt", 200)]
    )
    assert "| refused |" in table
    assert "1 of 2 operations authorized, 1 refused." in table


def test_the_probe_table_summary_counts_every_verdict_it_rendered():
    """The summary line is the only place a reader sees the whole shape, and
    `e20fb22`'s point was that a refusal and a harness fault are DIFFERENT
    outcomes. A summary that folded them together would undo that while every
    row still looked right, so the counts are asserted apart from the rows.

    400 is `malformed`, not `refused`: measured 2026-08-31, `GET /v1/config`
    answered 400 because the harness sent no `warehouse` parameter. Filed as a
    refusal it read as "ordinary principals may not read the catalog config",
    which is a claim about Polaris drawn from a mistake of ours.
    """
    table = render_probe_table(
        [
            OpStatus("GET  /a", "mgmt", 200),
            OpStatus("GET  /b", "mgmt", 403),
            OpStatus("GET  /c", "cat", 400),
            OpStatus("GET  /d", "cat", OpStatus.UNDRIVEABLE),
        ]
    )
    assert "1 of 4 operations authorized" in table
    for verdict in ("refused", "malformed", "undriveable"):
        assert f", 1 {verdict}" in table, f"{verdict} is missing from the summary"
    # and the two that are NOT authorization outcomes explain themselves,
    # because a reader who treats them as refusals draws a false conclusion
    # about Polaris from a fault in the harness or the fixture.
    assert "**malformed**" in table and "**undriveable**" in table


# ----------------------------------------------------------------------
# the drive
# ----------------------------------------------------------------------
def _drive(conn_users=3, **kw):
    w = world(conn_users)
    identities, _ = load_identities(metastore(conn_users), SCHEMA, REALM)
    ops_by_identity = {}

    def ops_for(client, identity):
        ops = [
            o
            for o in ops_for_fixture(identity.fixture())
            if not o[0].endswith(("/principals", "/catalogs"))
        ]
        ops_by_identity[identity.index] = ops
        return ops

    result = drive(
        lambda: FakePolaris(w),
        identities,
        kw.pop("secret", SECRET),
        ops_for,
        **kw,
    )
    return result, identities, ops_by_identity


def test_every_identity_is_driven_through_its_own_ops():
    result, identities, _ = _drive(3)

    assert result.identities == 3
    assert result.authenticated == 3
    assert result.errors == []
    # 3 identities x (1 token + 1 namespace resolve + 3 ops)
    assert result.requests == 15
    for i in (1, 2, 3):
        assert result.statuses[(i, "GET  /catalogs/{name}")] == 200


def test_each_identity_drives_its_own_catalog_not_the_first_ones():
    """The bug this pins: reusing one fixture would measure user1 1,000 times."""
    result, identities, ops = _drive(3)
    assert identities[2].catalog == "user3_catalog"
    assert identities[2].namespace == "ns1"
    assert all(result.statuses[(i, "GET  /namespaces")] == 200 for i in (1, 2, 3))


def test_a_wrong_shared_secret_aborts_early_instead_of_failing_1000_times():
    result, _identities, _ops = _drive(10, secret="wrong", stop_after_auth_failures=3)
    assert len(result.auth_failures) == 3
    assert result.authenticated == 0
    assert len(result.skipped) == 7
    assert "aborted" in result.skipped[0][1]


def test_progress_is_reported():
    seen = []
    w = world(4)
    identities, _ = load_identities(metastore(4), SCHEMA, REALM)
    drive(
        lambda: FakePolaris(w),
        identities,
        SECRET,
        lambda c, i: [],
        on_progress=lambda d, t, r: seen.append((d, t)),
        progress_every=2,
    )
    assert seen == [(2, 4), (4, 4)]


# ----------------------------------------------------------------------
# reporting
# ----------------------------------------------------------------------
def test_the_namespace_resolve_call_is_recorded_under_its_own_label():
    """The capture holds 2x `GET /namespaces`; the run JSON must say why.

    An unexplained 2x on exactly one API, in a scan whose whole output is a
    per-API distribution, is the shape of a finding. Naming the resolve call
    accounts for it.
    """
    from privilege_scan import NS_RESOLVE_LABEL

    result, _identities, _ops = _drive(3)
    assert all(result.statuses[(i, NS_RESOLVE_LABEL)] == 200 for i in (1, 2, 3))
    assert all(result.statuses[(i, "GET  /namespaces")] == 200 for i in (1, 2, 3))


def test_a_tolerated_403_is_recorded_but_is_not_an_error():
    """Denied ops are driven ON PURPOSE: a 403 still pays the auth prelude.

    Polaris has to resolve the grants to decide the request is refused, so the
    grantee lookup fires on the denial path too. Driving a sample of refusals
    turns that from a claim read off the source into capture evidence -- but
    only if an expected 403 does not read as a broken pass.
    """
    w = world(2)
    identities, _ = load_identities(metastore(2), SCHEMA, REALM)
    denied = "GET  /catalogs"

    result = drive(
        lambda: FakePolaris(w),
        identities,
        SECRET,
        lambda c, i: [o for o in ops_for_fixture(i.fixture()) if o[0] == denied],
        tolerated_labels={denied},
    )
    assert result.statuses[(1, denied)] == 403
    assert result.errors == []


def test_an_untolerated_403_is_still_an_error():
    w = world(2)
    identities, _ = load_identities(metastore(2), SCHEMA, REALM)
    denied = "GET  /catalogs"

    result = drive(
        lambda: FakePolaris(w),
        identities,
        SECRET,
        lambda c, i: [o for o in ops_for_fixture(i.fixture()) if o[0] == denied],
    )
    assert [e[2] for e in result.errors] == [403, 403]


# ----------------------------------------------------------------------
# capture liveness -- the gate that would have saved the 2026-08-24 pass
# ----------------------------------------------------------------------
def _cap(polaris=0, pg0=0, pg1=0):
    return {"polaris.log": polaris, "pg-0.log": pg0, "pg-1.log": pg1}


def test_a_live_capture_passes():
    ok, reasons = capture_verdict(
        _cap(100, 100, 100),
        _cap(900, 800, 700),
        polaris_tail="... DatasourceOperations ... SELECT ...",
        pg_tail="LOG:  statement: SELECT 1",
    )
    assert ok and reasons == []


def test_a_dead_polaris_stream_is_named_as_a_dead_stream():
    """The real 2026-08-24 fault: 410 bytes, one 'server stopped' line."""
    ok, reasons = capture_verdict(
        _cap(410, 100, 100),
        _cap(410, 800, 700),
        polaris_tail="Apache Polaris Server (incubating) stopped in 0.143s",
        pg_tail="LOG:  statement: SELECT 1",
    )
    assert not ok
    assert "did not grow" in reasons[0] and "restarted" in reasons[0]


def test_checkpoint_chatter_is_not_statement_evidence():
    """The other half of the real fault: pg logging on, statements off.

    A pg log full of checkpoints has a growing size and a recent mtime and
    contains nothing the audit can use.
    """
    ok, reasons = capture_verdict(
        _cap(100, 100, 100),
        _cap(900, 800, 700),
        polaris_tail="DatasourceOperations",
        pg_tail="LOG:  restartpoint starting: time\nLOG:  checkpoint complete:",
    )
    assert not ok
    assert any("log_statement" in r and "pgon" in r for r in reasons)


def test_polaris_logging_without_the_sql_logger_is_its_own_fault():
    ok, reasons = capture_verdict(
        _cap(100, 100, 100),
        _cap(900, 800, 700),
        polaris_tail="INFO some unrelated line",
        pg_tail="LOG:  statement: SELECT 1",
    )
    assert not ok
    assert any("above DEBUG" in r for r in reasons)


def test_an_empty_capture_directory_says_so_once():
    ok, reasons = capture_verdict({}, {}, "", "")
    assert not ok and len(reasons) == 1 and "no .log files" in reasons[0]


def test_one_giant_line_cannot_swallow_the_liveness_window(tmp_path):
    """The 2026-09-02 fault, reproduced at 1/10 scale.

    Nineteen real `DatasourceOperations` lines, then ONE line far longer than
    any character window a gate would take. A character tail sees only the
    giant line; a LINE tail still sees the nineteen. This is exactly the shape
    of `capture-admin-latest/polaris.log`: 25 lines, one of them 1,292,023
    bytes, 19 statements the gate reported as zero.
    """
    log = tmp_path / "polaris.log"
    body = "".join(
        f"line {i} DatasourceOperations query: SELECT {i}\n" for i in range(19)
    )
    log.write_text(
        body + "PolarisServiceImpl listCatalogs returning: " + ("x" * 200_000) + "\n",
        encoding="utf-8",
    )

    char_window = log.read_text(encoding="utf-8")[-40_000:]
    assert (
        char_window.count("DatasourceOperations") == 0
    ), "the character window is supposed to fail here — that is the bug"

    line_window = tail_lines(log, n=800)
    assert line_window.count("DatasourceOperations") == 19


def test_tail_lines_truncates_rather_than_holding_a_pathological_line(tmp_path):
    log = tmp_path / "polaris.log"
    log.write_text("DatasourceOperations " + ("y" * 100_000) + "\n", encoding="utf-8")
    out = tail_lines(log, n=10, max_line=64)
    assert len(out) <= 64
    assert "DatasourceOperations" in out  # the marker survives truncation


def test_tail_lines_keeps_only_the_last_n_lines_oldest_first(tmp_path):
    log = tmp_path / "polaris.log"
    log.write_text("".join(f"{i}\n" for i in range(10)), encoding="utf-8")
    assert tail_lines(log, n=3) == "7\n8\n9"


def test_tail_lines_on_a_missing_file_is_empty_not_an_error(tmp_path):
    assert tail_lines(tmp_path / "nope.log") == ""


def test_snapshot_measures_bytes_not_mtime(tmp_path):
    (tmp_path / "polaris.log").write_text("abc", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("ignored", encoding="utf-8")
    assert capture_snapshot(str(tmp_path)) == {"polaris.log": 3}
    assert capture_snapshot(str(tmp_path / "nope")) == {}


def test_status_matrix_counts_every_call_per_api():
    result, _identities, ops = _drive(3)
    matrix = status_matrix(result, ops[1])
    assert matrix["GET  /namespaces"] == {200: 3}


def test_report_leads_with_what_did_not_work():
    result, _identities, ops = _drive(10, secret="wrong", stop_after_auth_failures=2)
    text = render_scan_report(result, ops.get(1, []))
    assert "never authenticated" in text
    assert "identities skipped" in text
