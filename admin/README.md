# Admin / Teardown Utilities

## Concept
Operational maintenance notebooks for resetting a Polaris instance to a clean slate — distinct from the assertion-style test suites in the other directories.

## Purpose
Provide a safe, ordered teardown that drops all tables/views, namespaces, catalogs, principals, principal roles, and catalog roles, so a test environment can be reset between runs.

## Notebooks
- `polaris_clean_all.ipynb` — previews everything that will be deleted, then deletes in dependency order (enables `drop-with-purge.enabled=true` first so drops aren't blocked by the config gate).

## How to run
1. **Read the preview cell output before proceeding** — this notebook is destructive.
2. **Restart & Run All** only against an environment you intend to wipe.

## ⚠️ Scope & safety — LOCAL DEVICE ONLY (do NOT refactor onto shared config)
`polaris_clean_all.ipynb` is intentionally **self-contained and hardcoded to the local device** (`POLARIS_URL=http://192.168.139.2:8181`, local `client_secret`). This is **deliberate, not a gap**:

- It is **never** run against the company DEV or PROD environment. It exists purely to reset the local OrbStack instance.
- It is **fully destructive**: it deletes *all* catalogs, namespaces, principals, and roles. In a shared environment that would wipe **other users' data**.
- It must therefore **not** be wired to `init_env()` / `src/config/`. Hardcoding to localhost is a safety feature — it cannot be repointed at a shared cluster by switching an env file.

**Before running, confirm the target host is your local device. Never change the URL to a DEV/PROD host.**
