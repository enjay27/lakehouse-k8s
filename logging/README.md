# `logging/` — which document to read (status as of 2026-09-16, late)

Most files here are dated working documents. They stay because the reasoning in them is still cited, but **only the
first table describes the pipeline as it runs**. When a dated document disagrees with it, the first table wins.

## Current

| file | read it for |
|---|---|
| [`HANDOFF-pipeline-next-2026-09-16.md`](HANDOFF-pipeline-next-2026-09-16.md) | **start here** — state in sixty seconds, rules, ordered next steps |
| [`PROPOSAL-polaris-audit-log-retention.ko.md`](PROPOSAL-polaris-audit-log-retention.ko.md) | the design and its rationale (Korean): indices, policy rules 0–7, 404 handling, deploy method, gates |
| [`SCHEMA-report.md`](SCHEMA-report.md) | every `polaris-report-*` field, per schema version (v5 current) |
| [`REVIEW-pipeline-2026-09-16.md`](REVIEW-pipeline-2026-09-16.md) | end-to-end review of the running flow, P1–P12 with current-vs-proposed; **decisions pending** |
| [`REVIEW-lua-refactor-2026-09-16.md`](REVIEW-lua-refactor-2026-09-16.md) | the Lua refactor (one filter, R1–R6) and how it was proven equivalent — **rolled** |
| [`PLAN-audit-log-todo-2026-09-16.md`](PLAN-audit-log-todo-2026-09-16.md) | the phase 0–3 task table toward production (ISM handed to the Monitoring team) |
| [`opensearch/`](opensearch/) | index templates (`polaris-logs-template.json`, `polaris-report-template.json`) and `devtools-export.console` |
| [`scripts/`](scripts/) | see *Scripts* below |
| `../fluent-bit/values.yaml` · `../fluent-bit/polaris_access_log.lua` · `../fluent-bit/apply-lua.sh` | what is deployed, and how the Lua is rolled |

Not in this repo on purpose: retention / ISM policies — **the Monitoring team owns them** (2026-09-16).

## Dated reference — still useful, check against the current set

| file | date | what is still valid | what is not |
|---|---|---|---|
| `GUIDE-schema-v3-testing.md` | 09-16 | gate queries G1–G8, Gate 2 | predates v5 (404 no longer stored) |
| `GUIDE-opensearch-notebook.md` | 09-09 | notebook ↔ OpenSearch workflow | readouts: prefer `scripts/step10` + `step11` |
| `PLAN-tier1-dedup-2026-09-09.md` | 09-09 | the `Id_Key` trap and options A–C for `#18` | decision still open → `REVIEW-pipeline` P2 |
| `PLAN-opensearch-cutover-2026-09-08.md` | 09-08 | why two tails, why separate DBs, credentials | "uninstall `fb-polaris-shipper` after cutover" never recorded as done → `REVIEW-pipeline` P10 |
| `polaris-logging.drawio` | 09-14 | overall shape | pre-v4: two Lua filters, no allow-list/app_dropped |
| `fb-values.yaml` · `victoria-values.yaml` | 09-07 / 08-21 | the `fb-polaris-shipper` → VictoriaLogs release, if it still runs | not the OpenSearch pipeline |

## Historical — finished or superseded (kept for the reasoning)

| file | superseded by |
|---|---|
| `HANDOFF-audit-log-next-2026-09-16.md`, `HANDOFF-v5-rollout-2026-09-16.md` | `HANDOFF-pipeline-next-2026-09-16.md` |
| `RUNBOOK-lua-hot-reload-2026-09-16.md` | hot reload removed (rev 18); its section D `sequence` query still works |
| `PLAN-audit-allowlist-2026-09-15.md` | policy v4, rolled 09-15, then v5 |
| `PLAN-report-schema-v3-2026-09-09.md`, `PLAN-log-coverage-schema-v2-2026-09-07.md`, `HANDOFF-report-schema-v2-2026-09-07.md`, `HANDOFF-harness-schema-v2-2026-09-07.md` | `SCHEMA-report.md` (v5) |
| `PLAN-bulk-response-buffer-2026-09-09.md`, `PLAN-heartbeat-probe-2026-09-09.md`, `PLAN-tier2-parse-fault-2026-09-09.md` | faults closed (`#19`, the multiline fix) |
| `HANDOFF-notebook-run-2026-09-09.md`, `HANDOFF-notebook-window-attribution-2026-09-15.md`, `HANDOFF-polaris-log-coverage-2026-09-07.md` | step10/step11 readouts; `#26` for window attribution |
| `polaris-logging-architecture-spec.md` | 09-03 design for a PVC → VictoriaLogs shipper; the built pipeline is the proposal's (stdout → OpenSearch) |
| `POLARIS-LOGGING-GUIDE.ko.md` | 09-07 state (VictoriaLogs era); the proposal describes the current one |

## Scripts

| status | files |
|---|---|
| **live** | `step2-render-gate.sh` (render gate) · `step3-postupgrade.sh` (post-roll) · `step9-report-index-template.sh` · `step12-logs-index-template.sh` · `step10-v4-window-readout.sh` (one window, three sources) · `step11-replay-window.py` (replay; `POLARIS_LUA=` for a candidate) · `test-schema-v3/v4/v5.lua` · `test-first-tick.lua` · `test-raw-access-shim.lua` · `devtools-json-fix.py` |
| **finished / superseded** (proposed move to `scripts/attic/`, `REVIEW-pipeline` P11) | `step0-preflight.sh` · `step4-report-readout.sh` · `step5-probe-apply-verify.sh` · `step6-tier2-readout.sh` · `step7-dedup-check.sh` · `step8-subset-proof.sh` · `test-polaris-filters.py` (tests the shipper's Lua) · `report_readout.py` (used by step4) |
| harnesses | `candidates/diff-refactor.lua` · `bench-refactor.lua` · `bench-classify.lua` · `tier1-to-lua.py` |

The step numbers are the order of old plans, not an order of use.
