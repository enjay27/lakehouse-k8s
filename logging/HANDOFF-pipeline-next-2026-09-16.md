# HANDOFF — schema v6 is live and verified. Next: the 1800 s window. Start at §3 step 1.

**Final state of the 2026-09-16 Cowork session** (Lua refactor, thread-field trim, whole-pipeline review, schema v6 — commits
`5315e0d`..the one that added this line). Supersedes [`HANDOFF-audit-log-next-2026-09-16.md`](HANDOFF-audit-log-next-2026-09-16.md).
Reviews: [`REVIEW-pipeline-2026-09-16.md`](REVIEW-pipeline-2026-09-16.md) (decided, rolled except P5/P10) ·
[`REVIEW-lua-refactor-2026-09-16.md`](REVIEW-lua-refactor-2026-09-16.md) (rolled). Issues: `#30` `#31` `#32` verified, `#29` dropped,
`#18` closed by P2 (the output is gone), `#24` `#4` open. Plan: [`PLAN-audit-log-todo-2026-09-16.md`](PLAN-audit-log-todo-2026-09-16.md).
Docs index: [`README.md`](README.md). Monitoring team: [`NOTE-monitoring-team-handover-2026-09-16.md`](NOTE-monitoring-team-handover-2026-09-16.md).

---

## 1. In sixty seconds

| | state |
|---|---|
| Running on OrbStack | DaemonSet `benchmarks-fluent-bit`, pod **`62klp`**, one container `fluent-bit` 5.1.1, chart 0.57.6, no hot reload |
| Helm | 17 v5+reloader · 18 reloader removed · 19 thread/ndc trim · then the refactor (`#31`) · then **schema v6 (`#32`)** — the last two revision numbers were not recorded |
| Lua | policy v5 / **report schema 6**, one Lua filter; reads `message`. ConfigMap `polaris-fluent-bit-lua`, read at start |
| Tier 2 chain | parser → Rename `timestamp`→`_time` → trim (process\*, logger class, thread\*, ndc, stream, CRI time) → Lua → OpenSearch (no tag field) |
| Tier 1 | one output (`Id_Key` output deleted), Fluent Bit's own log excluded, no parser filters after `kubernetes` |
| Detail doc fields | `@timestamp _time api_path client_ip exception hostName http_method http_status level loggerName mdc message response_size sequence user_principal_name` |
| Report rows | no `app` / `level`; sentence `message` on `summary` only |
| Report window | **`WINDOW_SECONDS` 30** (verification value) |
| Verified live | window **16:02:30Z** (seq 4): every count equal to the v5 windows (355 / 200 / 155, 404 100 / 110, 67 rows same keys); detail 200 / 22 / 78; 0 stored 404, 0 parse errors; `http_status` int. Doc size (JSON): access 705 → 649 B, app 799 → 743 B, report row 755 → 518 B |
| Retention (ISM) | Monitoring team |

## 2. Rules the next session must not relearn

- **Lua only** → `bash fluent-bit/apply-lua.sh` (tests v3–v6 + first-tick → diff → apply → restart → log check → sha).
- **Values only** → step2 on a fresh render (no `--debug`) → `helm upgrade` → step3.
- **Lua and values together** → `apply-lua.sh --no-restart` → step2 → `helm upgrade` → step3, **no restart in between** (`#31`).
- **Readouts: `step10-v4-window-readout.sh <window_start>` then `step11-replay-window.py`** (exact JSON, tier 1 included). A Dev Tools
  panel copy is not JSON (`devtools-json-fix.py`) and never includes tier 1, so step11 cannot run on it.
- **Query strings through `.keyword`** in any index created after the v6 templates (the bare name is not indexed). The raw line and the
  summary sentence are `message`; indices from before 2026-09-16 16:0xZ still say `_msg`, `app`, `level`.
- **Cowork has no cluster reach and cannot delete in the mount.** After every git call move `.git/*.lock` into `.git/_to_delete/`.
- **Polaris is not changed from here.** Verify against the running object, never an intent artifact.

## 3. What is left — in this order

| | task | who | depends on | done when |
|---|---|---|---|---|
| **1** | **TODO 2.5 — `WINDOW_SECONDS` 30 → 1800** (Lua only, `apply-lua.sh`). After it one verification window costs 30 min; step10 takes `[window_seconds]` 1800 | C write · K apply | — | summary `window_seconds` 1800, `window_start` on :00/:30, step11 PASS on one 1800 s window |
| 2 | **TODO 2.7 — delete the 30 s-window `polaris-report-*` indices.** *Destructive: explicit OK at execution.* Tell the Monitoring team (see the note) | K | 1 | only 1800 s report indices remain |
| 3 | Uninstall `fb-polaris-shipper` / VictoriaLogs (review P10) — Kade, manually. Then update `CLAUDE.md`, `.memory/environments.md`, `.memory/goal.md` | K · C docs | — | `helm list -A` shows neither |
| 4 | Decide **P5** (Lua in the Helm release vs separate ConfigMap) before the GitOps port | K | — | decision recorded in the review |
| 5 | **Phase 3** (plan §3): 3.1 load test (pod CPU for `#31`/P1) · 3.2 row caps · 3.3 one-day size · 3.4 one vs two prod indices · 3.5 GitOps port · 3.6 tier-1 credentials to a Secret (`#4`) · 3.7 prod Polaris log level / replicas · 3.8 dashboards and alerts (use `.keyword` and `message`) | see plan | 1 for 3.3/3.8 | see plan |
| 6 | `#24` upstream report (four NPEs) — Kade's call | K | — | filed or declined |
| 7 | `polaris-logging.drawio` is pre-v4 — redraw from review §1 with the v6 chain | C | — | diagram matches §1 of this file |
| 8 | Git leftovers: `.git/_to_delete/`, `.git/objects/*/tmp_obj_*`. Not Claude's, uncommitted: `polaris/values.yaml`, `postgresql/values.yaml`, `Claude outputs/*` | K | — | — |

## 4. Not read on the cluster — do not state as fact

- The v6 roll's own outputs: the P4 gate count, step2, step3 (incl. its new absence checks), step9/step12 on the v6 templates, and the
  helm revision. Only the traffic result (report + detail exports) was read.
- Tier-1 effects of P2/P3/P4: no `k8s-logs` export after the roll (tier 1 still indexing, no Fluent Bit docs, unchanged DataHub docs).
- Whether the v6 mappings took: they shape indices created **after** step9/step12 ran; `polaris-logs-2026.09.16` is still dynamic.
- Pod CPU of anything; the start-up window fix (R4) on a real restart; production `requestId` without a client header.

## 5. Where things are

| file | what |
|---|---|
| `fluent-bit/values.yaml` | the DaemonSet: 3 inputs, tier-1 `kubernetes` + env filters, tier-2 parser / rename / trim / Lua, 3 outputs |
| `fluent-bit/polaris_access_log.lua` · `kustomization.yaml` · `apply-lua.sh` | Lua (schema 6) · its ConfigMap · the Lua roll |
| `logging/scripts/` | step2 render gate · step3 post-roll (+v6 absence checks) · step9/step12 templates (+`dynamic_templates`) · step10 readout · step11 replay · tests v3–v6, first-tick, shim · `attic/` finished scripts |
| `logging/opensearch/` | v6 templates, `devtools-export.console` |
| `logging/candidates/` | harnesses: `diff-v5-v6.lua`, `diff-refactor.lua`, `bench-*.lua`, `tier1-to-lua.py` |
| `.scratch/readout-2026-09-16T160230Z/` | the v6 verification window (report + detail; no tier 1) |
