# `logging/` — the Polaris audit-log domain (status 2026-09-29)

Two pipelines, one of them replacing the other:

| pipeline | state |
|---|---|
| **Fluent Bit Lua** — DaemonSet `benchmarks-fluent-bit` tails Polaris stdout → OpenSearch `k8s-logs-*` / `polaris-logs-*` / `polaris-report-*` (schema v6) | **live** — configuration in `../releases/fluent-bit/` |
| **Batch** — Polaris writes one JSON file per pod to PVC `polaris-logs-pvc`, rolled hourly (KST); CronJob `polaris-log-batch` processes each closed hour | file logging **live**; batch **written and tested, never built or run on the cluster** |

Documents deleted in the 2026-09-29 cleanup are listed in
[`../docs/DELETED-2026-09-29.md`](../docs/DELETED-2026-09-29.md), with the command that recovers each one.

## Read

| file | for |
|---|---|
| [`HANDOFF-polaris-log-batch-2026-09-28.md`](HANDOFF-polaris-log-batch-2026-09-28.md) | **start here for the batch** — what is live, what is written but never built, the ordered next steps with pass criteria |
| [`SPEC-polaris-log-batch.ko.md`](SPEC-polaris-log-batch.ko.md) | the batch's logic, function by function (Korean) |
| [`PLAN-polaris-log-batch-2026-09-27.md`](PLAN-polaris-log-batch-2026-09-27.md) | the batch's decision log — why per-pod files, selection by timestamp, orphans |
| [`SPEC-polaris-audit-logging.ko.md`](SPEC-polaris-audit-logging.ko.md) | **start here for the Lua pipeline** — the running system (Korean): policy, schema, indices, retention, deploy, §11 known limits |
| [`HANDOFF-pipeline-next-2026-09-16.md`](HANDOFF-pipeline-next-2026-09-16.md) | the Lua pipeline's remaining steps: `WINDOW_SECONDS` 30 → **3600** (decided 2026-09-21, not rolled), then deleting the 30 s report indices. Its state section predates Polaris 1.6.0 |
| [`SCHEMA-report.md`](SCHEMA-report.md) | every `polaris-report-*` field, per schema version (v6 current) |
| [`NOTE-monitoring-team-handover-2026-09-16.md`](NOTE-monitoring-team-handover-2026-09-16.md) | what the Monitoring team needs for production: retention values, verification indices, silent-loss metrics |
| [`HANDOFF-traffic-notebook-2026-09-21.md`](HANDOFF-traffic-notebook-2026-09-21.md) | building the traffic notebook that ends in OpenSearch (`diagnostics/ladders/log-coverage/polaris_api_traffic_v1.ipynb`) |
| [`GUIDE-sample-data-2026-09-21.ko.md`](GUIDE-sample-data-2026-09-21.ko.md) | sample v6 documents for new engineers (Korean). **Generated** by `scripts/step14-sample-doc.py` — do not hand-edit |
| [`polaris-logging.drawio`](polaris-logging.drawio) | pipeline diagram (Korean), v6 |

## Configuration

| path | what |
|---|---|
| `../releases/fluent-bit/values.yaml` · `polaris_access_log.lua` · `kustomization.yaml` | the live Fluent Bit release and its Lua |
| `../releases/fluent-bit/apply-lua.sh` | **the only way to roll a Lua change** — tests, diff, apply, restart. `kubectl apply -k` alone leaves the old script running; there is no hot reload |
| `k8s/polaris-logs-pvc.yaml` | the log PVC — `kubectl apply` it **before** `helm upgrade` of Polaris (the chart uses `existingClaim`) |
| `opensearch/` | index templates, ISM retention policies (ours on this cluster since 2026-09-18; production retention belongs to the Monitoring team) |
| `../charts/polaris-log-batch/` · `../images/polaris-log-batch/` | the batch's chart and image — a separate release from Polaris |

## Scripts (`scripts/`)

The step numbers are the order of old plans, not an order of use.

| script | does |
|---|---|
| `test-schema-v3.lua` … `test-schema-v6.lua`, `test-first-tick.lua`, `test-raw-access-shim.lua` | unit tests of the **live** Lua; `apply-lua.sh` runs them. By hand: `cp releases/fluent-bit/polaris_access_log.lua /tmp/polaris.lua && luajit logging/scripts/test-schema-v6.lua` |
| `step2-render-gate.sh` | render gate for a Fluent Bit values change |
| `step3-postupgrade.sh` | post-roll checks: pod log, deployed-Lua sha vs repo, tier 1–3 arrival (needs `OS_USER`/`OS_PASSWORD`) |
| `step9-report-index-template.sh` · `step12-logs-index-template.sh` | apply the OpenSearch index templates |
| `step13-ism-apply.sh` | apply ISM retention (dry run by default, `--apply` to write) |
| `step10-v4-window-readout.sh` · `step11-replay-window.py` | read one report window from three sources; replay it through the Lua (`POLARIS_LUA=` for a candidate) |
| `step14-sample-doc.py` | generates the sample-data guide from two exports |
| `step15-shared-file-size-rotation-test.sh` | the `#48` measurement: can N pods share one log file? (answer: no — 44.5 % lost) |
| `step16-batch-lua-parity.py` | batch vs Lua parity on the same input |
| `devtools-json-fix.py` | repairs OpenSearch Dev Tools exports |
