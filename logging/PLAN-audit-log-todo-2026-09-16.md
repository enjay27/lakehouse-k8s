# TODO — Polaris audit log, from `PROPOSAL-polaris-audit-log-retention.ko.md` to production

> **Update 2026-09-16 (late): phase 2 rolled except 2.5/2.7.** 2.6 done (v5, rev 17), hot reload removed (rev 18), thread/ndc trim
> (rev 19, `#30`), Lua refactor with one Lua filter rolled and verified (`#31`). **2.8 / 2.9 (ISM) are no longer ours — the Monitoring
> team writes and applies retention (Kade).** Whole-pipeline review with pending decisions: `REVIEW-pipeline-2026-09-16.md`.
> Current order of work: `HANDOFF-pipeline-next-2026-09-16.md` §3.

**Status: Phase 0 DONE 2026-09-16 — all checks PASS** ([`.memory/sessions/2026-09-16-v4-phase0-matrix-window.md`](../.memory/sessions/2026-09-16-v4-phase0-matrix-window.md)). **1.5 DONE 2026-09-16** — run `1789535345`: one table row at `probe_ns%1Fnested/…/mx_1789535345_deep` with requests 3 and commit_count 2, no dotted phantom; replay 67×30 PASS. **Phases 0 and 1 complete.**
**Update 2026-09-16 (later): 2.6 ROLLED and verified as rev 17; hot reload then REMOVED by decision — Lua changes are `bash fluent-bit/apply-lua.sh` (apply + restart), runbook B/C dropped; the removal is written, not rolled. (`active-issues #28`)** Original status: **Phase 2 bundle WRITTEN 2026-09-16, not rolled** — 2.1 decided (404 counted only, app lines dropped by `mdc.requestId`), 2.2 decided (Lua ConfigMap + chart hot reload, no `--set-file`), 2.3 and 2.4 implemented, tests pass. Next: 2.6 roll + `RUNBOOK-lua-hot-reload-2026-09-16.md` B/C/D; 2.5 (1800s) deliberately **not** in this bundle — step11 verification of v5 needs 30 s windows.
**1.1 DONE 2026-09-16** — step9 PASS: stored 37/37, simulated 37/37, all six v4 integers `long`.
**1.2 WRITTEN 2026-09-16** — `logging/opensearch/polaris-logs-template.json` + `logging/scripts/step12-logs-index-template.sh` (8 fields; strings left dynamic). **1.3 DONE 2026-09-16** — step12 PASS 8/8 stored and simulated. Existing indices 09.09–09.15 already mapped every declared field the same way, so the template is insurance, not a correction. No `polaris-logs-2026.09.16` yet: tier 1 holds 0 Polaris records today and the last detail doc is the test run's end (09-15 09:20:12Z) — Polaris idle, not a stall.

**Was: PLAN, nothing started.** Written 2026-09-16 from the proposal (`8331ce7`), its §10.1 steps and
§11 open items, plus what the 2026-09-15 reviews left owed. Every item names **who** (K = Kade: cluster,
exports, decisions · C = Claude: files, tests, reviews), **depends on**, and **done when** — a done-when
that can read 0 hits is not a pass.

Scope: local OrbStack first (phases 0–2), then the production port (phase 3). v4 is already rolled
(`active-issues #27`); nothing here changes Polaris.

---

## Phase 0 — finish verifying v4 as it runs now (no config change)

| # | Task | Who | Depends on | Done when |
|---|---|---|---|---|
| 0.1 | Export the **matrix window** report (`seq` 5 of run `1789463971`, or a fresh run) **with `commit_count`, `commit_ms_*`, `logger_name`, `dropped`, `access_seen`, `parse_errors`, `role_keys_forced` as columns** | K | — | CSV holds summary + resource + principal + app_dropped rows for a window with 4xx/403/500 traffic |
| 0.2 | Review 0.1 against the detail export: gates **G1, G3, G4, G5, G7, G8** + the per-window invariants (proposal §10.2) | C | 0.1 | every gate PASS or a finding filed in `active-issues` |
| 0.3 | **G2 / G6** — compare `sum(app_dropped.dropped)` and `sum(commit_count)` against the unfiltered `k8s-logs` copy over ≥10 whole windows | K export · C review | 0.1 | equal within boundary lines |
| 0.4 | **Gate 2 (`last_write_bytes`) against `k8s-logs`** — last 2xx `POST …/tables/probe_tbl` in the named window, `response_size` vs the row. Fix `GUIDE-schema-v3-testing.md` Gate 2 query 2 to search `k8s-logs-*` (successful catalog POST is never in `polaris-logs-*`) | K query · C guide fix | — | sizes equal on ≥1 table row; guide updated and committed |
| 0.5 | Confirm the **mapping** of v4 fields in today's `polaris-report-*` (`GET polaris-report-*/_mapping/field/commit_*,dropped,app_dropped_total`) | K | — | all `long` (dynamic) — or recorded as `float`/`text` → forces 1.1 before more data |

## Phase 1 — index hygiene on the local cluster

| # | Task | Who | Depends on | Done when |
|---|---|---|---|---|
| 1.1 | Apply the **report template**: `bash logging/scripts/step9-report-index-template.sh` | K | 0.5 | next day's index mapping shows `date` / `long` on the template's fields (not retroactive) |
| 1.2 | Write a **detail template** `logging/opensearch/polaris-logs-template.json` (`http_status`, `response_size` long; `mdc.requestId`, `loggerName`, `user_principal_name`, `api_path` keyword; `secret_redacted` boolean) + extend step9 or a sibling script | C | — | JSON valid, committed |
| 1.3 | Apply 1.2 | K | 1.2 | next `polaris-logs-*` index mapping matches |
| 1.4 | ~~**Notebook: one phase per window**~~ **CLOSED 2026-09-16 — option A: not needed.** The traffic notebook stays back to back in one window; phases are verified by `step10` (tick-interval readout) + `step11` (replay of the raw tier-1 copy, exact) + request-id lookups. Side fix in polaris-learning `c64cfd3`: `make_traffic.drive()` still waited `lag=0.5` per phase — now requires `tick_interval_s`. Was: (`polaris_log_coverage_v2.ipynb`, lag = `Interval_Sec + 1.5` into *each* window) — so role/grant gates read one phase | K (notebook repo) · C review | — | a run whose report shows ≥ one window per phase |
| 1.5 | **Nested namespace commit key** — *traffic written 2026-09-16 (polaris-learning `ed768b9`, phase J in `polaris_api_traffic_v1.ipynb` and `make_traffic` `full`); needs a run, then `step10` + `step11` on its window; pass = ONE row at the printed `resource_key` with `requests` and `commit_count`*. Was: — add an `a.b` namespace + table commit to the matrix; check the table row carries both `requests` and `commit_count` (no `a.b` phantom row) | K run · C review | 1.4 | one row, not two |

## Phase 2 — the next Lua roll (bundle changes; every roll is a whole-pipeline availability risk, proposal §9.2)

| # | Task | Who | Depends on | Done when |
|---|---|---|---|---|
| 2.1 | ~~Decide the 404 policy~~ **DECIDED 2026-09-16:** count, don't store; drop the request's allow-listed app lines by `mdc.requestId`. Proposal §3.9 written | K | — | §3.9 written; if it changes the Lua, spec added to this bundle |
| 2.2 | ~~Decide the deploy method~~ **DECIDED + WRITTEN 2026-09-16:** ConfigMap `polaris-fluent-bit-lua` via `fluent-bit/kustomization.yaml`, `extraVolumes`, `hotReload` (reloader sidecar). step2 takes the kustomize render as arg 2; step3 checks the new ConfigMap sha + reloader. Hot-reload safety unmeasured → runbook | K decide · C implement | — | chosen method in proposal §9.1 and `values.yaml` header |
| 2.3 | **DONE (written) 2026-09-16** — `/namespaces/{ns}/register` pattern, kind `collection` (the key is the namespace's table collection, like `POST …/tables`), case in `test-schema-v5.lua`. Was: kind `table` | C | — | test case passes |
| 2.4 | **DONE (written) 2026-09-16** — v5 Lua (hold/memo/orphans, 4 summary fields), `test-schema-v5.lua`, v3/v4 tests expect schema 5, report template +4 `long`, step11 predicts the detail index by logger | C | 2.1 | tests pass on LuaJIT/Lua 5.1; export replay shows the expected keep/drop |
| 2.5 | **OPEN** — **Revert the window to 1800s** (`WINDOW_SECONDS = 1800`; keep `Interval_Sec 5` — proposal §4.6-7) | C write · K `apply-lua.sh` | 2.6 verified (v5 is checked on 30s windows first; then a Lua-only change: apply + restart) | Lua + comments updated, tests adjusted (sed to 30 for tests) |
| 2.6 | **DONE 2026-09-16** (rev 17; then rev 18 reloader removed, rev 19 `#30`, refactor `#31`) — **Roll the bundle** (2.2–2.4; 2.5 follows as a hot-reload-only change): tests → kustomize + helm render → `step2-render-gate.sh render lua` → `kubectl apply -k fluent-bit/` → helm upgrade → step3 → step9 → traffic → step10/11 → runbook B/C/D | K | 2.2–2.4 | step3 all PASS, `k8s-logs` receiving, step11 PASS with detail 200/22/78-style prediction met, no 404 access doc in `polaris-logs-*` |
| 2.7 | **OPEN** — **Delete the 30s-window verification `polaris-report-*` indices** before the Monitoring team attaches a retention policy. *Destructive — explicit OK at execution time.* | K | 2.6 | only 1800s-window report indices remain |
| 2.8 | ~~Write ISM policies~~ **HANDED TO THE MONITORING TEAM 2026-09-16 (Kade)** — recommended values stay in proposal §5.3 (30 d detail, 365 d report) | Monitoring | — | — |
| 2.9 | ~~Apply ISM~~ **Monitoring team** | Monitoring | 2.7 | — |

## Phase 3 — production readiness and port

| # | Task | Who | Depends on | Done when |
|---|---|---|---|---|
| 3.1 | **Load test** the DaemonSet at production rate: ~580 lines/s average, and a peak (e.g. 3×), CPU limit 200m | K run · C harness + review | 2.6 | no input pause / backlog growth; CPU headroom recorded, or limits raised |
| 3.2 | **Row caps** — watch `resources_other`, `principals_other`, `role_keys_forced` under realistic key counts; size `REPORT_MAX_RESOURCES` | K · C | 3.1 or first prod day | caps never hit, or raised with memory re-checked |
| 3.3 | **One-day measurement** — `_cat/indices` sizes / doc counts for both indices; replace proposal §6 estimates (doc size, exception-lines-per-error ratio) | K measure · C doc | 2.6 (+ prod for real ratios) | §6 carries measured numbers |
| 3.4 | **Can production have two Polaris indices?** If not: merge into `polaris-audit-*` 30d (proposal §5.4) — one template holding both shapes | K confirm · C config | — | index layout decided for prod |
| 3.5 | **Port to GitOps** (Bitbucket → Jenkins → ArgoCD): values, Lua, templates (ISM is the Monitoring team's; decide the deploy unit first — `REVIEW-pipeline` P5); prod index prefix and OpenSearch endpoint; Secret-based credentials | C files · K pipeline | 2.2, 3.4 | ArgoCD app syncs; step3-equivalent checks pass in prod |
| 3.6 | **Tier 1 credentials to the Secret** (`#4`) — first verify the Secret's user can write `k8s-logs` | K verify · C change | — | two literal credentials gone; tier 1 still indexing |
| 3.7 | **Polaris runtime settings in prod** — console threshold (DEBUG would cost filter CPU for nothing), replica count (several Polaris pods on one node aggregate into one report) | K | — | recorded in proposal §11 |
| 3.8 | **Dashboards and alerts** from proposal §8 (commit mean via sum/count, auth_denied surge, new logger, `secret_redacted`, collection gap, `errors_5xx` minus the four `#24` operations) | C queries · K build | 2.6 (1800s data) | alerts fire on a synthetic trigger |

## Docs to keep in step (same commit as the change they describe)

| # | Task | Who | When |
|---|---|---|---|
| D.1 | `polaris-logging.drawio` — v4 diagram (tick, allow-list drop, app_dropped, two indices) | C | any time |
| D.2 | Proposal status table (top) and §10.1 after each phase | C | per phase |
| D.3 | `SCHEMA-report.md` for any schema change (404 policy, register) — **v5 section written 2026-09-16** | C | with 2.4 / 2.3 |
| D.4 | `.memory/active-issues.md` #25 / #27 closed or updated; `MEMORY.md` *Now* | C | per phase |

---

## Order at a glance

```
0.1 → 0.2 → 0.3          0.4   0.5 → 1.1          1.2 → 1.3
          1.4 → 1.5
2.1 ─┐  2.3 ─┐
2.2 ─┼──────┼─ 2.4, 2.6 → 2.5 → 2.7 → (Monitoring team: retention)
     │      │                   └→ 3.1 → 3.2, 3.3, 3.8
3.4 ─┴──────┴──────────────────────────────→ 3.5        3.6, 3.7 independent
```

**Critical path:** 0.1 → 0.2 → ~~1.4~~ → 1.5 → 2.6 → 2.5 → 2.7 (2.8/2.9 handed over). Everything that needs 30-second windows
(phase 0, 1.4, 1.5) must finish **before** 2.5 — after the revert, a verification run takes 30 minutes per
window.

**Decisions only Kade can make:** 2.1 (404), 2.2 (deploy method), 3.4 (index count in prod), and the OK for
2.7 (delete) at the moment of execution.
