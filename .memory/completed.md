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

## 2026-09-03 — the cluster was reset and rebuilt

Done by Kade directly, **not** by following `RESET-AND-CLEAN-INSTALL.md`. The whole
OrbStack cluster including the K8s services was reset and brought back; the four
config blockers (#1 Polaris root credential, #3 MinIO credential sets, #4 stale
persistence secret, #2 unpinned images) were resolved during the install. Fluent Bit
was deployed as a K8s DaemonSet and confirmed working. OpenSearch was not part of it —
it runs in Docker, outside the cluster and outside this repo.

Not done, deliberately: the verification assertions were not run, and the repo was not
reconciled against the live releases. Both are `active-issues.md` #1. The two root
runbooks become historical here — they are still the best account of *why* the rebuild
was needed (#F1, #F2), but they are no longer a procedure anyone should follow.

## 2026-09-03 — memory convention aligned with `polaris-learning`

`MEMORY.md` reduced to a ~40-line index, this `.memory/` tree created, `CLAUDE.md`
given a Repository Layout section, a memory-tree DoD, and the automatic
one-task-one-commit Version Control rule.

## 2026-09-03/04 — the Polaris → VictoriaLogs shipper, built

All in `logging/fb-values.yaml`; no `--set` flags, the values file is the definition.

- **Access-log field extraction.** The Quarkus `%h %l %u %t "%r" %s %b` line split out of
  `_msg` into `client_ip`, `user_principal_name`, `http_method`, `api_path`, `http_status`,
  `response_size`, gated on `loggerName == io.quarkus.http.access-log`. `_msg` is kept — it is
  the raw line, and what you read when the parse is wrong. A line from that logger that does
  not parse is tagged `access_log_parse_error:true` rather than dropped.
- **A retention policy** (`polaris_noise_filter`): ERROR/WARN keep, non-access-log keep,
  4xx/5xx keep, PUT/DELETE/PATCH keep, every POST keep except `/oauth/tokens`, GET/HEAD on a
  table or view once per principal per **KST** day. **Errors outrank dedup deliberately.** The
  day comes from the record's own `_time`, never wall-clock, so a shipper replay re-evaluates
  historical records against their own day.
- **The shipper's four silent faults**, all confirmed live against revision 10 before being
  changed: no tail `DB` (every restart re-read the file from byte 0), `Skip_Long_Lines Off`
  (which **stops** the tail rather than skipping the line — stack traces are the long lines),
  no `Rotate_Wait`, and no filesystem buffering. Plus `json_date_key false` and a per-record
  `Remove_key` pass.
- **A test harness that cannot drift.** `logging/scripts/test-polaris-filters.py` reads the
  Lua *out of* the values file and executes it, so the suite tests what ships rather than a
  copy of it. Needs a Lua interpreter; macOS has none, but a TeX install provides
  `luatex --luaonly`.

**Cross-listed, and the distinction matters here more than anywhere:** policy v2 (rule 5
inverted, the principal-keyed dedup key, the flush report) and the whole of the above's second
revision are **written and not running** — `active-issues.md` #14. Being finished as a piece
of work is not the same as being the running object; this repo has now made that mistake
twice in the same file.


---

## The Polaris log file leg, removed entirely — 2026-09-18

The second pipeline is gone: **`fb-polaris-shipper` uninstalled, VictoriaLogs uninstalled,
`polaris-shared-logs-pvc` deleted**, and Polaris upgraded to mount nothing
(`logging/RUNBOOK-log-pvc-removal-2026-09-18.md`, executed in full). Polaris now writes no log
file at all; everything goes to stdout and reaches OpenSearch through the DaemonSet.

**How it started.** A request to delete Polaris logs older than 3 days. There was no way to do
that: Quarkus/JBoss offers `max-file-size`, `max-backup-index` and `file-suffix` and **no
age-based deletion of any kind** (`#44`). The count-based bound looked like a day bound because
the file names carried dates — but the daily roll mints a new basename and nothing deletes the
previous day, which is how a declared bound of 5 sat over ~130 files and 27 MB reaching back to
08-21. Asking for retention exposed that the leg had no consumer worth keeping, and it was
removed instead.

**What it closed.** `#8` (three replicas appending to one RWO log file — closed at the *mount*
removal, not the claim deletion), `#38` (dead file-JSON config), `#40` (closed **unanswered**;
see below), the `REVIEW-pipeline` P10 loose end, and a duplicate-mountPath trap nobody had ever
hit: the chart mounts its own `logs-storage` volume at the same `/deployments/logs` that
`extraVolumes` claimed, so flipping `logging.file.enabled: true` would have been rejected by the
API server outright. `enabled: false` was silently load-bearing for the deployment rendering.

**Three things worth carrying forward, and none of them is about logging:**

1. **`ReadWriteOnce` does not serialise writers.** It restricts a volume to one *node*; any
   number of pods on that node may mount it, which on a single-node cluster is all of them.
   That misreading is what built `#8`.
2. **A gate must be able to fail.** The step-3 render gate returned 2 on a correct chart because
   it grepped `--debug`'s values dumps rather than the manifest; the fix added a positive
   control (`quarkus.log.file.enabled=false`, want 1) so a mistyped pattern cannot score 0/0 and
   read as a pass. That is `#43`'s lesson and the proposal's §9.3 warning, seen a **third** time
   — in a gate written the same day as both citations.
3. **"Closed" and "unknowable" are different endings.** `#40` asked whether the rotation bursts
   were `#8` already biting. Answering it needed the rotated files, and step 4 destroyed them.
   The cost was stated before the choice and accepted; it is filed as closed-unanswered rather
   than closed, so nobody reuses it as a precedent for deleting evidence.

**Verification grades differ, deliberately.** Step 3 carries its own output (gate armed, then
`ls /deployments/logs` → *No such file or directory*, exit 2). Steps 1, 2 and 4 are Kade's
report with no recorded output. **Closed 2026-09-18:** VictoriaLogs' own 50 Gi PVC in namespace
`logging` was deleted manually by Kade — `helm uninstall` does not remove it. The teardown is
complete end to end, and `logging` is now an empty namespace with no reason to exist.
