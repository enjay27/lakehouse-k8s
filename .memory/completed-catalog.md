# Completed structural work

Finished and not expected to change. Kept out of the roadmap so the roadmap
stays a list of what is live.

- [x] **Refactor pass 1 (2026-06-30):** migrated the canonical `purge-practice/refactor/` set into the `src/` + per-domain structure above (via `git mv`). Added per-dir READMEs. Notebooks now bootstrap `src/`. Fixed a latent bug where `common.yaml` lived outside `config/` and was never loaded.
- [x] **Refactor pass 2 (2026-06-30):** migrated `test/`, `notebooks/`, `error-cases/`, and `purge-practice/` root into the new categories (`availability/`, `rbac/`, `diagnostics/`, `etl/`, `scenario/` + existing dirs). Consolidated all Polaris suites onto `src/` (3 dup util copies → `attic/`; confirmed `src/` is a superset of their APIs). Repointed 25 utils-importing notebooks to `src/` with `require_not_prod()` guards (availability excluded — PROD-safe). Wrote READMEs for the new categories. DataHub left untouched.

