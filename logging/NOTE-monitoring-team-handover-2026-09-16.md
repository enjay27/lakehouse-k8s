# Note for the Monitoring team — Polaris log indices: retention and the signals to alert on

**From:** Polaris log pipeline (local OrbStack rehearsal, repo `local-k8s`), 2026-09-16.
**Why this note:** retention (ISM) for the Polaris indices is yours (decided 2026-09-16). This is what the pipeline assumes and
what it cannot tell anyone about by itself.

> **SUPERSEDED FOR THE LOCAL CLUSTER, 2026-09-18.** Kade took the local OrbStack cluster's retention back into this repo and
> set it much shorter than the figures below: `polaris-logs-*` **3 days**, `polaris-report-*` **30 days**, `k8s-logs-*`
> **3 days**. Policies are in `logging/opensearch/ism-*.json`, applied with `logging/scripts/step13-ism-apply.sh`.
> **Production retention is still yours, and the recommended column below is still what the design asks for** — the local
> figures are a rehearsal-environment choice, not a recommendation to carry over. Section 2 (silent loss) is unaffected.

## 1. Indices

| index | written by | content | recommended retention | why |
|---|---|---|---|---|
| `polaris-logs-YYYY.MM.DD` | Fluent Bit DaemonSet, tier 2 | selected Polaris log lines: every 4xx/5xx except 404, every PUT/DELETE/PATCH, management POST, two allow-listed app loggers, every WARN/ERROR | **30 days** *(local: 3 days)* | incident investigation; large |
| `polaris-report-YYYY.MM.DD` | same pod, tier 3 | one summary row + resource / principal / app_dropped rows per 30-minute window, schema v6 | **365 days** *(local: 30 days)* | the **only** record of successful reads and catalog POSTs (they are counted, not stored); small |
| `k8s-logs-YYYY.MM.DD` | same pod, tier 1 | every container, unfiltered | unchanged (5 days today) *(local: 3 days)* | raw source for cross-checks |

- Daily indices, no rollover: `min_index_age`-based delete fits.
- **Before attaching the 365-day policy: `polaris-report-*` indices written while the window was 30 s are verification data**
  (about 60× the rows per day). The pipeline owner deletes them after the switch to 1800 s; please don't retain them as production.
- Index templates (`polaris-logs`, `polaris-report`, priority 100) are applied by the pipeline owner. Schema v6 string fields are
  queried through `.keyword`.

## 2. Silent loss the pipeline cannot report itself

| what | when | metric (Fluent Bit `/api/v2/metrics/prometheus` on port 2020) | suggested alert |
|---|---|---|---|
| **Buffered chunks dropped** | OpenSearch unreachable long enough that tier 2 exceeds `storage.total_limit_size` 400M (tier 3: 200M). Oldest chunks are discarded. For tier 3 that loses report windows, the only record of counted traffic | `fluentbit_output_dropped_records_total{name=~"opensearch.*"}` · `fluentbit_storage_*` chunk gauges | any increase |
| Retries exhausted | a chunk fails `Retry_Limit` (5 for tier 2/3) | `fluentbit_output_retries_failed_total` | any increase |
| Per-document rejection inside HTTP 200 | mapping conflicts; counted by no metric | pod log lines from `Trace_Error On` (`kubectl logs ds/benchmarks-fluent-bit`) | log-based, if you ingest pod logs elsewhere (Fluent Bit's own log is no longer shipped to `k8s-logs` since 2026-09-16) |
| Reports stopped | Lua failed to load, or the pod is down | no new `polaris-report-*` doc for 30 min (`report_type.keyword: summary`) | absence of data |
| Pipeline restarted | every config or Lua change | summary row with `partial_window: "true"`, `report_seq` restarting at 1 | informational |

## 3. Contacts in the repo
`logging/SPEC-polaris-audit-logging.ko.md` §5.3 (retention), §8 (dashboards); `logging/SCHEMA-report.md` (fields).
