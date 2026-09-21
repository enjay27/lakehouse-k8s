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
# extraVolumes. So the Lua-content checks moved to the second argument (the kustomize
# output), and the helm render is checked for the wiring instead: the volume and the path.
# HOT RELOAD WAS REMOVED THE SAME DAY (rev 17 had it): the render must carry NO reloader and
# NO --enable-hot-reload, and MUST carry checksum/config (so Helm config changes restart).
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
# 3.2 was "Time_Keep On must exist". Since 2026-09-09 the tier-2 parser has NO Time_Key; the one match is the
# comment above polaris_stdout_json that quotes the old setting. Kept as a count so an edit to that block is noticed.
eq "3.2 old Time_Keep quoted once, in a comment" 'Time_Keep   On'        1
eq "3.3 no stale polaris.vlogs tag"         'polaris\.vlogs'          0
eq "3.4 Time_Key only on tier 1's output"   'Time_Key            @timestamp' 1
eq "3.6 credential reaches the outputs"     'OS_PASSWORD'             3
eq "3.7 Trace_Error on both new outputs"    'Trace_Error'             3

echo
echo "=== structure ==="
eq "three opensearch outputs (tier 1, 2, 3)" 'Name  *opensearch'   3
eq "no http output in THIS release"         'Name  *http'             0
eq "one report tick"                        'Name              dummy' 1
eq "two distinct tail DBs"                  'DB  */var/log/flb_'      2
ge "tier 2 index"                           'Logstash_Prefix     polaris-logs'   1
ge "tier 3 index"                           'Logstash_Prefix     polaris-report' 1
ge "filesystem buffering for the new chain" 'storage.path'            1
ge "the new parser exists"                  'polaris_stdout_json'     1
ge "image bumped to 5.1.1"                  'fluent-bit:5.1.1'        1

echo
echo "=== v5 wiring: Lua ConfigMap, read at start -- no hot reload (helm render) ==="
# chart 0.57.6 _pod.tpl / daemonset.yaml: with hotReload off and luaScripts {} the chart renders
# no reloader, no flag, no <release>-luascripts ConfigMap or /fluent-bit/scripts mount, and
# puts checksum/config back on the pod template (checksum/luascripts only if luaScripts is set).
eq "no hot reload flag"                     '--enable-hot-reload'     0
eq "no reloader sidecar"                    'name: reloader'          0
eq "no reloader image"                      'configmap-reload'        0
eq "no -luascripts ConfigMap / volume"      'luascripts'              0
eq "checksum/config on the pod template (config change restarts)" 'checksum/config' 1
eq "volume points at the Lua ConfigMap"     'name: polaris-fluent-bit-lua' 1
eq "Lua mount path in the fluent-bit container" 'mountPath: /fluent-bit/polaris-lua' 1
# R1 (2026-09-16 refactor): the access-line parser is inside polaris_noise_filter -- ONE Lua filter.
eq "one Lua FILTER uses the mounted script" 'script  */fluent-bit/polaris-lua/polaris_access_log\.lua' 1
eq "no FILTER calls the removed parser"     'call  *polaris_access_log' 0
eq "parsed ints lead FILTER 3's int list"   'type_int_key  http_status response_size schema_version' 1
eq "no FILTER left on the old path"         'script  */fluent-bit/scripts/' 0
eq "no Lua in the Helm render (--set-file gone)" 'APP_ALLOW' 0
# 1 = the one real directive (FILTER 3). Until the R1 merge it was 3: FILTER 2's directive plus the
# comment above it. A rendered block-scalar comment COUNTS (2026-09-15: a comment naming it made
# v4's gate read 5). Keep the word out of comments.
eq "type_int_key  (1 directive, no comment)" 'type_int_key'          1
ge "v4 commit fields in type_int_key"       'commit_ms_max dropped'   1
ge "v5 404 fields in type_int_key"          'held_orphans held_pending' 1
eq "carried_rows gone from type_int_key"    'distinct_principals carried_rows' 0

echo
echo "=== v5 Lua ConfigMap (kustomize render: $L) ==="
eq "one ConfigMap"                          '^kind: ConfigMap'        1 "$L"
eq "name, no hash suffix"                   '^  name: polaris-fluent-bit-lua$' 1 "$L"
eq "namespace"                              '^  namespace: datahub-hynix$' 1 "$L"
eq "the data key"                           '^  polaris_access_log.lua: |' 1 "$L"
eq "schema constant (v6)"                        'local SCHEMA_VERSION = 6' 1 "$L"
ge "allow-list present"                     'APP_ALLOW'               1 "$L"
ge "resource patterns present"              'RESOURCE_PATTERNS'       1 "$L"
ge "404 request-id hold present"            'HOLD_MAX_SECONDS'        1 "$L"
eq "WINDOW_SECONDS still 30 (flip to 1800 is TODO 2.5)" 'local WINDOW_SECONDS = 30 ' 1 "$L"
# Byte identity of ConfigMap data vs the file is checked AFTER apply, by step3 (sha).
# Measured 2026-09-16 with kustomize v5.4.3: the rendered data is byte-identical to the file.

echo
echo "=== polaris-logs-* field trim (2026-09-18 decision B: thread fields restored, ndc still removed; tier 2 only) ==="
# INVERTED 2026-09-18 (#42, reverses #30): the two thread fields must NOT be trimmed any more, so the expected
# count is 0. Left as counts rather than deleted, because a silent reappearance of either Remove_key line is
# exactly the regression this gate exists to catch.
eq "threadName NOT trimmed in polaris_field_trim" 'Remove_key    threadName' 0
eq "threadId NOT trimmed in polaris_field_trim"   'Remove_key    threadId'   0
eq "ndc still trimmed in polaris_field_trim"      'Remove_key    ndc$'       1

echo
echo "=== 2026-09-16 pipeline review: P1 P2 P3 P4 P6 (schema v6) ==="
# order(): line number of the first match of $1 must be smaller than that of $2
order(){ a=$(grep -n -m1 -- "$2" "$R" | cut -d: -f1); b=$(grep -n -m1 -- "$3" "$R" | cut -d: -f1)
         if [ -n "$a" ] && [ -n "$b" ] && [ "$a" -lt "$b" ]; then printf '  PASS  %-46s %s < %s\n' "$1" "$a" "$b";
         else printf '  FAIL  %-46s %s / %s\n' "$1" "${a:-none}" "${b:-none}"; FAIL=$((FAIL+1)); fi; }
order "P1 field trim runs BEFORE the Lua"       'Alias         polaris_field_trim' 'Alias         polaris_noise_filter'
order "P1 key rename runs before the trim"      'Alias         polaris_key_rename' 'Alias         polaris_field_trim'
eq "P6 stream trimmed"                          'Remove_key    stream'    1
eq "P6/v6 no message rename, no app added"      'Rename        message\|Add           app' 0
eq "P6 no tag field on tier 2 (only tier 1 has one)" 'Include_Tag_Key' 1
eq "P2 no Id_Key output left"                   '^ *Id_Key ' 0
eq "P3 Fluent Bit's own log excluded"           'Exclude_Path      /var/log/containers/benchmarks-fluent-bit-\*\.log' 1
eq "P4 no tier-1 parser filters / definitions"  'polaris_json\|polaris_text\|datahub_json' 0

echo
echo "=== tier 1 ==="
eq "tier-1 literal still present (#4 follow-up)" 'Str0ngP@ssw0rd123!' 1
eq "k8s-logs prefix (one tier-1 output)"    'Logstash_Prefix     k8s-logs' 1
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
  * that the pod was RESTARTED after the ConfigMap last changed. Fluent Bit reads the Lua
    only at start; step3 compares the container start time with the ConfigMap's last change.
    A Lua-only change goes through fluent-bit/apply-lua.sh (apply + restart in one step).
  * ORDER: `kubectl apply -k fluent-bit/` BEFORE `helm upgrade`. A pod whose volume names a
    ConfigMap that does not exist stays in ContainerCreating.
EOT
