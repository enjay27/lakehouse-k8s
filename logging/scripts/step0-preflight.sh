#!/usr/bin/env bash
# ============================================================================
# Step 0 of logging/PLAN-opensearch-cutover-2026-09-08.md
#
# Decides whether the OpenSearch cutover may start, and whether tier 2 may be
# sourced from stdout instead of the log PVC.
#
# READ-ONLY against OpenSearch and VictoriaLogs, with ONE exception: check 3
# creates and deletes a throwaway index named `polaris-preflight-probe`.
# Nothing else is written. No cluster mutation, no helm, no kubectl.
#
# Run it from the repo root:
#     export OS_URL=https://192.168.194.1:9200
#     export OS_USER=admin
#     export OS_PASSWORD='...'          # NOT stored in this repo -- see #4
#     export VL_URL=http://192.168.139.2:9428
#     bash logging/scripts/step0-preflight.sh
#
# Optional: --hours N   how far back to look for report windows (default 2)
#
# The gate is check 5. Everything before it is context that check 5 needs in
# order to mean anything.
# ============================================================================
set -uo pipefail

HOURS=2
[ "${1:-}" = "--hours" ] && HOURS="${2:-2}"

OS_URL="${OS_URL:-}"; OS_USER="${OS_USER:-}"; OS_PASSWORD="${OS_PASSWORD:-}"
VL_URL="${VL_URL:-}"
: "${OS_URL:?set OS_URL}"; : "${OS_USER:?set OS_USER}"; : "${OS_PASSWORD:?set OS_PASSWORD}"
: "${VL_URL:?set VL_URL -- the report side of the comparison lives in VictoriaLogs}"

command -v jq >/dev/null || { echo "FATAL: jq is required."; exit 2; }

OS=(curl -sS -k --max-time 30 -u "${OS_USER}:${OS_PASSWORD}")
PASS=0; FAIL=0; UNKNOWN=0
ok()   { echo "  PASS  $*"; PASS=$((PASS+1)); }
bad()  { echo "  FAIL  $*"; FAIL=$((FAIL+1)); }
huh()  { echo "  ????  $*"; UNKNOWN=$((UNKNOWN+1)); }
hdr()  { echo; echo "=== $* ==="; }

# ---------------------------------------------------------------- check 1 ---
hdr "1. OpenSearch version (recorded nowhere in this repo -- plan Q6)"
VER_JSON="$("${OS[@]}" "${OS_URL}/" 2>&1)"
VER="$(echo "$VER_JSON" | jq -r '.version.number // empty' 2>/dev/null)"
DIST="$(echo "$VER_JSON" | jq -r '.version.distribution // "elasticsearch"' 2>/dev/null)"
if [ -n "$VER" ]; then ok "$DIST $VER  <-- write this into .memory/environments.md"
else bad "could not read a version. Raw: $(echo "$VER_JSON" | head -c 200)"; fi

# ---------------------------------------------------------------- check 2 ---
hdr "2. Field mappings in k8s-logs -- the .keyword trap, on query one"
SEQ_FIELD=""; HOST_FIELD=""
map_of() {
  "${OS[@]}" "${OS_URL}/k8s-logs-*/_mapping/field/$1" 2>/dev/null \
    | jq -r --arg f "$1" \
      '[.[].mappings|to_entries[]|select(.key==$f)|.value.mapping[]?.type] | unique | join(",")' 2>/dev/null
}
agg_name() {  # echo the aggregatable name for a field, or empty
  local f="$1" t
  t="$("${OS[@]}" "${OS_URL}/k8s-logs-*/_mapping/field/${f}" 2>/dev/null \
       | jq -r "[.[].mappings|to_entries[]|select(.key==\"${f}\")|.value.mapping[]?.type] | unique | .[0] // empty")"
  case "$t" in
    text)                        echo "${f}.keyword" ;;
    keyword|long|integer|double) echo "${f}" ;;
    "")                          echo "" ;;
    *)                           echo "${f}" ;;
  esac
}
for F in sequence hostName loggerName; do
  T="$(map_of "$F")"; A="$(agg_name "$F")"
  if [ -z "$T" ]; then huh "$F: not mapped in k8s-logs-* (no document has carried it?)"
  else ok "$F: type=[$T] -> aggregate on '$A'"; fi
  [ "$F" = sequence ] && SEQ_FIELD="$A"
  [ "$F" = hostName ] && HOST_FIELD="$A"
done
LOGGER_FIELD="$(agg_name loggerName)"; LOGGER_FIELD="${LOGGER_FIELD:-loggerName.keyword}"
if [ -z "$SEQ_FIELD" ] || [ -z "$HOST_FIELD" ]; then
  bad "cannot dedup without both sequence and hostName. Stopping before check 5."
fi

# ---------------------------------------------------------------- check 3 ---
hdr "3. Does this OpenSearch accept a top-level '_msg' field? (plan 2.5)"
"${OS[@]}" -XDELETE "${OS_URL}/polaris-preflight-probe" >/dev/null 2>&1
PROBE="$("${OS[@]}" -XPOST -H 'Content-Type: application/json' \
  "${OS_URL}/polaris-preflight-probe/_doc?refresh=true" \
  -d '{"_msg":"probe","_time":"2026-09-08T00:00:00.123456789Z","sequence":1}' 2>&1)"
if echo "$PROBE" | jq -e '.result == "created"' >/dev/null 2>&1; then
  ok "'_msg' accepted -> plan 2.5 stands: do NOT rename. Dual-write is safe."
else
  bad "'_msg' rejected -> take the fallback: rename lands in the CUTOVER commit only."
  echo "        $(echo "$PROBE" | jq -c '.error.reason? // .' 2>/dev/null | head -c 300)"
fi

# ---------------------------------------------------------------- check 4 ---
hdr "4. Can this credential PUT a composable index template?"
TPL="$("${OS[@]}" -XPUT -H 'Content-Type: application/json' \
  "${OS_URL}/_index_template/polaris-preflight-probe-tpl" \
  -d '{"index_patterns":["polaris-preflight-probe-*"],"template":{"settings":{"number_of_shards":1}}}' 2>&1)"
if echo "$TPL" | jq -e '.acknowledged == true' >/dev/null 2>&1; then
  ok "template PUT accepted (composable _index_template API is available)"
  "${OS[@]}" -XDELETE "${OS_URL}/_index_template/polaris-preflight-probe-tpl" >/dev/null 2>&1
else
  bad "template PUT refused: $(echo "$TPL" | jq -c '.error.reason? // .' 2>/dev/null | head -c 300)"
fi
"${OS[@]}" -XDELETE "${OS_URL}/polaris-preflight-probe" >/dev/null 2>&1

hdr "4b. Is tier 1's 5-day retention an ISM policy? (plan Q5)"
ISM="$("${OS[@]}" "${OS_URL}/_plugins/_ism/policies" 2>/dev/null | jq -r '.total_policies? // empty')"
if [ -n "$ISM" ]; then ok "ISM plugin present, ${ISM} policy(ies) defined -- tiers 2/3 can use it"
else huh "no ISM policy list returned; tier 1's 5d may be a manual curator. Settle before step 9."; fi

# ---------------------------------------------------------------- check 5 ---
hdr "5. THE GATE -- does stdout carry the same access-log set as the log file?"
echo "    Method: the shipper's own report defines the windows. For each summary row,"
echo "    count DEDUPLICATED access-log records in k8s-logs for that exact window and"
echo "    compare with access_seen. Reports come from the file; k8s-logs comes from stdout."
echo

START="$(date -u -v-"${HOURS}"H +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -d "${HOURS} hours ago" +%Y-%m-%dT%H:%M:%SZ)"
END="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "    range: ${START} .. ${END}"

REPORTS="$(curl -sS --max-time 30 "${VL_URL}/select/logsql/query" \
  --data-urlencode 'query=app:polaris-shipper-report report_type:summary schema_version:2 | fields window_start, window_end, access_seen, hostname' \
  --data-urlencode "start=${START}" --data-urlencode "end=${END}" \
  --data-urlencode 'limit=0' 2>&1)"
NROWS="$(echo "$REPORTS" | grep -c 'window_start' || true)"
if [ "${NROWS:-0}" -eq 0 ]; then
  bad "no schema-v2 summary rows in that range -- widen --hours, or the shipper is not reporting."
  echo "        (A zero here is NOT a pass. 0 of 0 is not an answer.)"
else
  echo "    ${NROWS} report window(s) found"
fi

# deduplicated count for one window, via composite agg (exact; NOT cardinality)
dedup_window() {  # $1=start $2=end  -> "<total_hits> <distinct_buckets> <hist>"
  local ws="$1" we="$2" after='null' total=0 distinct=0 body resp hist=""
  local counts_file; counts_file="$(mktemp)"
  while : ; do
    body="$(jq -n --arg s "$ws" --arg e "$we" --arg lf "$LOGGER_FIELD" \
                  --arg hf "$HOST_FIELD" --arg sf "$SEQ_FIELD" --argjson a "$after" '
      {size:0,
       query:{bool:{filter:[
         {term:{($lf):"io.quarkus.http.access-log"}},
         {range:{"@timestamp":{gte:$s, lt:$e}}}]}},
       aggs:{u:{composite:( {size:1000,
         sources:[{h:{terms:{field:$hf}}},{s:{terms:{field:$sf}}}]}
         + (if $a == null then {} else {after:$a} end) )}}}')"
    resp="$("${OS[@]}" -XPOST -H 'Content-Type: application/json' \
            "${OS_URL}/k8s-logs-*/_search" -d "$body" 2>&1)"
    echo "$resp" | jq -e '.aggregations.u' >/dev/null 2>&1 || { echo "ERR $(echo "$resp" | jq -c '.error.reason? // .' | head -c 200)"; rm -f "$counts_file"; return 1; }
    echo "$resp" | jq -r '.aggregations.u.buckets[].doc_count' >> "$counts_file"
    total=$(( total + $(echo "$resp" | jq '[.aggregations.u.buckets[].doc_count] | add // 0') ))
    distinct=$(( distinct + $(echo "$resp" | jq '.aggregations.u.buckets | length') ))
    after="$(echo "$resp" | jq -c '.aggregations.u.after_key // null')"
    [ "$after" = "null" ] && break
  done
  local singles triples
  singles="$(awk '$1==1' "$counts_file" | wc -l | tr -d ' ')"
  triples="$(awk '$1>=3'  "$counts_file" | wc -l | tr -d ' ')"
  hist="$(sort -n "$counts_file" | uniq -c | awk '{printf "%s bucket(s)@%s-doc; ", $1, $2}')"
  rm -f "$counts_file"
  echo "$total $distinct $singles $triples $hist"
}

echo "$REPORTS" | while IFS= read -r row; do
  [ -z "$row" ] && continue
  WS="$(echo "$row" | jq -r '.window_start // empty' 2>/dev/null)"
  WE="$(echo "$row" | jq -r '.window_end   // empty' 2>/dev/null)"
  AS="$(echo "$row" | jq -r '.access_seen  // empty' 2>/dev/null)"
  HN="$(echo "$row" | jq -r '.hostname     // empty' 2>/dev/null)"
  [ -z "$WS" ] && continue
  R="$(dedup_window "$WS" "$WE")"
  if [ "${R%% *}" = "ERR" ]; then
    echo "  ????  ${WS} : ${R#ERR }"
    continue
  fi
  TOT="$(echo "$R" | awk '{print $1}')"; DIS="$(echo "$R" | awk '{print $2}')"
  SINGLES="$(echo "$R" | awk '{print $3}')"; TRIPLES="$(echo "$R" | awk '{print $4}')"
  HIST="$(echo "$R" | cut -d' ' -f5-)"
  printf '  %-22s report(file) access_seen=%-6s  k8s-logs(stdout) raw=%-6s dedup=%-6s\n' \
         "${WS}" "${AS}" "${TOT}" "${DIS}"
  printf '  %-22s bucket sizes: %s\n' "" "${HIST:-none}"
  if [ "${DIS:-0}" = "${AS:-x}" ]; then
    echo "  PASS  stdout carries the same access-log set as the file for this window."
  else
    echo "  FAIL  stdout and the file DISAGREE. Do not proceed to step 3 on this window."
    echo "        -> If dedup < access_seen, stdout is a PARTIAL view: take plan Q1's"
    echo "           fallback (keep the PVC tail + the composed _doc_id from fb91949)."
  fi
  if [ "${SINGLES:-0}" -gt 0 ]; then
    echo "  FAIL  ${SINGLES} bucket(s) hold ONE document where #16 predicts two."
    echo "        Tier 1's OUTPUT 1 upsert is LOSING records -- that is #16's testable"
    echo "        prediction coming true. Investigate before trusting ANY k8s-logs count."
  fi
  if [ "${TRIPLES:-0}" -gt 0 ]; then
    echo "  ????  ${TRIPLES} bucket(s) hold 3+ documents: something replayed. This window is"
    echo "        not clean -- pick another (#14d)."
  fi
  [ -n "$HN" ] && echo "        report emitted by pod: ${HN} (report_seq is per-pod -- guide 7.4 trap 3)"
  echo
done

# ---------------------------------------------------------------- summary ---
hdr "SUMMARY"
echo "  checks 1-4b:  ${PASS} pass, ${FAIL} fail, ${UNKNOWN} unknown"
echo
echo "  Check 5 is the gate and it is printed per window above -- a run with zero"
echo "  windows is NOT a pass. Absence is not zero."
echo
echo "  NOT COVERED BY THIS SCRIPT, and still required before step 3 (plan Q3):"
echo "    kubectl -n datahub-hynix exec deploy/fb-polaris-shipper -- \\"
echo "      curl -sk -o /dev/null -w '%{http_code}\\n' ${OS_URL}"
echo "  The DaemonSet reaches OpenSearch from a host-network context; the shipper is a"
echo "  Deployment and does not. Assume nothing."
[ "$FAIL" -gt 0 ] && exit 1
exit 0
