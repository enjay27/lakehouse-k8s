# HANDOFF — privilege-query index audit at 1,000 real principals

Written 2026-08-24. Standalone: everything needed to run the next task is here.

## The pivot

**SQL-based voluming is abandoned.** Volume now comes from real, API-seeded
principals. The SQL machinery built this week — `entity_replay` identity clones,
`bench_grantee_lookup.py`, `sql_fill` filler, 02c's clone-based sweep — is
**retained but off-path**; it is sound and tested, and the credential-clone
finding it rests on is confirmed, but the next task does not use it. Do not
delete it; it is the reference for how the write path behaves.

**Why the pivot is fine.** The whole audit's headline — the grantee lookup is a
Seq Scan that reads the entire `grant_records` table to return one principal's
~50 grants — is a property of the *query shape and volume*, not of how the rows
got there. Real API-seeded rows measure it exactly as well as filler, and they
carry no "synthetic, disclose it" asterisk. The only thing SQL bought was speed
of voluming, and Kade is choosing correctness of provenance over that.

## What the volume actually is — state it plainly

1,000 principals × 50 privileges = **50,000 granted grant_records + ~5,009
overhead ≈ 55,009 rows.** Not 500,000. Reaching 500K by API needs ~10,000
principals (~8.5 h of REST). So the fixture is **~55K**, and every number in the
report must say 55K, never 500K.

55K is still firmly in Seq-Scan territory — the crossover run measured Seq Scan
from ~5,000 rows up, and parallel escalation from ~80–160K. So at 55K the
grantee lookup is a **serial Seq Scan**: the index effect is real and clean, and
it does **not** escalate to parallel (that starts higher). That is arguably a
better volume to publish than 500K, because the number is uncontaminated by the
parallel-timing noise that wrecked 02b.

## Phase 1 — PREREQUISITE (Kade's job, not this task)

Seed 1,000 principals over the API, each:
- **client_id** in the `userN_client` format (distinct per principal — the PK on
  `principal_authentication_data` is `(realm_id, principal_client_id)`, so they
  cannot be literally identical);
- **the same secret** (Kade updates `principal_authentication_data` so every
  `main_secret_hash` + `secret_salt` matches). Then one secret authenticates all
  1,000: log in as `userN` with `(userN_client, shared_secret)`.

Tooling that exists: `seed_polaris.py --users 1000 --no-tables` then
`--upgrade-grants --grants-per-role 50` gives 1,000 owner_principal roles at 50
grants each. The equal-secret step is Kade's manual update.

**No Polaris restart needed after this.** Seeding goes through the API, so
Polaris's cache is written the normal way. The restart discipline (`reset_realm
.sh`) is only for writes made behind Polaris's back — the schema apply and SQL
clones, neither of which this task uses.

## Phase 2 — MEASURE (this task)

Notebook 01's method, at 1,000-user scale, with the analysis narrowed to
**index usage on the privilege query**.

### The measurement, two passes — this is not optional

The measurement hygiene note in MEMORY is the reason: **you cannot have index
evidence and clean latency in one pass.**

- **Pass A — logging ON (`capture.sh`).** Polaris `DatasourceOperations` DEBUG
  SQL + per-replica PostgreSQL statement logs. Drive every user's
  authentication and all GET APIs. This pass answers *which SQL each API issues*
  and *which index each statement uses* — correlate on `mdc.requestId` with
  `api_trace`, then `EXPLAIN (ANALYZE, BUFFERS)` each distinct statement on the
  **primary** (`/*NO LOAD BALANCE*/`, `pg_is_in_recovery()=False` asserted).
  Logging inflates timings 4.6x, so this pass's clock is discarded.
- **Pass B — logging OFF (`capture.sh pgoff`).** Re-run the same calls for
  wall-clock latency: `timeit(k=15, warmup=2)`, first EXPLAIN discarded
  (`EXPLAIN_N=11`). This pass's SQL shapes are NOT trusted (logging is off);
  Pass A owns those.

### What "all users, all GET APIs" means, and the cost

01 traces *one* of each API. This task drives *every* principal through the GET
surface, because the point is to see the grantee lookup fire 1,000 times with
1,000 different grantee ids against the same 55K table — the real distribution,
not one probe.

- ~1,000 principals × ~9 authenticated GET ops ≈ **9,000 requests per pass**,
  two passes. Minutes, not hours — these are reads.
- The auth prelude (7 statements) runs on every one, so Pass A's capture is
  large. **Rotate the capture** (`./capture.sh rotate <dir>`) — the 178 MB
  seeded capture was lost once to an in-place restart (MEMORY, Active Issues).

### The index question, precisely

For each distinct statement the GET surface issues, Pass A's EXPLAIN answers:
Seq Scan or Index Scan, and if Index, which one. The **grantee lookup** is the
one under the microscope: at 55K it is a Seq Scan without
`idx_grant_records_grantee` and an Index (Only) Scan with it. Run Pass A **index
absent** and **index present** to get the contrast — the durable evidence is
plan shape + buffers + rows-filtered (identical across runs), not the clock.

Everything else on the surface is expected to already be an index scan
(`entities` is well covered via `idx_entities`/`constraint_name`); the value of
scanning all of them is *confirming that*, and catching anything that is not.

## Phase 3 — REPORT (Markdown)

A standalone analysis document. Lead with the grantee-lookup finding at 55K
(plan shape, buffers, rows-filtered), then the per-API index-usage table across
the whole GET surface, then latency (Pass B, with the control `POST
/oauth/tokens` that resolves no grants and must not move). State the volume as
55K everywhere, disclose nothing as synthetic (it is all real), and keep timings
as illustration beside the buffer evidence that survives between runs.

## Guards carried from this session's scars

- **Restart Polaris only for behind-the-back writes.** API seeding needs none.
- **Capture dir by content, not name** — newest `capture*` with a non-empty log.
- **EXPLAIN on the primary**, pinned; the primary is currently `postgresql-1`,
  and it moves — detect it, don't hardcode.
- **`resolve_probes` still can't tell a clone from a real grantee** (Active
  Issues). Irrelevant here — no clones — but fix it before any SQL-path tool
  runs again.
- **Buffers and rows-filtered are the headline; the millisecond ratio is the
  footnote.** Same plan, 4.6x clock spread, measured.

## Definition of done

- Pass A capture (index absent + present) correlated, every GET statement's
  index usage rendered, grantee-lookup Seq→Index contrast shown at 55K.
- Pass B latency with the moving control, logging off.
- Markdown report, volume stated as ~55K throughout, all-real provenance.
- `black`/`isort`/`pytest` green on any new `src`/harness code (run black last —
  isort profile still unset, Active Issues).
