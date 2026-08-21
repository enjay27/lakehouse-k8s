#!/usr/bin/env python3
"""Does a cloned credential row authenticate? Live probe, self-cleaning.

    python3 probe_cloned_credentials.py
    python3 probe_cloned_credentials.py --keep     # leave the clone behind

THE CLAIM UNDER TEST
--------------------
`PLAN-api-latency-sweep.md` §2a states, as fact:

    "Clone it with a new id and client_id but the same hash and salt, and the
     clone authenticates with the secret of the principal it was cloned from --
     no hash scheme to reverse-engineer."

That was reasoned from `bootstrap.sql`'s comment, `SHA256(secret + ':' + salt)`,
which implies the hash binds to the SECRET and the SALT and to nothing else --
not the client_id, not the principal_id. If true, one API-minted credential
yields unlimited authenticable identities by INSERT.

It has never been run. The same reasoning-from-a-comment produced the
25-privilege list, the catalog `catalog_id` shape and privilege codes 11 and 12,
all three of which were wrong. So: ask the server.

WHY IT MATTERS
--------------
02c can currently only measure identities whose credentials it mints one REST
call at a time. If cloning works, `entity_replay` can produce thousands of
distinct authenticable principals by SQL, and the grant-set-size axis becomes a
curve instead of a two-point contrast.

THE NEGATIVE CONTROL IS NOT OPTIONAL
------------------------------------
"The clone authenticated" is consistent with two very different worlds: the
hash does not bind to identity, or this deployment is not checking the secret
at all. The probe therefore also tries the clone's client_id with a WRONG
secret and REQUIRES that to fail. Without that, a pass proves nothing.

It also checks that the minted token AUTHORIZES something, because a token that
issues and then resolves no grants would be a trap for anything built on top.
"""

import argparse
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE
while not (REPO / "src").is_dir() and REPO != REPO.parent:
    REPO = REPO.parent
sys.path.insert(0, str(REPO / "src"))

import api_trace  # noqa: E402
import entity_replay  # noqa: E402
from polaris_rest import PolarisREST  # noqa: E402

PG = dict(
    host=os.environ.get("PG_HOST", "192.168.139.2"),
    port=int(os.environ.get("PG_PORT", "5432")),
    dbname=os.environ.get("PG_DB", "polaris"),
    user=os.environ.get("PG_USER", "polaris"),
    password=os.environ.get("PG_PASSWORD", "polaris"),
)
SCHEMA = os.environ.get("PG_SCHEMA", "polaris_schema")
REALM = os.environ.get("POLARIS_REALM", "POLARIS")
POLARIS_URL = os.environ.get("POLARIS_URL", "http://192.168.139.2:8181")
ROOT_CLIENT = os.environ.get("POLARIS_ROOT_CLIENT", "root")
ROOT_SECRET = os.environ.get("POLARIS_ROOT_SECRET", "polaris-secret")

#: Its own prefix, not `sqlclone`. Deletion keys on the name, and mixing this
#: probe's rows in with the sweep's fixture would make one `--remove` ambiguous.
PROBE_PREFIX = "credprobe"

AUTH_COLUMNS = (
    "realm_id",
    "principal_id",
    "principal_client_id",
    "main_secret_hash",
    "secondary_secret_hash",
    "secret_salt",
)


def connect():
    import psycopg2

    if not any(h in PG["host"] for h in ("localhost", "127.0.0.1", "192.168.")):
        sys.exit(f"refusing to write to a non-local PostgreSQL: {PG['host']}")
    conn = psycopg2.connect(**PG)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("/*NO LOAD BALANCE*/ SELECT pg_is_in_recovery()")
        if cur.fetchone()[0]:
            sys.exit("routed to a STANDBY; connect to the primary directly")
    return conn


def root_client():
    pc = PolarisREST(POLARIS_URL, REALM)
    r = pc.get_token(ROOT_CLIENT, ROOT_SECRET)
    if r.status_code >= 300:
        sys.exit(f"root auth failed [{r.status_code}]: {r.text[:200]}")
    pc.token = r.json()["access_token"]
    return pc


def read_source(conn, principal_name):
    """The source principal's entity row and its credential row."""
    cols = ", ".join(entity_replay.ENTITY_COLUMNS)
    acols = ", ".join(AUTH_COLUMNS)
    with conn.cursor() as cur:
        cur.execute(
            api_trace.NO_LOAD_BALANCE
            + f"SELECT {cols} FROM {SCHEMA}.entities "  # noqa: S608
            "WHERE realm_id = %s AND type_code = 2 AND name = %s",
            (REALM, principal_name),
        )
        ent = cur.fetchone()
        if not ent:
            sys.exit(f"no principal named {principal_name!r} in realm {REALM}")
        cur.execute(
            api_trace.NO_LOAD_BALANCE
            + f"SELECT {acols} FROM {SCHEMA}.principal_authentication_data "  # noqa: S608
            "WHERE realm_id = %s AND principal_id = %s",
            (REALM, ent[0]),
        )
        auth = cur.fetchone()
        if not auth:
            sys.exit(
                f"{principal_name} has no principal_authentication_data row. "
                "Reset its credentials over REST first, or pick another."
            )
    return ent, auth


def insert_clone(conn, ent, auth, new_id, name, client_id):
    """One principal entity + one credential row carrying the SAME hash+salt."""
    from psycopg2.extras import Json

    ecols = ", ".join(entity_replay.ENTITY_COLUMNS)
    acols = ", ".join(AUTH_COLUMNS)
    row = list(ent)
    row[0] = new_id
    row[4] = name
    row = [Json(v) if i in (12, 13) and v is not None else v for i, v in enumerate(row)]
    with conn.cursor() as cur:
        cur.execute(
            f"INSERT INTO {SCHEMA}.entities ({ecols}) "  # noqa: S608
            f"VALUES ({', '.join(['%s'] * len(entity_replay.ENTITY_COLUMNS))})",
            row,
        )
        cur.execute(
            f"INSERT INTO {SCHEMA}.principal_authentication_data ({acols}) "  # noqa: S608
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (REALM, new_id, client_id, auth[3], auth[4], auth[5]),
        )


def cleanup(conn):
    """Name-scoped, never an id range -- the lesson from the 201-entity near-miss."""
    with conn.cursor() as cur:
        cur.execute(
            f"SELECT id FROM {SCHEMA}.entities "  # noqa: S608
            "WHERE realm_id = %s AND name LIKE %s",
            (REALM, f"{PROBE_PREFIX}%"),
        )
        ids = [r[0] for r in cur.fetchall()]
        if not ids:
            return {"entities": 0, "auth": 0}
        cur.execute(
            f"DELETE FROM {SCHEMA}.principal_authentication_data "  # noqa: S608
            "WHERE realm_id = %s AND principal_id = ANY(%s)",
            (REALM, ids),
        )
        n_auth = cur.rowcount
        cur.execute(
            f"DELETE FROM {SCHEMA}.entities WHERE realm_id = %s AND id = ANY(%s)",  # noqa: S608
            (REALM, ids),
        )
        return {"entities": cur.rowcount, "auth": n_auth}


def try_token(client_id, secret):
    pc = PolarisREST(POLARIS_URL, REALM)
    r = pc.get_token(client_id, secret)
    ok = r.status_code < 300
    return ok, r.status_code, (r.json().get("access_token") if ok else None)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--source", default="user1", help="principal to clone")
    ap.add_argument("--keep", action="store_true")
    args = ap.parse_args()

    conn = connect()
    try:
        cleanup(conn)  # a previous aborted run must not confuse this one
        pc = root_client()

        # Mint a KNOWN secret for the source. The hash in the table is not
        # reversible, so the probe has to be the one that chose the plaintext.
        r = pc.reset_principal_credentials(args.source)
        if r.status_code >= 300:
            sys.exit(f"could not reset {args.source}: [{r.status_code}] {r.text[:200]}")
        creds = r.json().get("credentials", r.json())
        src_client, src_secret = creds["clientId"], creds["clientSecret"]
        print(f"source   : {args.source}  client_id={src_client}")

        ent, auth = read_source(conn, args.source)
        print(f"           principal_id={ent[0]}  salt={auth[5][:12]}...")

        base, _ = entity_replay.find_clone_band(conn, SCHEMA, REALM, 1)
        clone_name = f"{PROBE_PREFIX}_principal"
        clone_client = f"{PROBE_PREFIX}-client"
        insert_clone(conn, ent, auth, base, clone_name, clone_client)
        print(f"clone    : {clone_name}  client_id={clone_client}  id={base}")
        print("           same main_secret_hash, same salt, different client_id")

        print("\n" + "=" * 64)
        print("1. clone client_id + SOURCE secret   (the claim)")
        ok, code, token = try_token(clone_client, src_secret)
        print(f"   -> [{code}] {'TOKEN ISSUED' if ok else 'refused'}")

        print("\n2. clone client_id + WRONG secret    (the control)")
        bad_ok, bad_code, _ = try_token(clone_client, src_secret + "-wrong")
        print(f"   -> [{bad_code}] {'TOKEN ISSUED' if bad_ok else 'refused'}")

        authorized = None
        if ok:
            print("\n3. does that token AUTHORIZE anything?")
            probe = PolarisREST(POLARIS_URL, REALM, token=token)
            resp = probe.list_catalogs()
            authorized = resp.status_code
            print(f"   GET /catalogs -> [{resp.status_code}]")
            if resp.status_code >= 300:
                print(f"      {(resp.text or '')[:160]}")

        print("\n" + "=" * 64)
        print("VERDICT")
        print("=" * 64)
        if bad_ok:
            print("  INVALID TEST. The wrong secret was ALSO accepted, so this")
            print("  deployment is not checking secrets and the pass above says")
            print("  nothing about the hash scheme. Investigate that first --")
            print("  it is a much bigger finding than the one being probed.")
            return 2
        if ok:
            print("  CONFIRMED. The hash binds to the SECRET and SALT only --")
            print("  not to client_id, not to principal_id. A cloned credential")
            print("  row authenticates with the source's secret, and the wrong")
            print("  secret is still refused.")
            print()
            print("  Unlocks: entity_replay can clone principal_authentication_data")
            print("  alongside entities, giving thousands of authenticable")
            print("  identities by INSERT. 02c's grant-set-size axis becomes a")
            print("  curve rather than a two-point contrast.")
            if authorized is not None and authorized >= 300:
                print()
                print(
                    f"  BUT the token authorized nothing (GET /catalogs "
                    f"[{authorized}]). It mints and then resolves no grants,"
                )
                print("  which is worse than useless for a fixture: calls would")
                print("  be timed as latency while returning errors. Clone the")
                print("  grant rows too, then re-check.")
            return 0
        print("  REFUTED. The clone did not authenticate, so the hash binds to")
        print("  something beyond secret+salt -- client_id or principal_id.")
        print("  §2a of PLAN-api-latency-sweep.md is wrong and should be struck.")
        print()
        print("  Note Polaris may simply not have seen the new row yet:")
        print("  restart it and re-run before concluding. If it still refuses,")
        print("  the claim is dead and identities must be minted over REST, one")
        print("  call each.")
        return 1
    finally:
        if not args.keep:
            removed = cleanup(conn)
            print(
                f"\ncleaned up {removed['entities']} entity, "
                f"{removed['auth']} credential row(s)"
            )
        else:
            print(f"\n--keep: {PROBE_PREFIX}* rows left in place.")
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
