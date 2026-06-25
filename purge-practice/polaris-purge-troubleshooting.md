# Polaris Purge Troubleshooting Guide

**Scope:** Apache Polaris 1.3.0 — diagnosing failures when dropping/purging catalogs, namespaces, tables, and views via the REST API, and understanding what purge actually does in our environment.

**Status of findings:** All behavior tables below were verified by direct testing against our cluster (API responses + direct MinIO observation), not assumed. Where a root cause requires cluster access we couldn't reach from Jupyter, it is marked as **needs System Engineer confirmation**.

Two tracks — read the one that fits your role:

- **👤 System Manager** — you operate Polaris: catalogs, RBAC, configuration via API.
- **📊 Data Manager** — you manage data (DS/DA); you decide what to keep/remove but don't operate Polaris internals.

---

# 📊 Data Manager Track

## Key terms (read first if these are new)

```
Polaris      The "catalog" service — an index of all tables: names,
             columns, and where files live. Like a library catalog.

PostgreSQL   The database holding that index (the catalog cards).
             Names and locations only — NOT the actual data.

MinIO        The storage holding the real data files.
             Like the shelves holding the actual books.

So a table = a catalog card (PostgreSQL) + the data files (MinIO).
```

## The most important finding for you

```
In our current environment, "purge" does NOT delete data files.

When you drop a table with purge:
  → the table disappears from the catalog (the card is removed)
  → BUT the actual data files stay in storage (orphaned)

This is a known issue: the background cleanup task that should delete files keeps failing (see System Manager
track). It means:
  → purge currently does NOT free up storage space
  → deleted data still physically exists in MinIO until cleaned manually
  → from a privacy/compliance view, "purged" data is NOT actually erased yet
```

## What "drop" and "purge" mean (and what actually happens here)

```
DROP (without purge):
  Intended:  remove catalog card, leave data files
  Here:      ✅ works as intended

PURGE (drop with purge):
  Intended:  remove catalog card AND delete data files
  Here:      ⚠️ removes catalog card ONLY; data files orphaned
             (async cleanup task fails — files not deleted)
```

## Why your drop might fail (plain language)

```
1. "Purge is turned off for this catalog"
   → A safety setting prevents purge. This is intentional protection.
   → Ask your System Manager if purge is genuinely needed.

2. "You're not allowed to purge"
   → Your access can drop the card but not request deletion of data.
   → Ask the System Manager.

3. "Namespace is not empty"
   → The folder still has tables in it. Remove tables first.

4. "Already exists"
   → Leftover with that name from before; needs cleanup before recreating.
```

## What's reversible vs permanent

```
Action                     In our environment
──────────────────────────────────────────────────────────────
Drop table (no purge)      Reversible — files remain in storage
Drop view                  Reversible — views hold no data
Drop table WITH purge      Card removed; files orphaned (recoverable
                           until someone manually cleans storage)
```

Note: once the cleanup-task issue is fixed, purge WILL permanently
delete files. Treat purge as permanent regardless, to be safe.

## When to ask your System Manager

```
Ask when you see:
  → "Unable to purge entity ... DROP_WITH_PURGE_ENABLED"
  → "not authorized for op DROP_TABLE_WITH_PURGE"
  → anything about "trash" or "stuck" entities
  → any drop returning an error code (403, 400, 409)

Note down: catalog/namespace/table name, exact error, and whether the
data is meant to be kept or destroyed.

Golden rule: if unsure whether data should be permanently deleted,
DROP without purge.
```

---

# 👤 System Manager Track

## Headline finding (fully proven from logs)

```
purgeRequested=true in OUR environment:
  → returns 204, removes the PostgreSQL catalog record
  → does NOT delete data (.parquet) OR metadata (.json) files from MinIO
  → both are orphaned (verified: real 727-byte Parquet, data 1→1, meta 1→1)

ROOT CAUSE (traced through Polaris logs — proven, not inferred):

The DELETE schedules an async cleanup task. That task RUNS but FAILS, and
retries forever. The failure is a CREDENTIAL-SUBSCOPING issue:

  When the cleanup task requests storage credentials for the table's
  /metadata sublocation, Polaris vends a session token with:
      allowedReadLocations  = [.../table/metadata]
      allowedWriteLocations = []          ← EMPTY

  With no write/delete scope, the task cannot delete the files. It fails
  ("Failed to handle task entity id ...") and TaskExecutorImpl retries
  indefinitely (~every 2s, backing off). Files are never removed.

Contrast — normal table data operations get FULL write scope:
      allowedWriteLocations = [.../table]   ← has write

So this is NOT connectivity (Polaris writes metadata fine) and NOT a
MinIO-side policy gap. It is Polaris's own credential subscoping returning
empty write-locations for the cleanup task's metadata-path request.

WHY the subscoping returns empty write-locations:
  This deployment has no STS (stsEndpoint: null). Polaris credential vending
  is built around STS AssumeRole to mint path-scoped write credentials.
  Without STS, the cleanup task cannot get write-scoped creds → empty list.
  Matches Apache Polaris issue #379 (the cleanup task ignores the
  SKIP_CREDENTIAL_SUBSCOPING_INDIRECTION flag meant for no-STS setups).
  → Confirm the running Polaris version vs #379 fix status (system engineer).
```

## Verified truth table — view drop behavior

```
                          drop-with-purge=false       drop-with-purge=true
──────────────────────────────────────────────────────────────────────────
purge-view-metadata=true  403 — view CANNOT drop      204 — view dropped,
                          (CONFIRMED)                  MinIO file orphaned
                                                       (CONFIRMED)

purge-view-metadata=false 204 — view dropped,         204 — view dropped,
                          MinIO file orphaned          MinIO file orphaned
                          (CONFIRMED)                  (CONFIRMED)
```

Key coupling discovered:
```
purge-view-metadata-on-drop=true REQUIRES drop-with-purge.enabled=true.
  → with metadata-purge=true and drop-purge=false, EVERY view drop → 403
  → the two configs are NOT independent
```

## Verified truth table — table purge behavior

```
Operation                          Result (CONFIRMED)
──────────────────────────────────────────────────────────────
Drop table, no purge flag          204; PostgreSQL record removed;
                                   MinIO files remain (expected)
Drop table, ?purgeRequested=true   204; PostgreSQL record removed;
 (drop-with-purge=true + grant)    MinIO data + metadata files ORPHANED
                                   (deletion silently fails)
Drop table, ?purgeRequested=true   403 "not authorized for op
 (without TABLE_WRITE_DATA)         DROP_TABLE_WITH_PURGE"
Drop table, ?purgeRequested=true   403 "Unable to purge ...
 (drop-with-purge=false)            DROP_WITH_PURGE_ENABLED"
```

## Quick reference — error → cause → fix

```
Error / symptom                              Cause                              Fix
──────────────────────────────────────────────────────────────────────────────────────────
"Unable to purge entity ...                  drop-with-purge.enabled=false      Set catalog property
 DROP_WITH_PURGE_ENABLED"                                                        drop-with-purge.enabled=true
                                                                                 (test catalogs only)

"not authorized for op                       catalog_admin lacks                Grant CATALOG_MANAGE_CONTENT
 DROP_TABLE_WITH_PURGE"                        TABLE_WRITE_DATA                    to catalog_admin

403 on view drop                             purge-view-metadata-on-drop=true   Set drop-with-purge=true,
                                              + drop-with-purge=false             OR set metadata-purge=false

"Namespace already exists" (409)             Leftover from failed run           Delete first, then recreate

"Namespace not empty" (409)                  Tables/views still inside          Drop children first

Catalog delete fails (400)                   Namespaces still inside            Drop all namespaces first

entityVersion = None / KeyError 'catalog'    Response is FLAT, not wrapped       Read r.json()["entityVersion"]

Config update silently ignored               Wrong entityVersion OR             Re-GET version; PUT with
                                              PATCH replaced properties          merged properties

Stuck entity in                              Async purge failed earlier         Enable purge + grant, then
 polaris-cleanup-trash-ns                                                        DELETE with purgeRequested=true

Purge returns 204 but files remain           Async cleanup task fails (no STS)  See "Root cause"
                                              (cleanup task fails)              (System Engineer task)
```

## no-purge vs purge — both leave files, different reasons (TESTED)

```
A clean A/B test (drop one table WITHOUT purge, one WITH purge) plus the
Polaris logs proves these are mechanically DIFFERENT:

  Drop WITHOUT purge:
    → files remain in MinIO
    → NO cleanup task is scheduled (verified in logs)
    → Polaris never even TRIES to delete → correct, passive behavior

  Drop WITH purge:
    → files remain in MinIO
    → a cleanup task IS scheduled ("Scheduled cleanup task <id> for table")
    → the task runs, FAILS (empty write-locations), retries forever

Verified in OpenSearch: every "Scheduled cleanup task" log line corresponds
to a PURGE operation. No no-purge table ever schedules one.

Implication: "use purge to actually delete files" does not work here. Until
the cleanup-task issue is fixed, purge ≈ no-purge in outcome (files remain),
the only difference being purge wastefully schedules a failing task.
```

## Catalog purge (TESTED)

```
A catalog cannot be deleted while non-empty (400 "not empty"). So a catalog
purge fans out to per-table purges first. Each per-table purge schedules a
cleanup task that fails the same way → ALL table files orphan.
Tested: catalog with 2 tables (4 files) → purge → 4 files orphaned.
```

## The three-layer purge model

A purge attempt passes through three gates. All three must allow it, AND the
storage layer must be reachable for files to actually be deleted.

```
Layer 1 — Catalog Configuration (is purge allowed?)
  polaris.config.drop-with-purge.enabled        gates TABLE purge
  polaris.config.purge-view-metadata-on-drop    gates VIEW metadata deletion
                                                 (and requires Layer-1 table flag)

Layer 2 — RBAC Privilege (are you allowed?)
  DROP_TABLE_WITH_PURGE requires TABLE_WRITE_DATA
  → catalog_admin alone does NOT include it
  → CATALOG_MANAGE_CONTENT bundles it

Layer 3 — API Request (how you ask)
  ?purgeRequested=true on the DELETE

Layer 4 — Async cleanup task (does deletion actually happen?)  ← OUR GAP
  After the 204, Polaris schedules a background TableCleanupTaskHandler to
  delete files. In our environment that task gets credentials with EMPTY
  write-locations, fails, and retries forever — files never deleted.
  (Connectivity is fine; Polaris writes metadata itself. It's the cleanup
  task's credential subscoping that breaks.)
```

## Privilege requirements table

```
Operation                  Required privilege(s)               Included in
─────────────────────────────────────────────────────────────────────────────────
DROP_TABLE                 TABLE_DROP                          TABLE_FULL_METADATA, catalog_admin
DROP_TABLE_WITH_PURGE      TABLE_DROP + TABLE_WRITE_DATA       CATALOG_MANAGE_CONTENT
DROP_VIEW                  VIEW_DROP                           VIEW_FULL_METADATA, catalog_admin
DROP_NAMESPACE             NAMESPACE_DROP                      NAMESPACE_FULL_METADATA
DROP_CATALOG               (management API)                    service_admin
```

## Config gotchas (cost the most debugging time)

### Gotcha 1 — Flat response structure
```python
# WRONG — there is no "catalog" wrapper
ver = r.json()["catalog"]["entityVersion"]   # KeyError / None

# RIGHT — fields are at the top level
ver   = r.json()["entityVersion"]
props = r.json().get("properties", {})
```
A wrong read makes `entityVersion` come back `None`, and every config update
then silently fails (optimistic-lock mismatch). This single bug caused hours
of "the purge flag won't enable" confusion.

### Gotcha 2 — Use PUT with merged properties, not PATCH
```python
r_get = requests.get(f"{BASE_MGMT}/catalogs/{CATALOG}", headers=h(tok))
cat = r_get.json()
merged = {**cat.get("properties", {}),                       # preserve existing
          "polaris.config.drop-with-purge.enabled": "true"}  # add new
requests.put(f"{BASE_MGMT}/catalogs/{CATALOG}", headers=h(tok),
             json={"currentEntityVersion": cat["entityVersion"], "properties": merged})
```

### Gotcha 3 — entityVersion must be current
Updates use optimistic locking; a stale `currentEntityVersion` is rejected.
GET immediately before each update.

## Investigation methodology (so the next engineer isn't misled)

```
When checking whether purge actually deleted MinIO files:

1. Use RECURSIVE listing (fs.find), not fs.ls.
   → fs.ls only shows the immediate directory and catches a 0-byte
     directory MARKER named "metadata", not the real file.

2. IGNORE 0-byte objects.
   → S3/MinIO represents "folders" as 0-byte marker objects.
   → The real view metadata is a ~380-byte .gz.metadata.json one level
     deeper; the real table data is a .parquet under data/.

3. Use UNIQUE entity names per test (uuid suffix).
   → Reusing a name across runs accumulates orphaned files and makes
     before/after counts meaningless.

Following these three rules turned a confusing "1 file before, 1 after,
is that the same file?" into a clear, repeatable measurement.
```

## Root cause — fully traced causal chain

```
Proven from Polaris logs (loggerName + message, OpenSearch k8s-logs-*):

  T+0.000  DELETE /tables/{t}?purgeRequested=true → 204
  T+0.000  IcebergCatalog: "Scheduled cleanup task <id> for table"
  T+0.000  StorageAccessConfigProvider: fetch credentials for /metadata path
  T+0.000  StorageCredentialCache: allowedWriteLocations=[]   ← THE PROBLEM
  T+0.001  TaskExecutorImpl: "Handling task entity id <id>"
  T+0.001  TableCleanupTaskHandler: "Handling table metadata cleanup task"
  T+1.005  TaskExecutorImpl: WARN "Failed to handle task entity id <id>"
  T+1.007  retry → Handling task <id>
  T+3.015  WARN Failed to handle task <id>
  T+6.023  WARN Failed to handle task <id>   ... retries indefinitely

The cleanup task receives credentials with an EMPTY write-location list,
so it cannot delete the files. It fails and retries forever; files orphan.
```

### The credential discrepancy (the key evidence)

```
Normal table data write (succeeds):
  tableLocation         = [.../table]
  allowedWriteLocations = [.../table]        ← write granted

Cleanup task credential fetch (fails):
  tableLocation         = [.../table/metadata]
  allowedReadLocations  = [.../table/metadata]
  allowedWriteLocations = []                  ← NO write granted

Both use session tokens (s3.session-token present), so STS-style
subscoping IS active. The cleanup path simply gets no write scope.
```

### What this is NOT (ruled out by evidence)

```
✗ NOT connectivity — Polaris writes metadata to MinIO successfully
                     (it creates .metadata.json files itself)
✗ NOT async timing — files from purges 10+ minutes old still present;
                     re-checked at +10/+20/+30s, unchanged
✗ NOT a missing API privilege — the DELETE returns 204, not 403
✗ NOT a MinIO-side policy — the failure is in Polaris's own credential
                     subscoping (empty write-locations), before MinIO
```

### For the System Engineer — confirm + fix

```
This matches Apache Polaris / Iceberg known behavior where the async
TableCleanupTaskHandler cannot obtain delete-capable credentials.
Related issues: apache/polaris#1195, #289, #1448; iceberg#14980
(DROP TABLE PURGE is best-effort).

To confirm from the pod (full stack trace not always in OpenSearch):
  kubectl logs -n datahub-hynix <benchmarks-polaris-pod> \
    | grep -A30 "Failed to handle task" | head -60
  → look for the "Caused by:" line under the failed task

Likely fixes to evaluate (System Engineer / platform owner):
  1. Polaris version: check for a fixed release of the cleanup-task
     credential subscoping (the empty allowedWriteLocations bug).
  2. Storage config: the cleanup path scopes to /metadata; ensure the
     catalog storage role/credentials grant write+delete on the FULL
     table location, not just read on /metadata.
  3. If using static MinIO creds without STS: verify the FileIO the
     cleanup task uses receives delete-capable credentials.

Operational mitigation until fixed:
  → purge will NOT reclaim storage; treat orphaned files as expected
  → run a periodic orphan-file cleanup (Iceberg remove_orphan_files,
    or a scheduled MinIO lifecycle/sweep job) to reclaim space
```

## Safe cleanup recipe (idempotent, API-only)

```python
def safe_purge_catalog(catalog):
    """Drop a test catalog and all contents. Idempotent.
    NOTE: in the current environment this removes catalog records but
    leaves MinIO files orphaned until the cleanup-task issue is fixed."""
    tok = root_token()
    catalogs = requests.get(f"{BASE_MGMT}/catalogs", headers=h(tok)).json().get("catalogs", [])
    if not any(c["name"] == catalog for c in catalogs):
        print("nothing to clean"); return

    # Layer 1 — enable purge (flat read, merged PUT)
    cat = requests.get(f"{BASE_MGMT}/catalogs/{catalog}", headers=h(tok)).json()
    merged = {**cat.get("properties", {}),
              "polaris.config.drop-with-purge.enabled": "true",
              "polaris.config.purge-view-metadata-on-drop": "false"}
    requests.put(f"{BASE_MGMT}/catalogs/{catalog}", headers=h(tok),
                 json={"currentEntityVersion": cat["entityVersion"], "properties": merged})

    # Layer 2 — grant purge privilege
    requests.put(f"{BASE_MGMT}/catalogs/{catalog}/catalog-roles/catalog_admin/grants",
                 headers=h(tok),
                 json={"grant": {"type": "catalog", "privilege": "CATALOG_MANAGE_CONTENT"}})

    # Bottom-up: tables → views → namespaces (incl. trash) → catalog
    for ns in requests.get(f"{BASE_CAT}/{catalog}/namespaces", headers=h(tok)).json().get("namespaces", []):
        ns_name = ns[0] if isinstance(ns, list) else ns
        for t in requests.get(f"{BASE_CAT}/{catalog}/namespaces/{ns_name}/tables", headers=h(tok)).json().get("identifiers", []):
            requests.delete(f"{BASE_CAT}/{catalog}/namespaces/{ns_name}/tables/{t['name']}?purgeRequested=true", headers=h(tok))
        for v in requests.get(f"{BASE_CAT}/{catalog}/namespaces/{ns_name}/views", headers=h(tok)).json().get("identifiers", []):
            requests.delete(f"{BASE_CAT}/{catalog}/namespaces/{ns_name}/views/{v['name']}?purgeRequested=true", headers=h(tok))
        requests.delete(f"{BASE_CAT}/{catalog}/namespaces/{ns_name}", headers=h(tok))
    requests.delete(f"{BASE_MGMT}/catalogs/{catalog}?purgeRequested=true", headers=h(tok))
    print(f"✅ records purged for {catalog} (MinIO files may remain orphaned)")
```

## Manual orphan cleanup — the reliable workaround (TESTED)

```
Since the static MinIO credentials CAN delete (tested), the dependable way to
reclaim storage today is to delete orphaned files directly — NOT via Polaris.

Pattern:
  1. drop the table via Polaris (removes catalog record)
  2. delete the table's storage prefix directly with static MinIO creds

Deletion method matters (we hit two walls):
  ❌ s3fs fs.rm(prefix, recursive=True) → MissingContentMD5
       (MinIO bulk DeleteObjects needs Content-MD5; this s3fs/botocore omits it)
  ❌ s3fs fs.rm_file(key)               → NotImplementedError (this s3fs version)
  ✅ MinIO REST API + SigV4 (requests)  → clean single-object DELETE
  ✅ boto3 client.delete_object(...)    → also works
  ✅ mc rm --recursive                  → MinIO client handles MD5 correctly

s3fs caching gotcha:
  s3fs caches directory listings. After deleting OUTSIDE s3fs, call
  fs.invalidate_cache(prefix) and fs.find(prefix, refresh=True), or you'll see
  stale "still there" results for files that are actually gone.
```

## Debugging the logs in OpenSearch — query pitfalls

```
Polaris logs land in k8s-logs-* (container benchmarks-polaris), with fields
level, message, loggerName, mdc.requestId. Two traps cost real time:

1. should + minimum_should_match=1 matches EVERYTHING
   → two different filters returning identical counts = the giveaway
   → use must (AND) to tie a log line to a specific entity

2. match_phrase on hyphenated values FAILS on the analyzed message field
   → the analyzer splits "withPurge-b37ed6" into separate tokens, so
     match_phrase "withPurge-" never matches (returns 0 — but it shows in
     the OpenSearch UI, which does substring matching)
   → fix: match a stable phrase ("Scheduled cleanup task") then substring-
     filter in Python ("withPurge-" in message)

To trace the cleanup-task failure, query:
  container = benchmarks-polaris
  loggerName: TableCleanupTaskHandler  OR  TaskExecutorImpl
  → "Scheduled cleanup task" then "Failed to handle task" (repeating)
  → allowedWriteLocations=[] near the same requestId
```

## Production safety note

```
DROP_WITH_PURGE_ENABLED = false is the correct production default.

bronze / silver / gold  →  drop-with-purge.enabled = false (protect data)
test / watchdog         →  drop-with-purge.enabled = true  (clean test data)

Until the cleanup-task credential issue is fixed, be aware that purge does
NOT reclaim storage in any catalog — it only removes catalog records.
Plan periodic orphan-file cleanup (Iceberg remove_orphan_files or a MinIO
sweep job) to reclaim space.
```
