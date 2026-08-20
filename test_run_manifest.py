"""Mocked tests for src/run_manifest.py -- no cluster, no filesystem outside tmp."""

import json
import pathlib

import pytest

import run_manifest as rm


def _manifest():
    return {
        "schema": "polaris_schema",
        "index": {"name": "idx_grant_records_grantee", "left_in_place": True},
        "fixture": {"exact_counts": {"entities": 7273, "grant_records": 30009}},
    }


class _Cur:
    """Answers by inspecting the SQL, not by call order.

    An order-keyed mock silently lies as soon as the code under test skips a
    query -- which is exactly the `left_in_place=False` path, where the index
    probe never runs and the first cursor is a count(*).
    """

    def __init__(self, conn):
        self._conn = conn
        self._row = None

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, q, p=None):
        if "pg_index" in q:
            self._row = self._conn.index_row
        else:
            table = q.rsplit(".", 1)[-1].strip()
            self._row = (self._conn.counts[table],)

    def fetchone(self):
        return self._row


class _Conn:
    def __init__(self, index_row, counts):
        self.index_row = index_row
        self.counts = counts

    def cursor(self):
        return _Cur(self)


COUNTS = {"entities": 7273, "grant_records": 30009}


def test_run_ids_sort_lexicographically_so_latest_is_max():
    assert rm.new_run_id.__doc__
    ids = ["20260820-090000", "20260820-145705", "20260119-235959"]
    assert max(ids) == "20260820-145705"


def test_write_list_and_load_latest(tmp_path):
    rm.write_run(tmp_path, "20260820-100000", _manifest())
    rm.write_run(tmp_path, "20260820-120000", _manifest())
    assert rm.list_runs(tmp_path) == ["20260820-100000", "20260820-120000"]
    run_id, payload = rm.load_run(tmp_path)
    assert run_id == "20260820-120000"
    assert payload["run_id"] == "20260820-120000"
    assert payload["written_at"]


def test_load_explicit_run(tmp_path):
    rm.write_run(tmp_path, "20260820-100000", _manifest())
    rm.write_run(tmp_path, "20260820-120000", _manifest())
    run_id, _ = rm.load_run(tmp_path, "20260820-100000")
    assert run_id == "20260820-100000"


def test_overwriting_a_recorded_run_is_refused(tmp_path):
    rm.write_run(tmp_path, "20260820-100000", _manifest())
    with pytest.raises(FileExistsError):
        rm.write_run(tmp_path, "20260820-100000", _manifest())


def test_missing_run_and_empty_dir_raise(tmp_path):
    with pytest.raises(FileNotFoundError):
        rm.load_run(tmp_path)
    rm.write_run(tmp_path, "20260820-100000", _manifest())
    with pytest.raises(FileNotFoundError):
        rm.load_run(tmp_path, "nope")


def test_diff_live_clean_when_cluster_matches():
    conn = _Conn((True, True), COUNTS)
    assert rm.diff_live(conn, _manifest()) == []


def test_diff_live_flags_absent_index():
    conn = _Conn(None, COUNTS)
    problems = rm.diff_live(conn, _manifest())
    assert any("ABSENT" in p for p in problems)


def test_diff_live_flags_invalid_index():
    """indisvalid=false is the interrupted-CONCURRENTLY case: present but unused."""
    conn = _Conn((False, True), COUNTS)
    problems = rm.diff_live(conn, _manifest())
    assert any("INVALID" in p for p in problems)


def test_diff_live_flags_row_drift_and_reports_the_delta():
    conn = _Conn((True, True), {**COUNTS, 'entities': 7280})
    problems = rm.diff_live(conn, _manifest())
    assert any("+7" in p and "entities" in p for p in problems)


def test_tolerance_absorbs_small_drift():
    conn = _Conn((True, True), {**COUNTS, 'entities': 7280})
    assert rm.diff_live(conn, _manifest(), tolerance=10) == []


def test_index_not_checked_when_not_left_in_place():
    m = _manifest()
    m["index"]["left_in_place"] = False
    conn = _Conn(None, COUNTS)
    assert rm.diff_live(conn, m) == []


def test_require_live_match_raises_listing_every_problem():
    conn = _Conn(None, {**COUNTS, 'entities': 9999})
    with pytest.raises(AssertionError) as e:
        rm.require_live_match(conn, _manifest())
    msg = str(e.value)
    assert "ABSENT" in msg and "entities" in msg


def test_require_live_match_returns_true_when_clean():
    conn = _Conn((True, True), COUNTS)
    assert rm.require_live_match(conn, _manifest()) is True
