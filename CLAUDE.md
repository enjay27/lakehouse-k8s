# Agent Operating Rules — lakehouse-k8s

One repo, two halves that were two repos until 2026-09-21: the **platform**
that builds the cluster, and the **suite** that measures it. The split cost
real money in drift (see `docs/MERGE-2026-09-21.md`), so the rule is now:
a fact and the thing it describes go in the same commit.

**Which half you are in decides which Definition of Done applies.** That is the
single most important thing on this page.

| tree | half | DoD gate |
|---|---|---|
| `charts/` `releases/` `logging/` `schema/` `runbooks/` | platform | `helm lint` + `--dry-run=client --debug` |
| `src/` `tests/` `notebooks/` `diagnostics/` | suite | `pytest` + `isort . && black .` |

---

## Tech Stack

### Platform
- **Orchestration:** Local Kubernetes (OrbStack, context `orbstack`) via **Helm 4** — *not* 3.x.
  Helm 4 defaults to **server-side apply**, so field-manager conflicts are a failure mode Helm 3
  did not have. Confirm with `helm version`.
- **Target Namespace:** `datahub-hynix` — **strictly enforced for every K8s asset, no exception**
  as of 2026-09-18. The `logging` namespace is empty and nothing belongs there.
- **Apache Polaris (Iceberg REST catalog):** local chart, **1.6.0**, deployed and verified
  2026-09-18 (metastore schema v4, plural `event-listener.types`). Management port **8182**,
  not the 8282 upstream docs default to.
- **PostgreSQL HA:** umbrella chart wrapping Bitnami `postgresql-ha` 16.3.2 — 3 replicas +
  **Pgpool-II** connection pooler (**not** PgBouncer).
- **MinIO:** local chart — S3 for the Iceberg warehouse (`data-catalog-bucket`) and Argo artifacts.
- **Fluent Bit:** one release, the DaemonSet `benchmarks-fluent-bit`, tailing
  `/var/log/containers/*.log` into **OpenSearch** in three tiers — tier 1 `k8s-logs-*`,
  tier 2 `polaris-logs-*`, tier 3 `polaris-report-*` (**schema v6**) — from Polaris's stdout.
  **As of 2026-09-27 Polaris also writes a JSON log file per pod**, `polaris-<pod>.log`,
  rolled hourly (KST) to `.yyyy-MM-dd-HH.gz` on PVC `polaris-logs-pvc` at `/deployments/logs` —
  created **before** the release by `kubectl apply -f logging/k8s/polaris-logs-pvc.yaml`, for the hourly batch job in `logging/PLAN-polaris-log-batch-2026-09-27.md`.
  Per pod because one shared file lost data within hours of rolling — active-issues `#48`.
  A Lua change is **`bash releases/fluent-bit/apply-lua.sh`** — `kubectl apply -k` alone leaves
  the old script running with no warning, and there is **no hot reload**.
  **Query `threadName.keyword`, never the bare field.**
- **OpenSearch:** **3.5.0**, runs in **Docker, outside the cluster and outside this repo**.
  Index templates and ISM policies are ours (`logging/opensearch/`).
- **VictoriaLogs:** **GONE 2026-09-18** — release, shipper and its 50 Gi PVC all removed, and
  its client code on 2026-09-29. The shipper's values survive only as
  `tests/fixtures/fb-values-shipper.yaml`, the log-coverage oracle's input: a fixture, not configuration.

### Suite
- **Language:** Python 3.12+ (`.python-version`), dependencies via `uv` (`pyproject.toml` / `uv.lock`).
- **Runtimes:** Jupyter notebooks (`.ipynb`), pytest.
- **Core libraries:** pandas, numpy, requests, psycopg2, sqlalchemy, matplotlib, seaborn.

---

## Repository Layout

```
.claude/commands/     capture-evidence · helm-diff-live · nb-sanitize
.claude/skills/       workflow-control (plan-first protocol, both trees)
.memory/              operational index; see .memory/README.md
charts/               LOCAL charts — this repo is the source of truth
                        minio/ polaris/ postgresql/ (postgresql is an UMBRELLA chart)
                        polaris-log-batch/ (its own release; shares only the log PVC with polaris)
images/               container images built from this repo — polaris-log-batch/ (Dockerfile + script)
releases/             VALUES-ONLY against upstream charts — airflow argo datahub
                        fluent-bit jupyter kafka schema-registry spark
logging/              the audit-logging domain: README (start here), SPECs, handoffs, k8s/ (log PVC),
                        opensearch/ templates + ISM, scripts/ (Lua tests, step2-step16)
schema/               Polaris DDL. schema_v3.sql is the ASF-shipped file and THE AUTHORITY
src/                  reusable Python modules imported by notebooks and tests
tests/                pytest suite (24 modules) + fixtures/
notebooks/            per-domain test notebooks: admin availability etl lifecycle
                        privilege purge rbac scenario error-cases datahub-error-cases
diagnostics/          inspect notebooks, plus:
  ladders/              high-rigor sweeps: log-coverage, api-sql-profile, replica-staleness
  outputs/banked/       TRACKED evidence — runs/ baselines/ reports/
  outputs/captures/     GITIGNORED — hundreds of MB, never committed
runbooks/             deterministic operational runs
docs/                 MERGE-2026-09-21.md — what the merge did and why
                        DELETED-2026-09-29.md — every file the cleanup removed, and how to read it back
```

**A path an older note names may not exist any more.** Superseded documents are deleted, not moved
to an `archive/` directory: look the path up in `docs/DELETED-2026-09-29.md` and read it with
`git show v-archive/pre-cleanup-2026-09-29:<path>`.

**`charts/` vs `releases/` is load-bearing.** A file under `charts/` changes what ships. A file
under `releases/` is a values overlay on someone else's chart. Do not move things between them.

**`postgresql/` is an umbrella chart** — values intended for the subchart **must** be nested
under `postgresql-ha:` or Helm silently ignores them.

**`diagnostics/outputs/banked/` is evidence and is tracked on purpose.** Do not gitignore it.
`run_manifest.py`: *the manifest carries values, the live cluster carries truth, never one
without the other.*

---

## Environments

**Platform: there is exactly one cluster** — a personal OrbStack single node. No shared company
cluster is reachable from this repo and none must ever be targeted from it. Dependency order is
real and one-directional: **MinIO → PostgreSQL → Polaris → everything else.**

**Suite: three distinct environments** whose settings and secrets are **totally different** —
never assume one's variables apply to another. Selected with `init_env(<env>)`:

1. **`local`** — the OrbStack node (`src/config/local.yaml`, gitignored). Full suite runs here,
   plus the destructive local-only utilities in `notebooks/admin/`. **This is the default.**
2. **`dev`** — shared company DEV. Functional / integration suites only. **Never** destructive
   teardown — it would delete other users' data.
3. **`prod`** — shared company PROD. **Availability tests only.**

- Secrets come from env vars and are never committed; only `common.yaml` and `*.example.yaml`
  are tracked. Each env ships a `*.example.yaml` template.
- Mutating notebooks call `require_not_prod(...)` right after setup.
- `notebooks/admin/` teardown notebooks are **`local`-only**, hardcoded to localhost by design,
  with an assert-based host guard, and must **not** be wired to `init_env()`.

### Notebook import convention
```python
import sys, pathlib
_ROOT = pathlib.Path.cwd()
while not (_ROOT / "src").is_dir() and _ROOT != _ROOT.parent:   # walk up to the repo root
    _ROOT = _ROOT.parent
sys.path.insert(0, str(_ROOT / "src"))
from polaris_test_utils import *
init_env("local")
require_not_prod("...")     # mutating notebooks only
```
The walk-up works at any depth; `tests/test_notebook_bootstrap.py` checks every notebook resolves it.

---

## Configuration Policy — VERIFY AGAINST DEFAULTS, NOT AGAINST INTENT

A values file is a statement of intent. Whether it is *in effect* is a separate fact, and the
gap between the two ran for months undetected here — an entire `postgresql:` block sat at the
wrong nesting level while the cluster served subchart defaults.

- **Never confirm a setting by reading the values file.** Confirm it by querying the running
  object and comparing against the **chart default**. A value that matches the default is not
  evidence: it is indistinguishable from a block that was never applied.
- **Un-inerting configuration that has never executed is a change, not a fix.**
- **`helm lint` is not a render.** Every change also gets `--dry-run=client --debug`.

## Schema Policy — PLAIN UPSTREAM, NO CUSTOM INDEXES

**Every measurement is taken on the schema Polaris ships.** The authority is
`schema/schema_v3.sql` (ASF-licensed); `schema/schema.sql` is structurally identical, differing
only in idempotency and `COMMENT ON`.

Upstream creates exactly three non-key indexes — `idx_entities`, `idx_locations`,
`idx_policy_mapping_record` — and gives `grant_records` **nothing but its 6-column primary key**.
`src/schema_audit.STOCK_INDEX_NAMES` is that set in code.

- **Do not create an index as part of a measurement.** A plan taken on a mutated schema is a
  statement about a database nobody runs, and is indistinguishable afterwards from one that is not.
- **Notebooks must not change the schema.** `04_explain_sweep.ipynb` is the model: read-only,
  safe to re-run. `02_index_audit.ipynb` and `02b_grant_scale_sweep.ipynb` measure a *proposed*
  index and are OFF-POLICY for the API-SQL audit — run them deliberately, from a shell, never
  as a step in a measurement.
- **Before measuring, confirm the schema is plain:**
  `uv run python drop_grantee_index.py --list` (non-zero if anything is custom).
- Proposing an index belongs in `schema_audit.INDEX_HYPOTHESES` as a remedy — a recommendation,
  never an applied change.

---

## Environment Commands

### Platform
- `kubectl config current-context` (must equal `orbstack`)
- `kubectl get pods -n datahub-hynix` · `helm list -n datahub-hynix`
- `helm upgrade --install <release> ./charts/<chart> -n datahub-hynix --dry-run=client --debug`
- `helm -n datahub-hynix get values <release> --revision N` — turns "what did I break" into a fact
- `kubectl logs deployment/benchmarks-polaris -n datahub-hynix --tail=50`
- `kubectl -n datahub-hynix port-forward pod/benchmarks-postgresql-postgresql-ha-postgresql-0 5433:5432`

### Suite
- `uv sync` (add a package: `uv add <pkg>`) · `pytest` · `isort . && black .`
- Notebook suites: **Restart & Run All**, top to bottom, no out-of-order cell dependencies.

---

## Jupyter Notebook Best Practices
- **Linear execution required.** Every notebook runs cleanly `Restart & Run All`.
- **Strict logic separation.** Notebooks do visualization, mapping, table printing and test
  summaries. Connectivity, OAuth engines and query execution live in `src/` and are imported.
- **Connection disposal.** Close cursors, clients and pools (`pool.close()` / `engine.dispose()`)
  in a dedicated teardown cell, to avoid overloading the local Pgpool-II pooler.
- **Memory release.** `del df` and `gc.collect()` after rendering large diagnostic tables.

---

## Tool Interaction Guardrails (CRITICAL)

- **Strict Plan-First Mode.** Do not modify modules, notebook cell structures, YAML or values
  files on your first turn. Present an impact analysis and wait for explicit developer
  confirmation. (See `.claude/skills/workflow-control/SKILL.md`.)
- **Cluster-Context Guard.** Before any mutating `kubectl`/`helm`, run
  `kubectl config current-context` and confirm it is exactly `orbstack`. The `-n datahub-hynix`
  flag alone does not protect against a context pointing at a different cluster.
- **Strict Namespace Enforcement.** Never create, deploy or modify resources outside
  `datahub-hynix`. Every mutating command passes `-n datahub-hynix` explicitly.
- **Zero Hardcoded Credentials.** Never write plaintext tokens, principal secrets, database
  passwords or cluster keys into a committed file or notebook cell. Load via `init_env()` or
  `os.environ`; pass to Helm via `--set-string` from an env var or a gitignored overlay.
- **Auto-Correction Restraint.** Self-correct a maximum of **2** times, then halt and request
  manual engineering feedback.
- **Destructive Commands Prohibited.** `kubectl delete namespace`, `helm uninstall`,
  `docker compose down -v`, PVC deletion and the OrbStack cluster reset each need separate,
  explicit authorisation **at the moment of execution** — approval of a plan that contains them
  is not approval to run them.
- **Persistent Server Block.** Never run blocking/attached containers that hang the console.
- **Timeout & Hang Guard.** A command is deadlocked only if it produces **no new stdout/stderr
  for 30 seconds** — not merely because total runtime exceeds 30s. Helm installs of PostgreSQL HA
  or Polaris routinely run several minutes waiting for `Ready`.
- **Cowork sessions have no cluster reach.** `device_bash` is an isolated VM with only this repo
  folder mounted — no `kubectl`, `helm` or `docker`. Claude edits files and commits; the developer
  runs every cluster command. **Never report a live-cluster check as passed when it could not be run.**

---

## Definition of Done

Common to both halves:

3. **Record the outcome in the memory tree.** `MEMORY.md` is an **index, kept under ~40 lines** —
   update its *Now* section and nothing else. Detail goes in `.memory/`: a fact with a number in
   `.memory/roadmap/`, anything you should not trust yet in `.memory/active-issues/`, the
   blow-by-blow including the wrong turns in `.memory/sessions/`.
4. **Commit the task as one versioned change, automatically** — see *Version Control*.

Steps 1 and 2 depend on the half:

**Platform (`charts/` `releases/` `logging/` `schema/` `runbooks/`)**
1. **Render, don't guess.** `helm lint` **and** a successful
   `helm upgrade --install ... --dry-run=client --debug` for every chart touched.
2. **Verify against defaults** — pods `Running`, and the changed setting queried from the running
   object, not read back out of the values file.

**Suite (`src/` `tests/` `notebooks/` `diagnostics/`)**
1. All test notebook cells run sequentially with zero runtime or compilation errors.
2. `pytest` green, then format with `isort . && black .`. `pyproject.toml` sets isort's `black`
   profile; without it the two tools undo each other and no order is clean (measured 2026-09-29).

---

## Version Control

**One task, one commit.** After each completed unit of work — a plan carried out, a fault found
and fixed, a measurement taken and reported — the change gets committed. Not per file edit, and
not batched across unrelated tasks: the unit is the thing you would describe in a sentence.

This matters here more than in most repos. The work is *findings* and *configuration whose
effect is invisible until it runs*. A finding that only exists in a chat transcript is lost the
moment the session ends, and Fault 1 was undiagnosable partly because nobody could say when the
nesting had last been correct.

### The gate: DoD first, commit second

Never commit a state you have not verified. Run the gate for your half, then:

```bash
git status                  # check BEFORE staging
git add <explicit paths>    # never -A (even scoped to a directory) while the tree holds work that isn't yours
git diff --cached --stat    # read it BEFORE committing
git commit
```

`git add -A diagnostics …` once committed 884 lines of Kade's uncommitted notebook edits into a
cleanup commit (2026-09-29, caught and rebuilt; `.memory/sessions/2026-09-29-repo-cleanup.md`).

### Message style

The subject line states **the finding or the point of the change**, not the files touched:

```
The postgresql: block was never applied -- Helm ignores un-nested subchart values
The sweep was measuring root, and root is the least representative identity
```

not `update values.yaml` or `fix bug`.

The body carries what a reader six months out cannot reconstruct: **what changed**, with the
numbers, intended vs actually in effect; **why**, especially when it corrects an earlier belief —
say what the old belief was and what it cost; **what is verified vs still open**, so the next
session does not re-establish what is settled or trust what is not.

Prefer the honest correction to the tidy summary. `MEMORY.md`, the `.memory/` files and any
runbook or `PLAN-*` / `HANDOFF-*` touched by the task belong in the **same commit** as the code —
they are the reasoning behind it, and they go stale the instant they are committed separately.

### Never commit
- **Secrets.** `src/config/<env>.yaml`, real tokens, principal secrets, MinIO keys, the seed
  ledger's credentials. Only `common.yaml` and `*.example.yaml` are tracked.
- **Capture directories** (`diagnostics/outputs/captures/`, `capture*/`, `*.log`) — hundreds of MB.
- **Vendored noise.** `node_modules/`, `.DS_Store`, chart tarballs, `helm get values` dumps.
- A broken, half-applied or half-formatted tree, to "save progress". Use a branch instead.

### Who runs it — Claude commits, automatically

**Every completed unit of work is committed by Claude, without being asked.** The developer must
be able to open `git log` and see the session's reasoning as a sequence of revisions. The commit
is not a closing formality Claude offers to perform — it is the last step of the task, run as
soon as the DoD gate is green.

- **One task, one commit** — auto-commit does **not** mean a commit per file edit.
- **The gate is not skippable.** If it cannot be run at all — and in a Cowork session it cannot,
  there is no `helm` and no cluster — commit anyway so the work is traceable, and say so **in the
  commit body**: `NOT VERIFIED: <gate> could not be run, no cluster reach from this session`.
- **Claude never commits work it did not do.** Pre-existing uncommitted changes stay untouched
  unless the task is about them.
- **`git push` is Kade's.** Auto-commit is local history; publishing is a separate decision.
- **Commit before a risky step**, not only after a finished one. An index toggle, a realm reset,
  a TRUNCATE, a teardown — get the tree committed first so the before-state is recoverable.

**Git from a Cowork session leaves lock files** when the mount lacks delete permission
(`unable to unlink '.git/index.lock'`). A left-behind `index.lock` blocks every later git command,
Kade's included. Either grant delete permission for the folder, or after each git call `mv -n` any
`.git/*.lock` aside and confirm none remain. The commit itself is written correctly either way.

**Identity:** this repo has no `user.name` / `user.email` in its local config and the mount does
not see Kade's global one, so Claude commits with `git -c user.name=... -c user.email=...`
matching the existing `git log` author rather than writing an identity into `.git/config`.

---

## Where the pre-merge history is

The 435 commits that made these two trees are in this repo, on refs of their own:

```bash
git log archive/local-k8s            # 212 commits, 2026-07-09 .. 09-21
git log archive/polaris-learning     # 223 commits, 2026-06-02 .. 09-21
git log --all --grep='<term>'        # searches both archives too
git log --all -S'<code string>'      # pickaxe across every ref
```

`git blame` on `main` stops at the merge commit — that is expected. Cross the seam with
`--all` searches, or check out the archive ref. See `docs/MERGE-2026-09-21.md`.

The tree **before the 2026-09-29 cleanup** is branch `archive/pre-cleanup-2026-09-29` and tag
`v-archive/pre-cleanup-2026-09-29` (`cf6eae8`); what it removed is `docs/DELETED-2026-09-29.md`.
