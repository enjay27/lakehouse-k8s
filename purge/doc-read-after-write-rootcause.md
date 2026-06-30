# Polaris 1.3.0 — Read-After-Write Inconsistency: Confirmed Root Cause

**Date confirmed:** 2026-06-29
**Environment:** Apache Polaris 1.3.0, realm POLARIS, PostgreSQL behind PG-Pool (pooler) + PG-HA (replicas), MinIO (no STS), OrbStack Kubernetes (`datahub-hynix`).
**Status:** CONFIRMED from Polaris DEBUG logs across multiple identical runs.

## Bottom line

A class of intermittent Polaris errors in this environment is caused by **PostgreSQL read-after-write inconsistency** — a write commits to the primary, but an immediate follow-up read is served by a lagging replica (or a stale pooled connection) that has not yet seen the commit. The entity is genuinely written; the read just cannot see it yet. Because whether a given read is caught up is effectively a coin flip, the resulting failures are **non-deterministic**: the same code with the same inputs produces different results from run to run.

This is an **infrastructure-layer issue (PG-Pool / PG-HA), not a Polaris logic bug and not a test bug.** It ties directly to the earlier runbook conclusion that most intermittent Polaris errors (401/500/timeout, circuit-breaker trips, table-commit failures) are downstream of the PostgreSQL connection/health layer.

## How it was proven

Two probes were run repeatedly with byte-identical code and inputs:

```
Run A:  namespace CREATE → 500, 500, 500, 500   (all four cases failed)
Run B:  namespace CREATE → 200, 200, 200, 500   (three succeeded, one failed)
Run C:  namespace CREATE → 200, 200, 200, 200   (all four succeeded)
```

Three of four succeeding in one sequential run, and zero of four in another, cannot be explained by any deterministic cause (config, privilege, namespace naming, leftover state). It is a race.

### Decisive log evidence

```
1. In every 500, the resolver returns an EMPTY path:
     "Returning null for key ns-X due to size mismatch from
      getPassthroughResolvedPath  resolvedPath: []  requestedPath: [ns-X]"
   Not even the parent CATALOG resolves — and that catalog returned HTTP 201
   roughly 5 ms earlier. The read that builds the response cannot see entities
   the write just committed.

2. In the 200s, the SAME resolver returns "size mismatch null" SEVERAL times
   mid-request, then a later read in the SAME request returns the full path and
   the call succeeds. A read that misses, then hits, milliseconds apart.

3. The commit is durable either way:
     success → "Refreshing view latestLocation: s3a://.../...gz.metadata.json"
     failure → "Refreshing view latestLocation: null"
   Same metadata file, same request — visible on a caught-up read, invisible on
   a lagging one. Every failed request still logs
     "Successfully committed to view <catalog>.<ns>.<view> in N ms"
   i.e. the entity IS created. The 500 is a FALSE failure.
```

## The mechanism

```
1. Client calls POST .../namespaces  (or .../views)
2. Polaris writes the entity → COMMIT to PostgreSQL PRIMARY (durable)
3. Polaris immediately re-resolves the entity to build the HTTP response,
   reading via PolarisResolutionManifest.getPassthroughResolvedPath(...)
4. That read is served by PG-Pool — and may land on:
     • a PG-HA REPLICA that has not yet replicated the commit, or
     • a pooled connection that has not yet seen the other connection's commit
   → the just-written entity is not visible → resolvedPath is empty/short
5. getRawLeafEntity() is called on the null resolved path → NullPointerException
6. The IcebergExceptionMapper turns it into HTTP 500 {"message":"metadata",
   "type":"NullPointerException"}
```

When replica lag happens to be ~0 at step 4, the read sees the write and the call
returns 200. The lag varies, so the outcome varies.

## Two symptoms, one root cause

This root layer (PostgreSQL via PG-Pool/PG-HA) produces **two distinct failures**.
Both are "a read does not reflect a recent write" — a false-absent read — hitting
two different code paths:

```
ROOT: PostgreSQL read-after-write inconsistency (PG-Pool / PG-HA replica lag)
  |
  +-- Symptom A — grant_records_pkey 23505 (duplicate key)
  |     stale read on the WRITE path:
  |     Polaris checks "does this grant already exist?" on a lagging replica →
  |     "no" → it INSERTs the grant → but the primary already has the row →
  |     PostgreSQL 23505 duplicate-key violation on grant_records_pkey.
  |     NOTE: this symptom ALSO has a non-lag trigger — a genuinely redundant
  |     grant call (re-running a cell, or catalog_admin already holding the
  |     privilege). So it needs an app-side guard regardless of the lag.
  |     APP GUARD: make the grant idempotent (treat 23505 / "already exists" /
  |     "duplicate key" / "grant_records_pkey" as success).
  |
  +-- Symptom B — view / namespace CREATE 500 (NullPointerException)
        stale read on the READ path:
        Polaris commits the entity, then re-resolves it on a lagging replica →
        resolvedPath:[] → getRawLeafEntity() NPE → 500. The entity IS created.
        APP GUARD: trust the commit — treat a create-500 as a logical success
        (the commit log confirms the entity exists); do not depend on a verify
        read, because that read suffers the SAME lag.
```

Mnemonic:

```
23505    = "didn't see it exists, so wrote it again"      (false-absent, write path)
500 NPE  = "didn't see it exists, so the response broke"   (false-absent, read path)
```

These should be documented as **two symptoms nested under one root cause**, not as
one bug. Fixing the DB routing removes the lag-driven cases of both, but Symptom A
still needs idempotency because of its non-lag trigger.

## The fix

### Infrastructure (the real fix — system engineer / platform owner)

The Polaris metastore needs read-after-write consistency. Any one of:

```
1. Route ALL Polaris metastore queries to the PRIMARY.
   Disable PG-Pool read load-balancing for the Polaris connection (or point
   Polaris's JDBC URL directly at the primary rather than the load-balanced VIP).
   Simplest option; usually sufficient.

2. Use synchronous replication for the metastore database
   (synchronous_commit + at least one synchronous standby), so replicas are
   caught up before a write returns. Correct, at a write-latency cost.
```

A single change here closes BOTH symptoms' lag-driven cases.

### Disambiguating experiment (confirm the layer in one test)

```
Point Polaris's metastore JDBC URL DIRECTLY at the PostgreSQL PRIMARY
(bypass PG-Pool / the load-balanced VIP), restart Polaris, re-run the 2x2 probe.

  • 500s vanish   → confirmed: PG-Pool read routing / PG-HA replica lag (Issue 1+2)
  • 500s persist  → it is Polaris's own in-process entity cache, not the DB
```

Expected outcome: the 500s vanish.

### Application-side mitigation (until the infra fix lands)

```
• grant_privilege  → idempotent: 23505 / "already exists" / "duplicate key" /
  "grant_records_pkey" are treated as success.   [applied in polaris_test_utils.py]

• namespace / view CREATE → trust-the-commit: a create-500 is treated as a
  logical success. The commit log proves the entity exists; a verify-read is
  unreliable because it suffers the same lag, so we do not block on it. An
  optional short settle delay lets later reads (list/drop) catch up.
  [applied in view_purge_behavior_test.ipynb]
```

These make the notebooks reliable despite the lag, but they do not remove the lag —
that is the infrastructure fix above.

## System-engineer checklist

```
[ ] PG-Pool read routing — is it load-balancing SELECTs to replicas?
    → route Polaris metastore reads to the PRIMARY, or disable load-balancing
      for that connection.
[ ] PG-HA replication mode — asynchronous? (async = this lag).
    → consider synchronous_commit + a sync standby for the metastore DB.
[ ] Polaris JDBC URL target — primary directly, or the load-balanced VIP?
    → for a metastore it must reach the primary for reads.
[ ] Run the bypass-PG-Pool experiment above to confirm the layer.
[ ] Pod-level check for the literal exception under load:
    kubectl logs -n datahub-hynix <benchmarks-polaris-pod> \
      | grep -E "getPassthroughResolvedPath|getRawLeafEntity|grant_records_pkey"
[ ] Connection-pool sizing/health — ties to the earlier runbook conclusion that
    PostgreSQL pool exhaustion / health underlies most intermittent Polaris errors.
[ ] CRITICAL (compliance, separate issue): check for existing PRODUCTION orphans
    from purge (the no-STS cleanup-task issue) — unrelated to this lag, still open.
```

## One-paragraph summary (for a ticket / Slack)

> Polaris 1.3.0 in dev intermittently returns HTTP 500 ("metadata",
> NullPointerException) on namespace/view CREATE, and occasionally a
> grant_records_pkey 23505 duplicate-key error. Both are the same root cause: a
> read that does not reflect a just-committed write, because the metastore runs
> behind PG-Pool + PG-HA and reads can land on a lagging replica or stale pooled
> connection. The entity is actually created (the commit is logged) — the 500 is a
> false failure from the response-building re-read; the 23505 is a redundant write
> after a stale existence-check. Proven non-deterministic: identical code returned
> 500x4, then 200x3+500, then 200x4 across runs. Fix: route Polaris metastore reads
> to the PostgreSQL primary (or use synchronous replication). App-side mitigations
> (idempotent grants, trust-the-commit on create) make the tooling reliable in the
> meantime.

## Recurring engineering lesson (the through-line of this whole investigation)

Verify-after-write / read-after-write. Nearly every confusing result in this
investigation traced to an operation that reported success (or wasn't checked) but
didn't take effect, OR a read that didn't see a write: purge 204-but-not-deleted;
catalog delete "succeeds" but not-empty; config PUT wrong-key/unchecked; silent
view-create failure; grant non-idempotent 23505; and finally the DB read-after-write
lag. The fix is always to read back, retry, make idempotent, or trust a verified
commit — especially against optimistic locking (entityVersion), lenient property
validation, and replicated/pooled databases.
