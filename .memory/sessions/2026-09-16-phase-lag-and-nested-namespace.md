# 2026-09-16 (session 15) — make_traffic's lag, and a nested-namespace phase

Driven from `local-k8s` TODO 1.4 / 1.5 (`logging/PLAN-audit-log-todo-2026-09-16.md` there). Kade chose:
**1.4 = option A** — the traffic notebook stays back to back in one window; per-phase isolation is
replaced on the verifier side by `step10` (tick-interval readout) + `step11` (replay of the raw tier-1
copy through the deployed Lua, 64 rows × 30 fields, 0 mismatches on 2026-09-16) + request-id lookups.
**Phase J goes in both the notebook and `make_traffic.drive()`.**

## Part 1 — `make_traffic.py` still waited with `lag=0.5`

MEMORY *Now* (session 14) had already flagged it: the session-13 fix reached the notebooks and never
`src/make_traffic.py`. Five `time.sleep(seconds_to_boundary(window_seconds, lag=0.5))` — in
`_grid_phase`, `_phase_commit`, `_phase_delete`, `_phase_grants`, `_phase_500` — so every CLI or
library drive fired each phase inside the report tick's blind spot (tick at `window_end + δ`,
δ ∈ [0, Interval_Sec), measured 3.673 s / 2.77 s / 1.765 s on three pods) and was booked one row early.

Changed:
- `drive(..., tick_interval_s=None, phase_lag=None)`. Driving without either raises `ContractError`;
  `dry_run` ignores both. Default lag `tick_interval_s + PHASE_LAG_MARGIN_S` (1.5).
- `phase_lag_for()` validates: lag must clear the tick interval and stay under half the window.
- `_wait_for_window()` is the ONLY boundary sleep; the five phase functions take `phase_lag`
  keyword-only.
- `run_traffic.py --tick-interval` (default 5, the 30/5 fast-run; 30 at 1800/30), like
  `--window-seconds`: the caller owns both numbers.
- Tests: refusal without a tick; default clears the tick; explicit lag inside the tick refused; lag
  eating half the window refused; a default-lag wait lands 5–15 s into a 30 s window; an AST test
  that fails on any literal `lag=` and on any boundary sleep outside `_wait_for_window`.

Verified: `pytest` 917 passed / 45 skipped (run in a VM venv outside the repo — the repo's `.venv`
points at the Mac's Python and cannot run in the Cowork VM); `black --check` clean. NOT run against
the cluster.
