# Service Testing & Verification Rules

## Tech Stack
- **Language:** Python 3.11+
- **Testing Runtimes:** Jupyter Notebooks (`.ipynb`), pytest
- **Core Integrations:** Apache Polaris (v1.3.0-incubating API), PostgreSQL HA (via **Pgpool-II** pool — NOT PgBouncer; corrected 2026-08-20), OpenSearch (v1.5.0)
- **Core Libraries:** pandas, numpy, requests, psycopg2, sqlalchemy, matplotlib, seaborn

## Repository Layout
- **`src/`** — all reusable Python modules imported by notebooks (`polaris_test_utils.py`, `minio_rest.py`). No test logic lives in notebooks that belongs in a module.
- **`src/config/`** — environment config. `common.yaml` (shared non-secret defaults) + `<env>.yaml` (per-env: `local` / `dev` / `prod`) are merged by `init_env(env)`. Secrets may be overridden by env vars (`POLARIS_ROOT_SECRET`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `OPENSEARCH_PASS`, `POSTGRES_PASSWORD`). `init_env` also exposes PostgreSQL globals (`PG_URL`, `PG_CONFIG`, `PG_HOST`…) for the diagnostics notebooks. `*.yaml` here is gitignored except `common.yaml` and `*.example.yaml`; each env ships a `*.example.yaml` template — copy e.g. `dev.example.yaml` → `dev.yaml` and fill in.
- **Per-test directories** — each test domain has its own folder containing its notebook(s) plus a `README.md` (concept / purpose / how-to-run / result) and any `doc-*.md` reference reports:
  - `lifecycle/` — catalog→namespace→table/view→snapshot→drop lifecycle.
  - `privilege/` — minimum-privilege matrix tests.
  - `rbac/` — RBAC wiring verification + role-graph visualization.
  - `purge/` — purge → MinIO file-deletion behavior.
  - `etl/` — data ingestion / end-to-end flow.
  - `diagnostics/` — read/inspect notebooks (config, metastore, data layers, entities, API deps).
  - `scenario/` — composite end-to-end production scenario.
  - `availability/` — read-only health checks; the **only** suite safe to run against PROD.
  - `error-cases/` — negative tests that provoke and assert specific failures (401/403/404/409/500/503…).
  - `admin/` — destructive teardown / clean-all + credential rotation utilities.
- **`attic/`** — superseded duplicates / backups parked for deletion; not part of the active suite.
- **`datahub-error-cases/`** — separate product (DataHub), its own `datahub_test_utils.py`; intentionally left outside the Polaris `src/` model.
- **Self-contained notebooks (remaining):** `rbac/polaris_rbac_graph.ipynb` and `scenario/polaris_production_scenario.ipynb` still hardcode endpoints/creds — they target a different realm (`DATACORP-PROD`) and were intentionally left as-is (tracked in `MEMORY.md`). `admin/polaris_clean_all.ipynb` stays hardcoded to localhost **by design**. Everything else (`diagnostics/`, `etl/`, `rbac/` verification + test) uses `init_env`/`src`.
- **Notebook import convention:** the first cell bootstraps `src/` onto the path before importing:
  ```python
  import sys, pathlib
  sys.path.insert(0, str(pathlib.Path.cwd().parent / "src"))
  from polaris_test_utils import *
  init_env("local")             # default is "local"; switch to "dev"/"prod" for shared clusters
  require_not_prod("…")         # mutating notebooks: hard-fail against company PROD
  ```

## Environments & Test Flow
Tests run across three **distinct** environments whose connection settings and secrets are **totally different** — never assume one environment's variables apply to another. Each is selected with `init_env(<env>)`, which loads a separate `src/config/<env>.yaml` (+ env-var secret overrides). The default (bare `import *` / `init_env()` with no arg) is **`local`** — the safe target.

1. **`local`** — personal OrbStack single-node (`src/config/local.yaml`, gitignored). The full test suite runs here, plus the destructive local-only utilities in `admin/`. This is the default env.
2. **`dev`** — shared **company** DEV cluster (`src/config/dev.yaml`, gitignored; copy from `dev.example.yaml`). Endpoints/secrets are totally different from `local`. Run functional / integration suites here, but **never** destructive teardown — it would delete other users' data.
3. **`prod`** — shared **company** PROD (`src/config/prod.yaml`, from `prod.example.yaml`). **Availability tests only.** Do not run lifecycle, privilege, purge, or any mutating / teardown notebook against PROD.

Rules:
- Secrets for the shared (`dev`/`prod`) environments come from env vars and are never committed; only `common.yaml` and `*.example.yaml` are tracked. Each env has a `*.example.yaml` template.
- Mutating notebooks call `require_not_prod(...)` right after setup so they hard-fail against `prod`; PROD is restricted to the availability suite.
- `admin/` teardown notebooks are **`local`-only** and hardcoded to localhost by design (see `admin/README.md`), with an `assert`-based host guard that refuses any non-local `POLARIS_URL`; they are never pointed at a shared environment, and must **not** be wired to `init_env()`.

## Environment Commands
*Always execute commands within your active local virtual environment (`.venv`); dependencies are managed with `uv` (`pyproject.toml` / `uv.lock`).*
- **Install Dependencies:** `uv sync`  (add a package: `uv add <pkg>`)
- **Run Functional Assertions:** `pytest`  (notebook suites: `Restart & Run All`)
- **Enforce Linting & Style:** `black . && isort .`

## Jupyter Notebook Best Practices
- **Linear Execution Required:** Every visualization and integration notebook must execute cleanly from top to bottom (`Restart & Run All`) without out-of-order cell dependencies.
- **Strict Logic Separation:** Keep notebooks dedicated strictly to visualization, token verification mapping, table printing, and test summaries. Core connectivity code, OAuth engines, and query execution blocks must live in reusable `.py` scripts inside `src/` and be imported into notebooks.
- **Connection Disposal:** You MUST explicitly close database cursors, clients, and active connection pools (`pool.close()` or `engine.dispose()`) inside a dedicated cleanup/teardown cell at the end of every notebook to avoid overloading the local Pgpool-II pooler.
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
4. **Commit the task as one versioned change, automatically** — see *Version Control* below. Claude runs the commit itself as the last step of the task, without being asked. A task is not done until it is in git; an uncommitted finding lives only in a chat transcript.

## Version Control

**One task, one commit.** After each completed unit of work — a plan carried out,
a bug found and fixed, a measurement taken and reported — the change gets
committed. Not per file edit, and not batched across unrelated tasks: the unit is
the thing you would describe to someone in a sentence.

This matters here more than in most repos. The work is *findings*, and a finding
that only exists in a chat transcript is lost the moment the session ends. The
commit is where it becomes durable and attributable to the state of the code that
produced it.

### The gate: DoD first, commit second

Never commit a state you have not verified. In order:

```bash
black .            # black LAST if you also run isort -- no [tool.isort] profile is set
pytest
git add -A && git commit
```

A commit whose tests were not run is a commit someone will later have to bisect.

### Message style

Follow what is already in `git log`. The subject line states **the finding or the
point of the change**, not the files touched:

```
The sweep was measuring root, and root is the least representative identity
reset_realm.sh: TRUNCATE via -c, not a heredoc -- kubectl exec drops stdin
```

not `update api_sweep.py` or `fix bug`.

The body carries what a reader six months out will need and cannot reconstruct:

- **what was measured or changed**, with the numbers;
- **why**, especially when the change corrects an earlier belief — say what the
  old belief was and what cost it;
- **what is verified vs still open**, so the next session does not re-establish
  what is settled or trust what is not.

Prefer the honest correction to the tidy summary. `MEMORY.md` and any
`PLAN-*.md` / `HANDOFF-*.md` touched by the task belong in the SAME commit as
the code — they are the reasoning behind it, and they go stale the instant they
are committed separately.

### Never commit

- Secrets. `src/config/<env>.yaml`, real tokens, principal secrets, the seed
  ledger's credentials. Only `common.yaml` and `*.example.yaml` are tracked.
- Capture directories (`capture*/`, `*.log`) — they run to hundreds of MB and are
  already gitignored per-directory. Check `git status` before `-A`, never after.
- A broken or half-formatted tree, to "save progress". Use a branch instead.

### Who runs it — Claude commits, automatically

**Every completed unit of work is committed by Claude, without being asked.**
The developer must be able to open `git log` and see the session's reasoning as
a sequence of revisions; a finding that sits uncommitted at the end of a session
is a finding that only exists in a chat transcript. So the commit is not a
closing formality Claude offers to perform — it is the last step of the task,
run as soon as the DoD gate above is green.

- **One task, one commit** — the rule above still holds. Auto-commit means
  Claude does not wait to be told; it does **not** mean a commit per file edit.
- **The gate is not skippable.** `pytest` green before `git commit`, always. If
  the gate cannot be run at all (no venv, no network), commit anyway so the work
  is traceable, and say so **in the commit body** — `NOT VERIFIED: pytest could
  not be run, <reason>` — so the next session knows not to trust the tree.
- **`git push` is still Kade's.** Auto-commit is local history; publishing is a
  separate decision.
- **Commit before a risky step**, not only after a finished one. An
  index toggle, a realm reset, a TRUNCATE — get the tree committed first so the
  before-state is recoverable.

**The lock blocker is resolved (2026-08-31).** The mount could create files under
`.git/` but not unlink them, so every `git commit` left a stale
`.git/index.lock` that blocked the next write — measured 2026-08-24, and it is
why this section previously said Kade ran the commits. The cause was the mount's
delete permission, not git: with deletion granted for this folder, `git add` /
`git commit` complete cleanly and remove their own locks. If a session ever
finds `git` failing on `index.lock` again, the fix is to re-grant delete
permission on the repo folder, not to hand the commit back.

Identity: this repo has no `user.name` / `user.email` in its local config and
the mount does not see Kade's global one, so Claude commits with
`git -c user.name=... -c user.email=...` rather than writing an identity into
`.git/config`.
