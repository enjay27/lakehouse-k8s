# Completed structural work

Finished and not to be re-litigated. Anything here that is *written but not yet
proved against a running cluster* is cross-listed in
[`active-issues.md`](active-issues.md) — being finished as a piece of work is not
the same as being verified.

## 2026-08-18 — the rebuild was diagnosed and documented

- **Root-caused both faults** behind the unstable PostgreSQL HA cluster: the
  umbrella-chart values nesting (#F1) and the IPv4-only `pg_hba` (#F2). Written up
  in `local-k8s-HANDOFF.md` §1, self-contained.
- **Wrote the reset procedure** — `RESET-AND-CLEAN-INSTALL.md`: blocking pre-flight
  image audit, insurance exports, teardown, a 12-step ordered reinstall with a gate
  per step, and a verification block. Plus `preflight-triage.sh`.
- **Audited the repo against the handoff** and found seven config blockers the
  handoff did not know about — the surviving ones are `active-issues.md` #1, #3, #4.
- **Decisions taken:** full OrbStack reset (not namespace-only); reinstall
  everything; image versions unchanged; write templates for the local MinIO chart
  rather than switching to an upstream one.

## 2026-08-18 — MinIO chart made installable

`minio/` had `Chart.yaml` and `values.yaml` but no `templates/` — `helm install
./minio` rendered zero resources. Twelve templates written (statefulset, service,
secret, ingress ×2, hpa, servicemonitor, serviceaccount, helpers, NOTES, plus
`configmap-policies.yaml` and `job-postinstall.yaml` that create the buckets and
the `benchmarks-minio-credentials` secret). Bucket names reconciled:
`data-catalog-bucket` (Polaris warehouse), `argo-artifacts` (Argo), and
`user-catalog-bucket`.

## 2026-08-19 — PostgreSQL values rewritten

All service settings moved under `postgresql-ha:`, `pg_hba` extended to both
address families, a real 1G `/dev/shm` emptyDir mounted, `persistence.size` set to
10Gi, `repmgr` kept in the preload list. On disk only.

## 2026-08-22 — logging made lightweight

`logging/victoria-values.yaml` (VictoriaLogs single, 30d retention, 50Gi PV,
LoadBalancer on 9428) and `logging/fb-values.yaml` committed as the replacement for
the heavier Elasticsearch-shaped log path.

## 2026-09-03 — memory convention aligned with `polaris-learning`

`MEMORY.md` reduced to a ~40-line index, this `.memory/` tree created, `CLAUDE.md`
given a Repository Layout section, a memory-tree DoD, and the automatic
one-task-one-commit Version Control rule.
