# API SQL Profile

## Concept

Map every Polaris **Management API** and **Iceberg REST Catalog API** operation to the exact SQL it
issues against the PostgreSQL metastore, the tables that SQL touches, and the MinIO objects it
accesses — then audit those statements for missing indexes.

This is `diagnostics/polaris_api_dependency_test.ipynb` taken one layer down: not "which API depends
on which API", but "which API hits which row in which table, by which query, with which access
path".

## Purpose

Three questions, in priority order:

1. **Which database table does each API use?** → the API → table matrix.
2. **Which queries are slow?** → per-statement server-side durations, ranked by
   `mean × calls` rather than by max duration, because the query worth fixing is the moderately
   slow one on the authorization path, not the slowest single outlier.
3. **Which index does not exist but should?** → schema-drift comparison against the expected
   `schema-v2` index set, plus an `EXPLAIN (ANALYZE, BUFFERS)` verdict per captured statement.

The third is the reason this exists. The deployed schema version matters: an instance created under
an older schema and never migrated will silently lack indexes its own version defines, and that is a
different problem from an index upstream never created. The audit distinguishes them.

## Notebooks

- `01_api_access_map.ipynb` — Phase 1. Schema drift → optional seed → full API sweep → API/table and
  API/MinIO matrices → statement inventory → index audit. Writes `doc-api-sql-matrix.md` and
  `doc-index-audit.md`.

Phase 2 (read-API cache/repeat protocol) and Phase 3 (all-CRUD performance) are separate, later
notebooks — see **Next phases** below.

## How to run

1. Work through `doc-instrumentation-runbook.md` first. The notebook's preflight fails loudly if the
   Polaris SQL DEBUG stream is not live — a silently-empty capture reads as "this API touched no
   tables", which is the most misleading result the run could produce.
2. `Restart & Run All`.
3. Decide on seeding. `RUN_SEED = False` by default: the API → table mapping is valid without it, but
   index verdicts will come back `TOO_SMALL`, because a sequential scan on a small table is the
   correct plan and proves nothing. Set `RUN_SEED = True` for a meaningful index audit.
4. Set `TEARDOWN_SEED = True` in the final section when finished, then revert the instrumentation.

**LOCAL ONLY.** The notebook calls `require_not_prod()`, asserts the target host is local, and
`polaris_seed.require_local()` refuses any non-local Polaris independently. This suite enables debug
logging, creates ~16,000 entities and deletes them again — none of that is acceptable on a shared
company realm.

## Cluster topology (confirmed 2026-08-18)

| Component | Resource | Endpoint |
|---|---|---|
| Polaris | `deploy/benchmarks-polaris` | `192.168.139.2:8181` |
| Polaris management | `svc/benchmarks-polaris-mgmt` | `192.168.139.2:8182` — `/q/metrics` |
| Pooler | `deploy/benchmarks-postgresql-postgresql-ha-pgpool` | `192.168.139.2:5432` |
| PostgreSQL | `statefulset/benchmarks-postgresql-postgresql-ha-postgresql` | ClusterIP only, 3 replicas |
| MinIO | `deploy/benchmarks-minio` | `192.168.139.2:9000` |

Two things this changes versus the original plan:

- **The pooler is Pgpool-II, not PgBouncer** (`CLAUDE.md` says PgBouncer; the Bitnami `postgresql-ha`
  chart ships Pgpool-II). Pgpool **load-balances SELECTs across the three replicas**, so a PG server
  log tailed from one pod misses statements, and the prepared-statement caveats differ from
  PgBouncer's.
- **Direct-to-Postgres requires a port-forward.** Only the pgpool service is a LoadBalancer, so
  decision #6's "direct access is available" holds only via
  `kubectl port-forward pod/...-postgresql-0 5433:5432`. Worth doing for the mapping and index runs;
  leave it out of any later latency run, since production traffic goes through the pooler.

## Modules

All logic lives in `src/`, per the repo convention; the notebook only orchestrates and renders.

| Module | Role |
|---|---|
| `src/iceberg_rest.py` | **New.** Complete Iceberg REST Catalog v1 client — config, namespaces, tables, views, transactions, HEAD-exists, stage-create, register, rename, metrics, credential delegation. Standalone; does not modify or import `polaris_rest.py`. |
| `src/api_trace.py` | **New.** Three-stream trace capture (Polaris DEBUG SQL log, PostgreSQL server log, `mc admin trace --json`) with windowed correlation, secret redaction, cache-verdict inference, and the matrix/inventory reporting helpers. |
| `src/schema_audit.py` | **New.** Schema-drift comparison, `EXPLAIN` with write-safety guards, access-path verdicts, and the documented index hypotheses. |
| `src/polaris_seed.py` | **New.** The 1,000-user fixture — resumable, idempotent, ledger-backed teardown, local-host guard. |
| `src/polaris_rest.py` | Unchanged. Used as-is. |

Tests: `test_iceberg_rest.py`, `test_api_trace.py`, `test_schema_audit.py`, `test_polaris_seed.py` —
140 cases, all mocked, no live cluster needed.

## The seed fixture

```
1,000 x  user{N}_principal
1,000 x  user{N}_principal_role      assigned to user{N}_principal
1,000 x  user{N}_catalog
           +-- catalog role `owner_principal`
           |     assigned to user{N}_principal_role
           |     granted the FULL explicit privilege set (~25 names)
           +-- 2 namespaces x 5 tables  (10 tables per catalog)
```

≈ 16,000 `entities` rows and ≈ 25,000 `grant_records` rows. The grant volume is the point:
`grant_records` is the table whose grantee access path is under suspicion, and a realm with
thousands of grants is where a missing index stops being theoretical.

**Cost:** ~17,000–33,000 API calls (15–30 minutes), ~10,000 MinIO objects. `SeedSpec(create_tables=False)`
gives a metadata-only variant that is roughly 10x faster and still fully populates `grant_records`.

Seeding is resumable: every completed user is written to a JSON ledger, so an interrupted run
resumes rather than restarting. **Teardown works from that ledger, not from a name sweep** — at
16,000 entities, deleting by prefix is not a safe cleanup strategy.

## Result

_To be filled in after the first live run._ Record here: schema version and drift verdict, the
API → table matrix summary, whether `load_table` reads `metadata.json` from MinIO, and the status of
each index hypothesis.

## Open hypotheses (pre-run)

Derived from reading the Polaris 1.3.0 DDL against `JdbcBasePersistenceImpl`'s query predicates.
**These are hypotheses, not findings** — stated up front so the run has something specific to confirm
or kill, and so a null result is still informative.

| Hypothesis | Severity | Claim |
|---|---|---|
| `grant_records_by_grantee` | high | `grant_records` has only its PK, which leads with the *securable* columns. `loadAllGrantRecordsOnGrantee` filters by *grantee* — positions 4–5 — so there is no selective access path. It runs on the authorization path of every authenticated request. |
| `entities_row_constructor_in` | high | The entity-cache validation query uses a row-constructor `IN` list, which PostgreSQL does not always turn into an efficient index scan. It is the single hottest query in the system. |
| `grant_records_delete_or` | medium | `deleteAllEntityGrantRecords` ORs two disjoint column sets, typically not servable by one index scan. |

## Next phases

Deferred by decision — see the plan doc §13.

- **Phase 2 — read-API cache and latency.** The R×N repeat protocol over ~15 read operations, plus
  the cache probe. Run it *after* the seed exists: cache behaviour at 16,000 entities is not the
  same as on an empty instance.
- **Phase 3 — all-CRUD performance.** `/q/metrics` per-API timers at
  **`http://192.168.139.2:8182/q/metrics`** (the `benchmarks-polaris-mgmt` LoadBalancer — note 8182,
  not the 8282 the upstream docs use as their default). Nearly free, start there;
  OpenTelemetry span trees, PostgreSQL statistics, write-path variable sweeps, and the official
  Gatling suite (`apache/polaris-tools/benchmarks`) for throughput.
- **Phase 4 — perspectives beyond DB/SQL/Index.** Client call-pattern analysis, response payload
  size, RBAC topology.
- **Phase 5 — remediation.** If a hypothesis confirms: create the index locally, re-run, record the
  before/after delta, check Polaris `main`, then file upstream.

The **schema-drift check** should also be split into `availability/` as a small read-only notebook —
it is PROD-safe and independently useful for answering "is this deployment's schema what we think it
is" on the company clusters, where this suite must never run.

## `04_explain_sweep.ipynb` — the EXPLAIN sweep, default schema

Plans every `(SQL, params)` pair the three matrix reports recorded, against the
schema **as this cluster runs it**, and reports what scans what. Drives no APIs
and needs no Polaris restart — plain `EXPLAIN`, never `EXPLAIN ANALYZE`, which
is what makes the write half askable and leaves no clock to misquote.

**It does not change the schema.** No index is created and none dropped. The
question is what this deployment does, and an experiment that adds an index is a
different question — one whose answer is worthless if the measurement it is
compared against was taken on a mutated schema.

Testing a proposed index is legitimate and lives elsewhere on purpose:
`drop_grantee_index.py` removes one and a `CREATE INDEX CONCURRENTLY` puts it
back. Run those knowingly from a shell and re-run the notebook afterwards —
never as a side effect of the measurement.

`Restart & Run All`; read-only against the schema, so re-running is always safe.
Cell 5's dry run touches no database and is where refusals are read: the 3
`principal_authentication_data` pairs are redacted at capture and permanent,
anything else is a parser fault worth stopping for.

## `render_index_findings.py` — the findings report

```bash
uv run python render_index_findings.py --latest
```

Renders `reports/doc-api-index-findings-<stamp>.md` (and the tracked
`-latest.md`) from the newest `runs/apiexplain-<case>-*.json` per case.

**Generated, not written.** Every figure is read from the run files at render
time and the document names the files it used, so it can be checked against its
own evidence. A report whose numbers are typed by hand drifts from the runs that
produced them and nobody notices until someone tries to reproduce it.

Re-run it after any sweep; it always reflects the newest runs on disk.

## `05_merge_explain.ipynb` — plans back into the matrix

Puts each statement's EXPLAIN line directly under the statement, in the matrix
report that recorded it. Writes
`reports/doc-api-sql-matrix-<case>-explained-<stamp>.md` and the tracked
`-latest.md`.

**Touches no database and no cluster** — two files in, one out. Safe to run
anywhere, any number of times; annotations are replaced, never stacked.

Set the filenames by hand in cell 2, one pair per case. Cell 3 refuses a pair
whose run was taken against a different case or a different matrix: a report
annotated with another identity's plans reads as correct and is not.

The join is on `(normalised SQL, params)` — a real key, since that is what
`query_profile` groups on. Position is unusable: `explains` and the matrix's
pairs were zipped at write time and neither list survives re-reading in order.
Cell 4 asserts every miss is a redacted secret-table statement; anything else
means the wrong two files were paired.

## `06_explain_workbook.ipynb` / `render_explain_workbook.py` — the comparison workbook

```bash
uv run python render_explain_workbook.py --case admin \
    --matrix reports/doc-api-sql-matrix-admin-<stamp>.md \
    --explain runs/apiexplain-admin-<stamp>.json
```

Writes `reports/api-explain-<case>-<stamp>.xlsx`, **one file per case**. Seven
sheets: `Summary`, `Statements`, `Distinct`, `Shapes`, `Unplanned`, `Schema`,
`Provenance`. Design in `PLAN-explain-workbook.md`.

**A view, not a source.** Every figure is read from the matrix report and the
run file at build time; the run JSON stays authoritative. Refuses a run whose
`case` or `matrix` disagrees with the report — a workbook built from a
mismatched pair looks entirely correct.

**Open `Provenance` first.** `total_cost` and `plan_rows` are planner estimates
that move with `ANALYZE` (11 of 264 changed between two sweeps while 0 changed
in plan shape), and `duration_ms` comes from the capture rather than the
EXPLAIN, which does not execute. The sheet says so where the reader will see it.
