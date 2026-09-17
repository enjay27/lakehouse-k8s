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
- `polaris_replica_staleness.ipynb` — **the only notebook here that changes server state.** Answers whether a read through Pgpool-II can miss a write made on another connection, by pausing WAL replay on every standby and then reading from 12 brand-new pooled sessions. Settles the database half of `local-k8s` `active-issues.md` #15 (create-namespace 500s) without involving Polaris. Carries `require_not_prod()` **and** a hard `ENV == "local"` assertion, because `dev` is shared and pausing replay there would degrade other people's reads. Has a standalone PANIC cell that resumes replay after an interrupted run. Needs `kubectl` with the context on `orbstack`.

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
All six now bootstrap `../src` and call `init_env("local")` — no hardcoded endpoints or credentials. Polaris/MinIO settings come from `init_env`; the PostgreSQL ones (`metastore`, `configuration`, `entities`) use the `PG_URL` / `PG_CONFIG` globals (`src/config/<env>.yaml` → `postgres_*`, password overridable via `POSTGRES_PASSWORD`). Switch environments with `init_env("dev")`.

## Reference reports
- `doc-shm-exhaustion-test-plan.md` — plain Postgres `/dev/shm` exhaustion reproduction (Docker + OrbStack K8s), tied to a production incident. Not a notebook and not wired to `src`/`init_env` — it's raw Docker/psql/K8s, run manually on the host and outside this repo's Polaris-testing model. Docker leg executed and verified 2026-07-09 (results in §10); OrbStack K8s leg still pending.
