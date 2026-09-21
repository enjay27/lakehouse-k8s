# The grant-record index, measured — 29 GET operations, three identity tiers, 60,784 rows

2026-08-31. Six captures, two cluster states, one question: what does
`idx_grant_records_grantee` actually buy on Apache Polaris 1.3.0-incubating.

**The answer, in one line: every authorised read on the surface pays one
grantee lookup, and without the index that lookup reads the whole
`grant_records` table — 572 pages and 60,783 discarded rows to return one.
With the index it reads 3 pages and discards none.**

---

## 1. What was measured

Three fixtures, all seeded through the API, no synthetic rows:

| tier | principals | privileges | entities | grant footprint | ops driven |
|---|---:|---:|---|---:|---:|
| `user` | 1000 | 50 | 2 namespaces | **52** | 7 permitted + 6 refused |
| `authz` | 100 | 50 | 2 ns, 5 tables, 2 views, 1 policy, 1 generic table | **52** | 21 |
| `admin` | 5 | 50 + `service_admin` | 2 ns, 5 tables, 2 views | not measured | 26 |

`user` and `authz` have **identical, uniform footprints** (n=100,
min=p50=p95=max=52), so they sit at the same point on the scan-vs-index curve
and their figures are directly comparable. `admin` is not footprint-comparable
and its profile says so: `service_admin` gains one grant per catalog, so its
grant set grows with the realm rather than with its own privileges.

Each tier was driven twice — once with the index absent, once with it present —
at one volume:

| tier | index | capture | run | requests | elapsed |
|---|---|---|---|---:|---:|
| user | absent | `capture-user-noindex-2` | `privscan-20260831-110305` | 15,000 | 148.9 s |
| user | present | `capture-user-index` | `privscan-20260831-111114` | 15,000 | 87.0 s |
| authz | absent | `capture-authz-noindex` | `privscan-20260831-105310` | 2,700 | 27.7 s |
| authz | present | `capture-authz-index` | `privscan-20260831-111200` | 2,700 | 19.7 s |
| admin | absent | `capture-admin-noindex` | `privscan-20260831-105456` | 160 | 2.6 s |
| admin | present | `capture-admin-index` | `privscan-20260831-111255` | 160 | 1.7 s |

Every run: 0 non-2xx beyond the 6,000 deliberate refusals, 0 auth failures, 0
skipped. All six captures reconcile against their run manifest with **0
unexplained requests** (§7).

**Volume.** `grant_records` held 60,782 rows when the drives ran and **60,784**
when the statements were replayed under EXPLAIN; two rows arrived in between.
Every plan figure below is at the measured 60,784. The difference is 0.003% and
changes nothing — a sequential scan reads all 572 pages either way.

**Method.** Polaris logs every statement with its `mdc.requestId`; the access
log carries the same id. Correlation joins them post-hoc, so nothing here is
instrumentation added to the request path. Each distinct statement shape is
then replayed against the primary under `EXPLAIN (ANALYZE, BUFFERS)` with
`/*NO LOAD BALANCE*/`, `pg_is_in_recovery() = false` asserted, and
`max_parallel_workers_per_gather = 0` pinned for the session.

EXPLAIN replays against the database **as it is**, not as it was, so
`--index-state` is required with `--explain` and is checked against live
`pg_indexes`. Each of the six records the index list it actually ran under; all
six agree with the capture they describe.

---

## 2. The headline — the grantee lookup

One statement, issued on every authorised read:

```sql
SELECT securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code
  FROM polaris_schema.grant_records
 WHERE grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?
```

`idx_grant_records_grantee` is `(realm_id, grantee_catalog_id, grantee_id)` —
an exact cover for that predicate.

| tier | index | plan | index used | shared buffers | rows removed by filter | rows returned |
|---|---|---|---|---:|---:|---:|
| user | absent | **Seq Scan** | — | **572** | **60,783** | 1 |
| user | present | Index Scan | `idx_grant_records_grantee` | **3** | 0 | 1 |
| authz | absent | **Seq Scan** | — | **572** | **60,783** | 1 |
| authz | present | Index Scan | `idx_grant_records_grantee` | **3** | 0 | 1 |
| admin | absent | **Seq Scan** | — | **572** | **60,782** | 2 |
| admin | present | Index Scan | `idx_grant_records_grantee` | **4** | 0 | 2 |

**190× fewer pages touched for the same answer**, consistent across three
independently seeded fixtures. `shared_read` is 0 in every case: the table is
572 pages ≈ 4.5 MiB and fully resident, so this is CPU and buffer-pin cost, not
I/O. The gap will widen, not close, once the table stops fitting in cache.

**The control is in the same table.** Polaris also looks grants up by
*securable*:

```sql
... WHERE securable_id = ? AND securable_catalog_id = ? AND realm_id = ?
```

whose leading columns `grant_records_pkey` already covers. It takes an Index
Only Scan at **3–5 buffers in both cluster states**, unchanged by the toggle.
Same table, same rows, same pass — so the contrast above is attributable to the
grantee predicate and not to anything ambient.

### What the sequential scan costs in aggregate

The `user` index-absent pass issued **18,001** grantee lookups. At 572 buffers
each that is **10.3 million buffer hits — about 79 GiB of page traffic — to
answer 15,000 requests**. The same pass with the index issued 15,001 lookups at
3 buffers: **45,003 hits, about 350 MiB**.

### Timings, and why they are not the finding

EXPLAIN-time execution of the single statement, median of the replays:

| tier | absent | present |
|---|---:|---:|
| user | 3.056 ms | 0.027 ms |
| authz | 4.335 ms | 0.015 ms |
| admin | 2.042 ms | 0.024 ms |

These are single-statement replays taken now, on an otherwise idle primary.
They are not request latency and must not be quoted as such. **The drive
elapsed times in §1 are not latency either** — every pass ran with statement
logging on, a measured 4.6× inflation in this repo, and the two halves did not
issue the same number of statements (§6). Buffers and rows-filtered are stable
across reruns; milliseconds are not. Pass B, with logging off, has not been run.

---

## 3. The denial path pays in full

The `user` tier drove 6,000 requests it had no privilege for. Measured, both
index states, identical:

| outcome | requests | statements | per request | min / median / max | grantee lookups per request |
|---|---:|---:|---:|---|---:|
| refused (403) | 6,000 | 42,000 | **7.000** | 7 / 7 / 7 | **1.000** |
| permitted (2xx) | 8,001 | 64,007 | 8.000 | 7 / 8 / 10 | 1.125 |
| auth (token) | 1,001 | 3,003 | 3.000 | 3 / 3 / 3 | 0.000 |

*(permitted and auth rows from the index-present pass; the refused row is
identical in both.)*

A refusal costs **exactly seven statements, every time — no spread at all** —
including exactly one grantee lookup. **The authorization cost is paid before
the authorization decision**, so a caller hammering endpoints it has no rights
to costs what real work costs.

With the index absent, those 6,000 refusals alone scan the whole table 6,000
times: **3.4 million buffer hits, ~26 GiB of page traffic, to say no**. With the
index, 18,000 hits.

This was previously asserted from reading the source. It is now measured, on
both cluster states.

---

## 4. Per-API index usage across all 29 operations

The suite reaches 29 of 29 GET/HEAD operations across the three tiers. Joining
each operation to the statement shapes it issued, and each shape to its plan:

**Index absent — 29 of 29 read operations issue a grantee lookup that
sequentially scans `grant_records`.** The only endpoint that does not is
`POST /oauth/tokens`, which authenticates before any grant is consulted. There
is no cheap corner of the read surface: `HEAD /namespaces/{ns}` pays the same
572 pages as `GET /catalog-roles/{r}/grants`.

**Index present — there is not a single sequential scan anywhere on the
surface.** Every shape across all 29 operations:

| table | plan | index | buffers | what it answers |
|---|---|---|---:|---|
| `entities` | Index Scan | `idx_entities` | 3 | entity by id |
| `entities` | Index Scan | `idx_entities` | 3 | entities by `(catalog_id, id)` list |
| `entities` | Index Scan | `constraint_name` | 3 | child by name |
| `entities` | Index Scan | `constraint_name` | 3 | children by sub-type |
| `entities` | Index Scan | `constraint_name` | 780 | list children of a parent (1,105 rows) |
| `entities` | Bitmap Heap Scan | `constraint_name` | 7 | as above, admin tier only (2 rows) |
| `grant_records` | Index Scan | `idx_grant_records_grantee` | 3–4 | **grants held by this grantee** |
| `grant_records` | Index Only Scan | `grant_records_pkey` | 5 | grants on this securable |
| `policy_mapping_record` | Index Scan | `policy_mapping_record_pkey` | 2 | policies attached to a target |

The 780-buffer `entities` listing is the largest remaining read, and it is
already on an index — it is large because it returns 1,105 rows, not because it
is scanning. The one Bitmap Heap Scan is a planner choice on an indexed path in
the `admin` tier, present in both cluster states, and unrelated to this toggle.

**One statement on the surface is deliberately unmeasured.** The credential
lookup on `principal_authentication_data` (`WHERE principal_client_id = ? AND
realm_id = ?`, 1,001 occurrences, one per token call) has its parameters
redacted at capture time because the table is on the secrets list, so it cannot
be replayed. Its plan is unknown. That is a safety rule working as designed, not
an oversight — but it does mean the authentication path's only statement is the
one thing here with no plan attached. Checking it needs a synthetic
`principal_client_id`, not a captured one.

---

## 5. Two faults this pass found in its own tooling

Both were found by looking at composition rather than totals, and both had
produced clean-looking output for the whole preceding session.

**The classifier only knew 13 of the 29 operations.** `operation_templates`
defaulted to `api_sweep.read_operations`, deliberately frozen at the 13 ops the
original unauthorised scan drove. Captures from the authorised tiers therefore
left their other 16 operations unclassified, and an unclassified request keeps
its raw path as its label — so `GET  /policies` appeared as 200 separate
one-request "operations" named after individual catalogs, while its own
template row showed zero.

Reconciliation did not catch it **because the two errors net out**: on the
admin capture, 75 requests missing from 13 template rows and 77 appearing on 61
raw-path rows summed to +2, which is exactly what the liveness probe costs. The
summary line looked normal on all six captures. Only the per-row composition
showed it. The default is now the full 29-op surface; all six captures
re-classify with **0 unclassified paths**.

This also mis-assigned 1,600 authz and 75 admin requests to the
`unclassified (not an op)` outcome class — the bucket whose entire purpose is
to keep non-API traffic out of the permitted mean. §3's figures are from the
corrected classification.

**The liveness probe's +2 was reported as an unexplained delta.**
`assert_capture_live` authenticates once and reads one catalog before each
drive, and neither request is in the run manifest. Every capture therefore
reconciled at +2 and printed a banner saying it "is not what the drive issued".
That is false, and a banner that cries wolf on every run trains the reader to
skip the one check that catches a genuinely short capture. The allowance is now
named per label, capped at the probe's own cost, and never applied to a
negative delta — a +3 still reports +1 unexplained, and a short capture keeps
its full deficit.

---

## 6. What this does NOT establish

- **Latency.** Nothing here is a latency measurement. Every pass ran with
  statement logging on (4.6× inflation, measured in this repo) and the drive
  clocks are discarded. Pass B has not been run.

- **Statement counts are not comparable across the two halves.** The
  index-absent passes issued *more statements*, not just slower ones: 122,010
  vs 109,010 on the `user` tier, concentrated in `GET  /namespaces` (13.5 vs
  8.0 statements per request) and `GET  /namespaces/{ns}`. An index changes how
  a statement executes, never how many are issued, so this is something else —
  most likely Polaris entity-cache warmth, since the absent passes ran first.
  It is not explained here. It also means part of the elapsed-time drop in §1
  is fewer statements, not faster ones, which is a second reason not to read
  those numbers as an index result.

- **`admin`'s grant footprint.** Assumed ~1,100 from `service_admin`'s
  one-grant-per-catalog property. Never measured. Run `--footprint --profile
  service-admin` before quoting it.

- **Write paths.** Read-only by construction. Four write statement shapes
  remain unparameterised and unmeasured.

- **The authentication statement's plan.** §4.

- **Behaviour above 60,784 rows.** The table is fully cached at this volume.
  The 190× buffer ratio is a page-access ratio, not a latency ratio, and the
  relationship between the two will change once `grant_records` exceeds shared
  buffers.

---

## 7. Reconciliation

Every capture against its own run manifest, after both fixes in §5:

| tier | index | requests expected | observed | probe | unexplained |
|---|---|---:|---:|---:|---:|
| user | absent | 15,000 | 15,002 | +2 | **0** |
| user | present | 15,000 | 15,002 | +2 | **0** |
| authz | absent | 2,700 | 2,702 | +2 | **0** |
| authz | present | 2,700 | 2,702 | +2 | **0** |
| admin | absent | 160 | 162 | +2 | **0** |
| admin | present | 160 | 162 | +2 | **0** |

0 orphan statements and 0 unclassified paths in all six.

---

## 8. Reproducing this

```bash
cd diagnostics/api-sql-profile

# labels, reconciliation, outcome classes, per-op statement mix — no database
python3 relabel_capture.py --capture capture-user-index --run 20260831-111114

# plans — replays against the CURRENT cluster, so the state must be declared
python3 profile_queries.py --capture capture-user-index --run privscan-20260831-111114 \
    --index-state present --explain --report
```

The six `runs/qprofile-*.json` hold the plans and the live `pg_indexes` state
each was taken in; the six `runs/relabel-*.json` hold the labels, reconciliation
and per-operation statement mix. The plans cannot be recomputed — half of them
were taken in a cluster state that no longer exists — which is why relabelling
writes a separate file rather than overwriting them.

Recreating the index-absent state:

```sql
DROP INDEX polaris_schema.idx_grant_records_grantee;
ANALYZE polaris_schema.grant_records;
-- and to restore:
CREATE INDEX CONCURRENTLY idx_grant_records_grantee
    ON polaris_schema.grant_records (realm_id, grantee_catalog_id, grantee_id);
ANALYZE polaris_schema.grant_records;
```

`ANALYZE` after each toggle is not optional: a planner working from stale
`reltuples` chooses a path for a table size that no longer exists.
