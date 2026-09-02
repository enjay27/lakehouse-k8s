# HANDOFF — the three drives ran, and recorded no SQL

Written 2026-09-01. Standalone. Companion to `PLAN-api-index-matrix.md` (design)
and `RUNBOOK-api-index-matrix.md` (commands). Read this one first.

---

## 0. Where this stands, in one paragraph

Three identity drives completed cleanly — unauthorized, authorized, admin — and
each wrote a report to `reports/doc-api-sql-matrix-<case>-<stamp>.md`. **Every
one of the 43 APIs in all three reports says `0 statements` and `tables: —`, and
the API→PostgreSQL matrix has an empty column.** The correlation recorded
nothing, so no SQL was captured and nothing can be EXPLAINed yet. The drives
themselves are sound; the *statement capture* is not. Fixing that is task 1 and
everything else waits on it.

---

## 1. THE BLOCKER, and the evidence

`polaris.log` across four separate runs: **1,311,110 / 1,311,107 / 1,311,109 /
1,311,112 bytes.** Four runs, near-identical volume. A 43-refusal run and a
43-success run cannot produce the same number of bytes. That is the Polaris
**startup burst** and nothing after it.

The liveness gate in notebook cell 9b passed anyway, and that is the second
fault. It uses `privilege_scan.capture_snapshot` / `capture_verdict`, which
check that bytes arrived AND that `DatasourceOperations` lines are present.
Seconds after a restart, the startup dump supplies both. The gate was written
for a steady-state cluster and is being called while the pod is still dumping,
so it confirms the stream is *alive* without confirming it recorded **the probe's
own call**.

### 1.1 The fix to make first — 01 already has it

`01_api_access_map.ipynb` cell 6 builds the tracer and then calls
`preflight(tracer, probe=lambda: pc.list_catalogs())`, with the comment:

> The tracer is built BEFORE preflight now, because preflight uses it to prove
> the stream is live rather than guessing from the log's tail.

That is the right shape and the runner does not have it. **Prove the TRACER sees
a statement**, not that the file contains one:

```python
tracer = Tracer(**capture_streams(capture))
with tracer.trace("preflight", "GET", "/v1/catalogs") as rec:
    pc.list_catalogs()
assert rec.sql_count > 0, "the tracer read no SQL for a call that certainly issued some"
```

Put it in `drive_api_surface.do_drive` before the sweep, and in cell 9b in place
of the byte/content gate. A drive that starts without this passes every existing
check and produces 43 empty rows.

### 1.2 Candidate causes, in the order worth testing

1. **`settle_s` too short for a restarted cluster.** 01 uses `settle_s=0.30`;
   `capture_streams` leaves the `Tracer` default of 0.25. If `kubectl logs -f` is
   buffering behind the startup burst, a request's lines land seconds late and
   every `read_since_mark()` returns startup text or nothing. Try 1.0–2.0 first;
   it is one argument and costs 43 seconds a run.
2. **The tail is behind, not stopped.** Check whether `polaris.log` keeps growing
   for a minute AFTER a drive ends. If it does, this is purely a timing problem
   and (1) fixes it.
3. **`parse_polaris_log(require_logger=True)`** rejecting lines whose logger name
   is abbreviated. `doc-instrumentation-runbook.md` §"lines read
   `[org.apa.pol.per.rel.jdb.DatasourceOperations]`" — the abbreviated form is
   expected and handled, but confirm against a real captured line.
4. **`MultiStream`/`FileStream` position.** Moved into `src/api_trace.py` on
   2026-09-01. Verify `mark()` then `read_since_mark()` returns non-empty text on
   a file being appended to by another process.

### 1.3 Do not re-drive until 1.1 is in

Each drive costs a Polaris restart plus a capture. Three of them have already
produced nothing. The preflight assertion turns that into a failure in the first
second rather than after the 43rd operation.

---

## 2. What the reports must contain when this is fixed

Kade's requirement, verbatim in shape:

```
### `iceberg.get_config`

- `GET /v1/config` → **200**
- wall 94 ms · 0 statements · 0 object ops · entity access: N/A
- tables: —
- QUERY (select from table ...)
```

Two additions per API:

**(a) The QUERY.** `api_report.render_statements` ALREADY emits this — full SQL
in a fenced block plus its `params:` line, per statement. It emitted nothing
because `rec.sql` was empty. **No renderer change is needed for the QUERY; fix
§1 and it appears.** Confirm with `test_api_report.py`, whose round-trip test
covers exactly this path.

**(b) The EXPLAIN result, per API.** This is new. `explain_api_matrix.py`
produces `runs/apiexplain-<case>-<stamp>.json` holding, per (SQL, params) pair:
`scans`, `seq_scanned`, `indexes_used`, and the full plan. The renderer must
join those onto the statements it prints — the pair is the key, and
`query_profile.parse_api_statements` already keys on it. Suggested per-statement
block:

```
**[3]** `grant_records` · SELECT · no timing

```sql
SELECT ... WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1002, POLARIS, 0`

EXPLAIN (index present) — Index Scan using idx_grant_records_grantee, 3 buffers
EXPLAIN (index absent)  — Seq Scan on grant_records, 572 buffers, 60,783 rows removed
```

Both index states on the same statement is the point; that contrast is the
finding. Add a per-API rollup line too (`per_api` in the run JSON already has
`seq_scanned` / `indexes_used` / `uses_index_only`).

---

## 3. Measured facts — carry these into the report

### 3.1 The identities, and what they actually exercised

| case | identity | token scope | footprint | permitted / refused / other |
|---|---|---|---:|---|
| unauthorized | `zerograve_principal` | own role | **1** | 2 / 22 / 19 |
| authorized | `authz1_principal` | own role | **78** | 28 / 5 / 10 |
| admin | `admin1_principal` | **`service_admin`** | 3,377 (ceiling) | see §3.4 |

**Footprint is not what the token carries.** `--footprint` walks EVERY role a
principal holds; a token is scoped to ONE. 3,377 is admin's ceiling, not what its
grantee lookup resolves. Say which in the report.

**`authz1` is an outlier in its own tier** — 78 against the other 99 identities'
52, because `--authorize` granted it rights on the shared probe catalog. Quote
the authorized case at 78.

### 3.2 The authorization boundary, measured

Authorized (catalog-scoped) is refused **exactly** the five service-scoped
operations: `mgmt.create_principal`, `create_principal_role`, `list_catalogs`,
`list_principal_roles`, `list_principals`. Every catalog-scoped `mgmt.*`
succeeded. Independently reproduces the 2026-08-24 probe's finding through a
different fixture and identity.

Admin is **not** a superset: `mgmt.reset_principal_credentials` → **403**.
`service_admin` reads every management API and is refused credential vending;
the catalog-scoped owner is the reverse. Neither tier contains the other, and
that is the headline the three-identity design exists to produce.

### 3.3 Statuses that are not authorization outcomes

- **404 is usually SECOND-ORDER.** A refused `create_*` leaves every dependent
  operation addressing an entity that does not exist. 19 in the unauthorized
  case, 10 in authorized, and they collapse as authority rises. They still issue
  SQL — entity-lookup-miss paths — and their statements belong in the report,
  labelled as such and never as denials.
- **500 on `create_view` and `create_namespace` is a WRITE THAT SUCCEEDED.**
  Kade: a database sync error. Corroborated independently — `load_view`,
  `head_view`, `rename_view` and `drop_view` all answered 2xx in the same run,
  which is impossible unless the create committed. Known PG-HA read-after-write
  signature; `_attempt` exists because of it.
- **Two operations succeed for a ZERO-grant principal**: `iceberg.get_config`
  (200) and `iceberg.report_metrics` (204). `get_config` is plausible;
  `report_metrics` accepting a write-shaped call from an identity with no rights
  is worth verifying against the source before it is called a finding.

### 3.4 Re-drive admin

The admin run in `reports/` was taken with the token scoped to
`admin1_principal_role` instead of `service_admin`, and is a copy of the
unauthorized case. `resolve_identity` is fixed (2026-09-01) but **the report on
disk is from before the fix** — the 2026-09-01 15:41 file shows the corrected
run. Verify the scope line reads `PRINCIPAL_ROLE:service_admin` before trusting
any admin report.

### 3.5 Volume at drive time

`entities` 9,634 · `grant_records` 60,819 · `policy_mapping_record` **0** ·
`principal_authentication_data` 1,108.

`policy_mapping_record` is empty and stays empty: a mapping row is written when a
policy is ATTACHED to a target, not when one is created (12 policy entities
exist). Its **2 statement texts are NOT MEASURABLE at this fixture** — report
them as that, never as a plan, because every plan against an empty table looks
identical.

---

## 4. The sweep, once statements exist

Unchanged from the plan. Per case, both index states:

```bash
uv run python explain_api_matrix.py --case <case> --index-state present \
    --matrix reports/doc-api-sql-matrix-<case>-<stamp>.md
# then drop_grantee_index.py + ANALYZE, repeat with --index-state absent, then restore
```

`--index-state` is checked against live `pg_indexes` and refuses on a mismatch.
`analyze=False` throughout: plain EXPLAIN never executes, which is what makes the
write half askable and leaves no clock to misquote.

Expect ~115 (SQL, params) pairs per case from a full matrix; 112 of 115 replay
in the archived root matrix, the other 3 being redacted secret-table parameters
that never will.

---

## 5. Guards — every one cost something this session

- **Compare distributions ACROSS runs.** Three separate faults were caught only
  this way, and none from a single run's output: two runs matching exactly is a
  fixture fault, not a finding. Each individual run looked perfect — 43/43,
  zero errors, healthy capture.
- **Bytes are not evidence, and neither is content right after a restart.** §1.
- **A summary that prints only the buckets you thought of hides the rest.**
  `permitted 2 refused 22` omitted 19 operations. `DriveResult.other` and
  `.distribution` now exist because of it.
- **Errors are not refusals.** 43 `IsADirectoryError` reported as errors; had
  they been collapsed into refusals it would have read as a flawless
  unauthorized pass.
- **A token is scoped to ONE principal-role.** An identity holding two gets the
  one it asked for. Never `PRINCIPAL_ROLE:ALL` for a non-root principal — 200
  with no effective role, then 403 everywhere.
- **A catalog-scoped principal cannot act on a catalog it does not own.** Grant
  it with `--authorize` first, or it reads as unauthorized.
- **Never write a secret into `os.environ`** — it persists for the kernel and
  the next case authenticates as the wrong identity. `sh(env=...)` overlays
  per-call. Never print one into a tracked notebook's output either.
- **`capture.sh rotate` does not enable statement logging.** `pgon` is separate.
  `PGDUR=1` adds durations.
- **`--footprint` said "uniform" for `[52, 78]`.** Fixed. A false green light is
  worse than a false alarm: nobody investigates it.

---

## 6. Definition of done

- A tracer-level preflight proving SQL is read, in the runner and cell 9b.
- Three reports where every API lists its statements with full SQL and params —
  the QUERY Kade asked for.
- Six `apiexplain-*.json` (3 cases × 2 index states), each recording the live
  `pg_indexes` state it was taken in.
- Reports carrying the EXPLAIN result per statement, both index states, plus a
  per-API rollup.
- `policy_mapping_record`'s 2 texts marked not-measurable; INSERT texts accounted
  for, not planned (`INSERT … VALUES` plans to a Result node — no scan, no index
  to detect).
- §3's measured facts stated, including that admin is not a superset.
- `black` (last), `isort`, `pytest` green — 183 across five suites.
- `MEMORY.md` *Now* + `.memory/` updated; one commit, message stating the finding.
