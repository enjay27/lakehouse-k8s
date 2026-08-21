# Grant-record scaling sweep — how the grantee index behaves as a realm grows

Generated 2026-08-21 16:00 against `http://192.168.139.2:8181` realm `POLARIS`. Timings are the **median of 10** `EXPLAIN (ANALYZE, BUFFERS)` runs with the first discarded, statement logging OFF, every statement pinned to the primary with `/*NO LOAD BALANCE*/`.

This supersedes the single-point measurement in `doc-index-measurement-latest.md` **without invalidating it** — that number is one cell of this grid.

## Read this before quoting any number

The larger table sizes are reached with **synthetic filler rows**, inserted directly in SQL because REST cannot reach production volume in a session (10,000 users x 50 grants is ~1,000,000 API calls). Filler rows:

- carry **negative** ids, so they match no entity and are inert for authorization;
- are entirely real to a Seq Scan, which is the only thing being measured here;
- are shaped realistically — roughly 50 rows per synthetic grantee, not one enormous grantee.

Rows derived from them are marked **SYNTHETIC** in every table below. Do not quote one upstream without that caveat.

> The plan specified a sentinel range of `>= 1_000_000_000`. That was wrong and is not what shipped: Polaris ids are snowflake-style and land around 10^18, so **every real grantee id is above that floor** and the cleanup `DELETE` would have removed the entire fixture. The negative range is asserted disjoint against the live table before any insert.

## The grid

| rows in table | probe | rows returned | plan without index | ms | plan with index | ms | speedup |
|---:|---|---:|---|---:|---|---:|---:|
| 125,235 | 1 rows | 1 | `Seq Scan` | 4.910 | `Index Only Scan` | 0.013 | 377.7x |
| 125,235 | 50 rows | 50 | `Seq Scan` | 11.642 | `Index Only Scan` | 0.026 | 447.8x |
| 125,235 | fattest (1111 rows) | 1111 | `Seq Scan` | 7.026 | `Index Only Scan` | 0.131 | 53.6x |
| 125,235 | ~10000 rows (SYNTHETIC) ⚠ | 10000 | `Seq Scan` | 7.783 | `Bitmap Heap Scan` | 1.328 | 5.9x |
| 125,235 | ~500 rows (SYNTHETIC) ⚠ | 500 | `Seq Scan` | 8.071 | `Index Only Scan` | 0.126 | 64.1x |
| 233,237 | 1 rows | 1 | `Gather` | 25.998 | `Index Only Scan` | 0.010 | 2599.8x |
| 233,237 | 50 rows | 50 | `Gather` | 79.352 | `Index Only Scan` | 0.013 | 6348.2x |
| 233,237 | fattest (1111 rows) | 1111 | `Gather` | 28.712 | `Index Only Scan` | 0.116 | 247.5x |
| 233,237 | ~10000 rows (SYNTHETIC) ⚠ | 10000 | `Seq Scan` | 70.542 | `Bitmap Heap Scan` | 0.986 | 71.6x |
| 233,237 | ~500 rows (SYNTHETIC) ⚠ | 500 | `Gather` | 95.645 | `Index Only Scan` | 0.070 | 1376.2x |
| 611,239 | 1 rows | 1 | `Gather` | 240.786 | `Index Only Scan` | 0.035 | 6879.6x |
| 611,239 | 50 rows | 50 | `Gather` | 292.310 | `Index Only Scan` | 0.053 | 5463.7x |
| 611,239 | fattest (1111 rows) | 1111 | `Gather` | 101.059 | `Index Only Scan` | 0.111 | 914.6x |
| 611,239 | ~10000 rows (SYNTHETIC) ⚠ | 10000 | `Gather` | 145.207 | `Bitmap Heap Scan` | 1.470 | 98.7x |
| 611,239 | ~500 rows (SYNTHETIC) ⚠ | 500 | `Gather` | 96.654 | `Index Only Scan` | 0.224 | 432.5x |

⚠ = the probed grantee is synthetic (see above).

## What the trend says

- **Index Only Scan** went from 0.126 ms to 0.224 ms across the same range — it tracks rows returned, not table size.
- Therefore **the speedup grows with realm size and shrinks with grantee fatness**. The previously published figure is a point on that surface, not a property of Polaris.

## Index build cost

| rows in table | build seconds |
|---:|---:|
| 125,235 | 0.8 |
| 233,237 | 1.7 |
| 611,239 | 3.2 |

`CREATE INDEX CONCURRENTLY` slowing at volume is expected and is part of the cost being proposed upstream, so it is recorded rather than omitted.

## Size accounting

| target | exact `count(*)` | `reltuples` | drift | filler rows |
|---:|---:|---:|---:|---:|
| 114,735 | 125,235 | 125,235 | +0 | 64,502 |
| 222,735 | 233,237 | 233,237 | +0 | 172,504 |
| 600,735 | 611,239 | 611,239 | +0 | 550,506 |

Exact counts, never `reltuples` alone — the estimate is stale by construction immediately after a bulk insert, which is exactly when it is read here. Both are recorded so the drift is visible rather than assumed.

