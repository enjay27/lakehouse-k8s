# Plan — per-API latency across grant and entity volume

Phase 1 stage 4. Answers "what does each API actually cost, and where does an
index change that" with wall-clock, not plans.

Status: **awaiting sign-off.** Nothing built.

Flow, as Kade framed it: seed at 100 / 1,000 / 10,000 → call every API → EXPLAIN
every statement those calls issued → read index requirements off the result.

---

## 1. A correction to something I said earlier

I have repeatedly called SQL-inserted filler rows "inert". That is true of
**authorization semantics** — they match no entity, so nothing resolves them.
It is **false for latency**, and the difference is the whole basis of this plan.

Every authenticated request pays a 7-statement authorization prelude, and one of
those statements is the grantee lookup. Without the index that is a Seq Scan,
and a Seq Scan reads **every row in the table, filler included**. So SQL-seeded
volume lands directly on real API latency.

That is why this scenario works at all, and it is worth stating plainly before
anyone reads "inert" in an older comment and concludes the opposite.

## 2. Entities by DML — capture the write path, then replay it

Two ways to get entities into the database without 610,000 API calls. The second
is Kade's and it is the better one.

### 2a. Clone an existing row (fallback, and required for one table)

`entities` has seventeen columns including two JSONB blobs, and a catalog's
`internal_properties` carries the storage config. Constructing one by hand means
getting all of that right. Cloning does not: the unique constraint is
`(realm_id, catalog_id, parent_id, type_code, name)`, so an `INSERT ... SELECT`
from a real row changing only **`id` and `name`** yields a row Polaris itself
authored.

This is **mandatory** for `principal_authentication_data`, whose columns are
`(realm_id, principal_id, principal_client_id, main_secret_hash,
secondary_secret_hash, secret_salt)`. Clone it with a new id and client_id but
the same hash and salt, and the clone authenticates with the secret of the
principal it was cloned from — no hash scheme to reverse-engineer. It is also
the only option there because a capture cannot supply it: `api_trace` redacts
every parameter of any statement touching that table, by design
(`SECRET_TABLES`), and that redaction stays.

### 2b. Capture the real write statements, then replay them — PREFERRED

Cloning still guesses at *which tables* a create touches. Recording the write
path does not. Issue ONE of each create over REST with PostgreSQL statement
logging on, and read back exactly what Polaris wrote:

    LOG:  execute <unnamed>: INSERT INTO entities (...) VALUES ($1, $2, ...)
    DETAIL:  parameters: $1 = 'POLARIS', $2 = '0', ...

`api_trace.parse_pg_log` already parses that shape, pid-aware, with the
redaction above. **Built: `capture_write_templates.py`** — it brackets each REST
call with a marker statement on its own connection, so the server log delimits
each API's block without needing Polaris's requestId, then reports every
statement with its bound values and writes `write-templates-<stamp>.json`.

Note what this closes: four write statements have sat at **NO_PARAMS** through
every audit so far, because `resolve_params` refuses statements whose
placeholder count spans SET/VALUES. Their values have never been recovered. The
server log has them.

**Run the capture before designing the replay.** Every table that appears is one
the replay must populate; any it misses leaves a realm that looks right and
behaves oddly, and that is precisely the class of bug this repo keeps finding by
rendering evidence rather than reasoning about it.

### Gates, both already checked

- **No sequence table.** `schema-v3.sql` declares six tables — `version`,
  `entities`, `grant_records`, `principal_authentication_data`,
  `policy_mapping_record`, `events` — and no `CREATE SEQUENCE`. Ids are
  generated in the application, so a bulk insert cannot desynchronise a database
  allocator. Still take ids from a range asserted disjoint from live data.
- **No foreign key on `grant_records`** (measured 2026-08-21).

### What replay still does not give you

- **Cloned or replayed catalogs share a `default-base-location`** unless it is
  rewritten per row. Harmless read-only, a collision the moment anything writes.
- **No MinIO objects.** Any API that vends credentials or touches storage fails.
- **`events`** is written by the `persistence-in-memory-buffer` listener. If the
  capture shows writes there, decide deliberately whether the replay reproduces
  them or the audit trail is knowingly incomplete.
- These remain synthetic rows, disclosed as such in every table.

### The safety property that makes this acceptable

`InMemoryEntityCache` holds an entity together with its grant_records, so
writing behind Polaris's back normally risks cache and database disagreeing for
up to an hour. **Kade's restart removes that**: a restarted Polaris starts empty
and reads what is in the table. Replay while it is down, or restart afterwards.

## 3. The cold/warm protocol

Kade's design: restart Polaris, take the first call as uncached, take later
calls as cached. It is simpler than notebook 03's per-iteration fixtures and it
is sound, with three things to hold onto.

**Cold-after-restart is not the same as a cache miss.** The first call also pays
JVM class loading, connection-pool establishment and pgjdbc's
`prepareThreshold=5` promotion. This repo has measured a first-call penalty of
**25.2 ms against a 1.3 ms steady state — 19x** — and almost none of that is the
entity cache. Mitigation: after each restart, issue warm-up calls against a
*different* catalog first, so the JVM and the pool are warm and only the entity
cache is cold for the entity actually being measured. Label the number "first
touch after restart" either way.

**One cold sample per restart.** Cold is not repeatable without another restart,
so a median of 5 costs 5 restarts. On OrbStack that is minutes, which is
acceptable — but it is the reason 03 was designed around fresh fixtures instead.

**Do not expect "super faster".** Measured on the 178 MB capture: **734 of 844
requests (87%) contain a batched revalidation, and ZERO were served purely from
cache** — because resolving a path must load its first entity by name. A warm
request issues *fewer* statements, not none. Predict a modest drop and a rise in
`batched_share`; a 2x improvement is the correct result, not a disappointing one.
If something reports 50x, suspect the measurement.

## 4. The grid

Two independent axes, and they affect different APIs:

| axis | mechanism | what it moves |
|---|---|---|
| `grant_records` rows | SQL filler (`sql_fill.py`) | **every authenticated call**, via the Seq Scan in the auth prelude |
| `entities` rows | cloned rows | LIST endpoints (payload size) and path resolution (index scans, ~log n) |

Cells: 3 grant volumes (100 / 1,000 / 10,000-user shapes) × index absent/present
× cold/warm. Entity volume held constant in the first build; see §7.

Per cell: every API on both surfaces, `timeit(k=15, warmup=2)`, with
`POST /oauth/tokens` as the **control that must not move** — it resolves no
grants, and the control moving the wrong way is what made 02's table credible.

Cost: ~43 APIs × 17 calls ≈ 730 calls per cell. Minutes, not hours.

## 5. State this before running it

At 30,009 rows, 02 measured the index's end-to-end effect at **−1.3 to −1.8 ms**
with the control moving **+0.5** — real, but marginal against noise. At ~611,000
rows a serial Seq Scan over ~45 MB of buffers is **tens of milliseconds per
request**. So this sweep should turn a marginal signal into an unmissable one.

If it does not — if per-API latency barely moves at 611k rows without the index —
then either the auth prelude is not running the statement we think it is, or the
cache is absorbing it, and that is a finding worth more than the sweep.

**Pin `max_parallel_workers_per_gather = 0`.** The first 02b run escalated to a
parallel Seq Scan at ~233k rows and the timings became unusable: probes with
identical plan cost and identical buffer counts measured a 3–10x spread. Record
the escalation separately — an unindexed grantee lookup that goes parallel is
consuming worker slots on every authenticated request, which is a worse story
than latency and belongs upstream on its own.

## 6. Risks and restore

| risk | handling |
|---|---|
| Cloned rows outlive the run | All clones carry a marker (a name prefix, and ids from a reserved range asserted disjoint against live data, as `grant_scale` already does). Removal is one predicate, verified by count. |
| A clone is served but broken | Read-only APIs only; a smoke pass calls each endpoint against one clone before the sweep and fails loudly rather than producing a slow number that is really an error path. |
| Cache/DB disagreement | Restart Polaris after cloning. Do not clone into a running instance whose cache already holds the source rows. |
| Timings quoted as exact | Report medians with min/max and the control, never a single figure — and keep the plan-shape and buffer evidence beside them, which is what survived when 02b's clock did not. |
| Cloned catalogs collide on storage | Read-only. If writes are ever added, rewrite `default-base-location` and `location_without_scheme` per clone first. |

## 7. Open

- **Entity volume in scope, or a second pass?** Grant volume alone is minutes and
  isolates the variable the index addresses. Adding cloned entities at 10,000
  answers the LIST-endpoint and path-resolution half. Recommendation: build the
  grant axis first, add the entity axis once the harness is proven.
- **Notebook name.** `02c_api_latency_sweep.ipynb` keeps the 02-family together
  and leaves `03` free; `04` would match execution order if this runs after 03.
- **Where the cold/warm restart is driven from.** A notebook cannot restart
  Polaris mid-run, so either the notebook pauses for a manual restart per round,
  or a shell driver restarts and re-invokes a headless measurement script.
  The second is more reproducible and is what a 5-restart median needs.
