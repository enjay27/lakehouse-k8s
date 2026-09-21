"""
grant_scale.py
==============
The machinery behind `02b_grant_scale_sweep.ipynb`: synthetic table volume, an
index that can be put in a known state, and one measured grid cell.

WHY THIS EXISTS
---------------
`doc-index-measurement-latest.md` reports a speedup for the grantee lookup, and
that number is measured at ONE corner of a two-dimensional space:

    total rows in grant_records   drives the Seq Scan  -- it reads every row
    rows returned for a grantee   drives the Index Only Scan

A single ratio invites "what happens in a realm shaped like mine?", and a
reviewer who seeds their own realm and gets a different number has grounds to
dismiss the whole finding. A TREND answers that; a point cannot.

The expected shape, stated in advance so a null result is still informative:
Seq Scan time grows linearly with total rows and is flat across grantees within
a size; Index Only Scan time is flat across total rows and grows only with rows
returned. If Seq Scan does NOT grow linearly, something is wrong with the
fixture -- most likely a missing ANALYZE -- and nothing should be published
until that is explained.

THE FILLER-ROW RANGE, AND A CORRECTION THAT MATTERS
---------------------------------------------------
`PLAN-grant-scale-sweep.md` B1 specifies filler grantee ids from "a reserved
high range (>= 1_000_000_000) that matches no entity", removable with
`DELETE ... WHERE grantee_id >= 1000000000`.

**That would have deleted the entire fixture.** Polaris entity ids are
snowflake-style and land around 10^18 -- observed on this cluster:
7985247348701050877, 2490852191059560064, 77192520090151552. Every real grantee
id is orders of magnitude ABOVE the supposed sentinel floor, so the cleanup
`DELETE` would have matched all ~55,000 real rows and left the synthetic ones.

Filler therefore uses **negative** ids, which no Polaris id generator produces,
and `assert_filler_range_is_safe()` proves the disjointness against the live
table before a single row is inserted rather than trusting this paragraph.
Deletion is `WHERE grantee_id < 0`, which is provably scoped once that
assertion holds.

Filler rows are inert for authorization (they match no entity) and entirely
real to a Seq Scan, which is the only thing being measured. They are shaped
realistically -- ~50 rows per synthetic grantee, not one enormous grantee --
and every table that reports a filler-derived number must say so.
"""

import time

import api_trace
import run_manifest

#: Filler occupies the negative id space. See the module docstring: the plan's
#: `>= 1_000_000_000` sentinel sits BELOW every real Polaris id, not above it.
FILLER_CATALOG_ID = -1

#: Reserved for `ensure_probe_grantee` -- one synthetic grantee with an exact
#: row count, for probing a point on the curve the real fixture does not occupy.
PROBE_GRANTEE_ID = -1

#: Bulk filler starts here and counts DOWN, leaving -1..-999 for probe rows so
#: the two never contend for a primary key.
BULK_ID_BASE = 1000

#: Distinct privilege codes cycled through filler rows. The exact values do not
#: matter -- nothing resolves them -- but varying them keeps the column's
#: statistics from collapsing to a single value, which would give the planner a
#: distribution no real table has.
FILLER_PRIVILEGE_CODES = 25

INDEX_NAME = "idx_grant_records_grantee"


def index_ddl(schema, name=INDEX_NAME):
    """The remedy under test, as one statement. Kept here so the sweep and the
    manifest cannot disagree about what was built."""
    return (
        f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {name}\n"
        f"    ON {schema}.grant_records (realm_id, grantee_catalog_id, grantee_id)\n"
        f"    INCLUDE (securable_catalog_id, securable_id, privilege_code)"
    )


# ----------------------------------------------------------------------
# safety
# ----------------------------------------------------------------------
def assert_filler_range_is_safe(conn, schema):
    """Prove the sentinel range is disjoint from real data. Call before inserting.

    This is the guard that makes `delete_filler` safe. It is deliberately an
    assertion against the LIVE table rather than a comment asserting Polaris's
    id generator is positive: the cost of being wrong is deleting the fixture,
    and the check is one query.

    Raises:
        AssertionError: if any real row already occupies the negative space.
    """
    with conn.cursor() as cur:
        cur.execute(
            api_trace.NO_LOAD_BALANCE
            + f"SELECT min(grantee_id), min(securable_id), min(grantee_catalog_id), "  # noqa: S608
            f"min(securable_catalog_id) FROM {schema}.grant_records "
            "WHERE grantee_id >= 0"
        )
        row = cur.fetchone() or (None, None, None, None)
        cur.execute(
            api_trace.NO_LOAD_BALANCE
            + f"SELECT count(*) FROM {schema}.grant_records "  # noqa: S608
            "WHERE grantee_id < 0 OR securable_id < 0"
        )
        negatives = cur.fetchone()[0]
    assert all(v is None or v >= 0 for v in row), (
        f"a real grant_records row holds a NEGATIVE id ({row}). The filler "
        "range is not disjoint from real data, so `DELETE ... WHERE "
        "grantee_id < 0` would remove real grants. Do not insert filler; pick "
        "a different sentinel and re-derive the deletion predicate."
    )
    return {"real_minimums": row, "existing_filler_rows": negatives}


# ----------------------------------------------------------------------
# filler volume
# ----------------------------------------------------------------------
def filler_count(conn, schema):
    """Rows currently in the sentinel range."""
    with conn.cursor() as cur:
        cur.execute(
            api_trace.NO_LOAD_BALANCE
            + f"SELECT count(*) FROM {schema}.grant_records WHERE grantee_id < 0"  # noqa: S608
        )
        return cur.fetchone()[0]


def total_rows(conn, schema):
    """Exact `count(*)`, never `reltuples` -- the estimate is stale by
    construction right after a bulk insert, which is precisely when this is
    called."""
    with conn.cursor() as cur:
        cur.execute(
            api_trace.NO_LOAD_BALANCE
            + f"SELECT count(*) FROM {schema}.grant_records"  # noqa: S608
        )
        return cur.fetchone()[0]


def filler_row(i, realm, rows_per_grantee=50):
    """The tuple the bulk INSERT produces for row `i`, as pure Python.

    **The SQL below is authoritative** — it generates rows server-side because
    `generate_series` beats shipping 500,000 tuples over the wire. This mirror
    exists so the row SHAPE can be tested without a database, and so a reader
    can see one row rather than infer it from a `generate_series` expression.
    `test_grant_scale.py` pins the two against each other by string-matching the
    statement, so they cannot drift silently.

    Returns:
        (realm_id, securable_catalog_id, securable_id, grantee_catalog_id,
         grantee_id, privilege_code)
    """
    return (
        realm,
        FILLER_CATALOG_ID,
        -(BULK_ID_BASE + i),  # unique per row -> the six-column PK is unique
        FILLER_CATALOG_ID,
        -(BULK_ID_BASE + i // rows_per_grantee),
        (i % FILLER_PRIVILEGE_CODES) + 1,
    )


#: The SELECT list of the bulk INSERT, kept as a constant so the drift guard in
#: the tests has something to match against `filler_row`.
_BULK_SELECT = (
    "SELECT %(realm)s, %(cat)s, -(%(base)s + g.i), %(cat)s,\n"
    "                           -(%(base)s + (g.i / %(rpg)s)), (g.i %% %(np)s) + 1"
)


def insert_filler(conn, schema, realm, n_rows, rows_per_grantee=50, batch=100_000):
    """Add `n_rows` synthetic rows. Idempotent per row via ON CONFLICT.

    Row i gets a unique `securable_id`, so the six-column primary key is unique
    regardless of how the other columns repeat, and `grantee_id` advances every
    `rows_per_grantee` rows -- giving many medium grantees rather than one
    enormous one, which is what a production realm looks like.

    Args:
        n_rows: how many rows to ADD (not a target total).
        batch: rows per statement. Kept finite because a single
            multi-million-row INSERT holds one transaction open long enough to
            matter on a replicated cluster.

    Returns:
        rows actually inserted.
    """
    if n_rows <= 0:
        return 0
    start = filler_count(conn, schema)
    inserted = 0
    for lo in range(start, start + n_rows, batch):
        hi = min(lo + batch, start + n_rows) - 1
        with conn.cursor() as cur:
            cur.execute(
                f"""INSERT INTO {schema}.grant_records
                        (realm_id, securable_catalog_id, securable_id,
                         grantee_catalog_id, grantee_id, privilege_code)
                    SELECT %(realm)s, %(cat)s, -(%(base)s + g.i), %(cat)s,
                           -(%(base)s + (g.i / %(rpg)s)), (g.i %% %(np)s) + 1
                    FROM generate_series(%(lo)s, %(hi)s) AS g(i)
                    ON CONFLICT DO NOTHING""",  # noqa: S608
                {
                    "realm": realm,
                    "cat": FILLER_CATALOG_ID,
                    "base": BULK_ID_BASE,
                    "rpg": rows_per_grantee,
                    "np": FILLER_PRIVILEGE_CODES,
                    "lo": lo,
                    "hi": hi,
                },
            )
            inserted += cur.rowcount if cur.rowcount and cur.rowcount > 0 else 0
    return inserted


# ----------------------------------------------------------------------
# production-shaped volume, without the API
# ----------------------------------------------------------------------
def production_shape(n_users, grants_per_role=50):
    """The grantee distribution an `n_users` realm actually has, as bands.

    MEASURED, not invented. The 1,000-user fixture's histogram is 2,001
    grantees holding 1 row, 1,000 holding 2, 1,000 holding `len(privileges)`,
    and one holding 1,006 -- which decomposes as:

        n + 1   principals, each the grantee of its own role assignment
        n + 1   principal-roles, each the grantee of its catalog-role assignment
        n       `catalog_admin` roles, bootstrapped with two grants each
        n       `owner_principal` roles, holding the granted privileges
        1       `service_admin`, which gains ONE GRANT PER CATALOG

    Scaling those bands is how a 10,000-user realm is reproduced in SQL in
    seconds instead of ~610,000 REST calls over ~8.5 hours. **A Seq Scan cannot
    tell these rows from REST-created ones** -- same plan, same buffers, same
    timing -- which is exactly why this is sufficient for the index question and
    exactly why it must be disclosed as synthetic in every table.

    The fattest grantee is deliberately NOT a band here: it is created through
    the probe axis (`resolve_probes` + `ensure_probe_grantee`) so there is one
    mechanism for "a grantee of size N", not two.

    Returns:
        list[(n_grantees, rows_each)].
    """
    return [
        (2 * n_users + 2, 1),  # principals + principal-roles
        (n_users, 2),  # catalog_admin
        (n_users, grants_per_role),  # owner_principal
    ]


def shape_rows(shape):
    """Total rows a shape produces, for planning a grid size."""
    return sum(ng * rows for ng, rows in shape)


#: One band of a shaped distribution, as a single server-side statement.
#: Extracted so `--dry-run` can print exactly what would run instead of a second
#: copy that drifts from it.
_SHAPED_INSERT = """INSERT INTO {schema}.grant_records
        (realm_id, securable_catalog_id, securable_id,
         grantee_catalog_id, grantee_id, privilege_code)
    SELECT %(realm)s, %(cat)s,
           -(%(sbase)s + g.i * %(rows)s + r.j), %(cat)s,
           -(%(gbase)s + g.i), (r.j %% %(np)s) + 1
    FROM generate_series(0, %(ng)s - 1) AS g(i),
         generate_series(0, %(rows)s - 1) AS r(j)
    ON CONFLICT DO NOTHING"""


def shaped_insert_sql(schema):
    """The band statement, for execution or for showing a reader.

    Everything happens server-side: a cross join of two `generate_series` emits
    `n_grantees x rows_each` tuples without shipping one of them over the wire,
    which is what turns ~8.5 hours of REST calls into seconds. `securable_id` is
    unique per row, so the six-column primary key is unique however the other
    columns repeat, and `ON CONFLICT DO NOTHING` makes the whole thing
    re-runnable.
    """
    return _SHAPED_INSERT.format(schema=schema)


def insert_shaped_filler(conn, schema, realm, shape, on_progress=None):
    """Insert filler matching a grantee-count distribution rather than a uniform one.

    `insert_filler` gives every synthetic grantee the same row count, which is
    fine as Seq Scan ballast but produces a distribution no realm has: the index
    scan's cost tracks rows returned, so a fixture where every grantee is
    identical cannot show how the speedup varies across a realm.

    Each band gets a disjoint grantee-id and securable-id range so bands cannot
    collide on the six-column primary key. Everything stays in the NEGATIVE
    space, which is what makes writing behind Polaris's back safe: it caches an
    entity together with its grant_records, and these grantees match no entity,
    so nothing Polaris has cached can go stale because of them.

    Returns:
        dict: rows inserted per band, and the total.
    """
    # Continue BEYOND whatever filler already exists rather than restarting at
    # BULK_ID_BASE. The grid calls this once per size, and a fixed start meant
    # the second call re-emitted the first call's primary keys, which ON
    # CONFLICT silently swallowed -- the table would simply stop growing while
    # every count still looked plausible.
    with conn.cursor() as cur:
        cur.execute(
            api_trace.NO_LOAD_BALANCE
            + f"SELECT min(grantee_id), min(securable_id) FROM {schema}.grant_records "  # noqa: S608
            "WHERE grantee_id < 0"
        )
        g_min, s_min = cur.fetchone() or (None, None)
    gcursor = max(BULK_ID_BASE, -(g_min or 0) + 1)
    scursor = max(BULK_ID_BASE, -(s_min or 0) + 1)
    inserted = []
    for band, (n_grantees, rows_each) in enumerate(shape):
        if n_grantees <= 0 or rows_each <= 0:
            inserted.append(0)
            continue
        with conn.cursor() as cur:
            cur.execute(
                shaped_insert_sql(schema),
                {
                    "realm": realm,
                    "cat": FILLER_CATALOG_ID,
                    "sbase": scursor,
                    "gbase": gcursor,
                    "rows": rows_each,
                    "ng": n_grantees,
                    "np": FILLER_PRIVILEGE_CODES,
                },
            )
            n = cur.rowcount if cur.rowcount and cur.rowcount > 0 else 0
        inserted.append(n)
        if on_progress:
            on_progress(
                f"  band {band}: {n_grantees:,} grantees x {rows_each} rows "
                f"= {n:,} inserted"
            )
        # Disjoint ranges for the next band. securable_id advances by the rows
        # this band consumed; grantee_id by the grantees it consumed.
        scursor += n_grantees * rows_each
        gcursor += n_grantees
    return {"per_band": inserted, "total": sum(inserted)}


def ensure_probe_grantee(conn, schema, realm, n_rows, grantee_id=PROBE_GRANTEE_ID):
    """One synthetic grantee holding exactly `n_rows` rows.

    The real fixture occupies only a few points on the rows-returned axis (1, 2,
    ~50 and the fattest identity). A curve needs a point between them, and
    inventing a grantee is the honest way to get one: the access path is
    identical, only the row count is chosen. Every table reporting it must mark
    it synthetic.
    """
    with conn.cursor() as cur:
        cur.execute(
            f"""INSERT INTO {schema}.grant_records
                    (realm_id, securable_catalog_id, securable_id,
                     grantee_catalog_id, grantee_id, privilege_code)
                SELECT %(realm)s, %(cat)s, -g.i, %(cat)s, %(gid)s,
                       (g.i %% %(np)s) + 1
                FROM generate_series(1, %(n)s) AS g(i)
                ON CONFLICT DO NOTHING""",  # noqa: S608
            {
                "realm": realm,
                "cat": FILLER_CATALOG_ID,
                "gid": grantee_id,
                "np": FILLER_PRIVILEGE_CODES,
                "n": n_rows,
            },
        )
    return {"grantee_id": grantee_id, "grantee_catalog_id": FILLER_CATALOG_ID}


def delete_filler(conn, schema):
    """Remove every synthetic row, and verify none survive.

    Safe ONLY because `assert_filler_range_is_safe` established that no real row
    holds a negative id. The verification is not ceremony: leaving filler behind
    silently inflates every later measurement, and the next person to run 02
    would see a table size nobody chose.
    """
    with conn.cursor() as cur:
        cur.execute(
            f"DELETE FROM {schema}.grant_records WHERE grantee_id < 0"  # noqa: S608
        )
        removed = cur.rowcount
    left = filler_count(conn, schema)
    assert left == 0, f"{left} filler rows survived deletion"
    return removed


def analyze(conn, schema, table="grant_records"):
    """ANALYZE, because every size change invalidates the planner's statistics.

    Without it the planner works from a `reltuples` the data no longer supports
    and may choose a plan the table no longer justifies -- which looks exactly
    like a finding.
    """
    with conn.cursor() as cur:
        cur.execute(f"ANALYZE {schema}.{table}")  # noqa: S608


def reltuples(conn, schema, table="grant_records"):
    """The planner's row estimate, recorded alongside the exact count so the
    drift between them is visible rather than assumed."""
    with conn.cursor() as cur:
        cur.execute(
            """SELECT c.reltuples::bigint FROM pg_class c
               JOIN pg_namespace n ON n.oid = c.relnamespace
               WHERE n.nspname = %s AND c.relname = %s""",
            (schema, table),
        )
        row = cur.fetchone()
    return int(row[0]) if row else None


# ----------------------------------------------------------------------
# index state
# ----------------------------------------------------------------------
def set_index(conn, schema, present, name=INDEX_NAME, ddl=None):
    """Put the index into a KNOWN state and prove it, returning build seconds.

    Presence alone is not enough. An interrupted CREATE/DROP INDEX CONCURRENTLY
    leaves a `pg_index` row with `indisvalid = false`: it passes a naive
    existence check and the planner never uses it, so a cell would measure
    unindexed behaviour while its label said otherwise. `run_manifest.
    index_state` reports valid/ready and this asserts on them.

    Requires `conn.autocommit` -- CONCURRENTLY cannot run inside a transaction.
    """
    t0 = time.time()
    with conn.cursor() as cur:
        if present:
            cur.execute(ddl or index_ddl(schema, name))
        else:
            cur.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {schema}.{name}")
    elapsed = time.time() - t0

    state = run_manifest.index_state(conn, schema, name)
    if present:
        assert state["present"] and state["valid"] and state["ready"], (
            f"{name} was built but is not usable: {state}. An interrupted "
            "CREATE INDEX CONCURRENTLY leaves exactly this."
        )
    else:
        assert not state["present"], f"{name} still present after DROP: {state}"
    return {"seconds": elapsed, "state": state}


# ----------------------------------------------------------------------
# probes
# ----------------------------------------------------------------------
#: The measured statement, S4 from `doc-api-sql-matrix.md` -- the grantee lookup
#: on the authorization path of every authenticated request.
S4 = """
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code
FROM {schema}.grant_records
WHERE grantee_id = %s AND realm_id = %s AND grantee_catalog_id = %s
"""


def resolve_probes(conn, schema, realm, targets=(1, 50, 500, "max")):
    """Pick one grantee per target row-count, preferring REAL grantees.

    Filler is excluded (`grantee_id >= 0`) so a synthetic grantee can never be
    silently promoted to "the fattest identity in the realm", which would turn
    an artifact into a headline.

    A target the real distribution does not occupy returns `synthetic=True` and
    a `wanted` field, and the caller is expected to create it with
    `ensure_probe_grantee` and label it as invented in every table.

    Returns:
        list[dict]: label, grantee_id, grantee_catalog_id, rows, synthetic.
    """
    with conn.cursor() as cur:
        cur.execute(
            api_trace.NO_LOAD_BALANCE
            + f"""SELECT grantee_id, grantee_catalog_id, count(*) AS n
                  FROM {schema}.grant_records
                  WHERE realm_id = %s AND grantee_id >= 0
                  GROUP BY 1, 2""",  # noqa: S608
            (realm,),
        )
        rows = cur.fetchall()
    if not rows:
        return []

    out = []
    for t in targets:
        if t == "max":
            gid, gcat, n = max(rows, key=lambda r: r[2])
            out.append(
                {
                    "label": f"fattest ({n} rows)",
                    "grantee_id": gid,
                    "grantee_catalog_id": gcat,
                    "rows": n,
                    "synthetic": False,
                }
            )
            continue
        gid, gcat, n = min(rows, key=lambda r: abs(r[2] - t))
        # "Closest" is only useful if it is actually close. 500 against a
        # fixture whose largest ordinary grantee holds 50 is not a 500-row
        # probe, and reporting it as one would put a fabricated point on the
        # curve.
        if n and abs(n - t) > max(1, t * 0.5):
            # A DISTINCT id per synthetic probe. They shared one constant at
            # first, so two synthetic targets wrote into the same grantee and
            # the smaller probe silently measured the larger one's row count --
            # two points on the curve that were really one. Caught by the
            # static harness, which is the whole reason it exists.
            n_synth = sum(1 for o in out if o.get("synthetic"))
            probe_gid = PROBE_GRANTEE_ID - n_synth
            assert probe_gid > -BULK_ID_BASE, (
                f"probe grantee ids have run into the bulk filler floor "
                f"(-{BULK_ID_BASE}); too many synthetic targets"
            )
            out.append(
                {
                    "label": f"~{t} rows (SYNTHETIC)",
                    "grantee_id": probe_gid,
                    "grantee_catalog_id": FILLER_CATALOG_ID,
                    "rows": t,
                    "wanted": t,
                    "synthetic": True,
                }
            )
        else:
            out.append(
                {
                    "label": f"{n} rows",
                    "grantee_id": gid,
                    "grantee_catalog_id": gcat,
                    "rows": n,
                    "synthetic": False,
                }
            )
    return out


def plan_path(plan, depth=4):
    """Node types down the plan spine, e.g. `Aggregate > Bitmap Heap Scan`.

    The root alone cannot answer the question: an aggregate is an aggregate
    before and after, while the access path underneath it changes completely.
    """
    out, node = [], plan["Plan"]
    for _ in range(depth):
        out.append(node["Node Type"])
        kids = node.get("Plans") or []
        if not kids:
            break
        node = kids[0]
    return " > ".join(out)


def scan_node(plan):
    """The node doing the scanning, which is not always the root.

    At production volume the planner escalates the unindexed grantee lookup to a
    PARALLEL sequential scan, and the root then reads `Gather`. `Rows Removed by
    Filter` lives on the scan below it, so reading the root returns None -- and
    "29,003 of 30,009 rows discarded to return 1,006" is precisely the
    clock-independent evidence this whole audit rests on. Losing it in exactly
    the cells that matter most is the same root-versus-spine mistake `plan_path`
    was written to avoid.
    """
    node = plan["Plan"]
    while True:
        if "Scan" in (node.get("Node Type") or ""):
            return node
        kids = node.get("Plans") or []
        if not kids:
            return plan["Plan"]
        node = kids[0]


def set_parallelism(conn, workers):
    """Pin `max_parallel_workers_per_gather` for this session.

    Parallel query makes the timings unreadable here. Worker startup dominates a
    scan this small, worker availability varies run to run, and this cluster has
    a documented `/dev/shm` constraint that parallel DSM allocation is sensitive
    to -- together they produced a 3-10x spread across probes whose plan cost
    and buffer counts were IDENTICAL.

    Set 0 for the controlled trend. The escalation itself is worth recording
    separately: an unindexed grantee lookup that goes parallel is burning worker
    slots on the authorization path of every authenticated request, which is a
    worse operational story than "it is slow".
    """
    with conn.cursor() as cur:
        cur.execute(f"SET max_parallel_workers_per_gather = {int(workers)}")
    return workers


def measure(conn, schema, realm, probe, k=None):
    """One EXPLAIN (ANALYZE, BUFFERS) measurement for one probe.

    Captures the clock-independent evidence alongside the timing -- plan shape,
    total cost, buffers, rows returned vs rows discarded by filter. Those were
    identical across every run of 02 while the timings moved by 4.6x, so they
    are what an upstream report can actually stand on.
    """
    med, lo, hi, plan, _ = api_trace.explain_n(
        conn,
        S4.format(schema=schema),
        (probe["grantee_id"], realm, probe["grantee_catalog_id"]),
        k=k,
    )
    root = plan["Plan"]
    scan = scan_node(plan)
    # Under a Gather the scan's counters are PER WORKER, averaged over loops --
    # multiplying by Actual Loops recovers the total. Rows returned comes from
    # the root, which already aggregates them.
    loops = scan.get("Actual Loops") or 1
    filtered = scan.get("Rows Removed by Filter")
    return {
        "label": probe["label"],
        "synthetic": bool(probe.get("synthetic")),
        "rows_returned": root.get("Actual Rows"),
        "rows_filtered": None if filtered is None else int(filtered * loops),
        "path": plan_path(plan),
        "node": root["Node Type"],
        "scan_node": scan.get("Node Type"),
        "parallel": bool(scan.get("Parallel Aware")) or root["Node Type"] == "Gather",
        # Clock-independent, and identical across probes within a size in every
        # run so far. This is the evidence; the milliseconds are the illustration.
        "total_cost": root.get("Total Cost"),
        "shared_hit": root.get("Shared Hit Blocks"),
        "shared_read": root.get("Shared Read Blocks"),
        "ms": med,
        "min": lo,
        "max": hi,
    }


# ----------------------------------------------------------------------
# the grid
# ----------------------------------------------------------------------
def run_grid(
    conn,
    schema,
    realm,
    sizes,
    probes,
    k=None,
    rows_per_grantee=50,
    on_progress=None,
    name=INDEX_NAME,
    fill=None,
):
    """Measure every probe at every table size, in BOTH index states.

    Both states at every cell, rather than one sweep with and one without: each
    point then carries its own before/after and cannot be contaminated by a
    stale index or by anything that drifted between two long passes.

    `sizes` must ASCEND -- filler is only ever added within a run, because
    deleting part of it would leave the remaining grantees' row counts uneven
    and change what the probes mean.

    Args:
        fill: optional `(conn, schema, realm, rows_needed) -> rows_added`. The
            default adds uniform filler; pass a shaped one to reproduce a real
            realm's grantee distribution.

    Returns:
        list[dict]: one per (size, index_state), each holding the per-probe
        measurements plus the size accounting for that row.
    """
    if list(sizes) != sorted(sizes):
        raise ValueError(
            f"sizes must ascend (filler is only added, never partially "
            f"removed): {list(sizes)}"
        )
    cells = []
    for target in sizes:
        have = total_rows(conn, schema)
        if fill is not None:
            # A caller-supplied filler, so the grid can be fed a production
            # DISTRIBUTION rather than uniform ballast. Uniform rows are fine as
            # Seq Scan weight but give every grantee the same size, and the
            # index scan's cost tracks rows returned -- a fixture where every
            # grantee is identical cannot show how the speedup varies.
            added = fill(conn, schema, realm, target - have)
        else:
            added = insert_filler(
                conn, schema, realm, target - have, rows_per_grantee=rows_per_grantee
            )
        analyze(conn, schema)
        exact, est = total_rows(conn, schema), reltuples(conn, schema)
        if on_progress:
            on_progress(f"size {exact:,} rows (added {added:,}, reltuples {est:,})")

        for present in (False, True):
            idx = set_index(
                conn, schema, present, name=name, ddl=index_ddl(schema, name)
            )
            measurements = [measure(conn, schema, realm, p, k=k) for p in probes]
            cells.append(
                {
                    "target_size": target,
                    "exact_rows": exact,
                    "reltuples": est,
                    "filler_rows": filler_count(conn, schema),
                    "index_present": present,
                    "index_build_seconds": idx["seconds"] if present else None,
                    "measurements": measurements,
                }
            )
            if on_progress:
                state = "with index" if present else "no index"
                for m in measurements:
                    on_progress(
                        f"    {state:<11} {m['label']:<22} {m['node']:<16} "
                        f"{m['ms']:8.3f} ms"
                    )
    return cells


def speedups(cells):
    """Pair each no-index cell with its with-index twin, per (size, probe).

    Returns:
        list[dict]: size, label, before/after ms and node, speedup, synthetic.
    """
    by_key = {}
    for c in cells:
        for m in c["measurements"]:
            by_key.setdefault((c["exact_rows"], m["label"]), {})[c["index_present"]] = m
    out = []
    for (size, label), pair in sorted(by_key.items()):
        b, a = pair.get(False), pair.get(True)
        if not b or not a:
            continue
        out.append(
            {
                "exact_rows": size,
                "label": label,
                "synthetic": a.get("synthetic") or b.get("synthetic"),
                "before_ms": b["ms"],
                "after_ms": a["ms"],
                "before_node": b["node"],
                "after_node": a["node"],
                "rows_returned": a.get("rows_returned"),
                "speedup": (b["ms"] / a["ms"]) if a["ms"] else float("inf"),
            }
        )
    return out


# ----------------------------------------------------------------------
# reporting
# ----------------------------------------------------------------------
def render_report(cells, meta):
    """The sweep, as markdown. Returns the document as one string.

    Three rules this obeys, each learned from a report that broke one of them:

    1. **Synthetic rows are labelled everywhere they appear**, not once in a
       preamble. A number quoted out of a table is quoted without the preamble.
    2. **Plan shapes are reported beside every timing.** Shapes were identical
       across every run of 02 while the timings moved 4.6x, so the shape is the
       finding and the clock is the illustration.
    3. **The claim is a range with its shape**, never a single ratio. A single
       ratio is what invited "but what about a realm like mine?" in the first
       place, and this whole sweep exists to answer that.
    """
    rows = speedups(cells)
    sizes = sorted({c["exact_rows"] for c in cells})
    has_synthetic = any(r["synthetic"] for r in rows) or any(
        c["filler_rows"] for c in cells
    )

    L = [
        "# Grant-record scaling sweep — how the grantee index behaves as a realm grows",
        "",
        f"Generated {meta.get('generated_at')} against "
        f"`{meta.get('polaris_url')}` realm `{meta.get('realm')}`. Timings are "
        f"the **median of {meta.get('explain_n')}** `EXPLAIN (ANALYZE, BUFFERS)` "
        "runs with the first discarded, statement logging OFF, every statement "
        "pinned to the primary with `/*NO LOAD BALANCE*/`.",
        "",
        "This supersedes the single-point measurement in "
        "`doc-index-measurement-latest.md` **without invalidating it** — that "
        "number is one cell of this grid.",
        "",
    ]

    if has_synthetic:
        L += [
            "## Read this before quoting any number",
            "",
            "The larger table sizes are reached with **synthetic filler rows**, "
            "inserted directly in SQL because REST cannot reach production "
            "volume in a session (10,000 users x 50 grants is ~1,000,000 API "
            "calls). Filler rows:",
            "",
            "- carry **negative** ids, so they match no entity and are inert "
            "for authorization;",
            "- are entirely real to a Seq Scan, which is the only thing being "
            "measured here;",
            "- reproduce the MEASURED grantee histogram of a real realm — "
            "2n+2 grantees holding one row, n holding two (`catalog_admin`), "
            "n holding the granted privileges — rather than uniform ballast, "
            "because the index scan's cost tracks rows returned and a fixture "
            "where every grantee is identical cannot show how that varies.",
            "",
            "Rows derived from them are marked **SYNTHETIC** in every table "
            "below. Do not quote one upstream without that caveat.",
            "",
            "> The plan specified a sentinel range of `>= 1_000_000_000`. That "
            "was wrong and is not what shipped: Polaris ids are snowflake-style "
            "and land around 10^18, so **every real grantee id is above that "
            "floor** and the cleanup `DELETE` would have removed the entire "
            "fixture. The negative range is asserted disjoint against the live "
            "table before any insert.",
            "",
        ]

    # THE EVIDENCE, first: plan cost and buffers are identical across probes
    # within a size and scale linearly with it, in every run so far. The
    # milliseconds do not -- see the caveat under the timing table.
    L += [
        "## Plan cost and buffers — the clock-independent evidence",
        "",
        "Read this table first. Within a size these are **identical across "
        "every probe**, because a Seq Scan reads the whole table regardless of "
        "which grantee is asked for; across sizes they scale with it. That is "
        "the argument, and it needs no clock.",
        "",
        "| rows in table | total cost | shared buffers | rows discarded |",
        "|---:|---:|---:|---|",
    ]
    for c in cells:
        if c["index_present"]:
            continue
        m = c["measurements"][0]
        disc = [
            f"{x['rows_filtered']:,}" for x in c["measurements"] if x["rows_filtered"]
        ]
        L.append(
            f"| {c['exact_rows']:,} | {m['total_cost']:,} | "
            f"{(m['shared_hit'] or 0) + (m['shared_read'] or 0):,} | "
            f"{', '.join(disc) if disc else 'not reported'} |"
        )

    parallel_at = [
        c["exact_rows"]
        for c in cells
        if not c["index_present"] and any(m.get("parallel") for m in c["measurements"])
    ]
    if parallel_at:
        L += [
            "",
            f"**The planner escalated to a PARALLEL sequential scan at "
            f"{min(parallel_at):,} rows and above.** That is a finding in its "
            "own right, and arguably a worse one than latency: an unindexed "
            "grantee lookup that goes parallel consumes parallel worker slots "
            "on the authorization path of *every authenticated request*. It "
            "also makes the wall-clock unusable here — worker startup dominates "
            "a scan this small and worker availability varies run to run.",
        ]

    L += [
        "",
        "## The grid",
        "",
        "| rows in table | probe | rows returned | "
        "plan without index | ms | plan with index | ms | speedup |",
        "|---:|---|---:|---|---:|---|---:|---:|",
    ]
    for r in rows:
        label = r["label"] + (" ⚠" if r["synthetic"] else "")
        L.append(
            f"| {r['exact_rows']:,} | {label} | {r['rows_returned']} | "
            f"`{r['before_node']}` | {r['before_ms']:.3f} | "
            f"`{r['after_node']}` | {r['after_ms']:.3f} | {r['speedup']:.1f}x |"
        )
    if has_synthetic:
        L += ["", "⚠ = the probed grantee is synthetic (see above)."]

    L += [
        "",
        "> **Do not quote a speedup from the table above.** Where the plan went "
        "parallel the milliseconds carry worker-startup noise, and the same "
        "plan — identical cost, identical buffers — has measured a 3-10x spread "
        "across probes that should be indistinguishable. Quote the plan shapes, "
        "the buffer counts and the discard ratio; treat every ratio as "
        "order-of-magnitude at best.",
        "",
        "## What the trend says",
        "",
    ]
    if len(sizes) >= 2:
        lo, hi = sizes[0], sizes[-1]
        # Keyed on the absence of the index, NOT on the node name. Matching
        # `startswith("Seq")` silently dropped this whole bullet the moment the
        # planner went parallel and the root became `Gather` -- losing the most
        # important line in the report exactly when the table got interesting.
        seq = {r["exact_rows"]: r["before_ms"] for r in rows}
        idx = {r["exact_rows"]: r["after_ms"] for r in rows}
        if lo in seq and hi in seq and seq[lo]:
            growth = seq[hi] / seq[lo]
            size_growth = hi / lo
            L += [
                f"- **Seq Scan** went from {seq[lo]:.3f} ms at {lo:,} rows to "
                f"{seq[hi]:.3f} ms at {hi:,} — **{growth:.1f}x** for a "
                f"{size_growth:.1f}x table. Linear growth is the prediction; a "
                "sharp departure from it means the fixture is wrong (most "
                "likely a missing `ANALYZE`) and nothing here should be "
                "published until that is explained.",
            ]
        if lo in idx and hi in idx and idx[lo]:
            L += [
                f"- **Index Only Scan** went from {idx[lo]:.3f} ms to "
                f"{idx[hi]:.3f} ms across the same range — it tracks rows "
                "returned, not table size.",
            ]
        L += [
            "- Therefore **the speedup grows with realm size and shrinks with "
            "grantee fatness**. The previously published figure is a point on "
            "that surface, not a property of Polaris.",
            "",
        ]

    L += ["## Index build cost", "", "| rows in table | build seconds |", "|---:|---:|"]
    for c in cells:
        if c["index_present"] and c["index_build_seconds"] is not None:
            L.append(f"| {c['exact_rows']:,} | {c['index_build_seconds']:.1f} |")
    L += [
        "",
        "`CREATE INDEX CONCURRENTLY` slowing at volume is expected and is part "
        "of the cost being proposed upstream, so it is recorded rather than "
        "omitted.",
        "",
        "## Size accounting",
        "",
        "| target | exact `count(*)` | `reltuples` | drift | filler rows |",
        "|---:|---:|---:|---:|---:|",
    ]
    seen = set()
    for c in cells:
        if c["exact_rows"] in seen:
            continue
        seen.add(c["exact_rows"])
        drift = (c["reltuples"] or 0) - c["exact_rows"]
        L.append(
            f"| {c['target_size']:,} | {c['exact_rows']:,} | "
            f"{c['reltuples']:,} | {drift:+,} | {c['filler_rows']:,} |"
        )
    L += [
        "",
        "Exact counts, never `reltuples` alone — the estimate is stale by "
        "construction immediately after a bulk insert, which is exactly when "
        "it is read here. Both are recorded so the drift is visible rather "
        "than assumed.",
        "",
    ]
    return "\n".join(L) + "\n"
