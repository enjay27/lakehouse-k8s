# Infrastructure Environment Rules

## Tech Stack
- **Orchestration:** Local Kubernetes (OrbStack, context `orbstack`) via Helm 3.x.
- **Target Namespace:** `datahub-hynix` — strictly enforced for every K8s asset. The one
  exception is `logging`, which holds the log sink only.
- **Apache Polaris (Iceberg REST catalog):** local chart, v1.3.0-incubating. Management
  port **8182**, not the 8282 upstream docs default to.
- **PostgreSQL HA:** local umbrella chart wrapping Bitnami `postgresql-ha` 16.3.2 —
  3 replicas + **Pgpool-II** connection pooler (**not** PgBouncer; corrected 2026-08-18).
- **MinIO:** local chart — S3 for the Iceberg warehouse (`data-catalog-bucket`) and Argo
  artifacts (`argo-artifacts`).
- **Fluent Bit — two releases, on purpose, both in `datahub-hynix`:**
  `fb-polaris-shipper` (chart `fluent-bit-0.58.1`, app **5.1.1**, Deployment) tails the
  Polaris log PVC into **VictoriaLogs**; a second DaemonSet release tails
  `/var/log/containers/*.log` into **OpenSearch**. Values: `logging/fb-values.yaml` and
  `fluent-bit/values.yaml` respectively — different deployments, not duplicates.
- **VictoriaLogs:** log sink in namespace `logging` (9428).
- **OpenSearch:** runs in **Docker, outside the cluster and outside this repo** — no compose
  file is versioned here. It is the DaemonSet's sink; VictoriaLogs is the shipper's. That
  question is settled — but **neither values file matches its live release**; see
  `.memory/active-issues.md` #5 before trusting one.
- **Values-only against upstream charts:** DataHub + prerequisites (Kafka / Elasticsearch /
  MySQL / ZooKeeper), Kafka, Schema Registry, Spark, Airflow, Argo Workflows, Jupyter.
  *Service versions are declared explicitly in each chart's `values.yaml`; several charts
  pin no image at all — see `.memory/active-issues.md` #2 before any reinstall.*

## Repository Layout
Full detail in [`.memory/repository-map.md`](.memory/repository-map.md). The shape:
- **Local charts (this repo is the source of truth):** `minio/`, `polaris/`, `postgresql/`.
  Each has `Chart.yaml` + `templates/`. `postgresql/` is an **umbrella chart** — values
  intended for the subchart **must** be nested under `postgresql-ha:` or Helm silently
  ignores them.
- **Values-only directories:** `airflow/`, `argo/`, `datahub/`, `fluent-bit/`, `jupyter/`,
  `kafka/`, `logging/`, `schema-registry/`, `spark/` — a `values.yaml` aimed at an upstream
  chart, nothing more.
- **`postgresql/schema/`** — Polaris DDL (`schema_v3.sql` is the ASF-shipped file and the
  authority; `schema.sql` and `bootstrap.sql` are the local variants).
- **`postgresql/secret/`** — Secret manifests. One of them is stale; see active issues #4.
- **Root runbooks** — `local-k8s-HANDOFF.md` (why), `RESET-AND-CLEAN-INSTALL.md` (how),
  `shipper-v2-upgrade-runbook.md`, `shm-exhaustion-orbstack-leg-runbook.md`,
  `preflight-triage.sh`. Written to be read cold.
- **Not part of the platform:** `server/` (a Node app with `node_modules/` committed),
  `dozzle/` (empty), `attic`-style duplicates — several `datahub-values*.yaml` and
  `prerequisites-values*.yaml` copies coexist at the root and inside `datahub/`. **The copy
  inside the service directory is the current one.**

## Environments
There is exactly **one** cluster: a personal OrbStack single node. No shared company cluster
is reachable from this repo and none must ever be targeted from it. Full detail —
ports, guards, secret handling — in [`.memory/environments.md`](.memory/environments.md).

Dependency order is one-directional and load-bearing:
**MinIO → PostgreSQL → Polaris → everything else.** Polaris will not bootstrap without its
bucket and its metastore.

## Environment Commands
*Always confirm the cluster context before anything mutating.*
- **Check Active Cluster Context:** `kubectl config current-context` (must equal `orbstack`)
- **Check K8s Cluster State:** `kubectl get pods -n datahub-hynix`
- **Check Helm Releases:** `helm list -n datahub-hynix`
- **Verify Manifest Dry-Run:** `helm upgrade --install <release> ./<chart> --namespace datahub-hynix --dry-run --debug`
- **Deploy/Upgrade Chart:** `helm upgrade --install <release> ./<chart> -f values.yaml -n datahub-hynix`
- **Diff a release against itself:** `helm -n datahub-hynix get values <release> --revision N`
  — turns "what did I break" into a fact rather than a guess.
- **Tail Service Logs:** `kubectl logs deployment/benchmarks-polaris -n datahub-hynix --tail=50`
- **Direct PostgreSQL (only pgpool is a LoadBalancer):**
  `kubectl -n datahub-hynix port-forward pod/benchmarks-postgresql-postgresql-ha-postgresql-0 5433:5432`

## Configuration Policy — VERIFY AGAINST DEFAULTS, NOT AGAINST INTENT
A values file is a statement of intent. Whether it is *in effect* is a separate fact, and in
this repo the gap between the two ran for months undetected — an entire `postgresql:` block
sat at the wrong nesting level while the cluster served subchart defaults.

- **Never confirm a setting by reading the values file.** Confirm it by querying the running
  object and comparing against the **chart default**. A value that matches the default is
  not evidence: it is indistinguishable from a block that was never applied.
- **Un-inerting configuration that has never executed is a change, not a fix.** Review it
  line by line against the defaults it replaces before assuming it is safe.
- **`helm lint` is not a render.** Every change gets `--dry-run --debug` as well; lint does
  not catch values/template errors that only surface at render time.
- The verification assertions that would have caught this are in
  [`.memory/roadmap.md`](.memory/roadmap.md) — run them after any PostgreSQL change.

## Tool Interaction Guardrails (CRITICAL)
- **Cluster-Context Guard:** Before any mutating `kubectl` or `helm` command, run
  `kubectl config current-context` and confirm it equals exactly `orbstack`. The
  `-n datahub-hynix` flag alone does not protect against a context pointing at a different
  cluster entirely. Anything else: halt and ask.
- **Strict Namespace Enforcement:** Never create, deploy or modify Kubernetes resources
  outside `datahub-hynix` (except the `logging` sink). Every mutating command passes
  `-n datahub-hynix` explicitly.
- **Strict Plan-First Mode:** Do not modify YAML, alter `values.yaml`, or run deployment
  changes on the first turn. Present an infrastructure impact plan and wait for explicit
  developer confirmation. (See `.claude/skills/workflow-control/SKILL.md`.)
- **Zero Hardcoded Credentials:** Never write plaintext passwords, Polaris root secrets or
  cluster keys into a committed file. Pass them via `--set-string` from an environment
  variable, or a gitignored `values-secret.yaml` overlay. Committed files carry non-secret
  defaults or a Secret *name* only.
- **Persistent Server Block:** Never run blocking/attached containers (e.g. `docker compose up`
  without `-d`) that hang the console.
- **Destructive Commands Prohibited:** `kubectl delete namespace`, `helm uninstall`,
  `docker compose down -v`, PVC deletion and the OrbStack cluster reset each need separate,
  explicit developer authorisation **at the moment of execution** — approval of a plan that
  contains them is not approval to run them.
- **Timeout & Hang Guard:** A command is deadlocked only if it produces **no new
  stdout/stderr for 30 seconds** — not merely because total runtime exceeds 30s. Helm installs
  of PostgreSQL HA or Polaris routinely run several minutes waiting for `Ready`. On a real
  stall, stop and output the stderr snippet.
- **Cowork sessions have no cluster reach.** `device_bash` is an isolated VM with only this
  repo folder mounted — no `kubectl`, `helm` or `docker`. Claude edits files and commits;
  the developer runs every cluster command. Never report a live-cluster check as passed
  when it could not be run.

## Definition of Done (DoD)
Before marking any infrastructure task complete:
1. **Render, don't guess.** `helm lint` **and** a successful
   `helm upgrade --install ... --dry-run --debug` for every chart touched.
2. **Verify against defaults**, per the Configuration Policy above — pods `Running`, and the
   changed setting queried from the running object, not read back out of the values file.
3. **Record the outcome in the memory tree.** `MEMORY.md` is an **index, kept under ~40
   lines** — update its *Now* section and nothing else. The detail goes in `.memory/`: a fact
   with a number in `.memory/roadmap.md`, anything you should not trust yet in
   `.memory/active-issues.md`, the blow-by-blow including the wrong turns in
   `.memory/sessions/<date>-<slug>.md`. See `.memory/README.md` for which file takes what.
4. **Commit the task as one versioned change, automatically** — see *Version Control* below.
   Claude runs the commit itself as the last step of the task, without being asked. A task is
   not done until it is in git; an uncommitted finding lives only in a chat transcript.

## Version Control

**One task, one commit.** After each completed unit of work — a plan carried out, a fault
found and fixed, a chart made installable — the change gets committed. Not per file edit, and
not batched across unrelated tasks: the unit is the thing you would describe to someone in a
sentence.

This matters here more than in most repos. The work is *configuration whose effect is
invisible until it runs*, and the commit is where a change becomes attributable to the cluster
state that produced it. Fault 1 was undiagnosable partly because nobody could say when the
nesting had last been correct.

### The gate: DoD first, commit second

Never commit a state you have not verified. In order:

```bash
helm lint ./<chart>
helm upgrade --install <release> ./<chart> -n datahub-hynix --dry-run --debug
git status                     # check BEFORE -A, never after
git add -A && git commit
```

### Message style

Follow what is already in `git log`. The subject line states **the finding or the point of
the change**, not the files touched:

```
The postgresql: block was never applied -- Helm ignores un-nested subchart values
minio/: chart had no templates/, so helm install rendered zero resources
```

not `update values.yaml` or `fix config`.

The body carries what a reader six months out will need and cannot reconstruct:

- **what was changed**, with the values — intended vs what was actually in effect;
- **why**, especially when the change corrects an earlier belief — say what the old belief was
  and what it cost;
- **what is verified vs still open**, so the next session does not re-establish what is
  settled or trust what is not.

Prefer the honest correction to the tidy summary. `MEMORY.md`, the `.memory/` files and any
runbook touched by the task belong in the **same commit** as the config — they are the
reasoning behind it, and they go stale the instant they are committed separately.

### Never commit

- **Secrets.** Real passwords, Polaris root secrets, MinIO keys. Committed files carry
  non-secret defaults or a Secret name only.
- **Vendored noise.** `node_modules/`, `.DS_Store`, chart tarballs pulled for insurance,
  exported `helm get values` dumps.
- A half-applied or unrendered tree, to "save progress". Use a branch instead.

### Who runs it — Claude commits, automatically

**Every completed unit of work is committed by Claude, without being asked.** The developer
must be able to open `git log` and see the session's reasoning as a sequence of revisions; a
change that sits uncommitted at the end of a session exists only in a chat transcript. The
commit is not a closing formality Claude offers to perform — it is the last step of the task,
run as soon as the DoD gate above is green.

- **One task, one commit** — auto-commit means Claude does not wait to be told; it does
  **not** mean a commit per file edit.
- **The gate is not skippable.** If it cannot be run at all — and in a Cowork session it
  cannot, there is no `helm` — commit anyway so the work is traceable, and say so **in the
  commit body**: `NOT VERIFIED: helm lint/--dry-run could not be run, no cluster reach from
  this session`. The next session then knows not to trust the tree.
- **Claude never commits work it did not do.** Pre-existing uncommitted changes in the tree
  stay untouched unless the task is about them.
- **`git push` is Kade's.** Auto-commit is local history; publishing is a separate decision.
- **Commit before a risky step**, not only after a finished one. A teardown, a namespace
  delete, an OrbStack reset — get the tree committed first so the before-state is recoverable.

Identity: this repo has no `user.name` / `user.email` in its local config and the mount does
not see Kade's global one, so Claude commits with `git -c user.name=... -c user.email=...`
matching the existing `git log` author rather than writing an identity into `.git/config`.
