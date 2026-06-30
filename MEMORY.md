# Active Service Testing State

## Current Context & Objective
- **Goal:** Build robust diagnostic / verification notebooks for the local platform services in the `datahub-hynix` namespace (Apache Polaris 1.3.0, PostgreSQL HA via PgBouncer, MinIO, OpenSearch 1.5.0).
- **Structure model (current):** reusable Python in `src/`; each test domain is its own directory holding notebook(s) + a `README.md` + `doc-*.md` reports. Notebooks bootstrap `src/` onto `sys.path` and call `init_env(env)` for config.

## Repository Map
- `src/polaris_test_utils.py`, `src/minio_rest.py` — shared modules.
- `src/config/` — `common.yaml` + `<env>.yaml` (merged by `init_env`); secrets via env vars. `dev.yaml`/`prod.yaml` gitignored.
- `lifecycle/` — entity lifecycle (`polaris_lifecycle_practice.ipynb`).
- `privilege/` — RBAC privilege matrix (`polaris_privilege_matrix_test.ipynb`).
- `purge/` — purge → MinIO behavior (`view_purge_behavior_test.ipynb`, `prove_minio_deletion_no_sts.ipynb`).
- `admin/` — teardown (`polaris_clean_all.ipynb`).

## Completed
- [x] **Refactor pass 1 (2026-06-30):** migrated the canonical `purge-practice/refactor/` set into the `src/` + per-domain structure above (via `git mv`). Added per-dir READMEs. Notebooks now bootstrap `src/`. Fixed a latent bug where `common.yaml` lived outside `config/` and was never loaded.

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
