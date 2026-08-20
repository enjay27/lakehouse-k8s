"""
Pytest suite for src/schema_audit.py.

Uses a fake psycopg2-shaped connection, so the whole audit — drift comparison,
EXPLAIN handling, verdict logic and hypothesis checking — is verifiable with no
live PostgreSQL.

Covers in particular the two ways this module could produce a WRONG finding:
  * calling a Seq Scan on a small table a defect (it isn't — TOO_SMALL)
  * letting EXPLAIN ANALYZE execute a write statement (it must not)

Run: pytest test_schema_audit.py
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent / "src"))
from schema_audit import (EXPECTED_INDEXES, INDEX_HYPOTHESES,  # noqa: E402
                          MIN_ROWS_FOR_VERDICT, audit_statements,
                          check_hypotheses, compare_schema, explain_statement,
                          parse_param_list, plan_summary, rank_statements)


# ----------------------------------------------------------------------
# fake connection
# ----------------------------------------------------------------------
class FakeCursor:
    def __init__(self, conn):
        self.conn = conn
        self._result = None
        self.description = None

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, args=None):
        self.conn.executed.append((sql, args))
        s = " ".join(sql.split()).upper()
        if s.startswith("SAVEPOINT") or s.startswith("ROLLBACK TO"):
            self._result = None
            return
        if s.startswith("EXPLAIN"):
            if self.conn.explain_error:
                raise RuntimeError(self.conn.explain_error)
            self._result = [self.conn.explain_plan]
            return
        if "TO_REGCLASS" in s:
            self._result = ["polaris_schema.version" if self.conn.has_version else None]
            return
        if "VERSION_VALUE" in s:
            self._result = [self.conn.version]
            return
        if "RELTUPLES" in s:
            table = args[1] if args else None
            self._result = [self.conn.rowcounts.get(table, 0)]
            return
        self._result = [None]

    def fetchone(self):
        return self._result

    def fetchall(self):
        return []


class FakeConn:
    def __init__(
        self,
        version=2,
        rowcounts=None,
        explain_plan=None,
        explain_error=None,
        has_version=True,
    ):
        self.version = version
        self.rowcounts = rowcounts or {}
        self.explain_plan = explain_plan
        self.explain_error = explain_error
        self.has_version = has_version
        self.executed = []
        self.rolled_back = 0

    def cursor(self):
        return FakeCursor(self)

    def commit(self):
        pass

    def rollback(self):
        self.rolled_back += 1


def seq_scan_plan(relation="grant_records", rows_removed=90000, ms=250.0):
    return [
        {
            "Plan": {
                "Node Type": "Seq Scan",
                "Relation Name": relation,
                "Rows Removed by Filter": rows_removed,
                "Shared Read Blocks": 900,
            },
            "Execution Time": ms,
        }
    ]


def index_scan_plan(index="idx_entities", relation="entities", removed=0, ms=0.4):
    return [
        {
            "Plan": {
                "Node Type": "Index Scan",
                "Index Name": index,
                "Relation Name": relation,
                "Rows Removed by Filter": removed,
                "Shared Hit Blocks": 4,
            },
            "Execution Time": ms,
        }
    ]


# ----------------------------------------------------------------------
# schema drift
# ----------------------------------------------------------------------
def full_snapshot(**over):
    snap = {
        "schema": "polaris_schema",
        "version": 2,
        "tables": sorted(
            [
                "version",
                "entities",
                "grant_records",
                "principal_authentication_data",
                "policy_mapping_record",
            ]
        ),
        "indexes": [
            {
                "name": name,
                "table": table,
                "definition": f"CREATE INDEX {name} ON {table} ({', '.join(cols)})",
                "columns": cols,
                "is_unique": kind in ("pk", "unique"),
                "is_primary": kind == "pk",
            }
            for (name, table, cols, kind) in EXPECTED_INDEXES
        ],
    }
    snap.update(over)
    return snap


def test_matching_schema_reports_ok():
    r = compare_schema(full_snapshot())
    assert r["verdict"] == "OK"
    assert r["missing_indexes"] == []
    assert r["missing_tables"] == []
    assert r["version_ok"] is True


def test_missing_index_is_detected_and_named():
    snap = full_snapshot()
    snap["indexes"] = [i for i in snap["indexes"] if i["name"] != "idx_locations"]
    r = compare_schema(snap)
    assert r["verdict"] == "DRIFT"
    assert [i["name"] for i in r["missing_indexes"]] == ["idx_locations"]
    assert any("MIGRATION" in n for n in r["notes"])


def test_index_matched_by_columns_not_name():
    """A differently-named index doing the same job counts as present — the
    question is whether an access path exists."""
    snap = full_snapshot()
    for i in snap["indexes"]:
        if i["name"] == "idx_entities":
            i["name"] = "my_hand_rolled_index"
    r = compare_schema(snap)
    assert r["missing_indexes"] == []


def test_wrong_schema_version_flagged():
    r = compare_schema(full_snapshot(version=3))
    assert r["version_ok"] is False
    assert r["verdict"] == "DRIFT"
    assert any("schema-v2" in n for n in r["notes"])


def test_events_table_recognised_as_event_listener_not_drift():
    """The Helm values enable eventListener.type: persistence-in-memory-buffer,
    which creates and writes `events`. Reporting that as schema drift would be a
    false positive on every single run."""
    snap = full_snapshot()
    snap["tables"] = sorted(snap["tables"] + ["events"])
    r = compare_schema(snap)
    assert r["unexpected_tables"] == []
    assert r["event_listener_tables"] == ["events"]
    assert r["verdict"] == "OK"
    assert any("event listener" in n for n in r["notes"])


def test_genuinely_unexpected_table_still_flagged():
    snap = full_snapshot()
    snap["tables"] = sorted(snap["tables"] + ["some_future_table"])
    r = compare_schema(snap)
    assert r["unexpected_tables"] == ["some_future_table"]


def test_missing_table_detected():
    snap = full_snapshot()
    snap["tables"] = [t for t in snap["tables"] if t != "policy_mapping_record"]
    r = compare_schema(snap)
    assert r["missing_tables"] == ["policy_mapping_record"]


def test_null_version_is_reported_not_crashed():
    r = compare_schema(full_snapshot(version=None))
    assert r["version_ok"] is False
    assert any("not be an initialized" in n for n in r["notes"])


# ----------------------------------------------------------------------
# params
# ----------------------------------------------------------------------
def test_parse_param_list_bracket_form_with_type_coercion():
    assert parse_param_list("[POLARIS, 0, 42, mycat]") == ["POLARIS", 0, 42, "mycat"]


def test_parse_param_list_pg_detail_form():
    assert parse_param_list("$1 = 'POLARIS', $2 = '42'") == ["POLARIS", 42]


def test_parse_param_list_refuses_redacted():
    """Redacted parameters must never be replaced with fabricated substitutes."""
    assert parse_param_list("<redacted>") is None
    assert parse_param_list(None) is None
    assert parse_param_list("") is None


# ----------------------------------------------------------------------
# EXPLAIN safety
# ----------------------------------------------------------------------
def test_explain_analyze_not_used_on_writes_by_default():
    conn = FakeConn(explain_plan=index_scan_plan())
    res = explain_statement(conn, "DELETE FROM entities WHERE id = ?", [1])
    assert res["ok"] is True
    assert res["analyzed"] is False, "ANALYZE would have executed the DELETE"
    explain_sql = [s for s, _ in conn.executed if s.upper().startswith("EXPLAIN")][0]
    assert "ANALYZE" not in explain_sql.upper()


def test_write_analyze_opt_in_is_wrapped_in_a_rolled_back_savepoint():
    conn = FakeConn(explain_plan=index_scan_plan())
    res = explain_statement(
        conn, "INSERT INTO entities (a) VALUES (?)", [1], allow_write_analyze=True
    )
    assert res["analyzed"] is True
    stmts = [" ".join(s.split()).upper() for s, _ in conn.executed]
    assert any(s.startswith("SAVEPOINT") for s in stmts)
    assert any(s.startswith("ROLLBACK TO SAVEPOINT") for s in stmts)


def test_reads_are_analyzed():
    conn = FakeConn(explain_plan=index_scan_plan())
    res = explain_statement(conn, "SELECT a FROM entities WHERE id = ?", [1])
    assert res["analyzed"] is True


def test_placeholders_converted_for_psycopg2():
    conn = FakeConn(explain_plan=index_scan_plan())
    explain_statement(conn, "SELECT a FROM entities WHERE r = $1 AND c = ?", ["x", 1])
    sql = [s for s, _ in conn.executed if s.upper().startswith("EXPLAIN")][0]
    assert "$1" not in sql and "?" not in sql and "%s" in sql


def test_explain_failure_is_returned_not_raised():
    conn = FakeConn(explain_error="syntax error")
    res = explain_statement(conn, "SELECT bogus", [])
    assert res["ok"] is False
    assert "syntax error" in res["error"]
    assert conn.rolled_back == 1


# ----------------------------------------------------------------------
# plan summary
# ----------------------------------------------------------------------
def test_plan_summary_extracts_scan_kinds():
    s = plan_summary(seq_scan_plan())
    assert s["seq_scans"] == ["grant_records"]
    assert s["index_scans"] == []
    assert s["rows_removed_by_filter"] == 90000
    assert s["total_ms"] == 250.0

    s2 = plan_summary(index_scan_plan())
    assert s2["index_scans"] == ["idx_entities"]
    assert s2["seq_scans"] == []


# ----------------------------------------------------------------------
# verdicts
# ----------------------------------------------------------------------
def _inv(sql, table, verb="SELECT", params="[POLARIS, 0, 42]"):
    return [
        {
            "sql": sql,
            "table": table,
            "verb": verb,
            "params": params,
            "apis": ["x"],
            "calls": 3,
        }
    ]


def test_seq_scan_on_large_table_is_flagged():
    conn = FakeConn(rowcounts={"grant_records": 50000}, explain_plan=seq_scan_plan())
    rows = audit_statements(
        conn, _inv("SELECT a FROM grant_records WHERE grantee_id = ?", "grant_records")
    )
    assert rows[0]["verdict"] == "SEQ_SCAN"
    assert "grant_records" in rows[0]["seq_scans"]


def test_seq_scan_on_small_table_is_not_a_finding():
    """The single easiest way to produce a false finding — guarded explicitly."""
    conn = FakeConn(rowcounts={"grant_records": 10}, explain_plan=seq_scan_plan())
    rows = audit_statements(
        conn, _inv("SELECT a FROM grant_records WHERE grantee_id = ?", "grant_records")
    )
    assert rows[0]["verdict"] == "TOO_SMALL"
    assert "Seed more data" in rows[0]["detail"]


def test_index_scan_verdict():
    conn = FakeConn(rowcounts={"entities": 100000}, explain_plan=index_scan_plan())
    rows = audit_statements(
        conn, _inv("SELECT a FROM entities WHERE id = ?", "entities")
    )
    assert rows[0]["verdict"] == "INDEX_SCAN"


def test_filter_heavy_verdict_for_partially_matching_index():
    plan = index_scan_plan(removed=60000)
    conn = FakeConn(rowcounts={"entities": 100000}, explain_plan=plan)
    rows = audit_statements(
        conn, _inv("SELECT a FROM entities WHERE id = ?", "entities")
    )
    assert rows[0]["verdict"] == "FILTER_HEAVY"


def test_missing_params_skips_explain():
    conn = FakeConn(rowcounts={"entities": 100000}, explain_plan=index_scan_plan())
    rows = audit_statements(
        conn, _inv("SELECT a FROM entities WHERE id = ?", "entities", params=None)
    )
    assert rows[0]["verdict"] == "NO_PARAMS"


def test_redacted_params_skip_explain():
    conn = FakeConn(
        rowcounts={"principal_authentication_data": 100000},
        explain_plan=index_scan_plan(),
    )
    rows = audit_statements(
        conn,
        _inv(
            "SELECT a FROM principal_authentication_data WHERE principal_client_id = ?",
            "principal_authentication_data",
            params="<redacted>",
        ),
    )
    assert rows[0]["verdict"] == "NO_PARAMS"


def test_explain_error_becomes_error_verdict():
    conn = FakeConn(rowcounts={"entities": 100000}, explain_error="boom")
    rows = audit_statements(
        conn, _inv("SELECT a FROM entities WHERE id = ?", "entities")
    )
    assert rows[0]["verdict"] == "ERROR"
    assert "boom" in rows[0]["error"]


# ----------------------------------------------------------------------
# hypotheses
# ----------------------------------------------------------------------
def test_grant_records_hypothesis_confirmed_by_seq_scan():
    audit = [{"table": "grant_records", "verdict": "SEQ_SCAN", "sql": "SELECT ..."}]
    res = check_hypotheses(None, audit)
    grantee = next(h for h in res if h["id"] == "grant_records_by_grantee")
    assert grantee["status"] == "CONFIRMED"
    assert grantee["severity"] == "high"
    assert "CREATE INDEX" in grantee["remedy"]


def test_hypothesis_refuted_when_index_used():
    audit = [{"table": "grant_records", "verdict": "INDEX_SCAN", "sql": "SELECT ..."}]
    res = check_hypotheses(None, audit)
    assert next(h for h in res if h["id"] == "grant_records_by_grantee")["status"] == (
        "REFUTED"
    )


def test_hypothesis_inconclusive_when_table_too_small():
    audit = [{"table": "grant_records", "verdict": "TOO_SMALL", "sql": "SELECT ..."}]
    res = check_hypotheses(None, audit)
    h = next(h for h in res if h["id"] == "grant_records_by_grantee")
    assert h["status"] == "INCONCLUSIVE"
    assert "seed more data" in h["evidence"][0]


def test_hypothesis_inconclusive_when_no_statement_captured():
    res = check_hypotheses(None, [])
    assert all(h["status"] == "INCONCLUSIVE" for h in res)


def test_every_hypothesis_carries_the_fields_a_report_needs():
    for h in INDEX_HYPOTHESES:
        for key in (
            "id",
            "table",
            "source_method",
            "claim",
            "why_it_matters",
            "severity",
            "remedy",
        ):
            assert h.get(key), f"{h.get('id')} missing {key}"


# ----------------------------------------------------------------------
# ranking
# ----------------------------------------------------------------------
def test_rank_by_total_time_not_max_duration():
    """A moderately slow query on the auth path outranks one slow outlier."""
    inv = [
        {"sql": "rare but slow", "total_ms": 300.0, "max_ms": 300.0, "calls": 1},
        {"sql": "auth path", "total_ms": 900.0, "max_ms": 3.0, "calls": 300},
    ]
    assert rank_statements(inv)[0]["sql"] == "auth path"


def test_rank_falls_back_to_calls_without_timings():
    inv = [
        {"sql": "a", "total_ms": None, "calls": 2},
        {"sql": "b", "total_ms": None, "calls": 50},
    ]
    assert rank_statements(inv)[0]["sql"] == "b"


def test_min_rows_threshold_is_sane():
    assert MIN_ROWS_FOR_VERDICT >= 1000


# ----------------------------------------------------------------------
# planner statistics — a stale estimate must not read as "small table"
# ----------------------------------------------------------------------
class StatsCursor(FakeCursor):
    def execute(self, sql, args=None):
        self.conn.executed.append((sql, args))
        s = " ".join(sql.split()).upper()
        if "RELTUPLES <" in s:
            self._result = None
            self.conn._stale = [(t,) for t in self.conn.unanalyzed]
            return
        if "RELTUPLES" in s:
            table = args[1] if args else None
            self._result = [self.conn.reltuples.get(table, 0)]
            return
        if s.startswith("SELECT COUNT(*)"):
            self.conn.exact_counts_taken += 1
            self._result = [self.conn.exact.get("n", 0)]
            return
        if s.startswith("ANALYZE"):
            self.conn.analyzed.append(sql)
            self._result = None
            return
        super().execute(sql, args)

    def fetchall(self):
        return getattr(self.conn, "_stale", [])


class StatsConn(FakeConn):
    def __init__(self, reltuples=None, exact_n=0, unanalyzed=()):
        super().__init__()
        self.reltuples = reltuples or {}
        self.exact = {"n": exact_n}
        self.exact_counts_taken = 0
        self.analyzed = []
        self.unanalyzed = list(unanalyzed)

    def cursor(self):
        return StatsCursor(self)


def test_never_analyzed_table_falls_back_to_exact_count():
    """reltuples = -1 means 'never analyzed'. Treating it as a row count would
    make a freshly seeded 25k-row table report TOO_SMALL — precisely the case
    the audit exists for."""
    from schema_audit import relation_rowcount

    conn = StatsConn(reltuples={"grant_records": -1}, exact_n=25000)
    assert relation_rowcount(conn, "grant_records") == 25000
    assert conn.exact_counts_taken == 1


def test_valid_estimate_avoids_the_exact_count():
    from schema_audit import relation_rowcount

    conn = StatsConn(reltuples={"entities": 16000}, exact_n=999)
    assert relation_rowcount(conn, "entities") == 16000
    assert conn.exact_counts_taken == 0, "an exact count on a large table is expensive"


def test_zero_estimate_is_trusted_as_genuinely_empty():
    from schema_audit import relation_rowcount

    conn = StatsConn(reltuples={"entities": 0}, exact_n=123)
    assert relation_rowcount(conn, "entities") == 0
    assert conn.exact_counts_taken == 0


def test_analyze_tables_runs_over_the_expected_set():
    from schema_audit import EXPECTED_TABLES, analyze_tables

    conn = StatsConn()
    done = analyze_tables(conn)
    assert set(done) == EXPECTED_TABLES
    assert all(a.startswith("ANALYZE") for a in conn.analyzed)


def test_statistics_are_stale_lists_unanalyzed_tables():
    from schema_audit import statistics_are_stale

    conn = StatsConn(unanalyzed=["entities", "grant_records"])
    assert statistics_are_stale(conn) == ["entities", "grant_records"]
