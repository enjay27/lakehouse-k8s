# PLAN — Polaris logging as an hourly batch (2026-09-27)

**Status:** step 1 (Polaris writes rotated log files to a PVC) is **written, not rolled**.
Steps 2–6 are not started. Decisions below are Kade's, 2026-09-27.

## Target flow

```
Polaris ──JSON, hourly .gz roll──▶ PVC polaris-logs-pvc  (/deployments/logs)
K8s CronJob (Python, "3 * * * *" Asia/Seoul) ──▶ processed-logs/ + aggregated-logs/ on the same PVC
Observability team (theirs from here) ──fetch from PVC──▶ OpenSearch
```

The batch job is a port of `releases/fluent-bit/polaris_access_log.lua`: **processed logs** are
the tier-2 detail documents (policy v5), **aggregated logs** are the tier-3 schema-v6 report rows
(summary / resource / principal / app_dropped) with a 1-hour window (#47's 3600 s).

## PVC layout

```
/deployments/logs/
  polaris-<pod>.log                    active file, one per pod (Polaris only) — read in place, never moved
  polaris-<pod>.log.2026-09-27-10.gz   hourly roll per pod; .N.gz extras if size rotation ever fires
  legacy-shared/                       the shared-file era (2026-09-27 18:34–rollout), quarantined by hand
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
| File | **one file per pod**, `polaris-${HOSTNAME}.log` (Kade, 2026-09-27; **measured 2026-09-28 by step15: a shared file lost 1780/4000 lines under rotation, per-pod lost 0**). First rolled as one shared `polaris.log`; `#48` showed two pods overwrite each other's hourly rolls. The job merges every pod's lines for hour H into ONE processed and ONE aggregated file, so downstream still sees one file per hour. **Orphans need no special case** (2026-09-28, see *Selection*): a removed pod's unrotated `polaris-<pod>.log` is read like any other file. No sealing, no RBAC, the job never renames a file a JVM may hold |
| D2 | **SELECT BY TIMESTAMP, NOT BY FILE** (Kade, 2026-09-28). The HH:03 run reads every pod's `.gz` rolls **and every pod's current `.log`**, and keeps only lines whose `timestamp` falls in the previous hour `[H:00:00, H+1:00:00)` KST. At 11:03 a current file holds 10:xx and 11:00–11:03 lines; the job takes the 10:xx ones. **No sort** — OpenSearch orders by the `timestamp` field. Because current files are read, every line of H exists on disk at H+1:03, so the late-file rebuild of the first design is gone. `event_id` = sha1 of the raw line: the same line read from a `.log` and later from its `.gz` gets the same id |
| D3 | malformed line → `malformed/`, rest of the file processed, counted as `rejected`. A `.gz` that fails to decode is retried 3 runs, then the whole file moves to `malformed/` |
| D4 | **KST**: `TZ=Asia/Seoul` on Polaris (the suffix uses the JVM zone), `timeZone: Asia/Seoul` on the CronJob, fixed +09:00 in Python |
| D5 | the job deletes `done/`, outputs and `malformed/` **3 days after publication** (checkpoint time, not the hour in the name). 3 days is the Observability team's pickup deadline |

## Batch algorithm (step 3) — revised 2026-09-28

**Target hour.** A run at `HH:03` publishes every hour from `last_published + 1` through `HH-1`, oldest
first (catch-up after missed runs is automatic). The checkpoint is **per hour**, not per file.

**Selection for hour H** (why it is complete and never double-counts):
- Candidates: every `polaris-<pod>.log` and `polaris-<pod>.log.<hour>[.N].gz` whose **mtime ≥ H:00:00**.
  A file last written before H cannot hold an H line. This one rule covers rolls of H, the few
  boundary-skew lines a roll of H+1 can open with, current files, and orphans of removed pods.
- Keep a line iff its `timestamp` ∈ `[H:00:00, H+1:00:00)`; parse the offset, compare in KST.
- **Current files are read while Polaris writes them.** Only newline-terminated lines count; an
  unterminated last line is ignored while the file's mtime is < 120 s old, and goes to `malformed/`
  once older (a pod killed mid-write).
- An idle pod that later rolls its file to `…-HH.gz` re-exposes lines of an already-published hour;
  the per-hour checkpoint never reopens that hour, and the mtime rule keeps old rolls out of later hours.

**Publish H.** Apply policy v5 → processed + aggregates; assert `in = processed + dropped + counted_404
+ rejected`; write `.tmp/`, fsync, `os.replace` into `processed-logs/` and `aggregated-logs/`, fsync
dirs; then checkpoint `H` (tmp + replace) with the source files, sizes and counts.

**Housekeeping.** After H is checkpointed, rolls named for hours ≤ H move to `done/YYYYMMDD/` (a roll
of H cannot contain lines of H+1: the first H+1 record is what rotates the file). Current `.log` files
are never moved. Retention (D5) deletes `done/`, outputs, `malformed/` and orphaned `.log` files
(mtime > 3 days).

`flock .state/lock` + `concurrencyPolicy: Forbid`. A crash anywhere → the next run redoes the
unpublished hour from files still in place, to identical bytes.

## Steps

1. **Polaris config + PVC** — `charts/polaris/values.yaml`; the claim is `logging/k8s/polaris-logs-pvc.yaml`,
   created **before** the release and outside it, referenced by `logging.file.storage.existingClaim`. *Written.*
2. **Spike on OrbStack (Kade)** — checks below.
3. Batch script (`charts/polaris/files/log-batch/`, stdlib only) + `tests/test_polaris_log_batch.py`.
4. Parity: same raw input through `logging/scripts/step11-replay-window.py` (Lua) and the job; diff.
5. CronJob + ConfigMap templates in `charts/polaris`; parallel run with Fluent Bit tiers 2/3; reconcile.
6. Handover contract to the Observability team; retire tiers 2/3.

## Step 2 — what the spike must establish (from the running object)

**`-f charts/polaris/values.yaml` is not optional.** Without any `-f`/`--set`, Helm prints
`copying values from old release` and re-applies the previous revision's user-supplied values
(the old values.yaml copy, `logging.file.enabled: false`) OVER the new chart defaults. First try on
2026-09-27 rendered `existingClaim: polaris-logs-pvc` (a new key, so it came from the chart
default) next to `quarkus.log.file.enabled=false` (an old key, so the old revision won).

```bash
kubectl config current-context                                   # must be orbstack
kubectl apply -f logging/k8s/polaris-logs-pvc.yaml -n datahub-hynix   # FIRST; Pending until a pod mounts it
helm lint charts/polaris
helm upgrade --install benchmarks-polaris ./charts/polaris -f charts/polaris/values.yaml -n datahub-hynix --dry-run=client --debug
helm upgrade --install benchmarks-polaris ./charts/polaris -f charts/polaris/values.yaml -n datahub-hynix
kubectl -n datahub-hynix get pvc polaris-logs-pvc                            # Bound after the roll, class local-path
kubectl -n datahub-hynix exec deploy/benchmarks-polaris -- \
  grep -E 'quarkus.log.file|rotation' /deployments/config/application.properties
kubectl -n datahub-hynix exec deploy/benchmarks-polaris -- env | grep -E 'TZ|QUARKUS_LOG_FILE'
kubectl -n datahub-hynix exec deploy/benchmarks-polaris -- ls -l /deployments/logs
kubectl -n datahub-hynix exec deploy/benchmarks-polaris -- sh -c 'tail -2 /deployments/logs/polaris-$HOSTNAME.log'
```

- [x] PVC Bound; pod `Running`; `polaris.log` exists and is **written by uid 10000** (local-path perms) — 2026-09-27
- [x] each line is one JSON object (`QUARKUS_LOG_FILE_JSON_ENABLED` took effect), `timestamp` ends `+09:00` — 2026-09-27
- [x] after the next hour + one request: `polaris.log.YYYY-MM-DD-HH.gz` exists, named in **KST**, and decompresses fully — `-18.gz`, 18:35–18:51 only
      (the UBI9 image has no `zcat` — copy it out: `kubectl cp` then `gzip -t`)
- [x] an idle hour produces no file; the late roll carries the hour of its content — 19–21 absent, `-18` rolled at 22:21
- [x] **FAILED PREMISE: a second replica appeared the same day (HPA)** — `#48` confirmed by experiment; switched to one file per pod
- [x] per-pod files: `polaris-<pod>.log` for each of 3 running pods, names = pod names (22:37)
- [x] after the hour: `polaris-<pod>.log.<hour>.gz` per pod that wrote — `bmt4t`, `rz56d` → `-22.gz` at 23:02
- [x] orphan: `2tklb` removed by the HPA; its file (22:37–22:48) is unrotated for good — the job seals it as `-22.gz`
- [x] shared-era files moved to `legacy-shared/` so the batch job never reads them (22:40)
- [ ] container restart mid-hour (`kill 1`) does **not** roll (rotate-on-boot=false) and nothing is lost
- [ ] console output and the Fluent Bit tiers are unchanged apart from the `+09:00` offset
