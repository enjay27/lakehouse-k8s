#!/usr/bin/env python3
"""Why does create_catalog 500 with grantee_not_found? Evidence, not a guess.

    python3 diagnose_catalog_bootstrap.py

WHAT THE SOURCE SAYS THE FAILURE IS
-----------------------------------
Traced in TransactionalMetaStoreManagerImpl.persistNewGrantRecord (1.3.0): on
create_catalog Polaris writes the `catalog_admin` catalog-role, writes a grant
to it, then LOOKS IT BACK UP to bump its grants-version:

    ms.writeToGrantRecordsInCurrentTxn(callCtx, grantRecord);
    PolarisBaseEntity granteeEntity =
        ms.lookupEntityInCurrentTxn(catalogId, id, typeCode);   // <- returns null
    checkNotNull(granteeEntity, "grantee_not_found", ...);       // <- 500 here

`lookupEntity` on the JDBC backend is a plain SELECT by
(realm_id, catalog_id, id, type_code) -- no cache, no drop_timestamp filter. So
if it returns null, the row it just wrote is not visible to the very next read.

TWO CANDIDATE CAUSES, AND HOW THIS TELLS THEM APART
---------------------------------------------------
1. READ-AFTER-WRITE LAG. Polaris reads through Pgpool; if a read in the same
   logical operation lands on a replica that has not caught up, the just-written
   catalog_admin is invisible. This cluster has a measured, load-dependent
   version of exactly this. TELL: replication is lagging, AND the catalog_admin
   rows for the failed attempts ARE present in the table on the primary.

2. STALE ENTITY CACHE AFTER THE DROP. If Polaris was not restarted since the
   schema was dropped and re-bootstrapped, InMemoryEntityCache may hold entries
   from the old realm and disagree with the tables. TELL: a restart fixes it and
   nothing in the DB looks wrong.

This script writes NOTHING. It reads replication state, the connection routing,
and whether the residue of the failed create_catalog attempts is sitting on the
primary.
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


def q(cur, sql, params=None, pin=True):
    cur.execute((api_trace.NO_LOAD_BALANCE if pin else "") + sql, params)
    return cur.fetchall()


def main():
    import psycopg2

    conn = psycopg2.connect(**PG)
    conn.autocommit = True
    cur = conn.cursor()

    print("=" * 64)
    print("ROUTING — is this connection even on the primary?")
    print("=" * 64)
    standby = q(cur, "SELECT pg_is_in_recovery()")[0][0]
    print(
        f"  pg_is_in_recovery() = {standby}  "
        f"({'STANDBY — reads here are already stale' if standby else 'primary'})"
    )
    # Ask the SAME question WITHOUT the pin, to see where an unpinned read (what
    # Polaris issues for most SELECTs) would land.
    unpinned = q(cur, "SELECT pg_is_in_recovery()", pin=False)[0][0]
    print(
        f"  without /*NO LOAD BALANCE*/  = {unpinned}  "
        f"(where an UNPINNED Polaris read may go)"
    )
    if unpinned and not standby:
        print("  ** An unpinned read is being routed to a STANDBY while the")
        print("     pinned one hits the primary. That is the read-after-write")
        print("     hazard, live, on the same connection. **")

    print("\n" + "=" * 64)
    print("REPLICATION — how far behind is each standby?")
    print("=" * 64)
    repl = q(
        cur,
        """SELECT application_name, state,
                     pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn) AS behind
                     FROM pg_stat_replication ORDER BY behind DESC NULLS LAST""",
    )
    if not repl:
        print("  pg_stat_replication is EMPTY on this node.")
        print("  Either this is not the primary, or no standby is streaming.")
    for name, state, behind in repl:
        flag = ""
        if behind and behind > 1_000_000:
            flag = "   <- ~{:.1f} MB behind, reads here would be badly stale".format(
                behind / 1e6
            )
        elif behind and behind > 0:
            flag = f"   <- {behind:,} bytes behind"
        print(
            f"  {name or '(none)':<24} {state or '?':<12} "
            f"behind={behind if behind is not None else 'n/a'}{flag}"
        )

    print("\n" + "=" * 64)
    print("RESIDUE — did the failed create_catalog attempts leave rows?")
    print("=" * 64)
    # If catalog_admin rows for the failed catalogs ARE on the primary, the
    # write half succeeded and only the read-back failed -> cause #1. If they
    # are absent, the whole transaction rolled back -> look elsewhere.
    cats = q(
        cur,
        f"""SELECT count(*) FROM {SCHEMA}.entities
                      WHERE realm_id = %s AND type_code = 4""",
        (REALM,),
    )[0][0]
    admins = q(
        cur,
        f"""SELECT count(*) FROM {SCHEMA}.entities
                        WHERE realm_id = %s AND type_code = 5
                          AND name = 'catalog_admin'""",
        (REALM,),
    )[0][0]
    orphan_cat = q(
        cur,
        f"""SELECT count(*) FROM {SCHEMA}.entities c
                            WHERE c.realm_id = %s AND c.type_code = 4
                              AND NOT EXISTS (
                                SELECT 1 FROM {SCHEMA}.entities r
                                WHERE r.realm_id = c.realm_id
                                  AND r.catalog_id = c.id
                                  AND r.type_code = 5
                                  AND r.name = 'catalog_admin')""",
        (REALM,),
    )[0][0]
    print(f"  catalogs (type 4)              : {cats:,}")
    print(f"  catalog_admin roles (type 5)   : {admins:,}")
    print(f"  catalogs with NO catalog_admin : {orphan_cat:,}")
    if orphan_cat:
        print("\n  Catalogs exist without their catalog_admin. The create wrote")
        print("  the catalog and then failed before/at the role bootstrap. That")
        print("  is the non-atomic-creation signature, here at scale.")

    print("\n" + "=" * 64)
    print("READ IT")
    print("=" * 64)
    print("""\
  unpinned read -> STANDBY, or a standby MB behind
        => READ-AFTER-WRITE LAG. Polaris writes catalog_admin to the primary and
           reads it back off a lagging replica. This is not fixed by a restart.
           Options, cheapest first:
             - if replication is simply catching up, wait and re-seed;
             - pin Polaris's datasource to the primary (jdbc url to the
               postgresql-0 service, or Pgpool black-listing the SELECT), which
               is a deployment change and needs sign-off;
             - seed with a smaller --users and a delay so lag stays bounded.

  replication healthy AND nothing looks wrong in the DB
        => STALE CACHE. Polaris was not restarted after the drop+rebootstrap.
           kubectl rollout restart deploy/benchmarks-polaris -n datahub-hynix
           then re-run triage_realm.py before re-seeding.

  Run this WHILE a seed is failing, not after — replication lag is a moment in
  time, and an idle cluster hides it.""")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
