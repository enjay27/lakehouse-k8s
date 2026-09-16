#!/usr/bin/env bash
# ============================================================================
# Step 3/4 gate for PLAN-opensearch-cutover-2026-09-08.md (v5)
#
# Run AFTER `helm upgrade` of benchmarks-fluent-bit. Read-only: kubectl gets,
# one port-forward, and OpenSearch _count queries. Changes nothing.
#
#     export OS_URL=https://192.168.194.1:9200
#     export OS_USER=admin
#     export OS_PASSWORD='...'
#     bash logging/scripts/step3-postupgrade.sh
#
# The order is deliberate: TIER 1 IS CHECKED BEFORE THE NEW TIERS. The image bump
# to 5.1.1 is the only change reaching node-wide collection, so if that broke, it
# matters more than whether the Polaris pipeline works.
# ============================================================================
set -uo pipefail
NS=datahub-hynix
DS=benchmarks-fluent-bit
# sha256 (first 16) of the repo script, computed now -- so it cannot go stale. Run from the
# repo root. Since policy v5 (2026-09-16) the script ships as its own ConfigMap
# polaris-fluent-bit-lua (`kubectl apply -k fluent-bit/`), not through Helm/--set-file.
# kustomize v5.4.3 was measured to store the bytes verbatim, so the ConfigMap must hash identically.
# (v4 as committed dfbbe21: f364c89653dfe481. v3 was the shipper's aa180e90b9f69bda.)
LUA_CM=polaris-fluent-bit-lua
LUA_FILE=fluent-bit/polaris_access_log.lua
[ -r "$LUA_FILE" ] || { echo "FATAL: run from the repo root ($LUA_FILE not found)"; exit 2; }
LUA_SHA_EXPECT=$(shasum -a 256 "$LUA_FILE" | cut -c1-16)
FAIL=0
ok(){ printf '  PASS  %s\n' "$*"; }
bad(){ printf '  FAIL  %s\n' "$*"; FAIL=$((FAIL+1)); }
huh(){ printf '  ????  %s\n' "$*"; }

[ "$(kubectl config current-context)" = "orbstack" ] || { echo "FATAL: context is not orbstack"; exit 2; }

echo "=== 1. Is the pod up, and on the right image? ==="
kubectl -n $NS rollout status ds/$DS --timeout=60s >/dev/null 2>&1 && ok "rollout complete" || bad "rollout NOT complete"
IMG=$(kubectl -n $NS get ds/$DS -o jsonpath='{.spec.template.spec.containers[*].image}')
case "$IMG" in *:5.1.1) ok "image $IMG";; *) bad "image is $IMG, expected :5.1.1";; esac
RESTARTS=$(kubectl -n $NS get pods -l app.kubernetes.io/instance=$DS \
  -o jsonpath='{.items[*].status.containerStatuses[*].restartCount}' 2>/dev/null)
echo "        restartCount: ${RESTARTS:-?}   (a climbing number is a crashloop)"

echo
echo "=== 2. THE POD LOG — the only place a rejected filter shows up ==="
echo "    #13's failure mode: the filter is disabled and everything else looks fine."
LOG=$(kubectl -n $NS logs ds/$DS --tail=200 2>/dev/null)
BADLINES=$(printf '%s\n' "$LOG" | grep -iE '\[error\]|\[warn\].*(lua|parser|type_int_key)|cannot|invalid|failed|rejected' | head -20)
if [ -z "$BADLINES" ]; then ok "no error/lua/parser complaints in the last 200 lines"
else bad "complaints in the pod log:"; printf '        %s\n' "$BADLINES"; fi
printf '%s\n' "$LOG" | grep -iE 'lua|polaris' | head -5 | sed 's/^/        /'

echo
echo "=== 3. Is the DEPLOYED script the one in the repo? And is hot reload wired? ==="
SHA=$(kubectl -n $NS get configmap $LUA_CM \
      -o jsonpath='{.data.polaris_access_log\.lua}' 2>/dev/null | shasum -a 256 | cut -c1-16)
EMPTY_SHA=$(printf '' | shasum -a 256 | cut -c1-16)
if [ -z "$SHA" ] || [ "$SHA" = "$EMPTY_SHA" ]; then bad "no $LUA_CM ConfigMap / no polaris_access_log.lua key (kubectl apply -k fluent-bit/)"
elif [ "$SHA" = "$LUA_SHA_EXPECT" ]; then ok "ConfigMap lua sha $SHA matches the repo"
else bad "ConfigMap lua sha $SHA != expected $LUA_SHA_EXPECT — deployed script differs from the file"; fi
# The ConfigMap is not the file the process reads. kubelet syncs the mount up to ~1 min later.
POD=$(kubectl -n $NS get pods -l app.kubernetes.io/instance=$DS -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
PSHA=$(kubectl -n $NS exec "$POD" -c fluent-bit -- cat /fluent-bit/polaris-lua/polaris_access_log.lua 2>/dev/null | shasum -a 256 | cut -c1-16)
if [ "$PSHA" = "$LUA_SHA_EXPECT" ]; then ok "file inside pod $POD matches the repo"
elif [ -z "$PSHA" ] || [ "$PSHA" = "$EMPTY_SHA" ]; then huh "could not read the script inside the pod (image may have no cat); skip"
else huh "file inside pod is $PSHA — kubelet may not have synced yet; wait ~60s and re-run"; fi
CONTAINERS=$(kubectl -n $NS get ds/$DS -o jsonpath='{.spec.template.spec.containers[*].name}')
case " $CONTAINERS " in *" reloader "*) ok "reloader sidecar present ($CONTAINERS)";; *) bad "no reloader container ($CONTAINERS) — hotReload not rendered";; esac
ARGS=$(kubectl -n $NS get ds/$DS -o jsonpath='{.spec.template.spec.containers[?(@.name=="fluent-bit")].args}')
case "$ARGS" in *--enable-hot-reload*) ok "--enable-hot-reload on fluent-bit";; *) bad "fluent-bit args lack --enable-hot-reload";; esac
RLOG=$(kubectl -n $NS logs "$POD" -c reloader --tail=50 2>/dev/null)
printf '%s\n' "$RLOG" | grep -iE 'error|fail' | head -5 | sed 's/^/        reloader: /'
printf '%s\n' "$RLOG" | grep -icE 'webhook|reload' | sed 's/^/        reloader lines mentioning reload: /'

echo
echo "=== 4. TIER 1 FIRST — did node-wide collection survive 5.1.1? ==="
OS=(curl -sS -k --max-time 20 -u "${OS_USER}:${OS_PASSWORD}")
cnt(){ "${OS[@]}" "${OS_URL}/$1/_count" -H 'Content-Type: application/json' \
        -d '{"query":{"range":{"@timestamp":{"gte":"now-10m"}}}}' 2>/dev/null \
      | sed -n 's/.*"count":\([0-9]*\).*/\1/p'; }
K=$(cnt 'k8s-logs-*')
if [ -n "$K" ] && [ "$K" -gt 0 ] 2>/dev/null; then ok "k8s-logs: $K docs in the last 10m — tier 1 alive"
else bad "k8s-logs shows ${K:-no answer} in the last 10m — TIER 1 MAY BE DOWN. Stop and read §0.2."; fi

echo
echo "=== 5. The new tiers ==="
for idx in polaris-logs polaris-report; do
  C=$(cnt "${idx}-*")
  if [ -n "$C" ] && [ "$C" -gt 0 ] 2>/dev/null; then ok "${idx}-*: $C docs in the last 10m"
  elif [ "${C:-0}" = "0" ]; then huh "${idx}-*: 0 docs. Ingest is async and the report only emits on a
        WINDOW_SECONDS boundary — wait one window and re-run before concluding anything."
  else bad "${idx}-*: no answer (index missing, or 401 — check \${OS_PASSWORD} expanded)"; fi
done

echo
echo "=== 6. Fluent Bit's own counters (port-forward 2020) ==="
kubectl -n $NS port-forward ds/$DS 2020:2020 >/dev/null 2>&1 &
PF=$!; trap 'kill $PF 2>/dev/null' EXIT; sleep 3
M=$(curl -sS --max-time 10 http://127.0.0.1:2020/api/v1/metrics 2>/dev/null)
if [ -z "$M" ]; then huh "metrics endpoint not reachable; skip"
else
  echo "$M" | python3 -c '
import json,sys
m=json.load(sys.stdin)
for name,v in (m.get("output") or {}).items():
    print(f"        output {name:28s} ok={v.get(\"proc_records\",0):<8} errors={v.get(\"errors\",0):<6} retries_failed={v.get(\"retries_failed\",0)}")
for name,v in (m.get("filter") or {}).items():
    d=v.get("drop_records",0); a=v.get("add_records",0)
    if "polaris" in name: print(f"        filter {name:28s} dropped={d:<8} added={a}")
' 2>/dev/null || echo "        (could not parse metrics)"
  HR=$(curl -sS --max-time 10 http://127.0.0.1:2020/api/v2/reload 2>/dev/null)
  echo "        hot reload counter (GET /api/v2/reload): ${HR:-no answer}   (0 right after a pod start)"
  echo "        NOTE: a per-item OpenSearch rejection inside an HTTP 200 increments NONE of these."
  echo "        That is what Trace_Error On is for — it lands in the pod log, section 2."
fi

echo
if [ "$FAIL" -gt 0 ]; then echo "RESULT: $FAIL check(s) FAILED."; exit 1; fi
cat <<'EOT'
RESULT: post-upgrade checks passed.

NEXT, and NOT covered here:
  * SKIP ONE FULL WINDOW before trusting any report row. The first window after an
    upgrade is a replay, not traffic (#14d). Then check on a report summary row:
        max_record_time - min_record_time  <=  window_seconds
  * THE COMPLETENESS COMPARISON, and it expires. While fb-polaris-shipper is still
    installed you have the same traffic filtered from TWO sources -- the shipper from
    the log FILE into VictoriaLogs, this DaemonSet from STDOUT into OpenSearch.
    Compare `access_seen` for the same window from both reports. Equal means stdout
    carries the same access-log set as the file. After the uninstall that number
    cannot be recovered.
EOT
