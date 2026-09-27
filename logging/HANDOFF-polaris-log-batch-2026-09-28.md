# HANDOFF — Polaris log batch (2026-09-28)

For whoever picks this up next — Kade in a new session, or a colleague. Read this first, then
`logging/SPEC-polaris-log-batch.ko.md` (the logic, in Korean) and, only if you need the *why*,
`logging/PLAN-polaris-log-batch-2026-09-27.md` (the decision log).

## The goal

Replace the Fluent Bit Lua pipeline for Polaris audit logs with files our team owns end to end:

```
Polaris pods --per-pod JSON log, hourly KST .gz--> PVC polaris-logs-pvc (/deployments/logs)
CronJob polaris-log-batch (HH:03 KST) -----------> processed-logs/ aggregated-logs/ malformed/ on the same PVC
Observability team (not us) ---------------------> fetch from the PVC -> OpenSearch
```

## State

| piece | state | evidence |
|---|---|---|
| `polaris-logs-pvc` (`logging/k8s/polaris-logs-pvc.yaml`) | **live** on OrbStack, Bound | Kade, 2026-09-27 |
| Polaris file logging (`charts/polaris/values.yaml`): JSON, `polaris-${HOSTNAME}.log`, `.yyyy-MM-dd-HH.gz`, `TZ=Asia/Seoul`, rotate-on-boot off | **live**, verified from the running pods | `-18.gz` (09-27), per-pod `-22.gz` at 23:02, `2tklb` orphan |
| One file per pod, not a shared file | **decided by measurement** | step15: shared lost 44.5 % / 44.2 % of load, 61 % of real traffic; per-pod 0 (`#48`, closed) |
| Batch script `images/polaris-log-batch/polaris_log_batch.py` | **written, tested** — not yet run on the cluster | 40 tests green; step16 parity with the real Lua identical on 5 seeds |
| Image `images/polaris-log-batch/Dockerfile` | **written, never built** | — |
| Chart `charts/polaris-log-batch/` (SA, Role, RoleBinding, CronJob) | **written, never rendered or installed** | no helm in the Cowork session |
| Fluent Bit tiers 2/3 | still running, untouched | — |

Everything that says "written" was produced in a Cowork session with no cluster reach and no `helm`:
**nothing in the batch half has been built, rendered or run yet.**

## Do next, in this order

### 0. Preconditions (one minute)
```bash
kubectl config current-context                                   # orbstack
kubectl -n datahub-hynix get pods -l app.kubernetes.io/instance=benchmarks-polaris
kubectl -n datahub-hynix exec deploy/benchmarks-polaris -- ls -ln /deployments/logs
```
- Current files must be named `polaris-benchmarks-polaris-<hash>-<id>.log`. If you see
  `polaris-sizetest-*` being written, the step15 test settings are still live:
  `bash logging/scripts/step15-shared-file-size-rotation-test.sh restore`.
- The Polaris chart **does not restart pods on a ConfigMap-only change** (no checksum annotation).
  After any `logging.*` change: `kubectl -n datahub-hynix rollout restart deploy/benchmarks-polaris`.
- If commit `9ec82a4` (the batch *inside* the Polaris chart) was ever applied, re-run the Polaris
  upgrade with `-f charts/polaris/values.yaml` to remove its CronJob/Role/ConfigMap. Otherwise skip.

### 1. Build the image
```bash
docker build -t polaris-log-batch:0.1.0 images/polaris-log-batch
```
OrbStack's cluster uses the local Docker daemon's images; the chart sets `pullPolicy: Never`.

### 2. Render, then install the batch release
```bash
helm lint charts/polaris-log-batch
helm upgrade --install polaris-log-batch ./charts/polaris-log-batch -f charts/polaris-log-batch/values.yaml \
  -n datahub-hynix --dry-run=client --debug
helm upgrade --install polaris-log-batch ./charts/polaris-log-batch -f charts/polaris-log-batch/values.yaml -n datahub-hynix
kubectl -n datahub-hynix auth can-i list pods --as=system:serviceaccount:datahub-hynix:polaris-log-batch   # yes
```
Always pass `-f`: without it Helm reuses the previous revision's values (`copying values from old
release`) — that already cost one round on 09-27.

### 3. One manual run, then check it
```bash
kubectl -n datahub-hynix create job --from=cronjob/polaris-log-batch log-batch-manual-1
kubectl -n datahub-hynix logs -f job/log-batch-manual-1
kubectl -n datahub-hynix exec deploy/benchmarks-polaris -- sh -c \
  'cd /deployments/logs && ls processed-logs aggregated-logs malformed done/* && cat .state/checkpoint.json | head -20'
```
Expect:
- one `{"event":"published",...}` line per hour, starting around `20260927-22` (no checkpoint yet, so it
  starts at the earliest line on disk; at most 72 hours in one run);
- for each hour `lines_in == processed + dropped + malformed`, `pod_list_error: null`;
- rolled `.gz` files moved to `done/<day>/`; the step15-era and `2tklb` leftover `.log` files moved to
  `done/<day>/…orphan` and listed in `orphans_moved`;
- `legacy-shared/`, `sizetest/`, `movetest/`, `polaris-sizetest-*` untouched.

If the pod fails: `ErrImageNeverPull` → step 1 did not reach OrbStack's Docker; `Permission denied`
on the PVC → uid/gid in `charts/polaris-log-batch/values.yaml` must equal Polaris's (10000/10001);
`pod_list_error` set → RBAC or `polaris.podSelector`.

### 4. Let the schedule run once
After the next HH:03, `kubectl -n datahub-hynix get jobs` shows a `polaris-log-batch-<n>` Job that
published exactly one hour.

### 5. Parity on real logs (optional, strong)
Copy one hour's files out (`kubectl exec … cat` — the Polaris image has no tar/zcat), then
`pip install lupa && python3 logging/scripts/step16-batch-lua-parity.py --file <files…> --hour YYYYMMDD-HH`.
Expected differences only of the documented kind: an error before its resource's first success
(SPEC §9.1).

### 6. Later
- Run next to Fluent Bit tiers 2/3 for a while and reconcile counts (local only — production Fluent Bit
  is not ours).
- Hand the Observability team the contract: directory layout, file names, **`aggregated-logs/H.jsonl`
  appears only after `processed-logs/H.jsonl` is complete**, `event_id` as `_id`, 3-day pickup window.
- Production: the image goes through Jenkins to the internal registry (`image.repository`,
  `pullPolicy: IfNotPresent`); the chart gets its own ArgoCD Application; the log PVC must be RWX or
  Polaris + the Job pinned to one node (`affinity`); size `resources.limits.memory` to an hour of
  production traffic.

## Things that will bite you

- **`helm upgrade` without `-f`** reuses old values. Always `-f <chart>/values.yaml`.
- **ConfigMap-only Polaris upgrades roll no pods.** Restart the Deployment yourself.
- **The batch chart restates Polaris facts** under `polaris:` (claim, logsDir, podPrefix, podSelector).
  Change one side, change the other.
- **The Job pod must never carry Polaris's selector labels** (it would receive catalog traffic).
- **`maxBackupIndex` deletes.** It bounds `.N` rolls within one hour; the step15 control lost 1929
  lines to it before the limit was raised for the test.
- **Rotation is lazy**: no file for an idle hour; that is why the batch reads current files too.
- **Cowork mount quirks**: git leaves `.git/*.lock` files unless deletion is allowed (this session had it
  allowed and removed them); `isort` cannot rewrite in place (format a copy and write it back); run
  pytest with `PYTHONDONTWRITEBYTECODE=1`.
- **The VM cannot run the full suite** (no pandas etc.) — only the two batch test modules were run.

## Where things are

| | |
|---|---|
| Logic, detailed (Korean) | `logging/SPEC-polaris-log-batch.ko.md` |
| Decisions and their order | `logging/PLAN-polaris-log-batch-2026-09-27.md` |
| The shared-file incident and measurements | `.memory/active-issues/platform.md` `#48` |
| Session narratives | `.memory/sessions/2026-09-27-polaris-log-batch-step1.md`, `.memory/sessions/2026-09-28-polaris-log-batch-p1a.md` |
| Tests | `tests/test_polaris_log_batch.py`, `tests/test_polaris_log_policy.py` |
| Test harnesses | `logging/scripts/step15-shared-file-size-rotation-test.sh`, `logging/scripts/step16-batch-lua-parity.py` |
| Traffic generator used by step15 | `diagnostics/ladders/log-coverage/run_traffic.py` (import path fixed 09-28) |

## Uncommitted in the tree (not ours — left alone)

`.gitignore` (modified), `diagnostics/ladders/log-coverage/polaris_api_traffic_v1.ipynb` (outputs from
Kade's notebook runs), `.claude/settings.local.json`, `.ignore`, `.mcp.json`.
