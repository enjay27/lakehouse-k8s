# Polaris Purge → MinIO: Test Report & Findings

**Environment:** Apache Polaris 1.3.0 on OrbStack K8s (`datahub-hynix`), MinIO storage, **no STS**
**Method:** Jupyter notebook against Polaris REST API + direct MinIO + Polaris logs via OpenSearch (`k8s-logs-*`, container `benchmarks-polaris`)
**Companion notebook:** `prove_minio_deletion_no_sts.ipynb`

---

## Bottom line

```
DROP TABLE ... ?purgeRequested=true  → returns 204, removes the catalog record,
but NEVER deletes the data/metadata files from MinIO. Files orphan permanently.

Root cause (proven at mechanism level): the async cleanup task receives storage
credentials with an EMPTY write-location list (no STS to subscope them), so it
cannot delete the files. It fails and retries forever.

This is NOT a MinIO problem, NOT a permission problem, NOT connectivity, NOT RBAC.
Deletion works fine with the static MinIO credentials directly.
```

---

## What was tested and PROVEN (with evidence)

### 1. Purge orphans files (data + metadata)
```
Wrote a real 727-byte Parquet file to a table, then purged.
Result: data files 1→1, metadata files 1→1 (both remain).
Files from purges 10+ minutes old still present → NOT async timing.
```

### 2. Polaris CAN write to MinIO (rules out connectivity)
```
On table create, Polaris wrote 00000-....metadata.json to MinIO BY ITSELF
(we wrote nothing). So Polaris reaches MinIO fine. The problem is delete-path only.
```

### 3. Raw MinIO credentials CAN delete (rules out MinIO / permission)  — Part A
```
Wrote an object with the static MinIO creds, deleted it via MinIO REST API
(SigV4-signed DELETE → HTTP 204), verified gone.
→ storage + credentials are fully capable of deletion.
```

### 4. The cleanup task RUNS and FAILS (Polaris logs)
```
Captured causal chain from OpenSearch (loggerName + message):

  IcebergCatalog          "Scheduled cleanup task <id> for table"
  StorageAccessConfig…    fetch credentials for .../metadata path
  StorageCredentialCache  allowedWriteLocations=[]        ← ROOT SYMPTOM
  TaskExecutorImpl        "Handling task entity id <id>"
  TableCleanupTaskHandler "Handling table metadata cleanup task"
  TaskExecutorImpl  WARN  "Failed to handle task entity id <id>"
  ... retries every ~2s indefinitely

Contrast — normal table writes get FULL scope:
  allowedWriteLocations = [.../table]    ← write granted (works)
Cleanup task gets:
  allowedWriteLocations = []             ← no write scope (fails)
```

### 5. Deletion works WITHOUT STS (the workaround)  — Part B
```
Purged a real table via Polaris → files orphaned (confirmed).
Then deleted those files directly with static MinIO creds (REST API,
single-object DELETE per key) → 0 files. 
→ data CAN be deleted correctly without STS; just not by Polaris's cleanup task.
```

### 6. no-purge vs purge — DIFFERENT mechanisms (Test #2)
```
TableA  drop WITHOUT purge → files 2→2
TableB  drop WITH purge    → files 2→2
Both leave files, BUT the logs show WHY they differ:

  no-purge → NO "Scheduled cleanup task" entry  (never requests deletion)
  purge    → "Scheduled cleanup task" present   (requests it → then fails)

Verified in OpenSearch: every "Scheduled cleanup task" line is a purge
operation (withPurge-*, catalog-purge t0/t1-*). NOT ONE no-purge table appears.

→ no-purge leaves files by DESIGN (passive, correct).
→ purge leaves files because of the BUG (tries, fails, retries).
```

### 7. Catalog purge orphans all files (Test #4)
```
Catalog with 2 tables (each with a Parquet file).
Catalog delete requires empty first (400 "not empty"), so it fans out to
per-table purges. Each table purge orphans its files.
Result: 4 files → 4 files (all orphaned). Same cleanup-task bug at catalog scope.
```

### 8. VIEW drop behavior — two gates (9-case matrix, config VERIFIED per case)

A view holds no data files, only a small `.gz.metadata.json`. A 9-case matrix
(each case on its OWN catalog with config baked in at create AND verified)
established that a view drop passes through TWO INDEPENDENT gates:

```
GATE 1 — CONFIG (drop-with-purge.enabled):
  purge-view-metadata-on-drop=true + drop-with-purge.enabled=FALSE → 403
    error: "Unable to purge entity ... To enable this feature, set the config"
  drop-with-purge.enabled=TRUE → 204 (drop succeeds; metadata file orphaned)

GATE 2 — PRIVILEGE:
  a view drop needs ONE OF:
    VIEW_DROP | CATALOG_MANAGE_METADATA | CATALOG_MANAGE_CONTENT
  with only TABLE_LIST/VIEW_LIST/VIEW_CREATE → 403
    error: "Principal '...' is not authorized"
  (proven by adding ONE privilege at a time; root/service_admin BYPASSES this)

TWO DIFFERENT 403s — distinguished by error text:
  "Unable to purge entity"  → config gate
  "is not authorized"       → privilege gate

In every 204 case the metadata file ORPHANS (same no-STS cleanup behavior).
grant vs no-grant made no difference at the same config; the param
?purgeRequested=true/false/absent made no difference.
```

> **TABLE is NOT the same story (measured 2026-07-06, `table_purge_privilege_test.ipynb`).**
> Root/service_admin **bypasses GATE 2 for views but NOT for a table purge**
> (`DROP TABLE ?purgeRequested=true` is its own op, `DROP_TABLE_WITH_PURGE`).
> `TABLE_DROP` alone is not sufficient there; `CATALOG_MANAGE_CONTENT` is. And
> when both gates are closed at once, the table case returns the PRIVILEGE
> 403 first, not the CONFIG one — worth checking whether that ordering also
> holds for views if this matrix is ever re-run. See
> `privilege/doc-privilege-results.md` and `purge/doc-purge-troubleshooting.md`.

### 9. VIEW / NAMESPACE CREATE 500 (NullPointerException) — read-after-write lag

> **CONFIRMED 2026-06-29: INTERMITTENT infrastructure issue (PG-Pool / PG-HA
> read-after-write), NOT a duplicate/nested namespace.** This finding supersedes
> the earlier "nested namespace" explanation. Full proof in
> `polaris-read-after-write-rootcause.md`.

```
SYMPTOM:  POST .../namespaces OR POST .../views → 500
          {"error":{"message":"metadata","type":"NullPointerException"}}.

NON-DETERMINISTIC — same code + same inputs, different results across runs:
  namespace CREATE observed as  500/500/500/500,  then 200/200/200/500,
  then 200/200/200/200. This is a RACE, not a logic bug.

MECHANISM (traced from DEBUG logs):
  Polaris commits the entity to the PostgreSQL PRIMARY ("Successfully committed
  to view ... in N ms"), then immediately RE-READS it to build the response via
  getPassthroughResolvedPath(). The metastore is behind PG-Pool + PG-HA, so the
  read can hit a LAGGING replica / stale pooled connection that has not yet seen
  the commit → entity invisible → resolvedPath:[] → getRawLeafEntity() NPE → 500.

DECISIVE EVIDENCE:
  • every 500 → resolvedPath:[] — even the parent CATALOG (201 ~5ms earlier) is
    invisible to the response-building read.
  • the 200s → resolver returns null several times mid-request, then a later
    read in the SAME request sees the full path.
  • failures log "Refreshing view latestLocation: null"; successes log the real
    metadata path — same file, visible only on a caught-up read.

RULED OUT:  drop-with-purge.enabled, principal privilege, namespace naming,
  nested/duplicate namespaces — all eliminated by controlled probes.

NOTE:  the 500 is a FALSE failure — the entity IS created. Do NOT depend on a
  verify-read (it suffers the same lag).

SAME ROOT as the grant_records_pkey 23505 duplicate-key error (a stale read on
  the WRITE path causes a redundant insert). One infra fix closes both.

FIX (infra):  route Polaris metastore READS to the PRIMARY (disable PG-Pool read
  load-balancing, or point JDBC at the primary), or use synchronous replication.
MITIGATION (app):  trust the commit — treat create-500 as logical success;
  add a short settle delay before subsequent list/drop reads.
```

---

## Root cause analysis

### Mechanism (proven)
The async cleanup task requests write-scoped storage credentials for the table's
`/metadata` path. Polaris credential vending is built around AWS STS AssumeRole.
**This deployment has no STS** (`stsEndpoint: null` in the catalog config). Without
STS, Polaris cannot mint path-scoped write credentials for the cleanup task, so it
returns an empty write-location set. The cleanup task's FileIO then has no authority
to delete → fails → retries forever → files orphan.

### Suspected upstream bug (needs version confirmation)
Apache Polaris **issue #379**: *"SKIP_CREDENTIAL_SUBSCOPING_INDIRECTION is ignored
in TaskFileIOSupplier."* Polaris has a flag intended for no-STS / single-tenant
deployments that tells it to skip subscoping and use static credentials instead.
Per #379, the async cleanup task ignores this flag and always tries to subscope —
reproduced upstream by "purge from a client that doesn't delete files client-side
(e.g. pyiceberg)," which is exactly our case. **We have not confirmed our Polaris
version contains the unfixed code** — see handoff items below.

### Why everything else works
Table create / write / read / metadata-write fall back to the static MinIO creds
correctly (we observed populated `allowedWriteLocations` for normal writes). Only
the async cleanup/purge task hits the STS-dependent subscoping path. That's why
purge is the *only* operation that fails.

---

## What is NOT yet proven (handoff to system engineer)

These require cluster / deployment access beyond the notebook:

```
1. The literal exception behind "Failed to handle task"
   → we have the WARN + empty write-locations, but not the "Caused by:" trace
   → GET it with:
       kubectl logs -n datahub-hynix <benchmarks-polaris-pod> \
         | grep -A30 "Failed to handle task" | head -60

2. That bug #379 is THE bug in our Polaris version
   → #379's symptom matches exactly, but confirm the running Polaris version
     and whether #379 is fixed in it (check changelog / issue status)

3. Whether SKIP_CREDENTIAL_SUBSCOPING_INDIRECTION is truly ignored here
   → setting it and re-testing requires a server config change
   → if it's honored in our version, it may be a viable fix
```

---

## Recommended verification in the COMPANY environment

```
□ Confirm orphaning on a THROWAWAY catalog (NOT real data):
    create table + write file → purge → wait 15s → list storage prefix
    (use fs.invalidate_cache + fs.find(refresh=True) to avoid stale cache)
    → files remain = confirmed

□ Confirm the log signature in the company OpenSearch:
    container = <polaris>, loggerName: TableCleanupTaskHandler / TaskExecutorImpl
    look for "Scheduled cleanup task" then "Failed to handle task" (repeating)
    and allowedWriteLocations=[] near that requestId

□ Confirm static-cred deletion works (the workaround):
    delete one orphaned object with static MinIO creds (REST/boto3/mc) → gone

□ Check the company catalog config:  stsEndpoint value (likely null)
□ Check the running Polaris VERSION  (vs #379 fix status)
□ CRITICAL — check for EXISTING production orphans from past purges:
    list a few known-purged table prefixes; if files remain, "deleted" data
    still physically exists → compliance implication
```

---

## Fixes (in order of preference)

```
1. Upgrade Polaris to a version where #379 is fixed
   → cleanup task honors skip-subscoping / falls back to static creds
   → verify on the issue/changelog before upgrading

2. Enable STS credential vending in MinIO (if feasible)
   → gives the cleanup task properly-scoped write creds (bigger infra change)

3. Operational workaround (works TODAY, no Polaris change):
   → treat Polaris purge as "removes catalog record only"
   → delete orphaned files directly with static MinIO creds:
       a. after dropping a table, delete its storage prefix, OR
       b. periodically sweep purged locations
   → for Spark: Iceberg remove_orphan_files needs prefix_listing => true
     (Iceberg ≥1.10, apache/iceberg#12254) so vended creds apply
```

---

## Practical gotchas discovered (save your time)

### MinIO deletion methods
```
❌ s3fs fs.rm(prefix, recursive=True)  → MissingContentMD5
                                         (MinIO bulk DeleteObjects needs Content-MD5;
                                          this s3fs/botocore version omits it)
❌ s3fs fs.rm_file(key)                → NotImplementedError (this s3fs version)
✅ MinIO REST API + SigV4 (requests)   → clean single-object DELETE
✅ boto3 client.delete_object(...)     → also works (single delete)
✅ mc rm --recursive                   → MinIO client handles MD5 correctly
```

### s3fs caching
```
s3fs caches directory listings. After deleting OUTSIDE s3fs (REST/boto3/mc),
call fs.invalidate_cache(prefix) and fs.find(prefix, refresh=True), or you'll
see stale "still there" results for files that are actually gone.
```

### OpenSearch query pitfalls
```
1. should + minimum_should_match=1 matches EVERYTHING
   → two different filters returning identical counts = the giveaway
   → use must (AND) to tie a log line to a specific entity

2. match_phrase on hyphenated values FAILS on analyzed fields
   → the `message` field is tokenized; a hyphen splits "withPurge-b37ed6"
     into separate tokens, so match_phrase "withPurge-" never matches
   → "shows in the OpenSearch UI but my API query returns 0" = analyzer mismatch
   → fix: pull broadly (match_phrase on a stable phrase like "Scheduled cleanup
     task") then substring-filter in Python ("withPurge-" in message)
```

### Teardown / "not empty" pitfalls (cost real debugging time)
```
A catalog reports "not empty" (400 on delete) for MORE than namespaces:
  • namespaces with tables/views
  • CHILD namespaces under a parent (nested, joined by 0x1F = %1F in URLs)
  • NON-DEFAULT catalog-roles (anything except catalog_admin)

Symptoms we hit:
  • "remaining namespaces: []" but catalog still "not empty" → it was a leftover
    catalog-role from a privilege test.
  • a namespace shown as parent-ns%1Fvp-ns wouldn't delete → it's a 2-level
    namespace; address it with the 0x1F separator and delete DEEPEST-FIRST.

Complete teardown order (each unblocks the next):
  tables/views → namespaces (deepest-first, multi-pass) → non-default
  catalog-roles → catalog.

Knock-on effect: an incomplete teardown leaves the catalog DIRTY, which then
is a separate teardown hygiene issue. (The view/namespace-CREATE 500 NPE in
finding #9 is NOT caused by this — it is the read-after-write lag.)
```

### Verify-after-write (the recurring lesson)
```
Every confusing result in this investigation traced to an operation that
REPORTED success (or wasn't checked) but didn't take effect:
  • purge returns 204 but doesn't delete the file
  • catalog delete "succeeds" but the catalog stays (not empty)
  • config PUT "succeeds" but used the wrong key (drop-with-purge-enabled vs
    drop-with-purge.enabled) → silently rejected → tests ran on stale config
  • view CREATE "ran" but silently failed → later drop returned a confusing 404
Fix in every case: READ BACK what you wrote. Never trust a write you didn't
verify — especially against optimistic-locking (entityVersion) or lenient
property validation.
```

---

## References

```
apache/polaris#379    SKIP_CREDENTIAL_SUBSCOPING_INDIRECTION ignored in TaskFileIOSupplier
apache/polaris#3742   Polaris vends temp creds despite stsUnavailable=true (S3-compatible)
apache/polaris#3640   Polaris can't connect to internal S3 without STS / credential vending
apache/iceberg#14980  DROP TABLE PURGE is best-effort
apache/iceberg#12254  remove_orphan_files prefix_listing for vended creds
```

---

## One-paragraph summary (for a ticket / Slack)

> Polaris 1.3.0 `purgeRequested=true` removes the catalog record (204) but never
> deletes the table's files from MinIO — they orphan permanently. Proven from logs:
> the async cleanup task gets credentials with empty write-locations (no STS to
> subscope them), fails, and retries forever (`TableCleanupTaskHandler` → "Failed to
> handle task", `allowedWriteLocations=[]`). Confirmed it's not MinIO/permission/
> connectivity: static MinIO creds delete files fine, and Polaris writes metadata to
> MinIO itself. no-purge drops never schedule a cleanup task (passive); purge drops do
> (and fail) — both leave files but for different reasons. Likely matches apache/
> polaris#379. Workaround until a fixed Polaris version or STS: treat purge as
> metadata-only and delete orphaned files directly with static MinIO creds.
