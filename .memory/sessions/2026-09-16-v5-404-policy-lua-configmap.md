# 2026-09-16 — policy v5: 404 counted not stored; Lua as its own ConfigMap with hot reload

Cowork session, no cluster reach. Everything below is written and tested off-cluster; nothing is rolled.
Tracking: `active-issues #28`. TODO items 2.1–2.4.

## Decisions (Kade)

1. "404 should be summarized, and not stored. This request should be counted in 4xx error field."
   Follow-up on how to drop the request's app lines: "By request id, since it has its own unique one."
2. "For production, how about create new ConfigMap for this lua script? which will load dynamically
   without any changes in runtime" → "new ConfigMap … should be created in FluentBit directory".

## What was built

- `fluent-bit/polaris_access_log.lua` v5: rule 3′ (404 → `counted_404`, `access_counted`), request-id hold
  for allow-listed INFO app lines (queue with head/tail integers — `#` on a holey table is undefined),
  30 s status memo for app lines that arrive after their access line, orphans stored with
  `held_orphan: true` after 30 s / 10000 records and flushed with the next *log* record (never from the
  tick — the tick's output goes to the report index). Summary +`counted_404`, `app_dropped_404`,
  `held_orphans`, `held_pending`. Register pattern (kind collection). `now_seconds(record)` instead of
  `os.time()` so orphan timing is testable.
- `fluent-bit/kustomization.yaml` (configMapGenerator, `disableNameSuffixHash` — a hash suffix would
  change the pod spec and turn every Lua change into a restart).
- `fluent-bit/values.yaml`: `luaScripts: {}`, `extraVolumes`/`extraVolumeMounts` (`/fluent-bit/polaris-lua`,
  no subPath), `hotReload.enabled` + `extraWatchVolumes: [polaris-lua]`, script paths, 4 int keys.
- step2 now takes the kustomize render as a second argument; Lua content checks moved there; helm
  render checks the wiring (reloader, `--enable-hot-reload`, volume, paths, no checksum annotation,
  `type_int_key` count 3).
- step3 reads the sha from `polaris-fluent-bit-lua`, checks the reloader and flag, prints the
  `/api/v2/reload` counter.
- Report template +4 `long` (41). Proposal (ko) §3.9, §4.5, §9.1–9.4, §10–12; SCHEMA-report v5;
  runbook `logging/RUNBOOK-lua-hot-reload-2026-09-16.md`.

## Evidence

- v3, v4, v5 tests: ALL PASS on LuaJIT and Lua 5.1 (v3/v4 now expect `schema_version` 5).
- `kustomize build` v5.4.3: ConfigMap data byte-identical to the file (sha compared).
- Chart 0.57.6 downloaded from GitHub releases and read: `configmap-luascripts.yaml` still renders
  (empty) when hotReload is on; `_pod.tpl` mounts it at `/fluent-bit/scripts` and adds the reloader with
  `-volume-dir=/watch/extra-0` for our volume; daemonset drops `checksum/*` annotations under hotReload.
- step2 run against a **simulated** helm render (Python re-implementation of the relevant template
  branches over chart defaults + values.yaml) and the real kustomize render: all PASS. The simulation
  reproduces the v4 gate's known counts (`OS_PASSWORD` 3, tier-1 literals 2), which is the only reason
  to trust it at all. A real `helm --dry-run` is still owed.
- step11 replay (earlier in the session) of the 2026-09-16 window with v5: detail 300/32/178 →
  200/22/78; with v4 the same replay is exact, so the difference is the policy.

## Wrong turns worth remembering

- The v5 file header line 2 still said "정책 v4 / 리포트 스키마 v4" after the body was v5 — caught only
  by reading the kustomize render. Grep headers when bumping versions.
- step2's first draft anchored `local WINDOW_SECONDS = 30$`; the real line carries a trailing comment.
  And `\/` in a grep pattern warns on newer GNU grep; Kade's Mac runs BSD grep — keep patterns plain.

## Open (see #28 and the runbook)

- Invalid-script hot reload on 5.1.1 (runbook C) — decides whether hot reload is acceptable in prod.
- Reload loss (tier-1 `sequence` gaps, runbook D), double-reload per apply.
- Polaris `requestId` when the client sends no request-id header (production).
- 2.5 (1800 s) intentionally after v5 is verified on 30 s windows.
