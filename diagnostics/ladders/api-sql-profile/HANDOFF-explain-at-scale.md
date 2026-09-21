# HANDOFF — the EXPLAIN sweep is done at 60,815 grants; next is the reseed to ~500K

Written 2026-09-03, end of session 5. Standalone — read this one first.

Companions: `PLAN-seeding-production-shape.md` (how to seed),
`RUNBOOK-api-index-matrix.md` §1 (the seed commands), `PLAN-explain-workbook.md`
(why the workbook has the sheets it has). `HANDOFF-api-index-matrix.md` describes
a capture blocker that is **closed** — keep it for the falsified-theories table in
§1.2, ignore its "where this stands".

---

## 0. Where this stands, in one paragraph

The three-identity EXPLAIN sweep is **complete and reported** on the plain
upstream schema at **60,815 `grant_records` / 9,646 `entities`**. Every finding
below is measured, not projected. The next task is Kade's: seed ~10,000
principals (~500K grant_records), then re-run the sweep and diff the two `Cost`
sheets. §4 is the trap list for that comparison — read it before drawing any
conclusion from the second run, because two of the four traps make the new
numbers look *reassuring* when they are not.

---

## 1. The finding, at 60,815 grants

**`grant_records` is the only relation ever sequentially scanned.** Across all
three identities, every other table — `entities`, `policy_mapping_record`,
`principal_authentication_data` — is reached by index every time.

Exactly two statement shapes cause it:

| shape | occurrences | APIs | cases | cost | predicate columns |
|---|---:|---:|---:|---:|---|
| grantee lookup `SELECT` | 163 | 43 (all) | 3 | 1637.26 | `realm_id, grantee_catalog_id, grantee_id` |
| cascade `DELETE` (OR-shaped) | 10 | 6 | 2 | 1941.34 | + `securable_catalog_id, securable_id` |

The grantee lookup is the whole story: **all 43 APIs issue it**, on every
authenticated call.

**Why the PK does not cover it.** `grant_records_pkey` is
`(realm_id, securable_catalog_id, securable_id, grantee_catalog_id, grantee_id,
privilege_code)`. The grantee columns sit at positions **4–5**, so after
`realm_id` the B-tree prefix breaks. The DELETE is different: its predicate would
be a clean prefix, but it is shaped as an `OR` of the securable side and the
grantee side, and the `OR` is what defeats the index.

The same table is served well in the other direction: **50 `SELECT`s use
`Index Only Scan` on `grant_records_pkey`** (the securable lookup), and the 4
`INSERT`s plan to a Result node with no scan. So the table is not the problem —
one access direction is.

**Confirmed upstream.** `schema_v3.sql` ships no index on the grantee columns.
This is not a local schema drift.

### Weight, per case

| case | statements reading the whole table | occurrences | share of planner cost |
|---|---:|---:|---:|
| unauthorized | 2 of 33 | 52 | 95.5% |
| authorized | 6 of 91 | 54 | 94.1% |
| admin | 11 of 128 | 67 | 93.8% |

All on `grant_records`. Roughly 94% of each case's planner cost is one access
pattern against one table.

---

## 2. What was built this session

### Tooling
- **`render_explain_workbook.py`** — 8-sheet workbook per case. New this session:
  the **`Cost`** sheet, and three columns carried onto `Statements`/`Distinct`:
  - `rows_scanned` — what the plan **reads**: the whole table for a Seq Scan, the
    `Index Cond` match for an index node.
  - `rows_basis` — `whole table` / `index match` / `index match, lower bound`.
  - `scales_with_table` — **the column to sort on before a reseed.** TRUE means
    rows *and* cost move with the row count.
  - Plus `cost_units` (`total_cost × occurrences`) and `cost_share`.
- **`-latest` copies.** Each build also writes `api-explain-<case>-latest.xlsx`,
  and `Provenance` rows 1–2 are now `workbook_file` / `workbook_built`.
- **`write_rows` width guard** — a row narrower than its header now raises.
- **Notebook 06** — cell 5b prints the `Cost` headline and the reseed split
  without opening Excel.

### Deliverables on disk
```
reports/api-explain-{unauthorized,authorized,admin}-latest.xlsx
reports/doc-api-index-findings-latest.md
reports/doc-api-sql-matrix-<case>-explained-latest.md
runs/apiexplain-<case>-20260903-1101*.json          <- the authority
```

### Deliberately NOT built
A hypothetical-index counterfactual. Kade's call, 2026-09-03: *"Why this plan
needs to create new index? No index means full-scan, so just write that query's
cost is high."* Rows and cost sit side by side; the reader draws the line. An
earlier commit (`17fb18e`) added ratio columns against a measured indexed
baseline and `513fb88` removed them again — do not reintroduce them without
asking.

---

## 3. Standing policy — do not violate without asking

**Plain upstream schema, no custom indexes.** Kade, 2026-09-03, applied to every
notebook. `02_index_audit.ipynb` and `02b_grant_scale_sweep.ipynb` are marked
**OFF-POLICY** in `CLAUDE.md` because they create indexes; `04_explain_sweep.ipynb`
is read-only by design. `drop_grantee_index.py --list` confirms the live state.

Also in force from `CLAUDE.md`: no hardcoded credentials (load via `init_env()`);
never commit secrets, capture directories, or a broken tree; `admin/` teardown is
local-only; mutating notebooks call `require_not_prod(...)`; PROD is availability
tests only; **`git push` is Kade's decision**.

---

## 4. THE RESEED — four traps, in the order they will bite

The plan is `PLAN-seeding-production-shape.md`; the commands are
`RUNBOOK-api-index-matrix.md` §1. What follows is not in either, and all four
make the second sweep *look* fine.

### 4.1 The sweep pins parallelism off, so the shape flip is invisible

`profile_queries.explain_statements` sets
`max_parallel_workers_per_gather = 0` for the session (`pin_serial=True`, the
default, and `explain_api_matrix.py` does not override it). This was deliberate —
02b measured parallel timings as unusable: identical plan cost and buffers with a
3–10× clock spread.

The consequence for the reseed: **`parallel` is structurally `FALSE` in these run
files, and the post-reseed sweep will still report `Seq Scan`.** That is the pin,
not the planner.

02b already measured what actually happens, unpinned:

| rows in table | plan without index |
|---:|---|
| 125,235 | `Seq Scan` |
| 233,237 | **`Gather`** (parallel) |
| 611,239 | **`Gather`** |

A 10,000-principal reseed lands past that boundary. So "same plan shape at 500K"
is an artifact of the pin. To ask the escalation question, run **one unpinned
pass** (`pin_serial=False`) alongside the pinned one, or cite
`reports/doc-grant-scale-sweep-latest.md`, which already answers it.

### 4.2 `Gather` is a different regime, not more of this one

Once the plan escalates, `cost_x`-style reasoning and the whole `Cost` ranking
change basis — a `Gather` node's cost is not comparable to a serial `Seq Scan`'s.
Compare **shapes** across the two sweeps, and treat the cost columns as
within-sweep only.

### 4.3 Growth is not uniform

`grant_records` grows with principals × grants. `entities` grows with catalogs
and tables. Seeding 10,000 principals moves one axis. The `scales_with_table`
TRUE rows are all on `grant_records`, so they move; the `entities` rows mostly do
not. **Do not multiply the whole sheet by the growth factor.**

### 4.4 The estimates drift, the shapes do not

Two sweeps 25 minutes apart differed in **11 of 264** `plan_rows` and **0 of 264**
plan shapes. Sort and compare shape. Do not average, sum or trend `total_cost` or
`plan_rows` across runs.

Also: `baseline`-style row counts of `1` are estimates with a **floor of 1** —
PostgreSQL never estimates below one row. The real grant footprints are 1
(unauthorized), 78 (authorized), ceiling 3,377 (admin).

### 4.5 Suggested order for the next session

1. Dump first (`RUNBOOK` §0) and **prove the dump restores**. The reseed is slow
   and not cheaply reversible.
2. `drop_grantee_index.py --list` → confirm the schema is still plain.
3. Seed. Record the new `count(*)` for all four tables before anything else —
   every plan is relative to them.
4. Re-drive the three identities (`RUNBOOK` §4; **drive from a terminal and pass
   `--capture`** — see §5 below).
5. Re-run `04_explain_sweep.ipynb`, then `05`, then `06`.
6. Add **one unpinned EXPLAIN pass** for the two seq-scanning shapes, to answer
   §4.1. This is the only genuinely new measurement the reseed enables.
7. Diff the two `Cost` sheets on `scales_with_table` and plan shape.

---

## 5. Landmines that have already cost a session each

- **Drive from a TERMINAL, not from notebook `03`.** The capture tail dies when
  started from the notebook; 859 lines vs 25. `RUNBOOK` §4.0. The notebook defect
  is still open.
- **`read_text()[-40000:]` swallowed by one long line.** A 1.29 MB
  `listCatalogs` INFO dump made a 25-line file look empty. Fixed by
  `privilege_scan.tail_lines(path, n=800)` — a *line* window, not a character
  one. Three sessions read a gate's output as data about the cluster when it was
  data about a slice.
- **Pgpool health checks** emit `LOG: statement: ` with empty text — 22.6% of pg
  statements. Dropped at the parse boundary.
- **The primary is `postgresql-1`, not `-0`.** HA behind **Pgpool-II**, not
  PgBouncer. `assert_primary(conn)` and `/*NO LOAD BALANCE*/` exist for this.
- **Placeholder dialects differ**: Polaris logs `?`, PostgreSQL logs `$N`.
  `normalize_sql` unifies them; `_PG_DETAIL_PARAMS` needs `re.I` because the
  cluster emits `DETAIL:  Parameters:` with a capital P.
- **`black` must run LAST** — no isort profile is set, so reordering imports
  after formatting churns the diff. And a string-replacement patch written
  against pre-`black` text will not match; re-read the formatted file first.
- **Nine near-identical workbook names** in `reports/` cost a round trip on
  2026-09-03 — the oldest generation sorts first in a file picker. Hence
  `-latest` and the `workbook_file` / `workbook_built` Provenance rows.

---

## 6. Open, and honest about it

- **`.venv` was rebuilt against macOS Python at 05:08 on 2026-09-03** and is no
  longer usable from a Linux side of the bridge (`.venv/bin/python` →
  `/Users/kade/.local/share/uv/python/cpython-3.12-macos-aarch64-none/...`).
  **The test gate was NOT re-run after commits `529dcea` and later.** Last known
  state: **1 failed, 638 passed**. Run `pytest` on the Mac before trusting the
  tree.
- **Pre-existing red test:** `test_privilege_scan.py::test_probe_table_names_the_refusals`
  expects `| NO |`; the renderer emits `refused` / `authorized`. Left for Kade to
  arbitrate — either the test or the renderer is right, and nobody has decided
  which.
- **Notebook `03` capture defect** — still open, worked around by driving from a
  terminal.
- **The `--index-state present` half of the sweep has never been run** under the
  current policy, and should not be without asking; it requires creating the
  index the policy forbids.
