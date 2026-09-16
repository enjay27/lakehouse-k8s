# 2026-09-16 — v5 rolled and verified; hot reload removed and rolled

Cowork session (no cluster reach). Kade ran every cluster command; Claude read results, fixed scripts, recorded.

## Pre-roll, off-cluster
- Lua tests v3/v4/v5 ALL PASS on LuaJIT 2.1 (sha `bfff86db220036c2`).
- helm could not be obtained (get.helm.sh, fluent.github.io, proxy.golang.org blocked). Read chart 0.57.6
  **source** from GitHub tag `fluent-bit-0.57.6` instead: step2's hot-reload expectations match `_pod.tpl`.

## The roll, including the wrong turn
- First step3: no reloader, no flag. Looked like a failed upgrade; `helm history` showed rev 16 (09-15)
  still deployed — **`helm upgrade` had simply not been run** (only `kubectl apply -k`). Pod `rvm49`, 23h.
- In-pod sha `8c1fb607…` was read as "not synced"; it was the hash of the runtime's `cat` not-found message
  (distroless image) — same value on a pod where the path did not exist.
- step2 on the **first real render**: all PASS. `helm upgrade` → rev 17. step3's single FAIL (image) and
  `????` were step3 bugs; also its metrics section had never worked (`\"` in f-string braces, Python < 3.12).
  Fixed; re-run PASS. step9 PASS (41).
- step 7, window 08:41:00Z: step11 PASS 67×34 (incl. detail-by-logger equality); `schema_version` 5,
  `counted_404` 100, `app_dropped_404` 110, held 0/0; detail 200/22/78 == pre-roll prediction; 0 stored 404s.

## Found on the way
- `#29`: tier-1 OUTPUT 2 dropped one chunk per traffic run (05:10 on v4, 08:41 on v5). Not the Polaris
  records of the window (720/720 distinct `sequence`, replay exact). Cause unread.
- "Why 2 replicas?" — `READY 2/2` was two containers (fluent-bit + reloader) in one DaemonSet pod.
- CLAUDE.md / environments.md still said image 3.2.2, REVISION 1, `--set-file`: corrected.
- Git from Cowork cannot unlink lock files; they are moved to `.git/_to_delete/` (note in CLAUDE.md).

## Decision: no hot reload
Kade: not needed; load at start, simple config. Offered `--set-file` (recommended: one command, chart
checksum restarts) vs separate ConfigMap + restart; **Kade chose ConfigMap + restart**. The risk that choice
carries — apply without restart leaves the old script running silently — is covered by `apply-lua.sh`
(apply and restart in one step) and a new step3 check (container start ≥ ConfigMap last change).
Written, gates adjusted, **not rolled**. Runbook B/C never ran; nothing about invalid-script reload was measured.

## Roll of the removal
Kade: step3 `RESULT: post-upgrade checks passed` (new checks: single container, no flag, start ≥ CM change).
step2 output and revision number not pasted.
