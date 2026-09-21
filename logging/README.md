# `logging/` — which document to read (status as of 2026-09-18 — schema v6 live; Polaris now 1.6.0)

Most files here are dated working documents. They stay because the reasoning in them is still cited, but **only the
first table describes the pipeline as it runs**. When a dated document disagrees with it, the first table wins.

## Current

| file | read it for |
|---|---|
| [`HANDOFF-thread-fields-2026-09-18.md`](HANDOFF-thread-fields-2026-09-18.md) | **START HERE** — the next task (restore `threadName`/`threadId`), what the 1.6.0 upgrade changed under the pipeline, and every open item |
| [`HANDOFF-pipeline-next-2026-09-16.md`](HANDOFF-pipeline-next-2026-09-16.md) | the rules and the ordered step list — **but its state section predates Polaris 1.6.0**; where the two disagree, the 09-18 handoff wins |
| [`SPEC-polaris-audit-logging.ko.md`](SPEC-polaris-audit-logging.ko.md) | **the specification of the running system** (Korean): indices, policy rules 0–7, 404 handling, retention, deploy method, gates, known limits. Renamed 2026-09-21 from `PROPOSAL-polaris-audit-log-retention.ko.md` — it stopped being a proposal when it rolled on 09-16 |
| [`GUIDE-sample-data.ko.md`](GUIDE-sample-data.ko.md) | 신규 엔지니어용 샘플 문서 (Korean): 스키마 v6 의 상세·요약 문서를 유형별로, 요청 추적, DQL 예시 |
| [`polaris-logging.drawio`](polaris-logging.drawio) | pipeline diagram (Korean): three inputs, the tier-2/3 filter chain, two Polaris indices + `k8s-logs` — v6, 2026-09-16 |
| [`NOTE-monitoring-team-handover-2026-09-16.md`](NOTE-monitoring-team-handover-2026-09-16.md) | what the Monitoring team needs: retention values, verification indices, silent-loss metrics |
| [`SCHEMA-report.md`](SCHEMA-report.md) | every `polaris-report-*` field, per schema version (**v6 current**) |
| [`REVIEW-pipeline-2026-09-16.md`](REVIEW-pipeline-2026-09-16.md) | end-to-end review, P1–P12 with before/after — **decided and rolled as schema v6** (P5 open, P10 manual) |
| [`REVIEW-lua-refactor-2026-09-16.md`](REVIEW-lua-refactor-2026-09-16.md) | the Lua refactor (one filter, R1–R6) and how it was proven equivalent — **rolled** |
| [`PLAN-audit-log-todo-2026-09-16.md`](PLAN-audit-log-todo-2026-09-16.md) | the phase 0–3 task table toward production (ISM handed to the Monitoring team) |
| [`opensearch/`](opensearch/) | index templates (`polaris-logs-template.json`, `polaris-report-template.json`), **ISM retention policies** (`ism-polaris-logs-3d.json`, `ism-polaris-report-30d.json`, `ism-k8s-logs-3d.json` — 2026-09-18, applied with `scripts/step13-ism-apply.sh`) and `devtools-export.console` |
| [`RUNBOOK-log-pvc-removal-2026-09-18.md`](RUNBOOK-log-pvc-removal-2026-09-18.md) | **EXECUTED 2026-09-18** — removed `polaris-shared-logs-pvc`, `fb-polaris-shipper` and VictoriaLogs. A record now, not a to-do |
| `fb-values.yaml`, `victoria-values.yaml` | **HISTORY as of 2026-09-18** — values for releases that no longer exist. Kept for the shipper's Lua and the four silent faults documented in it; do not read either as live configuration |
| [`scripts/`](scripts/) | see *Scripts* below |
| `../fluent-bit/values.yaml` · `../fluent-bit/polaris_access_log.lua` · `../fluent-bit/apply-lua.sh` | what is deployed, and how the Lua is rolled |

Not in this repo on purpose: retention / ISM policies — **the Monitoring team owns them** (2026-09-16). What they need from us: [`NOTE-monitoring-team-handover-2026-09-16.md`](NOTE-monitoring-team-handover-2026-09-16.md).

## Dated reference — still useful, check against the current set

| file | date | what is still valid | what is not |
|---|---|---|---|
| `GUIDE-schema-v3-testing.md` | 09-16 | gate queries G1–G8, Gate 2 | predates v5 (404 no longer stored) |
| `GUIDE-opensearch-notebook.md` | 09-09 | notebook ↔ OpenSearch workflow | readouts: prefer `scripts/step10` + `step11` |
| `PLAN-tier1-dedup-2026-09-09.md` | 09-09 | the `Id_Key` trap and options A–C for `#18` | decision still open → `REVIEW-pipeline` P2 |
| `PLAN-opensearch-cutover-2026-09-08.md` | 09-08 | why two tails, why separate DBs, credentials | "uninstall `fb-polaris-shipper` after cutover" never recorded as done → `REVIEW-pipeline` P10 |
| `fb-values.yaml` · `victoria-values.yaml` | 09-07 / 08-21 | the `fb-polaris-shipper` → VictoriaLogs release, if it still runs | not the OpenSearch pipeline |

## Historical — finished or superseded

Moved to [`archive/`](archive/README.md) on 2026-09-21, renamed `YYYY-MM-DD-<name>` by creation date.
Sixteen documents: the v5-rollout and audit-log-next handoffs, the hot-reload runbook, the allowlist and
schema-v2/v3 plans, the three closed-fault plans, the notebook handoffs, the 09-03 architecture spec and
the 09-07 Korean logging guide. [`archive/README.md`](archive/README.md) maps every old path to its new
one and says what superseded it.

## Scripts

| status | files |
|---|---|
| **live** | `step2-render-gate.sh` (render gate) · `step3-postupgrade.sh` (post-roll) · `step9-report-index-template.sh` · `step12-logs-index-template.sh` · `step13-ism-apply.sh` (retention; dry run by default, `--apply` to write) · `step10-v4-window-readout.sh` (one window, three sources) · `step11-replay-window.py` (replay; `POLARIS_LUA=` for a candidate) · `test-schema-v3/v4/v5/v6.lua` · `test-first-tick.lua` · `test-raw-access-shim.lua` · `devtools-json-fix.py` |
| **finished / superseded** — **moved to `scripts/attic/` 2026-09-16** (P11; old docs cite the old paths) | `step0-preflight.sh` · `step4-report-readout.sh` · `step5-probe-apply-verify.sh` · `step6-tier2-readout.sh` · `step7-dedup-check.sh` · `step8-subset-proof.sh` · `test-polaris-filters.py` (tests the shipper's Lua) · `report_readout.py` (used by step4) |
| harnesses | `candidates/diff-v5-v6.lua` (v5 vs v6) · `diff-refactor.lua` · `bench-refactor.lua` · `bench-classify.lua` (pre-v6 scripts: they feed `_msg`) · `tier1-to-lua.py` |

The step numbers are the order of old plans, not an order of use.
