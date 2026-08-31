# PLAN — API query-performance check (Pass A, index ABSENT)

Written 2026-08-24, after reading `CLAUDE.md`, `MEMORY.md`, `scan_privileges.py`,
`HANDOFF-privilege-scan.md`, `PLAN-50-grants-and-privilege-scan.md`, and the run
this plan is built on. **Nothing has been modified** — `CLAUDE.md`'s Strict
Plan-First rule applies. Scope confirmed with Kade: analyse the no-index capture
first and stop there. Deliverable: a runner script beside `scan_privileges.py`
plus a Markdown report.

---

## 0. What the completed drive actually established

`runs/privscan-20260824-123408.json`, driven with
`--drive --capture capture-scan-noindex-2 --deny-sample 100000`.

| | |
|---|---|
| identities | 1,000 authenticated, 1,000 loaded — no auth failures, no skips |
| requests | 15,000 = 1,000 token calls + 14,000 GETs |
| op labels | 14 = 7 authorized + 6 refused + `GET /namespaces [ns-resolve]` |
| authorized outcome | 8 labels × 1,000 = **8,000 × 200** |
| refused outcome | 6 labels × 1,000 = **6,000 × 403** |
| errors / auth_failures / skipped | all empty — a clean pass |
| elapsed | 138.3 s |

**`--deny-sample 100000` drove the refusals for every identity, not a sample.**
That is more evidence than the flag was designed to collect and it is the most
interesting thing in the run — see §1.

### The capture is live and complete — verified, not assumed

`capture-scan-noindex-2/` on disk:

```
polaris.log   119,453,003 bytes   138,014 lines
  first line  2026-08-24T03:31:47.981Z  seq  99,846  getToken
  last  line  2026-08-24T03:34:08.284Z  seq 237,859  user1000 GET .../ns1/views 200
pg-0.log       57,755,721 bytes   343,048 lines   (primary? — detect, §4.0)
pg-1.log        4,136,177 bytes
pg-2.log       83,848,123 bytes
```

The Polaris window is 2 m 20 s and brackets the drive's 138.3 s exactly. Counts
inside it:

```
DatasourceOperations lines   109,010     = 7.27 statements per request
grant_records mentions        89,008     = 5.93 grant_records statements per request
```

Two things follow, and both are worth stating plainly because both have until
now been read off the source rather than measured:

- The "**7-statement authorization prelude**" the handoff and `scan_privileges`'
  docstring assert is now **7.27 measured**, across 15,000 real requests.
- The grantee lookup is not one statement per request. **~5.9 of the ~7.3
  statements touch `grant_records`.** If that holds under correlation, the Seq
  Scan the whole audit is about fires roughly **six times per authenticated API
  call**, not once — which multiplies the finding by six and is a materially
  different operational story from the one currently written down.

Neither number goes in the report until §3 has attributed them per request. A
`grep -c` is a hint, not a correlation.

### One thing that is NOT yet verified

That the index was absent during this drive. The directory is *named*
`capture-scan-noindex-2`, and MEMORY's own rule is **resolve by content, never
by name**. §4.0 checks `pg_indexes` before anything is read into the capture.

---

## 1. The question this task answers

> For each API on the authenticated GET surface, which SQL does Polaris issue,
> how many times, and which access path does each statement take at the measured
> `grant_records` volume with `idx_grant_records_grantee` absent?

Plus one this run can settle and no previous run could:

> **Does a 403 pay the same authorization prelude as a 200?**

`scan_privileges.py`'s docstring asserts it does — "a refused request still pays
the full 7-statement authorization prelude, so the grantee lookup fires on the
denial path too" — and flags that asserting it from source is "the precise
mistake `cache_verdict` was". This capture holds 8,000 permitted and 6,000
refused requests under one clock, one fixture, one index state. Splitting
statements-per-request by outcome answers it from evidence, in one table.

If it holds, the finding is that **authorization cost is paid before the
authorization decision** — every rejected request scans the whole table too, so
a caller hammering endpoints it has no rights to costs the same as one doing
real work. That belongs in the report whichever way it comes out.

---

## 2. What exists, and the three gaps

### 2.1 Reusable as-is (no changes proposed to any of it)

- `api_trace.parse_polaris_log(text)` → `SqlStatement` with **`request_id`
  carried from `mdc.requestId`**. This is the whole correlation key, already
  parsed, already tested.
- `api_trace.parse_pg_log(text)` → statements with server-side `duration_ms`.
- `api_trace.normalize_sql` — unifies `?` / `$N`, whitespace, and IN-list
  cardinality, so one statement groups across both streams.
- `extract_table` / `extract_verb` / `where_clause` / `entity_access_shape` /
  `is_version_check` — the classification vocabulary notebook 01 reports in.
- `redact_params` has **already run** on every parsed statement; `grant_records`
  is not in `SECRET_TABLES`, so its bound parameters survive and its statements
  are replayable verbatim under EXPLAIN. `principal_authentication_data` is a
  secret table and its params are gone — §3.4.
- `explain_n(conn, sql, params, k)` with `NO_LOAD_BALANCE`, `pg_stat_*` helpers.
- `privilege_scan.py`, `scan_privileges.py`, `capture.sh` — untouched; this task
  reads what they produced.

### 2.2 GAP 1 — `Tracer` cannot be used here, and must not be reached for

`api_trace.Tracer` marks a stream, makes **one** call, reads the delta. It is a
live per-call instrument. This capture is 264 MB written by 15,000 requests that
have already happened. The correlation has to be **post-hoc, keyed on
`mdc.requestId`**, and stream in bounded memory.

That is not a limitation of the capture — it is better evidence. `requestId` is
a first-class MDC field on every line, so attribution is exact rather than
inferred from a time window.

### 2.3 GAP 2 — nothing maps a request to its op label

`parse_polaris_log` accepts only `DatasourceOperations` query lines. The line
that names the API is a different logger:

```json
"loggerName":"io.quarkus.http.access-log",
"message":"192.168.194.1 - user1000_principal [24/Aug/2026:03:34:08 +0000]
           \"GET /api/catalog/v1/user1000_catalog/namespaces/ns1/views HTTP/1.1\" 200 41",
"mdc":{"requestId":"...24083"}
```

It carries requestId, principal, method, concrete path, **and status**. So a new
access-log parser gives `requestId → (principal, method, path, status)`, and
joining it to the statements gives per-request, per-API, per-outcome attribution
with nothing assumed.

The concrete path must then be templated back to the **same 14 labels the run
JSON uses** (`user1000_catalog` → `{name}`, `ns1` → `{ns}`). If the report's
denominator does not match the drive's, the two documents disagree about what
was measured. The templating is driven off `api_sweep.read_operations` — the
single definition of the surface — never a second hand-written list.

### 2.4 GAP 3 — the PG logs run 101 minutes past the drive

Polaris's tail stops at 03:34:08. `pg-*.log` keep growing to **05:15**, because
`PGDUR=1 pgon` statement logging is still enabled on the cluster. So:

- every PG-side read must be **windowed to 03:31:47 → 03:34:08 UTC**, or
  durations from unrelated later traffic contaminate the merge;
- `./capture.sh pgoff` should be run when the correlation is done, or the next
  thing anyone does on that cluster is timed under 4.6× inflation.

---

## 3. The build

New files only. **No existing module changes**, so the 233 green tests, the
notebooks and `scan_privileges.py` are untouched by this task.

### 3.1 `src/query_profile.py` (new module)

| function | does |
|---|---|
| `iter_log_chunks(path, bytes=8<<20)` | stream a large log file line-aligned, bounded memory |
| `parse_access_log(text)` → `[AccessRecord]` | GAP 2: requestId, principal, method, path, status, bytes |
| `template_path(method, path, ops)` | concrete path → op label, driven off `api_sweep.read_operations` |
| `correlate(polaris_log, ops)` → `[RequestProfile]` | join statements to access records on `request_id`; carries op label, status, ordered statements |
| `window(records, start, end)` | GAP 3: clip a stream to the drive's clock |
| `statement_profile(profiles)` | per op label × normalized statement: count, per-request mean, table, verb, access shape |
| `prelude_by_outcome(profiles)` | §1's second question: statements/request split 200 vs 403, and which statements differ |
| `distinct_statements(profiles)` | the EXPLAIN worklist — one representative with real params per normalized shape |
| `render_*` | the report tables |

Tests in `test_query_profile.py`, mirroring `test_api_sweep.py`: mocked log text,
no live cluster, no large fixture. Cases: access-log line parses; a statement
with no matching access record is reported, not dropped; templating round-trips
every one of the 14 labels; window excludes out-of-range lines; a 403 profile
and a 200 profile separate correctly.

### 3.2 `diagnostics/api-sql-profile/profile_queries.py` (new runner)

Same shape as `scan_privileges.py` — argparse, env-var secrets, refuses rather
than guesses.

```bash
python3 profile_queries.py --capture capture-scan-noindex-2 --run privscan-20260824-123408
                                      # correlate, no DB needed, no EXPLAIN
python3 profile_queries.py --capture ... --run ... --explain
                                      # + EXPLAIN (ANALYZE, BUFFERS) on the PRIMARY
python3 profile_queries.py --capture ... --run ... --explain --report
                                      # + write reports/doc-privilege-query-performance-<run_id>.md
```

Refusals it makes, each one a scar in `MEMORY.md`:

- **no `--capture` → exit.** Resolve by content anyway: refuse a capture whose
  `polaris.log` holds no `DatasourceOperations` line, whatever it is called.
- **request count mismatch → exit.** The run JSON says 15,000 requests. If the
  capture's access-log yields materially fewer, the tail missed part of the
  drive and the distribution is a subset presented as a whole. This is the
  `assert_capture_live` lesson applied to the reading end.
- **`--explain` asserts `pg_is_in_recovery() = false`** and pins
  `/*NO LOAD BALANCE*/`. The primary is `postgresql-1` today and it moves —
  detect it.
- **`--explain` records the live `pg_indexes` state for `grant_records`** into
  the output JSON, so the report can never mislabel which pass it describes.

Writes `runs/qprofile-<run_id>.json` — the machine-readable half, so the report
is reproducible and a second (index-present) pass diffs against it directly.

### 3.3 EXPLAIN policy

For each distinct normalized statement, one representative replayed with its
**logged** parameters, `explain_n(k=11, first discarded)`, on the primary.
Recorded: plan shape, node type, index name if any, **shared buffers hit/read**,
**rows removed by filter**, plan rows vs actual rows.

Per `bench_grantee_lookup.py`'s reasoning, `max_parallel_workers_per_gather = 0`
is pinned **session-scoped** for the comparison, and whether the unindexed plan
*would* go parallel is recorded separately rather than being allowed to
contaminate it. At this volume it should not escalate — the crossover run put
parallel escalation at ~80–160 K rows — but that is a prediction, and the plan
output settles it.

**Pass A's clock is discarded.** Buffers and rows-filtered are the headline;
`duration_ms` from the PG log appears as a footnote column, labelled as inflated.

### 3.4 The one statement that cannot be replayed verbatim

`principal_authentication_data` is in `SECRET_TABLES`, so `redact_params`
replaced its whole parameter set. Its EXPLAIN needs parameters rebuilt from the
metastore (`privilege_scan.load_identities` already reads that table). It is a
PK lookup and not under suspicion — but the report must say the parameters were
reconstructed rather than observed, not quietly substitute them.

---

## 4. Run order (Kade runs these — this sandbox is blocked from `192.168.139.2`)

```
0.  VERIFY THE PASS'S PREMISE — before reading anything into the capture
    SELECT indexname FROM pg_indexes
     WHERE schemaname='polaris_schema' AND tablename='grant_records';
      -> idx_grant_records_grantee must be ABSENT, or this is not a no-index pass
    SELECT pg_is_in_recovery();            -- on each pg-N, to name the primary
    SELECT count(*) FROM polaris_schema.grant_records WHERE realm_id=...;
      -> the volume the report quotes. MEASURED. Not 55K, not 30,002, not 500K —
         whatever it is. PLAN §2 flagged a 55,002/55,009 discrepancy and the
         fixture may still be at 25 grants/role; --verify settles it.

1.  python3 profile_queries.py --capture capture-scan-noindex-2 \
                               --run privscan-20260824-123408
      -> correlation only. Read the statements-per-request table and the
         200-vs-403 split BEFORE spending EXPLAIN on it.

2.  ... --explain            -> plan shape + buffers per distinct statement
3.  ... --explain --report   -> the Markdown

4.  ./capture.sh pgoff       -- statement logging has been on since 03:31 and is
                                still on. Anything timed on that cluster until
                                it is off is inflated 4.6x.
```

Step 1 costs no database access at all — it is a pure read of files already on
disk. If the correlation disagrees with §0's `grep` arithmetic, that is the
finding and steps 2–3 wait.

---

## 5. Report shape — `reports/doc-privilege-query-performance-<run_id>.md`

1. **What was measured** — 1,000 real API-seeded principals, 15,000 requests,
   8,000 permitted / 6,000 refused, the measured `grant_records` count, index
   absent (asserted from `pg_indexes`, §4.0). All-real provenance, nothing
   synthetic to disclose.
2. **The grantee lookup at this volume** — plan shape, buffers, rows removed by
   filter, and **how many times per request it fires**. The headline.
3. **Prelude on the denial path** — §1's second question, as a table.
4. **Per-API index usage** — 14 op labels × distinct statements × access path.
   The point of scanning the whole surface is confirming `entities` is covered;
   anything that is not is a second finding.
5. **Statement inventory** — every distinct statement, count, table, verb, shape.
6. **Latency footnote** — PG-log durations, labelled inflated, explicitly not
   quotable. Real latency is Pass B and is out of this task's scope.
7. **What this pass does not establish** — the index-present contrast. Named as
   the next task, not implied to be covered.

---

## 6. Guards carried forward

- Capture resolved by **content**; refuse one whose logs are empty of statements.
- PG streams **windowed to the drive's clock**; 101 minutes of unrelated traffic
  sit past the end of every `pg-*.log`.
- EXPLAIN on the **detected** primary, `/*NO LOAD BALANCE*/`,
  `pg_is_in_recovery()=false` asserted.
- **Volume stated as measured**, never carried over from a doc. §0 shows three
  different figures already in circulation.
- Restart the kernel after any `src/` edit (a stale import cost two
  ConnectionErrors last session) — matters if any of this is exercised from a
  notebook.
- **Do not touch `grant_scale.resolve_probes`'s clone bug here**, but it is still
  live and still wrong; nothing on this path uses it.
- `black . && isort .` with **black last** (no `[tool.isort] profile`, Active
  Issues), then `pytest`. `test_iceberg_rest.py` is already black-dirty in the
  repo and will be reformatted — pre-existing.

---

## 7. Definition of done

- `src/query_profile.py` + `test_query_profile.py` green, mocked, no live cluster.
- `profile_queries.py` correlates 15,000 requests from `capture-scan-noindex-2`
  and reconciles its request count against `privscan-20260824-123408.json`.
- Per-API index-usage table across all 14 labels; grantee-lookup plan shape,
  buffers and rows-filtered at the measured volume; statements-per-request split
  by 200 vs 403.
- `runs/qprofile-<run_id>.json` written, recording the live `pg_indexes` state.
- Markdown report, volume measured not quoted, timings labelled inflated.
- `black`/`isort`/`pytest` green — black last.
- `MEMORY.md` updated per `CLAUDE.md`'s DoD item 3.

---

## 8. Decisions needed before I touch anything

1. **Sign off §3's build** — new `src/query_profile.py` + new runner, no existing
   module modified. Or redirect: fold it into `api_trace.py` instead (it is the
   natural home, but it is 60 KB and carries the tested parsers this depends on).
2. **§0's unverified premise** — can you confirm the index was absent for this
   drive, and give me `--verify`'s current grants-per-role? Three volume figures
   are in circulation (30,002 / 55,002 / 55,009) and the report needs one
   measured number.
3. **§1's 5.93 grant_records-per-request hint** — if correlation confirms it,
   that reframes the headline from "a Seq Scan per request" to "six per
   request". Do you want that pursued as the report's lead, or kept as a
   sub-finding until the index-present pass corroborates it?
4. **`capture.sh pgoff`** — statement logging is still on and has been since
   03:31. Turn it off now, or leave it for the index-present pass that follows?
