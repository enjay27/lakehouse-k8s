---
description: Strip credentials and volatile output from a notebook before commit
---
Sanitize the notebook(s) named in $ARGUMENTS before they are committed.

1. **Credentials.** No plaintext principal secret, `clientSecret`, root secret,
   MinIO key or database password may appear in a cell or in stored output.
   Load them via `init_env()` from `src/config/<env>.yaml` (gitignored) or from
   `os.environ`. Known offenders to check first: `notebooks/availability/` cell
   2 and `diagnostics/ladders/api-sql-profile/03_api_index_matrix.ipynb`.
2. **Hardcoded endpoints.** Flag any notebook outside the known-exempt set
   (`notebooks/rbac/polaris_rbac_graph.ipynb`,
   `notebooks/scenario/polaris_production_scenario.ipynb`,
   `notebooks/admin/polaris_clean_all.ipynb`) that does not bootstrap through
   `init_env`.
3. **Guards.** A mutating notebook must call `require_not_prod(...)` right
   after setup. An `admin/` teardown notebook must keep its assert-based
   localhost host guard and must NOT be wired to `init_env()`.
4. **Teardown.** Confirm a final cleanup cell closes cursors, clients and pools
   (`pool.close()` / `engine.dispose()`) and drops large frames (`del df`;
   `gc.collect()`).
5. Report what you changed per notebook. Do not clear outputs that a committed
   finding cites as evidence.
