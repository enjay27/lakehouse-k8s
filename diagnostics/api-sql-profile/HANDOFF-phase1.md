# Polaris API–SQL Profiling — Phase 1 handoff

State as of 2026-08-20. Written so a fresh session can start at notebook 02
without replaying the history.

## Where things stand

**Fixture is built and verified.** 1,000 users — principal, principal-role,
catalog, catalog-role, 2 namespaces each; no Iceberg tables (`--no-tables`).
Verified from the PostgreSQL **primary**: every entity present, zero gaps.

| table | rows |
|---|---:|
| `entities` | ~7,273 |
| `grant_records` | ~30,013 |
| `principal_authentication_data` | 1,002 |

Re-check any time with:

```bash
cd diagnostics/api-sql-profile && python3 seed_polaris.py --verify
```

**Notebook 01 is complete and its reports are trustworthy.** 43 APIs traced
across both surfaces, all healthy statuses (the single 404 is the deliberate
`load_table[missing]` probe). Reports land in `reports/` with a timestamp plus
a `-latest` copy; `.gitignore` there is yours to manage.

## The finding

`grant_records` is read on the authorization path of **every** authenticated
request. Its only index is the primary key
`(realm_id, securable_catalog_id, securable_id, grantee_catalog_id, grantee_id, privilege_code)`.

A lookup **by grantee** constrains positions 1, 4, 5 and leaves 2–3 free, so
only `realm_id` is usable as a leading prefix — which in a single-realm
deployment is the whole table.

| statement | plan | rows | ms |
|---|---|---:|---:|
| `grant_records` SELECT **by grantee** (59 calls) | **Seq Scan** | 30,013 | **3.19** |
| `grant_records` SELECT by securable (23 calls) | Index Scan `grant_records_pkey` | 30,013 | **0.02** |

Same table, same run, **160× apart**. Not size — predicate shape.

Proposed remedy (still absent from upstream `schema-v3.sql`, so an upgrade does
not supply it):

```sql
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_grant_records_grantee
    ON POLARIS_SCHEMA.grant_records (realm_id, grantee_catalog_id, grantee_id)
    INCLUDE (securable_catalog_id, securable_id, privilege_code);
```

`entities` is well covered — every statement an index scan under 0.1 ms via
`constraint_name` or `idx_entities`. **One index is the fix, not a schema
overhaul.**

## Hypothesis status

| id | status |
|---|---|
| `grant_records_by_grantee` | **CONFIRMED** |
| `grant_records_delete_or` | **CONFIRMED** |
| `entities_row_constructor_in` | **REFUTED** — measured, planner handles it |

## Next: notebook 02

```bash
# reads via the Pgpool LoadBalancer at 192.168.139.2:5432, but every EXPLAIN
# carries /*NO LOAD BALANCE*/ so it plans on the PRIMARY. A replica can hold
# different statistics and would silently measure the wrong node.
```

Leave `RUN_SEED = False` — 01 and 02 share `capture/seed_ledger.json`, and
seeding twice would create 2,000 users against `max_connections = 100`.

02 creates the index, re-EXPLAINs, and reports the before/after delta.

## Open items

**The IN-list statement — CLOSED.** The entity cache's bulk validation
(`(catalog_id, id) IN (...)`, 128 calls) was measured by cell 29 at list sizes
1/10/50/200/500. Worst plan is an **INDEX_SCAN** at every size, so the planner
handles the row constructor and the hypothesis is **REFUTED**. No upstream
rewrite needed — a real negative result, and it means the cache's validation
path is not a hidden cost.

**Four statements remain NO_PARAMS**, all writes: an `entities` UPDATE (13
calls) and three DELETE/INSERT variants. `resolve_params` refuses them because
the placeholder count spans SET/VALUES clauses, not just the WHERE. Their
predicates are PK-shaped and a sibling `entities` DELETE does show
INDEX_SCAN via `idx_entities`, so they are very likely fine — but they are
unmeasured, and should not be described as verified.

**`cache: MISS` on all 43 APIs — do not trust that column.** Including repeated
reads of the same table. Either the inference is wrong or every probe is
genuinely cold. The repeat protocol (Phase 2) is what would settle it.

**Durations are a sample, not a census.** ~1,343 statement rows carry a `ms`
value and ~761 do not, so per-statement timing covers roughly two thirds.

**Replication lag is load-dependent and significant.** Under the 1,000-user
seed, 61% of `create_namespace` calls returned 5xx for writes that had
committed; at low load it fell to 1.6%. The same fault also surfaces as 403
(authorization resolved against a lagging replica) and 404. `polaris_seed`
absorbs all three via `call_with_lag_retry`.

**Two Polaris behaviours worth writing up independently of the index work:**

1. *Catalog creation is not atomic.* The entity write and the `catalog_admin`
   grant bootstrap can commit separately. The result is a catalog that answers
   `GET /catalogs/{name}` with 200 and correct storage config while
   `list_catalog_roles` returns 403 — permanently unusable, unrepairable over
   REST, and possibly undeletable. 25 of 1,000 catalogs landed this way.
   `ensure_catalog()` detects and rebuilds them.
2. *The metrics endpoint is not free.* `POST .../tables/{table}/metrics` cost 12
   statements — a full entity-path resolution plus the 7-statement auth prelude
   — even for a request it rejected with 400. Iceberg engines post a scan report
   after every query.

## Gotchas that cost time here

- **Restart the kernel** after any `src/` edit. Jupyter caches modules at
  import; mid-notebook `importlib.reload` does not fix bindings earlier cells
  already used. Several runs produced stale, wrong reports this way.
- `log_statement='all'` captures **repmgr and Pgpool traffic too**.
  `api_trace.is_polaris_statement` filters it; without that the audit fills with
  `EXPLAIN` errors on `repmgr.nodes` and `SET`.
- `capture.sh rotate <dir>` writes to a new directory; 01 resolves the newest
  `capture*` dir, or honours `$CAPTURE_DIR`.
- Turn statement logging off when done: `./capture.sh pgoff`.
