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

## Part 2 — phase J: a table in a two-level namespace (local-k8s TODO 1.5)

Why: the shipper's v4 Lua keys a table row on the request path, and rebuilds the same key for commit
time from `Successfully committed to table cat.ns.child.table`, joining the middle levels with `%1F`.
That rebuild had only ever seen one-level namespaces. If it disagrees with the path, the commit lands on
a second row that no request touches — silently.

Added:
- `traffic_helpers.drive_nested_namespace(ic, run, catalog, parent_ns, schema, table_payload)` — six
  runner calls, each tagged: createNamespace `[parent, "nested"]`, createTable `mx_<run>_deep`,
  updateTable (commit), loadTable, dropTable, dropNamespace. The drops run even if an earlier step
  raised. Returns rows (make_traffic's row shape), `resource_key`
  (`/api/catalog/v1/<cat>/namespaces/<ns>%1Fnested/tables/mx_<run>_deep`), `path_encoded`, request ids.
- `nested_table_resource_key()`, `NESTED_CHILD`, and `__added_after_split__` — the re-export test guards
  names that MOVED from `log_coverage`; names born after the split are listed and excluded, and a test
  checks the list is real.
- `make_traffic`: phase `J` at the end of the `full` profile (`_phase_nested`, waits with the validated
  lag, records rows under phase J, writes `fixture.nested`). No new claim — that would bump
  `CONTRACT_VERSION`.
- `polaris_api_traffic_v1.ipynb`: cells 10b (markdown + code) before phase I, driven back to back with
  B–H; the summary prints J's request ids and the row to find. Existing outputs untouched.
- Tests (no network): `%1F` is what `requests` puts on the wire for the unit separator; six tagged calls
  in order and the tag cleared; the issued table path IS the resource key; drops still run when the
  commit raises; `full` ends with J.

Verified: `pytest` 923 passed / 45 skipped; `black --check` / isort clean; every notebook code cell
parses. **NOT run against the cluster** — the notebook's Restart & Run All and a `full` CLI drive are
Kade's; whether Polaris accepts a nested namespace in the probe catalog is therefore unmeasured.

## Result — run `1789535345` (2026-09-16 05:09:42Z)

Notebook Restart & Run All by Kade. Phase J: createNamespace 200, createTable 200, updateTable 200,
loadTable 200, dropTable 204, dropNamespace 204 — every path after the first carried `probe_ns%1Fnested`.
local-k8s (`step10` + `step11` on window 05:09:30Z): **one** table row, requests 3, commit_count 2
(24 + 12 ms), no dotted phantom; replay 67 rows × 30 fields, 0 mismatches. Measured, not asserted.
