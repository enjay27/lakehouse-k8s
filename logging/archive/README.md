# `logging/archive/` — finished or superseded documents

Every file here was current once and is not any more. Nothing in this directory describes the pipeline
as it runs: for that, read [`../README.md`](../README.md) and the documents its **Current** table lists.
They are kept because the reasoning in them is still cited — a decision's *why* outlives the decision.

**Naming: `YYYY-MM-DD-<original name>`, the date the document was created** (first commit that added it),
not the date it was archived. The old names carried the date at the end, or not at all; the prefix makes
the directory sort chronologically and makes it obvious at a glance how old a claim is.

**Do not edit these to keep them true.** A superseded document that gets quietly corrected stops being a
record of what was believed on its date, which is the only thing it is still good for. If one is wrong in
a way that matters, say so in the table below.

## What moved where — 2026-09-21

Links elsewhere in the repo were updated to these paths, with two deliberate exceptions: the narratives in
`.memory/sessions/` and the comment header of `fluent-bit/polaris_access_log.lua`. Session records describe
the repo as it stood on their date and are not rewritten; the Lua is deployed configuration, and editing a
comment in it changes the ConfigMap sha, which costs a pod restart and a reset of every Lua window counter.
Their old paths resolve through this table.

| old path | now | superseded by / why it is here |
|---|---|---|
| `logging/HANDOFF-audit-log-next-2026-09-16.md` | [`2026-09-16-HANDOFF-audit-log-next.md`](2026-09-16-HANDOFF-audit-log-next.md) | `../HANDOFF-pipeline-next-2026-09-16.md` |
| `logging/HANDOFF-v5-rollout-2026-09-16.md` | [`2026-09-16-HANDOFF-v5-rollout.md`](2026-09-16-HANDOFF-v5-rollout.md) | `../HANDOFF-pipeline-next-2026-09-16.md` |
| `logging/RUNBOOK-lua-hot-reload-2026-09-16.md` | [`2026-09-16-RUNBOOK-lua-hot-reload.md`](2026-09-16-RUNBOOK-lua-hot-reload.md) | hot reload removed at rev 18 — but its §D `sequence` query still works |
| `logging/PLAN-audit-allowlist-2026-09-15.md` | [`2026-09-15-PLAN-audit-allowlist.md`](2026-09-15-PLAN-audit-allowlist.md) | policy v4, rolled 09-15, then v5. Still cited by the Lua's own header |
| `logging/HANDOFF-notebook-window-attribution-2026-09-15.md` | [`2026-09-15-HANDOFF-notebook-window-attribution.md`](2026-09-15-HANDOFF-notebook-window-attribution.md) | `../scripts/step10` + `step11` readouts; `#26` |
| `logging/PLAN-report-schema-v3-2026-09-09.md` | [`2026-09-09-PLAN-report-schema-v3.md`](2026-09-09-PLAN-report-schema-v3.md) | `../SCHEMA-report.md` |
| `logging/PLAN-bulk-response-buffer-2026-09-09.md` | [`2026-09-09-PLAN-bulk-response-buffer.md`](2026-09-09-PLAN-bulk-response-buffer.md) | fault closed (`#19`, the multiline fix) |
| `logging/PLAN-heartbeat-probe-2026-09-09.md` | [`2026-09-09-PLAN-heartbeat-probe.md`](2026-09-09-PLAN-heartbeat-probe.md) | fault closed (`#19`) |
| `logging/PLAN-tier2-parse-fault-2026-09-09.md` | [`2026-09-09-PLAN-tier2-parse-fault.md`](2026-09-09-PLAN-tier2-parse-fault.md) | fault closed (`#19`) |
| `logging/HANDOFF-notebook-run-2026-09-09.md` | [`2026-09-09-HANDOFF-notebook-run.md`](2026-09-09-HANDOFF-notebook-run.md) | `../scripts/step10` + `step11` readouts |
| `logging/PLAN-log-coverage-schema-v2-2026-09-07.md` | [`2026-09-07-PLAN-log-coverage-schema-v2.md`](2026-09-07-PLAN-log-coverage-schema-v2.md) | `../SCHEMA-report.md` |
| `logging/HANDOFF-report-schema-v2-2026-09-07.md` | [`2026-09-07-HANDOFF-report-schema-v2.md`](2026-09-07-HANDOFF-report-schema-v2.md) | `../SCHEMA-report.md` |
| `logging/HANDOFF-harness-schema-v2-2026-09-07.md` | [`2026-09-07-HANDOFF-harness-schema-v2.md`](2026-09-07-HANDOFF-harness-schema-v2.md) | `../SCHEMA-report.md` |
| `logging/HANDOFF-polaris-log-coverage-2026-09-07.md` | [`2026-09-07-HANDOFF-polaris-log-coverage.md`](2026-09-07-HANDOFF-polaris-log-coverage.md) | `../scripts/step10` + `step11` readouts |
| `logging/POLARIS-LOGGING-GUIDE.ko.md` | [`2026-09-07-POLARIS-LOGGING-GUIDE.ko.md`](2026-09-07-POLARIS-LOGGING-GUIDE.ko.md) | describes the VictoriaLogs era (09-07). The current system: `../SPEC-polaris-audit-logging.ko.md` |
| `logging/GUIDE-sample-data.ko.md` | [`2026-09-16-GUIDE-sample-data.ko.md`](2026-09-16-GUIDE-sample-data.ko.md) | [`../GUIDE-sample-data-2026-09-21.ko.md`](../GUIDE-sample-data-2026-09-21.ko.md). **그 판의 상세 샘플에는 `threadName`/`threadId` 가 없다** — 09-18 복원(`#42`) 이전에 손으로 쓴 것이라 09-19 이후 인덱스와 다르다 |
| `logging/polaris-logging-architecture-spec.md` | [`2026-09-03-polaris-logging-architecture-spec.md`](2026-09-03-polaris-logging-architecture-spec.md) | 09-03 design for a PVC → VictoriaLogs shipper. **That leg was removed 2026-09-18** — nothing it describes is running |

## What is NOT here

- **`../fb-values.yaml` and `../victoria-values.yaml`** stayed in `logging/`. Both are values files for releases
  that were uninstalled on 2026-09-18 and both carry a HISTORY banner, but between them they are cited by
  some thirty files, most of them session records that must not be rewritten. They are config history, not
  documents. Move them only together with those citations.
- **Superseded *scripts*** have their own attic: `../scripts/attic/` (2026-09-16).
