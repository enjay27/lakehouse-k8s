# RBAC Tests & Visualization

## Concept
Role-based access control for Polaris: principals → principal roles → catalog roles → grants. This suite both **verifies** RBAC wiring and **visualizes** the role graph.

## Purpose
Validate that role assignments and grants resolve as intended, and render the relationships for inspection. Complements `privilege/`, which measures the minimum privilege per action; this dir focuses on the role/assignment graph itself.

## Notebooks
- `polaris_rbac_test.ipynb` — RBAC assertions via `../src/polaris_test_utils.py`.
- `polaris_rbac_verification.ipynb` — verifies principal/role/grant wiring.
- `polaris_rbac_graph.ipynb` — builds an interactive role graph; renders `polaris_rbac_graph.html` (uses `lib/` vis-network assets).

## How to run
1. **Restart & Run All.** Notebooks that import utils bootstrap `../src` in their first cell and call `require_not_prod(...)`.
2. Open `polaris_rbac_graph.html` in a browser to view the rendered graph (keep `lib/` alongside it).

## Notes
`polaris_rbac_test.ipynb` and `polaris_rbac_verification.ipynb` use `../src` + `init_env` (no hardcoded creds; verification also uses the `PG_*` globals). **`polaris_rbac_graph.ipynb` is intentionally left self-contained** — it targets a different realm (`DATACORP-PROD` / its own secret), so it was not folded onto the local `init_env` config. Reconciling it is tracked in `MEMORY.md`.
