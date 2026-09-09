#!/usr/bin/env bash
# ============================================================================
# Is tier 2 a SUBSET of tier 1? Both source the same Polaris stdout; tier 2 is
# tier 1 put through policy v3. So every `sequence` in polaris-logs-* must also
# be in k8s-logs. A sequence in tier 2 and not in tier 1 means the two tails
# disagree about what Polaris wrote.
#
# This became answerable only on 2026-09-09: before the multiline.parser fix
# tier 2 stored raw CRI envelopes with no `sequence` field to compare on.
#
# NO DEDUP IS APPLIED, deliberately. #16 said tier-1 counts are ~2x inflated and
# must be deduped on `sequence` first; that was measured FALSE (ratio 1.000,
# step7). Deduping here would halve a count that was never doubled.
#
#   export OS_URL=... OS_USER=... OS_PASSWORD='...'
#   bash logging/scripts/step8-subset-proof.sh [minutes]   # default 10
#
# Run it AFTER traffic and BEFORE the 1800/30 revert -- nothing here depends on
# the window length, but the revert is the plan's last step and this is not it.
# ============================================================================
set -uo pipefail
: "${OS_URL:?}"; : "${OS_USER:?}"; : "${OS_PASSWORD:?}"
MINS=${1:-10}
CAP=10000
OS=(curl -sS -k --max-time 40 -u "${OS_USER}:${OS_PASSWORD}" -H 'Content-Type: application/json')

seqs () {  # $1 = index pattern
  "${OS[@]}" "${OS_URL}/$1/_search" -d "{\"size\":0,
    \"query\":{\"bool\":{\"filter\":[{\"exists\":{\"field\":\"sequence\"}},
                                     {\"range\":{\"@timestamp\":{\"gte\":\"now-${MINS}m\"}}}]}},
    \"aggs\":{\"s\":{\"terms\":{\"field\":\"sequence\",\"size\":${CAP}}}}}" 2>/dev/null
}
t1=$(seqs 'k8s-logs-*'); t2=$(seqs 'polaris-logs-*')

python3 - "$t1" "$t2" "$MINS" "$CAP" <<'PY'
import json, sys
t1, t2, mins, cap = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
def load(raw, name):
    try:
        b = json.loads(raw)["aggregations"]["s"]["buckets"]
    except Exception as e:
        print(f"  could not read {name}: {e}"); sys.exit(2)
    return {x["key"] for x in b}, len(b)
A, na = load(t1, "k8s-logs (tier 1)")
B, nb = load(t2, "polaris-logs (tier 2)")

print(f"== last {mins}m, matched on `sequence` ==")
print(f"  tier 1  k8s-logs-*      distinct sequence: {len(A)}")
print(f"  tier 2  polaris-logs-*  distinct sequence: {len(B)}")
if na >= cap or nb >= cap:
    print(f"\n  !! bucket cap of {cap} reached -- the sets are TRUNCATED and any verdict below is")
    print( "     meaningless. Re-run over a shorter window.")
    sys.exit(1)
if not B:
    print("\n  tier 2 has no records in this window. Drive traffic and re-run.")
    sys.exit(1)

missing = B - A
extra   = A - B
print(f"\n  in tier 2 but NOT tier 1 : {len(missing)}")
print(f"  in tier 1 but not tier 2 : {len(extra)}   (expected -- policy v3 drops, and tier 1 is unfiltered)")
print()
if not missing:
    print("  PASS: tier 2 is a strict subset of tier 1. Every record tier 2 stored,")
    print("        tier 1 also saw. The two tails agree about what Polaris wrote.")
else:
    print(f"  FAIL: {len(missing)} sequence value(s) exist in tier 2 and not in tier 1.")
    print(f"        sample: {sorted(missing)[:10]}")
    print("        Both tails read the same files, so this is not a Polaris question --")
    print("        suspect tier 1's OUTPUT path first (#18: OUTPUT 1 indexes nothing, so")
    print("        every tier 1 document depends on OUTPUT 2 alone), or a dropped chunk (#19).")
PY
