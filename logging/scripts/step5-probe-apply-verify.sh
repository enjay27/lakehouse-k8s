#!/usr/bin/env bash
# ============================================================================
# Apply fluent-bit/values.yaml and PROVE the running instance picked it up.
#
# Written 2026-09-09 after losing three cycles to the same trap: `helm upgrade`
# updates the ConfigMap but a DaemonSet does NOT roll on a ConfigMap change, and
# `rollout restart` without a preceding upgrade restarts the OLD config. Either
# half alone looks like success. #20.
#
# The order below is the whole point, and each step is verified before the next:
#   render -> upgrade -> CONFIRM THE CONFIGMAP -> roll -> CONFIRM THE PROCESS
#
#   bash logging/scripts/step5-probe-apply-verify.sh            # dry-run only
#   bash logging/scripts/step5-probe-apply-verify.sh --apply    # do it
# ============================================================================
set -uo pipefail
NS=datahub-hynix
REL=benchmarks-fluent-bit
CHART=fluent/fluent-bit
VER=0.57.6
VALUES=fluent-bit/values.yaml
APPLY=${1:-}

die(){ echo "FAIL: $*" >&2; exit 1; }
step(){ printf '\n\033[1m== %s\033[0m\n' "$*"; }

step "0. cluster-context guard"
ctx=$(kubectl config current-context) || die "no kubectl"
[ "$ctx" = orbstack ] || die "context is '$ctx', expected 'orbstack'. HALT."
echo "    context=$ctx  ns=$NS  release=$REL"

step "1. render gate -- helm lint is not a render (CLAUDE.md DoD 1)"
helm upgrade --install "$REL" "$CHART" --version "$VER" -f "$VALUES" -n "$NS" \
  --dry-run=client >/dev/null 2>&1 || die "render failed. Re-run without >/dev/null to see it."
echo "    render OK"

# What the values file expects the running instance to contain. Add to this list
# whenever a probe is added; a gate that does not name what it checks cannot fail.
EXPECT=(hb_parse_probe hb_parse_nl_probe hb_parse_real_probe hb_tail_probe polaris_cri_unwrap)

if [ "$APPLY" != "--apply" ]; then
  echo
  echo "DRY RUN ONLY. Re-run with --apply to upgrade and roll."
  echo "Would then require these aliases in the ConfigMap and in /api/v1/metrics:"
  printf '    %s\n' "${EXPECT[@]}"
  exit 0
fi

step "2. helm upgrade"
helm upgrade --install "$REL" "$CHART" --version "$VER" -f "$VALUES" -n "$NS" || die "upgrade failed"

step "3. CONFIRM THE CONFIGMAP -- the step that was being skipped"
cm=$(kubectl -n "$NS" get cm "$REL" -o json | jq -r '.data["fluent-bit.conf"]') || die "no configmap"
miss=0
for a in "${EXPECT[@]}"; do
  if grep -q "$a" <<<"$cm"; then echo "    ok      $a"
  else echo "    MISSING $a"; miss=1; fi
done
[ "$miss" -eq 0 ] || die "the ConfigMap does not carry what $VALUES says. Do NOT roll -- the upgrade did not take."

step "4. roll the DaemonSet (a ConfigMap change alone will NOT do this)"
kubectl -n "$NS" rollout restart ds/"$REL"
kubectl -n "$NS" rollout status ds/"$REL" --timeout=180s || die "rollout did not complete"

step "5. CONFIRM THE PROCESS -- the ConfigMap is not the running config"
sleep 40   # let the 30s probes tick at least once
kubectl -n "$NS" port-forward ds/"$REL" 2021:2020 >/dev/null 2>&1 &
PF=$!; trap 'kill $PF 2>/dev/null' EXIT
sleep 3
m=$(curl -s --max-time 10 localhost:2021/api/v1/metrics) || die "no metrics endpoint"
for a in "${EXPECT[@]}"; do
  jq -e --arg a "$a" '.filter[$a]' <<<"$m" >/dev/null 2>&1 \
    && echo "    ok      $a" || { echo "    MISSING $a"; miss=1; }
done
[ "$miss" -eq 0 ] || die "config deployed but the process does not have it."

step "6. the probe readings"
echo "    130 B/rec => PARSED   |   ~153 B/rec => raw (probes 2 and 3)"
echo "    probe 4's payload is ~490 B raw, so its two outcomes are unmistakable"
jq -r '.filter | to_entries[] | select(.key|startswith("hb_"))
       | "    \(.key): \(.value.records) rec  \(.value.bytes) B  = \(if .value.records>0 then (.value.bytes/.value.records|.*10|round/10) else 0 end) B/rec"' <<<"$m"

step "7. the real chain, for comparison in the same process"
jq -r '.filter as $f
       | ($f.polaris_key_rename.bytes - $f.polaris_cri_unwrap.bytes) as $d
       | ($f.polaris_cri_unwrap.records) as $n
       | "    unwrap -> rename delta = \($d) B over \($n) rec = \(if $n>0 then ($d/$n*100|round/100) else 0 end) B/rec",
         "    9.00 = unwrap WORKING   |   12.00 = unwrap FAILING"' <<<"$m"
