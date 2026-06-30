# Active Service Testing State

## Current Context & Objective
- **Goal:** Build robust diagnostic / verification notebooks for the local platform services in the `datahub-hynix` namespace (Apache Polaris 1.3.0, PostgreSQL HA via PgBouncer, MinIO, OpenSearch 1.5.0).
- **Structure model (current):** reusable Python in `src/`; each test domain is its own directory holding notebook(s) + a `README.md` + `doc-*.md` reports. Notebooks bootstrap `src/` onto `sys.path` and call `init_env(env)` for config.

## Repository Map
- `src/polaris_test_utils.py`, `src/minio_rest.py` — shared modules.
- `src/config/` — `common.yaml` + `<env>.yaml` (merged by `init_env`); secrets via env vars. `dev.yaml`/`prod.yaml` gitignored.
- `lifecycle/` — entity lifecycle. `privilege/` — min-privilege matrix. `rbac/` — RBAC verify + role graph.
- `purge/` — purge→MinIO (purge_practice, view_purge, prove_minio). `etl/` — ingestion/flow. `diagnostics/` — config/metastore/data_layers/entities/api_deps.
- `scenario/` — composite scenario. `availability/` — read-only checks (**PROD-safe**). `error-cases/` — 21 negative tests. `admin/` — teardown + rotate_credential.
- `attic/` — superseded dups/backups (delete on host). `datahub-error-cases/` — separate product, left untouched (will move to a datahub root later).

## Completed
- [x] **Refactor pass 1 (2026-06-30):** migrated the canonical `purge-practice/refactor/` set into the `src/` + per-domain structure above (via `git mv`). Added per-dir READMEs. Notebooks now bootstrap `src/`. Fixed a latent bug where `common.yaml` lived outside `config/` and was never loaded.
- [x] **Refactor pass 2 (2026-06-30):** migrated `test/`, `notebooks/`, `error-cases/`, and `purge-practice/` root into the new categories (`availability/`, `rbac/`, `diagnostics/`, `etl/`, `scenario/` + existing dirs). Consolidated all Polaris suites onto `src/` (3 dup util copies → `attic/`; confirmed `src/` is a superset of their APIs). Repointed 25 utils-importing notebooks to `src/` with `require_not_prod()` guards (availability excluded — PROD-safe). Wrote READMEs for the new categories. DataHub left untouched.

## Environments & Test Flow (do not conflate)
Three environments, totally different connection vars/secrets, selected via `init_env(<env>)`. Default = **`local`** (safe):
1. **`local`** — personal OrbStack; full suite + destructive `admin/` utilities. `src/config/local.yaml` (gitignored).
2. **`dev`** — shared **company** DEV; functional/integration suites only. NEVER destructive teardown (wipes other users' data). `src/config/dev.yaml` from `dev.example.yaml`.
3. **`prod`** — shared **company** PROD; **availability tests ONLY.** No lifecycle/privilege/purge/mutating notebooks. From `prod.example.yaml`.
Enforcement now in place: module default env = `local`; mutating notebooks call `require_not_prod(...)`; `admin/polaris_clean_all.ipynb` is **intentionally** hardcoded to localhost + has an `assert` host guard (a safety feature) — do NOT port it onto `init_env`/shared config.

## Active State & Roadmap
- [ ] **Pass 2 — migrate remaining suites** into the new structure (after sign-off): `purge-practice/` root duplicates, `notebooks/`, `test/` (availability/etl/rbac), `error-cases/`, `datahub-error-cases/`.
- [x] **Config naming (done 2026-06-30)** — renamed `dev.yaml` → `local.yaml`; added `local.example.yaml` + company `dev.example.yaml` (+ existing `prod.example.yaml`); module default env flipped `dev` → `local`; notebooks now `init_env("local")`.
- [x] **PROD guardrail (done 2026-06-30)** — mutating notebooks (lifecycle/privilege/purge) call `require_not_prod(...)`; `clean_all` has a localhost `assert` guard. TODO refinement: a positive availability-only allowlist for any future PROD notebook.
- [ ] **Company DEV/PROD configs** — copy `dev.example.yaml`/`prod.example.yaml` → real (gitignored) `dev.yaml`/`prod.yaml` with company endpoints; inject secrets via env vars only.
- [x] **Port self-contained notebooks (done 2026-06-30)** — refactored the 7 POLARIS-realm notebooks (`diagnostics/{api_dependency,configuration,data_layers,entities,metastore}`, `rbac/polaris_rbac_verification`, `etl/polaris_insert_data`) onto `src`/`init_env`; removed all hardcoded URL/realm/`polaris-secret`/MinIO/PG literals. Added **PostgreSQL config support**: `postgres_*` keys in yaml + `PG_URL`/`PG_CONFIG`/`PG_*` globals in `init_env` (password via `POSTGRES_PASSWORD`). `etl/polaris_insert_data` got `require_not_prod()`. Static-verified (all cells parse, no residual secrets); **not yet run against live Polaris**.
- [ ] **Reconcile DATACORP-PROD notebooks** — `rbac/polaris_rbac_graph.ipynb` + `scenario/polaris_production_scenario.ipynb` use `REALM=DATACORP-PROD` / `datacorp-secret`, left hardcoded by decision. Decide whether DATACORP-PROD is a real env (→ add a config) or fold onto local realm.
- [ ] **Live-verify the ported notebooks** — run each against a local Polaris+PG (Restart & Run All) to confirm the `init_env`/`PG_*` wiring; the refactor was static-checked only.
- [ ] **`admin/polaris_clean_all`** stays hardcoded to localhost by design (not a port target).
- [ ] **Delete `attic/` on host** — superseded dups/backups (sandbox couldn't hard-delete).
- [ ] **Move DataHub out** — relocate `datahub-error-cases/` to its own datahub root later (per owner).
- [ ] **Authority test notebook** — assert RBAC + OAuth tokens against the Polaris catalog API (build on `privilege/` harness).
- [ ] **PgBouncer connection verifier** in `src/` — loop tests against the pool endpoint for connection isolation.
- [ ] **Schema/table mapping notebook** — audit table existence, row distributions, structural schemas across the PostgreSQL HA nodes.
- [ ] **OpenSearch indexing telemetry checker** (v1.5.0) — confirm pipeline sync.

## Active Issues & Blockers
- **Secret untracking pending (action required):** `src/config/dev.yaml` contains plaintext secrets and is still staged in git. It is now gitignored, but the existing index entry must be removed manually:
  `rm -f .git/index.lock && git rm --cached src/config/dev.yaml`
  (The sandbox could not clear a stale `.git/index.lock` — run this from the host shell.)
- `purge/prove_minio_deletion_no_sts.ipynb` uses `s3fs`; prefer `src/minio_rest.py` (s3fs disallowed by policy) for new work.
- **Network assumption:** Polaris `8181`, PgBouncer `5432`, OpenSearch `9200` must be port-forwarded from `datahub-hynix` to the host as configured in `src/config/dev.yaml`.
- Purge behavior on this build orphans MinIO files (issue #379); `dev.yaml: purge_deletes_files: false`.

---
*Note to Claude: Keep this tracking context under 150 lines. Move historical telemetry summaries to ARCHIVE.md when complete.*
