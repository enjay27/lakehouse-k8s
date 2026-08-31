"""Tests for `api_report` — the renderer half of the report contract.

The renderer and `query_profile.parse_api_statements` are two halves of one
contract: the sweep replays what the report records, so a format change on
either side breaks the other silently. The report would still look right — it
is markdown, it renders fine — and the worklist would just come out short.

So the central test here is a ROUND-TRIP, not a byte comparison: render records,
parse them back, and assert the same statements with the same parameters come
out. That is the property anything downstream depends on, and it is the one a
golden-file test would not actually check.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
import api_report as rep  # noqa: E402
import query_profile as qp  # noqa: E402


class Stmt:
    def __init__(self, seq, table, verb, sql, params=None, duration_ms=None):
        self.seq, self.table, self.verb = seq, table, verb
        self.sql, self.params, self.duration_ms = sql, params, duration_ms


class RecObj:
    def __init__(self, api, method, path, status, sql=(), tables=(), minio=()):
        self.api, self.method, self.path, self.status = api, method, path, status
        self.sql = list(sql)
        self.tables_touched = list(tables)
        self.minio = list(minio)
        self.wall_ms = 12.0
        self.sql_count = len(self.sql)
        self.minio_count = len(self.minio)
        self.cache_shape = "MISS"
        self.batched_share = None
        self.entity_access = {"entity_reads": 0}


SEL = "SELECT id, name\nFROM POLARIS_SCHEMA.ENTITIES\nWHERE realm_id = ? AND id = ?"
INS = "INSERT INTO POLARIS_SCHEMA.ENTITIES (id) VALUES (?)"


def _records():
    return [
        RecObj(
            "mgmt.get_principal",
            "GET",
            "/v1/principals/{p}",
            200,
            sql=[
                Stmt(0, "entities", "SELECT", SEL, "POLARIS, 1002", 0.06),
                Stmt(1, "grant_records", "SELECT", SEL, "POLARIS, 7", 1.5),
            ],
            tables=["entities", "grant_records"],
        ),
        RecObj(
            "iceberg.create_table",
            "POST",
            "/v1/{cat}/namespaces/{ns}/tables",
            200,
            sql=[
                Stmt(0, "entities", "INSERT", INS, "9085954845997121812"),
                Stmt(1, None, "SET", "SET synchronous_commit TO 'local'"),
            ],
            tables=["entities"],
        ),
    ]


def test_render_then_parse_returns_the_same_statements():
    """THE contract. A format drift on either side shows up here and nowhere else."""
    text = rep.render_matrix_report(_records(), {}, case="admin")
    r = qp.parse_api_statements(text)
    assert r.clean, f"{r.unparsed} blocks failed to parse"
    assert set(r.apis) == {"mgmt.get_principal", "iceberg.create_table"}
    assert r.instances == 4
    by_sql = {p.sql.strip(): p for p in r.pairs}
    assert set(by_sql) == {SEL, INS, "SET synchronous_commit TO 'local'"}
    #: the same SQL under two different parameter sets stays two pairs
    assert len([p for p in r.pairs if p.sql.strip() == SEL]) == 2


def test_a_multiline_statement_survives_the_round_trip_whole():
    """The fenced block exists because a markdown CELL cannot hold a newline.
    The table version cut statements at 180 chars and removed the WHERE clause
    from exactly the long ones worth reading."""
    text = rep.render_matrix_report(_records(), {})
    (pair,) = [
        p for p in qp.parse_api_statements(text).pairs if p.params == "POLARIS, 1002"
    ]
    assert pair.sql.strip() == SEL
    assert "WHERE realm_id = ? AND id = ?" in pair.sql
    assert pair.sql.count("\n") == 2, "newlines preserved, not flattened"


def test_a_statement_that_bound_nothing_gets_no_params_line_and_refuses():
    text = rep.render_matrix_report(_records(), {})
    assert "SET synchronous_commit" in text
    r = qp.parse_api_statements(text)
    (setter,) = [p for p in r.pairs if p.verb == "SET"]
    assert setter.params == ""
    assert not setter.replayable
    assert setter.table == rep.DASH, "an unattributed table renders as a dash"
    assert r.clean, "no params is not a parse fault"


def test_redacted_params_pass_through_and_are_not_replayable():
    recs = [
        RecObj(
            "mgmt.create_principal",
            "POST",
            "/v1/principals",
            200,
            sql=[Stmt(0, "principal_authentication_data", "INSERT", INS, qp.REDACTED)],
            tables=["principal_authentication_data"],
        )
    ]
    text = rep.render_matrix_report(recs, {})
    (pair,) = qp.parse_api_statements(text).pairs
    assert pair.params == qp.REDACTED
    assert not pair.replayable


def test_the_identity_case_is_stated_in_the_report_header():
    """Three reports that differ only by caller would otherwise be
    indistinguishable, and a 403 column would not say whose authorization it
    describes."""
    text = rep.render_matrix_report(
        _records(), {}, case="unauthorized", identity="zerograve_principal"
    )
    assert "Identity case: `unauthorized`" in text
    assert "zerograve_principal" in text
    assert "403 here is a measurement, not a gap" in text


def test_the_measured_volume_is_stamped_on_the_report():
    text = rep.render_matrix_report(_records(), {}, volume={"grant_records": 60784})
    assert "`grant_records` 60,784" in text


def test_the_table_matrix_renders_a_dot_for_untouched_tables():
    matrix = {
        "mgmt.get_principal": {"entities": "R", "grant_records": "R"},
        "iceberg.create_table": {"entities": "RW"},
    }
    text = rep.render_matrix_report(_records(), matrix)
    assert "| `iceberg.create_table` | RW | · |" in text


def test_write_report_can_refuse_to_touch_latest(tmp_path):
    """Only `doc-*-latest.md` is tracked by reports/.gitignore, so refreshing it
    replaces the only version-controlled copy of the previous report."""
    p = rep.write_report(tmp_path, "doc-api-sql-matrix", "x", stamp="S", latest=False)
    assert p.name == "doc-api-sql-matrix-S.md"
    assert not (tmp_path / "doc-api-sql-matrix-latest.md").exists()
    rep.write_report(tmp_path, "doc-api-sql-matrix", "y", stamp="T")
    assert (tmp_path / "doc-api-sql-matrix-latest.md").read_text() == "y"
    assert (
        tmp_path / "doc-api-sql-matrix-S.md"
    ).read_text() == "x", "never overwritten"
