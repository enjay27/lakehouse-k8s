"""Tests for `query_profile` — post-hoc correlation of a privilege-scan capture.

The fakes here are hostile in the three places this module can fail SILENTLY,
because every one of those failures produces a plausible-looking report rather
than an exception:

  * a statement with no access-log line — dropping it shrinks the denominator;
  * a path the op templates do not match — folding it into a real op inflates
    one API's statement count;
  * a chunk boundary landing mid-line — losing a line from a 120 MB file that
    nobody will ever diff by hand.

So the chunk size is set absurdly small on purpose, the fixture log carries an
orphan and an unclassified request, and the reconciliation case asserts the
delta rather than just the totals.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import api_sweep as sweep  # noqa: E402
import query_profile as qp  # noqa: E402

ACC = qp.ACCESS_LOGGER
DSO = "org.apache.polaris.persistence.relational.jdbc.DatasourceOperations"

#: The real `DatasourceOperations.logQuery` shape, taken from
#: capture-scan-noindex-2: `query: <sql>` then each bound parameter on its own
#: indented line. NOT `; parameters: ...` — an earlier draft of these fixtures
#: invented that separator and the parser dutifully left it inside the SQL.
GRANTS_SQL = (
    "SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, "
    "privilege_code FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND "
    "realm_id = ? AND grantee_catalog_id = ?"
)
ENTITY_SQL = (
    "SELECT id, catalog_id, name FROM POLARIS_SCHEMA.ENTITIES "
    "WHERE realm_id = ? AND catalog_id = ? AND id = ?"
)
AUTH_SQL = (
    "SELECT principal_id, principal_client_id, main_secret_hash, secret_salt "
    "FROM POLARIS_SCHEMA.PRINCIPAL_AUTHENTICATION_DATA "
    "WHERE realm_id = ? AND principal_client_id = ?"
)


def query(sql, *params):
    return "query: " + sql + "".join(f"\n    {p}" for p in params)


def jline(logger, message, rid, ts="2026-08-24T03:31:47.000000000Z"):
    return json.dumps(
        {
            "timestamp": ts,
            "loggerName": logger,
            "level": "DEBUG",
            "message": message,
            "mdc": {"requestId": rid, "realmId": "POLARIS"},
        }
    )


def access(
    method, path, status, rid, principal="user7_principal", nbytes="41", ts=None
):
    msg = (
        f"192.168.194.1 - {principal} [24/Aug/2026:03:31:47 +0000] "
        f'"{method} {path} HTTP/1.1" {status} {nbytes}'
    )
    return jline(ACC, msg, rid, ts or "2026-08-24T03:31:47.900000000Z")


@pytest.fixture
def capture(tmp_path):
    """One permitted request, one refused, a token call, an orphan, a health probe."""
    lines = [
        jline(DSO, query(AUTH_SQL, "POLARIS", "user7_client"), "r-200"),
        jline(DSO, query(GRANTS_SQL, "1001", "POLARIS", "1002"), "r-200"),
        jline(DSO, query(GRANTS_SQL, "1001", "POLARIS", "1002"), "r-200"),
        jline(DSO, query(ENTITY_SQL, "POLARIS", "1002", "1003"), "r-200"),
        access(
            "GET",
            "/api/catalog/v1/user7_catalog/namespaces/ns1/views",
            200,
            "r-200",
        ),
        jline(DSO, query(GRANTS_SQL, "1001", "POLARIS", "1002"), "r-403"),
        jline(DSO, query(GRANTS_SQL, "1001", "POLARIS", "1002"), "r-403"),
        access("GET", "/api/management/v1/principals", 403, "r-403", nbytes="78"),
        access(
            "POST",
            "/api/catalog/v1/oauth/tokens",
            200,
            "r-tok",
            principal="-",
            nbytes="-",
        ),
        jline(DSO, query(GRANTS_SQL, "9", "POLARIS", "9"), "r-orphan"),
        access("GET", "/q/health", 200, "r-health", principal="-", nbytes="12"),
    ]
    p = tmp_path / "polaris.log"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


# ----------------------------------------------------------------------
# streaming
# ----------------------------------------------------------------------
def test_chunks_never_split_a_line(tmp_path):
    p = tmp_path / "big.log"
    p.write_text("".join(f"line-{i}\n" for i in range(500)), encoding="utf-8")
    chunks = list(qp.iter_log_chunks(str(p), chunk_bytes=7))
    assert len(chunks) > 1, "chunk size too large to exercise the splitter"
    assert all(c.endswith("\n") for c in chunks)
    assert "".join(chunks) == p.read_text()


def test_chunks_yield_a_trailing_line_without_newline(tmp_path):
    p = tmp_path / "nonl.log"
    p.write_text("a\nb\nc", encoding="utf-8")
    assert "".join(qp.iter_log_chunks(str(p), chunk_bytes=2)) == "a\nb\nc"


# ----------------------------------------------------------------------
# the access log
# ----------------------------------------------------------------------
def test_access_line_parses_every_field():
    (rec,) = qp.parse_access_log(
        access("GET", "/api/management/v1/catalogs/c1", 200, "r-1")
    )
    assert rec.request_id == "r-1"
    assert rec.principal == "user7_principal"
    assert rec.method == "GET"
    assert rec.path == "/api/management/v1/catalogs/c1"
    assert rec.status == 200
    assert rec.ok


def test_access_line_survives_dash_bytes_and_anonymous_principal():
    (rec,) = qp.parse_access_log(
        access(
            "POST", "/api/catalog/v1/oauth/tokens", 200, "r", principal="-", nbytes="-"
        )
    )
    assert rec.bytes == 0 and rec.principal == "-"


def test_access_query_string_is_split_off():
    (rec,) = qp.parse_access_log(
        access("GET", "/api/catalog/v1/c/namespaces?parent=a", 200, "r")
    )
    assert rec.path == "/api/catalog/v1/c/namespaces"
    assert rec.query == "parent=a"


def test_non_access_loggers_are_ignored():
    assert qp.parse_access_log(jline(DSO, query(GRANTS_SQL, "1"), "r")) == []


def test_access_record_without_request_id_is_dropped():
    line = json.dumps(
        {
            "loggerName": ACC,
            "message": '1.2.3.4 - - [24/Aug/2026:03:31:47 +0000] "GET /x HTTP/1.1" 200 1',
            "mdc": {},
        }
    )
    assert qp.parse_access_log(line) == []


# ----------------------------------------------------------------------
# op templates — derived from api_sweep + polaris_rest, not transcribed
# ----------------------------------------------------------------------
def test_every_read_operation_gets_a_template():
    templates = qp.operation_templates()
    labels = {t.label for t in templates}
    for label, _surface, _fn in sweep.read_operations(qp._SENTINELS):
        assert label in labels, f"{label} has no URL template"
    assert "POST /oauth/tokens" in labels


def test_no_sentinel_survives_into_a_template():
    for t in qp.operation_templates():
        for token in qp._SENTINELS.values():
            assert token not in t.template, f"{t.label} kept the sentinel {token}"


def test_every_op_label_round_trips_through_a_concrete_path():
    """The report's labels must be the run JSON's labels, for all 14.

    A label that does not round-trip shows up in the report as an
    "unclassified path" — i.e. as a fixture fault, when it is a bug here.
    """
    templates = qp.operation_templates()
    real = {
        "catalog": "user7_catalog",
        "namespace": "ns1",
        "principal": "user7_principal",
        "principal_role": "user7_principal_role",
        "catalog_role": "owner_principal",
    }
    for t in templates:
        concrete = t.template
        for name, value in real.items():
            concrete = concrete.replace("{" + name + "}", value)
        label, surface, ents = qp.classify(t.method, concrete, templates)
        assert label == t.label, f"{concrete} classified as {label!r}"
        for name, value in ents.items():
            assert value == real[name]


def test_collection_and_item_paths_do_not_collide():
    templates = qp.operation_templates()
    assert qp.classify("GET", "/api/management/v1/catalogs", templates)[0] == (
        "GET  /catalogs"
    )
    assert qp.classify("GET", "/api/management/v1/catalogs/c1", templates)[0] == (
        "GET  /catalogs/{name}"
    )


def test_method_is_part_of_the_match():
    templates = qp.operation_templates()
    assert qp.classify("DELETE", "/api/management/v1/catalogs", templates)[0] is None


def test_unknown_path_is_unclassified_not_guessed():
    assert qp.classify("GET", "/q/health", qp.operation_templates())[0] is None


# ----------------------------------------------------------------------
# the join
# ----------------------------------------------------------------------
def test_statements_attach_to_their_request(capture):
    corr = qp.correlate(str(capture), chunk_bytes=64)
    by_rid = {p.request_id: p for p in corr.profiles}
    assert by_rid["r-200"].n_statements == 4
    assert by_rid["r-403"].n_statements == 2
    assert by_rid["r-tok"].n_statements == 0


def test_orphan_statements_are_counted_not_dropped(capture):
    corr = qp.correlate(str(capture), chunk_bytes=64)
    assert corr.orphan_statements == 1
    assert "r-orphan" in corr.orphan_request_ids
    assert sum(p.n_statements for p in corr.profiles) + corr.orphan_statements == (
        corr.statements
    )


def test_unclassified_request_keeps_its_raw_path(capture):
    corr = qp.correlate(str(capture), chunk_bytes=64)
    assert corr.unclassified_paths == {"GET /q/health": 1}
    (health,) = [p for p in corr.profiles if p.request_id == "r-health"]
    assert health.surface == "unclassified"
    assert health.label == "GET /q/health"


def test_tiny_chunks_give_the_same_result_as_one_big_one(capture):
    small = qp.correlate(str(capture), chunk_bytes=16)
    big = qp.correlate(str(capture), chunk_bytes=1 << 20)
    assert small.statements == big.statements
    assert small.access_records == big.access_records
    assert [p.n_statements for p in small.profiles] == [
        p.n_statements for p in big.profiles
    ]


# ----------------------------------------------------------------------
# profiling
# ----------------------------------------------------------------------
def test_statement_profile_groups_by_normalised_sql(capture):
    corr = qp.correlate(str(capture), chunk_bytes=64)
    shapes = qp.statement_profile(corr.profiles)
    grants = next(s for s in shapes.values() if s.table == "grant_records")
    assert grants.occurrences == 4  # 2 permitted + 2 refused; the orphan is excluded
    assert grants.requests == 2
    assert grants.per_request == 2.0


def test_secret_table_params_are_flagged_unreplayable(capture):
    """§3.4: the auth lookup cannot be EXPLAINed with observed parameters.

    `redact_params` blanks the whole set for a SECRET_TABLES statement, so the
    report has to SAY the parameters were reconstructed rather than quietly
    substitute one.
    """
    corr = qp.correlate(str(capture), chunk_bytes=64)
    shapes = qp.statement_profile(corr.profiles)
    auth = next(
        s for s in shapes.values() if s.table == "principal_authentication_data"
    )
    assert not auth.params_observed
    grants = next(s for s in shapes.values() if s.table == "grant_records")
    assert grants.params_observed


def test_prelude_split_separates_permitted_refused_and_probes(capture):
    corr = qp.correlate(str(capture), chunk_bytes=64)
    classes, diff = qp.prelude_by_outcome(corr)
    assert classes["permitted (2xx)"]["requests"] == 1
    assert classes["permitted (2xx)"]["per_request"] == 4.0
    assert classes["refused (403)"]["requests"] == 1
    assert classes["refused (403)"]["per_request"] == 2.0
    assert classes["auth (token)"]["requests"] == 1
    #: The health probe answers 200 and issues no SQL. Folded into "permitted"
    #: it would halve that class's mean — a prelude made to look cheaper than
    #: it is, by a request that is not an API call at all.
    assert classes["unclassified (not an op)"]["requests"] == 1
    assert classes["unclassified (not an op)"]["per_request"] == 0.0


def test_prelude_diff_names_the_shapes_unique_to_each_path(capture):
    corr = qp.correlate(str(capture), chunk_bytes=64)
    _classes, diff = qp.prelude_by_outcome(corr)
    assert any("ENTITIES" in s for s in diff["only_permitted"])
    assert any("GRANT_RECORDS" in s for s in diff["shared"])
    assert diff["only_refused"] == []


def test_explain_worklist_is_frequency_ordered_and_filterable(capture):
    corr = qp.correlate(str(capture), chunk_bytes=64)
    shapes = qp.statement_profile(corr.profiles)
    work = qp.explain_worklist(shapes)
    assert work[0].table == "grant_records"
    assert [s.table for s in qp.explain_worklist(shapes, table="entities")] == (
        ["entities"]
    )


# ----------------------------------------------------------------------
# windowing
# ----------------------------------------------------------------------
def test_pg_window_excludes_traffic_after_the_drive():
    text = (
        "2026-08-24 03:31:47.500 GMT [258] LOG:  statement: SELECT 1\n"
        "2026-08-24 05:15:00.000 GMT [259] LOG:  statement: SELECT 2\n"
    )
    kept = qp.window_pg_text(text, "2026-08-24T03:31:00Z", "2026-08-24T03:35:00Z")
    assert "SELECT 1" in kept and "SELECT 2" not in kept


def test_pg_window_keeps_continuation_lines():
    """A wrapped statement's continuation carries no timestamp.

    Dropping it truncates the statement — the exact failure `parse_pg_log` was
    fixed for ("syntax error at end of input" on the grant_records OR-delete).
    """
    text = (
        "2026-08-24 03:31:47.500 GMT [258] LOG:  statement: DELETE FROM x WHERE (\n"
        "\ta = 1 AND b = 2)\n"
        "2026-08-24 05:15:00.000 GMT [259] LOG:  statement: SELECT 2\n"
        "\tOR c = 3\n"
    )
    kept = qp.window_pg_text(text, "2026-08-24T03:31:00Z", "2026-08-24T03:35:00Z")
    assert "a = 1 AND b = 2)" in kept
    assert "OR c = 3" not in kept, "a continuation of an EXCLUDED statement leaked in"


def test_iso_key_orders_both_log_formats_together():
    polaris = qp._iso_key("2026-08-24T03:31:47.981196241Z")
    postgres = qp._iso_key("2026-08-24 03:31:47.500 GMT")
    assert postgres < polaris


def test_profile_window_spans_first_to_last(capture):
    corr = qp.correlate(str(capture), chunk_bytes=64)
    first, last = qp.profile_window(corr.profiles)
    assert first <= last


# ----------------------------------------------------------------------
# reconciliation
# ----------------------------------------------------------------------
def test_ns_resolve_is_folded_into_the_op_it_duplicates():
    """The two labels are the SAME HTTP request and cannot be told apart.

    `privilege_scan` records them separately so the run JSON accounts for the
    2x. Reconciliation folds them back and says so; leaving them split would
    report a -1000 delta on an op that is not missing anything.
    """
    corr = qp.Correlation()
    corr.profiles = [
        qp.RequestProfile(
            "r%d" % i, "GET  /namespaces", "iceberg", "GET", "/p", "u", 200
        )
        for i in range(4)
    ]
    run = {
        "status_counts": {
            "GET  /namespaces": {"200": 2},
            "GET  /namespaces [ns-resolve]": {"200": 2},
        },
        "authenticated": 0,
    }
    rec = qp.reconcile(corr, run)
    (row,) = [r for r in rec["rows"] if r["label"] == "GET  /namespaces"]
    assert row["expected"] == 4 and row["observed"] == 4 and row["delta"] == 0
    assert row["folded"] is True
    assert rec["clean"]


def test_reconcile_reports_a_short_capture_rather_than_averaging_it_away():
    corr = qp.Correlation()
    corr.profiles = [
        qp.RequestProfile(
            "r%d" % i, "GET  /catalogs/{name}", "mgmt", "GET", "/p", "u", 200
        )
        for i in range(900)
    ]
    run = {
        "status_counts": {"GET  /catalogs/{name}": {"200": 1000}},
        "authenticated": 0,
    }
    rec = qp.reconcile(corr, run)
    assert rec["clean"] is False
    assert rec["delta_total"] == -100


def test_reconcile_counts_token_calls_from_authenticated():
    corr = qp.Correlation()
    corr.profiles = [
        qp.RequestProfile(
            "t%d" % i, "POST /oauth/tokens", "auth", "POST", "/p", "-", 200
        )
        for i in range(5)
    ]
    rec = qp.reconcile(corr, {"status_counts": {}, "authenticated": 5})
    assert rec["clean"]


# ----------------------------------------------------------------------
# rendering — the labels that stop a number being misquoted
# ----------------------------------------------------------------------
def test_outcome_render_states_the_no_short_circuit_conclusion_explicitly():
    corr = qp.Correlation()
    corr.profiles = [
        qp.RequestProfile("a", "GET  /catalogs/{name}", "mgmt", "GET", "/p", "u", 200),
        qp.RequestProfile("b", "GET  /principals", "mgmt", "GET", "/p", "u", 403),
    ]
    classes, diff = qp.prelude_by_outcome(corr)
    out = qp.render_outcome_split(classes, diff)
    assert "does not short-circuit" in out


def test_integrity_render_names_orphans_and_unclassified(capture):
    corr = qp.correlate(str(capture), chunk_bytes=64)
    out = qp.render_integrity(corr)
    assert "1 statements had no access-log line" in out
    assert "GET /q/health" in out


# ----------------------------------------------------------------------
# replay — the bugs the first --explain run found, at the cost of a whole pass
# ----------------------------------------------------------------------
def test_normalised_sql_is_never_what_gets_replayed(capture):
    """`sql` is a grouping key; `sample_sql` is the statement.

    `normalize_sql` collapses a row-constructor IN-list to `IN (<rows>)` so one
    statement can be counted across calls of differing arity. That string is
    not executable — EXPLAINing it fails with `syntax error at or near "<"`,
    which is exactly what the first --explain run did to 1 of its 8 statements.
    """
    corr = qp.correlate(str(capture), chunk_bytes=64)
    for s in qp.statement_profile(corr.profiles).values():
        assert s.sample_sql, "no raw representative kept"
        sql, _params = s.replay()
        if sql is not None:
            assert "<rows>" not in sql and "<list>" not in sql


def test_replay_converts_jdbc_placeholders():
    """`?` is a VALID operator character in PostgreSQL (jsonb `?`, `?|`, `?&`).

    So a statement sent with `?` intact does not fail at the placeholder — the
    parser reads `= ?` as an operator expression and reports `syntax error at
    or near "AND"`, pointing several tokens past the real cause. That
    misdirection is why the first --explain run's 7 failures read as a SQL
    problem rather than a driver-dialect one.
    """
    assert qp.to_psycopg("WHERE a = ? AND b = ?") == "WHERE a = %s AND b = %s"
    assert "?" not in qp.to_psycopg("SELECT x FROM t WHERE id = ?")


def test_replay_escapes_a_literal_percent():
    """psycopg2 treats `%` as its own introducer once parameters are passed."""
    assert qp.to_psycopg("WHERE name LIKE '100%' AND id = ?") == (
        "WHERE name LIKE '100%%' AND id = %s"
    )


def test_replay_placeholder_and_parameter_counts_must_agree():
    """A mismatched replay is worse than a refused one.

    `split_query_message` separates SQL from parameters BY the placeholder
    count, so a disagreement here means its fallback path ran and the split is
    not trustworthy. Refuse rather than send a statement bound to the wrong
    number of values.
    """
    sp = qp.StatementProfile(
        sql="k", table="t", verb="SELECT", occurrences=1, requests=1
    )
    sp.sample_sql = "SELECT 1 FROM t WHERE a = ? AND b = ?"
    sp.sample_params = "1"
    assert not sp.replayable
    assert sp.replay() == (None, None)
    sp.sample_params = "1, 2"
    assert sp.replayable
    assert sp.replay() == ("SELECT 1 FROM t WHERE a = %s AND b = %s", ("1", "2"))


def test_redacted_statement_is_not_replayable(capture):
    corr = qp.correlate(str(capture), chunk_bytes=64)
    shapes = qp.statement_profile(corr.profiles)
    auth = next(
        s for s in shapes.values() if s.table == "principal_authentication_data"
    )
    assert not auth.replayable and auth.replay() == (None, None)


def test_param_tuple_splits_on_the_joiner_split_query_message_uses(capture):
    corr = qp.correlate(str(capture), chunk_bytes=64)
    grants = next(
        s
        for s in qp.statement_profile(corr.profiles).values()
        if s.table == "grant_records"
    )
    assert qp.param_tuple(grants.sample_params) == ("1001", "POLARIS", "1002")


def test_every_capture_statement_except_the_secret_one_is_replayable(capture):
    corr = qp.correlate(str(capture), chunk_bytes=64)
    shapes = qp.statement_profile(corr.profiles)
    unreplayable = [s.table for s in shapes.values() if not s.replayable]
    assert unreplayable == ["principal_authentication_data"]
