# Building the OpenSearch coverage notebook

**For whoever writes the replacement for `polaris-learning/log-coverage`.** That notebook reads
VictoriaLogs through `fb-polaris-shipper`. Once the shipper is uninstalled its data source stops
existing, and the same measurements have to come from OpenSearch instead.

Source of truth for the pipeline's design and its LogsQL originals:
[`archive/2026-09-07-POLARIS-LOGGING-GUIDE.ko.md`](archive/2026-09-07-POLARIS-LOGGING-GUIDE.ko.md) §7 and §8. **This document is the
port, not a replacement** — every trap in that guide's §7.4 still applies, and OpenSearch adds
several of its own.

---

## 1. What changes, and what deliberately does not

**Only the query language changes.** The pipeline keeps `_msg` and `_time` as field names on
purpose (`fluent-bit/values.yaml`, filter 1) precisely so the port is a query-layer job and not a
re-learning of the schema. Field names, `report_type` values and the schema-v2 semantics are all
identical to what the LogsQL notebook used.

| | before | after |
|---|---|---|
| logs | VictoriaLogs `app:polaris` | OpenSearch `polaris-logs-*` |
| reports | VictoriaLogs `app:polaris-shipper-report` | OpenSearch `polaris-report-*` |
| unfiltered | — | `k8s-logs-*` (tier 1, node-wide) |
| query | LogsQL pipes | `_search` DSL |
| source | the log **file** on the PVC | Polaris **stdout** |

**Stdout and the file were measured equivalent on 2026-09-09**: `access_seen` 265 == 265 and
`access_kept` 126 == 126 over one burst on matched windows. That is why this port is safe. It was
measurable only while both releases ran, and it cannot be repeated once the shipper is gone.

## 2. Connecting

```python
import requests, urllib3, json
urllib3.disable_warnings()
OS = "https://192.168.194.1:9200"          # Docker, outside the cluster
AUTH = ("admin", os.environ["OS_PASSWORD"])  # never hardcode -- see active-issues #4

def q(index, body):
    r = requests.post(f"{OS}/{index}/_search", json=body, auth=AUTH, verify=False, timeout=30)
    r.raise_for_status()
    return r.json()
```

No port-forward is needed — OpenSearch is not in the cluster. **Fluent Bit metrics still are**, so
keep the existing `kubectl port-forward ds/benchmarks-fluent-bit 2020:2020` cell; note it is now
`ds/benchmarks-fluent-bit`, **not** `deploy/fb-polaris-shipper`, and the drop counters it returns
now describe the DaemonSet.

## 3. LogsQL → OpenSearch

| LogsQL | OpenSearch |
|---|---|
| `app:polaris` | index `polaris-logs-*` (the whole index is that stream) |
| `report_type:summary` | `{"match":{"report_type":"summary"}}` — **filter server-side, §5.1** |
| `errors_5xx:>0` | `{"range":{"errors_5xx":{"gt":0}}}` |
| `\| stats count() as n` | `hits.total.value` with `"track_total_hits": true` |
| `\| stats by (f) count()` | `{"aggs":{"by_f":{"terms":{"field":"f.keyword","size":N}}}}` |
| `\| stats sum(x) as s` | `{"aggs":{"s":{"sum":{"field":"x"}}}}` — **pair with `value_count`, §5.3** |
| `\| stats min(x), max(x)` | `min` / `max` aggs |
| `\| sort by (n) desc` | `"order":{"_count":"desc"}` inside the terms agg |
| time range | `{"range":{"@timestamp":{"gte":"now-10m"}}}` |

`.keyword` is required for aggregating any **text**-mapped field (`loggerName`, `api_path`,
`user_principal_name`, `hostname`, `report_type`). Numeric fields aggregate directly. Check with
`GET polaris-report-*/_mapping` rather than guessing — a terms agg on a text field without
`.keyword` fails loudly, which is the good case; the bad case is aggregating an analysed field and
getting tokens.

## 4. The report schema — unchanged from v2

Three `report_type` values share one `report_seq`, one `hostname` and one `window_start`:

- **`summary`** — one row per window. `access_seen` / `access_kept` / `access_counted`,
  `errors_4xx` / `errors_5xx` / `auth_denied`, `parse_errors`, `carried_rows`, `windows_skipped`,
  `distinct_resources`, `distinct_principals`, `window_seconds`, `schema_version`.
- **`resource`** — per table path: `requests`, `reads`, `writes`, `errors`, `response_bytes`.
- **`principal`** — per principal, same measures.

**`access_seen` counts what the filter SAW, before any keep/drop.** That property is what made the
stdout-vs-file measurement possible and it is the single most useful field in the schema.

**`_time` is the END of the window.** A row with `window_start 05:59:00` carries `_time 05:59:30`.
All three types share it, so grouping by `_time` groups one window.

## 5. Traps — the six from §7.4 still apply, and OpenSearch adds four

### 5.1 A `size` without a filter shrinks under load — this one bit on 2026-09-09

`step4-report-readout.sh` fetched `{"size":30, "sort":[{"@timestamp":"desc"}]}` and filtered to
summaries **client-side**. `resource` and `principal` rows only exist *when there was traffic*, so
the busier the window, the more of the 30 slots they took and the shorter the summary coverage got.
**The instrument's window contracted in proportion to the thing it was measuring**, and it read
perfectly during every idle test.

**Always filter `report_type` in the query, never after it.**

### 5.2 `track_total_hits` defaults to 10,000

`hits.total.value` silently caps and reports `"relation": "gte"`. Any count taken from it above
10,000 is wrong. Set `"track_total_hits": true`, and check `relation == "eq"`.

### 5.3 `sum` returns `0.0` where LogsQL returned `NaN` — and 0.0 looks like an answer

LogsQL's `NaN` at least announced that a field was absent. OpenSearch returns a clean `0.0`, which
is indistinguishable from a real zero. **Pair every `sum` with a `value_count` on the same field**;
if the count is 0 the sum is meaningless. This is §7.4's "absence is not zero", made worse.

### 5.4 Terms aggs truncate silently

`"size"` defaults to 10. Larger requests still truncate at the cap you set, and
`sum_other_doc_count` in the response tells you it happened — read it. `step8-subset-proof.sh`
refuses to give a verdict when its cap is hit rather than comparing two truncated sets.

### 5.5 Old documents share the index with new ones

`polaris-logs-*` holds ~29,800 documents written before the 2026-09-09 parse fix, with a raw `log`
field and no `loggerName`. **Split by time into buckets rather than filtering to a window** — a
single window straddling a change reads as "mixed" and cannot tell a transition from a partial
failure. See reading C in `step6-tier2-readout.sh`.

### 5.6 Still true from §7.4

1. Take conclusions from `curl`/`requests`, not a UI.
2. **Every count needs a denominator.** A 500-count of 25 became 6 once the range was matched.
3. `report_seq` is **per pod** — always filter `hostname`, or two pod generations invent a gap.
4. Filter `schema_version:2` — v1 rows are still in the stream and silently reduce v2 sums.
5. Absence is not zero (see 5.3).
6. `_time` is the window's end, and records aggregate into the window they **arrived** in.

## 6. The health checklist, ported

```python
# report continuity -- the strongest single statement. hi - lo + 1 == n
q("polaris-report-*", {"size":0, "track_total_hits":True,
  "query":{"bool":{"filter":[
      {"match":{"report_type":"summary"}},
      {"term":{"schema_version":2}},
      {"match":{"hostname":"<current pod>"}}]}},
  "aggs":{"lo":{"min":{"field":"report_seq"}},
          "hi":{"max":{"field":"report_seq"}},
          "n":{"value_count":{"field":"report_seq"}}}})
```

| check | expect |
|---|---|
| continuity | `hi - lo + 1 == n`, no gaps, no duplicates |
| margin equality | `sum(resource.requests) == sum(principal.requests) == access_seen - parse_errors` |
| carry accounting | rows with `requests:0` == `carried_rows` |
| startup blind spot | `report_seq:1` has `partial_window: true` |
| parser health | `access_log_parse_error:true` -> 0 |
| **tier 2 parse health (new)** | every doc in a recent window has `loggerName`, none has `log` |
| **transport (new)** | pod log free of `cannot increase buffer` / `cannot be retried` |

The last two did not exist in the LogsQL era. Both were live faults on 2026-09-09
(`active-issues` #21, #19) that every existing gate passed while they were broken.

## 7. What the notebook should NOT re-derive

- **Retention policy governs audit fidelity, not disk.** Access-log lines are ~2.2-2.4% of Polaris's
  output; `DatasourceOperations` DEBUG is ~59-60%. Tuning policy rules to save space is tuning the
  wrong 2.4%.
- **Successful namespace creation leaves no individual record** — rule 5 counts it. Its count lives
  only in the report's `writes`. A `stats by (http_status)` on that path returns *only errors, at
  any range*.
- **No `%D`** — no request duration is recorded anywhere. Client-side timing is the only source.
- Polaris 500s are a **create-path** NullPointerException, not a background fault (`#15`).

## 8. Before writing a single query

Run `logging/scripts/step6-tier2-readout.sh`. If the newest bucket is not fully parsed, the index
you are about to measure is not carrying the fields you are about to ask for, and every result will
be a confident zero.
