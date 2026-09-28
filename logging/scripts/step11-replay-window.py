#!/usr/bin/env python3
"""
Replay ONE report window's unfiltered tier-1 copy through the deployed Lua and diff every
report row against what the pipeline actually wrote. The strongest v4 check there is:
it compares the filter's output with the filter applied to the raw input, field by field.

    bash logging/scripts/step10-v4-window-readout.sh 2026-09-15T09:20:00Z   # writes .scratch/readout-*/
    python3 logging/scripts/step11-replay-window.py .scratch/readout-2026-09-15T092000Z

Needs `luajit` (Fluent Bit's runtime) or `lua5.1` on PATH. Run from the repo root.
The Lua is releases/fluent-bit/polaris_access_log.lua as it is in the repo -- if it differs from
the deployed ConfigMap (step3's sha check), a diff here means "repo != deployed", not a fault.

First measured 2026-09-15 window 09:20:00Z (run 1789463971): 64 rows, 28 fields, 0 mismatches.
Since v5 it also predicts the DETAIL index: every record the filter emits (arrays included) is
tallied by logger and compared with detail.json. Replaying a window the pipeline processed with an
OLDER script than the repo's shows the policy change as mismatches -- expected when previewing a
change, not a fault.
"""
import json, os, re, shutil, subprocess, sys, tempfile

d = sys.argv[1] if len(sys.argv) > 1 else sys.exit(__doc__)
lua_bin = shutil.which("luajit") or shutil.which("lua5.1") or sys.exit("need luajit or lua5.1 on PATH")
# POLARIS_LUA=<file> replays a candidate script instead of the deployed one.
script = os.path.abspath(os.environ.get("POLARIS_LUA", "releases/fluent-bit/polaris_access_log.lua"))
rep = json.load(open(f"{d}/report.json"))
t1 = json.load(open(f"{d}/tier1.json"))
summary = [r for r in rep if r.get("report_type") == "summary"]
if len(summary) != 1:
    sys.exit(f"expected one summary row in {d}/report.json, found {len(summary)}")
ws = int(summary[0].get("window_seconds", 30))

def q(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "") + '"'

# Tier-1 records carry the raw Polaris JSON; tier 2 keeps `message` under its own name since schema v6 (no rename).
# The window is opened by one tick and closed by the next; record times are irrelevant to
# attribution (the Lua counts into whichever window is open), so any T0 on the grid works.
lines = [
    f'local src = io.open({q(script)}):read("*a")',
    f'src = src:gsub("local WINDOW_SECONDS = %d+", "local WINDOW_SECONDS = {ws}", 1)',
    'assert(loadstring(src))()',
    f'local T0 = {ws * 60000000}',
    'polaris_noise_filter("polaris.report", 0, {_now_override = T0 + 1})',
    # v5 (2026-09-16): the filter can return an ARRAY of records (held app lines released
    # with their access line), so every emitted record is tallied by logger -- the prediction
    # of what polaris-logs-* holds, compared below against detail.json.
    'local KEPT = {}',
    'local function tally(x) KEPT[x.loggerName or "-"] = (KEPT[x.loggerName or "-"] or 0) + 1 end',
    # Split script (FILTER 2 polaris_access_log + FILTER 3) or merged (refactor R1, 2026-09-16): call the
    # parser only if the script still defines it.
    'local function F(r) local r2 = r; if polaris_access_log then local _, _, x = polaris_access_log("polaris.logs", 0, r); r2 = x or r end; '
    'local c, _, o = polaris_noise_filter("polaris.logs", 0, r2); '
    'if c ~= -1 then if type(o) == "table" and type(o[1]) == "table" then '
    'for _, x in ipairs(o) do tally(x) end else tally(o) end end end',
]
for r in t1:
    rid = (r.get("mdc") or {}).get("requestId")
    lines.append("F({loggerName=%s,level=%s,message=%s,_time=%s%s})" % (
        q(r.get("loggerName", "")), q(r.get("level", "")), q(r.get("message", "")), q(r.get("@timestamp", "")),
        f",mdc={{requestId={q(rid)}}}" if rid else ""))
lines.append(f'local _, _, o = polaris_noise_filter("polaris.report", 0, {{_now_override = T0 + {ws} + 1}})')
lines.append('for _, x in ipairs(o) do local p = {} for k, v in pairs(x) do if k ~= "message" and k ~= "_msg" and k ~= "_time" then '
             'p[#p+1] = string.format("%q:%s", k, type(v) == "number" and tostring(v) or string.format("%q", tostring(v))) '
             'end end print("{" .. table.concat(p, ",") .. "}") end')
lines.append('for k, v in pairs(KEPT) do print("KEPT\\t" .. k .. "\\t" .. v) end')
with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False) as f:
    f.write("\n".join(lines))
run = subprocess.run([lua_bin, f.name], capture_output=True, text=True)
os.unlink(f.name)
if run.returncode != 0:
    sys.exit("lua failed:\n" + run.stderr[-2000:])
sim = [json.loads(l) for l in run.stdout.splitlines() if l.startswith("{")]
kept = {l.split("\t")[1]: int(l.split("\t")[2]) for l in run.stdout.splitlines() if l.startswith("KEPT\t")}

FIELDS = ["requests", "reads", "writes", "errors", "errors_4xx", "errors_5xx", "auth_denied", "response_bytes",
          "last_read_bytes", "last_write_bytes", "commit_count", "commit_ms_sum", "commit_ms_min", "commit_ms_max",
          "dropped", "resource_kind", "api_kind", "access_seen", "access_kept", "access_counted", "counted_read",
          "counted_post", "errors_kept", "parse_errors", "app_dropped_total", "distinct_resources",
          "distinct_principals", "role_keys_forced", "resources_other", "principals_other",
          "counted_404", "app_dropped_404", "held_orphans", "held_pending"]
key = lambda r: (r["report_type"], r.get("resource") or r.get("user_principal_name") or r.get("logger_name") or "")
R, S = {key(r): r for r in rep}, {key(r): r for r in sim}
print(f"rows: pipeline {len(R)}, replay {len(S)}")
for k in sorted(set(R) - set(S)): print("  ONLY IN PIPELINE", k)
for k in sorted(set(S) - set(R)): print("  ONLY IN REPLAY  ", k)
bad = 0
for k in sorted(R.keys() & S.keys()):
    for fld in FIELDS:
        if R[k].get(fld) != S[k].get(fld):
            bad += 1
            print(f"  DIFF {k} {fld}: pipeline={R[k].get(fld)} replay={S[k].get(fld)}")
ok = bad == 0 and set(R) == set(S)
if os.path.exists(f"{d}/detail.json"):
    from collections import Counter
    det = Counter(x.get("loggerName") for x in json.load(open(f"{d}/detail.json")))
    print("detail docs by logger: stored / replay-emitted")
    for lg in sorted(set(det) | set(kept)):
        mark = "" if det.get(lg, 0) == kept.get(lg, 0) else "   <-- differs"
        print(f"  {det.get(lg, 0):>5} / {kept.get(lg, 0):<5} {lg}{mark}")
    ok = ok and dict(det) == kept
print(f"{'PASS' if ok else 'FAIL'}: {bad} field mismatch(es) over {len(R.keys() & S.keys())} rows x {len(FIELDS)} fields")
print("  A near-edge off-by-one means step10 cut the interval differently from the tick -- re-check the emit time before calling it a fault.")
sys.exit(0 if ok else 1)
