#!/usr/bin/env bash
# ============================================================================
# Why is polaris-logs-* empty? The report already answers it.
#
# access_seen counts every access-log line the filter SAW, before any keep/drop
# decision. So:
#     access_seen == 0 -> Polaris had no traffic; an empty polaris-logs-* is the
#                         pipeline working, not failing.
#     access_seen  > 0 -> the filter saw records, and the fault is after it.
#
#     export OS_URL=... OS_USER=... OS_PASSWORD=...
#     export VL_URL=http://192.168.139.2:9428     # optional, for the comparison
#     bash logging/scripts/step4-report-readout.sh
# ============================================================================
set -uo pipefail
: "${OS_URL:?}"; : "${OS_USER:?}"; : "${OS_PASSWORD:?}"
OS=(curl -sS -k --max-time 20 -u "${OS_USER}:${OS_PASSWORD}")
TMP=$(mktemp)
trap 'rm -f "$TMP"' EXIT

echo "=== do the indices exist at all? ==="
echo "    An index ABSENT here has never received a document — which is a different"
echo "    fact from 'no documents in the last 10 minutes'."
"${OS[@]}" "${OS_URL}/_cat/indices/polaris-*?v&h=index,docs.count,store.size" 2>/dev/null \
  | sed 's/^/    /' || echo "    (no answer)"

echo
echo "=== the last summary rows ==="
"${OS[@]}" -H 'Content-Type: application/json' "${OS_URL}/polaris-report-*/_search" \
  -d '{"size":30,"sort":[{"@timestamp":"desc"}]}' > "$TMP" 2>/dev/null
python3 "$(dirname "$0")/report_readout.py" < "$TMP"

if [ -n "${VL_URL:-}" ]; then
  echo
  echo "=== THE COMPARISON THAT EXPIRES — same traffic, two sources ==="
  echo "    Above: STDOUT-sourced (this DaemonSet, into OpenSearch)."
  echo "    Below: FILE-sourced (fb-polaris-shipper, still installed, into VictoriaLogs)."
  echo "    Equal access_seen for one window => stdout carries the same set as the file."
  echo "    This can only be measured while BOTH releases run."
  # `sort` is not decoration. LogsQL returns rows in ARBITRARY order, so the
  # previous `| tail -8` picked 8 of ~60 windows at random and printed them as if
  # they were the most recent 8 -- against the OpenSearch side, which really is
  # sorted desc. At zero traffic the two agreed anyway and the defect was
  # invisible; with traffic it would have compared unrelated windows and called
  # the difference a coverage gap. Sort here, and match rows BY window_start.
  # 30 rows to match the OpenSearch side's size:30 -- at 30s windows that is 15
  # minutes of coverage on both halves. Fewer rows here than there silently
  # shortens the comparable span and can miss the very windows that had traffic.
  curl -sS --max-time 20 "${VL_URL}/select/logsql/query" \
    --data-urlencode 'query=app:polaris-shipper-report report_type:summary | sort by (window_start) desc | limit 30 | fields window_start, access_seen, access_kept' \
    --data-urlencode "start=$(date -u -v-30M +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -d '30 min ago' +%Y-%m-%dT%H:%M:%SZ)" \
    --data-urlencode "end=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --data-urlencode 'limit=0' 2>/dev/null | head -30 | sed 's/^/    /'
  echo "    (empty => the shipper saw no traffic either, which corroborates 'idle')"
fi
