# HANDOFF — refactored v5 is live; the pipeline review awaits decisions. Start at §3 step 1.

**Written 2026-09-16 (late KST) at the end of the Cowork session that refactored and rolled the Lua, removed the thread
fields and reviewed the whole pipeline (commits `5315e0d`..this one).**
Supersedes [`HANDOFF-audit-log-next-2026-09-16.md`](HANDOFF-audit-log-next-2026-09-16.md).
Reviews: [`REVIEW-pipeline-2026-09-16.md`](REVIEW-pipeline-2026-09-16.md) (whole flow, P1–P12, decisions pending) ·
[`REVIEW-lua-refactor-2026-09-16.md`](REVIEW-lua-refactor-2026-09-16.md) (done, rolled). Issues `#30` `#31` (verified), `#29`
(dropped), `#18` `#24` `#4` (open). Plan: [`PLAN-audit-log-todo-2026-09-16.md`](PLAN-audit-log-todo-2026-09-16.md).
Docs index: [`README.md`](README.md).

---

## 1. In sixty seconds

| | state |
|---|---|
| Running on OrbStack | DaemonSet `benchmarks-fluent-bit`, pod `qr4br`, one container `fluent-bit` 5.1.1, chart 0.57.6, no hot reload |
| Helm | rev 17 v5 + reloader · 18 reloader removed · **19** thread/ndc trim (`#30`) · **next** = Lua refactor with FILTER 2 removed (`#31`; number not recorded, expected 20) |
| Lua | policy/report schema **v5**, **one** Lua filter (FILTER 3 parses, decides, counts, reports). ConfigMap `polaris-fluent-bit-lua`, sha `2fbcfa47c513f5a0`, read at start |
| Report window | **`WINDOW_SECONDS` 30** (verification value) — 1800 still to do |
| Detail docs | no `threadName` / `threadId` / `ndc` (0 / 386 verified) |
| Verified live | window 15:01Z after the refactor = 14:44Z and 08:41Z before it, count for count; detail 200 / 22 / 78; 0 stored 404s, 0 parse errors; `http_status` integer |
| Retention (ISM) | **not ours** — the Monitoring team writes and applies it (Kade, 2026-09-16) |
| Dropped | `#29` tier-1 chunk drops — not diagnosed, by decision |

## 2. Rules the next session must not relearn

- **Lua only** → `bash fluent-bit/apply-lua.sh` (tests v3/v4/v5 + first-tick → diff → apply → restart → log check → sha).
- **Values only** → step2 on a fresh render (no `--debug`) → `helm upgrade` → step3.
- **Lua and values together** → `apply-lua.sh --no-restart` → step2 → `helm upgrade` → step3, **with no restart in between**.
  One half alone either stops every input (tier 1 included) or stores every access line as a parse error (`#31`).
- **Readouts: use `step10-v4-window-readout.sh <window_start>` then `step11-replay-window.py`** — exact JSON, all three sources, window
  cut by the tick. Dev Tools panel copies are not JSON, miss tier 1, and cost round trips (review P9).
  If a panel copy is all there is: `logging/scripts/devtools-json-fix.py`.
- **Cowork has no cluster reach and cannot delete in the mount.** After every git call move `.git/*.lock` into `.git/_to_delete/`.
- **Polaris is not changed from here.** Verify against the running object, never an intent artifact.

## 3. What is left — in this order

| | task | who | depends on | done when |
|---|---|---|---|---|
| **1** | **Review measurements M1–M5** (`REVIEW-pipeline` §4, read-only): skip-log count on OUTPUT 1, Fluent Bit self-ingest volume, `log`-field docs in tier 1, shipper still installed?, index sizes | K run · C read | — | numbers filed against P2/P3/P4/P8/P10 |
| **2** | **Decide review items** — P1 (trim before Lua) + P6 constants, P2/P3/P4 (tier 1), P5 (one deploy unit), P6 `_msg`, P7 report `_msg`, P8 mappings, P10 shipper, P11 script moves | K decide · C write | 1 for P2–P4, P8, P10 | decisions recorded; accepted items planned |
| 3 | **P1 + P6-constants roll** (tier 2 values only) while windows are still 30 s: step2 → `helm upgrade` → step3 → traffic → step10/11 | C write · K roll | 2 | report rows and detail-by-logger unchanged; stored field list minus the removed constants |
| 4 | **TODO 2.5 — `WINDOW_SECONDS` 30 → 1800** (Lua-only, `apply-lua.sh`). Do everything that wants 30 s windows first (3, tier-1 items). After it a verification window costs 30 min; step10 takes `[window_seconds]` 1800 | C write · K apply | 3 (preferably) | summary `window_seconds` 1800, `window_start` on :00/:30, step11 PASS on one 1800 s window |
| 5 | **TODO 2.7 — delete the 30 s-window `polaris-report-*` indices.** *Destructive: explicit OK at execution.* Tell the Monitoring team they are verification data | K | 4 | only 1800 s report indices remain |
| 6 | **Tier-1 roll** for accepted P2/P3/P4 (node-wide: tier 1 must still index afterwards) | C write · K roll | 1, 2 | step3 section 4 PASS; M1–M3 re-read |
| 7 | **Phase 3** (plan §3): 3.1 load test (also measures `#31` and P1 CPU) · 3.2 row caps · 3.3 one-day size · 3.4 one vs two prod indices · 3.5 GitOps port (decide P5 first) · 3.6 tier-1 credentials to a Secret (`#4`) · 3.7 prod Polaris log level / replicas · 3.8 dashboards and alerts (hand the P12 buffer-drop metrics to the Monitoring team) | see plan | 4 for 3.3/3.8 | see plan |
| 8 | `#24` upstream report (four NPEs) — **Kade's call** | K | — | filed or declined |
| 9 | Docs: `polaris-logging.drawio` is still pre-v4 (two Lua filters, no report tick detail) | C | — | diagram matches review §1 |
| 10 | Git leftovers: `.git/_to_delete/`, `.git/objects/*/tmp_obj_*` (or grant Claude delete once). Not Claude's, uncommitted: `polaris/values.yaml`, `postgresql/values.yaml`, `Claude outputs/*` | K | — | — |

## 4. Unmeasured — do not state as fact

- CPU of any of it: the refactor's C-side saving, P1's. Phase 3.1.
- The start-up window fix (R4) on the cluster: the first window after the refactor restart was not exported.
- Helm revision number of the refactor roll; step2/step3 output of that roll (only the traffic result was read).
- Whether `fb-polaris-shipper` / VictoriaLogs still run (review P10) and whether Polaris writes its log file (`#5`).
- Production: whether Polaris assigns `requestId` without a client header (if not, app lines of 404s are kept).
- Tier-1 loss across a pod restart.

## 5. Where things are

| file | what |
|---|---|
| `fluent-bit/values.yaml` | the DaemonSet: 3 inputs, tier-1 filters, tier-2 FILTER 0/1/3/4, 4 outputs |
| `fluent-bit/polaris_access_log.lua` · `kustomization.yaml` · `apply-lua.sh` | v5 Lua (one filter) · its ConfigMap · the Lua roll |
| `logging/scripts/step2-render-gate.sh` · `step3-postupgrade.sh` · `step10-…` · `step11-…` · `step9-…` · `step12-…` | render gate · post-roll checks · window readout · replay · report / logs templates |
| `logging/scripts/test-schema-v3/v4/v5.lua` · `test-first-tick.lua` · `test-raw-access-shim.lua` | Lua tests (raw `_msg` input) |
| `logging/candidates/` | refactor harnesses: `diff-refactor.lua`, `bench-*.lua`, `tier1-to-lua.py`, the applied R1 patch |
| `logging/opensearch/` | index templates, `devtools-export.console` |
| `.scratch/readout-2026-09-16T144400Z/` | last full readout (tier1 + report + detail), old script |
