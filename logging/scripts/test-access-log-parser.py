#!/usr/bin/env python3
"""Run the access-log parser's test cases against the copy that is deployed.

The Lua lives in logging/fb-values.yaml under luaScripts, because this cluster's
convention is that everything is in the values file and nothing is passed with
--set. That leaves the script untestable unless the tests read it from there —
which is what this does, so the tests can never drift from what ships.

Needs a Lua interpreter. There is no `lua` on macOS by default, but a TeX
install provides one: `luatex --luaonly` is a standalone Lua 5.3.

    python3 logging/scripts/test-access-log-parser.py
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

# (record fields, expected return code, expected extracted fields)
CASES = [
    ("the sample 404",
     {"loggerName": "io.quarkus.http.access-log",
      "_msg": '192.168.194.1 - root [03/Sep/2026:06:37:47 +0000] '
              '"DELETE /api/management/v1/principals/apiprofile1788334618_p HTTP/1.1" 404 133'},
     2, {"client_ip": "192.168.194.1", "user_principal_name": "root",
         "http_method": "DELETE",
         "api_path": "/api/management/v1/principals/apiprofile1788334618_p",
         "http_status": "404", "response_size": "133"}),

    ("zero-byte body, %b writes '-'",
     {"loggerName": "io.quarkus.http.access-log",
      "_msg": '192.168.194.1 - root [03/Sep/2026:06:35:13 +0000] '
              '"DELETE /api/catalog/v1/admin5_catalog/namespaces/ns1/views/vw2 HTTP/1.1" 200 -'},
     2, {"http_status": "200", "response_size": "0"}),

    ("query string kept, anonymous user",
     {"loggerName": "io.quarkus.http.access-log",
      "_msg": '10.0.0.5 - - [03/Sep/2026:06:35:13 +0000] '
              '"GET /api/catalog/v1/c/namespaces/ns1/tables/t1?snapshots=all HTTP/1.1" 200 51234'},
     2, {"api_path": "/api/catalog/v1/c/namespaces/ns1/tables/t1?snapshots=all",
         "user_principal_name": "-", "response_size": "51234"}),

    ("IPv6 client on HTTP/2.0",
     {"loggerName": "io.quarkus.http.access-log",
      "_msg": 'fd00::1 - admin [03/Sep/2026:06:35:13 +0000] "PUT /x HTTP/2.0" 204 0'},
     2, {"client_ip": "fd00::1", "http_method": "PUT", "http_status": "204"}),

    ("unparseable line from that logger is tagged, not dropped",
     {"loggerName": "io.quarkus.http.access-log", "_msg": 'the format changed'},
     2, {"access_log_parse_error": "true"}),

    ("a non-access-log record is returned untouched",
     {"loggerName": "org.apache.polaris.persistence.relational.jdbc.DatasourceOperations",
      "_msg": 'query: INSERT INTO POLARIS_SCHEMA.ENTITIES ...'},
     0, {}),
]


def lua_binary():
    for exe, pre in (("lua", []), ("lua5.4", []), ("lua5.3", []),
                     ("luajit", []), ("luatex", ["--luaonly"])):
        if shutil.which(exe):
            return [exe] + pre
    sys.exit("no Lua interpreter found (tried lua, lua5.4, lua5.3, luajit, luatex)")


def lua_literal(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def main():
    values = yaml.safe_load(VALUES.read_text(encoding="utf-8"))
    script = values["luaScripts"][SCRIPT_KEY]

    harness = [script, "local function q(v) if v == nil then return '<nil>' end return tostring(v) end"]
    for i, (_name, record, _code, expect) in enumerate(CASES):
        fields = ", ".join("[%s]=%s" % (lua_literal(k), lua_literal(v))
                           for k, v in record.items())
        harness.append("local c%d, _, r%d = polaris_access_log('polaris.vlogs', 0, {%s})"
                       % (i, i, fields))
        harness.append("print(%d, c%d, %s)" % (i, i, ", ".join(
            ["'%s='..q(r%d[%s])" % (k, i, lua_literal(k)) for k in sorted(expect)] or ["''"])))

    with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False) as fh:
        fh.write("\n".join(harness) + "\n")
        path = fh.name

    out = subprocess.run(lua_binary() + [path], capture_output=True, text=True)
    if out.returncode != 0:
        sys.exit("lua failed:\n" + out.stdout + out.stderr)

    lines = [l for l in out.stdout.splitlines() if l and l[0].isdigit()]
    failures = 0
    for (name, _rec, want_code, expect), line in zip(CASES, lines):
        parts = line.replace("\t", " ").split(" ")
        got_code = int(parts[1])
        rest = " ".join(parts[2:])
        ok = got_code == want_code
        for k, v in expect.items():
            if ("%s=%s" % (k, v)) not in rest:
                ok = False
        print(("  ok   " if ok else "  FAIL ") + name)
        if not ok:
            print("         want code=%d %s" % (want_code, expect))
            print("         got  code=%d %s" % (got_code, rest))
            failures += 1

    print("\n%d/%d passed" % (len(CASES) - failures, len(CASES)))
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
