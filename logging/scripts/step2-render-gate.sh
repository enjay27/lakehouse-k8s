#!/usr/bin/env bash
# ============================================================================
# Step 2 gate for PLAN-opensearch-cutover-2026-09-08.md (v5)
#
# Checks a rendered manifest of `benchmarks-fluent-bit` before any helm upgrade.
#
#   helm upgrade --install benchmarks-fluent-bit fluent/fluent-bit \
#     --version 0.57.6 -n datahub-hynix -f fluent-bit/values.yaml \
#     --dry-run=client > /tmp/render-after.txt
#   bash logging/scripts/step2-render-gate.sh /tmp/render-after.txt
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
#   2. THE ENTIRE LUA SCRIPT RENDERS AS ONE LINE. The ConfigMap emits it as a single
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
[ -r "$R" ] || { echo "FATAL: cannot read $R"; exit 2; }
grep -q 'kind: DaemonSet' "$R" || echo "WARN: no 'kind: DaemonSet' in $R — is this the right render?"

FAIL=0
eq(){ n=$(grep -c -- "$2" "$R"); if [ "$n" = "$3" ]; then printf '  PASS  %-46s %s\n' "$1" "$n";
      else printf '  FAIL  %-46s %s (want %s)\n' "$1" "$n" "$3"; FAIL=$((FAIL+1)); fi; }
ge(){ n=$(grep -c -- "$2" "$R"); if [ "$n" -ge "$3" ]; then printf '  PASS  %-46s %s\n' "$1" "$n";
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
ge "chart renders the luascripts ConfigMap" 'luascripts'              1
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
echo "=== policy v3 / schema v2 arrived intact (guide §4.7, corrected) ==="
ge "RESOURCE_PATTERNS present"              'RESOURCE_PATTERNS'       1
ge "MGMT_PREFIX present"                    'MGMT_PREFIX'             1
eq "type_int_key  (guide says 2; ACTUAL 4)" 'type_int_key'            4
eq "DEDUP_MAX_KEYS (guide says 0; ACTUAL 1, a comment)" 'DEDUP_MAX_KEYS' 1

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
  * that the deployed script matches the file:
      kubectl -n datahub-hynix get configmap benchmarks-fluent-bit-luascripts \
        -o jsonpath='{.data.polaris_access_log\.lua}' | shasum -a 256
      # must equal the shipper's:  aa180e90b9f69bda...
EOT
