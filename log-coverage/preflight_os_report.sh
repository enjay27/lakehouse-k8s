#!/usr/bin/env bash
# Read-only preflight for PLAN-api-status-matrix.md sections 0.1 / 0.2 / 0.3.
#
# It answers the two questions that decide whether the api-status-matrix run is
# worth taking, and NOTHING else -- no writes, no traffic, no mutation:
#
#   0.1  do polaris-report-* / polaris-logs-* exist in OpenSearch at all?
#   0.2  is REPORT schema v3 flowing, or is everything stored still v2?
#   0.3  which Lua is actually RUNNING, and what are its constants?
#
# Every check prints PASS / FAIL / UNKNOWN with the reason. A check that cannot
# run says so; it never prints a tidy zero. Run it AFTER some Polaris traffic --
# a freshly rolled shipper has counted nothing yet, which is not the same as
# broken.
#
#   export OS_PASSWORD=...            # never hardcoded; same value as opensearch_pass
#   ./preflight_os_report.sh
#
# Optional overrides:
#   OS_URL       (default https://localhost:9200)   OS_USER (default admin)
#   NS           (default datahub-hynix)
#   DS_RELEASE   (default benchmarks-fluent-bit)    the DaemonSet -> OpenSearch
#   DEP_RELEASE  (default fb-polaris-shipper)       the Deployment -> VictoriaLogs

set -uo pipefail

OS_URL="${OS_URL:-https://localhost:9200}"
OS_USER="${OS_USER:-admin}"
NS="${NS:-datahub-hynix}"
DS_RELEASE="${DS_RELEASE:-benchmarks-fluent-bit}"
DEP_RELEASE="${DEP_RELEASE:-fb-polaris-shipper}"
: "${OS_PASSWORD:?set OS_PASSWORD (do not put it on the command line)}"

pass() { printf '  \033[32mPASS\033[0m   %s\n' "$*"; }
fail() { printf '  \033[31mFAIL\033[0m   %s\n' "$*"; }
unkn() { printf '  \033[33m?\033[0m      %s\n' "$*"; }
head_() { printf '\n== %s\n' "$*"; }

os() {  # os <path> [body]
  local path="$1"; shift || true
  if [ $# -gt 0 ]; then
    curl -sk -u "$OS_USER:$OS_PASSWORD" -H 'Content-Type: application/json' \
         -m 20 "$OS_URL$path" -d "$1"
  else
    curl -sk -u "$OS_USER:$OS_PASSWORD" -m 20 "$OS_URL$path"
  fi
}

head_ "0 -- can we talk to OpenSearch"
ROOT="$(os "/" || true)"
if [ -z "$ROOT" ] || ! echo "$ROOT" | jq -e .version.number >/dev/null 2>&1; then
  fail "$OS_URL unreachable or not OpenSearch. Port-forward first:"
  echo "         kubectl -n <os-ns> port-forward svc/<opensearch> 9200:9200"
  echo "       Everything below would print an honest-looking zero, so: stopping."
  exit 2
fi
pass "$OS_URL  $(echo "$ROOT" | jq -r '.version.distribution + " " + .version.number')"

# ---------------------------------------------------------------- 0.1 indices
head_ "0.1 -- do the guide's indices exist"
IDX="$(os "/_cat/indices/polaris-*?h=index,docs.count,store.size&format=json" || true)"
if [ -z "$IDX" ] || [ "$(echo "$IDX" | jq -r 'type')" != "array" ] || [ "$(echo "$IDX" | jq 'length')" = "0" ]; then
  fail "NO polaris-* index exists. GUIDE-schema-v3-testing gates 0-6 have no source."
  echo "       The DaemonSet may be shipping to k8s-logs-* (its stock index) rather than"
  echo "       to polaris-logs-* / polaris-report-*. Compare:"
  os "/_cat/indices/*log*?h=index,docs.count" | sed 's/^/         /'
  echo "       -> the api-status-matrix run CANNOT be taken against OpenSearch until this"
  echo "          is wired. That is decision (2) in PLAN-api-status-matrix.md section 7."
else
  echo "$IDX" | jq -r '.[] | "         \(.index)  docs=\(."docs.count")  \(."store.size")"'
  echo "$IDX" | jq -e 'map(select(.index|startswith("polaris-report"))) | length > 0' >/dev/null \
    && pass "polaris-report-* present" || fail "polaris-report-* MISSING -- gates 0-6 have no source"
  echo "$IDX" | jq -e 'map(select(.index|startswith("polaris-logs"))) | length > 0' >/dev/null \
    && pass "polaris-logs-* present"   || fail "polaris-logs-* MISSING -- gate 2's cross-check and the per-call rule-3 check have no source"
fi

# ------------------------------------------------------------ 0.2 schema v3
head_ "0.2 -- GATE 0: is REPORT schema v3 actually flowing"
SV="$(os "/polaris-report-*/_search" '{"size":0,"aggs":{"v":{"terms":{"field":"schema_version","size":10}}}}' || true)"
if echo "$SV" | jq -e '.aggregations.v.buckets' >/dev/null 2>&1; then
  echo "$SV" | jq -r '.aggregations.v.buckets[] | "         schema_version=\(.key)  rows=\(.doc_count)"'
  if echo "$SV" | jq -e '.aggregations.v.buckets|map(select(.key==3))|length>0' >/dev/null; then
    LATEST="$(os "/polaris-report-*/_search" '{"size":1,"query":{"bool":{"filter":[{"term":{"schema_version":3}}]}},"sort":[{"@timestamp":"desc"}],"_source":["window_start","window_end","window_seconds","report_type","report_seq","hostname","access_seen","partial_window"]}' || true)"
    pass "v3 rows exist -- newest:"
    echo "$LATEST" | jq -c '.hits.hits[0]._source' | sed 's/^/         /'
  else
    fail "NO schema_version:3 row. SCHEMA-report.md says v3 is 'written, not yet deployed' --"
    echo "       this confirms it. Gates 2 / 4-denial / 5 are UNAVAILABLE, not failed."
    echo "       -> that is decision (1) in PLAN-api-status-matrix.md section 7."
  fi
else
  unkn "cannot aggregate schema_version (index absent, or the field is not mapped as a number)"
fi

head_ "0.2b -- the array split (one window must hold three report_types)"
WS="$(os "/polaris-report-*/_search" '{"size":0,"query":{"bool":{"filter":[{"range":{"access_seen":{"gt":0}}}]}},"aggs":{"w":{"terms":{"field":"window_start.keyword","size":1,"order":{"_key":"desc"}},"aggs":{"t":{"terms":{"field":"report_type.keyword"}}}}}}' || true)"
if echo "$WS" | jq -e '.aggregations.w.buckets[0]' >/dev/null 2>&1; then
  echo "$WS" | jq -r '.aggregations.w.buckets[0] | "         window \(.key):  " + (.t.buckets|map("\(.key)=\(.doc_count)")|join("  "))'
  echo "$WS" | jq -e '[.aggregations.w.buckets[0].t.buckets[].key]|sort == ["principal","resource","summary"]' >/dev/null \
    && pass "Fluent Bit splits the array into three record types" \
    || fail "the array did NOT split into summary/resource/principal -- the schema these gates target does not exist in this index"
else
  unkn "no window with access_seen > 0 yet. EXPECTED right after a roll: Polaris logs only on"
  echo "       request. Drive some traffic, wait one WINDOW_SECONDS, re-run."
fi

# --------------------------------------------------- the guide's mapping trap
head_ "0.2c -- the min_record_time trap (guide: 'Traps carried over')"
NEW="$(os "/_cat/indices/polaris-report-*?h=index&s=index:desc" | head -1 | tr -d ' ')"
if [ -n "$NEW" ]; then
  MT="$(os "/$NEW/_mapping/field/min_record_time" || true)"
  T="$(echo "$MT" | jq -r '..|.type? // empty' | head -1)"
  case "$T" in
    date) pass "$NEW: min_record_time mapped as date -- date maths works" ;;
    text|keyword) fail "$NEW: min_record_time mapped as $T. The Lua writes \"\" on idle windows and"
          echo "       OpenSearch typed the field from the first one. PERMANENT for this index." ;;
    "")   unkn "$NEW: min_record_time not mapped yet (no row has carried it)" ;;
    *)    unkn "$NEW: min_record_time mapped as $T" ;;
  esac
  PW="$(os "/$NEW/_search" '{"size":0,"query":{"term":{"partial_window":"true"}}}' || true)"
  echo "$PW" | jq -e '.hits.total.value' >/dev/null 2>&1 \
    && echo "         partial_window:\"true\" (STRING, per review #1) matches $(echo "$PW" | jq -r '.hits.total.value') rows"
fi

# ------------------------------------------------------- 0.3 the running Lua
head_ "0.3 -- which Lua is RUNNING (the ConfigMap is not the process)"
if ! command -v kubectl >/dev/null; then
  unkn "kubectl not on PATH -- cannot confirm the running config"
else
  for rel in "$DS_RELEASE" "$DEP_RELEASE"; do
    CM="$(kubectl -n "$NS" get cm -l "app.kubernetes.io/instance=$rel" -o yaml 2>/dev/null)"
    if [ -z "$CM" ]; then unkn "$rel: no ConfigMap found in $NS"; continue; fi
    echo "       --- $rel"
    for k in polaris_cri_unwrap polaris_key_rename polaris_noise_filter build_report; do
      echo "$CM" | grep -q "$k" && echo "         ok      $k" || echo "         absent  $k"
    done
    for c in SCHEMA_VERSION WINDOW_SECONDS REPORT_MAX_RESOURCES REPORT_MAX_PRINCIPALS REPORT_MAX_ROLE_KEYS; do
      v="$(echo "$CM" | grep -oE "local +$c *= *[0-9]+" | grep -oE '[0-9]+$' | head -1)"
      [ -n "$v" ] && echo "         $c = $v"
    done
    POD="$(kubectl -n "$NS" get pods -l "app.kubernetes.io/instance=$rel" \
           -o jsonpath='{range .items[*]}{.metadata.name}@{.status.startTime}{"\n"}{end}' 2>/dev/null)"
    [ -n "$POD" ] && echo "         pods: $POD" | tr '\n' ' ' && echo
  done
  echo "       NOTE: a ConfigMap change alone does not roll a pod. If the pod predates the"
  echo "             ConfigMap, the file is deployed and the POLICY is not -- this repo's"
  echo "             most expensive failure (2026-09-03, 0 of 34 expected drops dropped)."
fi

# --------------------------------------------- does the access log reach OS?
head_ "0.4 -- does the ACCESS LOG reach polaris-logs-* (not just app lines)"
AL="$(os "/polaris-logs-*/_search" '{"size":0,"query":{"bool":{"filter":[{"exists":{"field":"http_status"}}]}},"aggs":{"s":{"terms":{"field":"http_status","size":12}}}}' || true)"
if echo "$AL" | jq -e '.aggregations.s.buckets' >/dev/null 2>&1; then
  N="$(echo "$AL" | jq -r '.hits.total.value')"
  if [ "$N" = "0" ]; then
    fail "polaris-logs-* holds NO record with http_status. The DaemonSet tails CONTAINER"
    echo "       STDOUT; the access log is written to /deployments/logs/polaris.log on the PVC."
    echo "       If Polaris does not also echo it to stdout, the per-call half of the matrix"
    echo "       has no source in OpenSearch even though the report half works."
  else
    pass "$N access-log records; status mix:"
    echo "$AL" | jq -r '.aggregations.s.buckets[] | "         \(.key)  x\(.doc_count)"'
  fi
else
  unkn "polaris-logs-* absent, or http_status not mapped as a number (type_int_key)"
fi

# ------------------------------------------ which index actually holds the rows
head_ "0.5 -- WHERE the report rows live (_cat and the aggregation disagreed once)"
BY="$(os "/polaris-report-*/_search" '{"size":0,"aggs":{"i":{"terms":{"field":"_index","size":20},"aggs":{"v":{"terms":{"field":"schema_version","size":5}}}}}}' || true)"
if echo "$BY" | jq -e '.aggregations.i.buckets' >/dev/null 2>&1; then
  echo "$BY" | jq -r '.aggregations.i.buckets[] | "         \(.key)  total=\(.doc_count)  " + (.v.buckets|map("v\(.key)=\(.doc_count)")|join("  "))'
  TOTAL="$(echo "$BY" | jq -r '[.aggregations.i.buckets[].doc_count]|add')"
  echo "         aggregation total = $TOTAL"
  echo "       Compare with the docs= figures in 0.1. If they disagree, the daily index"
  echo "       suffix is NOT tracking the window date -- and every per-index conclusion"
  echo "       above (the mapping check especially) was taken on the wrong index."
  # the mapping that actually matters: the index holding the v3 rows
  V3IDX="$(echo "$BY" | jq -r '[.aggregations.i.buckets[]|select(.v.buckets|map(.key)|index(3))]|sort_by(.doc_count)|last|.key // empty')"
  if [ -n "$V3IDX" ]; then
    T2="$(os "/$V3IDX/_mapping/field/min_record_time" | jq -r '..|.type? // empty' | head -1)"
    case "$T2" in
      date) pass "$V3IDX (holds the v3 rows): min_record_time mapped as date" ;;
      "")   unkn "$V3IDX (holds the v3 rows): min_record_time not mapped yet" ;;
      *)    fail "$V3IDX (holds the v3 rows): min_record_time mapped as $T2 -- permanent for this index" ;;
    esac
  fi
else
  unkn "cannot aggregate by _index"
fi


printf '\n== done. Paste this whole output back into the session.\n'
