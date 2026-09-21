# Availability Tests

## Concept
Lightweight, **read-only** health/availability checks against the Polaris catalog API and its backing services — the one suite that is safe to run against **any** environment, including company PROD.

## Purpose
Confirm the service is up and responding (token issuance, catalog listing, basic reachability) without mutating any state.

## Notebooks
- `polaris_availability_test.ipynb` — availability assertions via `../src/polaris_test_utils.py`.

## How to run
1. **Restart & Run All.** The first cell bootstraps `../src` and imports the utils.
2. Select the target with `init_env(...)`: `local` (default), `dev`, or `prod`.

## ⚠️ PROD note
This is the **only** suite intended to run against PROD. It is deliberately **not** wrapped in `require_not_prod()` (that guard is for mutating suites). Keep it read-only — do not add create/drop/grant calls here, or it loses its PROD-safe status.
