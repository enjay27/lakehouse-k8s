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

# The difference is not merely "expected" -- it is PREDICTED. Policy v3 keeps every
# NON-access-log record, so the only records tier 1 can hold and tier 2 lack are
# access-log lines the policy COUNTED instead of storing. That number is reported by
# the pipeline itself as `access_counted`, so the gap is checkable rather than assumed.
rep=$("${OS[@]}" "${OS_URL}/polaris-report-*/_search" -d "{\"size\":0,
  \"query\":{\"bool\":{\"filter\":[{\"match\":{\"report_type\":\"summary\"}},
                                   {\"range\":{\"@timestamp\":{\"gte\":\"now-${MINS}m\"}}}]}},
  \"aggs\":{\"counted\":{\"sum\":{\"field\":\"access_counted\"}},
            \"n\":{\"value_count\":{\"field\":\"access_counted\"}},
            \"seen\":{\"sum\":{\"field\":\"access_seen\"}}}}" 2>/dev/null)

python3 - "$t1" "$t2" "$MINS" "$CAP" "$rep" <<'PY'
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
    # Account for the gap rather than calling it expected.
    try:
        a = json.loads(sys.argv[5])["aggregations"]
        counted, nrows = int(a["counted"]["value"]), int(a["n"]["value"])
    except Exception:
        counted, nrows = None, 0
    print()
    if not nrows:
        print("  Gap unaccounted: no summary rows in this window, so `access_counted` could not")
        print("  be read. The 'expected' above is an assumption, not a measurement.")
    else:
        d = len(extra)
        print(f"  ACCOUNTING FOR THE GAP: policy v3 keeps every NON-access-log record, so the")
        print(f"  only records tier 1 can hold and tier 2 lack are access-log lines the policy")
        print(f"  COUNTED instead of storing.")
        print(f"    tier1-only records : {d}")
        print(f"    access_counted     : {counted}   (summed over {nrows} summary rows)")
        if counted and abs(d - counted) <= max(3, 0.05 * counted):
            print(f"  => accounted for. The gap IS the counted-only traffic, not loss.")
        else:
            print(f"  => NOT accounted for: {d - counted:+d} unexplained. The report window and the")
            print(f"     log window do not align exactly, so a small residue is normal -- a large")
            print(f"     one is not. Re-run over a window that fully contains one traffic burst")
            print(f"     before treating this as a fault.")
else:
    print(f"  FAIL: {len(missing)} sequence value(s) exist in tier 2 and not in tier 1.")
    print(f"        sample: {sorted(missing)[:10]}")
    print("        Both tails read the same files, so this is not a Polaris question --")
    print("        suspect tier 1's OUTPUT path first (#18: OUTPUT 1 indexes nothing, so")
    print("        every tier 1 document depends on OUTPUT 2 alone), or a dropped chunk (#19).")
PY
