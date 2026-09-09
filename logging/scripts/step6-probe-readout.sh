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
      "  ratio \(($f.hb_tail_probe.bytes/$hn) / ($f.polaris_cri_unwrap.bytes/$pn) * 1000 | round / 1000)   <1.0 by ~10% => probe 5 PARSED, the cri multiline parser is the fault"
     else "  (need traffic on BOTH -- neither has records yet)" end)' <<<"$m"

echo
echo "== the real chain delta =="
jq -r '.filter as $f | ($f.polaris_key_rename.bytes - $f.polaris_cri_unwrap.bytes) as $d
  | ($f.polaris_cri_unwrap.records) as $n
  | if $n>0 then "  unwrap -> rename = \($d) B over \($n) rec = \($d/$n*100|round/100) B/rec   (9.00 working / 12.00 failing)"
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
fi
