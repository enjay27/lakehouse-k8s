# Production Scenario

## Concept
A composite, end-to-end "day in the life" scenario that strings together realistic Polaris operations (catalog/namespace/table setup, data writes, role/grant flows) to mimic production usage.

## Purpose
Exercise the system the way a real workload would, surfacing integration issues that isolated unit-style tests miss.

## Notebooks
- `polaris_production_scenario.ipynb` — the composite scenario walkthrough.

## How to run
**Restart & Run All** against `local` (or company `dev`). Despite the name, this is a *scenario simulation* — **not** intended for company PROD.

## Migration note
Migrated self-contained (hardcoded local endpoint). Porting onto `init_env`/`../src` — and adding a `require_not_prod()` guard once it imports the utils — is tracked in `MEMORY.md`.
