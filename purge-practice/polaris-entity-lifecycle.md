# Polaris Entity Lifecycle Guide

**Scope:** Apache Polaris 1.3.0 — the full lifecycle of catalogs, namespaces, tables, and views, from creation through data writes to removal.

Two tracks — read the one that fits your role:

- **👤 System Manager** — you operate Polaris through the API.
- **📊 Data Manager** — you manage data and need the conceptual model, not the internals.

---

# 📊 Data Manager Track

## Key terms (read this first if these are new)

```
Polaris      The "catalog" service — an index of all your tables: their
             names, columns, and where their files are stored. Like a
             library catalog listing every book and its shelf.

PostgreSQL   The database holding that index (the metadata / catalog cards).
             Stores names and locations — NOT the actual data.

MinIO        The storage holding the real data files (Parquet files).
             Like the shelves holding the actual books.

Iceberg      The table format Polaris uses. It tracks table history as
             "snapshots" — each snapshot is a version of the table at a
             point in time, so you can see how data changed.

Snapshot     One saved version of a table's data. Writing new data creates
             a new snapshot; the old ones remain as history.
```

## The four entities (folder/file analogy)

```
Catalog      A top-level container — like a whole filing cabinet.
             Example: "bronze", "silver", "gold", "watchdog"

Namespace    A folder inside the cabinet — groups related tables.
             Can be nested (folders within folders).
             Example: "orders", "customers"

Table        The actual dataset — rows and columns, with data files.
             Example: "clean_orders"

View         A saved query — NOT data itself, just a stored SELECT
             statement that reads from tables. Holds no files.
             Example: "monthly_summary"
```

## Hierarchy and order

```
Catalog
  └── Namespace
        └── Table  (has data files in storage)
        └── View   (just a saved query, no files)

Create:  top-down   → catalog, then namespace, then table/view
Remove:  bottom-up  → table/view, then namespace, then catalog

You cannot remove a folder that still has things in it.
You cannot remove a cabinet that still has folders in it.
```

## The lifecycle as a story

```
1. CREATE
   System Manager creates a catalog (cabinet) and gives you access.
   You (or they) create namespaces (folders) and tables (datasets).

2. FILL (write data)
   Data is written into a table. Each write creates a new SNAPSHOT —
   a saved version. Old snapshots remain, so the table has history.
   The actual rows live as files in storage (MinIO).

3. USE (read / query)
   Query engines (Spark, Trino) read the table through Polaris.
   Views let you save common queries for reuse.
   Reading never changes the data.

4. EVOLVE
   You can add columns, write more data (new snapshots), or update rows.
   Iceberg keeps the history so nothing is lost unexpectedly.

5. RETIRE (drop)
   When a table is no longer needed, it's dropped.
   → Drop without purge: the dataset is "unlisted" but its files remain
     (recoverable).
   → Drop with purge: the dataset AND its files are permanently deleted.
```

## What "purge" means for your data

```
Dropping a table has two modes:

Without purge (safe default):
  → The table vanishes from the catalog
  → Its data files stay in storage
  → A mistake can be undone → data recovered

With purge (intended to be permanent):
  → The table vanishes from the catalog
  → Intended: data files also deleted
  → In our current setup: data files are NOT actually deleted yet
    (async cleanup task fails — files left behind)

Important right now:
  → purge does NOT free storage space in our environment
  → "purged" data still physically exists until manually cleaned
  → for privacy/compliance, do not assume purged data is erased —
    confirm with your System Manager

Views:
  → A view is just a saved query; it holds no data files
  → Dropping a view removes the saved query only
  → The tables it read from are untouched
```

## Safe-handling rules

```
1. Always remove bottom-up: table → namespace → catalog.
   Trying to skip levels gives "not empty" errors.

2. When unsure, drop WITHOUT purge.
   Unlisted files can be cleaned up later by the System Manager.
   Purged data is gone forever.

3. Views are safe to drop — they never delete data.

4. If a drop fails with an error code, don't retry blindly.
   Note the error and ask your System Manager (see Troubleshooting Guide).

5. Production data (bronze/silver/gold) should rarely be purged.
   Purge is mainly for temporary or test data.
```

---

# 👤 System Manager Track

## Entity hierarchy and dependency order

```
Catalog (management API)
  └── Namespace (catalog API)
        └── Table  → metadata in PostgreSQL + data files in MinIO
        └── View   → metadata in PostgreSQL only (no data files)

Create order (top-down):   catalog → namespace → table/view
Delete order (bottom-up):  table/view → namespace → catalog

Enforced: cannot drop a non-empty namespace (409) or non-empty catalog (400).
```

## Catalog lifecycle

```
CREATE   POST /api/management/v1/catalogs
         → body: name, type INTERNAL, storageConfigInfo (S3/MinIO),
           properties (default-base-location, purge configs)

CONFIGURE PUT /api/management/v1/catalogs/{name}
         → read entityVersion (flat), merge properties, PUT
         → set purge flags here

GRANT    PUT /catalogs/{name}/catalog-roles/{role}/grants
         → assign privileges to catalog roles

DROP     DELETE /api/management/v1/catalogs/{name}
         → must be empty first
         → ?purgeRequested=true also removes base location in MinIO
```

## Namespace lifecycle

```
CREATE   POST /api/catalog/v1/{catalog}/namespaces
         → body: namespace as array ["orders"], optional properties

NEST     POST with ["orders", "sub"] for nested namespace

LIST     GET /api/catalog/v1/{catalog}/namespaces
         → returns namespaces as arrays

DROP     DELETE /api/catalog/v1/{catalog}/namespaces/{ns}
         → must be empty (no tables/views/child namespaces)
```

## Table lifecycle

```
CREATE   POST /{catalog}/namespaces/{ns}/tables
         → body: name, location, schema (fields with id/name/type/required)
         → returns format-version 2, current-snapshot-id -1 (empty)

WRITE    (see "Iceberg data write flow" below)

READ     GET /{catalog}/namespaces/{ns}/tables/{table}
         → returns metadata, snapshots, current-snapshot-id

UPDATE   POST /{catalog}/namespaces/{ns}/tables/{table}
         → updateTable: requirements + updates (set-properties,
           add-snapshot, set-snapshot-ref)

DROP     DELETE /{catalog}/namespaces/{ns}/tables/{table}
         → without purge: metadata removed, MinIO files remain (no cleanup task)
         → ?purgeRequested=true: needs TABLE_WRITE_DATA (=CATALOG_MANAGE_CONTENT)
           and drop-with-purge.enabled=true. Schedules async cleanup task.
           ⚠️ In our env that task FAILS (no STS) → files orphaned anyway.
```

## View lifecycle

```
CREATE   POST /{catalog}/namespaces/{ns}/views
         → body MUST include:
           name
           default-namespace: [ns]        (top level)
           schema: with schema-id: 0
           view-version: (kebab-case, NOT viewVersion)
             version-id, timestamp-ms, schema-id,
             default-namespace: [ns], summary, representations (SQL)
           location

DROP     DELETE /{catalog}/namespaces/{ns}/views/{view}
         → metadata-only if purge-view-metadata-on-drop=false
         → otherwise tries to delete metadata file from MinIO
```

## Iceberg data write flow (no Spark)

Writing data without a compute engine is a 3-step process. Polaris stores
the metadata; you write the files.

```
Step 1 — Write the Parquet data file to MinIO
  → use direct MinIO credentials (s3fs / pyarrow)
  → endpoint_url goes in client_kwargs, not top-level
  → path: {table-location}/data/{uuid}.parquet

Step 2 — Write Iceberg metadata files to MinIO
  a) manifest file (.avro)      → lists the data file(s) added
  b) manifest-list file (.avro) → lists the manifest(s)
  → both written to {table-location}/metadata/

Step 3 — Commit the snapshot (Polaris API)
  POST /{catalog}/namespaces/{ns}/tables/{table}
  → action: add-snapshot, referencing the manifest-list path
  → then a SEPARATE request: action: set-snapshot-ref (main branch)
```

### Polaris 1.3.0 commit quirks (confirmed by testing)

```
✅ requirements can be []
✅ add-snapshot and set-snapshot-ref must be SEPARATE requests
✅ manifest-list must be a real written path (empty string → 400)
❌ do NOT include sequence-number in the snapshot body (→ 400)
✅ response is flat: read current-snapshot-id from metadata
```

## What happens in MinIO vs PostgreSQL at each step

```
Action                  PostgreSQL (metadata)        MinIO (storage)
──────────────────────────────────────────────────────────────────────
Create catalog          catalog record               (base location noted)
Create namespace        namespace record             —
Create table            table record, snapshot -1    metadata/00000.json
Write Parquet           —                            data/{uuid}.parquet
Write manifests         —                            metadata/*.avro
Commit snapshot         snapshot record added        metadata/0000N.json
Drop table (no purge)   table record removed         files REMAIN (orphaned)
Drop table (purge)      table record removed         files ORPHANED* (not deleted)
Drop view               view record removed          metadata file orphaned*
Drop catalog (purge)    all records removed          files ORPHANED* (not deleted)

* In our environment purge does NOT delete MinIO files: the async cleanup
  task fails (empty write-location credentials) and retries forever.
  By design these would be DELETED.
```

## Drop behavior matrix (VERIFIED in our environment)

```
Entity     Mode          PostgreSQL    MinIO (OUR ENV)         Reversible?
──────────────────────────────────────────────────────────────────────────────
Table      no purge      removed       files remain            ✅ recreate+register
Table      purge         removed       files ORPHANED*         ✅ (until manual cleanup)
View       no purge      removed       metadata file orphaned* ✅ (no data anyway)
View       purge=true +  removed       metadata file orphaned* ✅
           drop-purge=true
View       purge=true +  403 — BLOCKED —                       n/a
           drop-purge=false
Namespace  drop          removed       —                       ✅ recreate
Catalog    purge         removed       files ORPHANED*         ✅ (until manual cleanup)

* VERIFIED: In our environment, purge removes the PostgreSQL record (204) but
  does NOT delete MinIO files. The async cleanup task is scheduled, runs, and
  FAILS — it receives credentials with an empty write-location list (no STS to
  subscope them), so it cannot delete, and retries forever.
  Proven by writing a real 727-byte Parquet file, purging, and counting:
  data files 1→1, metadata files 1→1 (both orphaned).
  By DESIGN purge SHOULD delete files.
  See the Purge Troubleshooting Guide → Root cause for the full traced chain.
```

### What purgeRequested=true actually does (verified)

```
By design:     remove catalog record + delete data & metadata files from MinIO
In our env:    remove catalog record ONLY; data + metadata files orphaned

So purgeRequested=true currently does NOT reclaim storage. Treat it as
permanent anyway — once the storage issue is fixed, it WILL delete files.
```

## RBAC at each lifecycle stage

```
Stage              Privilege needed
──────────────────────────────────────────────────────
Create catalog     service_admin (management API)
Create namespace   NAMESPACE_CREATE
Create table       TABLE_CREATE
Write data         TABLE_WRITE_DATA
Read data          TABLE_READ_DATA
Create view        VIEW_CREATE
Drop table         TABLE_DROP
Drop table+purge   TABLE_DROP + TABLE_WRITE_DATA  (= CATALOG_MANAGE_CONTENT)
Drop view          VIEW_DROP
Drop namespace     NAMESPACE_DROP
Drop catalog       service_admin

Tip: CATALOG_MANAGE_CONTENT bundles create/read/write/drop for
     tables, views, and namespaces — convenient for trusted roles.
```

## Orphaned files note

```
Two distinct sources of orphaned files in MinIO:

1. Drop WITHOUT purge (by design):
   → leaves Parquet + metadata files; no cleanup task is scheduled
   → expected, recoverable; the no-purge default exists for this

2. Drop WITH purge (a BUG in our environment):
   → schedules an async cleanup task that FAILS and retries forever
   → files orphan even though purge was requested
   → root cause: no STS → the cleanup task gets empty write-location
     credentials and cannot delete (see Troubleshooting Guide → Root cause)

So in our environment, BOTH no-purge and purge leave files — but for
different reasons (no-purge never tries; purge tries and fails).

Cleanup options (API-only, no redeploy):
  → Reliable now: delete orphaned files directly with the static MinIO
    credentials (MinIO REST API / mc), since those creds CAN delete
  → Proper fix: a Polaris version where the cleanup task works without
    STS (see Troubleshooting Guide), or enable STS credential vending

NOTE: "drop WITH purge to reclaim space" does NOT currently work here —
purge does not delete files until the cleanup-task issue is fixed.
```

## Quick lifecycle checklist

```
Setup a new working area:
  □ catalog created (storage config + purge flags set)
  □ catalog roles granted appropriate privileges
  □ namespace created
  □ table created with schema

Write data:
  □ Parquet written to MinIO data/
  □ manifest + manifest-list written to MinIO metadata/
  □ add-snapshot committed
  □ set-snapshot-ref (main) committed
  □ verify current-snapshot-id updated

Tear down (bottom-up):
  □ tables dropped (purge only if intentional)
  □ views dropped
  □ namespaces dropped
  □ catalog dropped
```
