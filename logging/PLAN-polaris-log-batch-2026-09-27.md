# PLAN — Polaris logging as an hourly batch (2026-09-27)

**Status:** step 1 (Polaris writes rotated log files to a PVC) is **written, not rolled**.
Steps 2–6 are not started. Decisions below are Kade's, 2026-09-27.

## Target flow

```
Polaris ──JSON, hourly .gz roll──▶ PVC <fullname>-logs  (/deployments/logs)
K8s CronJob (Python, "3 * * * *" Asia/Seoul) ──▶ processed-logs/ + aggregated-logs/ on the same PVC
Observability team (theirs from here) ──fetch from PVC──▶ OpenSearch
```

The batch job is a port of `releases/fluent-bit/polaris_access_log.lua`: **processed logs** are
the tier-2 detail documents (policy v5), **aggregated logs** are the tier-3 schema-v6 report rows
(summary / resource / principal / app_dropped) with a 1-hour window (#47's 3600 s).

## PVC layout

```
/deployments/logs/
  polaris.log                          active file (Polaris only)
  polaris.log.2026-09-27-10.gz         hourly roll; .N.gz extras if size rotation ever fires
  done/20260927/                       originals after processing (job moves them)
  processed-logs/20260927-10.jsonl     one event per line + event_id
  aggregated-logs/20260927-10.jsonl    v6 report rows for the hour
  malformed/20260927-10.jsonl          unparseable lines (raw text + source + line no)
  .tmp/  .state/checkpoint.json  .state/lock
```

## Decisions

| # | decision |
|---|---|
| Rotation | `fileSuffix: .yyyy-MM-dd-HH.gz`, `maxFileSize: 2Gi` (size roll unreachable, cannot be disabled), `maxBackupIndex: 50`, `rotate-on-boot=false` |
| File | **one `polaris.log` for the whole Deployment** (Kade). Every replica gets the same ConfigMap path; the HPA does not create per-pod files. Safe only with one writer — see active-issues `#48` |
| D2 | the HH:03 run reads **every** source for the previous hour (`-10.gz`, `-10.1.gz`, …). A source for H arriving later → rebuild H from `done/` + the new file, replace atomically; stable `event_id` makes re-indexing idempotent |
| D3 | malformed line → `malformed/`, rest of the file processed, counted as `rejected`. A `.gz` that fails to decode is retried 3 runs, then the whole file moves to `malformed/` |
| D4 | **KST**: `TZ=Asia/Seoul` on Polaris (the suffix uses the JVM zone), `timeZone: Asia/Seoul` on the CronJob, fixed +09:00 in Python |
| D5 | the job deletes `done/`, outputs and `malformed/` **3 days after publication** (checkpoint time, not the hour in the name). 3 days is the Observability team's pickup deadline |

## Batch algorithm (step 3)

0. `flock .state/lock`, exit 0 if held (`concurrencyPolicy: Forbid` as well).
1. Load checkpoint. 2. Inbox = rotated `.gz` not in checkpoint, mtime older than 120 s.
3. Group by hour from the file name. 4. Per hour, oldest first: decode all sources (gzip CRC at
   EOF), apply policy → processed + aggregates; assert `in = processed + dropped + counted_404 +
   rejected`; write `.tmp/`, fsync, `os.replace`, fsync dirs; update checkpoint (tmp + replace);
   move sources to `done/`. 5. Retention sweep.

Crash anywhere → the next run recomputes to identical bytes (outputs are a pure function of the
sources), so every step is idempotent.

## Steps

1. **Polaris config + PVC** — `charts/polaris/values.yaml`, `templates/storage.yaml`. *Written.*
2. **Spike on OrbStack (Kade)** — checks below.
3. Batch script (`charts/polaris/files/log-batch/`, stdlib only) + `tests/test_polaris_log_batch.py`.
4. Parity: same raw input through `logging/scripts/step11-replay-window.py` (Lua) and the job; diff.
5. CronJob + ConfigMap templates in `charts/polaris`; parallel run with Fluent Bit tiers 2/3; reconcile.
6. Handover contract to the Observability team; retire tiers 2/3.

## Step 2 — what the spike must establish (from the running object)

```bash
kubectl config current-context                                   # must be orbstack
helm lint charts/polaris
helm upgrade --install benchmarks-polaris ./charts/polaris -n datahub-hynix --dry-run=client --debug
helm upgrade --install benchmarks-polaris ./charts/polaris -n datahub-hynix
kubectl -n datahub-hynix get pvc benchmarks-polaris-logs                     # Bound, class local-path
kubectl -n datahub-hynix exec deploy/benchmarks-polaris -- \
  grep -E 'quarkus.log.file|rotation' /deployments/config/application.properties
kubectl -n datahub-hynix exec deploy/benchmarks-polaris -- env | grep -E 'TZ|QUARKUS_LOG_FILE'
kubectl -n datahub-hynix exec deploy/benchmarks-polaris -- ls -l /deployments/logs
kubectl -n datahub-hynix exec deploy/benchmarks-polaris -- tail -2 /deployments/logs/polaris.log
```

- [ ] PVC Bound; pod `Running`; `polaris.log` exists and is **written by uid 10000** (local-path perms)
- [ ] each line is one JSON object (`QUARKUS_LOG_FILE_JSON_ENABLED` took effect), `timestamp` ends `+09:00`
- [ ] after the next hour + one request: `polaris.log.YYYY-MM-DD-HH.gz` exists, named in **KST**, and decompresses fully
      (the UBI9 image has no `zcat` — copy it out: `kubectl cp` then `gzip -t`)
- [ ] an idle hour produces no file; the late roll carries the hour of its content
- [ ] container restart mid-hour (`kill 1`) does **not** roll (rotate-on-boot=false) and nothing is lost
- [ ] console output and the Fluent Bit tiers are unchanged apart from the `+09:00` offset
