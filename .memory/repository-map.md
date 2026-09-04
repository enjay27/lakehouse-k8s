# Repository map

Root holds the two convention files (`CLAUDE.md`, `MEMORY.md`), the task runbooks,
and one directory per service. A service directory is either a **local chart**
(`Chart.yaml` + `templates/`) or just a **values file** aimed at an upstream chart.

## Local charts — this repo is the source of truth

| dir | release | notes |
|---|---|---|
| `minio/` | `benchmarks-minio` | Chart + templates written 2026-08-18. Creates `data-catalog-bucket`, `argo-artifacts`, `user-catalog-bucket` and the `benchmarks-minio-credentials` secret via `job-postinstall.yaml`. **Installed first — Polaris will not bootstrap without it.** |
| `postgresql/` | `benchmarks-postgresql` | **Umbrella chart**: `Chart.yaml` declares Bitnami `postgresql-ha` 16.3.2 as a dependency (vendored at `charts/postgresql-ha-16.3.2.tgz`). Everything intended for the subchart **must** be nested under `postgresql-ha:` — see `active-issues.md` #F1. Also holds `schema/` (Polaris DDL) and `secret/`. |
| `polaris/` | `benchmarks-polaris` | Apache Polaris v1.3.0-incubating. `values-old.yaml` is a superseded copy kept for diffing, not for installing. |

## Values-only — upstream chart, local values

`airflow/`, `argo/`, `jupyter/`, `kafka/`, `schema-registry/`, `spark/`,
`fluent-bit/`, `logging/`, `datahub/` (chart README, `datahub-values.yaml`,
`prerequisites-values.yaml`, logback configmap).

**There are two Fluent Bit values files and they are different deployments, not
duplicates** — `fluent-bit/values.yaml` is the **DaemonSet** (container logs →
OpenSearch in Docker); `logging/fb-values.yaml` is a **single-replica Deployment**
(shared-PVC file tail → VictoriaLogs). `logging/` also holds
`victoria-values.yaml` and `polaris-logging-architecture-spec.md`, the design doc
those two are built against (filed 2026-09-03). Only `fluent-bit/values.yaml.bak`
is an actual backup.

**Duplicate values files are a live hazard here.** `datahub-values.yaml`,
`datahub-values (2).yaml`, `datahub/datahub-values (4).yaml`,
`prerequisites-values.yaml`, `datahub/prerequisites-values*.yaml` and
`fluent-bit/values.yaml.bak` all coexist. The copy **inside** the service
directory is the one to treat as current; the root-level and parenthesised copies
are downloads and backups. Nothing enforces this — check the mtime before trusting
either.

## Not part of the platform

- `server/` — a small Node app (4 tracked files plus
  `datahub-prerequisites-0.3.0.tgz`). Its `node_modules/` is on disk but gitignored.
- `dozzle/` — empty directory, no chart, no values.
- `.claude/skills/workflow-control/` — the plan-first execution protocol Claude
  follows in this repo.

## Root runbooks

| file | what it is |
|---|---|
| `local-k8s-HANDOFF.md` | **HISTORICAL** (rebuild done 2026-09-03, outside it). Still the best account of *why*: Fault 1 (inert values nesting), Fault 2 (IPv4-only pg_hba), and the operational gotchas. |
| `RESET-AND-CLEAN-INSTALL.md` | **HISTORICAL** — the procedure that was not followed. Its install order and verification block are still valid for any future reinstall. |
| `shipper-v3-upgrade-runbook.md` | **PENDING** — installing the Fluent Bit policy v3 and the flush report, which are written and have never executed (`active-issues.md` #14). Phased, with a render gate, the two assumptions no test could reach, the report's margin self-check, and a rollback that costs a second log replay. |
| `shm-exhaustion-orbstack-leg-runbook.md` | the `/dev/shm` exhaustion repro + fix verification (S5 pending item). |
| `preflight-triage.sh` | script form of the RESET §1 pre-flight checks. |
| `POLARIS-API-LOG-COVERAGE-NOTEBOOK.md` | **the live handoff.** Plan for a notebook, built in the *Polaris* project, that calls every Polaris API to drive the log pipeline across every branch of its retention policy. Restates the whole pipeline cold, and documents the limitation of each policy rule. Written 2026-09-03. |
