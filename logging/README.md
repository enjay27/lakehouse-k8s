# `logging/` — which document to read (status as of 2026-09-21 — schema v6 live, thread fields restored; Polaris 1.6.0)

Most files here are dated working documents. They stay because the reasoning in them is still cited, but **only the
first table describes the pipeline as it runs**. When a dated document disagrees with it, the first table wins.

## Current

| file | read it for |
|---|---|
| [`HANDOFF-polaris-log-batch-2026-09-28.md`](HANDOFF-polaris-log-batch-2026-09-28.md) | **START HERE for the batch** — what is live, what is written but never built/run, the ordered next steps with commands and pass criteria, the traps |
| [`SPEC-polaris-log-batch.ko.md`](SPEC-polaris-log-batch.ko.md) | **the batch pipeline, in Korean** — part 1 design (per-pod files and why, selection by timestamp, exactly-once per hour, orphans, policy v5, report schema 7 vs v6), part 2 the script's logic function by function (run flow, process_hour, AuditPolicy, publish/housekeep/retention, checkpoint and output formats, errors and exit codes, constants, CLI), part 3 build/deploy and verification |
| [`PLAN-polaris-log-batch-2026-09-27.md`](PLAN-polaris-log-batch-2026-09-27.md) | **the next architecture** — Polaris → PVC (hourly `.gz`) → Python CronJob → processed/aggregated JSONL → Observability team. Step 1 (file logging + PVC) written, not rolled; the SPEC below still describes what runs |
| [`SPEC-polaris-audit-logging.ko.md`](SPEC-polaris-audit-logging.ko.md) | **START HERE** — the specification of the running system (Korean). Policy, schema, indices, retention, deploy procedure, and §11's list of what is known-broken |
| [`HANDOFF-thread-fields-2026-09-18.md`](HANDOFF-thread-fields-2026-09-18.md) | **a completed-task record, not a to-do** — `threadName`/`threadId` were restored, rolled and verified on 2026-09-18 (`#42`). Read it for *why*, and for what the 1.6.0 upgrade changed under the pipeline |
| [`HANDOFF-pipeline-next-2026-09-16.md`](HANDOFF-pipeline-next-2026-09-16.md) | the rules and the ordered step list — **but its state section predates Polaris 1.6.0**; where the two disagree, the 09-18 handoff wins |
| [`SPEC-polaris-audit-logging.ko.md`](SPEC-polaris-audit-logging.ko.md) | **the specification of the running system** (Korean): indices, policy rules 0–7, 404 handling, retention, deploy method, gates, known limits. Renamed 2026-09-21 from `PROPOSAL-polaris-audit-log-retention.ko.md` — it stopped being a proposal when it rolled on 09-16 |
| [`HANDOFF-traffic-notebook-2026-09-21.md`](HANDOFF-traffic-notebook-2026-09-21.md) | **for a session in the polaris-logging project** — how to build the traffic notebook there: the policy branches to exercise, the preflight that proves the requestId chain in ten seconds, the reconciliation and invariants, and the traps (`#24`, `#42`, `#45`, `#46`, `#47`). The notebook is a client of this pipeline and lives in that project, not here |
| [`GUIDE-sample-data-2026-09-21.ko.md`](GUIDE-sample-data-2026-09-21.ko.md) | 신규 엔지니어용 샘플 문서 (Korean): 스키마 v6 의 상세·요약 문서를 유형별로, 요청 추적, DQL 예시. **생성물** — `scripts/step14-sample-doc.py` 가 export 에서 만든다, 손으로 고치지 말 것. 09-16 판은 `archive/` (그 판의 상세 샘플에는 `threadName`/`threadId` 가 없다) |
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

Retention / ISM: **ours for this local cluster since 2026-09-18** — `opensearch/ism-*.json`, applied with `scripts/step13-ism-apply.sh`, live and evaluating (first deletion 2026-09-20 08:42Z). The 2026-09-16 "the Monitoring team owns them" rule still holds **for production**; what they need from us is [`NOTE-monitoring-team-handover-2026-09-16.md`](NOTE-monitoring-team-handover-2026-09-16.md).

## Dated reference — still useful, check against the current set

| file | date | what is still valid | what is not |
|---|---|---|---|
| `GUIDE-schema-v3-testing.md` | 09-16 | gate queries G1–G8, Gate 2 | predates v5 (404 no longer stored) |
| `GUIDE-opensearch-notebook.md` | 09-09 | notebook ↔ OpenSearch workflow | readouts: prefer `scripts/step10` + `step11` |
| `PLAN-tier1-dedup-2026-09-09.md` | 09-09 | the `Id_Key` trap and options A–C for `#18` | decision still open → `REVIEW-pipeline` P2 |
| `PLAN-opensearch-cutover-2026-09-08.md` | 09-08 | why two tails, why separate DBs, credentials | "uninstall `fb-polaris-shipper` after cutover" never recorded as done → `REVIEW-pipeline` P10 |
| `fb-values.yaml` · `victoria-values.yaml` | 09-07 / 08-21 | the shipper's Lua and the four silent faults documented in it | **both releases were uninstalled 2026-09-18** — neither is configuration any more. They stay in `logging/` rather than `archive/` only because ~30 files cite them, most of them session records |

## Historical — finished or superseded

Moved to [`archive/`](archive/README.md) on 2026-09-21, renamed `YYYY-MM-DD-<name>` by creation date.
Seventeen documents: the 09-16 sample-data guide, the v5-rollout and audit-log-next handoffs, the hot-reload runbook, the allowlist and
schema-v2/v3 plans, the three closed-fault plans, the notebook handoffs, the 09-03 architecture spec and
the 09-07 Korean logging guide. [`archive/README.md`](archive/README.md) maps every old path to its new
one and says what superseded it.

## Scripts

| status | files |
|---|---|
| **test** | `step15-shared-file-size-rotation-test.sh` (`run shared` · `run perpod` · `restore` — drives `run_traffic.py --profile full`, no notebook: can N pods share one log file with fast size rotation? every notebook request id must be on exactly one access line across all rolls — #48) |
| **live** | `step14-sample-doc.py` (샘플 문서 생성; 인자 두 개 = 상세·요약 export) · `step2-render-gate.sh` (render gate) · `step3-postupgrade.sh` (post-roll) · `step9-report-index-template.sh` · `step12-logs-index-template.sh` · `step13-ism-apply.sh` (retention; dry run by default, `--apply` to write) · `step10-v4-window-readout.sh` (one window, three sources) · `step11-replay-window.py` (replay; `POLARIS_LUA=` for a candidate) · `test-schema-v3/v4/v5/v6.lua` · `test-first-tick.lua` · `test-raw-access-shim.lua` · `devtools-json-fix.py` |
| **finished / superseded** — **moved to `scripts/attic/` 2026-09-16** (P11; old docs cite the old paths) | `step0-preflight.sh` · `step4-report-readout.sh` · `step5-probe-apply-verify.sh` · `step6-tier2-readout.sh` · `step7-dedup-check.sh` · `step8-subset-proof.sh` · `test-polaris-filters.py` (tests the shipper's Lua) · `report_readout.py` (used by step4) |
| harnesses | `candidates/diff-v5-v6.lua` (v5 vs v6) · `diff-refactor.lua` · `bench-refactor.lua` · `bench-classify.lua` (pre-v6 scripts: they feed `_msg`) · `tier1-to-lua.py` |

The step numbers are the order of old plans, not an order of use.
