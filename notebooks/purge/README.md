# Purge / MinIO Behavior Tests

## Concept
What actually happens to the underlying **MinIO data files** when a Polaris table is dropped with `?purgeRequested=true`. Spans Polaris (catalog), MinIO (Parquet/metadata files), and Polaris logs surfaced via OpenSearch (`k8s-logs-*`, container `benchmarks-polaris`).

## Purpose
Prove, at the mechanism level, whether purge removes files or orphans them — and isolate the root cause — for a build running **without STS**.

## Notebooks
- `polaris_purge_practice.ipynb` — main purge walkthrough: write a real table, purge it, and observe MinIO + logs.
- `view_purge_behavior_test.ipynb` — the original 9-case (C1-C9) config/privilege/`purgeRequested`-param matrix for VIEW drops, plus the deletion-log check that first proved views never even attempt a cleanup task. Still the source of truth for views.
- `table_view_purge_privilege_test.ipynb` — extends the same matrix methodology to TABLE alongside VIEW, with a real committed Parquet/manifest/snapshot smoking-gun proof. Its first live run (2026-07-06) surfaced an unexpected 403 on table purge that led directly to the next notebook.
- `table_purge_privilege_test.ipynb` — **table-only**, supersedes the table portions of the notebook above. Adds a pre-flight `ensure_privilege()` check before every purge attempt and an explicit `purgeRequested` control in every matrix case, to fix that 403 and cleanly separate the CONFIG gate from the (newly discovered) PRIVILEGE gate. This is the current source of truth for table purge + privilege.
- `prove_minio_deletion_no_sts.ipynb` — direct-to-MinIO proof that file deletion itself works with static credentials (isolating the issue from MinIO/permissions/RBAC).

## How to run
1. Confirm Polaris, MinIO, and OpenSearch are reachable per `../src/config/local.yaml` (or `dev.yaml`).
2. **Restart & Run All**. The first cell bootstraps `../src` and imports the utils.

## Result / findings (bottom line)
Once authorized, `DROP TABLE ... ?purgeRequested=true` returns 204 and removes the catalog record, **but never deletes the data/metadata files from MinIO — they orphan permanently.** Root cause (proven): the async cleanup task receives storage credentials with an **empty write-location list** (no STS to subscope them), so it cannot delete the files and retries forever. The *file-orphan* behavior itself is **not** a MinIO, permission, connectivity, or RBAC problem — direct deletion with static MinIO credentials works fine. Tracks upstream Polaris issue #379; `dev.yaml` flag `purge_deletes_files: false` reflects this build.

**Getting authorized to even attempt the purge IS an RBAC problem, though (measured 2026-07-06):** `DROP TABLE ?purgeRequested=true` is gated by a distinct op, `DROP_TABLE_WITH_PURGE`, that **root/service_admin does not bypass** — unlike a plain table drop or a view drop, both of which root bypasses freely. `TABLE_DROP` alone does not authorize it; `CATALOG_MANAGE_CONTENT` does. When both the config gate (`drop-with-purge.enabled=false`) and the privilege gate (missing `CATALOG_MANAGE_CONTENT`) are closed at once, the PRIVILEGE 403 fires, not the CONFIG one. See `table_purge_privilege_test.ipynb` and `privilege/doc-privilege-results.md`.

> Note: `prove_minio_deletion_no_sts.ipynb` uses `s3fs` for the direct-deletion proof. The shared `../src/minio_rest.py` client deliberately avoids `s3fs` (company policy) — prefer it for new work.

## Reference docs
- `doc-purge-test-report.md` — full report with evidence.
- `doc-purge-troubleshooting.md` — troubleshooting log.
- `doc-read-after-write-rootcause.md` — read-after-write 500 root-cause analysis.
