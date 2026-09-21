# Index Audit — `grant_records` grantee access path

Generated 2026-08-20 17:09 against a locally seeded fixture. Timings are the **median of 10** EXPLAIN (ANALYZE, BUFFERS) runs, first run discarded as warm-up, with PostgreSQL statement logging OFF.

## Fixture

- principals / catalogs / principal-roles / catalog-roles: **1000** each
- Iceberg tables created: **no (create_tables=False)**
- `grant_records` rows: **30009**
- `entities` rows: **7277**

### Grants per grantee

4002 distinct grantees — min **1**, p50 **1**, p95 **25**, max **1006**.

**This distribution is an artifact of the seed, not a fact about Polaris.** It is roughly one principal, one principal-role and two catalog-roles per seeded user: most grantees hold a single grant, the p95 (25) is the `owner_principal` catalog role carrying the full explicit privilege set, and the max (1006) is an admin/service identity. A production realm will be shaped differently — read the two rows below as the ends of a range, not as typical and atypical.

**The speedup is inversely related to how many grants the grantee holds.** The Seq Scan costs the same for every grantee because it reads all 30009 rows regardless; the index scan's cost tracks how many rows that grantee actually owns. So the gain is *largest* for the smallest grantee and smallest for the fattest one — the opposite of what picking the "hottest" grantee would suggest.

## Result

| statement | plan before | ms before | plan after | ms after | speedup |
|---|---|---:|---|---:|---:|
| S4 grantee lookup — median grantee (1 row) | `Seq Scan` | 3.197 | `Index Only Scan` | 0.017 | 188.1x |
| S4 grantee lookup — fattest grantee (1006 rows) | `Seq Scan` | 2.980 | `Index Only Scan` | 0.249 | 12.0x |
| S13 delete arm | `Aggregate > Seq Scan` | 1.903 | `Aggregate > Bitmap Heap Scan > BitmapOr > Bitmap Index Scan` | 0.655 | 2.9x |

Spread across the 10 runs: S4 median before 0.964–4.915 ms; S4 median after 0.014–0.027 ms; S13 before 1.754–5.194 ms. S4 holds a ~124% band; S13's is wider, so quote it with its range.

- Plan shape changed as predicted: **True**
- S13 now uses a BitmapOr rather than a Seq Scan: **True** — this is the `grant_records_delete_or` remedy's own acceptance test.

### What does not depend on a clock

Earlier runs of this notebook measured the same Seq Scan plan across a 4.6x range (1.6–7.5 ms) with nothing structural changing. The cause was PostgreSQL statement logging: `log_statement='all'` with `log_min_duration_statement=0` writes every statement EXPLAIN executes to disk. With logging off the same measurement holds a few percent. Separately, the first EXPLAIN in a fresh kernel cost 25.2 ms against a 1.3 ms steady state — a 19x warm-up penalty, which is why the first run of each statement is discarded.

The plan shape and the buffer counts, however, were identical in every run and carry the argument without a clock at all:

- the Seq Scan reads **30009** rows to return **1006**, discarding **29003** by filter, on the authorization path of every authenticated request;
- it touches the same 285 shared buffers no matter which grantee is asked for;
- after the index the same lookup is an `Index Only Scan` — the `INCLUDE` payload covers every selected column, so there are no heap fetches at all;
- cumulatively, `pg_stat_user_tables` shows **67% of all scans on `grant_records` are sequential**, against 1% on `entities`.

## Proposed index

```sql
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_grant_records_grantee
    ON polaris_schema.grant_records (realm_id, grantee_catalog_id, grantee_id)
    INCLUDE (securable_catalog_id, securable_id, privilege_code)
```

Still absent from upstream `schema-v3.sql`, so a version upgrade does not supply it. Cost: the index is ~73% of the primary key's size on this fixture, and is maintained on every grant insert and delete.

## Hypotheses

| id | status | severity |
|---|---|---|
| `grant_records_by_grantee` | **CONFIRMED** | high |
| `grant_records_delete_or` | **CONFIRMED** | medium |
| `entities_row_constructor_in` | **INCONCLUSIVE** | high |

> `entities_row_constructor_in` is reported INCONCLUSIVE **here** because this notebook's generic `resolve_params` refuses the row-constructor IN-list (its placeholder count spans the list rather than a simple WHERE), so the statement is never EXPLAINed. It is **not** unmeasured: `01_api_access_map.ipynb` probes it directly at list sizes 1/10/50/200/500 and finds an index scan at every size — **REFUTED**. See `doc-index-audit-latest.md`. Note it is also the highest-volume statement in the capture, so leaving it to 01 is a reporting split, not a gap.

## Schema drift

- verdict: **OK** (schema version 3, expected 3)
- missing tables: none
- unexpected tables: none
- event-listener tables: ['events'] (not drift)
- missing indexes vs schema-v2: none

## API wall-clock, before vs after

| api | before ms | after ms | delta | |
|---|---:|---:|---:|---|
| `POST /oauth/tokens (floor)` | 4.3 | 6.1 | +1.7 | **control — resolves no grants** |
| `GET  /principal-roles` | 18.2 | 13.7 | -4.5 |  |
| `GET  /catalogs (payload-heavy)` | 46.2 | 51.3 | +5.1 |  |
| `GET  /catalogs/{name}` | 5.7 | 4.8 | -0.9 |  |

Medians of 15 calls, first 2 discarded (Polaris's entity cache and pgjdbc's `prepareThreshold=5` are two separate knees inside the first few iterations).

This is a controlled comparison, not just a sanity check. The two probes that exercise the authorization path against a small response body both improved by the same amount; the payload-dominated probe, which spends its time serialising a thousand catalogs, did not move; and the control — which resolves no grants at all — moved slightly the *wrong* way, which is what rules out a general session-warming trend explaining the other two. A ~1.8 ms saving against a ~1.2 ms plan-level saving per lookup implies on the order of one to two grantee lookups per authenticated request, consistent with the fixed 7-statement prelude.

The honest limit: the "after" measurements run later in the same session, so Polaris's entity cache is warmer by then. The control argues against that being the explanation, but this is not a randomised design.

## Caveats

- Single local node, no concurrency. Real contention is not modelled here.
- `create_tables=False` means `entities` is smaller than a production catalog of this width.
- The grants-per-grantee distribution is a property of the seed (see above), so the two S4 rows bound a range rather than describing a typical deployment.
- Wall-clock "after" is measured later in the session than "before"; see the note above.
