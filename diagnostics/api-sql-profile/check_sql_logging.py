#!/usr/bin/env python3
"""
check_sql_logging.py — diagnose "grep -c DatasourceOperations capture/polaris.log -> 0"

Walks the failure ladder in order and reports which rung actually broke, rather
than leaving you to guess between "logging is off", "the tail is dead",
"nothing has called Polaris yet" and "Polaris isn't using PostgreSQL at all".

It generates its own traffic and watches what appears, so a zero count becomes
informative instead of ambiguous. Handles both the plain-text and the JSON
console formats (`quarkus.log.console.json.enabled=true`).

Read-only apart from the probe calls, which are harmless GETs. Creates nothing
and changes no server config — same posture as `diagnostics/probe_auth_mode.py`.

Usage (from the repo root, inside .venv):
    python diagnostics/api-sql-profile/check_sql_logging.py
    python diagnostics/api-sql-profile/check_sql_logging.py --calls 5 --wait 3
"""

import argparse
import collections
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))

OK, BAD, INFO = "PASS", "FAIL", "  ->"
DSO = "DatasourceOperations"


def _read_tail(path, since=0):
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        fh.seek(since)
        return fh.read(), fh.tell()


def classify(lines):
    """Bucket log lines by format, level and logger. Format-agnostic."""
    out = {
        "json": 0,
        "text": 0,
        "debug": 0,
        "dso": 0,
        "query": 0,
        "loggers": collections.Counter(),
    }
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("{"):
            try:
                obj = json.loads(line)
            except ValueError:
                continue
            out["json"] += 1
            logger = obj.get("loggerName", "") or ""
            level = obj.get("level", "") or ""
            message = obj.get("message", "") or ""
        else:
            out["text"] += 1
            logger = line
            level = "DEBUG" if " DEBUG " in line else ""
            message = line
        if level == "DEBUG":
            out["debug"] += 1
            out["loggers"][logger] += 1
        if DSO in logger:
            out["dso"] += 1
        if message.startswith("query:") or " query: " in message:
            out["query"] += 1
    return out


# Tables that identify each persistence implementation. Checking the actual
# database is decisive in a way that reading env vars is not: it distinguishes
# relational-jdbc from eclipse-link from a store Polaris never wrote to.
JDBC_TABLES = {
    "entities",
    "grant_records",
    "principal_authentication_data",
    "policy_mapping_record",
    "version",
}
ECLIPSELINK_MARKERS = {
    "entities_change_tracking",
    "entities_active",
    "entities_dropped",
    "principal_secrets",
    "policy_mapping_records",
}


def probe_metastore(ptu):
    """Look in PostgreSQL and report which Polaris persistence layer wrote there.

    Returns a dict with `verdict` in:
        relational-jdbc  — schema-v2 tables present; SQL should be logged
        eclipse-link     — the older JPA metastore; it does NOT go through
                           DatasourceOperations, so no `query:` lines will ever
                           appear no matter how the category is configured
        empty            — connected, but nothing Polaris-shaped is there
        unknown          — could not connect / psycopg2 missing
    """
    try:
        import psycopg2
    except ImportError:
        return {"verdict": "unknown", "detail": "psycopg2 not installed"}

    kw = dict(
        host=getattr(ptu, "PG_HOST", None),
        port=getattr(ptu, "PG_PORT", 5432),
        dbname=getattr(ptu, "PG_DB", "polaris"),
        user=getattr(ptu, "PG_USER", "polaris"),
        password=getattr(ptu, "PG_PASSWORD", None),
        connect_timeout=5,
    )
    if not kw["host"]:
        return {"verdict": "unknown", "detail": "no PG_HOST in config"}
    try:
        conn = psycopg2.connect(**kw)
    except Exception as exc:  # noqa: BLE001
        return {"verdict": "unknown", "detail": f"{type(exc).__name__}: {exc}"}

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
                ORDER BY 1, 2
                """)
            rows = cur.fetchall()
            names = {t.lower() for _, t in rows}
            schemas = sorted({sc for sc, _ in rows})

            jdbc_hits = names & JDBC_TABLES
            el_hits = names & ECLIPSELINK_MARKERS

            counts = {}
            if len(jdbc_hits) >= 3:
                verdict = "relational-jdbc"
                for sc, t in rows:
                    if t.lower() in ("entities", "grant_records"):
                        try:
                            cur.execute(
                                f'SELECT count(*) FROM "{sc}"."{t}"'
                            )  # noqa: S608
                            counts[f"{sc}.{t}"] = cur.fetchone()[0]
                        except Exception:  # noqa: BLE001
                            conn.rollback()
            elif el_hits:
                verdict = "eclipse-link"
            else:
                verdict = "empty"
    finally:
        conn.close()

    return {
        "verdict": verdict,
        "schemas": schemas,
        "tables": sorted(names)[:25],
        "counts": counts if verdict == "relational-jdbc" else {},
        "detail": "",
    }


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--log", default="capture/polaris.log")
    ap.add_argument("--env", default="local")
    ap.add_argument("--calls", type=int, default=3)
    ap.add_argument("--wait", type=float, default=2.0)
    ap.add_argument(
        "--namespace",
        default="datahub-hynix",
        help="Kubernetes namespace (default: datahub-hynix)",
    )
    args = ap.parse_args()

    from polaris_test_utils import init_env, root_token  # noqa: E402

    init_env(args.env)
    import polaris_test_utils as ptu  # noqa: E402
    from polaris_rest import PolarisREST  # noqa: E402

    # Resource names come from config, not from a guess: common.yaml already
    # records polaris_container_name (benchmarks-polaris on this cluster), and
    # the deployment is named after it.
    container = getattr(ptu, "POLARIS_CONTAINER_NAME", None) or "benchmarks-polaris"
    ns = args.namespace
    deploy = f"deploy/{container}"

    log = pathlib.Path(args.log)
    print(f"Polaris : {ptu.POLARIS_URL}  realm={ptu.REALM}")
    print(f"K8s     : -n {ns} {deploy}")
    print(f"Log file: {log.resolve()}\n")

    # ---- rung 1: capture file present and non-empty ---------------------
    if not log.exists() or log.stat().st_size == 0:
        print(f"{BAD} capture file missing or empty.")
        print(f"{INFO} Start the tail:")
        print("       mkdir -p capture")
        print(f"       kubectl -n {ns} logs -f {deploy} > capture/polaris.log &")
        print(
            f"{INFO} Polaris also logs to a file inside the container "
            "(quarkus.log.file.path=./logs/polaris.log) if console output is off."
        )
        return 1
    print(f"{OK} capture file exists, {log.stat().st_size:,} bytes")

    text0, pos = _read_tail(log)
    before = classify(text0.splitlines())
    fmt = "JSON" if before["json"] > before["text"] else "text"
    print(
        f"{OK} format detected: {fmt} "
        f"({before['json']} json / {before['text']} text lines)"
    )

    # ---- rung 2: generate known traffic ---------------------------------
    print(f"\nMaking {args.calls} probe call(s)...")
    pc = PolarisREST(ptu.POLARIS_URL, ptu.REALM, token=root_token())
    try:
        statuses = [pc.list_catalogs().status_code for _ in range(args.calls)]
    except Exception as exc:  # noqa: BLE001
        print(f"{BAD} probe call failed: {type(exc).__name__}: {exc}")
        print(f"{INFO} Polaris is unreachable — fix connectivity first.")
        return 1
    print(f"{OK} probe calls returned {statuses}")
    bad = [c for c in statuses if c >= 300]
    if bad:
        print(
            f"{INFO} WARNING: {len(bad)} of {len(statuses)} probe calls were NOT 2xx.\n"
            "       Logging can still look healthy here — an authorization failure\n"
            "       runs the whole auth path and emits plenty of SQL — but the sweep\n"
            "       needs SUCCESSFUL calls. A 403 means the token is valid but the\n"
            "       principal lacks the privilege; check root's role assignment before\n"
            "       running the notebook."
        )

    time.sleep(args.wait)
    new_lines = _read_tail(log, pos)[0].splitlines()
    after = classify(new_lines)

    # ---- rung 3: did anything new arrive? -------------------------------
    print()
    if not new_lines:
        print(f"{BAD} no new log lines after {args.calls} successful API calls.")
        print(f"{INFO} Polaris served the requests, so the TAIL is not delivering —")
        print("       most likely it is following a pod that has since been replaced")
        print("       (`kubectl set env` triggers a rollout). Restart the tail.")
        return 1
    print(f"{OK} {len(new_lines)} new line(s) — the tail is live")
    print(f"{INFO} new DEBUG lines          : {after['debug']}")
    print(f"{INFO} new DatasourceOperations : {after['dso']}")
    print(f"{INFO} new 'query:' messages    : {after['query']}")

    # ---- success --------------------------------------------------------
    if after["dso"] and after["query"]:
        if bad:
            print(
                f"\n{OK} SQL DEBUG logging is WORKING — but see the non-2xx warning above."
            )
            print(
                "       Fix the authorization failure before running the notebook, or"
            )
            print(
                "       every operation in the sweep will map the 403 path instead of"
            )
            print("       the real one.")
            return 1
        print(f"\n{OK} SQL DEBUG logging is WORKING.")
        print("       The earlier grep returned 0 only because no traffic had reached")
        print("       Polaris since the tail started. Run the notebook.")
        return 0

    # ---- rung 4: DEBUG on, but no SQL -----------------------------------
    print(f"\n{BAD} no SQL statements are being logged.")

    if after["debug"]:
        print(f"\n{after['debug']} DEBUG line(s) from OTHER categories DID appear:")
        for logger, n in after["loggers"].most_common(6):
            print(f"       {n:>4}  {logger[:90]}")
        print("\nSo DEBUG logging works and the level is not the problem.")
        print("`DatasourceOperations.logQuery()` is called unconditionally from")
        print("executeSelectOverStream / executeUpdate / execute, gated only by the")
        print("SLF4J debug level — so if JDBC persistence were running, these lines")
        print("would be here.\n")
        # Ask the database directly — decisive, unlike reading env vars.
        print(">>> CHECK 1: what is actually in PostgreSQL?")
        meta = probe_metastore(ptu)
        v = meta["verdict"]
        if v == "unknown":
            print(f"    Could not check: {meta['detail']}")
        else:
            print(f"    schemas: {meta.get('schemas')}")
            print(f"    tables : {meta.get('tables')}")
            if meta.get("counts"):
                print(f"    rows   : {meta['counts']}")
        print()

        if v == "relational-jdbc":
            print(
                "    VERDICT: relational-jdbc IS in use — schema-v2 tables are present."
            )
            print("    So persistence is fine and the problem is the log CATEGORY.")
            print("    Widen it and re-run:")
            print(f"      kubectl -n {ns} set env {deploy} \\")
            print(
                "        QUARKUS_LOG_CATEGORY__ORG_APACHE_POLARIS_PERSISTENCE__LEVEL=DEBUG"
            )
            print("    If org.apache.polaris.persistence.* lines appear but never")
            print(
                "    DatasourceOperations, this build logs SQL from a different class."
            )
            return 1
        if v == "eclipse-link":
            print(
                "    VERDICT: the ECLIPSE-LINK metastore is in use, not relational-jdbc."
            )
            print("    That fully explains the symptom: EclipseLink is a JPA layer and")
            print(
                "    does NOT go through DatasourceOperations, so `query:` lines will"
            )
            print("    NEVER appear no matter how the category is set.")
            print("    Consequences for this profiling work:")
            print(
                "      - the schema is EclipseLink's, not POLARIS_SCHEMA schema-v2, so"
            )
            print("        schema_audit.EXPECTED_INDEXES does not apply as written;")
            print(
                "      - SQL must be captured from the PostgreSQL server log instead;"
            )
            print(
                "      - the grant_records index hypothesis needs re-deriving against"
            )
            print("        the actual EclipseLink DDL before it means anything.")
            print("    Tell me and I will retarget the audit.")
            return 1
        if v == "empty":
            print("    VERDICT: nothing Polaris-shaped exists in this database.")
            print("    Polaris is almost certainly on the IN-MEMORY store")
            print("    (`polaris.persistence.type` defaults to `in-memory` in 1.3.0).")
            print("    There is no SQL to log, and nothing survives a pod restart.")
        print()
        print(">>> CHECK 1b: confirm from the pod's own configuration")
        print(f"      kubectl -n {ns} exec {deploy} -- \\")
        print("        env | grep -i -E 'POLARIS_PERSISTENCE|QUARKUS_DATASOURCE'")
        print("    Expect POLARIS_PERSISTENCE_TYPE=relational-jdbc. If it is unset,")
        print("    the in-memory default is in force.\n")
        print(">>> CHECK 2: is the category name right for THIS build?")
        print("    Widen to the parent package and re-run this script:")
        print(f"      kubectl -n {ns} set env {deploy} \\")
        print(
            "        QUARKUS_LOG_CATEGORY__ORG_APACHE_POLARIS_PERSISTENCE__LEVEL=DEBUG"
        )
        print(
            "    If lines appear from org.apache.polaris.persistence.* but never from"
        )
        print("    ...relational.jdbc.DatasourceOperations, the persistence backend is")
        print("    not relational-jdbc after all.\n")
        print("    Fix — set on the deployment, then restart:")
        print("      POLARIS_PERSISTENCE_TYPE=relational-jdbc")
        print("      QUARKUS_DATASOURCE_DB_KIND=postgresql")
        print("      QUARKUS_DATASOURCE_JDBC_URL=jdbc:postgresql://<host>:5432/polaris")
        print("      QUARKUS_DATASOURCE_USERNAME=polaris")
        print(
            "      QUARKUS_DATASOURCE_PASSWORD=<secret>  # from a Secret, not a literal"
        )
        print("\n    Then BOOTSTRAP the realm before use — a fresh JDBC metastore has")
        print("    no schema and no root principal:")
        print("      polaris-admin-tool bootstrap --realm POLARIS \\")
        print("        --credential POLARIS,root,<secret>")
        print("    The <secret> must match root_secret in src/config/local.yaml.")
    else:
        print("\nNo DEBUG lines of ANY category appeared, so this is the log level.")
        print("  1. Confirm the env var is set on the RUNNING pod:")
        print(f"       kubectl -n {ns} exec {deploy} -- env | grep QUARKUS_LOG")
        print("     Expect the DOUBLE underscores (they encode the quotes in")
        print(
            '     quarkus.log.category."...".level) — a single one silently does nothing:'
        )
        print(
            "       QUARKUS_LOG_CATEGORY__ORG_APACHE_POLARIS_PERSISTENCE_"
            "RELATIONAL_JDBC__LEVEL=DEBUG"
        )
        print("  2. Confirm the pod restarted after the change:")
        print(f"       kubectl -n {ns} rollout status {deploy}")
        print("  3. Check for a mounted application.properties pinning the category.")
        print("  4. Or sidestep env-var mangling entirely:")
        print(
            "       JAVA_OPTS_APPEND='-Dquarkus.log.category.\"org.apache.polaris"
            ".persistence.relational.jdbc\".level=DEBUG'"
        )
    return 1


if __name__ == "__main__":
    sys.exit(main())
