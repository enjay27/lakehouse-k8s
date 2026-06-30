# Purge / MinIO Behavior Tests

## Concept
What actually happens to the underlying **MinIO data files** when a Polaris table is dropped with `?purgeRequested=true`. Spans Polaris (catalog), MinIO (Parquet/metadata files), and Polaris logs surfaced via OpenSearch (`k8s-logs-*`, container `benchmarks-polaris`).

## Purpose
Prove, at the mechanism level, whether purge removes files or orphans them — and isolate the root cause — for a build running **without STS**.

## Notebooks
- `view_purge_behavior_test.ipynb` — observes purge behavior for views/tables and correlates with logs.
- `prove_minio_deletion_no_sts.ipynb` — direct-to-MinIO proof that file deletion itself works with static credentials (isolating the issue from MinIO/permissions/RBAC).

## How to run
1. Confirm Polaris, MinIO, and OpenSearch are reachable per `../src/config/dev.yaml`.
2. **Restart & Run All**. The first cell bootstraps `../src` and imports the utils.

## Result / findings (bottom line)
`DROP TABLE ... ?purgeRequested=true` returns 204 and removes the catalog record, **but never deletes the data/metadata files from MinIO — they orphan permanently.** Root cause (proven): the async cleanup task receives storage credentials with an **empty write-location list** (no STS to subscope them), so it cannot delete the files and retries forever. This is **not** a MinIO, permission, connectivity, or RBAC problem — direct deletion with static MinIO credentials works fine. Tracks upstream Polaris issue #379; `dev.yaml` flag `purge_deletes_files: false` reflects this build.

> Note: `prove_minio_deletion_no_sts.ipynb` uses `s3fs` for the direct-deletion proof. The shared `../src/minio_rest.py` client deliberately avoids `s3fs` (company policy) — prefer it for new work.

## Reference docs
- `doc-purge-test-report.md` — full report with evidence.
- `doc-purge-troubleshooting.md` — troubleshooting log.
- `doc-read-after-write-rootcause.md` — read-after-write 500 root-cause analysis.
