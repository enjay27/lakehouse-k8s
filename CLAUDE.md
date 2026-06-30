# Service Testing & Verification Rules

## Tech Stack
- **Language:** Python 3.11+
- **Testing Runtimes:** Jupyter Notebooks (`.ipynb`), pytest
- **Core Integrations:** Apache Polaris (v1.3.0-incubating API), PostgreSQL HA (via PgBouncer pool), OpenSearch (v1.5.0)
- **Core Libraries:** pandas, numpy, requests, psycopg2, sqlalchemy, matplotlib, seaborn

## Repository Layout
- **`src/`** — all reusable Python modules imported by notebooks (`polaris_test_utils.py`, `minio_rest.py`). No test logic lives in notebooks that belongs in a module.
- **`src/config/`** — environment config. `common.yaml` (shared non-secret defaults) + `<env>.yaml` (per-env, e.g. `dev.yaml`) are merged by `init_env(env)`. Secrets may be overridden by env vars (`POLARIS_ROOT_SECRET`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `OPENSEARCH_PASS`). `*.yaml` here is gitignored except `common.yaml` and `*.example.yaml`; copy `prod.example.yaml` → `prod.yaml` and fill in.
- **Per-test directories** — each test domain has its own folder containing its notebook(s) plus a `README.md` (concept / purpose / how-to-run / result) and any `doc-*.md` reference reports:
  - `lifecycle/` — catalog→namespace→table/view→snapshot→drop lifecycle.
  - `privilege/` — RBAC privilege-matrix tests.
  - `purge/` — purge → MinIO file-deletion behavior.
  - `admin/` — destructive teardown / clean-all utilities.
- **Notebook import convention:** the first cell bootstraps `src/` onto the path before importing:
  ```python
  import sys, pathlib
  sys.path.insert(0, str(pathlib.Path.cwd().parent / "src"))
  from polaris_test_utils import *
  init_env("dev")   # switch env here: "dev" → "prod"
  ```

## Environments & Test Flow
Tests run across three **distinct** environments whose connection settings and secrets are **totally different** — never assume one environment's variables apply to another. Each is selected with `init_env(<env>)`, which loads a separate `src/config/<env>.yaml` (+ env-var secret overrides).

1. **Local device** — personal OrbStack single-node. The full test suite runs here, plus the destructive local-only utilities in `admin/`. (Currently `src/config/dev.yaml` targets this local device.)
2. **Company DEV** — shared team environment with its own endpoints and credentials (injected via env vars / its own `<env>.yaml`). Run functional / integration suites here, but **never** destructive teardown — it would delete other users' data.
3. **Company PROD** — **availability tests only.** Do not run lifecycle, privilege, purge, or any mutating / teardown notebook against PROD.

Rules:
- Secrets for the shared (DEV/PROD) environments come from env vars and are never committed; only `common.yaml` and `*.example.yaml` are tracked.
- `admin/` teardown notebooks are **local-device only** and hardcoded to localhost by design (see `admin/README.md`); they are never pointed at a shared environment.
- Gate mutating tests so they refuse to run against PROD (e.g. `require_not_prod()`); PROD is restricted to the availability suite.

## Environment Commands
*Always execute commands within your active local virtual environment (`.venv`); dependencies are managed with `uv` (`pyproject.toml` / `uv.lock`).*
- **Install Dependencies:** `uv sync`  (add a package: `uv add <pkg>`)
- **Run Functional Assertions:** `pytest`  (notebook suites: `Restart & Run All`)
- **Enforce Linting & Style:** `black . && isort .`

## Jupyter Notebook Best Practices
- **Linear Execution Required:** Every visualization and integration notebook must execute cleanly from top to bottom (`Restart & Run All`) without out-of-order cell dependencies.
- **Strict Logic Separation:** Keep notebooks dedicated strictly to visualization, token verification mapping, table printing, and test summaries. Core connectivity code, OAuth engines, and query execution blocks must live in reusable `.py` scripts inside `src/` and be imported into notebooks.
- **Connection Disposal:** You MUST explicitly close database cursors, clients, and active connection pools (`pool.close()` or `engine.dispose()`) inside a dedicated cleanup/teardown cell at the end of every notebook to avoid overloading the local PgBouncer pooler.
- **Memory Release:** Explicitly drop massive retrieved dataframes (`del df`) and trigger garbage collection (`import gc; gc.collect()`) after rendering visual diagnostic tables.

## Tool Interaction Guardrails (CRITICAL)
- **Strict Plan-First Mode:** You are forbidden from modifying python modules, changing notebook cell structures, or generating test configurations on your first turn. Propose a clear textual testing strategy first and wait for explicit developer sign-off.
- **Zero Hardcoded Credentials:** Never write plain-text administrative tokens, database passwords, or cluster keys into notebook cells or modules. Load them via `init_env()` from `src/config/<env>.yaml` (gitignored) or override from `os.environ`. Config files holding real secrets must stay gitignored.
- **Auto-Correction Restraint:** You are authorized to run local python tests natively to check your code. If minor validation exceptions occur, you may self-correct a maximum of 2 times before halting to request manual engineering feedback.

## Definition of Done (DoD)
Before marking any verification task as complete:
1. Ensure all test notebook cells run sequentially with zero runtime or compilation errors.
2. Format all newly updated Python logic modules using `black . && isort .`.
3. Document the successful endpoints, data table definitions, and security authority states inside `MEMORY.md`.