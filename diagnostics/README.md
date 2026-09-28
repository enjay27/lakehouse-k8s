# Diagnostics

## Concept
Read/inspect notebooks that surface the internal state of Polaris and its backing stores (with one deliberate exception, `polaris_replica_staleness.ipynb`, which provokes a condition rather than only observing one) — configuration, metastore (PostgreSQL), data layers (MinIO), entity inventory, and API dependency relationships.

## Purpose
Provide visibility for debugging and verification: what catalogs/namespaces/entities exist, how config is set, how the metastore and storage layers map to catalog records, and which API calls depend on which.

## Notebooks
- `polaris_configuration.ipynb` — Polaris configuration inspection.
- `polaris_metastore.ipynb` — PostgreSQL metastore inspection.
- `polaris_data_layers.ipynb` — MinIO / storage-layer mapping.
- `polaris_entities.ipynb` — catalog/namespace/table/view inventory.
- `polaris_api_dependency_test.ipynb` — API call dependency mapping.
- `polaris_replica_staleness.ipynb` — **the only notebook here that changes server state**, on both PostgreSQL and Polaris. Pauses WAL replay on every standby, then measures two things: whether a pooled read through Pgpool-II misses a committed write (the *mechanism*), and whether the `local-k8s` #15 ladder — 3 brand-new catalogs, first namespace in each — returns 500 while replication is stale, with a control run against healthy replication (the *symptom*). Routing is read from Pgpool's own `select_cnt` counters, never from a function inside the measured query; §2b hard-fails unless `SHOW pool_nodes` answers, so the notebook cannot report "no load balancing" when it was never talking to Pgpool. Creates and tears down its own catalogs. `require_not_prod()` **plus** a hard `ENV == "local"` assert, because `dev` is shared. Standalone PANIC cell resumes replay after an interrupted run. Needs `kubectl` with the context on `orbstack`.

## Scripts
- `probe_auth_mode.py` — **read-only** probe answering "who mints the token Polaris accepts?" (internal token broker vs. external IdP/Keycloak), plus measured TTL, whether a `refresh_token` is issued for `client_credentials`, which grants the issuer advertises (notably token-exchange), and — with `--expiry-check` — whether expiry is actually *enforced*. Step 0 of the Spark token-TTL / auto-refresh investigation (Lakehouse Stage 1); lives here rather than in the lakehouse project because it establishes a Polaris **service** fact, not a Spark one.

## How to run
**Notebooks:** Restart & Run All. Linear execution; close DB cursors/pools in the teardown cell.

**`probe_auth_mode.py`** (from the repo root, inside `.venv`):
```bash
python diagnostics/probe_auth_mode.py                 # default env=local
python diagnostics/probe_auth_mode.py --expiry-check  # only after TTL is lowered
# probing an external IdP directly:
export PROBE_CLIENT_SECRET=...                        # never on the command line
python diagnostics/probe_auth_mode.py --no-realm-header \
  --token-endpoint https://<keycloak>/realms/<realm>/protocol/openid-connect/token \
  --client-id <spark client>
```
Creates nothing and changes no server config, so it carries no `require_not_prod()` guard — same posture as `availability/`.

## Configuration
Every notebook here walks up from its own directory to the repo root, puts `src/` on `sys.path` (gated by `tests/test_notebook_bootstrap.py`) and calls `init_env("local")` — no hardcoded endpoints or credentials. Polaris/MinIO settings come from `init_env`; the PostgreSQL ones (`metastore`, `configuration`, `entities`) use the `PG_URL` / `PG_CONFIG` globals (`src/config/<env>.yaml` → `postgres_*`, password overridable via `POSTGRES_PASSWORD`). Switch environments with `init_env("dev")`.

## Reference reports
- `doc-shm-exhaustion-test-plan.md` — plain Postgres `/dev/shm` exhaustion reproduction (Docker + OrbStack K8s), tied to a production incident. Not a notebook and not wired to `src`/`init_env` — it's raw Docker/psql/K8s, run manually on the host and outside this repo's Polaris-testing model. Docker leg executed and verified 2026-07-09 (results in §10); OrbStack K8s leg still pending.
