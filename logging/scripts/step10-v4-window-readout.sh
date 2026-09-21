#!/usr/bin/env bash
# ============================================================================
# Phase 0 of logging/PLAN-audit-log-todo-2026-09-16.md -- ONE report window, all
# three sources, saved as JSON for review. Read-only: _search and _mapping only.
#
#   export OS_URL=https://192.168.194.1:9200 OS_USER=admin OS_PASSWORD='...'
#   bash logging/scripts/step10-v4-window-readout.sh 2026-09-15T09:20:00Z [window_seconds]
#
# The argument is the report row's window_start, in UTC (KST - 9h). Default window 30s.
#
# WHY THE TIME RANGE IS NOT THE LABEL. A report row labelled [W, W+30) actually
# holds the records between the tick that closed the previous window and the tick
# that closed this one (#26): [emit - 30s, emit), emit = window_end + tick phase.
# The script reads `emit` off the summary row itself and cuts the detail and the
# k8s-logs copy on that interval, so no phase is assumed.
#
# Writes .scratch/readout-<W>/ (gitignored):
#   report.json    every report row for W (summary, resource, principal, app_dropped)
#   detail.json    polaris-logs-* docs in [emit-30s, emit)
#   tier1.json     k8s-logs-* Polaris docs in the same interval (unfiltered copy)
#   mapping.json   field mappings of the v4 fields in both Polaris indices
# and prints the counts that gates G1-G8 and Gate 2 are read from.
# ============================================================================
set -uo pipefail
: "${OS_URL:?}"; : "${OS_USER:?}"; : "${OS_PASSWORD:?}"
W="${1:?usage: $0 <window_start UTC, e.g. 2026-09-15T09:20:00Z> [window_seconds]}"
WS="${2:-30}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="$ROOT/.scratch/readout-${W//:/}"
mkdir -p "$OUT"
OS=(curl -sS -k --max-time 60 -u "${OS_USER}:${OS_PASSWORD}" -H 'Content-Type: application/json')

python3 - "$W" "$WS" "$OUT" "$OS_URL" <<'PY' || exit 1
import json, subprocess, sys, os, datetime as dt
W, WS, OUT, URL = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
auth = f"{os.environ['OS_USER']}:{os.environ['OS_PASSWORD']}"
def q(path, body):
    r = subprocess.run(["curl","-sS","-k","--max-time","60","-u",auth,"-H","Content-Type: application/json",
                        f"{URL}/{path}","-d",json.dumps(body)], capture_output=True, text=True)
    try: return json.loads(r.stdout)
    except Exception: print("  !! bad response from", path, r.stdout[:300], r.stderr[:300]); sys.exit(1)
def hits(resp):
    if "hits" not in resp: print("  !! query error:", json.dumps(resp)[:400]); sys.exit(1)
    return [h["_source"] for h in resp["hits"]["hits"]]
iso = lambda t: t.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
w0 = dt.datetime.strptime(W, "%Y-%m-%dT%H:%M:%SZ")
w1 = w0 + dt.timedelta(seconds=WS)

# 1. report rows: emitted within 10s after window_end (tick phase < Interval_Sec 5)
rep = hits(q("polaris-report-*/_search", {"size": 5000, "query": {"range": {"@timestamp": {
      "gte": iso(w1), "lt": iso(w1 + dt.timedelta(seconds=10))}}}, "sort": [{"@timestamp": "asc"}]}))
rep = [r for r in rep if str(r.get("window_start","")).startswith(W[:19])]
json.dump(rep, open(f"{OUT}/report.json","w"), indent=1, ensure_ascii=False)
summ = [r for r in rep if r.get("report_type") == "summary"]
if len(summ) != 1:
    print(f"  !! expected exactly 1 summary row for {W}, found {len(summ)} (rows: {len(rep)}).")
    print("     Wrong window, or the report index has no row for it."); sys.exit(1)
s = summ[0]
emit = dt.datetime.strptime(s["@timestamp"][:23], "%Y-%m-%dT%H:%M:%S.%f")
lo, hi = emit - dt.timedelta(seconds=WS), emit
print(f"== window {W} ({WS}s)  seq={s.get('report_seq')}@{s.get('hostname')}  schema={s.get('schema_version')}")
print(f"   emitted {iso(emit)}  -> tick phase {(emit - w1).total_seconds():.3f}s")
print(f"   record interval [{iso(lo)}, {iso(hi)})")

# 2. detail docs in the tick interval
det = hits(q("polaris-logs-*/_search", {"size": 10000, "query": {"range": {"@timestamp": {
      "gte": iso(lo), "lt": iso(hi)}}}, "sort": [{"@timestamp": "asc"}]}))
json.dump(det, open(f"{OUT}/detail.json","w"), indent=1, ensure_ascii=False)

# 3. tier-1 copy: Polaris records are the ones carrying `sequence` + `loggerName`
t1 = hits(q("k8s-logs-*/_search", {"size": 10000, "query": {"bool": {"filter": [
      {"exists": {"field": "sequence"}}, {"exists": {"field": "loggerName"}},
      {"range": {"@timestamp": {"gte": iso(lo), "lt": iso(hi)}}}]}},
      "_source": {"excludes": ["kubernetes.labels*", "kubernetes.annotations*"]},
      "sort": [{"@timestamp": "asc"}]}))
json.dump(t1, open(f"{OUT}/tier1.json","w"), indent=1, ensure_ascii=False)

# 4. mappings of the v4 fields
flds = "commit_count,commit_ms_sum,commit_ms_min,commit_ms_max,dropped,app_dropped_total,logger_name,window_start,min_record_time,http_status,response_size,secret_redacted"
mp = {}
for idx in ("polaris-report-*", "polaris-logs-*"):
    r = subprocess.run(["curl","-sS","-k","--max-time","60","-u",auth, f"{URL}/{idx}/_mapping/field/{flds}"],
                       capture_output=True, text=True)
    try: mp[idx] = json.loads(r.stdout)
    except Exception: mp[idx] = r.stdout
json.dump(mp, open(f"{OUT}/mapping.json","w"), indent=1)

from collections import Counter
types = Counter(r.get("report_type") for r in rep)
print(f"\n-- report rows: {dict(types)}")
for k in ("access_seen","access_kept","access_counted","parse_errors","errors_4xx","errors_5xx","auth_denied",
          "app_dropped_total","distinct_resources","distinct_principals","resources_other","role_keys_forced","windows_skipped"):
    print(f"   summary.{k:<22} {s.get(k)}")
print(f"\n-- detail docs: {len(det)}   by logger: {dict(Counter(d.get('loggerName') for d in det))}")
print(f"-- tier1 Polaris docs: {len(t1)}   by logger (top 10): {dict(Counter(d.get('loggerName') for d in t1).most_common(10))}")
if t1: print(f"   tier1 sample keys: {sorted(t1[0].keys())[:25]}")
print(f"\nSaved to {OUT}/  -- tell Claude the window; it reads the JSON from there.")
PY
