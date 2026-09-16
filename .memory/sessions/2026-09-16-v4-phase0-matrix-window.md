# 2026-09-16 — Phase 0 of the audit-log TODO: v4 verified on the matrix window

Source: `logging/scripts/step10-v4-window-readout.sh 2026-09-15T09:20:00Z` (run `1789463971`,
`seq=5@benchmarks-fluent-bit-rvm49`), JSON under `.scratch/readout-2026-09-15T092000Z/` (not committed).
Tick emit 09:20:31.770Z → phase **1.770s**; record interval [09:20:01.770, 09:20:31.770).

## Result: every Phase-0 check passes, most of them exactly

| check | pipeline | reference | verdict |
|---|---|---|---|
| **replay** — tier-1 copy (696 raw docs) through the repo Lua vs the rows the pipeline wrote | 64 rows | 64 rows | **0 mismatches over 30 fields** (`step11-replay-window.py`) |
| access_seen | 349 | tier-1 access lines 349 | exact |
| access_kept (= seen − counted 51) | 298 | polaris-logs access docs 298 | exact |
| invariant resource == principal == seen − parse_errors | 349 / 349 | 349 | exact |
| errors_4xx + errors_5xx / auth_denied / 5xx | 251 / 104 / 4 | detail ≥400: 251, 401+403: 104, 5xx: 4 | exact |
| **G1** loggers in polaris-logs | access 298, ExceptionMapper 174 INFO + 4 ERROR, ServiceImpl 32 | allowed set only | PASS |
| **G2** app_dropped vs tier-1 non-allowed lines | 54/33/26/20/4 = 137 | same per logger | **exact** |
| allowed app logs | ExceptionMapper 178, ServiceImpl 32 | tier-1 178, 32 | exact (nothing allowed was dropped) |
| **G3** requestId join | 210 / 210 | — | PASS |
| **G4** clientSecret | `*` (1), no `secret_redacted` | — | PASS |
| **G5** schema / mapping | 64 rows schema 4, no `carried_rows`; commit_*, dropped, app_dropped_total **long** | — | PASS |
| **G6** commit lines | sum(commit_count) 9 | tier-1 `Successfully committed` 9 | exact |
| **G7** commit-only rows | none this window | — | vacuous (creates were in seq 4, checked 09-15) |
| **G8** zero rows without commits | 0 | — | PASS |
| **Gate 2** `last_write_bytes`, table `probe_tbl` | 1941 (writes 23) | tier-1 2xx non-empty writes 1181, 1549, 1549, **1941** (last) | **PASS** — last-wins, not first; 2xx and >0 guards hold. `tables/rename` 12 == 12 |

v3's Gate 2 had never passed once ("until this gate passes once, v3 is unproven") — it now has, on v4.

## Findings that are not faults

- **`polaris-report-*` `min_record_time` maps as `date` in some indices and `text` in others** — the old
  2026-09-10 index (#25). Template (TODO 1.1) prevents recurrence; the text index stays text for its life.
- `logger_name` dynamic-maps as `text` (+ `.keyword`), as intended for strings.
- `role_keys_forced` 4 — denied grants creating role rows, well under the cap of 100.
- `resources_other` 0 at 54 resources — the 500 cap is nowhere near on test traffic (prod question, TODO 3.2).
