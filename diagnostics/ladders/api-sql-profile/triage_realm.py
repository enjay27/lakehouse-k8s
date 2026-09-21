#!/usr/bin/env python3
"""Read-only damage assessment after data loss. Writes NOTHING.

    python3 triage_realm.py

Answers the only question that decides what happens next: **did the bootstrap
survive?** Everything in this realm is synthetic and re-creatable in minutes
EXCEPT the root principal, its credentials and the `service_admin` role. Those
are created once, when Polaris bootstraps a realm, and nothing in this repo can
put them back -- without them there is no identity that can call an API, so the
recovery path stops being "re-seed" and becomes "re-bootstrap the realm".

It also looks for orphans, because a delete that took `entities` but not
`principal_authentication_data` leaves credential rows pointing at principals
that no longer exist. Those are invisible to every API and will quietly outlive
the next rebuild.
"""

import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE
while not (REPO / "src").is_dir() and REPO != REPO.parent:
    REPO = REPO.parent
sys.path.insert(0, str(REPO / "src"))

import api_trace  # noqa: E402

PG = dict(
    host=os.environ.get("PG_HOST", "192.168.139.2"),
    port=int(os.environ.get("PG_PORT", "5432")),
    dbname=os.environ.get("PG_DB", "polaris"),
    user=os.environ.get("PG_USER", "polaris"),
    password=os.environ.get("PG_PASSWORD", "polaris"),
)
SCHEMA = os.environ.get("PG_SCHEMA", "polaris_schema")
REALM = os.environ.get("POLARIS_REALM", "POLARIS")

TABLES = (
    "version",
    "entities",
    "grant_records",
    "principal_authentication_data",
    "policy_mapping_record",
    "events",
)

#: Verified against PolarisPrivilege.java at tag apache-polaris-1.3.0-incubating
#: (2026-08-21), NOT transcribed from a REST spec. The distinction matters: the
#: hand-rolled bootstrap wrote 11 and 12, which are NAMESPACE_LIST and
#: TABLE_LIST in that enum, and this script reported the bootstrap "OK" because
#: it counted the grants without reading what they conferred.
SERVICE_MANAGE_ACCESS = 1
PRINCIPAL_ROLE_USAGE = 4
PRIVILEGE_NAMES = {
    1: "SERVICE_MANAGE_ACCESS",
    4: "PRINCIPAL_ROLE_USAGE",
    11: "NAMESPACE_LIST",
    12: "TABLE_LIST",
    25: "CATALOG_CREATE",
    44: "PRINCIPAL_CREATE",
    54: "PRINCIPAL_ROLE_CREATE",
}

TYPE_NAMES = {
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


def q(cur, sql, params=None):
    cur.execute(api_trace.NO_LOAD_BALANCE + sql, params)
    return cur.fetchall()


def main():
    import psycopg2

    conn = psycopg2.connect(**PG)
    conn.autocommit = True
    with conn.cursor() as cur:
        assert not q(cur, "SELECT pg_is_in_recovery()")[0][0], (
            "routed to a STANDBY -- a replica may lag the primary, so counts "
            "read here could understate what actually survived. Connect direct."
        )

        print("=" * 62)
        print("ROW COUNTS")
        print("=" * 62)
        counts = {}
        for t in TABLES:
            try:
                counts[t] = q(cur, f"SELECT count(*) FROM {SCHEMA}.{t}")[0][
                    0
                ]  # noqa: S608
                print(f"  {t:<32} {counts[t]:>10,}")
            except psycopg2.Error as exc:
                counts[t] = None
                print(f"  {t:<32} {'MISSING':>10}  <- {str(exc).splitlines()[0]}")
                conn.rollback() if not conn.autocommit else None

        if counts.get("entities") is None:
            print("\nThe `entities` TABLE is gone, not just its rows. This is a")
            print("schema-level loss: re-create the schema from Polaris's own")
            print("`schema-v3.sql` before anything else.")
            return 2

        print()
        print("=" * 62)
        print("BY REALM -- the counts above are WHOLE-TABLE, not this realm")
        print("=" * 62)
        # Added after the first live run: `entities` totalled 6 while realm
        # POLARIS held 3. The block above counts the whole table and everything
        # below it filters by realm, so reading the two together silently
        # invents rows. A second bootstrapped realm is the ordinary
        # explanation; render it rather than leave the discrepancy to be
        # rationalised.
        for realm_id, n in q(
            cur,
            f"""SELECT realm_id, count(*) FROM {SCHEMA}.entities
                GROUP BY realm_id ORDER BY count(*) DESC""",  # noqa: S608
        ):
            mark = "  <- this run" if realm_id == REALM else ""
            print(f"  {realm_id:<40} {n:>8,}{mark}")

        print()
        print("=" * 62)
        print("WHAT SURVIVED, BY TYPE")
        print(f"(realm {REALM} only)")
        print("=" * 62)
        rows = q(
            cur,
            f"""SELECT type_code, count(*), min(name), max(name)
                FROM {SCHEMA}.entities WHERE realm_id = %s
                GROUP BY type_code ORDER BY type_code""",  # noqa: S608
            (REALM,),
        )
        if not rows:
            print("  (nothing at all in this realm)")
        for tc, n, lo, hi in rows:
            print(f"  {tc:>3} {TYPE_NAMES.get(tc, '?'):<16} {n:>8,}  {lo} .. {hi}")

        print()
        print("=" * 62)
        print("THE BOOTSTRAP -- this is the answer that matters")
        print("=" * 62)
        checks = [
            (
                "ROOT container (type 1)",
                "SELECT count(*) FROM {s}.entities "
                "WHERE realm_id = %s AND type_code = 1",
                (REALM,),
            ),
            (
                "root principal",
                "SELECT count(*) FROM {s}.entities "
                "WHERE realm_id = %s AND type_code = 2 AND name = 'root'",
                (REALM,),
            ),
            (
                "service_admin role",
                "SELECT count(*) FROM {s}.entities "
                "WHERE realm_id = %s AND type_code = 3 AND name = 'service_admin'",
                (REALM,),
            ),
            (
                "root credentials",
                "SELECT count(*) FROM {s}."
                "principal_authentication_data pad JOIN {s}.entities e "
                "ON e.id = pad.principal_id AND e.realm_id = pad.realm_id "
                "WHERE pad.realm_id = %s AND e.name = 'root'",
                (REALM,),
            ),
            (
                "service_admin holds SERVICE_MANAGE_ACCESS",
                "SELECT count(*) FROM {s}.grant_records g "
                "JOIN {s}.entities e ON e.id = g.grantee_id AND e.realm_id = g.realm_id "
                f"WHERE g.realm_id = %s AND e.name = 'service_admin' "
                f"AND g.privilege_code = {SERVICE_MANAGE_ACCESS}",
                (REALM,),
            ),
            (
                "root holds PRINCIPAL_ROLE_USAGE",
                "SELECT count(*) FROM {s}.grant_records g "
                "JOIN {s}.entities e ON e.id = g.grantee_id AND e.realm_id = g.realm_id "
                f"WHERE g.realm_id = %s AND e.name = 'root' "
                f"AND g.privilege_code = {PRINCIPAL_ROLE_USAGE}",
                (REALM,),
            ),
        ]
        alive = True
        for label, sql, params in checks:
            n = q(cur, sql.format(s=SCHEMA), params)[0][0]
            ok = n > 0
            alive = alive and ok
            print(f"  {'OK ' if ok else 'GONE'}  {label:<28} {n:>6,}")

        print()
        print("=" * 62)
        print("WHAT THE BOOTSTRAP GRANTS ACTUALLY CONFER")
        print("=" * 62)
        # Counting these rows is not the same as reading them. An earlier
        # version of this script did the former, printed "bootstrap SURVIVED",
        # and the very next command failed 403 on CREATE_PRINCIPAL because
        # service_admin's one grant was NAMESPACE_LIST.
        for gid, pc, n in q(
            cur,
            f"""SELECT grantee_id, privilege_code, count(*)
                FROM {SCHEMA}.grant_records
                WHERE realm_id = %s AND grantee_id IN (1, 2)
                GROUP BY grantee_id, privilege_code
                ORDER BY grantee_id""",  # noqa: S608
            (REALM,),
        ):
            who = {1: "root", 2: "service_admin"}.get(gid, str(gid))
            name = PRIVILEGE_NAMES.get(pc, "?")
            flag = (
                ""
                if pc in (SERVICE_MANAGE_ACCESS, PRINCIPAL_ROLE_USAGE)
                else "  <- WRONG"
            )
            print(f"  {who:<14} code {pc:>3}  {name:<22} x{n}{flag}")

        print()
        print("=" * 62)
        print("ORPHANS -- rows pointing at entities that no longer exist")
        print("=" * 62)
        orphan_creds = q(
            cur,
            f"""SELECT count(*) FROM {SCHEMA}.principal_authentication_data pad
                WHERE pad.realm_id = %s AND NOT EXISTS (
                  SELECT 1 FROM {SCHEMA}.entities e
                  WHERE e.realm_id = pad.realm_id AND e.id = pad.principal_id)""",  # noqa: S608
            (REALM,),
        )[0][0]
        orphan_grants = q(
            cur,
            f"""SELECT count(*) FROM {SCHEMA}.grant_records g
                WHERE g.realm_id = %s AND NOT EXISTS (
                  SELECT 1 FROM {SCHEMA}.entities e
                  WHERE e.realm_id = g.realm_id AND e.id = g.grantee_id)""",  # noqa: S608
            (REALM,),
        )[0][0]
        print(f"  credentials with no principal   {orphan_creds:>8,}")
        print(f"  grants with no grantee          {orphan_grants:>8,}")
        if orphan_creds or orphan_grants:
            print("\n  These are invisible to every API and will outlive a rebuild.")
            print("  Clean them only AFTER the bootstrap question is settled --")
            print("  root's own credential row is in that table.")

        print()
        print("=" * 62)
        print("INDEX")
        print("=" * 62)
        idx = q(
            cur,
            "SELECT indexrelid::regclass::text, indisvalid, indisready "
            "FROM pg_index i JOIN pg_class c ON c.oid = i.indrelid "
            "JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname = %s AND c.relname = 'grant_records'",
            (SCHEMA,),
        )
        for name, valid, ready in idx:
            print(f"  {name:<52} valid={valid} ready={ready}")

        print()
        print("=" * 62)
        print("VERDICT")
        print("=" * 62)
        if alive:
            print("  The bootstrap SURVIVED **and its grants confer what they")
            print("  must**. Root can authenticate AND create principals.")
            print("  Root can still authenticate, so the")
            print("  fixture is re-creatable from this repo's own tooling.")
            print()
            print("  And it is far cheaper than it was in July: 02c needs exactly")
            print("  TWO real user-sets -- one to target, one as the warm-up decoy")
            print("  -- because volume now comes from clones. Seed two by API in")
            print("  seconds, clone the rest.")
            print()
            print("  What is NOT recoverable is comparability with 02's numbers:")
            print("  those were measured at 30,009 grant_records with a specific")
            print("  grantee distribution (p50 1, p95 25, max 1,006). A rebuilt")
            print("  fixture will not reproduce it. 02's plan-shape evidence is")
            print("  committed and stands; its millisecond table is now a")
            print("  historical measurement of a fixture that no longer exists.")
            return 0

        print("  The bootstrap is INCOMPLETE. Read the two blocks above to see")
        print("  which half failed -- they are different problems:")
        print()
        print("  * ENTITIES or CREDENTIALS missing -> root cannot authenticate")
        print("    at all. Nothing here can re-create root; its secret is hashed")
        print("    with a salt only the bootstrap knew. Re-bootstrap the realm.")
        print()
        print("  * ENTITIES present but a grant carries the WRONG CODE -> root")
        print("    authenticates, service_admin activates, and every write is")
        print("    still 403. That is a two-row repair, not a rebuild:")
        print("       psql -f diagnostics/api-sql-profile/repair_bootstrap_grants.sql")
        print("       then RESTART Polaris -- the cache holds entities WITH")
        print("       their grants, so it keeps enforcing what it already read.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
