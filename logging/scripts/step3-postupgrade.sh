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
# polaris-fluent-bit-lua (`bash releases/fluent-bit/apply-lua.sh`), not through Helm/--set-file.
# kustomize v5.4.3 was measured to store the bytes verbatim, so the ConfigMap must hash identically.
# (v4 as committed dfbbe21: f364c89653dfe481. v3 was the shipper's aa180e90b9f69bda.)
LUA_CM=polaris-fluent-bit-lua
LUA_FILE=releases/fluent-bit/polaris_access_log.lua
[ -r "$LUA_FILE" ] || { echo "FATAL: run from the repo root ($LUA_FILE not found)"; exit 2; }
LUA_SHA_EXPECT=$(shasum -a 256 "$LUA_FILE" | cut -c1-16)
FAIL=0
ok(){ printf '  PASS  %s\n' "$*"; }
bad(){ printf '  FAIL  %s\n' "$*"; FAIL=$((FAIL+1)); }
huh(){ printf '  ????  %s\n' "$*"; }

[ "$(kubectl config current-context)" = "orbstack" ] || { echo "FATAL: context is not orbstack"; exit 2; }

echo "=== 1. Is the pod up, and on the right image? ==="
kubectl -n $NS rollout status ds/$DS --timeout=60s >/dev/null 2>&1 && ok "rollout complete" || bad "rollout NOT complete"
# Select by name: rev 17 had a reloader sidecar and [*] then listed its image too (never ends in :5.1.1).
IMG=$(kubectl -n $NS get ds/$DS -o jsonpath='{.spec.template.spec.containers[?(@.name=="fluent-bit")].image}')
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
echo "=== 3. Is the DEPLOYED script the one in the repo -- and has the process LOADED it? ==="
SHA=$(kubectl -n $NS get configmap $LUA_CM \
      -o jsonpath='{.data.polaris_access_log\.lua}' 2>/dev/null | shasum -a 256 | cut -c1-16)
EMPTY_SHA=$(printf '' | shasum -a 256 | cut -c1-16)
if [ -z "$SHA" ] || [ "$SHA" = "$EMPTY_SHA" ]; then bad "no $LUA_CM ConfigMap / no polaris_access_log.lua key (kubectl apply -k releases/fluent-bit/)"
elif [ "$SHA" = "$LUA_SHA_EXPECT" ]; then ok "ConfigMap lua sha $SHA matches the repo"
else bad "ConfigMap lua sha $SHA != expected $LUA_SHA_EXPECT — deployed script differs from the file"; fi
# No hot reload since 2026-09-16: Fluent Bit reads the Lua ONCE, at container start. The mounted file is
# refreshed by kubelet without a restart, so the file inside the pod says nothing about what runs (and the
# distroless image has no `cat` anyway). The fact that matters is ordering: the fluent-bit container must
# have STARTED AFTER the ConfigMap's last change. Otherwise `kubectl apply -k` ran without a restart (#13/#20).
POD=$(kubectl -n $NS get pods -l app.kubernetes.io/instance=$DS -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
CM_T=$(kubectl -n $NS get configmap $LUA_CM -o jsonpath='{range .metadata.managedFields[*]}{.time}{"\n"}{end}' 2>/dev/null | sort | tail -1)
START_T=$(kubectl -n $NS get pod "$POD" -o jsonpath='{.status.containerStatuses[?(@.name=="fluent-bit")].state.running.startedAt}' 2>/dev/null)
if [ -z "$CM_T" ] || [ -z "$START_T" ]; then huh "could not read ConfigMap change time ($CM_T) or container start ($START_T)"
elif [[ ! "$START_T" < "$CM_T" ]]; then ok "fluent-bit started $START_T, after the ConfigMap's last change $CM_T -- it runs this script"
else bad "fluent-bit started $START_T, BEFORE the ConfigMap changed at $CM_T -- the OLD script is running: bash releases/fluent-bit/apply-lua.sh --restart"; fi
CONTAINERS=$(kubectl -n $NS get ds/$DS -o jsonpath='{.spec.template.spec.containers[*].name}')
[ "$CONTAINERS" = "fluent-bit" ] && ok "one container: fluent-bit (no reloader)" || bad "containers are '$CONTAINERS' -- expected only fluent-bit (hot reload removed)"
ARGS=$(kubectl -n $NS get ds/$DS -o jsonpath='{.spec.template.spec.containers[?(@.name=="fluent-bit")].args}')
case "$ARGS" in *--enable-hot-reload*) bad "fluent-bit still has --enable-hot-reload";; *) ok "no --enable-hot-reload";; esac

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

# 2026-09-16: fields that must NOT be on docs written after this pod started. Older docs in the same daily index still
# carry them, so only the time filter makes this a check. ndc (#42; #30's thread fields were RESTORED 2026-09-18 and
# are asserted PRESENT further down), P1/P6 + schema v6 (_msg renamed to message,
# app / stream / flb_tag constants gone), P7 (report envelope without app / level, sentence only on summary rows).
count_since(){ "${OS[@]}" "${OS_URL}/$1/_count" -H 'Content-Type: application/json' \
    -d "{\"query\":{\"bool\":{\"filter\":[{\"range\":{\"@timestamp\":{\"gt\":\"${START_T}\"}}}$2]}}}" 2>/dev/null \
    | sed -n 's/.*"count":\([0-9]*\).*/\1/p'; }
none_since(){ N=$(count_since "$1" "$2")
    if [ "$N" = "0" ]; then ok "$1: 0 docs $3 since pod start"
    elif [ -z "$N" ]; then huh "$1: could not count docs $3"
    else bad "$1: $N docs $3 since pod start -- $4"; fi; }
if [ -n "${START_T:-}" ]; then
  for f in ndc processName stream flb_tag app _msg; do
    none_since "polaris-logs-*" ",{\"exists\":{\"field\":\"$f\"}}" "with $f" "the tier-2 trim / v6 rename is not in effect"
  done
  M=$(count_since "polaris-logs-*" ",{\"exists\":{\"field\":\"message\"}}")
  if [ -n "$M" ] && [ "$M" -gt 0 ] 2>/dev/null; then ok "polaris-logs-*: $M docs carry message since pod start"
  else huh "polaris-logs-*: ${M:-no answer} docs with message since pod start -- run traffic, then re-run"; fi
  # 2026-09-18 (#42, reverses #30): the thread fields are shipped again and must now be PRESENT on new docs.
  # threadName is an UNDECLARED string under the v6 template -- text with index:false plus a .keyword sub-field --
  # so exists MUST name threadName.keyword; the bare field finds nothing and would fail this check for the wrong
  # reason. threadId is mapped long (template properties), so the bare field is the right one for it.
  #
  # SELF-ARMING (#43, 2026-09-18): huh() does NOT increment FAIL, so a plain "0 docs -> huh" presence check is
  # compatible with RESULT: passed even when the fields are genuinely gone -- which is a gate that passes for the
  # wrong reason, the same class of bug as querying bare threadName. $M (docs carrying `message`) is the arming
  # signal: if documents ARE being written since pod start and these fields are absent from them, that is a real
  # FAIL, not a "run traffic and re-try". Only when no document has been written at all is 0 uninformative.
  for f in threadName.keyword threadId; do
    N=$(count_since "polaris-logs-*" ",{\"exists\":{\"field\":\"$f\"}}")
    if [ -n "$N" ] && [ "$N" -gt 0 ] 2>/dev/null; then ok "polaris-logs-*: $N docs carry $f since pod start"
    elif [ -n "$M" ] && [ "$M" -gt 0 ] 2>/dev/null; then
      bad "polaris-logs-*: ${N:-no answer} docs with $f since pod start, but $M carry message -- docs ARE being written without it, so the tier-2 trim is still removing it (#42)"
    else
      huh "polaris-logs-*: ${N:-no answer} docs with $f since pod start -- nothing written yet (message: ${M:-0}), run traffic, then re-run (#42)"; fi
  done
  for f in app level _msg; do
    none_since "polaris-report-*" ",{\"exists\":{\"field\":\"$f\"}}" "with $f" "the Lua is not schema v6"
  done
  none_since "polaris-report-*" ",{\"exists\":{\"field\":\"message\"}}],\"must_not\":[{\"term\":{\"report_type.keyword\":\"summary\"}}" \
    "that are rows carrying message" "the Lua is not schema v6"
  none_since "k8s-logs-*" ",{\"wildcard\":{\"kubernetes.pod_name.keyword\":\"benchmarks-fluent-bit-*\"}}" \
    "from Fluent Bit's own pod (P3 Exclude_Path)" "Exclude_Path is not in effect"
else huh "no container start time -- skipped the field checks"; fi

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
# No backslashes inside f-string braces: a SyntaxError before Python 3.12 (macOS ships 3.9), which is
# why this printed "could not parse metrics" on every run until 2026-09-16.
for name,v in (m.get("output") or {}).items():
    ok_=v.get("proc_records",0); er=v.get("errors",0); rf=v.get("retries_failed",0)
    print(f"        output {name:28s} ok={ok_:<8} errors={er:<6} retries_failed={rf}")
for name,v in (m.get("filter") or {}).items():
    d=v.get("drop_records",0); a=v.get("add_records",0)
    if "polaris" in name: print(f"        filter {name:28s} dropped={d:<8} added={a}")
' 2>/dev/null || echo "        (could not parse metrics)"
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
  * THE COMPLETENESS COMPARISON HAS EXPIRED -- 2026-09-18. It said: while
    fb-polaris-shipper is installed you have the same traffic from TWO sources (the
    shipper from the log FILE into VictoriaLogs, this DaemonSet from STDOUT into
    OpenSearch), so comparing `access_seen` for one window proves stdout carries the
    same access-log set as the file. The shipper, VictoriaLogs and the log PVC are all
    gone, so that number can no longer be obtained. IT WAS NEVER TAKEN. Nothing now
    independently corroborates that stdout == file for the access log; tier 1
    (`k8s-logs-*`) remains the only cross-check, and it reads the same stdout.
EOT
