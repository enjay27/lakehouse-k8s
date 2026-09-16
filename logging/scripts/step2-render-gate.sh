#!/usr/bin/env bash
# ============================================================================
# Step 2 gate for PLAN-opensearch-cutover-2026-09-08.md (v5); policy v5 wiring since 2026-09-16
#
# Checks a rendered manifest of `benchmarks-fluent-bit` before any helm upgrade.
#
#   kubectl kustomize fluent-bit/ > /tmp/render-lua.txt          # the Lua ConfigMap (v5+)
#   helm upgrade --install benchmarks-fluent-bit fluent/fluent-bit \
#     --version 0.57.6 -n datahub-hynix -f fluent-bit/values.yaml \
#     --dry-run=client > /tmp/render-after.txt                     # NO --set-file since v5
#   bash logging/scripts/step2-render-gate.sh /tmp/render-after.txt /tmp/render-lua.txt
#
# SINCE POLICY v5 (2026-09-16) THE LUA IS NOT IN THE HELM RENDER. It ships as its own
# ConfigMap `polaris-fluent-bit-lua` (fluent-bit/kustomization.yaml), mounted through
# extraVolumes and watched by the chart's hot-reload sidecar. So the Lua-content checks
# moved to the second argument (the kustomize output), and the helm render is checked
# for the wiring instead: the volume, the mount path, the reloader, --enable-hot-reload.
#
# RENDER WITHOUT --debug. --debug prints USER-SUPPLIED and COMPUTED VALUES before
# the manifest, so every config string appears three times and every count below
# triples.
#
# TWO THINGS MAKE RENDER COUNTS != VALUES-FILE COUNTS. Both bit the first version
# of this script, and both are the reason its numbers were corrected on 2026-09-09:
#
#   1. Top-level YAML comments DO NOT RENDER. Only text inside a `key: |` block
#      scalar reaches the ConfigMap. A comment in the values file is invisible here.
#
#   2. (v4 and earlier, when the Lua was a Helm value) THE ENTIRE LUA SCRIPT RENDERED AS ONE LINE. The ConfigMap emits it as a single
#      escaped scalar, so `grep -c` over anything inside those 560 lines returns 1,
#      never the real number. That is why RESOURCE_PATTERNS, MGMT_PREFIX and
#      DEDUP_MAX_KEYS are presence checks here and not counts -- and why the Lua's
#      real integrity is checked by SHA against the deployed ConfigMap, below, not
#      by grep. Use `grep -o PATTERN file | wc -l` if you ever need a true count.
#
# Every expectation here was MEASURED against a real render, not assumed.
# Two of the guide's §4.7 numbers are wrong and fire on a correct config
# (type_int_key, DEDUP_MAX_KEYS) -- the corrected values are used below.
# ============================================================================
set -uo pipefail
R="${1:-/tmp/render-after.txt}"
L="${2:-/tmp/render-lua.txt}"
[ -r "$R" ] || { echo "FATAL: cannot read $R"; exit 2; }
[ -r "$L" ] || { echo "FATAL: cannot read $L (kubectl kustomize fluent-bit/ > $L)"; exit 2; }
grep -q 'kind: DaemonSet' "$R" || echo "WARN: no 'kind: DaemonSet' in $R — is this the right render?"

FAIL=0
eq(){ n=$(grep -c -- "$2" "${4:-$R}"); if [ "$n" = "$3" ]; then printf '  PASS  %-46s %s\n' "$1" "$n";
      else printf '  FAIL  %-46s %s (want %s)\n' "$1" "$n" "$3"; FAIL=$((FAIL+1)); fi; }
ge(){ n=$(grep -c -- "$2" "${4:-$R}"); if [ "$n" -ge "$3" ]; then printf '  PASS  %-46s %s\n' "$1" "$n";
      else printf '  FAIL  %-46s %s (want >=%s)\n' "$1" "$n" "$3"; FAIL=$((FAIL+1)); fi; }

echo "=== the five silent traps ==="
eq "3.1 both Parsers_File lines"            'Parsers_File'            2
eq "3.2 Time_Keep On (or _time never exists)" 'Time_Keep   On'        1
eq "3.3 no stale polaris.vlogs tag"         'polaris\.vlogs'          0
eq "3.4 Time_Key only on tier 1's outputs"  'Time_Key            @timestamp' 2
eq "3.6 credential reaches the outputs"     'OS_PASSWORD'             3
eq "3.7 Trace_Error on both new outputs"    'Trace_Error'             3

echo
echo "=== structure ==="
eq "four opensearch outputs (2 tier-1 + 2 new)" 'Name  *opensearch'   4
eq "no http output in THIS release"         'Name  *http'             0
eq "one report tick"                        'Name              dummy' 1
eq "two distinct tail DBs"                  'DB  */var/log/flb_'      2
ge "tier 2 index"                           'Logstash_Prefix     polaris-logs'   1
ge "tier 3 index"                           'Logstash_Prefix     polaris-report' 1
ge "filesystem buffering for the new chain" 'storage.path'            1
ge "the new parser exists"                  'polaris_stdout_json'     1
ge "image bumped to 5.1.1"                  'fluent-bit:5.1.1'        1

echo
echo "=== v5 wiring: Lua ConfigMap + hot reload (helm render) ==="
# The chart still renders an EMPTY <release>-luascripts ConfigMap and mounts it at
# /fluent-bit/scripts whenever hotReload is on. Harmless: nothing points a script there.
eq "hot reload flag on fluent-bit"          '--enable-hot-reload'     1
eq "reloader sidecar"                       'name: reloader'          1
ge "reloader image"                         'configmap-reload'        1
eq "reloader watches the Lua volume"        '-volume-dir=/watch/extra-0' 1
eq "volume points at the Lua ConfigMap"     'name: polaris-fluent-bit-lua' 1
eq "Lua mount path in the fluent-bit container" 'mountPath: /fluent-bit/polaris-lua' 1
eq "both FILTERs use the mounted script"    'script  */fluent-bit/polaris-lua/polaris_access_log\.lua' 2
eq "no FILTER left on the old path"         'script  */fluent-bit/scripts/' 0
eq "no checksum annotation (hot reload, not restart)" 'checksum/config' 0
eq "no Lua in the Helm render (--set-file gone)" 'APP_ALLOW' 0
# 3 = 2 real directives + 1 comment in the filters block. A rendered block-scalar comment
# COUNTS (2026-09-15: a comment naming it made v4's gate read 5). Keep the word out of comments.
eq "type_int_key  (2 directives + 1 comment)" 'type_int_key'          3
ge "v4 commit fields in type_int_key"       'commit_ms_max dropped'   1
ge "v5 404 fields in type_int_key"          'held_orphans held_pending' 1
eq "carried_rows gone from type_int_key"    'distinct_principals carried_rows' 0

echo
echo "=== v5 Lua ConfigMap (kustomize render: $L) ==="
eq "one ConfigMap"                          '^kind: ConfigMap'        1 "$L"
eq "name, no hash suffix"                   '^  name: polaris-fluent-bit-lua$' 1 "$L"
eq "namespace"                              '^  namespace: datahub-hynix$' 1 "$L"
eq "the data key"                           '^  polaris_access_log.lua: |' 1 "$L"
eq "schema constant"                        'local SCHEMA_VERSION = 5' 1 "$L"
ge "allow-list present"                     'APP_ALLOW'               1 "$L"
ge "resource patterns present"              'RESOURCE_PATTERNS'       1 "$L"
ge "404 request-id hold present"            'HOLD_MAX_SECONDS'        1 "$L"
eq "WINDOW_SECONDS still 30 (flip to 1800 is TODO 2.5)" 'local WINDOW_SECONDS = 30 ' 1 "$L"
# Byte identity of ConfigMap data vs the file is checked AFTER apply, by step3 (sha).
# Measured 2026-09-16 with kustomize v5.4.3: the rendered data is byte-identical to the file.

echo
echo "=== tier 1 untouched ==="
eq "tier-1 literals still present (#4 follow-up)" 'Str0ngP@ssw0rd123!' 2
eq "k8s-logs prefix unchanged"              'Logstash_Prefix     k8s-logs' 2
eq "tier-1 tail path unchanged"             'Path              /var/log/containers/\*\.log' 1

echo
if [ "$FAIL" -gt 0 ]; then
  echo "RESULT: $FAIL check(s) FAILED — do not upgrade."
  exit 1
fi
cat <<'EOT'
RESULT: all render checks passed.

STILL NOT PROVEN BY ANY OF THIS, and each has bitten this pipeline before:
  * that the Lua actually LOADS. A rejected type_int_key or a Lua syntax error shows
    up in the POD LOG, and a disabled filter looks like success from outside (#13).
    After upgrading:  kubectl -n datahub-hynix logs ds/benchmarks-fluent-bit | head -60
  * that ${OS_PASSWORD} expands. An undefined var becomes the empty string and
    OpenSearch answers 401 silently. Trace_Error On is what surfaces it.
  * that tier 1 still works on Fluent Bit 5.1.1. That is the one change reaching
    node-wide collection: confirm k8s-logs is still receiving after the rollout.
  * that the deployed script matches the file: step3 compares the sha of ConfigMap
    polaris-fluent-bit-lua against fluent-bit/polaris_access_log.lua.
  * that a hot reload leaves the engine running. Invalid-script behaviour on reload is
    UNMEASURED on 5.1.1: logging/RUNBOOK-lua-hot-reload-2026-09-16.md, section C.
  * ORDER: `kubectl apply -k fluent-bit/` BEFORE `helm upgrade`. A pod whose volume names a
    ConfigMap that does not exist stays in ContainerCreating.
EOT
