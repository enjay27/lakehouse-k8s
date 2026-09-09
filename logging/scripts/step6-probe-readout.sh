#!/usr/bin/env bash
# ============================================================================
# READ-ONLY. Mutates nothing -- no helm, no rollout. Run it after Polaris has
# produced traffic; step5 --apply only needs re-running when the config changes.
#
#   export OS_URL=https://192.168.194.1:9200 OS_USER=admin OS_PASSWORD='...'
#   bash logging/scripts/step6-probe-readout.sh
#
# Probe 5 (hb_tail_probe) cannot be read by a byte DELTA -- nothing follows it on
# its tag. Two independent readings instead:
#   A. its B/rec against polaris_cri_unwrap's, since both tail the SAME FILES.
#      A parsed record is ~10% smaller than the raw envelope carrying it.
#   B. the stored documents: does a heartbeat.tail doc have `loggerName` as a
#      FIELD? That needs no arithmetic and cannot be misread.
# ============================================================================
set -uo pipefail
NS=datahub-hynix; REL=benchmarks-fluent-bit

kubectl -n "$NS" port-forward ds/"$REL" 2021:2020 >/dev/null 2>&1 &
PF=$!; trap 'kill $PF 2>/dev/null' EXIT; sleep 3
m=$(curl -s --max-time 10 localhost:2021/api/v1/metrics) || { echo "no metrics endpoint"; exit 1; }

echo "== filter metrics =="
jq -r '.filter as $f
  | "  hb_parse_probe       \($f.hb_parse_probe.records) rec   \(if $f.hb_parse_probe.records>0 then ($f.hb_parse_probe.bytes/$f.hb_parse_probe.records*10|round/10) else 0 end) B/rec   (130 = parsed)",
    "  hb_parse_nl_probe    \($f.hb_parse_nl_probe.records) rec   \(if $f.hb_parse_nl_probe.records>0 then ($f.hb_parse_nl_probe.bytes/$f.hb_parse_nl_probe.records*10|round/10) else 0 end) B/rec   (133 = parsed)",
    "  hb_parse_real_probe  \($f.hb_parse_real_probe.records) rec   \(if $f.hb_parse_real_probe.records>0 then ($f.hb_parse_real_probe.bytes/$f.hb_parse_real_probe.records*10|round/10) else 0 end) B/rec   (553 = parsed)"' <<<"$m"

echo
echo "== READING A: probe 5 vs the real chain -- same files, same parser, different INPUT =="
jq -r '.filter as $f
  | ($f.hb_tail_probe.records // 0) as $hn | ($f.polaris_cri_unwrap.records // 0) as $pn
  | "  hb_tail_probe       \($hn) rec   \(if $hn>0 then ($f.hb_tail_probe.bytes/$hn*10|round/10) else 0 end) B/rec   [multiline.parser docker, cri]",
    "  polaris_cri_unwrap  \($pn) rec   \(if $pn>0 then ($f.polaris_cri_unwrap.bytes/$pn*10|round/10) else 0 end) B/rec   [multiline.parser cri]",
    (if $hn>0 and $pn>0 then
      "  ratio \(($f.hb_tail_probe.bytes/$hn) / ($f.polaris_cri_unwrap.bytes/$pn) * 1000 | round / 1000)   NO VERDICT -- see below"
     else "  (need traffic on BOTH -- neither has records yet)" end)' <<<"$m"
echo "  This ratio carries NO verdict. It was wrong once already: it read 1.015 while probe 5"
echo "  had in fact parsed every one of 4,314 records. The two inputs emit different envelopes"
echo "  and the samples are different sizes, so the per-record averages were never comparable."
echo "  Judge by READING B below, or by the delta above. Kept only as a sanity display."

echo
echo "== the real chain delta =="
jq -r '.filter as $f | ($f.polaris_key_rename.bytes - $f.polaris_cri_unwrap.bytes) as $d
  | ($f.polaris_cri_unwrap.records) as $n
  | if $n>0 then "  unwrap -> rename = \($d) B over \($n) rec = \($d/$n*100|round/100) B/rec   (12.00 = FAILING, neither rename fires; 5.00-7.00 = working)"
    else "  (no Polaris traffic since the last restart)" end' <<<"$m"

if [ -n "${OS_URL:-}" ] && [ -n "${OS_PASSWORD:-}" ]; then
  echo
  echo "== READING B: the stored documents. Does a heartbeat.tail doc carry loggerName? =="
  curl -sS -k --max-time 20 -u "${OS_USER}:${OS_PASSWORD}" -H 'Content-Type: application/json' \
    "${OS_URL}/fb-heartbeat-*/_search" -d '{"size":0,"aggs":{
      "by_tag":{"terms":{"field":"flb_tag.keyword","size":10},
        "aggs":{"parsed":{"filter":{"exists":{"field":"loggerName"}}},
                "raw":{"filter":{"exists":{"field":"log"}}}}}}}' 2>/dev/null \
  | jq -r '.aggregations.by_tag.buckets[]?
      | "  \(.key): \(.doc_count) docs   loggerName=\(.parsed.doc_count)   log=\(.raw.doc_count)"' \
  || echo "  (no answer)"
  echo "  heartbeat.tail with loggerName>0 and log=0 => probe 5 PARSED. This is the unambiguous read."

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
  echo "  PASS = the newest bucket has loggerName>0 and log=0."
  echo "  Older buckets staying raw is expected and correct: those documents predate the fix"
  echo "  and nothing rewrites them. They age out with the 30d policy."
fi
