"""
Pytest suite for src/grant_scale.py — the grant-record scaling sweep.

No cluster required. The fake answers by INSPECTING THE SQL rather than by call
order: an order-keyed mock silently lies the moment the code under test skips a
query, which is exactly the branch (`index already absent`, `nothing to insert`)
these tests exist to cover.

The tests that matter most are the sentinel-range ones. The signed-off plan
specified `DELETE ... WHERE grantee_id >= 1_000_000_000`, and real Polaris ids
are ~10^18 — that predicate matches every real grant in the fixture.

Run: pytest test_grant_scale.py
"""

import sys
from pathlib import Path

import pytest

import grant_scale as gs  # noqa: E402

SCHEMA = "polaris_schema"
REALM = "POLARIS"

#: Real grantee ids observed on the cluster (from a task entity's serialized
#: payload). Snowflake-style, ~10^18 — the shape the sentinel must clear.
REAL_IDS = [7985247348701050877, 2490852191059560064, 77192520090151552]


class FakeCursor:
    def __init__(self, db):
        self.db = db
        self._result = None

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    @property
    def rowcount(self):
        return self.db.last_rowcount

    def execute(self, sql, params=None):
        self.db.log.append((sql, params))
        s = " ".join(sql.split())
        self.db.last_rowcount = -1

        # EXPLAIN first, and ANALYZE matched only as a leading keyword. An
        # `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` contains the substring
        # "ANALYZE", so a loose `elif "ANALYZE" in s` swallowed every
        # measurement and returned no plan at all. Second time in this one
        # dispatcher that a substring appeared in more statements than intended
        # — match on the distinguishing part, not on a word that happens to be
        # present.
        if "EXPLAIN" in s:
            self._result = [(self.db.next_plan(params),)]
        elif "INSERT INTO" in s and "generate_series" in s:
            self._insert(params)
        elif "DELETE FROM" in s and "grantee_id < 0" in s:
            keep = [r for r in self.db.rows if r[4] >= 0]
            self.db.last_rowcount = len(self.db.rows) - len(keep)
            self.db.rows = keep
        elif s.startswith("SET "):
            self.db.settings[s.split("=")[0].split()[-1].strip()] = s.split("=")[
                -1
            ].strip()
        elif s.startswith("ANALYZE "):
            self.db.analyzed += 1
            self.db.reltuples = len(self.db.rows)
        elif "DROP INDEX" in s:
            self.db.index = None
        elif "CREATE INDEX" in s:
            self.db.index = dict(self.db.index_build_state)
        elif "min(grantee_id)" in s and "grantee_id < 0" in s:
            # The filler EXTENTS query, not the safety check. Both start
            # `min(grantee_id)` and they return different arities — told apart
            # by which half of the id space they look at.
            neg = [r for r in self.db.rows if r[4] < 0]
            self._result = [
                (
                    min((r[4] for r in neg), default=None),
                    min((r[2] for r in neg), default=None),
                )
            ]
        elif "min(grantee_id)" in s:
            real = [r for r in self.db.rows if r[4] >= 0]
            self._result = [
                (
                    min((r[4] for r in real), default=None),
                    min((r[2] for r in real), default=None),
                    min((r[3] for r in real), default=None),
                    min((r[1] for r in real), default=None),
                )
            ]
        elif "GROUP BY 1, 2" in s:
            # Before the count(*) branches: this statement contains `count(*)`
            # too, and matching on it first returned a scalar where the caller
            # expected per-grantee rows.
            agg = {}
            for r in self.db.rows:
                if r[0] == (params[0] if params else REALM) and r[4] >= 0:
                    agg[(r[4], r[3])] = agg.get((r[4], r[3]), 0) + 1
            self._result = [(gid, gcat, n) for (gid, gcat), n in agg.items()]
        elif "count(*)" in s and "grantee_id < 0 OR securable_id < 0" in s:
            self._result = [(len([r for r in self.db.rows if r[4] < 0 or r[2] < 0]),)]
        elif "count(*)" in s and "grantee_id < 0" in s:
            self._result = [(len([r for r in self.db.rows if r[4] < 0]),)]
        elif "count(*)" in s:
            self._result = [(len(self.db.rows),)]
        elif "reltuples" in s:
            self._result = [(self.db.reltuples,)]
        elif "indisvalid" in s:
            ix = self.db.index
            self._result = [(ix["valid"], ix["ready"])] if ix else []
        else:  # pragma: no cover - an unhandled shape must be loud
            raise AssertionError(f"FakeCursor has no branch for: {s[:120]}")

    def _insert(self, p):
        """Three INSERT shapes share this branch — uniform bulk, one probe
        grantee, and a distribution band — told apart by their parameters."""
        before = len(self.db.rows)
        seen = {r[1:] for r in self.db.rows}

        def add(row):
            if row[1:] not in seen:  # ON CONFLICT DO NOTHING
                seen.add(row[1:])
                self.db.rows.append(row)

        if "lo" in p:  # uniform bulk filler
            for i in range(p["lo"], p["hi"] + 1):
                add(gs.filler_row(i, p["realm"], p["rpg"]))
        elif "ng" in p:  # one band of a shaped distribution
            for i in range(p["ng"]):
                for j in range(p["rows"]):
                    add(
                        (
                            p["realm"],
                            p["cat"],
                            -(p["sbase"] + i * p["rows"] + j),
                            p["cat"],
                            -(p["gbase"] + i),
                            (j % p["np"]) + 1,
                        )
                    )
        else:  # one probe grantee with an exact row count
            for i in range(1, p["n"] + 1):
                add((p["realm"], p["cat"], -i, p["cat"], p["gid"], (i % p["np"]) + 1))
        self.db.last_rowcount = len(self.db.rows) - before

    def fetchone(self):
        return self._result[0] if self._result else None

    def fetchall(self):
        return list(self._result or [])


class FakeDB:
    """grant_records as a list of six-column tuples, plus index state."""

    def __init__(self, real_rows=(), index=None, index_build_state=None):
        self.rows = list(real_rows)
        self.log = []
        self.analyzed = 0
        self.reltuples = len(self.rows)
        self.last_rowcount = -1
        self.settings = {}
        self.index = index
        self.index_build_state = index_build_state or {"valid": True, "ready": True}
        self.plan_ms = 1.0

    def next_plan(self, params):
        node = "Index Only Scan" if self.index else "Seq Scan"
        gid = params[0] if params else 0
        returned = len([r for r in self.rows if r[4] == gid])
        return [
            {
                "Plan": {
                    "Node Type": node,
                    "Actual Rows": returned,
                    "Rows Removed by Filter": (
                        len(self.rows) - returned if node == "Seq Scan" else 0
                    ),
                    "Total Cost": 810.16,
                    "Shared Hit Blocks": 285,
                    "Shared Read Blocks": 0,
                },
                "Execution Time": self.plan_ms,
            }
        ]

    def cursor(self):
        return FakeCursor(self)


def real_rows(n_grantees=3, per=2):
    """A handful of rows with realistic snowflake-scale ids."""
    out = []
    for g, gid in enumerate(REAL_IDS[:n_grantees]):
        for j in range(per):
            out.append((REALM, 10**18 + g, 10**18 + g * 100 + j, 10**18, gid, j + 1))
    return out


# ----------------------------------------------------------------------
# the sentinel range — the correction this module exists to encode
# ----------------------------------------------------------------------
def test_the_plans_sentinel_would_have_matched_every_real_grantee():
    """`PLAN-grant-scale-sweep.md` B1, pinned as the bug it was.

    It reserved ids `>= 1_000_000_000` for filler and removed them with
    `DELETE ... WHERE grantee_id >= 1000000000`. Polaris ids are snowflake-style
    and land around 10^18, so that predicate matches EVERY real grant. Running
    the documented cleanup would have deleted the fixture and left the synthetic
    rows behind.
    """
    assert all(i >= 1_000_000_000 for i in REAL_IDS), (
        "if this ever fails, real ids have moved and the plan's sentinel may be "
        "viable again — but re-derive it against live data, do not assume"
    )
    # What shipped instead: negative, which no id generator here produces.
    assert all(gs.filler_row(i, REALM)[4] < 0 for i in range(100))
    assert all(i >= 0 for i in REAL_IDS), "the deletion predicate depends on this"


def test_range_guard_passes_on_realistic_data():
    db = FakeDB(real_rows())
    info = gs.assert_filler_range_is_safe(db, SCHEMA)
    assert info["existing_filler_rows"] == 0


def test_range_guard_refuses_when_a_real_row_is_negative():
    """The one condition that makes `delete_filler` unsafe, caught before any
    insert rather than discovered by the DELETE."""
    db = FakeDB(real_rows() + [(REALM, -5, -5, -5, -5, 1)])
    db.rows[-1] = (REALM, 10**18, 10**18, 10**18, -1, 1)  # a REAL row, negative gid
    db.rows[-1] = (REALM, 10**18, -7, 10**18, 5, 1)  # negative securable, real grantee
    with pytest.raises(AssertionError, match="NEGATIVE id"):
        gs.assert_filler_range_is_safe(db, SCHEMA)


# ----------------------------------------------------------------------
# filler shape
# ----------------------------------------------------------------------
def test_filler_rows_have_unique_primary_keys():
    """The PK is all six columns; `securable_id` is what makes each row
    distinct. If it ever repeats, ON CONFLICT silently swallows the row and the
    table never reaches the requested size."""
    rows = [gs.filler_row(i, REALM) for i in range(5000)]
    assert len({r[1:] for r in rows}) == 5000


def test_filler_is_shaped_as_many_medium_grantees():
    """~50 rows per synthetic grantee, not one enormous one — a single fat
    grantee would make the index scan look far worse than production."""
    rows = [gs.filler_row(i, REALM, rows_per_grantee=50) for i in range(1000)]
    per = {}
    for r in rows:
        per[r[4]] = per.get(r[4], 0) + 1
    assert set(per.values()) == {50}
    assert len(per) == 20


def test_the_sql_and_the_python_mirror_have_not_drifted():
    """`filler_row` documents what the INSERT generates. The SQL is
    authoritative, so this pins the two together — a change to one that misses
    the other fails here rather than in a fixture that is quietly the wrong
    shape."""
    import inspect

    src = inspect.getsource(gs.insert_filler)
    assert "-(%(base)s + g.i)" in src, "securable_id expression changed"
    assert "-(%(base)s + (g.i / %(rpg)s))" in src, "grantee_id expression changed"
    assert "(g.i %% %(np)s) + 1" in src, "privilege_code expression changed"


def test_insert_then_delete_leaves_only_real_rows():
    db = FakeDB(real_rows())
    n_real = len(db.rows)
    gs.insert_filler(db, SCHEMA, REALM, 500)
    assert gs.total_rows(db, SCHEMA) == n_real + 500
    assert gs.filler_count(db, SCHEMA) == 500

    removed = gs.delete_filler(db, SCHEMA)
    assert removed == 500
    assert gs.total_rows(db, SCHEMA) == n_real
    assert all(r[4] >= 0 for r in db.rows), "a real row was deleted"


def test_insert_filler_is_a_noop_for_a_non_positive_request():
    db = FakeDB(real_rows())
    assert gs.insert_filler(db, SCHEMA, REALM, 0) == 0
    assert gs.insert_filler(db, SCHEMA, REALM, -100) == 0


# ----------------------------------------------------------------------
# index state
# ----------------------------------------------------------------------
def test_set_index_refuses_an_invalid_index():
    """Presence is not enough. An interrupted CREATE INDEX CONCURRENTLY leaves
    `indisvalid = false`: it passes an existence check and the planner never
    uses it, so the cell would measure unindexed behaviour under an "indexed"
    label."""
    db = FakeDB(real_rows(), index_build_state={"valid": False, "ready": True})
    with pytest.raises(AssertionError, match="not usable"):
        gs.set_index(db, SCHEMA, True)


def test_set_index_reaches_both_states():
    db = FakeDB(real_rows())
    built = gs.set_index(db, SCHEMA, True)
    assert built["state"] == {"present": True, "valid": True, "ready": True}
    assert built["seconds"] >= 0
    dropped = gs.set_index(db, SCHEMA, False)
    assert dropped["state"]["present"] is False


# ----------------------------------------------------------------------
# probes
# ----------------------------------------------------------------------
def test_a_filler_grantee_is_never_reported_as_the_fattest_identity():
    """Filler is excluded from probe selection. Otherwise a synthetic grantee
    could be promoted to "the fattest identity in the realm" and an artifact
    would become the headline."""
    db = FakeDB(real_rows(n_grantees=3, per=4))
    gs.insert_filler(db, SCHEMA, REALM, 5000)  # far more rows than any real one
    probes = gs.resolve_probes(db, SCHEMA, REALM, targets=("max",))
    assert probes[0]["grantee_id"] in REAL_IDS
    assert probes[0]["synthetic"] is False


def test_a_target_the_fixture_cannot_supply_is_marked_synthetic():
    """ "Closest" is only useful if it is close. 500 against a fixture whose
    largest grantee holds 2 is not a 500-row probe, and reporting it as one puts
    a fabricated point on the curve."""
    db = FakeDB(real_rows(per=2))
    probes = gs.resolve_probes(db, SCHEMA, REALM, targets=(500,))
    assert probes[0]["synthetic"] is True
    assert "SYNTHETIC" in probes[0]["label"]
    assert probes[0]["grantee_id"] == gs.PROBE_GRANTEE_ID


def test_a_target_the_fixture_does_supply_is_not_marked_synthetic():
    db = FakeDB(real_rows(per=2))
    probes = gs.resolve_probes(db, SCHEMA, REALM, targets=(2,))
    assert probes[0]["synthetic"] is False
    assert probes[0]["rows"] == 2


# ----------------------------------------------------------------------
# the grid
# ----------------------------------------------------------------------
def test_grid_refuses_descending_sizes():
    """Filler is only ever added. Partially removing it would leave the
    remaining grantees' row counts uneven and change what the probes mean."""
    with pytest.raises(ValueError, match="ascend"):
        gs.run_grid(FakeDB(), SCHEMA, REALM, sizes=[500, 100], probes=[])


def test_grid_measures_both_index_states_at_every_size():
    db = FakeDB(real_rows(per=2))
    probes = gs.resolve_probes(db, SCHEMA, REALM, targets=(2, "max"))
    cells = gs.run_grid(db, SCHEMA, REALM, sizes=[100, 300], probes=probes, k=3)

    assert len(cells) == 4, "2 sizes x 2 index states"
    assert [c["index_present"] for c in cells] == [False, True, False, True]
    assert db.analyzed == 2, "one ANALYZE per size change, and no more"
    for c in cells:
        assert c["exact_rows"] >= c["target_size"]
        assert len(c["measurements"]) == 2
    # The whole point: the plan shape flips with the index state.
    assert cells[0]["measurements"][0]["node"] == "Seq Scan"
    assert cells[1]["measurements"][0]["node"] == "Index Only Scan"


def test_speedups_pairs_each_probe_with_its_own_twin():
    db = FakeDB(real_rows(per=2))
    probes = gs.resolve_probes(db, SCHEMA, REALM, targets=(2,))
    cells = gs.run_grid(db, SCHEMA, REALM, sizes=[100], probes=probes, k=3)
    rows = gs.speedups(cells)
    assert len(rows) == 1
    r = rows[0]
    assert r["before_node"] == "Seq Scan" and r["after_node"] == "Index Only Scan"
    assert r["speedup"] == pytest.approx(r["before_ms"] / r["after_ms"])


# ----------------------------------------------------------------------
# the report
# ----------------------------------------------------------------------
def test_report_labels_synthetic_rows_and_carries_the_sentinel_warning():
    """Synthetic provenance is repeated in the table, not stated once in a
    preamble — a number quoted out of a table is quoted without the preamble."""
    db = FakeDB(real_rows(per=2))
    probes = gs.resolve_probes(db, SCHEMA, REALM, targets=(500,))
    gs.ensure_probe_grantee(db, SCHEMA, REALM, 500)
    cells = gs.run_grid(db, SCHEMA, REALM, sizes=[1000], probes=probes, k=3)

    md = gs.render_report(cells, {"generated_at": "now", "explain_n": 10})
    assert "SYNTHETIC" in md
    assert "⚠" in md
    assert "1_000_000_000" in md, "the corrected sentinel must be disclosed"
    assert "Index build cost" in md
    assert "reltuples" in md


def test_report_states_the_trend_rather_than_a_single_ratio():
    db = FakeDB(real_rows(per=2))
    probes = gs.resolve_probes(db, SCHEMA, REALM, targets=(2,))
    cells = gs.run_grid(db, SCHEMA, REALM, sizes=[1000, 4000], probes=probes, k=3)
    md = gs.render_report(cells, {"generated_at": "now", "explain_n": 10})
    assert "Seq Scan** went from" in md
    assert "point on that surface" in md


def test_two_synthetic_probes_get_distinct_grantees():
    """They shared one constant at first, so both wrote into grantee -1 and the
    smaller probe silently measured the larger one's row count — two points on
    the curve that were really one point, reported twice. The static harness
    caught it; this keeps it caught."""
    db = FakeDB(real_rows(per=2))
    probes = gs.resolve_probes(db, SCHEMA, REALM, targets=(50, 500))
    assert all(p["synthetic"] for p in probes)
    ids = [p["grantee_id"] for p in probes]
    assert len(set(ids)) == 2, f"synthetic probes collided on {ids}"
    assert all(i < 0 for i in ids)
    assert all(i > -gs.BULK_ID_BASE for i in ids), "must stay clear of bulk filler"


def test_each_synthetic_probe_holds_only_its_own_rows():
    db = FakeDB(real_rows(per=2))
    probes = gs.resolve_probes(db, SCHEMA, REALM, targets=(50, 500))
    for p in probes:
        gs.ensure_probe_grantee(db, SCHEMA, REALM, p["wanted"], p["grantee_id"])
    for p in probes:
        held = len([r for r in db.rows if r[4] == p["grantee_id"]])
        assert held == p["wanted"], f"{p['label']} holds {held}, wanted {p['wanted']}"


# ----------------------------------------------------------------------
# production shape without the API
# ----------------------------------------------------------------------
def test_production_shape_reproduces_the_measured_histogram():
    """Scaled from the real 1,000-user fixture, not invented.

    Measured there: 2,001 grantees hold 1 row, 1,000 hold 2 (catalog_admin),
    1,000 hold the granted privileges. The fattest identity is deliberately not
    a band — it comes through the probe axis, so there is one mechanism for "a
    grantee of size N" rather than two.
    """
    bands = dict((rows, n) for n, rows in gs.production_shape(1000, grants_per_role=50))
    assert bands[1] == 2002
    assert bands[2] == 1000
    assert bands[50] == 1000
    assert gs.shape_rows(gs.production_shape(1000, 50)) == 54_002
    # 10x the users is 10x the rows: the whole point of doing this in SQL.
    assert gs.shape_rows(gs.production_shape(10_000, 50)) == 540_002


def test_shaped_filler_produces_the_requested_distribution():
    db = FakeDB(real_rows(per=2))
    shape = [(5, 1), (3, 2), (2, 50)]
    res = gs.insert_shaped_filler(db, SCHEMA, REALM, shape)

    assert res["total"] == gs.shape_rows(shape) == 5 + 6 + 100
    per = {}
    for r in db.rows:
        if r[4] < 0:
            per[r[4]] = per.get(r[4], 0) + 1
    assert sorted(per.values()) == [1] * 5 + [2] * 3 + [50] * 2


def test_shaped_filler_bands_do_not_collide():
    """Disjoint grantee AND securable ranges per band. Overlapping securable ids
    would be swallowed by ON CONFLICT, leaving the table quietly short of the
    size the grid asked for."""
    db = FakeDB()
    shape = [(4, 3), (4, 3), (4, 3)]  # identical bands: the collision case
    res = gs.insert_shaped_filler(db, SCHEMA, REALM, shape)
    assert res["total"] == 36, "a band was swallowed by ON CONFLICT"
    assert len({r[1:] for r in db.rows}) == 36, "primary keys collided"
    assert len({r[4] for r in db.rows}) == 12, "grantee ids collided across bands"


def test_shaped_filler_stays_in_the_deletable_range():
    """Everything it writes must come out again with `grantee_id < 0` — the one
    predicate `delete_filler` uses."""
    db = FakeDB(real_rows(per=2))
    n_real = len(db.rows)
    gs.insert_shaped_filler(db, SCHEMA, REALM, gs.production_shape(20, 50))
    assert gs.delete_filler(db, SCHEMA) > 0
    assert len(db.rows) == n_real


def test_successive_shaped_inserts_are_additive():
    """The grid calls the filler once per size. A fixed id start meant the
    second call re-emitted the first call's primary keys, ON CONFLICT swallowed
    them, and the table stopped growing while every count still looked
    plausible."""
    db = FakeDB()
    shape = [(4, 3)]
    first = gs.insert_shaped_filler(db, SCHEMA, REALM, shape)
    second = gs.insert_shaped_filler(db, SCHEMA, REALM, shape)
    assert first["total"] == second["total"] == 12
    assert gs.filler_count(db, SCHEMA) == 24
    assert len({r[4] for r in db.rows}) == 8, "grantee ids collided between calls"


def test_grid_accepts_a_shaped_filler():
    db = FakeDB(real_rows(per=2))
    probes = gs.resolve_probes(db, SCHEMA, REALM, targets=(2,))
    calls = []

    def fill(conn, schema, realm, needed):
        calls.append(needed)
        return gs.insert_shaped_filler(
            conn, schema, realm, gs.production_shape(max(1, needed // 54), 50)
        )["total"]

    cells = gs.run_grid(
        db, SCHEMA, REALM, sizes=[600, 1200], probes=probes, k=3, fill=fill
    )
    assert len(calls) == 2, "the hook replaced the uniform filler at every size"
    assert len(cells) == 4
    assert cells[-1]["exact_rows"] > cells[0]["exact_rows"]


# ----------------------------------------------------------------------
# parallel plans — what the first live run exposed
# ----------------------------------------------------------------------
def _gather_plan(returned, filtered, loops=3):
    """A parallel Seq Scan, as PostgreSQL reports it: the filter counter lives
    on the scan BELOW the Gather, and is per worker."""
    return {
        "Plan": {
            "Node Type": "Gather",
            "Actual Rows": returned,
            "Total Cost": 11171.05,
            "Shared Hit Blocks": 5714,
            "Shared Read Blocks": 0,
            "Plans": [
                {
                    "Node Type": "Seq Scan",
                    "Parallel Aware": True,
                    "Actual Rows": returned // loops,
                    "Actual Loops": loops,
                    "Rows Removed by Filter": filtered // loops,
                }
            ],
        },
        "Execution Time": 240.786,
    }


def test_scan_node_looks_below_a_gather():
    """The live run reported `rows_filtered: None` for every parallel cell,
    because the counter is on the scan and the code read the root. That discard
    ratio is the clock-independent evidence the whole audit rests on."""
    plan = _gather_plan(999, 600_000)
    assert gs.scan_node(plan)["Node Type"] == "Seq Scan"
    assert gs.plan_path(plan) == "Gather > Seq Scan"
    # A non-parallel plan still resolves to itself.
    flat = {"Plan": {"Node Type": "Seq Scan", "Actual Rows": 1}}
    assert gs.scan_node(flat)["Node Type"] == "Seq Scan"


def test_measure_recovers_per_worker_counters(monkeypatch):
    monkeypatch.setattr(
        gs.api_trace,
        "explain_n",
        lambda *a, **k: (240.786, 1.0, 999.0, _gather_plan(999, 600_000), []),
    )
    m = gs.measure(
        FakeDB(),
        SCHEMA,
        REALM,
        {"label": "x", "grantee_id": 1, "grantee_catalog_id": 0},
    )
    assert m["rows_returned"] == 999, "the root already aggregates these"
    # Integer division means the recovered total is approximate, not exact --
    # PostgreSQL reports the per-worker average rounded. Close enough to carry
    # a discard ratio; not a row count to quote to the unit.
    assert m["rows_filtered"] == 600_000, "per-worker counters x Actual Loops"
    assert m["parallel"] is True
    assert m["scan_node"] == "Seq Scan"
    assert m["node"] == "Gather"


def test_report_keeps_the_trend_line_when_the_plan_goes_parallel():
    """Matching `startswith("Seq")` dropped this bullet the moment the root
    became `Gather` — losing the most important line exactly when the table got
    interesting."""
    cells = [
        {
            "target_size": s,
            "exact_rows": s,
            "reltuples": s,
            "filler_rows": 0,
            "index_present": present,
            "index_build_seconds": 1.0 if present else None,
            "measurements": [
                {
                    "label": "p",
                    "synthetic": False,
                    "rows_returned": 1,
                    "rows_filtered": s - 1,
                    "path": "Gather > Seq Scan",
                    "node": "Gather" if not present else "Index Only Scan",
                    "scan_node": "Seq Scan",
                    "parallel": not present,
                    "total_cost": 1000.0 * s,
                    "shared_hit": s // 100,
                    "shared_read": 0,
                    "ms": 10.0 * s if not present else 0.02,
                    "min": 1.0,
                    "max": 2.0,
                }
            ],
        }
        for s in (100, 400)
        for present in (False, True)
    ]
    md = gs.render_report(cells, {"generated_at": "now", "explain_n": 10})
    assert "went from" in md, "the trend bullet vanished on a parallel plan"
    assert "PARALLEL sequential scan" in md, "the escalation must be reported"
    assert "Do not quote a speedup" in md
    assert "clock-independent evidence" in md


def test_set_parallelism_pins_the_session():
    db = FakeDB()
    assert gs.set_parallelism(db, 0) == 0
    assert db.settings["max_parallel_workers_per_gather"] == "0"
    gs.set_parallelism(db, 4)
    assert db.settings["max_parallel_workers_per_gather"] == "4"
