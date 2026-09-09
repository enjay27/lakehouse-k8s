#!/usr/bin/env bash
# ============================================================================
# Settle #16 vs #18. They contradict each other and both are currently cited.
#
#   #16 (2026-09-08, reasoned from the config): OUTPUT 1 matches
#       kube.*benchmarks-polaris* and OUTPUT 2 matches kube.*, Fluent Bit routes
#       a record to EVERY matching output, so every Polaris line is in k8s-logs
#       TWICE. It instructs every tier-1 comparison to dedup on `sequence` first
#       and calls a raw count "~2x wrong".
#
#   #18 (2026-09-09, read from the pod log): OUTPUT 1 logs "the value of
#       sequence is not string" then "skipping record with missing or unsafe
#       Id_Key value" continuously, so it indexes NOTHING and only OUTPUT 2 ever
#       stores the record -- one copy, not two.
#
# Both cannot hold. Neither has been measured against the index. #18's "skips the
# record" is a reading of the message text, not a proven drop.
#
# `sequence` is a per-JVM counter that resets on restart, so a long window can
# collide values across restarts and inflate the ratio on its own. 30 minutes.
#
#   export OS_URL=... OS_USER=... OS_PASSWORD='...'
#   bash logging/scripts/step7-dedup-check.sh
# ============================================================================
set -uo pipefail
: "${OS_URL:?}"; : "${OS_USER:?}"; : "${OS_PASSWORD:?}"
OS=(curl -sS -k --max-time 25 -u "${OS_USER}:${OS_PASSWORD}" -H 'Content-Type: application/json')

r=$("${OS[@]}" "${OS_URL}/k8s-logs-*/_search" -d '{"size":0,
  "query":{"bool":{"filter":[{"exists":{"field":"sequence"}},
                             {"range":{"@timestamp":{"gte":"now-30m"}}}]}},
  "track_total_hits":true,
  "aggs":{"distinct_seq":{"cardinality":{"field":"sequence","precision_threshold":40000}},
          "sample":{"terms":{"field":"sequence","size":8,"order":{"_count":"desc"}}}}}' 2>/dev/null)

docs=$(jq -r '.hits.total.value // 0' <<<"$r")
dist=$(jq -r '.aggregations.distinct_seq.value // 0' <<<"$r")

echo "== k8s-logs, last 30m, records carrying \`sequence\` =="
echo "    documents         : $docs"
echo "    distinct sequence : $dist"
if [ "${dist:-0}" -gt 0 ] && [ "${docs:-0}" -gt 0 ]; then
  python3 - "$docs" "$dist" <<'PY'
import sys
d,s=int(sys.argv[1]),int(sys.argv[2]); r=d/s
print(f"    ratio             : {r:.3f}")
print()
if r >= 1.7:
    print("    => ~2 copies per record. #16 IS RIGHT: both outputs index, counts over")
    print("       k8s-logs are ~2x inflated and must be deduped on `sequence`.")
    print("       #18's 'OUTPUT 1 skips the record' reading is WRONG -- it evidently")
    print("       skips only the _id, not the document. Correct #18.")
elif r <= 1.3:
    print("    => ~1 copy per record. #18 IS RIGHT: OUTPUT 1 indexes nothing, so there")
    print("       is no double write. #16's '~2x wrong' warning is VOID, and so is the")
    print("       dedup instruction it puts on PLAN-opensearch-cutover §7. Correct #16")
    print("       BEFORE running the §7 subset proof -- deduping there would halve a")
    print("       count that was never doubled.")
else:
    print("    => between 1.3 and 1.7: neither claim as stated. Most likely the window")
    print("       spans a Polaris restart and `sequence` has wrapped, colliding values")
    print("       from two JVM runs. Narrow to a window with no restart and re-run.")
PY
else
  echo "    (no records with \`sequence\` in the last 30m -- Polaris idle. Drive traffic first.)"
fi

echo
echo "== busiest sequence values (a per-JVM counter: each should appear once, or twice if #16 holds) =="
jq -r '.aggregations.sample.buckets[]? | "    sequence \(.key): \(.doc_count) doc(s)"' <<<"$r" \
  || echo "    (none)"
