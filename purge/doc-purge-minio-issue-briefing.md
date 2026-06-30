# Polaris Purge → MinIO: Why It Fails, and How to Verify

**For:** platform/data engineers running Apache Polaris 1.3.0 on MinIO without STS
**TL;DR:** `DROP TABLE ... purgeRequested=true` returns 204 and removes the catalog
record, but the data/metadata files are **never deleted from MinIO**. They orphan
permanently. Root cause is a Polaris credential-subscoping issue in the async cleanup
task (apache/polaris#379), triggered by the absence of STS credential vending. This is
**not** a MinIO problem, a permission problem, or a connectivity problem.

---

## 1. Symptom

```
DELETE /api/catalog/v1/{cat}/namespaces/{ns}/tables/{tbl}?purgeRequested=true
  → HTTP 204
  → table gone from catalog (GET returns 404)
  → BUT the table's files remain in MinIO forever:
       .../data/<uuid>.parquet
       .../metadata/00000-....metadata.json
```

Files from purges done many minutes ago stay present. This is **not** async timing —
they never get deleted.

---

## 2. Proven causal chain (from Polaris logs)

Captured via OpenSearch (`k8s-logs-*`, container `benchmarks-polaris`, by `loggerName`):

```
T+0.000  IcebergCatalog        "Scheduled cleanup task <id> for table"
T+0.000  StorageAccessConfig…  Fetching client credentials for .../metadata
T+0.000  StorageCredentialCache  allowedWriteLocations=[]      ← ROOT SYMPTOM
T+0.001  TaskExecutorImpl      "Handling task entity id <id>"
T+0.001  TableCleanupTaskHandler "Handling table metadata cleanup task"
T+1.005  TaskExecutorImpl  WARN "Failed to handle task entity id <id>"
T+1.007  (retry) Handling task <id>
T+3.015  WARN Failed to handle task <id>
T+6.023  WARN Failed to handle task <id>   ... retries indefinitely
```

The cleanup task is handed credentials with an **empty write-location list**, so its
FileIO has no authority to delete. It fails and `TaskExecutorImpl` retries forever.

### The credential discrepancy (the key evidence)

```
Normal table data write (SUCCEEDS):
  tableLocation         = [.../tbl]
  allowedWriteLocations = [.../tbl]          ← write granted

Cleanup task credential fetch (FAILS):
  tableLocation         = [.../tbl/metadata]
  allowedReadLocations  = [.../tbl/metadata]
  allowedWriteLocations = []                  ← NO write granted
```

Both use session tokens (`s3.session-token` present), so the subscoping path IS
active — it just yields no write scope for the cleanup task.

---

## 3. Root cause

### Layer 1 — No STS in this deployment
The catalog storage config shows `stsEndpoint: null`. Polaris credential vending is
built around AWS STS AssumeRole to mint path-scoped temporary credentials. Without
STS, Polaris cannot mint write-scoped creds for the cleanup task → empty
write-locations.

### Layer 2 — apache/polaris#379 (the escape hatch is ignored)
Polaris has a flag for exactly the no-STS case:
`SKIP_CREDENTIAL_SUBSCOPING_INDIRECTION` → "skip subscoping, use static table-level
credentials for the FileIO instead." Intended for single-tenant / no-vending setups.

**Bug #379:** *"SKIP_CREDENTIAL_SUBSCOPING_INDIRECTION is ignored in
TaskFileIOSupplier."* The async cleanup task always tries to subscope and ignores the
flag. Reproduced upstream by "send a purge from a client that doesn't delete files
client-side (e.g. pyiceberg)" — exactly our case (REST/notebook purge).

So even setting the skip flag does **not** fix the cleanup task in affected versions.

### Why everything else works
Table create / write / read / metadata-write use a credential path that falls back to
the static MinIO creds correctly (we observed populated `allowedWriteLocations` for
normal writes). Only the **async cleanup/purge task** is routed through the
STS-dependent subscoping code that #379 leaves broken. That's why purge is the *only*
operation that fails.

---

## 4. What it is NOT (each ruled out by evidence)

```
✗ NOT a MinIO problem         — static creds delete objects fine (tested, below)
✗ NOT missing s3:DeleteObject — the static creds CAN delete
✗ NOT connectivity            — Polaris writes metadata to MinIO itself on create
✗ NOT RBAC / API              — the DELETE returns 204, not 403
✓ IS Polaris cleanup-task credential subscoping (no STS) + bug #379
```

---

## 5. Proof that deletion works WITHOUT STS (manual path)

Using the static MinIO credentials directly (the same key Polaris is configured with):

```
Part A — single object: write → DELETE (204) → gone.          ✅ MinIO deletes fine
Part B — purge a real table via Polaris → files orphaned;     ⚠️ confirms #379
         then delete those files directly with static creds → gone.  ✅ no STS needed
```

So data **can** be deleted correctly without STS — just not by Polaris's broken
cleanup task. We delete the orphans ourselves.

### Deletion-method gotchas (hit these in testing — save yourself the time)

```
❌ s3fs fs.rm(prefix, recursive=True)  → MissingContentMD5 (MinIO bulk-delete
                                          needs Content-MD5; s3fs omits it)
❌ s3fs fs.rm_file(key)                → NotImplementedError (this s3fs version)
✅ MinIO REST API + SigV4 (requests)   → clean single-object DELETE
✅ boto3 client.delete_object(...)     → also works (single delete)
✅ mc rm --recursive                   → MinIO client handles MD5 correctly

Also: s3fs CACHES listings. After deleting outside s3fs, call
fs.invalidate_cache(prefix) and fs.find(prefix, refresh=True), or you'll see
stale "still there" results for files that are actually gone.
```

---

## 6. Verify in the COMPANY environment

Read-only first, then optional cleanup. Adjust catalog/namespace/bucket names.

### Step 1 — Confirm the orphaning (READ-ONLY, safe on production)
```python
# For a table you will purge in a TEST catalog (don't test on real data):
#  1. create table + write a small file
#  2. purge via Polaris
#  3. wait 15s, then list the table's storage prefix
# If files remain → orphaning confirmed in the company env too.

import s3fs
fs = s3fs.S3FileSystem(key=KEY, secret=SECRET, use_ssl=False,
                       client_kwargs={"endpoint_url": MINIO_ENDPOINT})
fs.invalidate_cache(prefix)
remaining = [f for f in fs.find(prefix, refresh=True) if fs.info(f)["size"] > 0]
print(f"orphaned files: {len(remaining)}")
```

### Step 2 — Confirm the log signature (READ-ONLY)
```
In OpenSearch (company log store), filter:
  container = <polaris-container-name>
  loggerName: TableCleanupTaskHandler  OR  TaskExecutorImpl
Look for:
  "Scheduled cleanup task"   then
  "Failed to handle task entity id <id>"  (repeating)
And in StorageCredentialCache around the same requestId:
  allowedWriteLocations=[]
If you see these → same root cause confirmed.
```

### Step 3 — Confirm static-cred deletion works (the workaround)
```
Delete one orphaned object with the static MinIO creds (REST/boto3/mc).
If it deletes → the manual cleanup path is viable in production.
```

### Important checks specific to the company env
```
□ Does the company catalog config also have stsEndpoint: null?
   (GET /api/management/v1/catalogs/{cat} → storageConfigInfo)
□ What Polaris version is the company running? (#379 fix status)
□ Are there ALREADY orphaned files in production from past purges?
   → list a few known-purged table prefixes; check for leftover files
   → this has compliance implications if "deleted" data still exists
```

---

## 7. Fixes (in order of preference)

```
1. Upgrade Polaris to a version where #379 is fixed
   → cleanup task honors SKIP_CREDENTIAL_SUBSCOPING_INDIRECTION /
     falls back to static creds. Verify on the changelog/issue before upgrading.

2. Enable STS credential vending in MinIO (if feasible)
   → gives the cleanup task properly-scoped write creds. Bigger infra change.

3. Operational workaround (works TODAY, no Polaris change):
   → treat Polaris purge as "removes catalog record only"
   → run a scheduled orphan-cleanup job using static MinIO creds:
       a. after dropping a table, delete its storage prefix directly
          (REST API single-object DELETE per key, or `mc rm --recursive`)
       b. OR periodically sweep purged locations
   → for Spark-based cleanup, note Iceberg remove_orphan_files needs
     prefix_listing => true (Iceberg ≥1.10) so vended creds apply
     (see apache/iceberg#12254); otherwise it lists via Hadoop and misses creds
```

---

## 8. References

```
apache/polaris#379   SKIP_CREDENTIAL_SUBSCOPING_INDIRECTION ignored in TaskFileIOSupplier
apache/polaris#3742  Polaris vends temp creds despite stsUnavailable=true (S3-compatible)
apache/polaris#3640  Polaris can't connect to internal S3 without STS / credential vending
apache/iceberg#14980 DROP TABLE PURGE is best-effort
apache/iceberg#12254 remove_orphan_files prefix_listing for vended creds
Polaris config ref   SKIP_CREDENTIAL_SUBSCOPING_INDIRECTION, STORAGE_CREDENTIAL_* settings
```

---

## 9. One-paragraph summary (for a ticket / Slack)

> Polaris 1.3.0 `purgeRequested=true` removes the catalog record (204) but never
> deletes the table's files from MinIO — they orphan permanently. Root cause: the
> async cleanup task requests STS-style write-scoped credentials it can't get (we run
> MinIO without STS), so it receives empty write-locations, fails, and retries forever.
> The config flag meant to bypass subscoping for no-STS setups
> (`SKIP_CREDENTIAL_SUBSCOPING_INDIRECTION`) is ignored by the cleanup task due to
> apache/polaris#379. Proven from Polaris logs (`TableCleanupTaskHandler` → "Failed to
> handle task", `allowedWriteLocations=[]`). Not a MinIO/permission/connectivity issue:
> static MinIO creds delete files fine. Workaround until a fixed Polaris version: treat
> purge as metadata-only and delete orphaned files directly with static MinIO creds.
