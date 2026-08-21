#!/usr/bin/env python3
"""Record the exact SQL every entity-creation API emits.

SUPERSEDED FOR ITS ORIGINAL PURPOSE — READ THIS FIRST
-----------------------------------------------------
This was written to recover write statements from the PostgreSQL server log.
It turns out **notebook 01 already captured them from Polaris's own log**, and
`reports/doc-api-sql-matrix-latest.md` already contains every one:

    INSERT INTO POLARIS_SCHEMA.ENTITIES        (17 columns, order recorded)
    INSERT INTO POLARIS_SCHEMA.GRANT_RECORDS   (6 columns, order recorded)
    INSERT INTO POLARIS_SCHEMA.PRINCIPAL_AUTHENTICATION_DATA
    UPDATE      POLARIS_SCHEMA.ENTITIES
    DELETE FROM ENTITIES / GRANT_RECORDS / POLICY_MAPPING_RECORD / PRINCIPAL_AUTHENTICATION_DATA

**A create writes exactly two tables**: `entities` and `grant_records`. There is
no INSERT into `policy_mapping_record` (it appears only in teardown DELETEs) and
**zero `events` traffic on any traced path**. That is the question a replay
needed answered, and it was answered before this file existed.

Polaris logs `?` placeholders, not values. That is not a gap for a synthetic
replay: ids, names and timestamps are generated, and the two JSONB columns are
copied from a live row with `INSERT ... SELECT`. The only thing the values would
have added is `principal_authentication_data`, which is skipped entirely when
the cloned principals are never authenticated.

So this file remains useful only for confirming the write path after a Polaris
upgrade, or for recovering the four statements that sit at NO_PARAMS in the
audit. For the replay, read the matrix.

---

Original purpose follows.

WHY
---
Creating a 10,000-user realm over REST is ~610,000 API calls and ~8.5 hours.
Replaying the SQL those calls emit is one `INSERT ... SELECT generate_series`
per table. The only thing standing between the two is knowing *precisely* what
Polaris writes -- which tables, which columns, in which order -- and that is not
something to infer from the schema and hope.

So: issue ONE of each create over REST with PostgreSQL statement logging on, and
read back what actually happened.

WHY THE POSTGRESQL LOG AND NOT POLARIS'S
----------------------------------------
Polaris's `DatasourceOperations` DEBUG stream gives statements correlated to the
API that issued them, which is what notebook 01 uses. But four write statements
have sat at **NO_PARAMS** through every audit so far -- `resolve_params` refuses
them because the placeholder count spans SET/VALUES -- so their VALUES have
never been recovered, and values are exactly what a replay needs.

PostgreSQL's own log has them:

    LOG:  execute <unnamed>: INSERT INTO entities (...) VALUES ($1, $2, ...)
    DETAIL:  parameters: $1 = 'POLARIS', $2 = '0', ...

`api_trace.parse_pg_log` already parses that shape, pid-aware, and already
redacts every parameter of any statement touching
`principal_authentication_data` (`api_trace.SECRET_TABLES`). That redaction is
deliberate and stays: the auth row cannot be replayed from a capture, and must
be CLONED instead -- copy an existing row's `main_secret_hash` and `secret_salt`
under a new `principal_id`/`principal_client_id`, and the clone authenticates
with the secret of the principal it was cloned from.

TWO GATES, BOTH ALREADY CHECKED
-------------------------------
* **No sequence table.** `schema-v3.sql` declares six tables -- `version`,
  `entities`, `grant_records`, `principal_authentication_data`,
  `policy_mapping_record`, `events` -- and no `CREATE SEQUENCE`. Ids are
  generated in the application, so bulk inserts cannot desynchronise a database
  allocator. Still choose ids from a range disjoint from live data.
* **No foreign key on `grant_records`.** Measured 2026-08-21.

HOW IT DELIMITS
---------------
Correlating the PostgreSQL log back to an API is awkward -- Polaris's requestId
is in ITS log, not the server's. So each REST call is bracketed by a marker
statement issued on our own connection:

    SELECT '<<<polaris-write-capture api=create_catalog phase=begin>>>'

Markers land in the same log file in chronological order, so the statements
between two markers are that call's. Crude, and it does not depend on parsing
anything Polaris chose to emit.

USAGE
-----
    ./capture.sh pgon                       # statement logging must be ON
    python3 capture_write_templates.py
    ./capture.sh pgoff                      # turn it back off before any timing

Read the output before designing a replay. Designing it from the schema instead
is the guess this file exists to avoid.
"""

import argparse
import json
import os
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE
while not (REPO / "src").is_dir() and REPO != REPO.parent:
    REPO = REPO.parent
sys.path.insert(0, str(REPO / "src"))

import api_trace  # noqa: E402
from iceberg_rest import IcebergREST  # noqa: E402
from polaris_rest import PolarisREST  # noqa: E402
from polaris_seed import delete_catalog_fully  # noqa: E402

POLARIS_URL = os.environ.get("POLARIS_URL", "http://192.168.139.2:8181")
REALM = os.environ.get("POLARIS_REALM", "POLARIS")
ROOT_CLIENT = os.environ.get("POLARIS_ROOT_CLIENT", "root")
ROOT_SECRET = os.environ.get("POLARIS_ROOT_SECRET", "polaris-secret")
MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "http://192.168.139.2:9000")
BUCKET = os.environ.get("MINIO_BUCKET", "data-catalog-bucket")

PG = dict(
    host=os.environ.get("PG_HOST", "192.168.139.2"),
    port=int(os.environ.get("PG_PORT", "5432")),
    dbname=os.environ.get("PG_DB", "polaris"),
    user=os.environ.get("PG_USER", "polaris"),
    password=os.environ.get("PG_PASSWORD", "polaris"),
)

MARKER = "<<<polaris-write-capture api={api} phase={phase}>>>"


def marker(conn, api, phase):
    """Emit a delimiter into the server log on our own connection."""
    with conn.cursor() as cur:
        cur.execute(f"SELECT '{MARKER.format(api=api, phase=phase)}'")


def log_files(capture_dir):
    return sorted(capture_dir.glob("pg-*.log"))


def read_since(files, offsets):
    """Only the bytes appended since `offsets` -- the history is irrelevant and
    these files reach hundreds of MB with logging on."""
    chunks = []
    for f in files:
        try:
            with open(f, "r", encoding="utf-8", errors="replace") as fh:
                fh.seek(offsets.get(f, 0))
                chunks.append(fh.read())
        except OSError:
            continue
    return "\n".join(chunks)


def build_fixture(pc, ic, stamp):
    """One of each create, each bracketed by markers.

    Deliberately ONE of each: the point is the statement shape, and a second
    instance would only add log volume. Table and view creation come last so a
    failure there still leaves the metadata-only statements captured.
    """
    n = {
        "principal": f"wtc{stamp}_principal",
        "principal_role": f"wtc{stamp}_principal_role",
        "catalog": f"wtc{stamp}_catalog",
        "catalog_role": f"wtc{stamp}_catalog_role",
        "namespace": "wtc_ns",
        "table": "wtc_tbl",
    }
    steps = [
        ("create_principal", lambda: pc.create_principal(n["principal"])),
        (
            "create_principal_role",
            lambda: pc.create_principal_role(n["principal_role"]),
        ),
        (
            "assign_principal_role",
            lambda: pc.assign_principal_role_to_principal(
                n["principal"], n["principal_role"]
            ),
        ),
        (
            "create_catalog",
            lambda: pc.create_catalog(
                n["catalog"], bucket=BUCKET, minio_endpoint=MINIO_ENDPOINT
            ),
        ),
        (
            "create_catalog_role",
            lambda: pc.create_catalog_role(n["catalog"], n["catalog_role"]),
        ),
        (
            "assign_catalog_role",
            lambda: pc.assign_catalog_role_to_principal_role(
                n["catalog"], n["principal_role"], n["catalog_role"]
            ),
        ),
        (
            "grant_privilege",
            lambda: pc.grant_privilege(
                n["catalog"],
                n["catalog_role"],
                "TABLE_READ_DATA",
                skip_if_present=False,
            ),
        ),
        (
            "create_namespace",
            lambda: ic.create_namespace(n["catalog"], n["namespace"]),
        ),
        (
            "create_table",
            lambda: ic.create_table(
                n["catalog"],
                n["namespace"],
                {
                    "name": n["table"],
                    "schema": {
                        "type": "struct",
                        "schema-id": 0,
                        "fields": [
                            {"id": 1, "name": "id", "required": True, "type": "long"}
                        ],
                    },
                },
            ),
        ),
    ]
    return n, steps


def slice_by_marker(statements, api):
    """Statements between this API's begin and end markers."""
    begin = MARKER.format(api=api, phase="begin")
    end = MARKER.format(api=api, phase="end")
    lo = hi = None
    for i, st in enumerate(statements):
        if begin in (st.sql or ""):
            lo = i
        elif end in (st.sql or "") and lo is not None:
            hi = i
            break
    if lo is None or hi is None:
        return []
    return [
        st
        for st in statements[lo + 1 : hi]
        if "polaris-write-capture" not in (st.sql or "")
    ]


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--keep", action="store_true", help="do not tear the fixture down")
    args = ap.parse_args()

    import psycopg2

    capture = api_trace.find_capture_dir(roots=(HERE, REPO))
    if capture is None:
        sys.exit("no capture* directory found; run ./capture.sh first")
    files = log_files(capture)
    if not files:
        sys.exit(f"no pg-*.log under {capture}; is the PostgreSQL log tail running?")
    print(f"capture dir : {capture}")
    print(f"pg logs     : {[f.name for f in files]}")

    offsets = {f: f.stat().st_size for f in files}

    pc = PolarisREST(POLARIS_URL, REALM)
    r = pc.get_token(ROOT_CLIENT, ROOT_SECRET)
    if r.status_code >= 300:
        sys.exit(f"auth failed [{r.status_code}]: {r.text[:200]}")
    pc.token = r.json()["access_token"]
    ic = IcebergREST(POLARIS_URL, REALM, token=pc.token)

    conn = psycopg2.connect(**PG)
    conn.autocommit = True

    stamp = int(time.time())
    names, steps = build_fixture(pc, ic, stamp)
    print(f"fixture     : wtc{stamp}_*\n")

    results = {}
    try:
        for api, call in steps:
            marker(conn, api, "begin")
            resp = call()
            marker(conn, api, "end")
            ok = resp.status_code < 300
            results[api] = {"status": resp.status_code, "ok": ok}
            print(f"  {api:<24} {resp.status_code}")
            if not ok:
                print(f"      {resp.text[:160]}")
            time.sleep(0.3)  # let the log flush before the next marker
    finally:
        time.sleep(1.0)
        text = read_since(files, offsets)
        if not text.strip():
            print("\nNOTHING WAS LOGGED. Statement logging is off — run")
            print("    ./capture.sh pgon")
            print("and try again. Continuing would report 'no writes' for every")
            print("API, which is indistinguishable from a real finding.")
        if not args.keep:
            print("\ntearing down…")
            # delete_catalog_fully, NOT delete_catalog: a catalog carrying a
            # non-default catalog-role refuses deletion with 400. This teardown
            # used the bare call and got exactly that -- the second time the
            # same mistake stranded a catalog in this directory, after
            # delete_catalog_fully had already been written for the first.
            ok, d = delete_catalog_fully(pc, names["catalog"])
            print(f"  {'catalog':<16} {'deleted' if ok else d.status_code}")
            if not ok:
                print(f"      {(d.text or '')[:300]}")
            for label, call in (
                (
                    "principal_role",
                    lambda: pc.delete_principal_role(names["principal_role"]),
                ),
                ("principal", lambda: pc.delete_principal(names["principal"])),
            ):
                try:
                    d = call()
                    print(f"  {label:<16} {d.status_code}")
                except Exception as exc:  # noqa: BLE001
                    print(f"  {label:<16} {type(exc).__name__}")
        conn.close()

    stmts = api_trace.parse_pg_log(text)
    print(f"\nparsed {len(stmts)} statements from the appended log\n")

    out = {}
    for api, _ in steps:
        block = slice_by_marker(stmts, api)
        rows = []
        for st in block:
            rows.append(
                {
                    "table": getattr(st, "table", None),
                    "verb": getattr(st, "verb", None),
                    "sql": " ".join((st.sql or "").split()),
                    "params": st.params,
                    "duration_ms": st.duration_ms,
                }
            )
        out[api] = {"result": results.get(api), "statements": rows}
        writes = [
            r
            for r in rows
            if (r["verb"] or "").upper() in ("INSERT", "UPDATE", "DELETE")
        ]
        print(f"{api:<24} {len(rows):>3} statements, {len(writes):>2} writes")
        for w in writes:
            print(f"    {w['verb']:<7} {w['table']}")
            print(f"      {w['sql'][:150]}")
            print(f"      params: {str(w['params'])[:150]}")

    path = HERE / f"write-templates-{stamp}.json"
    path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(f"\nwrote {path}")
    print("\nRead the WRITE statements above before designing a bulk replay.")
    print("Every table that appears is one the replay has to populate; any it")
    print("misses leaves a realm that looks right and behaves oddly. Note that")
    print("principal_authentication_data parameters are REDACTED by design —")
    print("that row is cloned, not replayed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
