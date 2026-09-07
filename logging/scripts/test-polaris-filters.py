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
import re
import shutil
import subprocess
import sys
import tempfile

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]
VALUES = ROOT / "logging" / "fb-values.yaml"
SCRIPT_KEY = "polaris_access_log.lua"

SCRIPT = yaml.safe_load(VALUES.read_text(encoding="utf-8"))["luaScripts"][SCRIPT_KEY]

# The report period is read OFF THE DEPLOYED LUA, never hardcoded. Suite 3 used to
# assume 1800 and every boundary offset was written out as a literal; the day the
# window changed, "a tick inside the window" became a tick three windows later and the
# suite reported a policy finding that was really a stale constant. Offsets below are
# multiples of WINDOW, so the suite follows the values file wherever it goes.
_m = re.search(r"^\s*local WINDOW_SECONDS\s*=\s*(\d+)", SCRIPT, re.M)
if not _m:
    sys.exit("could not read WINDOW_SECONDS out of " + str(VALUES))
WINDOW = int(_m.group(1))

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
# polaris_noise_filter: what survives? v3 has no per-key state, so keep/drop no
# longer depends on order -- but the counters do, and suite 3 reads them, so these
# still run in one process in order.
CAT  = "/api/catalog/v1/c"
TBL  = CAT + "/namespaces/ns1/tables/ta"
MG   = "/api/management/v1"
# invented table names: an error against one of these must never create a resource key
NOPE1 = CAT + "/namespaces/ns1/tables/nope1"
NOPE2 = CAT + "/namespaces/ns1/tables/nope2"


def acc(t, method, path, status, level="INFO", user="root", size=0):
    return {"loggerName": ACCESS, "level": level, "_time": t,
            "http_method": method, "api_path": path, "http_status": str(status),
            "user_principal_name": user, "response_size": str(size)}


KEEP, DROP = 0, -1
T = "2026-09-03T08:00:00Z"

POLICY_CASES = [
    # rule 3 -- every failure is kept. All of them, no cap: this is the decision,
    # and the repetition below is the point rather than padding.
    ("404 on a table read",                    acc(T, "GET", TBL, 404), KEEP),
    ("the same 404 again",                     acc(T, "GET", TBL, 404), KEEP),
    ("and again",                              acc(T, "GET", TBL, 404), KEEP),
    ("403 denied read",                        acc(T, "GET", TBL, 403), KEEP),
    ("401 on the token endpoint",              acc(T, "POST", CAT + "/oauth/tokens", 401), KEEP),
    ("500 on a table read",                    acc(T, "GET", TBL, 500), KEEP),
    ("a line that did not parse",              {"loggerName": ACCESS, "level": "INFO",
                                                "_time": T, "access_log_parse_error": "true"}, KEEP),

    # rule 4 -- every non-POST mutation
    ("PUT a grant",                            acc(T, "PUT", MG + "/catalogs/c/catalog-roles/r/grants", 201), KEEP),
    ("DELETE a table",                         acc(T, "DELETE", TBL, 204), KEEP),
    ("DELETE a principal",                     acc(T, "DELETE", MG + "/principals/p", 204), KEEP),

    # rule 5 -- management POST is the create verb and is kept in full
    ("POST create a principal",                acc(T, "POST", MG + "/principals", 201), KEEP),
    ("POST create a principal role",           acc(T, "POST", MG + "/principal-roles", 201), KEEP),
    ("POST create a catalog role",             acc(T, "POST", MG + "/catalogs/c/catalog-roles", 201), KEEP),
    ("POST reset credentials -- the one that matters", acc(T, "POST", MG + "/principals/p/reset", 200), KEEP),

    # rule 5 -- catalog POST is data-plane volume and is counted
    ("POST create a table",                    acc(T, "POST", CAT + "/namespaces/ns1/tables", 200), DROP),
    ("POST commit a table",                    acc(T, "POST", TBL, 200), DROP),
    ("POST rename a table",                    acc(T, "POST", CAT + "/tables/rename", 200), DROP),
    ("POST report metrics",                    acc(T, "POST", TBL + "/metrics", 204), DROP),
    ("POST an oauth token, 200",               acc(T, "POST", CAT + "/oauth/tokens", 200), DROP),
    ("POST create a namespace",                acc(T, "POST", CAT + "/namespaces", 200), DROP),

    # rule 6 -- successful reads are counts, never records
    ("GET a table",                            acc(T, "GET", TBL, 200), DROP),
    ("GET the same table again",               acc(T, "GET", TBL, 200), DROP),
    ("HEAD a table",                           acc(T, "HEAD", TBL, 204), DROP),
    ("GET a table listing",                    acc(T, "GET", CAT + "/namespaces/ns1/tables", 200), DROP),
    ("GET /v1/config",                         acc(T, "GET", CAT + "/config", 200), DROP),
    ("GET management list_principals",         acc(T, "GET", MG + "/principals", 200), DROP),

    # rules 1 and 2 -- untouched
    ("application DEBUG log", {"loggerName": "org.apache.polaris.service.catalog",
                               "level": "DEBUG", "_msg": "..."}, KEEP),
    ("application ERROR log", {"loggerName": "org.apache.polaris.service.catalog",
                               "level": "ERROR", "_msg": "boom"}, KEEP),
    ("application WARN log", {"loggerName": "org.apache.polaris.service.catalog",
                              "level": "WARN", "_msg": "hmm"}, KEEP),
]

# ---------------------------------------------------------------- suite 3
# The flush report and its schema. Counters only exist from the first tick, so the
# traffic below -- not suite 2's -- is what the asserted window contains.
# T0 is snapped down to a WINDOW boundary, so no test sleeps and the arithmetic is
# exact at any window length. Ticks are placed at T0, mid-window, and on the next
# three boundaries -- what makes a tick a boundary is WINDOW, not a literal.
# `_now_override` is the filter's test hook; the dummy INPUT never sets it.
T0 = (1787999400 // WINDOW) * WINDOW
MID = WINDOW // 2         # a tick inside the open window: must report nothing
EMIT = 2          # the tick returns 2: record replaced, by the array of reports
W = "2026-09-05T16:0"


def tick(t):
    return {"_now_override": t}


REPORT_CASES = [
    ("first tick only opens the window", "tick", tick(T0), DROP, {"nrec": "0"}),

    ("root reads the table",        "rec", acc(W + "0:00Z", "GET", TBL, 200, size=100), DROP, {}),
    ("alice reads the same table",  "rec", acc(W + "1:00Z", "GET", TBL, 200, user="alice", size=50), DROP, {}),
    # /metrics must count against the TABLE, not beside it -- v2 emitted two rows
    ("root posts scan metrics",     "rec", acc(W + "2:00Z", "POST", TBL + "/metrics", 204), DROP, {}),
    ("a query string is not a new resource", "rec", acc(W + "3:00Z", "GET", TBL + "?snapshots=all", 200, size=25), DROP, {}),
    # an error on a resource never seen successfully must not create a key
    ("root 404s an invented table", "rec", acc(W + "4:00Z", "GET", CAT + "/namespaces/ns1/tables/nope", 404), KEEP, {}),
    ("root creates a principal",    "rec", acc(W + "5:00Z", "POST", MG + "/principals", 201), KEEP, {}),
    ("root deletes the table",      "rec", acc(W + "6:00Z", "DELETE", TBL, 204), KEEP, {}),
    ("an application log is not counted", "rec", {"loggerName": "x", "level": "DEBUG", "_msg": "."}, KEEP, {}),

    ("a tick inside the window reports nothing", "tick", tick(T0 + MID), DROP, {"nrec": "0"}),

    # 1 summary + 3 resources (the table, __other__, the principals collection)
    #           + 2 principals (root, alice)
    ("the boundary tick emits the window", "tick", tick(T0 + WINDOW), EMIT, {
        "nrec": "6",
        "access_seen": "7", "access_kept": "3", "access_counted": "4",
        "counted_read": "3", "counted_post": "1", "errors_kept": "1",
        "distinct_resources": "3", "distinct_principals": "2",
        "carried_rows": "0", "windows_skipped": "0",
        # the 404 on the invented table, split by kind (v1 had one `errors` integer)
        "errors_4xx": "1", "errors_5xx": "0", "auth_denied": "0",
        "bytes_total": "175",
        "resources_other": "1", "resources_other_distinct": "1",
        "principals_other": "0",
        "tbl_requests": "5", "tbl_reads": "3", "tbl_writes": "2", "tbl_bytes": "175",
        "other_errors": "1",
        "root_requests": "6", "root_reads": "3", "root_writes": "3",
        "alice_reads": "1",
        "min_time": "2026-09-05T16:00:00Z", "max_time": "2026-09-05T16:06:00Z",
        "schema": "2",
        # the schema's own self-check: both margins must sum to the same total,
        # and that total must be access_seen - parse_errors
        "res_total": "7", "pri_total": "7",
    }),

    # zero-carry: every key that was non-zero is emitted once more as an explicit 0,
    # so a fall to nothing is a data point instead of a missing row.
    # v2: the rows are still emitted, but distinct_resources no longer counts them --
    # it reads 0 here, where v1 reported 3 resources in a window with no traffic at all.
    # carried_rows is where that number went: 3 resources + 2 principals.
    ("a quiet window carries the keys as zeros", "tick", tick(T0 + 2 * WINDOW), EMIT, {
        "nrec": "6", "access_seen": "0", "distinct_resources": "0",
        "distinct_principals": "0", "carried_rows": "5", "windows_skipped": "0",
        "tbl_requests": "0", "tbl_reads": "0", "root_requests": "0",
    }),

    # ...and the carry decays: a key that stayed zero is not carried again
    ("the carry decays after one window", "tick", tick(T0 + 3 * WINDOW), EMIT, {
        "nrec": "1", "access_seen": "0", "distinct_resources": "0",
        "distinct_principals": "0", "carried_rows": "0", "tbl_requests": "<none>",
    }),

    # ── v2 fields ──────────────────────────────────────────────────────────────
    # A fresh window (opened by the tick above, no carry) exercising every field the
    # schema bump added. Order matters: the 500 lands on the table only because the
    # table was already created by a successful read -- an error never creates a key.
    ("HEAD counts as a read, not a GET", "rec", acc(W + "7:00Z", "HEAD", TBL, 200, size=10), DROP, {}),
    ("a successful GET creates the key",  "rec", acc(W + "7:01Z", "GET", TBL, 200, size=20), DROP, {}),
    ("a 500 on the known table",          "rec", acc(W + "7:02Z", "GET", TBL, 500, size=5), KEEP, {}),
    ("a 404 folds into __other__",        "rec", acc(W + "7:03Z", "GET", NOPE1, 404, size=1), KEEP, {}),
    ("a second invented name folds too",  "rec", acc(W + "7:04Z", "GET", NOPE2, 404, size=1), KEEP, {}),
    # the same folded key again: resources_other counts REQUESTS folded and goes to 3,
    # resources_other_distinct counts KEYS and stays at 2. One broken client is not a
    # scanner walking twenty names, and v1 could not tell them apart.
    ("the same invented name again",      "rec", acc(W + "7:05Z", "GET", NOPE1, 404, size=1), KEEP, {}),
    ("a 401 is denied, not just 4xx",     "rec", acc(W + "7:06Z", "GET", TBL, 401, user="denied", size=1), KEEP, {}),
    ("a 403 is denied too",               "rec", acc(W + "7:07Z", "GET", TBL, 403, user="denied", size=1), KEEP, {}),

    ("the v2 window emits its split counters", "tick", tick(T0 + 4 * WINDOW), EMIT, {
        "nrec": "5",                       # summary + tbl + __other__ + root + denied
        "access_seen": "8", "access_kept": "6", "access_counted": "2",
        "counted_read": "2", "counted_post": "0", "errors_kept": "6",
        "errors_4xx": "5", "errors_5xx": "1", "auth_denied": "2",
        "bytes_total": "40",
        "distinct_resources": "2", "distinct_principals": "2", "carried_rows": "0",
        "resources_other": "3", "resources_other_distinct": "2",
        "windows_skipped": "0",
        "tbl_requests": "5", "tbl_reads": "5", "tbl_5xx": "1", "tbl_4xx": "2",
        "tbl_denied": "2", "tbl_bytes": "37",
        "other_4xx": "3", "other_5xx": "0",
        "denied_requests": "2", "denied_denied": "2",
        "res_total": "8", "pri_total": "8",
    }),

    # a tick that jumps two window indices: the skipped windows were never built, so
    # report_seq still increments by exactly 1 and v1 said nothing at all about the gap
    ("a jumped tick states the windows it skipped", "tick", tick(T0 + 7 * WINDOW), EMIT, {
        "nrec": "5", "access_seen": "0", "windows_skipped": "2",
        "distinct_resources": "0", "carried_rows": "4",
    }),
]

SUMMARY_FIELDS = ["access_seen", "access_kept", "access_counted", "counted_read",
                  "counted_post", "errors_kept", "parse_errors",
                  "errors_4xx", "errors_5xx", "auth_denied", "bytes_total",
                  "distinct_resources", "distinct_principals", "carried_rows",
                  "resources_other", "resources_other_distinct",
                  "principals_other", "windows_skipped"]

# (probe name, report_type, key field, key value, field to read)
ROW_PROBES = [
    ("tbl_requests",  "resource",  "resource", TBL, "requests"),
    ("tbl_reads",     "resource",  "resource", TBL, "reads"),
    ("tbl_writes",    "resource",  "resource", TBL, "writes"),
    ("tbl_bytes",     "resource",  "resource", TBL, "response_bytes"),
    ("tbl_kind",      "resource",  "resource", TBL, "resource_kind"),
    ("other_errors",  "resource",  "resource", "__other__", "errors"),
    ("tbl_4xx",       "resource",  "resource", TBL, "errors_4xx"),
    ("tbl_5xx",       "resource",  "resource", TBL, "errors_5xx"),
    ("tbl_denied",    "resource",  "resource", TBL, "auth_denied"),
    ("other_4xx",     "resource",  "resource", "__other__", "errors_4xx"),
    ("other_5xx",     "resource",  "resource", "__other__", "errors_5xx"),
    ("root_requests", "principal", "user_principal_name", "root", "requests"),
    ("root_reads",    "principal", "user_principal_name", "root", "reads"),
    ("root_writes",   "principal", "user_principal_name", "root", "writes"),
    ("alice_reads",   "principal", "user_principal_name", "alice", "reads"),
    ("denied_requests", "principal", "user_principal_name", "denied", "requests"),
    ("denied_denied",   "principal", "user_principal_name", "denied", "auth_denied"),
]

SUMMARY_STR = [("min_time", "min_record_time"), ("max_time", "max_record_time"),
               ("schema", "schema_version")]


# ---------------------------------------------------------------- suite 4
# A numeric field missing from filter 3's type_int_key is encoded as a double,
# VictoriaLogs stores "482.0", and `requests:>0` silently matches nothing -- the
# failure is invisible until someone writes a query. Reading it out of the same
# values file the Lua came from is the only way this stays true after an edit.
TYPE_INT_CHECKS = 2
_STR_SUMMARY = {"min_record_time", "max_record_time", "partial_window", "_msg"}
_STR_ROW = {"resource", "resource_kind", "user_principal_name", "_msg"}
# set by base(), not by an assignment the regexes below can see
_ENVELOPE_INTS = {"schema_version", "report_seq", "window_seconds"}


def check_type_int_key():
    filters = yaml.safe_load(VALUES.read_text(encoding="utf-8"))["config"]["filters"]
    # the comment above the directive contains the words too; the directive is longest
    lines = re.findall(r"^\s*type_int_key\s+(.+)$", filters, re.M)
    if not lines:
        print("  FAIL no type_int_key directive in config.filters")
        return TYPE_INT_CHECKS
    declared = set(max(lines, key=len).split())

    emitted = set(re.findall(r"^\s*s\.(\w+)\s*=", SCRIPT, re.M)) - _STR_SUMMARY
    emitted |= set(re.findall(r"e\.(\w+)", SCRIPT)) - _STR_ROW

    failures = 0
    missing = sorted(emitted - declared)
    if missing:
        print("  FAIL numeric fields NOT in type_int_key: " + ", ".join(missing))
        failures += 1
    else:
        print("  ok   every emitted numeric field is declared")

    stale = sorted(declared - emitted - _ENVELOPE_INTS)
    if stale:
        print("  FAIL type_int_key names fields the report no longer emits: "
              + ", ".join(stale))
        failures += 1
    else:
        print("  ok   type_int_key names nothing the report stopped emitting")
    return failures


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
    lines = [
        SCRIPT,
        "local function q(v) if v==nil then return '<nil>' end return tostring(v) end",
        "local function nrec(r) if type(r)~='table' or r[1]==nil then return 0 end return #r end",
        "local function sf(r,k) if type(r)~='table' or r[1]==nil then return '<nil>' end return q(r[1][k]) end",
        "local function rq(r,t,kf,kv,f) if type(r)~='table' or r[1]==nil then return '<nil>' end "
        "for _,e in ipairs(r) do if e.report_type==t and e[kf]==kv then return q(e[f]) end end return '<none>' end",
        "local function rsum(r,t,f) if type(r)~='table' or r[1]==nil then return '<nil>' end local n=0 "
        "for _,e in ipairs(r) do if e.report_type==t then n=n+e[f] end end return q(n) end",
    ]
    for i, (_n, rec, _c, expect) in enumerate(PARSE_CASES):
        lines.append("local c%d,_,r%d = polaris_access_log('t', 0, %s)" % (i, i, tbl(rec)))
        want = ["'%s='..q(r%d[%s])" % (k, i, lit(k)) for k in sorted(expect)] or ["''"]
        lines.append("print('P', %d, c%d, %s)" % (i, i, ", ".join(want)))
    for i, (_n, rec, _c) in enumerate(POLICY_CASES):
        lines.append("local n%d = polaris_noise_filter('t', 0, %s)" % (i, tbl(rec)))
        lines.append("print('N', %d, n%d)" % (i, i))
    for i, (_n, kind, payload, _c, _e) in enumerate(REPORT_CASES):
        tag = "polaris.report" if kind == "tick" else "t"
        lines.append("local s%d,_,q%d = polaris_noise_filter('%s', 0, %s)"
                     % (i, i, tag, tbl(payload)))
        want = ["'nrec='..nrec(q%d)" % i] + \
               ["'%s='..sf(q%d, %s)" % (k, i, lit(k)) for k in SUMMARY_FIELDS] + \
               ["'%s='..sf(q%d, %s)" % (n, i, lit(f)) for n, f in SUMMARY_STR] + \
               ["'res_total='..rsum(q%d,'resource','requests')" % i,
                "'pri_total='..rsum(q%d,'principal','requests')" % i] + \
               ["'%s='..rq(q%d, %s, %s, %s, %s)"
                % (n, i, lit(t), lit(kf), lit(kv), lit(f))
                for n, t, kf, kv, f in ROW_PROBES]
        lines.append("print('S', %d, s%d, %s)" % (i, i, ", ".join(want)))

    with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False) as fh:
        fh.write("\n".join(lines) + "\n")
        path = fh.name

    out = subprocess.run(lua_binary() + [path], capture_output=True, text=True)
    if out.returncode != 0:
        sys.exit("lua failed:\n" + out.stdout + out.stderr)

    got = {}
    for line in out.stdout.splitlines():
        f = line.replace("\t", " ").split(" ")
        if f and f[0] in ("P", "N", "S"):
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

    print("\npolaris_noise_filter -- the flush report (stateful, continues above)")
    for i, (name, kind, _payload, want_code, checks) in enumerate(REPORT_CASES):
        code, rest = got[("S", i)]
        ok = code == want_code and all("%s=%s" % (k, v) in rest for k, v in checks.items())
        verdict = "drop" if code == -1 else ("emit" if kind == "tick" else "keep")
        print(("  ok   " if ok else "  FAIL ") + "%-42s %s" % (name, verdict))
        if not ok:
            print("         want code=%d %s\n         got  code=%d %s"
                  % (want_code, checks, code, rest))
            failures += 1

    print("\ntype_int_key -- every numeric field the report emits")
    int_failures = check_type_int_key()
    failures += int_failures

    total = (len(PARSE_CASES) + len(POLICY_CASES) + len(REPORT_CASES)
             + TYPE_INT_CHECKS)
    print("\n%d/%d passed" % (total - failures, total))
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
