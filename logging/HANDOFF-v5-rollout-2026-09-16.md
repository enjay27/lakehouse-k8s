# HANDOFF — policy v5 is committed and NOT on the cluster. Start at §2 step 1.

> **SUPERSEDED by [`HANDOFF-audit-log-next-2026-09-16.md`](HANDOFF-audit-log-next-2026-09-16.md) — start there.**
>
> **UPDATE 2026-09-16 (later the same day).** §2 was run: v5 is live as **rev 17** and verified (step11
> 67×34, `counted_404` 100 with 0 stored, detail 200/22/78 as predicted — `active-issues.md` #28). Then
> **hot reload was removed** (Kade): `hotReload` is gone from `values.yaml`, Lua changes go through
> `bash fluent-bit/apply-lua.sh` (apply + restart). Everything below about the reloader, runbook B/C and
> "reload" is history. The removal itself is written and **not rolled** — see #28 for its roll.

**Written 2026-09-16 at `aaf7679`, for the next session (Kade + Claude).**
Read §1 and §2 before touching the cluster. §4 is the remaining plan; §5 is what nobody has measured.

Plan: [`PLAN-audit-log-todo-2026-09-16.md`](PLAN-audit-log-todo-2026-09-16.md) (Phase 2 onward) ·
issue [`#28`](../.memory/active-issues.md) · session note
[`2026-09-16-v5-404-policy-lua-configmap.md`](../.memory/sessions/2026-09-16-v5-404-policy-lua-configmap.md) ·
runbook [`RUNBOOK-lua-hot-reload-2026-09-16.md`](RUNBOOK-lua-hot-reload-2026-09-16.md).

---

## 1. In sixty seconds

| | state |
|---|---|
| Running on OrbStack | **policy v4**, pod `benchmarks-fluent-bit-rvm49`, Lua via Helm `--set-file`, `WINDOW_SECONDS` 30 |
| In the repo | **policy v5** — nothing below has been applied |
| Phases 0 and 1 | done (v4 verified by replay 64×30 and 67×30, both index templates applied) |
| Phase 2 | 2.1–2.4 decided and written; **2.6 (roll) is next**; 2.5, 2.7–2.9 after |

What v5 changes (Kade's decisions, 2026-09-16):

1. **404 is counted, not stored.** It stays in `errors` / `errors_4xx` on resource and principal rows;
   summary gains `counted_404`. The request's allow-listed INFO app lines (IcebergExceptionMapper,
   PolarisServiceImpl) are dropped too, matched by **`mdc.requestId`** — `app_dropped_404`. WARN/ERROR are
   always kept. App lines are held until their access line arrives (they are logged *before* it); unmatched
   after 30 s they are stored with `held_orphan: true` (`held_orphans`, `held_pending`).
2. **The Lua is its own ConfigMap** `polaris-fluent-bit-lua` (`fluent-bit/kustomization.yaml`), mounted via
   `extraVolumes`, reloaded by the chart's `hotReload` sidecar. **No `--set-file` after v5 rolls.**
3. `/namespaces/{ns}/register` → `resource_kind: collection`.

Verified off-cluster only: v3/v4/v5 Lua tests ALL PASS (LuaJIT, Lua 5.1); kustomize output is byte-identical
to the file; step2 PASS against a **simulated** helm render (no helm in Cowork). Replay of the 09-16 window
predicts detail docs **300 / 32 / 178 → 200 / 22 / 78** (access / PolarisServiceImpl / IcebergExceptionMapper).

## 2. The roll (TODO 2.6) — run in this order

The Helm upgrade restarts the pod **once** (new volume + sidecar). Every command from the repo root,
context `orbstack`.

```bash
kubectl config current-context                                  # must print orbstack
# 1. Lua tests
cp fluent-bit/polaris_access_log.lua /tmp/polaris.lua
for t in v3 v4 v5; do luajit logging/scripts/test-schema-$t.lua || break; done      # ALL PASS x3
# 2. Renders — NO --set-file, NO --debug
kubectl kustomize fluent-bit/ > /tmp/render-lua.txt
helm upgrade --install benchmarks-fluent-bit fluent/fluent-bit --version 0.57.6 \
  -n datahub-hynix -f fluent-bit/values.yaml --dry-run=client > /tmp/render-after.txt
# 3. Gate — two arguments since v5
bash logging/scripts/step2-render-gate.sh /tmp/render-after.txt /tmp/render-lua.txt
# 4. ConfigMap BEFORE Helm (else the new pod hangs in ContainerCreating)
kubectl apply -k fluent-bit/
# 5. Upgrade — step 2's helm command without --dry-run
# 6. Post-upgrade checks, then the report template (41 fields)
bash logging/scripts/step3-postupgrade.sh
bash logging/scripts/step9-report-index-template.sh
```

Then:

7. **Skip one window**, run traffic (`polaris_api_traffic_v1.ipynb` or `make_traffic`), then
   `step10-v4-window-readout.sh <window>` and `python3 logging/scripts/step11-replay-window.py <dir>`.
   Pass: step11 PASS including the detail-by-logger comparison; **no `http_status: 404` access doc** in
   `polaris-logs-*` after the roll; summary `schema_version` 5.
8. Runbook **B** (comment-only reload, no restart) and **D** (tier-1 `sequence` gaps across a reload).
9. Runbook **C** (invalid script) — **only with Kade's explicit OK at that moment**: it may stop tier 1
   for every namespace.

Record each result in `#28` and the runbook. Paste-backs: redact tier-1 `HTTP_Passwd` values (`#4`).

### If step 2 or 3 fails

- **step2 is new and has only met a simulated render.** A FAIL on a real render may be a wrong
  expectation, not a wrong config — show Claude the failing line and the matching render lines before
  changing values. Counts are *lines*; rendered comments inside `config:` count.
- `kubectl kustomize` missing flags on an old kubectl → `kustomize build fluent-bit/`.

### If the roll goes wrong

- Pod stuck ContainerCreating → the ConfigMap is missing: `kubectl apply -k fluent-bit/`.
- `cannot access script` / filter init failed / k8s-logs silent → `helm -n datahub-hynix history benchmarks-fluent-bit`
  and `helm rollback … <last v4 revision>` (restores the `--set-file` Lua and removes the sidecar). v4's step3:
  `git show 7fbea4d:logging/scripts/step3-postupgrade.sh > /tmp/step3-v4.sh`.
- Leaving `polaris-fluent-bit-lua` behind after a rollback is harmless; deleting it needs Kade's OK.

## 3. Changed files (all in `aaf7679`)

| file | what to know |
|---|---|
| `fluent-bit/polaris_access_log.lua` | v5. `WINDOW_SECONDS` still **30** |
| `fluent-bit/kustomization.yaml` | new. `disableNameSuffixHash` on purpose (a suffix turns reloads into restarts) |
| `fluent-bit/values.yaml` | `luaScripts: {}`, `extraVolumes/Mounts`, `hotReload`, script path `/fluent-bit/polaris-lua/…`, +4 int keys |
| `logging/scripts/step2-render-gate.sh` | arg 2 = kustomize render; `type_int_key` expected **3** |
| `logging/scripts/step3-postupgrade.sh` | sha from `polaris-fluent-bit-lua`; reloader + `--enable-hot-reload`; `/api/v2/reload` counter |
| `logging/scripts/test-schema-v5.lua` | new; v3/v4 tests now expect `schema_version` 5 |
| `logging/scripts/step11-replay-window.py` | predicts detail docs by logger; replaying a v4-processed window with v5 shows the policy as mismatches |
| `logging/opensearch/polaris-report-template.json` | +`counted_404`, `app_dropped_404`, `held_orphans`, `held_pending` (41) |
| proposal (ko) §3.9, §9.1–9.4 · `SCHEMA-report.md` v5 · runbook · TODO · `#28` · `MEMORY.md` | docs |

Not Claude's, left uncommitted: `polaris/values.yaml`, `postgresql/values.yaml`,
`Claude outputs/*`.

## 4. After the roll — remaining TODO

| # | task | who | depends on |
|---|---|---|---|
| 2.5 | `WINDOW_SECONDS` 30 → 1800 — a Lua-only change via `bash fluent-bit/apply-lua.sh` (restart) | C write · K apply | 2.6 verified |
| 2.7 | delete the 30 s-window `polaris-report-*` indices — **destructive, explicit OK** | K | 2.5 |
| 2.8 | ISM policies `ism-polaris-logs-30d.json`, `ism-polaris-report-365d.json` + apply script | C | — (can start any time) |
| 2.9 | apply ISM | K | 2.7, 2.8 |
| 3.1–3.8 | load test, row caps, one-day measurement, prod index count, GitOps port, tier-1 creds to Secret, prod Polaris settings, dashboards/alerts | see plan | mostly 2.6 |
| D.1 | `polaris-logging.drawio` still pre-v4 | C | any time |



## 5. Unmeasured — do not state as fact

- What Fluent Bit 5.1.1 does when a **reloaded script is invalid** (runbook C). Decides hot reload for prod.
- Whether one `kubectl apply -k` triggers one reload or two; reload latency (expected ~60–90 s).
- Loss across a reload (tier 1 memory buffers; runbook D).
- Whether Helm config and Lua changes applied together can reload out of order — until measured, integer-key
  changes go through Helm first, Lua second.
- **Production:** whether Polaris assigns `requestId` when the client sends no request-id header. If not,
  404 app lines are kept (safe, but less storage saved than proposal §6.2 says).
- `@timestamp` of held lines becomes the access line's (ms later); orphans take the next record's. `_time`
  keeps the original — dashboards on app lines should prefer `_time` if that matters.
