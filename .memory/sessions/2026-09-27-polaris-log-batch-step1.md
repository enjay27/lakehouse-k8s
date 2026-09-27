# 2026-09-27 — Polaris logging to a PVC for an hourly batch job (step 1)

Kade redesigned Polaris logging: Polaris writes files to a PVC, a Python CronJob at HH:03 turns the
previous hour's rotated `.gz` into processed and aggregated JSONL, and the Observability team ships
those to OpenSearch. Plan: `logging/PLAN-polaris-log-batch-2026-09-27.md`.

## How the decisions landed
- **Lazy rotation.** Kade first read it as a config problem. It is not: Quarkus exposes only
  max-file-size / max-backup-index / file-suffix / rotate-on-boot, and JBoss rolls on the first write
  after the period. Accepted; the job must never assume hour H is complete at H+1:03.
- **One file vs per pod.** Asked whether the HPA makes per-pod files: it does not (checked in the
  chart — one ConfigMap path for every replica). Kade chose one `polaris.log` anyway → `#48`.
- **Size rotation.** Kade wanted hourly only. It cannot be disabled once a suffix is set, so
  `maxFileSize: 2Gi` makes it unreachable. Kade expected extras named `-10.gz.1`; the 09-09 PVC listing
  in `#40` shows the real form is `polaris.log.2026-09-09.1.gz` — index before `.gz`.
- `maxBackupIndex` is not irrelevant as first claimed: it deletes the oldest `.N` of an hour once
  exceeded, so 50, not 1.
- D2 rebuild-and-replace with `event_id`; D3 `malformed/`; D4 KST via `TZ` on the JVM (the suffix
  follows the JVM zone); D5 the job deletes after 3 days, counted from publication.

## Not verified
No helm or kubectl from Cowork, and `get.helm.sh` is blocked by the egress proxy, so not even
`helm template` ran. The values file parses as YAML and the four env vars and file block read back as
intended — that is all.
