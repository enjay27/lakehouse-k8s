#!/usr/bin/env python3
"""Test both Fluent Bit Lua filters against the copy that is deployed.

The Lua lives in logging/fb-values.yaml under luaScripts, because this cluster's
convention is that everything is in the values file and nothing is passed with
--set. That would leave the script untestable, so this reads it back out of the
values file: the tests cannot drift from what ships.

Needs a Lua interpreter. macOS has none by default, but a TeX install provides
one -- `luatex --luaonly` is a standalone Lua 5.3.

    python3 logging/scripts/test-polaris-filters.py
"""
import pathlib
import shutil
import subprocess
import sys
import tempfile

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]
VALUES = ROOT / "logging" / "fb-values.yaml"
SCRIPT_KEY = "polaris_access_log.lua"

ACCESS = "io.quarkus.http.access-log"

# ---------------------------------------------------------------- suite 1
# polaris_access_log: does the line split into the right fields?
PARSE_CASES = [
    ("the live 404 sample", {
        "loggerName": ACCESS,
        "_msg": '192.168.194.1 - user11_principal [03/Sep/2026:08:04:24 +0000] '
                '"GET /api/catalog/v1/watchdog-catalog/namespaces/watchdog-ns/tables/watchdog-table HTTP/1.1" 404 113'},
     2, {"client_ip": "192.168.194.1", "user_principal_name": "user11_principal",
         "http_method": "GET", "http_status": "404", "response_size": "113",
         "api_path": "/api/catalog/v1/watchdog-catalog/namespaces/watchdog-ns/tables/watchdog-table"}),

    ("zero-byte body, %b writes '-'", {
        "loggerName": ACCESS,
        "_msg": '192.168.194.1 - root [03/Sep/2026:06:35:13 +0000] "DELETE /api/x HTTP/1.1" 200 -'},
     2, {"http_status": "200", "response_size": "0"}),

    ("query string kept, anonymous user", {
        "loggerName": ACCESS,
        "_msg": '10.0.0.5 - - [03/Sep/2026:06:35:13 +0000] '
                '"GET /api/catalog/v1/c/namespaces/ns1/tables/t1?snapshots=all HTTP/1.1" 200 51234'},
     2, {"api_path": "/api/catalog/v1/c/namespaces/ns1/tables/t1?snapshots=all",
         "user_principal_name": "-", "response_size": "51234"}),

    ("IPv6 client on HTTP/2.0", {
        "loggerName": ACCESS,
        "_msg": 'fd00::1 - admin [03/Sep/2026:06:35:13 +0000] "PUT /x HTTP/2.0" 204 0'},
     2, {"client_ip": "fd00::1", "http_method": "PUT", "http_status": "204"}),

    ("unparseable line is tagged, not dropped", {
        "loggerName": ACCESS, "_msg": "the format changed"},
     2, {"access_log_parse_error": "true"}),

    ("a non-access-log record is untouched", {
        "loggerName": "org.apache.polaris.persistence.relational.jdbc.DatasourceOperations",
        "_msg": "query: INSERT INTO POLARIS_SCHEMA.ENTITIES ..."},
     0, {}),
]

# ---------------------------------------------------------------- suite 2
# polaris_noise_filter: what survives? Stateful -- these run in order, in one
# Lua process, and later cases depend on earlier ones.
#   KST day boundary is 15:00 UTC, so 2026-09-03T15:00Z is already 09-04 in KST.
TBL_A = "/api/catalog/v1/c/namespaces/ns1/tables/ta"
TBL_B = "/api/catalog/v1/c/namespaces/ns1/tables/tb"


def acc(t, method, path, status, level="INFO", user="root"):
    return {"loggerName": ACCESS, "level": level, "_time": t,
            "http_method": method, "api_path": path, "http_status": str(status),
            "user_principal_name": user}


KEEP, DROP = 0, -1
POLICY_CASES = [
    ("GET table A, first of the KST day",      acc("2026-09-03T08:00:00Z", "GET", TBL_A, 200), KEEP),
    ("GET table A again, same KST day",        acc("2026-09-03T09:00:00Z", "GET", TBL_A, 200), DROP),
    ("GET table B, different table",           acc("2026-09-03T09:01:00Z", "GET", TBL_B, 200), KEEP),
    ("GET table A but 404 -- errors outrank",  acc("2026-09-03T09:02:00Z", "GET", TBL_A, 404), KEEP),
    ("GET table A at 14:59Z, still same day",  acc("2026-09-03T14:59:59Z", "GET", TBL_A, 200), DROP),
    ("GET table A at 15:00Z, new KST day",     acc("2026-09-03T15:00:00Z", "GET", TBL_A, 200), KEEP),
    ("GET table A again in the new day",       acc("2026-09-03T16:00:00Z", "GET", TBL_A, 200), DROP),
    ("straggler for yesterday, already seen",  acc("2026-09-03T14:00:00Z", "GET", TBL_B, 200), DROP),
    ("HEAD is a different key from GET",       acc("2026-09-03T16:01:00Z", "HEAD", TBL_A, 200), KEEP),
    ("query string is not a new key",          acc("2026-09-03T16:02:00Z", "GET", TBL_A + "?snapshots=all", 200), DROP),

    ("POST table commit",                      acc("2026-09-03T16:03:00Z", "POST", TBL_A, 200), KEEP),
    ("POST view commit (added, not specified)", acc("2026-09-03T16:03:30Z", "POST", "/api/catalog/v1/c/namespaces/ns1/views/v2", 201), KEEP),
    ("POST oauth token, first for root today", acc("2026-09-03T16:04:00Z", "POST", "/api/catalog/v1/oauth/tokens", 200), KEEP),
    ("POST oauth token again, same principal", acc("2026-09-03T16:04:30Z", "POST", "/api/catalog/v1/oauth/tokens", 200), DROP),
    ("POST oauth token, other principal",      acc("2026-09-03T16:04:40Z", "POST", "/api/catalog/v1/oauth/tokens", 200, user="analyst"), KEEP),
    ("POST oauth token, 401 -- errors outrank", acc("2026-09-03T16:05:00Z", "POST", "/api/catalog/v1/oauth/tokens", 401), KEEP),

    ("PUT on a catalog role",                  acc("2026-09-03T16:06:00Z", "PUT", "/api/management/v1/catalogs/c/catalog-roles/r", 200), KEEP),
    ("DELETE a view",                          acc("2026-09-03T16:07:00Z", "DELETE", "/api/catalog/v1/c/namespaces/ns1/views/v1", 204), KEEP),
    ("GET /v1/config -- not a table, kept",    acc("2026-09-03T16:08:00Z", "GET", "/api/catalog/v1/config", 200), KEEP),
    ("GET table LIST -- no table name, kept",  acc("2026-09-03T16:09:00Z", "GET", "/api/catalog/v1/c/namespaces/ns1/tables", 200), KEEP),
    ("GET table list again -- still kept",     acc("2026-09-03T16:10:00Z", "GET", "/api/catalog/v1/c/namespaces/ns1/tables", 200), KEEP),
    ("500 on a table read",                    acc("2026-09-03T16:11:00Z", "GET", TBL_A, 500), KEEP),

    ("application DEBUG log", {"loggerName": "org.apache.polaris.service.catalog",
                               "level": "DEBUG", "_msg": "..."}, KEEP),
    ("application ERROR log", {"loggerName": "org.apache.polaris.service.catalog",
                               "level": "ERROR", "_msg": "boom"}, KEEP),
    ("application WARN log", {"loggerName": "org.apache.polaris.service.catalog",
                              "level": "WARN", "_msg": "hmm"}, KEEP),
    ("access-log line that did not parse", {"loggerName": ACCESS, "level": "INFO",
                                            "_time": "2026-09-03T16:12:00Z",
                                            "access_log_parse_error": "true"}, KEEP),

    # Rule 5 inverted. Every one of these left NO access-log record under the
    # keep-list, measured by the 2026-09-04 coverage run.
    ("POST create a principal",                acc("2026-09-03T16:13:00Z", "POST", "/api/management/v1/principals", 201), KEEP),
    ("POST create a principal role",           acc("2026-09-03T16:13:10Z", "POST", "/api/management/v1/principal-roles", 201), KEEP),
    ("POST create a catalog role",             acc("2026-09-03T16:13:20Z", "POST", "/api/management/v1/catalogs/c/catalog-roles", 201), KEEP),
    ("POST reset credentials -- the big one",  acc("2026-09-03T16:13:30Z", "POST", "/api/management/v1/principals/p/reset", 200), KEEP),
    ("POST rename a table",                    acc("2026-09-03T16:13:40Z", "POST", "/api/catalog/v1/c/tables/rename", 200), KEEP),
    ("POST rename a view",                     acc("2026-09-03T16:13:50Z", "POST", "/api/catalog/v1/c/views/rename", 204), KEEP),
    ("POST create a namespace",                acc("2026-09-03T16:14:00Z", "POST", "/api/catalog/v1/c/namespaces", 200), KEEP),
    ("POST namespace properties",              acc("2026-09-03T16:14:10Z", "POST", "/api/catalog/v1/c/namespaces/ns1/properties", 200), KEEP),

    # The dedup key now carries the principal. Fresh KST day (16:00Z on 09-04 is
    # already 09-05 in KST), so these do not depend on the buckets above.
    ("fresh day, root reads table A",          acc("2026-09-04T16:00:00Z", "GET", TBL_A, 200), KEEP),
    ("root reads it again",                    acc("2026-09-04T16:01:00Z", "GET", TBL_A, 200), DROP),
    ("a second principal reads the same table", acc("2026-09-04T16:02:00Z", "GET", TBL_A, 200, user="analyst"), KEEP),
    ("that principal reads it again",          acc("2026-09-04T16:03:00Z", "GET", TBL_A, 200, user="analyst"), DROP),
    ("and its query-string variant",           acc("2026-09-04T16:04:00Z", "GET", TBL_A + "?snapshots=refs", 200, user="analyst"), DROP),
    ("an anonymous read is its own bucket",    acc("2026-09-04T16:05:00Z", "GET", TBL_A, 200, user="-"), KEEP),
]


def lua_binary():
    for exe, pre in (("lua", []), ("lua5.4", []), ("lua5.3", []),
                     ("luajit", []), ("luatex", ["--luaonly"])):
        if shutil.which(exe):
            return [exe] + pre
    sys.exit("no Lua interpreter found (tried lua, lua5.4, lua5.3, luajit, luatex)")


def lit(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def tbl(record):
    return "{" + ", ".join("[%s]=%s" % (lit(k), lit(v)) for k, v in record.items()) + "}"


def main():
    script = yaml.safe_load(VALUES.read_text(encoding="utf-8"))["luaScripts"][SCRIPT_KEY]

    lines = [script, "local function q(v) if v==nil then return '<nil>' end return tostring(v) end"]
    for i, (_n, rec, _c, expect) in enumerate(PARSE_CASES):
        lines.append("local c%d,_,r%d = polaris_access_log('t', 0, %s)" % (i, i, tbl(rec)))
        want = ["'%s='..q(r%d[%s])" % (k, i, lit(k)) for k in sorted(expect)] or ["''"]
        lines.append("print('P', %d, c%d, %s)" % (i, i, ", ".join(want)))
    for i, (_n, rec, _c) in enumerate(POLICY_CASES):
        lines.append("local n%d = polaris_noise_filter('t', 0, %s)" % (i, tbl(rec)))
        lines.append("print('N', %d, n%d)" % (i, i))

    with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False) as fh:
        fh.write("\n".join(lines) + "\n")
        path = fh.name

    out = subprocess.run(lua_binary() + [path], capture_output=True, text=True)
    if out.returncode != 0:
        sys.exit("lua failed:\n" + out.stdout + out.stderr)

    got = {}
    for line in out.stdout.splitlines():
        f = line.replace("\t", " ").split(" ")
        if f and f[0] in ("P", "N"):
            got[(f[0], int(f[1]))] = (int(f[2]), " ".join(f[3:]))

    failures = 0
    print("polaris_access_log -- field extraction")
    for i, (name, _rec, want_code, expect) in enumerate(PARSE_CASES):
        code, rest = got[("P", i)]
        ok = code == want_code and all("%s=%s" % (k, v) in rest for k, v in expect.items())
        print(("  ok   " if ok else "  FAIL ") + name)
        if not ok:
            print("         want code=%d %s\n         got  code=%d %s" % (want_code, expect, code, rest))
            failures += 1

    print("\npolaris_noise_filter -- what survives (stateful, in order)")
    for i, (name, _rec, want) in enumerate(POLICY_CASES):
        code, _ = got[("N", i)]
        ok = code == want
        verdict = "drop" if code == -1 else "keep"
        print(("  ok   " if ok else "  FAIL ") + "%-42s %s" % (name, verdict))
        if not ok:
            print("         wanted %s" % ("drop" if want == -1 else "keep"))
            failures += 1

    total = len(PARSE_CASES) + len(POLICY_CASES)
    print("\n%d/%d passed" % (total - failures, total))
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
