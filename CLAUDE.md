# Infrastructure Environment Rules

## Tech Stack
- **Orchestration:** Hybrid Environment (Local Kubernetes via Helm 3.x + Docker Compose)
- **Target Namespace:** `datahub-hynix` (Strictly enforced for all K8s assets)
- **OpenSearch:** Docker Compose (v1.5.0)
- **Apache Polaris (Iceberg Catalog):** Helm (v1.3.0-incubating)
- **PostgreSQL HA Cluster:** Helm (3 HA Replicas + 1 Pool / PgBouncer connection pooler)
- **FluentBit:** Helm (DaemonSet log collector)
- **DataHub:** Helm (Currently UNINSTALLED; target `values.yaml` preserved)
- **DataHub-Prerequisites (Kafka, ElasticSearch, MySQL):** Helm (Currently UNINSTALLED; target `values.yaml` preserved)
  *Note: All specific service versions are declared explicitly within their respective chart values.yaml files.*

## Environment Commands
*Always check service health or use explicit cluster/compose contexts before execution.*
- **Check OpenSearch State:** `docker-compose ps`
- **Tail OpenSearch Logs:** `docker-compose logs --tail=50`
- **Check K8s Cluster State:** `kubectl get pods -n datahub-hynix`
- **Check FluentBit DaemonSet:** `kubectl get daemonset -n datahub-hynix`
- **Check Helm Releases:** `helm list -n datahub-hynix`
- **Verify Manifest Dry-Run:** `helm upgrade --install <release> ./charts/<chart> --namespace datahub-hynix --dry-run --debug`
- **Deploy/Upgrade Chart:** `helm upgrade --install <release> ./charts/<chart> -f values.yaml -n datahub-hynix`
- **Tail Service Logs:** `kubectl logs deployment/datahub-gms -n datahub-hynix --tail=50`
- **Check Active Cluster Context:** `kubectl config current-context` (must equal `orbstack` — see Cluster-Context Guard below)

## Tool Interaction Guardrails (CRITICAL)
- **Cluster-Context Guard:** Before any mutating `kubectl` or `helm` command, run `kubectl config current-context` and confirm it equals exactly `orbstack` (the local OrbStack cluster). The `-n datahub-hynix` namespace flag alone does not protect against an accidentally-switched context pointing at a different cluster entirely. If the context is anything other than `orbstack`, halt immediately and ask for explicit confirmation before proceeding.
- **Strict Namespace Enforcement:** You are completely forbidden from creating, deploying, or modifying Kubernetes resources outside of the `datahub-hynix` namespace. Every single `kubectl` or `helm` file mutation or deployment command MUST explicitly pass `-n datahub-hynix` or `--namespace datahub-hynix`.
- **Strict Plan-First Mode:** You are strictly forbidden from modifying any YAML configurations, altering values.yaml files, or running deployment changes on your first turn. You must present an infrastructure impact plan first and wait for explicit developer confirmation.
- **Zero Hardcoded Credentials:** Never write plaintext database passwords, Polaris root secrets, or other credentials into `values.yaml` or any committed file. Pass secrets via `--set-string` sourced from environment variables, or a gitignored values-secret overlay file (e.g. `values-secret.yaml`, never committed). Committed `values.yaml` files must only contain non-secret defaults or references to a Secret name.
- **Persistent Server Block:** Never execute blocking or attached container runs (e.g., standard `docker-compose up` without `-d`) that hang the console.
- **Destructive Commands Prohibited:** You are completely unauthorized to execute `kubectl delete namespace`, `helm uninstall`, `docker-compose down -v`, or destructive purge commands without separate, explicit developer verification on each occurrence.
- **Timeout & Hang Guard:** A command is only assumed deadlocked/hung if it produces **no new stdout/stderr output for 30 seconds**, not simply because total runtime exceeds 30 seconds — legitimate Helm installs/upgrades for the PostgreSQL HA cluster or Apache Polaris commonly run several minutes while waiting for pods to reach `Running`/`Ready`. If a command does stall with no output, stop execution immediately and output the stderr snippet.

## Definition of Done (DoD)
Before finalizing an infrastructure task or prompting the user for sign-off:
1. Verify Docker Compose containers (`opensearch`) and active K8s platform pods inside `datahub-hynix` are stable and `Running`.
2. Confirm configuration templates pass native helm linting (`helm lint`) **and** a successful `helm upgrade --install ... --dry-run --debug` render if updates were made — lint alone does not catch values/template errors that only surface at render time.
3. Automatically document the updated cluster topology and chart parameters inside `MEMORY.md`.