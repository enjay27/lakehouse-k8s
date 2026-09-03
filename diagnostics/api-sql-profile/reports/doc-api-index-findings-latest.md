# The authorization prelude sequentially scans `grant_records` on every request

Generated 2026-09-03 02:06 from the runs named below — Polaris 1.3.0-incubating, realm POLARIS, **plain upstream schema**.

**129 of 129 (case, API) pairs sequentially scan `grant_records`** at 60,815 rows. All 43 operations, all three identities, every refusal included.

This confirms the `grant_records_by_grantee` hypothesis, which `doc-index-audit.md` has carried as **INCONCLUSIVE** since 2026-08-20.

## 1. What was measured

Plain `EXPLAIN` — never `EXPLAIN ANALYZE`. It does not execute, which is what makes the write half askable at all and leaves no clock to misquote. Plan *shape* is deterministic here; execution time is not.

Every `(SQL, params)` pair recorded in the three API→SQL matrices was replayed against the live database, in the state the cluster runs.

| case | APIs | statement instances | (SQL, params) pairs | planned | skipped | APIs that seq-scan |
|---|---:|---:|---:|---:|---:|---:|
| `unauthorized` | 43 | 390 | 33 | 333 | 0 | **43 / 43** |
| `authorized` | 43 | 460 | 93 | 412 | 5 | **43 / 43** |
| `admin` | 43 | 564 | 138 | 504 | 10 | **43 / 43** |

Table volume at replay time:

- `entities` — 9,646
- `grant_records` — 60,815
- `policy_mapping_record` — 0
- `principal_authentication_data` — 1,108

Index state: **absent** — `idx_grant_records_grantee` is not created by the schema and was not created for this measurement.

## 2. The headline — the grantee lookup cannot use the primary key

`grant_records` has exactly one index, its primary key:

```sql
PRIMARY KEY (realm_id, securable_catalog_id, securable_id,
             grantee_catalog_id, grantee_id, privilege_code)
```

Two lookups, two fates:

| verb | predicate | plan | index | est. rows | est. cost |
|---|---|---|---|---:|---:|
| DELETE | `( (grantee_id = ? AND grantee_catalog_id = ?) OR (securable_id = ? AND sec…` | ModifyTable, Seq Scan | — | 1 | 1941.34 |
| SELECT | `grantee_catalog_id = ? AND grantee_id = ? AND realm_id = ?` | Seq Scan | — | 1 | 1637.26 |
| INSERT | _(VALUES — no predicate)_ | ModifyTable, Result | — | 0 | 0.01 |
| SELECT | `securable_id = ? AND securable_catalog_id = ? AND realm_id = ?` | Index Only Scan | grant_records_pkey | 20 | 14.11 |

_Planner estimates, from the runs named in §8; they move with `ANALYZE` — see §6. The INSERT is listed for completeness: it plans to a Result node, so no index could apply to it._

The **securable** lookup constrains `realm_id, securable_catalog_id, securable_id` — the key's leading three columns — and is served. The **grantee** lookup constrains columns 1, 4 and 5; the prefix breaks after `realm_id`, so PostgreSQL cannot use the key selectively and reads the table.

**The planner expects a single row and reads 60,815 to find it** (`plan_rows = 1`).

## 3. Every request pays it, including every refusal

The grantee lookup is `loadAllGrantRecordsOnGrantee`, on the authorization path of every authenticated request. It fires before the authorization decision, so a 403 pays the full scan:

| case | permitted | refused | grantee lookups | APIs reaching it |
|---|---:|---:|---:|---:|
| `unauthorized` | 2 | 22 | 51 | 43 / 43 |
| `authorized` | 29 | 5 | 45 | 43 / 43 |
| `admin` | 41 | 1 | 45 | 43 / 43 |

Independently reproduces the 2026-08-24 result — 6,000 refusals, 1.00 grantee lookup each — now with the plan behind the count.

## 4. `entities` is well served, by contrast

The problem is specific to `grant_records`, and to one direction of it. Indexes observed in use across the sweep:

- `constraint_name`
- `entities_pkey`
- `grant_records_pkey`
- `idx_entities`
- `policy_mapping_record_pkey`

Nothing scans `entities` sequentially. Upstream gives it `idx_entities` and `idx_locations` on top of its key and unique constraint; `policy_mapping_record` gets `idx_policy_mapping_record`. **`grant_records` is the only table read on every request and the only one with nothing but its key.**

## 5. This is upstream, not this deployment

The schema is `schema_v3.sql` — ASF licence header, *"Changes from v2: Added `events` table"* — the Apache Polaris file. The local `schema.sql` beside it is structurally identical: all 12 statements match once comments, `IF NOT EXISTS`, `ON CONFLICT` and `COMMENT ON` are normalised away, differing only in idempotency and documentation.

Upstream says it itself, at `schema_v3.sql:57`:

```sql
-- TODO: create indexes based on all query pattern.
CREATE INDEX IF NOT EXISTS idx_entities ON entities (realm_id, catalog_id, id);
```

The TODO sits directly above the two `entities` indexes. `grant_records` never got its turn.

## 6. What this does NOT establish

- **No timing claim.** `EXPLAIN` without `ANALYZE` does not execute. The cost figures are planner estimates, comparable to each other and to nothing else.
- **Reproduction covers SHAPE only.** Two sweeps 25 minutes apart across 264 explains: 0 differ in shape, 11 differ in `plan_rows` (all 19 → 20), 28 differ in some field once costs are counted — statistics moving under autovacuum. Quote the shape; never quote `plan_rows` or a cost as stable.
- **One volume.** Every plan here is relative to 60,815 `grant_records` rows. The crossover measurements put parallel escalation near 160K and the table leaving shared_buffers between 320K and 640K, so a larger realm is a different regime, not more of this one.
- **That the proposed index fixes it is untested here.** This sweep measures the schema as shipped and deliberately creates nothing.
- **`policy_mapping_record` is empty** (0 rows), so its statements are recorded and not plan-measurable — every plan against an empty table looks alike.

## 7. Statements that could not be replayed

A refused pair is not planned and not counted. Two kinds:

- **Permanent (3, admin only):** `principal_authentication_data` parameters are redacted at capture because the table holds secret material. They will never replay.
- **Recoverable (7, admin; 2, authorized):** six `grant_records` statements whose text was corrupted by a log-parsing fault, and the async `events` INSERT. The parser is fixed; they return on the next drive. All six are on the cascade-delete read path.

## 8. Reproducing this

```bash
cd diagnostics/api-sql-profile
uv run python drop_grantee_index.py --list    # confirm the schema is plain
# then: Restart & Run All on 04_explain_sweep.ipynb
uv run python render_index_findings.py        # regenerate this document
```

Read from:

- `apiexplain-admin-20260903-110152.json` — admin, index absent
- `apiexplain-authorized-20260903-110149.json` — authorized, index absent
- `apiexplain-unauthorized-20260903-110148.json` — unauthorized, index absent

