#!/usr/bin/env bash
# ============================================================================
# READ-ONLY tier 2 health check. Mutates nothing -- no helm, no rollout.
#
# The five heartbeat probes were removed once they had answered their question
# (root cause: multiline.parser cri alone). What survives is what stays useful:
# the unwrap->rename delta, and the time-split read of polaris-logs-* itself.
#
#   export OS_URL=https://192.168.194.1:9200 OS_USER=admin OS_PASSWORD='...'
#   bash logging/scripts/step6-probe-readout.sh
#
# ============================================================================
set -uo pipefail
NS=datahub-hynix; REL=benchmarks-fluent-bit

kubectl -n "$NS" port-forward ds/"$REL" 2021:2020 >/dev/null 2>&1 &
PF=$!; trap 'kill $PF 2>/dev/null' EXIT; sleep 3
m=$(curl -s --max-time 10 localhost:2021/api/v1/metrics) || { echo "no metrics endpoint"; exit 1; }

echo "== the real chain delta =="
jq -r '.filter as $f | ($f.polaris_key_rename.bytes - $f.polaris_cri_unwrap.bytes) as $d
  | ($f.polaris_cri_unwrap.records) as $n
  | if $n>0 then "  unwrap -> rename = \($d) B over \($n) rec = \($d/$n*100|round/100) B/rec   (12.00 = FAILING, neither rename fires; 5.00-7.00 = working)"
    else "  (no Polaris traffic since the last restart)" end' <<<"$m"

if [ -n "${OS_URL:-}" ] && [ -n "${OS_PASSWORD:-}" ]; then
  echo

  echo
  echo "== READING C: THE ACTUAL GATE -- polaris-logs-* documents, split by time =="
  echo "   Old raw docs sit in the same index and will mask a fix. Split, do not filter."
  curl -sS -k --max-time 20 -u "${OS_USER}:${OS_PASSWORD}" -H 'Content-Type: application/json' \
    "${OS_URL}/polaris-logs-*/_search" -d '{"size":0,"aggs":{
      "when":{"date_range":{"field":"@timestamp","ranges":[
                {"key":"1_older_than_10m","to":"now-10m"},
                {"key":"2_10m_to_5m","from":"now-10m","to":"now-5m"},
                {"key":"3_5m_to_2m","from":"now-5m","to":"now-2m"},
                {"key":"4_last_2m","from":"now-2m"}]},
        "aggs":{"parsed":{"filter":{"exists":{"field":"loggerName"}}},
                "raw":{"filter":{"exists":{"field":"log"}}}}}}}' 2>/dev/null \
  | jq -r '.aggregations.when.buckets[]?
      | "  \(.key): \(.doc_count) docs   loggerName=\(.parsed.doc_count)   log=\(.raw.doc_count)"' \
  || echo "  (no answer)"
  echo
  echo "  Read the LAST bucket only. A roll part-way through a window splits it, so a mixed"
  echo "  bucket is a transition, not a failure -- the buckets exist to show which."
  echo "  PASS = the newest NON-EMPTY bucket has loggerName>0 and log=0."
  echo "  An empty newest bucket just means Polaris was idle in that window."
  echo "  Older buckets staying raw is expected and correct: those documents predate the fix"
  echo "  and nothing rewrites them. They age out with the 30d policy."
fi
