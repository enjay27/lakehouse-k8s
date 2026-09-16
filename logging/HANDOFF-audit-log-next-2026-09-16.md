# HANDOFF — v5 is live without hot reload. What is left, in order. Start at §3 A.

**Written 2026-09-16 at the end of the Cowork session that rolled v5 (commits `28300b8`..`63cf6e9`).**
Supersedes [`HANDOFF-v5-rollout-2026-09-16.md`](HANDOFF-v5-rollout-2026-09-16.md) (its §2 roll is done).
Plan: [`PLAN-audit-log-todo-2026-09-16.md`](PLAN-audit-log-todo-2026-09-16.md) · issues
[`#28`](../.memory/active-issues.md) (v5), `#29` (tier-1 chunk drops), `#24` (four 500s) · session note
[`2026-09-16-v5-roll-and-hot-reload-removal.md`](../.memory/sessions/2026-09-16-v5-roll-and-hot-reload-removal.md).

---

## 1. In sixty seconds

| | state |
|---|---|
| Running on OrbStack | **policy v5 / report schema v5**, DaemonSet `benchmarks-fluent-bit`, pod `benchmarks-fluent-bit-fjdjb`, **one container** (`fluent-bit` 5.1.1), **no hot reload** |
| Helm | chart `fluent-bit` 0.57.6; rev 17 = v5 with reloader; the removal is the next revision (**number not recorded**, expected 18) |
| Lua | ConfigMap `polaris-fluent-bit-lua` (`fluent-bit/kustomization.yaml`), mounted at `/fluent-bit/polaris-lua/`, sha `bfff86db220036c2`, read **at start only** |
| Report window | **`WINDOW_SECONDS` 30** (verification value) — production value 1800 is TODO 2.5 |
| Index templates | report (41 fields) and logs (8 fields) applied; not retroactive |
| Verified live | 404 counted not stored (100 counted / 0 stored), app lines of 404s dropped by request id (110), detail 200/22/78 as predicted, step11 67×34 exact — twice (08:41Z with reloader, 09:11Z without) |
| Open fault | `#29` tier-1 OUTPUT 2 discards one chunk per traffic run — cause unread |

## 2. Rules the next session must not relearn

- **Lua change = `bash fluent-bit/apply-lua.sh`** (context guard → LuaJIT tests → diff → apply → rollout restart →
  log check → sha). `kubectl apply -k` alone leaves the **old** script running, silently. `--no-restart` only when a
  `helm upgrade` follows. **Never `--set-file`** (v4 and earlier). `apply-lua.sh` has **never run for real** yet.
- **Helm config change** = step2 on a fresh render (no `--debug`) → `helm upgrade` → step3. The chart's
  `checksum/config` restarts the pod; every restart resets Lua state (one partial report window).
- step3's section 3 now proves "the process loaded this script" by **container start ≥ ConfigMap last change**.
- **Dev Tools response panel is not JSON** (triple-quoted multi-line strings, re-indented). Export with
  "Copy as cURL"/curl; repair a panel copy with `logging/scripts/devtools-json-fix.py`. Queries:
  `logging/opensearch/devtools-export.console`. Best of all: save exports under `.scratch/` so Claude reads them in place.
- **Cowork has no cluster reach and cannot delete in the mount.** Git leaves `.git/*.lock` / `tmp_obj_*`; move locks
  to `.git/_to_delete/` after every git call (CLAUDE.md, Version Control).

## 3. What is left — in this order

| | task | who | depends on | done when |
|---|---|---|---|---|
| **A** | **`#29` diagnosis.** Run a traffic notebook, then (read-only) the unfiltered fluent-bit log around the `cannot be retried` line, `docker logs opensearch-node` for that minute grepped for `reject\|mapper\|parse\|exception\|429`, and `_cat/thread_pool/write?v`. Commands are in this session's chat and repeated below. | K run · C read | — | cause named (mapping reject / 429 / buffer) and a fix proposed in `#29` |
| B | Housekeeping for the record: `helm -n datahub-hynix history benchmarks-fluent-bit \| tail -3` (revision of the hot-reload removal) | K | — | revision in `#28` |
| C | **TODO 2.8 — ISM policies** `logging/opensearch/ism-polaris-logs-30d.json`, `ism-polaris-report-365d.json` + apply script | C | — | JSON valid, committed |
| D | **TODO 2.5 — `WINDOW_SECONDS` 30 → 1800.** Claude edits the Lua (tests keep 30 via sed, as planned) → Kade `bash fluent-bit/apply-lua.sh` (its first real run) → step3. Finish anything that still wants 30 s windows first (A's reproduction, optional runbook D "tier-1 `sequence` gaps across a restart"). After it, a verification run costs 30 min per window; step10 takes `[window_seconds]` 1800. Re-check `#26`: the 5 s tick must divide 1800, rows on :00/:30 | C write · K apply | A (preferably) | summary `window_seconds` 1800, `window_start` on :00/:30, step11 PASS on one 1800 s window |
| E | **TODO 2.7 — delete the 30 s-window `polaris-report-*` indices.** *Destructive: explicit OK at execution.* | K | D | only 1800 s report indices remain |
| F | **TODO 2.9 — apply ISM** | K | C, E | `_plugins/_ism/explain/polaris-*` shows both policies |
| G | **Phase 3** (plan §3): 3.1 load test (~580 lines/s, 3× peak, CPU 200m) · 3.2 row caps · 3.3 one-day size measurement · 3.4 one vs two prod indices · 3.5 GitOps port (Bitbucket→Jenkins→ArgoCD; the "apply + restart" step needs a trigger there) · 3.6 tier-1 credentials to a Secret (`#4`) · 3.7 prod Polaris log level / replicas · 3.8 dashboards and alerts | see plan | D for 3.3/3.8 | see plan |
| H | Tier-1 debt: `#18` OUTPUT 1 `Id_Key sequence` indexes nothing (decision pending in `PLAN-tier1-dedup-2026-09-09.md`); `#4` plaintext password (with 3.6) | K decide · C change | — | — |
| I | `#24` upstream report — stack traces for all four NPEs are in `#24`. **Kade's call** (Polaris is not changed from here) | K | — | filed or declined |
| J | Docs: D.1 `polaris-logging.drawio` (still pre-v4); close stale headers — `#25` says "NOT APPLIED" but its body closes it, `#27` "NOT ROLLED" is superseded by v5; proposal §10.1 after D/F | C | — | headers match bodies |
| K | Git leftovers: delete `.git/_to_delete/` and `.git/objects/*/tmp_obj_*` (or grant Claude delete once). Not Claude's, still uncommitted: `polaris/values.yaml`, `postgresql/values.yaml`, `Claude outputs/*` | K | — | — |

### A — the commands (read-only, from the repo root)

```bash
NS=datahub-hynix
POD=$(kubectl -n $NS get pods -l app.kubernetes.io/instance=benchmarks-fluent-bit -o jsonpath='{.items[0].metadata.name}')
kubectl -n $NS logs "$POD" -c fluent-bit --since=30m | grep -n -B15 -A2 'cannot be retried' | grep -v inotify | tail -80
docker logs opensearch-node --since 30m 2>&1 | grep -iE 'reject|mapper|parse|exception|429|circuit|too many' | tail -30
curl -sk -u "$OS_USER:$OS_PASSWORD" "$OS_URL/_cat/thread_pool/write?v&h=node_name,active,queue,rejected,completed"
```
If the fluent-bit log shows no reason line, the next step is `Trace_Error On` on OUTPUT 2 — a values change
(plan first, then step2 → helm upgrade → step3).

## 4. Unmeasured — do not state as fact

- Cause of `#29`, and which container's chunk is lost (chunks are per tag; the Polaris records of both checked windows were intact).
- Tier-1 loss across a pod restart (every Lua change is now a restart).
- `apply-lua.sh` on a real cluster; the PIT request (10) in `devtools-export.console` on 3.5.0.
- Production: whether Polaris assigns `requestId` without a client request-id header (if not, 404 app lines are kept).
- step2's output for the hot-reload-removal render (only step3's RESULT line was recorded).

## 5. Where things are

| file | what |
|---|---|
| `fluent-bit/values.yaml` | the DaemonSet; no `hotReload`; FILTER 2/3 script path `/fluent-bit/polaris-lua/…` |
| `fluent-bit/polaris_access_log.lua` · `kustomization.yaml` · `apply-lua.sh` | v5 Lua · its ConfigMap · the only way to roll it |
| `logging/scripts/step2-render-gate.sh` · `step3-postupgrade.sh` · `step9-…` · `step10-…` · `step11-…` | render gate · post-roll checks · report template · one-window readout · replay |
| `logging/opensearch/` | index templates, `devtools-export.console` |
| `logging/RUNBOOK-lua-hot-reload-2026-09-16.md` | SUPERSEDED; section D's `sequence` query is still useful |
| `logging/PROPOSAL-polaris-audit-log-retention.ko.md` | the proposal (§9.1 deploy method updated) |
