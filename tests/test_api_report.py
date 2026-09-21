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


# ----------------------------------------------------------------------
# the empty-row fallback -- an empty statement list must explain itself
# ----------------------------------------------------------------------
class _Empty:
    """A record that captured nothing, with a raw window to explain it."""

    def __init__(self, raw=None):
        self.api = "iceberg.get_config"
        self.method, self.path, self.status = "GET", "/v1/config", 200
        self.sql = []
        self.minio = []
        self.raw_log = raw
        self.wall_ms = 12.0
        self.sql_count = 0
        self.minio_count = 0
        self.cache_shape = "n/a"
        self.tables_touched = []


def test_an_empty_row_that_recorded_nothing_says_the_stream_is_the_fault():
    out = "\n".join(rep.render_empty_window(_Empty(raw="")))
    assert "recorded NOTHING" in out
    assert "--capture" in out, "names the stale-directory trap"
    assert ".pids" in out, "names the dead-tail check"


def test_an_empty_row_with_output_but_no_sql_logger_lines_says_which_two_causes():
    raw = '{"loggerName":"io.quarkus.http.access-log","message":"GET /v1/config 400"}'
    out = "\n".join(rep.render_empty_window(_Empty(raw=raw)))
    assert "no DatasourceOperations lines" in out
    assert "preflight" in out
    assert raw in out, "the raw window is what settles it, so it must be shown"


def test_an_empty_row_whose_window_HAS_sql_lines_is_named_a_parser_fault():
    """The rarest of the three, and the only one where the raw text is the bug."""
    raw = '{"loggerName":"org.apache.polaris...DatasourceOperations","message":"query: SELECT 1"}'
    out = "\n".join(rep.render_empty_window(_Empty(raw=raw)))
    assert "PARSER fault" in out
    assert "require_logger" in out


def test_a_record_with_no_raw_window_says_so_rather_than_implying_silence():
    out = "\n".join(rep.render_empty_window(_Empty(raw=None)))
    assert "No raw window was retained" in out


def test_render_statements_falls_back_when_there_are_no_statements():
    """The fallback must be on the path the report actually uses."""
    out = "\n".join(rep.render_statements(_Empty(raw="")))
    assert "No SQL was captured" in out


def test_a_populated_record_is_unaffected_by_the_fallback():
    rec = _records()[0]
    assert rec.sql, "the shared fixture must actually carry statements"
    out = "\n".join(rep.render_statements(rec))
    assert "No SQL was captured" not in out
    assert "```sql" in out


def test_a_statement_with_no_text_is_named_not_rendered_as_a_blank_block():
    """Pgpool health checks reached the report as `[8] — · — · 0.06 ms`.

    35-38% of the statement entries in the 2026-09-02 reports were these.
    Fixed at the parse boundary; this guard keeps the symptom legible if
    anything else ever produces one.
    """
    rec = RecObj("x", "GET", "/x", 200, sql=[Stmt(8, None, None, " ", None, 0.06)])
    out = "\n".join(rep.render_statements(rec))
    assert "no SQL text" in out
    assert "```sql\n\n```" not in out, "never an empty code block"


# ----------------------------------------------------------------------
# merging EXPLAIN results back into a matrix report
# ----------------------------------------------------------------------
MATRIX = """### `iceberg.get_config`

- `GET /v1/config` → **200**

**[0]** `grant_records` · SELECT · 0.31 ms

```sql
SELECT a FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ?
```
params: `1002, POLARIS`

**[1]** `principal_authentication_data` · SELECT · 0.02 ms

```sql
SELECT s FROM POLARIS_SCHEMA.PRINCIPAL_AUTHENTICATION_DATA WHERE realm_id = ?
```
params: `<redacted>`
"""

EXPLAINS = [
    {
        "sql": "SELECT a FROM POLARIS_SCHEMA.GRANT_RECORDS WHERE grantee_id = ? AND realm_id = ?",
        "params": "1002, POLARIS",
        "scans": [{"node": "Seq Scan", "relation": "grant_records", "index": None}],
        "node_types": ["Seq Scan"],
        "plan_rows": 1,
        "plan": {"Plan": {"Total Cost": 1637.26}},
        "rows_removed_by_filter": 60814,
    }
]


def test_a_plan_lands_under_the_statement_it_belongs_to():
    out, stats = rep.annotate_with_explains(MATRIX, EXPLAINS, "index absent")
    assert stats["matched"] == 1
    line = [x for x in out.splitlines() if x.startswith("EXPLAIN")][0]
    assert "Seq Scan on grant_records" in line
    assert "cost 1637.26" in line
    assert "60,814 rows filtered" in line
    #: Its OWN paragraph. Without the blank line markdown joins it onto the
    #: `params:` line above and the report reads as a wall of prose.
    assert "`\n\nEXPLAIN" in out
    #: directly beneath its own params line, not floating at the end
    body = out.split("**[0]**")[1]
    assert body.index("EXPLAIN") > body.index("params:")
    assert body.index("EXPLAIN") < body.index("**[1]**")


def test_a_redacted_statement_says_why_rather_than_going_blank():
    """A blank line here reads as a capture fault, which is precisely what the
    2026-09-02 session was spent proving something was NOT."""
    out, stats = rep.annotate_with_explains(MATRIX, EXPLAINS, "index absent")
    assert stats["redacted"] == 1 and stats["unmatched"] == 0
    assert "never be replayed" in out


def test_re_running_replaces_the_annotation_rather_than_stacking_it():
    once, _ = rep.annotate_with_explains(MATRIX, EXPLAINS, "index absent")
    twice, _ = rep.annotate_with_explains(once, EXPLAINS, "index absent")
    assert twice == once
    assert once.count("EXPLAIN (index absent)") == 1


def test_a_statement_with_no_plan_and_no_redaction_is_counted_unmatched():
    """The signal that a report and a run come from different drives."""
    out, stats = rep.annotate_with_explains(MATRIX, [], "index absent")
    assert stats == {"matched": 0, "redacted": 1, "unmatched": 1}
    assert "not in the sweep's worklist" in out


def test_the_join_ignores_placeholder_dialect():
    """The pg log writes $1/$2 where Polaris writes ?; normalize_sql unifies
    them, so a statement captured from either stream joins."""
    ex = [
        dict(
            EXPLAINS[0],
            sql="SELECT a FROM POLARIS_SCHEMA.GRANT_RECORDS "
            "WHERE grantee_id = $1 AND realm_id = $2",
        )
    ]
    out, stats = rep.annotate_with_explains(MATRIX, ex, "index absent")
    assert stats["matched"] == 1
