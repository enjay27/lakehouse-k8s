"""
Pytest suite for src/api_trace.py.

Every parser takes text and returns records, so the whole module is testable
offline against fixtures — no Polaris, Postgres or MinIO required. Fixtures
below are the real line shapes each stream produces.

Includes an explicit secret-safety test: no unredacted hash or salt material
may survive parsing of a principal_authentication_data statement.

Run: pytest test_api_trace.py
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent / "src"))
from api_trace import (  # noqa: E402
    REDACTED,
    MinioOp,
    SqlStatement,
    StringStream,
    Tracer,
    TraceRecord,
    api_minio_matrix,
    api_table_matrix,
    extract_table,
    extract_verb,
    normalize_sql,
    parse_minio_trace,
    parse_pg_log,
    parse_polaris_log,
    records_to_rows,
    redact_params,
    scrub_text,
    split_query_message,
    statement_inventory,
    unknown_tables,
)

# ----------------------------------------------------------------------
# fixtures — real line shapes
# ----------------------------------------------------------------------
POLARIS_LOG = """\
2026-08-18 10:00:00,100 DEBUG [org.apa.pol.per.rel.jdb.DatasourceOperations] (executor-thread-1) query: SELECT realm_id, catalog_id, id, parent_id, name FROM POLARIS_SCHEMA.entities WHERE realm_id = ? AND catalog_id = ? AND parent_id = ? AND type_code = ? AND name = ? [POLARIS, 0, 0, 2, mycat]
2026-08-18 10:00:00,110 INFO  [io.quarkus] (main) something unrelated
2026-08-18 10:00:00,120 DEBUG [org.apa.pol.per.rel.jdb.DatasourceOperations] (executor-thread-1) query: SELECT privilege_code FROM POLARIS_SCHEMA.grant_records WHERE realm_id = ? AND grantee_catalog_id = ? AND grantee_id = ? [POLARIS, 0, 42]
"""

POLARIS_LOG_CACHE_HIT = """\
2026-08-18 10:00:05,100 DEBUG [org.apa.pol.per.rel.jdb.DatasourceOperations] (executor-thread-1) query: SELECT entity_version, grant_records_version FROM POLARIS_SCHEMA.entities WHERE (catalog_id, id) IN ((?,?),(?,?)) AND realm_id = ? [0, 1, 0, 2, POLARIS]
"""

POLARIS_LOG_SECRET = """\
2026-08-18 10:00:00,100 DEBUG [org.apa.pol.per.rel.jdb.DatasourceOperations] (executor-thread-1) query: INSERT INTO POLARIS_SCHEMA.principal_authentication_data (principal_id, principal_client_id, main_secret_hash, secret_salt, realm_id) VALUES (?,?,?,?,?) [42, abc123, 5f4dcc3b5aa765d61d8327deb882cf99aabbccddeeff00112233445566778899, deadbeefcafebabe1234567890abcdef, POLARIS]
"""

PG_LOG = """\
2026-08-18 10:00:00.100 UTC [1234] db=polaris,user=polaris,app=,xid=0 LOG:  execute <unnamed>: SELECT realm_id, catalog_id, id FROM POLARIS_SCHEMA.entities WHERE realm_id = $1
2026-08-18 10:00:00.100 UTC [1234] db=polaris,user=polaris,app=,xid=0 DETAIL:  parameters: $1 = 'POLARIS'
2026-08-18 10:00:00.104 UTC [1234] db=polaris,user=polaris,app=,xid=0 LOG:  duration: 3.512 ms
2026-08-18 10:00:00.105 UTC [1234] db=polaris,user=polaris,app=,xid=0 LOG:  statement: COMMIT
2026-08-18 10:00:00.106 UTC [1234] db=polaris,user=polaris,app=,xid=0 LOG:  duration: 0.201 ms
"""

PG_LOG_INTERLEAVED = """\
2026-08-18 10:00:00.100 UTC [1111] LOG:  execute <unnamed>: SELECT a FROM POLARIS_SCHEMA.entities WHERE realm_id = $1
2026-08-18 10:00:00.101 UTC [2222] LOG:  execute <unnamed>: SELECT b FROM POLARIS_SCHEMA.grant_records WHERE realm_id = $1
2026-08-18 10:00:00.110 UTC [2222] LOG:  duration: 9.000 ms
2026-08-18 10:00:00.120 UTC [1111] LOG:  duration: 20.000 ms
"""

MINIO_TRACE = """\
Streaming trace, press Ctrl-C to stop
{"api":"s3.GetObject","request":{"method":"GET","path":"/data-catalog-bucket/mycat/myns/mytbl/metadata/00001.metadata.json"},"response":{"statusCode":200},"callStats":{"duration":4200000,"rx":0,"tx":20480}}
{"api":"s3.PutObject","request":{"method":"PUT","path":"/data-catalog-bucket/mycat/myns/mytbl/metadata/00002.metadata.json"},"response":{"statusCode":200},"callStats":{"duration":8100000,"rx":20480,"tx":0}}
not json at all
"""


# ----------------------------------------------------------------------
# SQL helpers
# ----------------------------------------------------------------------
def test_extract_table_handles_schema_qualified_and_bare():
    assert (
        extract_table("SELECT x FROM POLARIS_SCHEMA.entities WHERE a=?") == "entities"
    )
    assert extract_table("SELECT x FROM entities") == "entities"
    assert extract_table("INSERT INTO POLARIS_SCHEMA.grant_records (a) VALUES (?)") == (
        "grant_records"
    )
    assert extract_table("UPDATE POLARIS_SCHEMA.entities SET a=?") == "entities"
    assert extract_table("DELETE FROM POLARIS_SCHEMA.entities WHERE id=?") == "entities"


def test_extract_table_returns_none_for_transaction_control():
    assert extract_table("COMMIT") is None
    assert extract_table("") is None
    assert extract_table(None) is None


def test_extract_verb():
    assert extract_verb("  select 1 from t") == "SELECT"
    assert extract_verb("COMMIT") == "COMMIT"
    assert extract_verb("gibberish") is None


def test_normalize_sql_collapses_whitespace_and_in_lists():
    a = normalize_sql(
        "SELECT  a\n FROM t WHERE (catalog_id, id) IN ((?,?),(?,?)) AND r=?"
    )
    b = normalize_sql(
        "SELECT a FROM t WHERE (catalog_id, id) IN ((?,?),(?,?),(?,?)) AND r=?"
    )
    assert a == b, "row-constructor IN lists of differing size must normalize alike"
    assert "<rows>" in a


def test_normalize_sql_scalar_in_list():
    assert "<list>" in normalize_sql("SELECT a FROM t WHERE id IN (?, ?, ?)")
    assert "<list>" in normalize_sql("SELECT a FROM t WHERE id IN ($1, $2, $3)")


def test_normalize_sql_unifies_jdbc_and_postgres_placeholder_styles():
    """Polaris logs `?`, PostgreSQL logs `$1`. If these don't normalize to the
    same string, server-side durations never attach to Polaris's statements —
    and the failure is silent."""
    assert normalize_sql("SELECT a FROM t WHERE r = ? AND c = ?") == normalize_sql(
        "SELECT a FROM t WHERE r = $1 AND c = $2"
    )


# ----------------------------------------------------------------------
# redaction — hard requirement
# ----------------------------------------------------------------------
def test_secret_table_params_fully_redacted():
    stmts = parse_polaris_log(POLARIS_LOG_SECRET)
    assert len(stmts) == 1
    assert stmts[0].table == "principal_authentication_data"
    assert stmts[0].params == REDACTED


def test_no_hash_material_survives_parsing():
    """The whole point of the redaction layer: nothing hash-shaped may leak."""
    stmts = parse_polaris_log(POLARIS_LOG_SECRET)
    blob = " ".join(str(s.params) for s in stmts)
    assert "5f4dcc3b5aa765d61d8327deb882cf99" not in blob
    assert "deadbeefcafebabe1234567890abcdef" not in blob


def test_hashlike_values_redacted_outside_secret_tables():
    out = redact_params(
        "SELECT x FROM POLARIS_SCHEMA.entities WHERE a = ?",
        "[5f4dcc3b5aa765d61d8327deb882cf995f4dcc3b, plainvalue]",
    )
    assert "5f4dcc3b5aa765d61d8327deb882cf99" not in out
    assert "plainvalue" in out, "ordinary values must survive"


def test_redact_params_passes_through_none():
    assert redact_params("SELECT 1", None) is None


def test_scrub_text_redacts_parameter_payload_on_secret_lines():
    scrubbed = scrub_text(POLARIS_LOG_SECRET)
    assert "5f4dcc3b5aa765d61d8327deb882cf99" not in scrubbed


# ----------------------------------------------------------------------
# Polaris log parser
# ----------------------------------------------------------------------
def test_parse_polaris_log_extracts_statements_and_skips_other_lines():
    stmts = parse_polaris_log(POLARIS_LOG)
    assert len(stmts) == 2
    assert [s.table for s in stmts] == ["entities", "grant_records"]
    assert all(s.verb == "SELECT" for s in stmts)
    assert all(s.source == "polaris" for s in stmts)
    assert [s.seq for s in stmts] == [0, 1]


def test_parse_polaris_log_splits_trailing_params_off_the_sql():
    stmts = parse_polaris_log(POLARIS_LOG)
    assert not stmts[0].sql.rstrip().endswith("]")
    assert "mycat" in stmts[0].params


POLARIS_LOG_REAL_FORMAT = (
    "2026-08-18 10:00:00,100 DEBUG [org.apa.pol.per.rel.jdb.DatasourceOperations] "
    "[req-abc123,POLARIS] [4bf92f3577b34da6,00f067aa0ba902b7,a1b2c3d4,true] "
    "(executor-thread-1) query: SELECT realm_id, id FROM POLARIS_SCHEMA.entities "
    "WHERE realm_id = ? [POLARIS]\n"
)


def test_parses_polaris_shipped_console_format_with_positional_mdc():
    """Polaris 1.3.0 ships `[%X{requestId},%X{realmId}] [%X{traceId},...]` — the
    MDC is POSITIONAL, so a key=value matcher finds nothing against real logs."""
    stmts = parse_polaris_log(POLARIS_LOG_REAL_FORMAT)
    assert len(stmts) == 1
    assert stmts[0].table == "entities"
    assert stmts[0].request_id == "req-abc123"
    assert stmts[0].trace_id == "4bf92f3577b34da6"


def test_key_value_mdc_still_supported_as_fallback():
    line = (
        "2026-08-18 10:00:00,100 DEBUG [DatasourceOperations] requestId=zz1 "
        "traceId=abc123 query: SELECT a FROM POLARIS_SCHEMA.entities"
    )
    s = parse_polaris_log(line)[0]
    assert s.request_id == "zz1" and s.trace_id == "abc123"


def test_missing_mdc_is_not_an_error():
    stmts = parse_polaris_log(POLARIS_LOG)
    assert stmts[0].request_id is None and stmts[0].trace_id is None


# ----------------------------------------------------------------------
# JSON log format — what Polaris actually emits with
# quarkus.log.console.json.enabled=true
# ----------------------------------------------------------------------
JSON_LOG = (
    '{"timestamp":"2026-08-18T02:41:13.436842992Z","sequence":2092,'
    '"loggerClassName":"org.slf4j.spi.DefaultLoggingEventBuilder",'
    '"loggerName":"org.apache.polaris.persistence.relational.jdbc.DatasourceOperations",'
    '"level":"DEBUG",'
    '"message":"query: SELECT realm_id, catalog_id, id FROM POLARIS_SCHEMA.entities '
    'WHERE realm_id = ? AND catalog_id = ?\\n    POLARIS\\n    0",'
    '"threadName":"executor-thread-1","threadId":27,'
    '"mdc":{"requestId":"464c8234-6679_0000000000000000002","realmId":"POLARIS"},'
    '"ndc":"","hostName":"benchmarks-polaris-6bbf6b84c5-d72q6","processId":1}\n'
    '{"timestamp":"2026-08-18T02:41:13.489406453Z","sequence":2093,'
    '"loggerName":"io.quarkus.http.access-log","level":"INFO",'
    '"message":"192.168.194.1 - root [18/Aug/2026:02:41:13 +0000] '
    '\\"GET /api/management/v1/catalogs HTTP/1.1\\" 200 15",'
    '"mdc":{"requestId":"464c8234-6679_0000000000000000002","realmId":"POLARIS"}}\n'
)

JSON_LOG_NO_PARAMS = (
    '{"loggerName":"org.apache.polaris.persistence.relational.jdbc.DatasourceOperations",'
    '"level":"DEBUG","message":"query: SELECT version_value FROM POLARIS_SCHEMA.version'
    '\\n    ","mdc":{}}\n'
)

JSON_LOG_SECRET = (
    '{"loggerName":"org.apache.polaris.persistence.relational.jdbc.DatasourceOperations",'
    '"level":"DEBUG","message":"query: INSERT INTO '
    "POLARIS_SCHEMA.principal_authentication_data (principal_client_id, main_secret_hash) "
    "VALUES (?,?)\\n    abc123"
    '\\n    5f4dcc3b5aa765d61d8327deb882cf99aabbccddeeff00112233445566778899",'
    '"mdc":{"requestId":"r1"}}\n'
)


def test_parses_quarkus_json_log_format():
    stmts = parse_polaris_log(JSON_LOG)
    assert len(stmts) == 1, "the access-log line must not be picked up"
    s = stmts[0]
    assert s.table == "entities"
    assert s.verb == "SELECT"
    assert s.sql.endswith("catalog_id = ?"), "params must be split off the SQL"
    assert "\n" not in s.sql
    assert s.params == "POLARIS, 0"
    assert s.request_id == "464c8234-6679_0000000000000000002"


def test_json_params_are_newline_separated_not_bracketed():
    """logQuery joins parameters with '\\n    ' — a bracket-matching parser
    silently captures none of them."""
    s = parse_polaris_log(JSON_LOG)[0]
    assert s.params is not None and "POLARIS" in s.params


def test_json_empty_parameter_list_yields_none():
    """An empty parameter stream still emits the joiner prefix, leaving a bare
    trailing newline — that is no parameters, not one empty parameter."""
    s = parse_polaris_log(JSON_LOG_NO_PARAMS)[0]
    assert s.table == "version"
    assert s.params is None


def test_json_secret_table_params_still_redacted():
    s = parse_polaris_log(JSON_LOG_SECRET)[0]
    assert s.table == "principal_authentication_data"
    assert s.params == REDACTED
    assert "5f4dcc3b5aa765d61d8327deb882cf99" not in str(s.params)


def test_malformed_json_line_is_skipped_not_fatal():
    assert parse_polaris_log('{"loggerName":"DatasourceOperations", broken\n') == []


def test_split_query_message_handles_both_forms():
    sql, params = split_query_message("SELECT 1 FROM t\n    a\n    b")
    assert sql == "SELECT 1 FROM t" and params == "a, b"

    sql, params = split_query_message("SELECT 1 FROM t [a, b]")
    assert sql == "SELECT 1 FROM t" and params == "[a, b]"

    sql, params = split_query_message("COMMIT")
    assert sql == "COMMIT" and params is None


def test_require_logger_false_is_more_permissive():
    text = "2026-08-18 10:00:00,100 DEBUG [x] query: SELECT 1 FROM entities"
    assert parse_polaris_log(text) == []
    assert len(parse_polaris_log(text, require_logger=False)) == 1


# ----------------------------------------------------------------------
# cache verdict
# ----------------------------------------------------------------------
def test_version_only_select_is_recognised_as_cache_validation():
    stmts = parse_polaris_log(POLARIS_LOG_CACHE_HIT)
    assert stmts[0].is_version_check is True


def test_full_column_select_is_not_a_version_check():
    stmts = parse_polaris_log(POLARIS_LOG)
    assert stmts[0].is_version_check is False


def test_cache_verdict_hit_miss_and_na():
    hit = TraceRecord(api="a", sql=parse_polaris_log(POLARIS_LOG_CACHE_HIT))
    assert hit.cache_verdict == "HIT"

    miss = TraceRecord(api="a", sql=parse_polaris_log(POLARIS_LOG))
    assert miss.cache_verdict == "MISS"

    na = TraceRecord(api="a", sql=[])
    assert na.cache_verdict == "N/A"


def test_cache_verdict_na_when_only_non_entity_tables_read():
    rec = TraceRecord(
        api="a",
        sql=[
            SqlStatement(
                seq=0,
                sql="SELECT x FROM grant_records",
                table="grant_records",
                verb="SELECT",
            )
        ],
    )
    assert rec.cache_verdict == "N/A"


# ----------------------------------------------------------------------
# PostgreSQL log parser
# ----------------------------------------------------------------------
def test_parse_pg_log_attaches_params_and_duration():
    stmts = parse_pg_log(PG_LOG)
    assert len(stmts) == 2
    assert stmts[0].table == "entities"
    assert stmts[0].duration_ms == 3.512
    assert "POLARIS" in stmts[0].params
    assert stmts[1].verb == "COMMIT"
    assert stmts[1].duration_ms == 0.201


def test_parse_pg_log_matches_duration_to_the_right_backend_pid():
    """Interleaved backends must not cross-assign durations — under PgBouncer
    this is routine, not hypothetical."""
    stmts = parse_pg_log(PG_LOG_INTERLEAVED)
    by_table = {s.table: s for s in stmts}
    assert by_table["entities"].duration_ms == 20.0
    assert by_table["grant_records"].duration_ms == 9.0


# ----------------------------------------------------------------------
# MinIO parser
# ----------------------------------------------------------------------
def test_parse_minio_trace_reads_json_lines_and_skips_noise():
    ops = parse_minio_trace(MINIO_TRACE)
    assert len(ops) == 2
    assert ops[0].method == "GET"
    assert ops[0].bucket == "data-catalog-bucket"
    assert ops[0].key.endswith("00001.metadata.json")
    assert ops[0].status == 200
    assert ops[0].duration_ms == pytest.approx(4.2)
    assert ops[1].method == "PUT"
    assert ops[1].rx == 20480


def test_parse_minio_trace_tolerates_empty_input():
    assert parse_minio_trace("") == []


# ----------------------------------------------------------------------
# Tracer end-to-end (with in-memory streams)
# ----------------------------------------------------------------------
def test_tracer_captures_only_output_produced_inside_the_window():
    polaris = StringStream("PRE-EXISTING NOISE\n")
    minio = StringStream("")
    tracer = Tracer(polaris_log=polaris, minio_trace=minio, settle_s=0)

    with tracer.trace(
        "iceberg.load_table", "GET", "/v1/c/namespaces/n/tables/t"
    ) as rec:
        polaris.append(POLARIS_LOG)
        minio.append(MINIO_TRACE)
        rec.status = 200

    assert rec.sql_count == 2
    assert rec.minio_count == 2
    assert rec.tables_touched == ["entities", "grant_records"]
    assert rec.status == 200
    assert rec.wall_ms is not None
    assert len(tracer.records) == 1


def test_tracer_excludes_output_written_before_the_window():
    polaris = StringStream("")
    tracer = Tracer(polaris_log=polaris, settle_s=0)
    polaris.append(POLARIS_LOG)  # before the window opens

    with tracer.trace("noop") as rec:
        pass

    assert rec.sql_count == 0, "pre-window log output must not be attributed"


def test_tracer_records_error_and_reraises():
    polaris = StringStream("")
    tracer = Tracer(polaris_log=polaris, settle_s=0)

    with pytest.raises(RuntimeError):
        with tracer.trace("boom") as rec:
            polaris.append(POLARIS_LOG)
            raise RuntimeError("kaboom")

    assert "kaboom" in rec.error
    assert rec.sql_count == 2, "a failed call's SQL is still collected"


def test_tracer_works_with_no_streams_configured():
    tracer = Tracer(settle_s=0)
    with tracer.trace("bare") as rec:
        rec.status = 204
    assert rec.wall_ms is not None
    assert rec.sql_count == 0
    assert rec.cache_verdict == "N/A"


def test_pg_durations_merge_onto_polaris_statements():
    polaris = StringStream("")
    pg = StringStream("")
    tracer = Tracer(polaris_log=polaris, pg_log=pg, settle_s=0)

    with tracer.trace("merge") as rec:
        polaris.append(
            "2026-08-18 10:00:00,100 DEBUG [DatasourceOperations] query: "
            "SELECT realm_id, catalog_id, id FROM POLARIS_SCHEMA.entities WHERE realm_id = ?\n"
        )
        pg.append(PG_LOG)

    entities = [s for s in rec.sql if s.table == "entities"]
    assert entities[0].duration_ms == 3.512, "server-side duration attached to stream A"
    verbs = [s.verb for s in rec.sql]
    assert "COMMIT" in verbs, "PG-only statements are appended, not dropped"


# ----------------------------------------------------------------------
# reporting
# ----------------------------------------------------------------------
def _two_records():
    a = TraceRecord(
        api="load_table", method="GET", path="/t", status=200, t0=0.0, t1=0.05
    )
    a.sql = parse_polaris_log(POLARIS_LOG)
    a.minio = parse_minio_trace(MINIO_TRACE)
    b = TraceRecord(
        api="list_tables", method="GET", path="/ts", status=200, t0=0.0, t1=0.01
    )
    b.sql = parse_polaris_log(POLARIS_LOG)
    return [a, b]


def test_api_table_matrix_marks_read_and_write():
    recs = _two_records()
    recs[0].sql.append(
        SqlStatement(
            seq=9,
            sql="INSERT INTO POLARIS_SCHEMA.entities (a) VALUES (?)",
            table="entities",
            verb="INSERT",
        )
    )
    m = api_table_matrix(recs)
    assert m["load_table"]["entities"] == "RW"
    assert m["load_table"]["grant_records"] == "R"
    assert m["list_tables"]["entities"] == "R"


def test_api_minio_matrix_aggregates_paths():
    m = api_minio_matrix(_two_records())
    assert len(m["load_table"]) == 2
    assert m["list_tables"] == []
    assert any(e["method"] == "PUT" for e in m["load_table"])


def test_statement_inventory_groups_and_counts():
    inv = statement_inventory(_two_records())
    assert len(inv) == 2, "same two statements across both records"
    for entry in inv:
        assert entry["calls"] == 2
        assert entry["apis"] == ["list_tables", "load_table"]


def test_records_to_rows_shape():
    rows = records_to_rows(_two_records())
    assert rows[0]["api"] == "load_table"
    assert rows[0]["sql_count"] == 2
    assert rows[0]["minio_count"] == 2
    assert rows[0]["cache_verdict"] == "MISS"
    assert rows[0]["wall_ms"] == pytest.approx(50.0, rel=0.01)


def test_unaccounted_time_computed_when_durations_present():
    rec = TraceRecord(api="x", t0=0.0, t1=0.10)
    rec.sql = [
        SqlStatement(
            seq=0,
            sql="SELECT 1 FROM entities",
            table="entities",
            verb="SELECT",
            duration_ms=20.0,
        )
    ]
    rec.minio = [MinioOp(seq=0, method="GET", path="/b/k", duration_ms=30.0)]
    assert rec.unaccounted_ms == pytest.approx(50.0, rel=0.01)


def test_unknown_tables_flags_genuinely_unexpected_tables():
    recs = _two_records()
    assert unknown_tables(recs) == []
    recs[0].sql.append(
        SqlStatement(
            seq=99,
            sql="SELECT x FROM POLARIS_SCHEMA.some_future_table",
            table="some_future_table",
            verb="SELECT",
        )
    )
    assert unknown_tables(recs) == ["some_future_table"]


def test_events_table_is_not_flagged_as_unknown():
    """`events` is created by the persistence event listener
    (eventListener.type: persistence-in-memory-buffer), so on 1.3.0 it is
    expected configuration — not schema drift."""
    recs = _two_records()
    recs[0].sql.append(
        SqlStatement(
            seq=99,
            sql="INSERT INTO POLARIS_SCHEMA.events (event_id) VALUES (?)",
            table="events",
            verb="INSERT",
        )
    )
    assert unknown_tables(recs) == []


def test_async_event_writes_reported_separately_not_as_api_cost():
    """The listener flushes on a timer (bufferTime PT5S), so its INSERTs land in
    whatever window is open when the flush fires — not the window of the call
    that produced them. Counting them as this API's work would inflate a random
    subset of measurements and make the sweep non-reproducible."""
    rec = TraceRecord(api="load_table", t0=0.0, t1=0.05)
    rec.sql = parse_polaris_log(POLARIS_LOG)
    rec.sql.append(
        SqlStatement(
            seq=99,
            sql="INSERT INTO POLARIS_SCHEMA.events (event_id) VALUES (?)",
            table="events",
            verb="INSERT",
        )
    )
    assert "events" not in rec.tables_touched
    assert rec.async_tables == ["events"]
    assert len(rec.sync_sql) == len(rec.sql) - 1
    assert rec.to_row()["async_tables"] == "events"


def test_event_writes_excluded_from_the_api_table_matrix():
    rec = TraceRecord(api="load_table")
    rec.sql = [
        SqlStatement(
            seq=0, sql="SELECT a FROM entities", table="entities", verb="SELECT"
        ),
        SqlStatement(
            seq=1,
            sql="INSERT INTO events (a) VALUES (?)",
            table="events",
            verb="INSERT",
        ),
    ]
    assert api_table_matrix([rec])["load_table"] == {"entities": "R"}
