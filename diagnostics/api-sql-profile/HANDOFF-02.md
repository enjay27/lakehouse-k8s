# Phase 1 stage 2 — index remediation, measured. Handoff.

State as of 2026-08-20, run `20260820-152803`. Written so a fresh session can
start at notebook 03 without replaying the history. Companion to
`HANDOFF-phase1.md`, which covers stage 1 (the API→SQL access map).

## Where things stand

**Notebook 02 is complete and its last run is clean.** Execution counts
`In[1]`→`In[22]`, monotonic, zero errors — a real `Restart & Run All`, so DoD #1
is met. Statement logging was OFF (`./capture.sh pgoff`), which matters more than
it sounds; see *Measurement hygiene* below.

Artifacts, paired by `run_id`:

- `runs/20260820-152803.json` — the machine-readable manifest 03 consumes
- `reports/doc-index-measurement-20260820-152803.md` (and `-latest.md`)

**On the cluster right now:** `idx_grant_records_grantee` is **present and
valid**, the 1,000-user fixture is intact (7,273 `entities`, 30,009
`grant_records`, 1,002 auth rows). 02's final cell asserts this rather than
dropping the index, because 03 requires it.

## The finding

`grant_records`' only index is its PK
`(realm_id, securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code)`.
A lookup **by grantee** constrains positions 1, 4, 5 and leaves 2–3 free, so only
`realm_id` is a usable prefix — the whole table in a single-realm deployment. It
runs on the authorization path of **every authenticated request**.

```sql
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_grant_records_grantee
    ON POLARIS_SCHEMA.grant_records (realm_id, grantee_catalog_id, grantee_id)
    INCLUDE (securable_catalog_id, securable_id, privilege_code);
```

Still absent from upstream `schema-v3.sql`, so an upgrade does not supply it.
Cost: ~2000 kB against the PK's 2744 kB (~73%), maintained on every grant insert
and delete. Builds in 0.1 s at this volume.

### What is reproducible, and what is not

**Publish the plan shapes. Treat every speedup ratio as order-of-magnitude.**

Deterministic — identical in all four runs to date:

| | before | after |
|---|---|---|
| S4 grantee lookup | `Seq Scan` | `Index Only Scan` |
| S13 delete arm | `Aggregate > Seq Scan` | `Aggregate > Bitmap Heap Scan > BitmapOr > Bitmap Index Scan` |

`Index Only Scan` (not plain `Index Scan`) means the `INCLUDE` payload covers
every selected column — zero heap fetches. The S13 `BitmapOr` is the
`grant_records_delete_or` hypothesis's own stated acceptance test, now passed.

Also identical every run: Total Cost 810.16, 285 shared hits, 0 disk reads, and
**29,003 of 30,009 rows discarded by filter** to return 1,006. That last number
is the argument, and it needs no clock.

Timings, the two most recent runs (both logging off, medians of 10):

| measurement | run 145705 | run 152803 |
|---|---:|---:|
| S4 median grantee, before | 1.202 ms | 1.452 ms |
| S4 median grantee, after | 0.018 ms | 0.015 ms |
| **speedup, median grantee** | **68.7x** | **93.6x** |
| S4 fattest grantee, before | 1.332 ms | 2.694 ms |
| S4 fattest grantee, after | 0.339 ms | 0.259 ms |
| speedup, fattest grantee | 3.9x | 10.4x |
| S13 delete arm | 13.1x | 5.9x |

Within a run the medians are tight (median grantee ±8%). **Between runs the
baseline moves by up to 2x.** Note where the movement is: the *after* numbers are
stable (0.015–0.018, 0.259–0.339) while the *before* numbers swing. That is not a
coincidence — the Seq Scan reads 285 buffers and discards 29,003 rows, so it is
exposed to whatever else the node is doing; the index scan touches a handful of
pages and is nearly immune. The index scan's own stability is a result in itself.

So: "roughly 100x for a typical principal, single digits for an admin identity
holding a thousand grants" is defensible. "68.7x" is not.

### The speedup is inversely related to grantee size

`hottest_grantee()` picks the grantee owning the **most** rows — the index's
**worst** case, because the index still has to return all of them. Seq Scan cost
does not vary with grantee (it reads the whole table regardless), so the gain is
*largest* for the smallest grantee. The distribution:

> 4,002 grantees — min 1, **p50 1**, p95 25, max 1,006.

**This shape is an artifact of the seed, not a fact about Polaris**: roughly one
principal, one principal-role and two catalog-roles per seeded user. p95 = 25 is
the `owner_principal` catalog role carrying the full explicit privilege set
(decision #9); the 1,006 outlier is an admin/service identity. Report the two
rows as the ends of a range, not as typical vs atypical.

### End-to-end effect, with a control

Reproducible across both runs — medians of 15 calls, first 2 discarded:

| probe | run 145705 | run 152803 |
|---|---:|---:|
| `GET /catalogs/{name}` (full prelude, tiny body) | −1.8 ms | −1.4 ms |
| `GET /principal-roles` | −1.8 ms | −1.3 ms |
| `GET /catalogs` (payload-dominated) | +0.4 ms | −0.6 ms |
| `POST /oauth/tokens` (**control** — resolves no grants) | +0.5 ms | +0.6 ms |

The two authorization-path probes improve by a similar amount in both runs, and
the control moves slightly the *wrong* way in both — which is what rules out
general session warming as the explanation. A ~1.5 ms saving against a ~1.2 ms
plan-level saving per lookup implies one to two grantee lookups per authenticated
request, consistent with the fixed 7-statement prelude.

Honest limit: "after" is measured later in the same session, so Polaris's entity
cache is warmer. The control argues against that being the cause; it is still not
a randomised design.

## Hypotheses

| id | status |
|---|---|
| `grant_records_by_grantee` | **CONFIRMED** |
| `grant_records_delete_or` | **CONFIRMED** (BitmapOr observed) |
| `entities_row_constructor_in` | **INCONCLUSIVE in 02 — REFUTED in 01** |

The last one is a reporting split, not a gap. 02's generic `resolve_params`
refuses the row-constructor IN-list (its placeholder count spans the list rather
than a simple WHERE), so the statement is never EXPLAINed. 01 probes it directly
at list sizes 1/10/50/200/500 and finds an index scan at every size. See
`doc-index-audit-latest.md`. It is also the highest-volume statement in the
capture, so do not let the INCONCLUSIVE read as "unmeasured".

## Read this before writing notebook 03: the cache verdict was never real

`TraceRecord.cache_verdict` returns HIT only when every `entities` SELECT
satisfies `is_version_check`, which matches a projection of just
`entity_version, grant_records_version`. **Polaris 1.3.0 never emits that.**
Measured against the real 75.7 MB capture: every `entities` SELECT — *including*
the row-constructor cache-validation query, the highest-volume statement in the
system at 1,662 calls — projects the same full column list. So `is_version_check`
is always False and `cache_verdict` can only ever return MISS or N/A.

**"`cache: MISS` on all 43 APIs" was never evidence about the cache.** It was the
classifier's only reachable answer. The belief that the validation query is a
narrow projection came from source reading and was never asserted against real
output.

The fix is in `src/api_trace.py` as `entity_access_shape()` — discriminate on the
**WHERE** clause, which does carry signal:

| WHERE shape | calls | meaning |
|---|---:|---|
| `(catalog_id, id) IN (<rows>)` | 1,662 | batched validation |
| `realm_id, id, type_code, catalog_id` | 1,621 | per-entity load by id |
| `realm_id, name, catalog_id, parent_id, type_code` | 1,024 | per-entity load by name |
| `realm_id, catalog_id, id` | 654 | per-entity load by id |

**And then do not make the same mistake again.** A first shape-based classifier
scored a request MISS if it contained *any* per-entity load, and measured 100%
MISS across all 703 requests — which looked like confirmation and was the same
error in a new place. Any API resolving a path (catalog → namespace → table)
*must* look the first entity up by name, because a name is all the caller
supplied. A warm request is not one with zero per-entity loads.

Measure a **share**, not a boolean. `entity_access_profile()` returns per-shape
counts plus `batched_share` and a graded WARM/MIXED/COLD/N-A verdict. On the
reference capture: **628 of 703 requests (89.3%) contain at least one batched
validation**, median batched share 0.33, modal shape 2 batched to 4 per-entity.
The cache is plainly working. Neither binary classifier could see it.

03's prediction is therefore that `batched_share` **rises with iteration index**,
not that a verdict flips.

## The manifest contract (how 03 gets its inputs)

`src/run_manifest.py`, 13 mocked tests in `test_run_manifest.py`.

- 02 writes `runs/<run_id>.json`; `run_id` is a sortable timestamp, shared with
  the report, so `runs/<id>.json` and `reports/doc-index-measurement-<id>.md` are
  always the same measurement.
- 03 calls `load_run(OUT)` for the newest, or `load_run(OUT, RUN_ID)` for a named
  one. It returns `(resolved_id, payload)` — print the id, because "newest" can
  change under you between sessions.
- **The manifest carries values; the live cluster carries truth.** A manifest
  saying "index present" is a statement about the past. 03 must call
  `require_live_match(conn, manifest)`, which hard-fails listing every mismatch.
- `index_state()` returns `present` / `valid` / `ready`. Presence alone is not
  enough: an interrupted `CREATE`/`DROP INDEX CONCURRENTLY` leaves a `pg_index`
  row with `indisvalid = false` that passes a naive check but the planner never
  uses — 03 would measure unindexed behaviour while believing otherwise.
- `table_counts()` uses exact `count(*)`, not `pg_stat`'s `n_live_tup`, which
  drifts after bulk changes until the next ANALYZE.

## Measurement hygiene (learned the hard way)

1. **Turn statement logging off before any timing.** With `log_statement='all'`
   and `log_min_duration_statement=0`, the same Seq Scan plan measured
   1.6–7.5 ms across runs — a 4.6x spread that moved the headline 11.6x → 6.3x on
   noise alone. `./capture.sh pgoff`. The capture is already on disk; notebook 02
   cell 20 reads it from there and needs no live logging.
2. **Warm-up is enormous.** The first EXPLAIN in a fresh kernel measured
   **25.2 ms** against a 1.3 ms steady state — 19x. `EXPLAIN_N = 11` with the
   first discarded; `timeit(k=15, warmup=2)` for wall-clock, because Polaris's
   entity cache and pgjdbc's `prepareThreshold=5` are two separate knees inside
   the first few iterations.
3. **The capture directory must be resolved by content, not by name.** 02 once
   picked a 0-byte `capture/polaris.log` over the 28 MB `capture-seeded/` one and
   silently reported every hypothesis INCONCLUSIVE. Resolution order is
   `$CAPTURE_DIR`, then the newest `capture*` holding a **non-empty**
   `polaris.log`.
4. **Restart the kernel after any `src/` edit.** A mid-notebook
   `importlib.reload` does not rebind names earlier cells already resolved; the
   run ends up half-old and half-new, silently. The reload that used to be in
   cell 19 has been removed for this reason.
5. **EXPLAIN must run on the PRIMARY.** Every statement carries
   `/*NO LOAD BALANCE*/`; cell 3 asserts `pg_is_in_recovery() = False`. A replica
   can hold different statistics and would silently plan differently.

## Re-running 02

Section 5 **refuses to run when the index already exists**, because the index now
persists and a second run would otherwise measure a "before" state that already
has it — reporting ~1x, which reads as a refutation of the finding rather than a
stale cluster. To re-run: uncomment the `DROP INDEX CONCURRENTLY` in the final
cell, run it, restart, and set `index.left_in_place = False` in the manifest cell
if you intend to leave the index off.

## Open items

- `verify_counts` prints "Row counts match the spec" while expected is 6,000
  entities / 25,000 grants against an actual 7,273 / 30,009. It is evidently a
  `>=` check with misleading note text. Explain the surplus before any of these
  numbers go upstream.
- Four statements remain `NO_PARAMS`, all writes: an `entities` UPDATE and three
  DELETE/INSERT variants, where the placeholder count spans SET/VALUES rather
  than the WHERE. Predicates are PK-shaped and a sibling `entities` DELETE does
  show INDEX_SCAN, so they are very likely fine — but they are unmeasured and
  should not be described as verified.
- `_find_capture_dir` is duplicated in 01 and 02. Promote it into
  `src/api_trace.py` and repoint both.
- `black . && isort .` still needs running on `src/api_trace.py` and
  `src/run_manifest.py`.
- `runs/.gitignore` contained a bare `*`, which would have left every manifest
  untracked. Changed to keep `*.json` — provenance is the point of the manifest.
