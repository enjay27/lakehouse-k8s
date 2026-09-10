#!/usr/bin/env bash
# ============================================================================
# Apply the polaris-report-* index template, and prove it took.
#
# WHY THIS EXISTS. Run 1789026666 (2026-09-10) found `min_record_time` mapped as
# TEXT in polaris-report-2026.09.10. Nothing wrote it wrong: the Lua wrote "" on
# an idle window, OpenSearch dynamic-mapped the field from that first document,
# and dynamic mapping is FOR THE LIFE OF THE INDEX. At 30s windows the first
# window of a day is almost always idle, so this recurs every midnight until a
# template exists. The invariant is still checkable client-side (RFC3339 sorts
# and parses), but no range query and no date histogram works on that index.
#
# ORDER MATTERS. The Lua must OMIT the key when nil first -- it does, since
# 2026-09-10 -- because with `date` mapping a document carrying "" is REJECTED
# PER ITEM inside a _bulk that still returns HTTP 200. Losing summary rows that
# way is worse than the text mapping: since policy v3 a successful read exists
# ONLY as an aggregate in this stream. `ignore_malformed: true` on both fields
# is the belt to that braces -- a surprise value costs the field, not the doc.
# Deliberate, because a silently dropped report is the failure this pipeline
# keeps rediscovering.
#
# NOT RETROACTIVE. Indices already created keep their mappings. This takes
# effect on the next daily index (or on one you reindex yourself).
#
#   export OS_URL=https://192.168.194.1:9200 OS_USER=admin OS_PASSWORD='...'
#   bash logging/scripts/step9-report-index-template.sh
# ============================================================================
set -uo pipefail
: "${OS_URL:?}"; : "${OS_USER:?}"; : "${OS_PASSWORD:?}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TPL="${HERE}/opensearch/polaris-report-template.json"
OS=(curl -sS -k --max-time 30 -u "${OS_USER}:${OS_PASSWORD}" -H 'Content-Type: application/json')

echo "== PUT _index_template/polaris-report =="
"${OS[@]}" -X PUT "${OS_URL}/_index_template/polaris-report" --data-binary "@${TPL}"; echo

echo
echo "== read it back from the cluster, not from the file =="
"${OS[@]}" "${OS_URL}/_index_template/polaris-report?pretty" \
  | grep -E '"index_patterns"|min_record_time|"type"|priority' | head -20

echo
echo "== simulate: what mapping would a NEW polaris-report index get? =="
"${OS[@]}" -X POST "${OS_URL}/_index_template/_simulate_index/polaris-report-9999.12.31?pretty" \
  | grep -A4 -E 'min_record_time|max_record_time'

echo
echo "== the existing indices are UNCHANGED -- this is the fact to expect, not a fault =="
"${OS[@]}" "${OS_URL}/polaris-report-*/_mapping/field/min_record_time?pretty" \
  | grep -E 'polaris-report-|"type"'

echo
echo "PASS looks like: the simulate block says \"type\" : \"date\", and today's index"
echo "still says \"text\". Tomorrow's index is the first one that maps correctly."
