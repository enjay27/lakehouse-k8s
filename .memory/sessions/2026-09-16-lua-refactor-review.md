# 2026-09-16 — Lua review/refactor and thread-field removal (Cowork)

Asked by Kade: review `polaris_access_log.lua` for unnecessary logic and inefficient loops, and propose better logic to
compare with the current one (not replace it). Remove thread name/id. Plan first.

## Decisions (Kade, after the plan)
1. Thread fields: `polaris-logs-*` only. Tier 1 and the VictoriaLogs shipper keep them.
2. R4 (pre-first-tick records uncounted): fix. A partial window is visible anyway (`partial_window`, `window_start` vs `min_record_time`).
3. R1 (merge the two Lua filters): go.
4. `ndc`: remove as well.

## What happened
- **Commit 1 (`5315e0d`):** `Remove_key threadName/threadId/ndc` in FILTER 4 (not in Lua: in Lua every stored record would need
  return code 2 and a re-encode), `threadId` mapping out of the logs template, step2/step3 checks. `#30`.
- **Candidate.** The first idea for R2 was a segment tokenizer. It was benchmarked against a plain-find literal guard in front of the
  same patterns, and it lost: slower (2.35 vs 1.95 µs) and riskier, because every rule was re-expressed by hand. The chosen version is
  guard + per-window cache (0.62 µs, from 5.25). The ablation showed R2 is most of the Lua-side gain. Without the guard the whole
  candidate is only 1.07× faster.
- **Tests fed pre-parsed fields** (`http_status` etc.), which the merged filter never sees in production. Rather than keep a
  "parse only if not parsed" branch in the Lua, the tests got a shim that turns those fields into a raw `_msg` line and runs the
  split parser if the script has one. Both scripts now go through the real parse path in all three suites.
- **Differential harness** loads both scripts into separate environments (`setfenv`) and compares every return, field by field:
  real readouts plus a seeded fuzz. It was checked for sensitivity with 5 mutants. The two real readouts processed by v4 still show
  step11's 7 expected mismatches for **both** scripts (policy change, not a fault).
- Promotion order worked out from `apply-lua.sh`'s own header (`--no-restart` then helm): a pod starting with new Lua and old config
  would fail FILTER 2's init (`call polaris_access_log` missing) and stop every input.

## Open
- Kade compares; promotion per the review's §3; do it before TODO 2.5 (1800 s).
- The C-side saving of R1 is only measurable in phase 3.1.
