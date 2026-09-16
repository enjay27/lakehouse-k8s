#!/usr/bin/env bash
# ============================================================================
# Step 1 of logging/PLAN-opensearch-cutover-2026-09-08.md (v4)
#
# Scope: the two OpenSearch-side facts the Fluent Bit change depends on, and
# nothing more. v4 §6 hands templates, ISM, dedup and the query layer to someone
# else -- this script deliberately does NOT check them.
#
# READ-ONLY except for one throwaway index (`polaris-preflight-probe`) that it
# creates and deletes. No helm, no kubectl mutation, no config change.
#
#     export OS_URL=https://192.168.194.1:9200
#     export OS_USER=admin
#     export OS_PASSWORD='...'        # never stored in this repo -- issue #4
#     bash logging/scripts/step0-preflight.sh
#
# The third check of v4 step 1 -- reachability FROM A POD -- cannot be done from
# a laptop shell. The command is printed at the end; run it yourself.
# ============================================================================
set -uo pipefail

: "${OS_URL:?set OS_URL}"; : "${OS_USER:?set OS_USER}"; : "${OS_PASSWORD:?set OS_PASSWORD}"
command -v jq >/dev/null || { echo "FATAL: jq is required."; exit 2; }

OS=(curl -sS -k --max-time 30 -u "${OS_USER}:${OS_PASSWORD}")
FAIL=0
ok()  { echo "  PASS  $*"; }
bad() { echo "  FAIL  $*"; FAIL=$((FAIL+1)); }

echo "=== 1. OpenSearch version — recorded nowhere in this repo ==="
V="$("${OS[@]}" "${OS_URL}/" 2>&1)"
NUM="$(echo "$V" | jq -r '.version.number // empty' 2>/dev/null)"
DIST="$(echo "$V" | jq -r '.version.distribution // "elasticsearch"' 2>/dev/null)"
if [ -n "$NUM" ]; then
  ok "$DIST $NUM   <-- write this into .memory/environments.md"
else
  bad "no version returned. Raw: $(echo "$V" | head -c 200)"
  echo "        If this failed on TLS or auth, the shipper will fail the same way (trap 3.6)."
fi

echo
echo "=== 2. Does this OpenSearch accept a top-level '_msg' field? ==="
echo "    v4 §2.4 keeps the VictoriaLogs field names. If '_msg' is rejected, that"
echo "    decision has to change BEFORE the config is written, not after."
"${OS[@]}" -XDELETE "${OS_URL}/polaris-preflight-probe" >/dev/null 2>&1
P="$("${OS[@]}" -XPOST -H 'Content-Type: application/json' \
     "${OS_URL}/polaris-preflight-probe/_doc?refresh=true" \
     -d '{"_msg":"probe","_time":"2026-09-08T00:00:00.123456789Z","sequence":1,"http_status":404}' 2>&1)"
if echo "$P" | jq -e '.result == "created"' >/dev/null 2>&1; then
  ok "'_msg' accepted — keep the field names, no rename filter needed."
  NS="$("${OS[@]}" "${OS_URL}/polaris-preflight-probe/_mapping" 2>/dev/null \
        | jq -r '..|.["_time"]?|select(.!=null)|.type' 2>/dev/null | head -1)"
  [ -n "$NS" ] && echo "        FYI dynamic mapping gave '_time' type='${NS}' — 9 fractional digits"
  echo "        may need date_nanos (v4 §5 Q3). That decision is §6's, not this change's."
else
  bad "'_msg' REJECTED — v4 §2.4 must change before the config is written."
  echo "        $(echo "$P" | jq -c '.error.reason? // .' 2>/dev/null | head -c 300)"
fi
"${OS[@]}" -XDELETE "${OS_URL}/polaris-preflight-probe" >/dev/null 2>&1

echo
echo "=== 3. NOT CHECKED HERE — reachability from a Deployment pod (v4 §5 Q2) ==="
echo "    The DaemonSet reaches OpenSearch from a host-network context. The shipper is a"
echo "    Deployment and does not. A PASS above proves your laptop can reach 9200; it"
echo "    proves nothing about the pod. Confirm the context first, then run:"
echo
echo "      kubectl config current-context      # must be exactly: orbstack"
echo "      kubectl -n datahub-hynix exec deploy/fb-polaris-shipper -- \\"
echo "        curl -sk -o /dev/null -w '%{http_code}\\n' --max-time 10 ${OS_URL}"
echo
echo "    Anything other than 200/401 means the shipper cannot ship, and every"
echo "    render grep in step 2 will still pass."
echo
[ "$FAIL" -gt 0 ] && { echo "RESULT: ${FAIL} check(s) failed — do not start step 2."; exit 1; }
echo "RESULT: laptop-side checks passed. Step 3 above is still outstanding."
exit 0
