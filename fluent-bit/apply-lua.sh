#!/usr/bin/env bash
# ============================================================================
# Roll a change to fluent-bit/polaris_access_log.lua -- the ONLY supported way.
#
#     bash fluent-bit/apply-lua.sh            # from anywhere inside the repo
#     bash fluent-bit/apply-lua.sh --restart  # restart even if the ConfigMap is unchanged
#
# Since 2026-09-16 there is no hot reload: Fluent Bit reads its Lua ONCE, at start.
# The script lives in ConfigMap polaris-fluent-bit-lua (fluent-bit/kustomization.yaml),
# which Helm does not own, so a Lua change never restarts the pod by itself.
# `kubectl apply -k` without a restart leaves the OLD script running with no warning --
# #13 / #20's failure mode. This script makes apply and restart one step.
#
# Order and why:
#   1. context guard           -- -n datahub-hynix does not protect against another cluster
#   2. LuaJIT tests v3..v5     -- a broken script fails filter init at start, every input
#                                 pauses, and TIER 1 STOPS with it (2026-09-15). Not skippable.
#   3. kubectl diff -k         -- shows what changes; nothing changed -> nothing to do
#   4. kubectl apply -k
#   5. rollout restart + status
#   6. pod log: filter init errors in the new pod
#
# A change that ALSO touches fluent-bit/values.yaml (e.g. type_int_key for a new field):
# run this script's steps 1-4 (`--no-restart`), then the Helm upgrade -- Helm's
# checksum/config annotation restarts the pod and it reads the new ConfigMap.
# Rollback: check out the previous polaris_access_log.lua and run this script again.
# ============================================================================
set -uo pipefail
NS=datahub-hynix; DS=benchmarks-fluent-bit; CM=polaris-fluent-bit-lua
FORCE=0; NORESTART=0
for a in "$@"; do case "$a" in --restart) FORCE=1;; --no-restart) NORESTART=1;;
  *) echo "usage: $0 [--restart|--no-restart]"; exit 2;; esac; done
cd "$(git rev-parse --show-toplevel 2>/dev/null || echo "$(dirname "$0")/..")" || exit 2
[ -r fluent-bit/polaris_access_log.lua ] || { echo "FATAL: run inside the local-k8s repo"; exit 2; }

echo "== 1. context"
CTX=$(kubectl config current-context 2>/dev/null)
[ "$CTX" = "orbstack" ] || { echo "FATAL: context is '$CTX', not orbstack -- halting"; exit 2; }
echo "   orbstack"

echo "== 2. Lua tests (LuaJIT, the engine Fluent Bit embeds)"
command -v luajit >/dev/null || { echo "FATAL: luajit not on PATH (brew install luajit)"; exit 2; }
cp fluent-bit/polaris_access_log.lua /tmp/polaris.lua
for t in v3 v4 v5; do
  if luajit "logging/scripts/test-schema-$t.lua" > "/tmp/apply-lua-test-$t.txt" 2>&1 \
     && grep -q '^ALL PASS' "/tmp/apply-lua-test-$t.txt"; then echo "   $t ALL PASS"
  else echo "FATAL: test-schema-$t failed -- NOT applied:"; tail -15 "/tmp/apply-lua-test-$t.txt"; exit 1; fi
done

echo "== 3. diff against the cluster"
kubectl -n $NS diff -k fluent-bit/ > /tmp/apply-lua-diff.txt 2>&1; DRC=$?
if [ $DRC -gt 1 ]; then echo "FATAL: kubectl diff failed:"; tail -10 /tmp/apply-lua-diff.txt; exit 2; fi
if [ $DRC -eq 0 ] && [ $FORCE -eq 0 ]; then
  CMT=$(kubectl -n $NS get cm $CM -o jsonpath='{range .metadata.managedFields[*]}{.time}{"\n"}{end}' | sort | tail -1)
  STT=$(kubectl -n $NS get pods -l app.kubernetes.io/instance=$DS \
        -o jsonpath='{.items[0].status.containerStatuses[?(@.name=="fluent-bit")].state.running.startedAt}')
  if [[ -n "$STT" && ! "$STT" < "$CMT" ]]; then
    echo "   ConfigMap unchanged and the pod started ($STT) after its last change ($CMT) -- nothing to do."
    exit 0
  fi
  echo "   ConfigMap unchanged, but the pod started ($STT) BEFORE its last change ($CMT): restarting."
else
  grep -E '^[-+][^-+]' /tmp/apply-lua-diff.txt | grep -vE '^[-+] *(resourceVersion|generation|uid|creationTimestamp):' | head -20 | sed 's/^/   /'
  echo "== 4. apply"
  kubectl -n $NS apply -k fluent-bit/ || { echo "FATAL: apply failed"; exit 1; }
fi
if [ $NORESTART -eq 1 ]; then
  echo "   --no-restart: the pod still runs the OLD script until helm upgrade / rollout restart."; exit 0
fi

echo "== 5. restart (Lua state resets: next report window is partial, report_seq restarts at 1)"
kubectl -n $NS rollout restart ds/$DS || exit 1
kubectl -n $NS rollout status ds/$DS --timeout=180s || { echo "FAIL: rollout not complete -- see Rollback in the header"; exit 1; }

echo "== 6. new pod's log"
sleep 5
LOG=$(kubectl -n $NS logs ds/$DS -c fluent-bit --since=3m 2>/dev/null)
BAD=$(printf '%s\n' "$LOG" | grep -iE 'cannot access script|filter initialization failed|\[error\].*lua|lua.*error' | head -10)
if [ -n "$BAD" ]; then echo "FAIL: Lua did not load -- tier 1 may be stopped. Roll back NOW:"; printf '   %s\n' "$BAD"; exit 1; fi
CS=$(kubectl -n $NS get cm $CM -o jsonpath='{.data.polaris_access_log\.lua}' | shasum -a 256 | cut -c1-16)
RS=$(shasum -a 256 fluent-bit/polaris_access_log.lua | cut -c1-16)
echo "   no Lua load errors."
if [ "$CS" = "$RS" ]; then echo "   ConfigMap sha $CS == repo"; else echo "FAIL: ConfigMap sha $CS != repo $RS (uncommitted edit after apply?)"; exit 1; fi
echo "   next: bash logging/scripts/step3-postupgrade.sh"
