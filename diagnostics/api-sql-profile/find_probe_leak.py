"""Identify exactly which entities notebook 01 leaves behind.

Read-only. 01's row count rose by exactly 4 per run across five runs
(7273 -> 7289) while its teardown reported "no residue" every time.

ANSWERED 2026-08-21. Teardown is NOT broken: zero probe-named rows survive. The
survivors are `entityCleanup_*` rows with `type_code = 8` and `catalog_id = 0`,
carrying no `drop_timestamp` — live TASK entities at the realm root, which
Polaris enqueues when something is dropped with purge and which nothing here
reaps. So this is Polaris's own async-task bookkeeping, not residue of ours, and
deleting the rows would delete the evidence rather than fix anything.

The first run of this script mislabelled them **FILE**. Its TYPE map was
hand-written and shifted by one against the real `PolarisEntityType`, which is
NULL_TYPE=0, ROOT=1, PRINCIPAL=2, PRINCIPAL_ROLE=3, CATALOG=4, CATALOG_ROLE=5,
NAMESPACE=6, TABLE_LIKE=7, TASK=8, FILE=9, POLICY=10 (verified against the
1.3.0-incubating source). Every type this script printed was therefore one place
off. Fixed below — and worth noting as the same failure mode as the classifier
bugs: a table transcribed from memory and never checked against the source.
"""

import json
import os
from collections import Counter

import psycopg2

PG = dict(
    host=os.environ.get("PG_HOST", "192.168.139.2"),
    port=int(os.environ.get("PG_PORT", "5432")),
    dbname=os.environ.get("PG_DB", "polaris"),
    user=os.environ.get("PG_USER", "polaris"),
    password=os.environ.get("PG_PASSWORD", "polaris"),
)

# PolarisEntityType, verbatim from polaris-core at tag
# apache-polaris-1.3.0-incubating. Do not re-derive this from memory.
TYPE = {
    0: "NULL_TYPE",
    1: "ROOT",
    2: "PRINCIPAL",
    3: "PRINCIPAL_ROLE",
    4: "CATALOG",
    5: "CATALOG_ROLE",
    6: "NAMESPACE",
    7: "TABLE_LIKE",
    8: "TASK",
    9: "FILE",
    10: "POLICY",
}
# PolarisEntitySubType, likewise verbatim from the 1.3.0 source. Note there is
# no code 1 — the hand-written map this file used to carry filled that gap and
# so mislabelled every table as a view and every view as a generic table. Second
# off-by-one in the same file; both were guesses that nobody checked.
SUB = {
    -1: "ANY_SUBTYPE",
    0: "-",
    2: "ICEBERG_TABLE",
    3: "ICEBERG_VIEW",
    4: "GENERIC_TABLE",
}
TASK_TYPE_CODE = 8

# PolarisTaskConstants — the keys Polaris writes into a task entity's internal
# properties. `taskType` is the one that matters: the executor dispatches on it,
# so a row without it can never be handled, and `attemptCount` /
# `lastAttemptStartTime` separate "never picked up" from "tried and failed".
TASK_KEYS = (
    "taskType",
    "attemptCount",
    "lastAttemptStartTime",
    "lastAttemptExecutorId",
    "storageLocation",
)


def _as_dict(raw):
    """Best-effort JSON object from a column that may be None, '', or nested.

    Polaris stores these as TEXT, and `properties.data` is itself a JSON string
    inside the JSON — so this gets called twice on the way in. A row that will
    not parse returns {} rather than taking the whole census down with it.
    """
    if not raw:
        return {}
    if isinstance(raw, dict):
        return raw
    try:
        val = json.loads(raw)
    except (TypeError, ValueError):
        return {}
    return val if isinstance(val, dict) else {}


conn = psycopg2.connect(**PG)
conn.autocommit = True
with conn.cursor() as cur:
    cur.execute("SELECT count(*) FROM polaris_schema.entities")
    print(f"entities total: {cur.fetchone()[0]}\n")

    # Anything named like a probe artifact. 01 names its fixture
    # apiprofile<unix-ts>_* and its children probe_*.
    cur.execute("""
        SELECT name, type_code, sub_type_code, catalog_id, parent_id,
               to_timestamp(create_timestamp/1000) AS created
        FROM polaris_schema.entities
        WHERE name LIKE 'apiprofile%' OR name LIKE 'probe%'
        ORDER BY create_timestamp
    """)
    rows = cur.fetchall()
    print(f"probe-named entities still present: {len(rows)}")
    for n, t, st, cid, pid, ts in rows:
        print(
            f"  {ts:%H:%M:%S}  {TYPE.get(t, t):<15} {SUB.get(st, st):<14} "
            f"catalog={cid:<6} parent={pid:<6} {n}"
        )

    print("\nby type:", dict(Counter(TYPE.get(r[1], r[1]) for r in rows)) or "none")

    # The census. Answers "what is this realm actually made of" in one shot, and
    # is the entity half of the seeding plan's P4 baseline. Read it against the
    # fixture's shape: 1,000 each of PRINCIPAL / PRINCIPAL_ROLE / CATALOG,
    # 2,000 CATALOG_ROLE (owner_principal + the catalog_admin Polaris bootstraps)
    # and 2,000 NAMESPACE. Anything else is either ROOT or accumulation.
    cur.execute("""
        SELECT type_code, count(*), count(drop_timestamp) FILTER (
                   WHERE drop_timestamp IS NOT NULL AND drop_timestamp <> 0)
        FROM polaris_schema.entities
        GROUP BY type_code ORDER BY type_code
    """)
    print(f"\ncensus by type       {'live+dropped':>13} {'soft-deleted':>13}")
    for t, total, dropped in cur.fetchall():
        print(f"  {TYPE.get(t, t):<18} {total:>13} {dropped:>13}")

    # The accumulation itself. TASK rows are created by Polaris when an entity is
    # dropped with purge and are removed only when the task completes; a build
    # that does not delete files (this one -- purge_deletes_files: false, upstream
    # #379) can leave them permanently. `internal_properties` carries taskType,
    # attemptCount and lastAttemptStartTime, which is what distinguishes "never
    # picked up" from "tried and failed" -- a completely different fix each way.
    cur.execute(
        """
        SELECT count(*),
               to_timestamp(min(create_timestamp)/1000),
               to_timestamp(max(create_timestamp)/1000)
        FROM polaris_schema.entities WHERE type_code = %s
    """,
        (TASK_TYPE_CODE,),
    )
    n_tasks, first, last = cur.fetchone()
    print(f"\nTASK entities: {n_tasks}")
    if n_tasks:
        print(f"  oldest {first:%Y-%m-%d %H:%M:%S}   newest {last:%Y-%m-%d %H:%M:%S}")

        # KEYS, not values, and parsed in Python rather than by casting the
        # column to jsonb: the previous run truncated internal_properties at 400
        # chars, cutting off exactly the fields the question turns on, and a
        # single malformed row would take a server-side jsonb cast down with it.
        # 279 rows is nothing to pull across.
        cur.execute(
            """
            SELECT internal_properties, properties
            FROM polaris_schema.entities WHERE type_code = %s
        """,
            (TASK_TYPE_CODE,),
        )
        key_counts, empty_internal, dropped_type = Counter(), 0, Counter()
        unparsed = 0
        for internal, props in cur.fetchall():
            d = _as_dict(internal)
            if not d:
                empty_internal += 1
            key_counts.update(d.keys())
            # `properties.data` is PolarisTaskConstants.TASK_DATA: the dropped
            # entity, serialized as a JSON STRING inside the JSON. Two decodes.
            inner = _as_dict(_as_dict(props).get("data"))
            tc = inner.get("typeCode")
            if tc is None:
                unparsed += 1
            else:
                dropped_type[tc] += 1

        print(f"\n  internal_properties keys across all {n_tasks} TASK rows:")
        print(f"    ({empty_internal} rows carry no internal properties at all)")
        for k, c in key_counts.most_common():
            mark = "  <-- task metadata" if k in TASK_KEYS else ""
            print(f"    {k:<32} {c:>5}{mark}")
        for k in TASK_KEYS:
            if k not in key_counts:
                print(f"    {k:<32} {0:>5}  <-- ABSENT on every row")

        # The verdict this script exists to reach.
        if "taskType" not in key_counts:
            print(
                "\n  VERDICT: no row carries `taskType`. The executor dispatches on\n"
                "  it, so nothing can ever handle these -- they were enqueued and\n"
                "  abandoned at creation. The fix is not in 01's teardown, and\n"
                "  deleting the rows would hide it."
            )
        elif "attemptCount" not in key_counts:
            print(
                "\n  VERDICT: `taskType` is set but not one row was ever attempted --\n"
                "  the task executor is not picking them up. Check Polaris's task\n"
                "  configuration before calling this an upstream bug."
            )
        else:
            print(
                f"\n  VERDICT: {key_counts['attemptCount']} of {n_tasks} rows record\n"
                "  an attempt -- they are being tried and failing. The fix is\n"
                "  wherever they fail; check the Polaris log for that task type."
            )

        # What each task was created FOR. This is what makes "exactly 4 per 01
        # run" legible: 01 drops a table, a view, a principal-role and a
        # catalog-role, and each one leaves a row behind.
        print("\n  cleanup tasks by the type of entity that was dropped:")
        for tc, c in dropped_type.most_common():
            print(f"    {TYPE.get(tc, tc):<18} {c:>5}")
        if unparsed:
            print(f"    {'(unparsed)':<18} {unparsed:>5}")

    # Fallback: the newest rows regardless of name.
    cur.execute("""
        SELECT name, type_code, sub_type_code, catalog_id,
               to_timestamp(create_timestamp/1000) AS created,
               drop_timestamp, purge_timestamp
        FROM polaris_schema.entities
        ORDER BY create_timestamp DESC LIMIT 12
    """)
    print("\n12 most recently created entities:")
    for n, t, st, cid, ts, dts, pts in cur.fetchall():
        flag = ""
        if dts:
            flag += f" DROPPED(drop_ts={dts}"
            flag += f", purge_ts={pts})" if pts else ", not purged)"
        print(f"  {ts:%m-%d %H:%M:%S}  {TYPE.get(t, t):<15} catalog={cid:<6} {n}{flag}")
conn.close()
