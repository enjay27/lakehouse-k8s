"""
schema_audit.py
===============
Audit the Polaris PostgreSQL metastore: is the deployed schema the version we
think it is, does every index the running Polaris expects actually exist, and
which of the captured statements have no selective access path?

Answers the three questions behind Phase 1:

    1. "Check Database Table"        -> `describe_schema`, `compare_schema`
    2. "Check Slow Query"            -> `explain_statement`, `rank_statements`
    3. "Check INDEX which does not
        exist in Table"              -> `compare_schema`, `audit_statements`,
                                        `INDEX_HYPOTHESES`

WHY THE DRIFT CHECK COMES FIRST
-------------------------------
A missing index has two very different causes, and they need different fixes:

    * the running Polaris version's schema never defined it  -> upstream gap
    * this instance was created under an older schema and
      never migrated                                         -> local migration gap

`compare_schema` distinguishes them by comparing the LIVE index set against
the expected set for the version recorded in the `version` table. Run it
before drawing any conclusion from an EXPLAIN, or a local migration problem
will be misreported as an upstream bug.

A WARNING ABOUT EMPTY DATABASES
-------------------------------
PostgreSQL will choose a sequential scan on a small table because that is
genuinely the cheaper plan. An index audit against a near-empty instance
proves nothing. `explain_statement` refuses to render a verdict when the
relation is below `MIN_ROWS_FOR_VERDICT`, rather than reporting a
false "Seq Scan!" -- see `audit_statements`.

SAFETY: EXPLAIN ANALYZE EXECUTES THE STATEMENT
----------------------------------------------
`EXPLAIN ANALYZE` on an INSERT/UPDATE/DELETE really performs the write. This
module will NOT do that by default: write statements get a plain `EXPLAIN`
(plan only, no execution). Pass `allow_write_analyze=True` to opt in, and the
statement is then wrapped in a transaction that is ALWAYS rolled back.
"""

import json
import re

# ----------------------------------------------------------------------
# expected schema — Polaris 1.3.0 / schema-v2
# ----------------------------------------------------------------------

# The deployed cluster reports version 3. v3 differs from v2 ONLY by adding the
# `events` table and bumping the version value -- verified by diffing upstream
# postgres/schema-v2.sql against schema-v3.sql at apache-polaris-1.3.0-incubating.
# Every index on entities/grant_records is byte-identical between them, so index
# findings carry across unchanged. Pinning this to 2 produced a false DRIFT.
SCHEMA_VERSION_EXPECTED = 3
SCHEMA_VERSIONS_ACCEPTED = (2, 3)

#: Tables defined by schema-v2.
EXPECTED_TABLES = {
    "version",
    "entities",
    "grant_records",
    "principal_authentication_data",
    "policy_mapping_record",
}

TABLES_ADDED_IN_V3 = {"events"}

#: `events` is created and written by Polaris 1.3.0 whenever a persistence-backed
#: event listener is configured (`eventListener.type: persistence-in-memory-buffer`
#: in the Helm values). Its presence is therefore expected configuration, not
#: schema drift — flagging it as "newer schema" would be a false positive.
EVENT_LISTENER_TABLES = {"events"}

#: Expected access paths, as (name, table, columns, kind). Names follow the
#: upstream DDL; primary keys and unique constraints are included because in
#: PostgreSQL they are backed by indexes and are what most of these queries
#: actually use.
EXPECTED_INDEXES = [
    ("version_pkey", "version", ["version_key"], "pk"),
    ("entities_pkey", "entities", ["realm_id", "id"], "pk"),
    (
        "entities_realm_id_catalog_id_parent_id_type_code_name_key",
        "entities",
        ["realm_id", "catalog_id", "parent_id", "type_code", "name"],
        "unique",
    ),
    ("idx_entities", "entities", ["realm_id", "catalog_id", "id"], "index"),
    (
        "idx_locations",
        "entities",
        ["realm_id", "parent_id", "location_without_scheme"],
        "partial index",
    ),
    (
        "grant_records_pkey",
        "grant_records",
        [
            "realm_id",
            "securable_catalog_id",
            "securable_id",
            "grantee_catalog_id",
            "grantee_id",
            "privilege_code",
        ],
        "pk",
    ),
    (
        "principal_authentication_data_pkey",
        "principal_authentication_data",
        ["realm_id", "principal_client_id"],
        "pk",
    ),
    (
        "policy_mapping_record_pkey",
        "policy_mapping_record",
        [
            "realm_id",
            "target_catalog_id",
            "target_id",
            "policy_type_code",
            "policy_catalog_id",
            "policy_id",
        ],
        "pk",
    ),
    (
        "idx_policy_mapping_record",
        "policy_mapping_record",
        [
            "realm_id",
            "policy_type_code",
            "policy_catalog_id",
            "policy_id",
            "target_catalog_id",
            "target_id",
        ],
        "index",
    ),
]

#: Documented suspicions, derived from reading the 1.3.0 DDL against
#: JdbcBasePersistenceImpl's query predicates. These are HYPOTHESES to confirm
#: or kill with a seeded dataset -- not findings. Each carries the predicate to
#: probe and the remedy if it holds.
INDEX_HYPOTHESES = [
    {
        "id": "grant_records_by_grantee",
        "table": "grant_records",
        "source_method": "loadAllGrantRecordsOnGrantee",
        "predicate": ["realm_id", "grantee_catalog_id", "grantee_id"],
        "claim": (
            "grant_records has exactly one index (its PK), which leads with "
            "realm_id then the SECURABLE columns. A lookup by GRANTEE cannot "
            "use it selectively -- grantee columns sit at positions 4-5 with "
            "the securable columns unconstrained in front of them."
        ),
        "why_it_matters": (
            "loadAllGrantRecordsOnGrantee runs on the authorization path of "
            "EVERY authenticated request, so per-request auth cost would grow "
            "with the total number of grants in the realm. Invisible with a "
            "handful of grants; steadily worse in a shared realm."
        ),
        "severity": "high",
        "remedy": (
            "CREATE INDEX idx_grant_records_grantee ON grant_records "
            "(realm_id, grantee_catalog_id, grantee_id);"
        ),
    },
    {
        "id": "grant_records_delete_or",
        "table": "grant_records",
        "source_method": "deleteAllEntityGrantRecords", "sql_contains": "delete",
        "predicate": ["realm_id", "grantee_id|securable_id"],
        "claim": (
            "The delete predicate ORs two disjoint column sets "
            "((grantee_id, grantee_catalog_id) OR (securable_id, "
            "securable_catalog_id)), which typically cannot be served by a "
            "single index scan."
        ),
        "why_it_matters": (
            "Runs on every entity deletion, so it shows up in teardown and in "
            "any drop-heavy workload rather than on the read path."
        ),
        "severity": "medium",
        "remedy": (
            "Covered by the grantee index above plus the existing PK prefix; "
            "confirm the planner uses a BitmapOr rather than a Seq Scan."
        ),
    },
    {
        "id": "entities_row_constructor_in",
        "table": "entities",
        "source_method": "loadEntitiesChangeTracking", "sql_contains": "in (",
        "predicate": ["realm_id", "(catalog_id, id) IN (...)"],
        "claim": (
            "The entity-cache validation query uses a row-constructor IN list. "
            "PostgreSQL does not always turn this into an efficient index scan "
            "on idx_entities(realm_id, catalog_id, id)."
        ),
        "why_it_matters": (
            "This is the single hottest query in the system -- every cached "
            "request runs exactly one of these. A poor plan here taxes "
            "everything, including the requests the cache was supposed to "
            "make cheap."
        ),
        "severity": "high",
        "remedy": (
            "No new index needed if the planner handles it; if not, the fix is "
            "upstream (rewrite as an OR-of-equalities or a VALUES join)."
        ),
    },
]

#: Below this row count an EXPLAIN verdict is meaningless -- a Seq Scan on a
#: tiny table is correct, not a defect.
MIN_ROWS_FOR_VERDICT = 5000

_WRITE_VERBS = {"INSERT", "UPDATE", "DELETE"}


# ----------------------------------------------------------------------
# live schema inspection
# ----------------------------------------------------------------------
def read_schema_version(conn, schema="polaris_schema"):
    """Read `version.version_value` from the metastore.

    Returns:
        int, or None if the version table is absent or empty (which itself
        means the metastore is not an initialized Polaris JDBC store).
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT to_regclass(%s)", (f"{schema}.version",)
        )
        if cur.fetchone()[0] is None:
            return None
        cur.execute(f"SELECT version_value FROM {schema}.version LIMIT 1")  # noqa: S608
        row = cur.fetchone()
    return row[0] if row else None


def live_tables(conn, schema="polaris_schema"):
    """Return the set of table names present in the metastore schema."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname = %s", (schema,)
        )
        return {r[0].lower() for r in cur.fetchall()}


def live_indexes(conn, schema="polaris_schema"):
    """Return every index in the metastore schema.

    Returns:
        list[dict]: {name, table, definition, columns, is_unique, is_primary}.
        `columns` is parsed out of the index definition, so it reflects what
        PostgreSQL actually built rather than what the DDL intended.
    """
    sql = """
        SELECT i.relname  AS index_name,
               t.relname  AS table_name,
               pg_get_indexdef(i.oid) AS definition,
               ix.indisunique,
               ix.indisprimary
        FROM pg_index ix
        JOIN pg_class i ON i.oid = ix.indexrelid
        JOIN pg_class t ON t.oid = ix.indrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE n.nspname = %s
        ORDER BY t.relname, i.relname
    """
    out = []
    with conn.cursor() as cur:
        cur.execute(sql, (schema,))
        for name, table, definition, uniq, prim in cur.fetchall():
            out.append(
                {
                    "name": name.lower(),
                    "table": table.lower(),
                    "definition": definition,
                    "columns": _columns_from_indexdef(definition),
                    "is_unique": bool(uniq),
                    "is_primary": bool(prim),
                }
            )
    return out


def _columns_from_indexdef(definition):
    """Pull the indexed column list out of a `pg_get_indexdef` string."""
    m = re.search(r"\((?P<cols>[^)]*)\)", definition or "")
    if not m:
        return []
    return [
        c.strip().strip('"').split()[0].lower()
        for c in m.group("cols").split(",")
        if c.strip()
    ]


def describe_schema(conn, schema="polaris_schema"):
    """One-call snapshot of the live metastore schema.

    Returns:
        dict: {schema, version, tables, indexes}.
    """
    return {
        "schema": schema,
        "version": read_schema_version(conn, schema),
        "tables": sorted(live_tables(conn, schema)),
        "indexes": live_indexes(conn, schema),
    }


# ----------------------------------------------------------------------
# drift comparison
# ----------------------------------------------------------------------
def compare_schema(snapshot, expected_version=SCHEMA_VERSION_EXPECTED):
    """Compare a `describe_schema` snapshot against the expected schema-v2 set.

    Matches indexes by (table, column list) rather than by name, because a
    hand-created index that does the same job under a different name should
    count as present -- the question is whether an access path exists, not
    whether upstream's name was used.

    Returns:
        dict with keys:
            version_ok, version_found, version_expected
            missing_tables, unexpected_tables
            missing_indexes  -- expected access paths with no live equivalent
            extra_indexes    -- live indexes not in the expected set
            verdict          -- "OK" | "DRIFT"
            notes            -- human-readable interpretation
    """
    live_tbls = set(snapshot["tables"])
    live_idx = snapshot["indexes"]
    live_sigs = {(i["table"], tuple(i["columns"])) for i in live_idx}

    missing_tables = sorted(EXPECTED_TABLES - live_tbls)
    unexpected_tables = sorted(live_tbls - EXPECTED_TABLES - EVENT_LISTENER_TABLES)
    event_tables = sorted(live_tbls & EVENT_LISTENER_TABLES)

    missing_indexes = []
    for name, table, cols, kind in EXPECTED_INDEXES:
        if (table, tuple(cols)) not in live_sigs:
            missing_indexes.append(
                {"name": name, "table": table, "columns": cols, "kind": kind}
            )

    expected_sigs = {(t, tuple(c)) for (_, t, c, _) in EXPECTED_INDEXES}
    extra_indexes = [
        i for i in live_idx if (i["table"], tuple(i["columns"])) not in expected_sigs
    ]

    version_found = snapshot.get("version")
    # Accept any version whose index definitions we have actually verified as
    # equivalent, not just one exact number. v2 and v3 differ only by the
    # `events` table, so both are valid baselines for an INDEX audit.
    version_ok = version_found in SCHEMA_VERSIONS_ACCEPTED

    notes = []
    if version_found is None:
        notes.append(
            "No version row found — this may not be an initialized Polaris "
            "JDBC metastore, or the schema name is wrong."
        )
    elif not version_ok:
        notes.append(
            f"Schema version is {version_found}; this module has verified index "
            f"expectations only for {list(SCHEMA_VERSIONS_ACCEPTED)}. Treat index "
            "findings as unverified until the expected set is checked against "
            "the deployed version's DDL."
        )
    if unexpected_tables:
        v3 = sorted(set(unexpected_tables) & TABLES_ADDED_IN_V3)
        if v3 and version_found and version_found >= 3:
            # Expected at this version: not drift, not a mismatch.
            unexpected_tables = [t for t in unexpected_tables if t not in v3]
            notes.append(f"Tables {v3} are part of schema-v{version_found}.")
        elif v3:
            notes.append(
                f"Tables {v3} exist only in schema-v3+, so the deployed schema "
                "is NEWER than the reported version. Version mismatch, not a bug."
            )
    if missing_indexes:
        notes.append(
            "Missing expected access paths — this is a LOCAL MIGRATION gap "
            "(the deployed instance lacks something its own schema defines), "
            "which is a different problem from an index upstream never "
            "created. Fix by migrating before reporting anything upstream."
        )
    if event_tables:
        notes.append(
            f"{event_tables} present — created by the persistence event listener "
            "(eventListener.type: persistence-in-memory-buffer), which is "
            "configuration, not schema drift. Note its writes are flushed on a "
            "timer, so they are attributed separately during tracing."
        )
    if not notes:
        notes.append(
            f"Live schema (v{version_found}) matches the expected definition."
        )

    drift = bool(missing_tables or missing_indexes or not version_ok)
    return {
        "version_ok": version_ok,
        "version_found": version_found,
        "version_expected": expected_version,
        "missing_tables": missing_tables,
        "unexpected_tables": unexpected_tables,
        "event_listener_tables": event_tables,
        "missing_indexes": missing_indexes,
        "extra_indexes": extra_indexes,
        "verdict": "DRIFT" if drift else "OK",
        "notes": notes,
    }


# ----------------------------------------------------------------------
# table statistics
# ----------------------------------------------------------------------
def table_stats(conn, schema="polaris_schema"):
    """Per-table access statistics from `pg_stat_user_tables`.

    Needs no per-query attribution, which makes it the cheapest way to spot a
    table being sequentially scanned: a high `seq_scan` with a large
    `seq_tup_read` is the smoking gun for a missing access path.

    Returns:
        list[dict]: {table, seq_scan, seq_tup_read, idx_scan, idx_tup_fetch,
        n_live_tup, n_tup_ins, n_tup_upd, n_tup_del, n_tup_hot_upd,
        hot_update_ratio, seq_scan_ratio}.
    """
    sql = """
        SELECT relname, seq_scan, seq_tup_read,
               COALESCE(idx_scan, 0), COALESCE(idx_tup_fetch, 0),
               n_live_tup, n_tup_ins, n_tup_upd, n_tup_del,
               COALESCE(n_tup_hot_upd, 0)
        FROM pg_stat_user_tables
        WHERE schemaname = %s
        ORDER BY seq_tup_read DESC
    """
    out = []
    with conn.cursor() as cur:
        cur.execute(sql, (schema,))
        for row in cur.fetchall():
            (
                relname, seq_scan, seq_tup_read, idx_scan, idx_tup_fetch,
                live, ins, upd, dele, hot,
            ) = row
            scans = (seq_scan or 0) + (idx_scan or 0)
            out.append(
                {
                    "table": relname.lower(),
                    "seq_scan": seq_scan or 0,
                    "seq_tup_read": seq_tup_read or 0,
                    "idx_scan": idx_scan or 0,
                    "idx_tup_fetch": idx_tup_fetch or 0,
                    "n_live_tup": live or 0,
                    "n_tup_ins": ins or 0,
                    "n_tup_upd": upd or 0,
                    "n_tup_del": dele or 0,
                    "n_tup_hot_upd": hot or 0,
                    "hot_update_ratio": round(hot / upd, 3) if upd else None,
                    "seq_scan_ratio": round((seq_scan or 0) / scans, 3) if scans else None,
                }
            )
    return out


# Populated by analyze_tables(): {table: first line of the error}. Empty on
# a clean run. Read this when a table stays stale despite ANALYZE.
LAST_ANALYZE_ERRORS = {}


def analyze_tables(conn, schema="polaris_schema", tables=None):
    """Run ANALYZE so the planner has fresh statistics.

    MUST be called after seeding and before any EXPLAIN. `pg_class.reltuples`
    is only refreshed by VACUUM/ANALYZE, and autovacuum here is deliberately
    throttled (`autovacuum_naptime = 30s`, `autovacuum_max_workers = 2`). So
    immediately after inserting tens of thousands of rows the planner still
    believes the tables are empty — it will pick sequential scans that are
    correct for the statistics it has and wrong for the data that is actually
    there, and the audit would record a false SEQ_SCAN finding.

    Args:
        conn: psycopg2 connection.
        schema: metastore schema.
        tables: iterable of table names. Defaults to every live table in the
            schema -- NOT EXPECTED_TABLES. `statistics_are_stale` inspects all
            relations in the schema, so scoping the ANALYZE to the expected set
            left anything else (notably `events`, created by the persistence
            event listener) permanently unanalyzed, and the staleness assert
            could never pass.

    Returns:
        list of tables analyzed.
    """
    if tables is None:
        try:
            tables = [t["name"] if isinstance(t, dict) else t
                      for t in live_tables(conn, schema=schema)]
        except Exception:  # noqa: BLE001 -- fall back to the known set
            conn.rollback()
            tables = EXPECTED_TABLES
    targets = sorted(tables or EXPECTED_TABLES)
    done = []
    LAST_ANALYZE_ERRORS.clear()
    with conn.cursor() as cur:
        for t in targets:
            try:
                cur.execute(f'ANALYZE "{schema}"."{t}"')  # noqa: S608
                done.append(t)
            except Exception as exc:  # noqa: BLE001 — absent table is not fatal
                # Record it. Swallowing this silently is how "ANALYZE ran but
                # the table is still stale" became impossible to diagnose from
                # the notebook: the caller saw a short `done` list and no reason.
                LAST_ANALYZE_ERRORS[t] = str(exc).strip().splitlines()[0][:200]
                conn.rollback()
    try:
        conn.commit()
    except Exception:  # noqa: BLE001
        pass
    return done


def relation_rowcount(conn, table, schema="polaris_schema", exact_if_unanalyzed=True):
    """Live row count for a table.

    Prefers `pg_class.reltuples` — this is called per statement during an audit
    and an exact COUNT(*) on a large table would dominate the audit's runtime.

    BUT PostgreSQL stores `reltuples = -1` for a relation that has never been
    vacuumed or analyzed, and 0 for one analyzed while empty. Treating -1 as a
    row count would make every statement come back TOO_SMALL on a freshly
    seeded database — the exact situation this audit is designed for. So when
    the estimate is negative we fall back to an exact count and let the caller
    know the statistics are stale.

    Returns:
        int row count (>= 0).
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT c.reltuples::bigint
            FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = %s AND c.relname = %s
            """,
            (schema, table),
        )
        row = cur.fetchone()
        est = int(row[0]) if row and row[0] is not None else 0
        if est >= 0:
            return est
        # reltuples = -1 → never analyzed. An estimate of -1 must never be
        # allowed to masquerade as "this table is small".
        if not exact_if_unanalyzed:
            return 0
        try:
            cur.execute(f'SELECT count(*) FROM "{schema}"."{table}"')  # noqa: S608
            return int(cur.fetchone()[0])
        except Exception:  # noqa: BLE001
            conn.rollback()
            return 0


def statistics_are_stale(conn, schema="polaris_schema"):
    """Report tables whose planner statistics have never been gathered.

    Returns:
        list[str] of table names with `reltuples < 0`. A non-empty result means
        `analyze_tables()` has not been run and every EXPLAIN verdict from this
        state is untrustworthy.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT c.relname
            FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = %s AND c.relkind = 'r' AND c.reltuples < 0
            ORDER BY 1
            """,
            (schema,),
        )
        return [r[0] for r in cur.fetchall()]


# ----------------------------------------------------------------------
# EXPLAIN
# ----------------------------------------------------------------------
def parse_param_list(params):
    """Parse a captured parameter string into a Python list.

    Accepts the bracketed form from the Polaris log (`[POLARIS, 0, 42]`) and
    the PostgreSQL DETAIL form (`$1 = 'POLARIS', $2 = '0'`). Integer-looking
    values are coerced to int so the planner sees the right types.

    Returns:
        list, or None if the input was None/empty/redacted. A redacted value
        yields None deliberately: statements whose parameters were redacted
        must not be EXPLAINed with fabricated substitutes.
    """
    if not params:
        return None

    # Already a sequence of bound values -- which is what
    # `resolve_params`/`enrich_inventory` produce, since they read values
    # straight out of a live row rather than out of a log line. Only log-derived
    # parameters arrive as text needing a parse. Assuming a string here is what
    # raised "'tuple' object has no attribute 'strip'".
    if isinstance(params, (list, tuple)):
        return list(params)

    s = params.strip()
    if "<redacted>" in s:
        return None
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1]
        parts = [p.strip() for p in s.split(",")] if s.strip() else []
    else:
        parts = [
            m.group("v").strip().strip("'")
            for m in re.finditer(r"\$\d+\s*=\s*(?P<v>'[^']*'|[^,]+)", s)
        ]
        if not parts:
            # Polaris's own log joins parameters as plain comma-separated
            # VALUES ("POLARIS, 305799478250450321"), with no `$N =` prefix.
            # Only the PostgreSQL DETAIL form has that prefix, so this branch
            # previously produced an empty list -- which is falsy, so every
            # caller read it as "no parameters" and rendered NO_PARAMS. An
            # empty list and None have to mean different things here.
            parts = [x.strip() for x in s.split(",")] if s else []
    out = []
    for p in parts:
        p = p.strip().strip("'")
        if re.fullmatch(r"-?\d+", p):
            out.append(int(p))
        elif p.upper() == "NULL":
            out.append(None)
        else:
            out.append(p)
    return out


def explain_statement(conn, sql, params=None, analyze=True, buffers=True,
                      allow_write_analyze=False):
    """EXPLAIN one statement and return the plan as parsed JSON.

    Args:
        conn: psycopg2 connection.
        sql: statement text, with `?` or `$N` placeholders.
        params: list of bound values (see `parse_param_list`). Required when
            the statement has placeholders.
        analyze: run EXPLAIN ANALYZE (actual timings and row counts).
        buffers: include BUFFERS output.
        allow_write_analyze: permit ANALYZE on INSERT/UPDATE/DELETE. Off by
            default because ANALYZE EXECUTES the statement. When enabled, the
            statement runs inside a transaction that is ALWAYS rolled back.

    Returns:
        dict: {ok, plan, error, analyzed, wrote} where `plan` is the parsed
        JSON plan tree.

    Raises:
        Never — failures are returned in the dict, because an audit sweeping
        dozens of statements should report a bad one and continue rather than
        abort the run.
    """
    verb = (re.match(r"\s*(\w+)", sql or "") or [None, ""])[1].upper() if sql else ""
    is_write = verb in _WRITE_VERBS
    do_analyze = analyze and (not is_write or allow_write_analyze)

    opts = ["FORMAT JSON"]
    if do_analyze:
        opts.append("ANALYZE")
        if buffers:
            opts.append("BUFFERS")
    prefix = f"EXPLAIN ({', '.join(opts)}) "

    # psycopg2 interpolates %s; Polaris logs ? and PostgreSQL logs $N.
    stmt = re.sub(r"\$\d+", "?", sql).replace("?", "%s")
    args = tuple(params) if params else None

    needs_tx = is_write and do_analyze
    try:
        with conn.cursor() as cur:
            if needs_tx:
                cur.execute("SAVEPOINT _audit_sp")
            cur.execute(prefix + stmt, args)
            plan = cur.fetchone()[0]
            if needs_tx:
                # Always undo: an audit must never mutate the metastore.
                cur.execute("ROLLBACK TO SAVEPOINT _audit_sp")
        if isinstance(plan, str):
            plan = json.loads(plan)
        return {
            "ok": True,
            "plan": plan,
            "error": None,
            "analyzed": do_analyze,
            "wrote": False,
        }
    except Exception as exc:  # noqa: BLE001 — audit continues past a bad statement
        try:
            conn.rollback()
        except Exception:  # noqa: BLE001
            pass
        return {
            "ok": False,
            "plan": None,
            "error": f"{type(exc).__name__}: {exc}",
            "analyzed": False,
            "wrote": False,
        }


def walk_plan(plan):
    """Yield every node in a parsed EXPLAIN JSON plan tree, depth-first."""
    if isinstance(plan, list):
        for item in plan:
            yield from walk_plan(item)
        return
    if not isinstance(plan, dict):
        return
    node = plan.get("Plan", plan)
    if isinstance(node, dict) and "Node Type" in node:
        yield node
        for child in node.get("Plans", []) or []:
            yield from walk_plan({"Plan": child})
    elif "Plan" in plan:
        yield from walk_plan(plan["Plan"])


def plan_summary(plan):
    """Condense a plan tree into the few facts the audit cares about.

    Returns:
        dict: {node_types, scan_nodes, seq_scans, index_scans, total_ms,
        rows_removed, shared_hit, shared_read}.
    """
    nodes = list(walk_plan(plan))
    seq, idx, removed, hit, read = [], [], 0, 0, 0
    for n in nodes:
        nt = n.get("Node Type", "")
        if nt == "Seq Scan":
            seq.append(n.get("Relation Name"))
        elif "Index" in nt:
            idx.append(n.get("Index Name") or n.get("Relation Name"))
        removed += n.get("Rows Removed by Filter", 0) or 0
        hit += n.get("Shared Hit Blocks", 0) or 0
        read += n.get("Shared Read Blocks", 0) or 0
    total_ms = None
    if isinstance(plan, list) and plan and isinstance(plan[0], dict):
        total_ms = plan[0].get("Execution Time")
    return {
        "node_types": [n.get("Node Type") for n in nodes],
        "seq_scans": [s for s in seq if s],
        "index_scans": [i for i in idx if i],
        "total_ms": total_ms,
        "rows_removed_by_filter": removed,
        "shared_hit": hit,
        "shared_read": read,
    }



_EQ_PREDICATE = re.compile(r"(\w+)\s*=\s*(?:\?|%s|\$\d+)", re.I)


def resolve_params(conn, sql, table, realm=None, schema="polaris_schema",
                   _cache=None):
    """Derive representative bind values for a captured statement.

    WHY THIS EXISTS
    ---------------
    Polaris logs bind parameters as `?` and `api_trace.redact_params` strips the
    values, so a captured inventory arrives with no parameters at all.
    `audit_statements` then -- correctly -- refuses to EXPLAIN and returns
    NO_PARAMS. The consequence is that an entire audit run comes back with no
    verdicts and reads like a clean bill of health when in fact nothing was
    measured. That is the worst possible failure mode for this module.

    The fix is to read the equality columns out of the statement's WHERE clause
    in order, then take those column values from a REAL row of that table. The
    plan is then measured against parameters that actually select something,
    rather than invented ones that make every lookup look free.

    Returns None -- deliberately leaving the statement as NO_PARAMS -- when the
    values cannot be resolved honestly:
      * `normalize_sql` collapsed a row-constructor IN list to a marker, which
        is not valid SQL and must never reach EXPLAIN;
      * there is no WHERE clause (INSERTs), so the placeholders are VALUES and
        sampling a row would produce a meaningless plan;
      * the placeholder count and the parsed column count disagree (ORs,
        functions, LIKE), which means the parse is not trustworthy.

    Args:
        conn: psycopg2 connection.
        sql: normalized statement text.
        table: table the statement targets.
        realm: value to bind for `realm_id`; sampled from the row if omitted.
        schema: metastore schema.
        _cache: optional dict reused across calls to avoid re-sampling.

    Returns:
        tuple of bind values in placeholder order, or None.
    """
    if not table or not sql:
        return None
    if "<" in sql or not re.search(r"\sWHERE\s", sql, re.I):
        return None

    where = re.split(r"\sWHERE\s", sql, maxsplit=1, flags=re.I)[-1]
    cols = [m.group(1).lower() for m in _EQ_PREDICATE.finditer(where)]
    n_placeholders = sql.count("?") + sql.count("%s") + len(
        re.findall(r"\$\d+", sql)
    )
    if not cols or len(cols) != n_placeholders:
        return None

    cache = _cache if _cache is not None else {}
    if table not in cache:
        try:
            with conn.cursor() as cur:
                cur.execute(f'SELECT * FROM "{schema}"."{table}" LIMIT 1')  # noqa: S608
                if cur.description is None:
                    cache[table] = {}
                else:
                    names = [d[0].lower() for d in cur.description]
                    row = cur.fetchone()
                    cache[table] = dict(zip(names, row)) if row else {}
        except Exception:  # noqa: BLE001
            conn.rollback()
            cache[table] = {}
    row = cache[table]
    if not row:
        return None

    out = []
    for c in cols:
        if c == "realm_id" and realm is not None:
            out.append(realm)
        elif c in row:
            out.append(row[c])
        else:
            return None
    return tuple(out)


def enrich_inventory(conn, inventory, realm=None, schema="polaris_schema"):
    """Attach `params` to every statement that can be resolved honestly.

    Returns:
        (inventory, resolved_count) -- the same list, mutated in place.
    """
    cache = {}
    resolved = 0
    for row in inventory:
        # "Has params" is not the same as "has USABLE params": a redacted set,
        # or one that does not parse, or one whose length disagrees with the
        # placeholder count, is worse than none -- it suppresses sampling and
        # guarantees NO_PARAMS. Validate before trusting it.
        existing = row.get("params")
        if existing:
            try:
                parsed = parse_param_list(existing)
            except Exception:  # noqa: BLE001
                parsed = None
            sql = row.get("sql") or ""
            want = sql.count("?") + sql.count("%s") + len(re.findall(r"\$\d+", sql))
            if parsed and len(parsed) == want:
                resolved += 1
                continue
            row.pop("params", None)
        p = resolve_params(conn, row.get("sql"), row.get("table"),
                           realm=realm, schema=schema, _cache=cache)
        if p is not None:
            row["params"] = p
            resolved += 1
    return inventory, resolved



# `api_trace.normalize_sql` collapses a row-constructor IN list to this marker
# so that a thousand executions with different id sets group as ONE statement.
# Necessary for the inventory, fatal for EXPLAIN: the marker is not valid SQL.
_ROWS_MARKER = "<rows>"
_ROW_CTOR = re.compile(
    r"\(\s*(?P<cols>\w+(?:\s*,\s*\w+)*)\s*\)\s+IN\s*\(\s*<rows>\s*\)", re.I
)


def expand_row_constructor(conn, sql, realm=None, schema="polaris_schema",
                           n_rows=20):
    """Rebuild a real IN-list for a collapsed row-constructor statement.

    WHY THIS IS NEEDED
    ------------------
    The entity-cache validation query

        SELECT ... FROM entities WHERE (catalog_id, id) IN (...) AND realm_id = ?

    is the single most frequently executed statement in Polaris -- every cached
    request runs exactly one. It cannot be EXPLAINed from the inventory because
    the id set was replaced by a marker, so it has sat at NO_PARAMS through
    every audit run: the hottest query in the system, never measured.

    Rather than skip it, sample `n_rows` REAL (catalog_id, id) pairs from the
    table and substitute them as literals. The row count matters -- PostgreSQL
    can switch between an index scan per element and a sequential scan as the
    list grows -- so callers should probe several sizes, not one.

    Values are inlined as literals rather than bound, because a row-constructor
    IN list has a variable arity that placeholders cannot express. Only integers
    and quote-escaped strings are emitted, and the pairs come from the database
    itself, so this is not an injection path.

    Returns:
        (expanded_sql, n_pairs) or (None, 0) if there is no marker or no data.
    """
    if _ROWS_MARKER not in (sql or ""):
        return None, 0
    m = _ROW_CTOR.search(sql)
    if not m:
        return None, 0
    cols = [c.strip() for c in m.group("cols").split(",")]

    tm = re.search(r"FROM\s+(?:\w+\.)?(\w+)", sql, re.I)
    if not tm:
        return None, 0
    table = tm.group(1).lower()

    try:
        with conn.cursor() as cur:
            cur.execute(
                f'SELECT {", ".join(cols)} FROM "{schema}"."{table}" '  # noqa: S608
                f"WHERE realm_id = %s LIMIT %s",
                (realm, n_rows),
            )
            rows = cur.fetchall()
    except Exception:  # noqa: BLE001
        conn.rollback()
        return None, 0
    if not rows:
        return None, 0

    def lit(v):
        if v is None:
            return "NULL"
        if isinstance(v, bool):
            return "TRUE" if v else "FALSE"
        if isinstance(v, int):
            return str(v)
        return "'" + str(v).replace("'", "''") + "'"

    tuples = ", ".join("(" + ", ".join(lit(v) for v in r) + ")" for r in rows)
    expanded = sql[: m.start()] + f'({", ".join(cols)}) IN ({tuples})' + sql[m.end():]
    return expanded, len(rows)


def audit_row_constructor(conn, sql, realm=None, schema="polaris_schema",
                          sizes=(1, 10, 50, 200)):
    """EXPLAIN the collapsed IN-list statement at several list lengths.

    One size proves nothing: the planner legitimately changes strategy as the
    list grows, and the interesting question is whether it degrades at the sizes
    the entity cache actually produces.

    Returns:
        list[dict] with {n, verdict, node, plan_ms, sql}.
    """
    out = []
    for n in sizes:
        expanded, got = expand_row_constructor(
            conn, sql, realm=realm, schema=schema, n_rows=n)
        if not expanded:
            continue
        params = resolve_params(conn, expanded, None, realm=realm, schema=schema)
        if params is None:
            # only realm_id should remain
            params = (realm,) if "?" in expanded or "%s" in expanded else None
        try:
            plan = explain_statement(conn, expanded, params=params, analyze=True)
        except Exception as exc:  # noqa: BLE001
            conn.rollback()
            out.append({"n": got, "verdict": "ERROR", "node": None,
                        "plan_ms": None, "error": str(exc).splitlines()[0][:160]})
            continue
        summ = plan_summary(plan)
        types = summ.get("node_types") or []
        seq = summ.get("seq_scans") or []
        out.append({
            "n": got,
            "verdict": "SEQ_SCAN" if seq else "INDEX_SCAN",
            "node": types[0] if types else None,
            "indexes": summ.get("index_scans") or [],
            "plan_ms": summ.get("total_ms"),
            "rows_removed": summ.get("rows_removed_by_filter"),
        })
    return out

def audit_statements(conn, inventory, schema="polaris_schema", analyze=True,
                     min_rows=MIN_ROWS_FOR_VERDICT):
    """EXPLAIN every captured statement and render an access-path verdict.

    Args:
        conn: psycopg2 connection.
        inventory: output of `api_trace.statement_inventory` — needs at least
            `sql`, `table`, `verb`, and optionally `params` and `apis`.
        schema: metastore schema name.
        analyze: pass through to `explain_statement`.
        min_rows: below this live row count, no verdict is rendered. A Seq Scan
            on a small table is the correct plan, and calling it a defect is
            the single easiest way to produce a false finding.

    Returns:
        list[dict] per statement: {sql, table, verb, apis, calls, verdict,
        detail, seq_scans, index_scans, rows_removed_by_filter, plan_ms,
        table_rows, error}.

        verdict is one of:
            SEQ_SCAN        — sequential scan on a table big enough to matter
            INDEX_SCAN      — a selective access path was used
            FILTER_HEAVY    — indexed, but discarding many rows after the scan
                              (a partially-matching index — often the more
                              interesting finding, because it looks fine)
            TOO_SMALL       — table below min_rows; no verdict possible
            NO_PARAMS       — parameters unavailable or redacted; not EXPLAINed
            ERROR           — EXPLAIN failed; see `error`
    """
    results = []
    rowcounts = {}
    for entry in inventory:
        sql = entry.get("sql")
        table = entry.get("table")
        params = entry.get("params")
        row = {
            "sql": sql,
            "table": table,
            "verb": entry.get("verb"),
            "apis": entry.get("apis", []),
            "calls": entry.get("calls"),
            "verdict": None,
            "detail": "",
            "seq_scans": [],
            "index_scans": [],
            "rows_removed_by_filter": None,
            "plan_ms": None,
            "table_rows": None,
            "error": None,
        }

        if table:
            if table not in rowcounts:
                rowcounts[table] = relation_rowcount(conn, table, schema)
            row["table_rows"] = rowcounts[table]

        parsed = parse_param_list(params) if params else None
        if ("?" in (sql or "") or "$1" in (sql or "")) and not parsed:
            row["verdict"] = "NO_PARAMS"
            row["detail"] = (
                "Statement has placeholders but no usable parameters "
                "(absent, or redacted because it touches secret material). "
                "Supply representative parameters to audit this one."
            )
            results.append(row)
            continue

        res = explain_statement(conn, sql, parsed, analyze=analyze)
        if not res["ok"]:
            row["verdict"] = "ERROR"
            row["error"] = res["error"]
            results.append(row)
            continue

        summary = plan_summary(res["plan"])
        row["seq_scans"] = summary["seq_scans"]
        row["index_scans"] = summary["index_scans"]
        row["rows_removed_by_filter"] = summary["rows_removed_by_filter"]
        row["plan_ms"] = summary["total_ms"]

        if row["table_rows"] is not None and row["table_rows"] < min_rows:
            row["verdict"] = "TOO_SMALL"
            row["detail"] = (
                f"{table} holds ~{row['table_rows']} rows (< {min_rows}). "
                "PostgreSQL prefers a sequential scan on small tables because "
                "it is genuinely cheaper — no conclusion can be drawn. Seed "
                "more data before trusting an index verdict here."
            )
        elif summary["seq_scans"]:
            row["verdict"] = "SEQ_SCAN"
            row["detail"] = (
                f"Sequential scan on {summary['seq_scans']} at ~"
                f"{row['table_rows']} rows — no selective access path."
            )
        elif summary["rows_removed_by_filter"] and row["table_rows"]:
            ratio = summary["rows_removed_by_filter"] / max(row["table_rows"], 1)
            if ratio > 0.1:
                row["verdict"] = "FILTER_HEAVY"
                row["detail"] = (
                    f"Index used, but {summary['rows_removed_by_filter']} rows "
                    "were discarded by filter afterwards — the index matches "
                    "the query only partially. This is the failure mode that "
                    "looks healthy in a plan summary."
                )
            else:
                row["verdict"] = "INDEX_SCAN"
                row["detail"] = f"Index scan via {summary['index_scans']}."
        else:
            row["verdict"] = "INDEX_SCAN"
            row["detail"] = f"Index scan via {summary['index_scans']}."

        results.append(row)
    return results


def rank_statements(inventory, top=20):
    """Rank statements by total time, falling back to call count.

    Deliberately NOT ranked by max duration: the slowest single query is
    rarely the problem. The moderately slow query on the authorization path,
    called on every request, is — and only `total = mean x calls` surfaces it.
    """
    ranked = sorted(
        inventory,
        key=lambda r: (
            -(r.get("total_ms") or 0),
            -(r.get("calls") or 0),
        ),
    )
    return ranked[:top]


def check_hypotheses(conn, audit_rows, schema="polaris_schema"):
    """Check each documented hypothesis in INDEX_HYPOTHESES against the audit.

    Returns:
        list[dict]: the hypothesis plus {status, evidence}, where status is
            CONFIRMED    — a SEQ_SCAN or FILTER_HEAVY verdict on that table
            REFUTED      — that table's statements all used a selective path
            INCONCLUSIVE — no matching statement, or the table was too small
    """
    out = []
    for hyp in INDEX_HYPOTHESES:
        # Match on the PREDICATE, not just the table. Matching by table alone
        # let unrelated statements stand in as evidence: entities has a dozen
        # well-indexed lookups, so the row-constructor-IN hypothesis was
        # reported REFUTED on the strength of queries it says nothing about,
        # while the statement it IS about sat there unEXPLAINed as NO_PARAMS.
        # A confident wrong answer is worse than INCONCLUSIVE.
        cols = [c for c in (hyp.get("predicate") or [])
                if re.fullmatch(r"\w+", c)]   # skip prose entries like
                                              # "(catalog_id, id) IN (...)"
                                              # and alternations "a|b"
        rows = []
        for r in audit_rows:
            if r.get("table") != hyp["table"]:
                continue
            sql = (r.get("sql") or "").lower()
            if cols and not all(re.search(rf"\b{re.escape(c)}\b", sql) for c in cols):
                continue
            if hyp.get("sql_contains") and hyp["sql_contains"].lower() not in sql:
                continue
            rows.append(r)
        bad = [r for r in rows if r.get("verdict") in ("SEQ_SCAN", "FILTER_HEAVY")]
        small = [r for r in rows if r.get("verdict") == "TOO_SMALL"]
        good = [r for r in rows if r.get("verdict") == "INDEX_SCAN"]

        unexplained = [r for r in rows if r.get("verdict") in ("NO_PARAMS", "ERROR")]
        if bad:
            status, evidence = "CONFIRMED", [r["sql"] for r in bad]
        elif unexplained and not good:
            # The statement this hypothesis is about exists but was never
            # planned, so nothing has been measured either way.
            status = "INCONCLUSIVE"
            evidence = [
                f"matching statement was not EXPLAINed "
                f"({unexplained[0].get('verdict')}): {unexplained[0].get('sql','')[:120]}"
            ]
        elif small or not rows:
            status = "INCONCLUSIVE"
            evidence = (
                ["table too small for a verdict — seed more data"]
                if small
                else ["no captured statement matched this hypothesis's predicate"]
            )
        elif good:
            status, evidence = "REFUTED", [r["sql"] for r in good]
        else:
            status, evidence = "INCONCLUSIVE", []

        entry = dict(hyp)
        entry["status"] = status
        entry["evidence"] = evidence
        out.append(entry)
    return out
