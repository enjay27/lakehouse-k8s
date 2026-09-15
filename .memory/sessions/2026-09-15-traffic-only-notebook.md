# 2026-09-15 — `polaris_api_traffic_v1.ipynb`: v2's traffic, and nothing that verifies

**Input:** Kade — make a notebook with exactly v2's traffic logic and no verification; it must
not read OpenSearch or any other service. **Output:** `log-coverage/polaris_api_traffic_v1.ipynb`
(33 cells, 16 code), one commit. **Not executed against the cluster.**

## What was kept, and how "exactly the same" was checked

Built by script from `polaris_log_coverage_v2.ipynb` **as it was on disk**, including session 13's
uncommitted `PHASE_LAG` edits. Traffic cells kept: v2 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30
(identities, fixture + `BINDING` + doomed family + `teardown_all`/atexit, grid + dry run +
`run_phase`, phases B–I) and 36 (target vs status matrix — Polaris-side only).

A diff of every kept cell against v2, after the renames below, shows **only printed strings and
one comment changed** (the ones that talked about gates/VOID/access log). No call, order, request
id, boundary wait or lag differs.

Renames, for the import boundary `make_traffic.py` already obeys:
- `lc.*` → `traffic_helpers.*` — asserted `is`-identical (log_coverage re-exports them).
- `osr.seconds_to_boundary` / `osr.window_bounds` → `make_traffic`'s copies — asserted equal.
- No `os_report`, `log_coverage`, `vlogs`, `kubectl` anywhere in code cells.

Removed: v2 0–8 verification preflight (OpenSearch ping/indices, Gate 7 Lua test, ConfigMap
read, Gate 0/mappings), 31–34 collection + raw documents, 37–40 gates + invariants, 41–42 findings
and both report writers. Replaced by one cell printing run id, phase windows, the E/F/G request ids
and every ≥500 — the handoff to `local-k8s`, with no verdicts.

## The one decision: window timing is a parameter (Kade chose option 1)

v2 read `WINDOW_SECONDS` and `Interval_Sec` from the Fluent Bit ConfigMap via kubectl. v1 takes
them as literals (**30 / 5, the temporary fast-run values**) and derives
`PHASE_LAG = TICK_INTERVAL_S + 1.5` exactly as v2. Added one assert v2 lacked:
`WINDOW_SECONDS % TICK_INTERVAL_S == 0` — the lag only means something while the tick divides
the window. **Cost:** reverting local-k8s to 1800/30 now also means editing this cell by hand.

## Found on the way, NOT fixed

**`src/make_traffic.py` still waits with `lag=0.5`** (`_grid_phase`, `_phase_commit`,
`_phase_delete`, `_phase_grants`, `_phase_500`). Session 13 fixed that blind-spot bug in v2 only,
so `run_traffic.py` and whatever `local-k8s` imports still fire every phase inside the tick's
blind spot. Out of scope for this task; it is the next thing to fix.

## Verification that ran

nbformat valid; all 16 code cells parse; used `th.`/`mt.`/`mx.` attributes all exist;
`run_traffic.py --dry-run` builds 286 requests; `pytest` 911 passed / 45 skipped (in a VM venv
synced from `uv.lock` — the checkout's `.venv` is the Mac's and does not run in the VM).
