# PLAN — per-API index detection across the 44-API surface

Proposed 2026-08-31. **Plan-first: nothing is built until Kade signs off.**

Task: seed ~1,000 principals with their catalogs, namespaces, tables, views and
privileges; then, for every API in `reports/doc-api-sql-matrix-latest.md`, EXPLAIN
each SQL statement it issues and record **whether an index is used** — presence,
not performance. No timings anywhere in the deliverable.

---

## 0. What is already true — measured 2026-08-31, before any work

These are facts about the repo as it stands, not assumptions:

- **`reports/doc-api-sql-matrix-latest.md` is directly usable as the worklist.**
  It carries the **full, untruncated SQL** in fenced blocks *and* the bound
  `params:` line for every statement. (The top-level `doc-api-sql-matrix.md` is a
  different, older render whose SQL column is truncated at ~150 chars and which
  additionally logs Pgpool-II health-check traffic — `nodes`,
  `pg_stat_replication` — as if Polaris issued it. Use the `reports/` one.)
- **The unit is 115 statements, not 27.** 513 statement instances collapse to 27
  distinct SQL *texts* — but to **115 distinct (SQL, params) pairs**, and 20 of
  the 27 texts carry more than one parameter set (one carries 13). PostgreSQL
  estimates selectivity from parameter *values*, so the same SQL can plan as a
  Seq Scan with one parameter and an Index Scan with another. **EXPLAINing 27
  would answer "each distinct SQL text once, with an arbitrary parameter" — not
  "every query every API request issues."** Corrected 2026-08-31; the earlier
  draft of this plan had it wrong.

  | | count |
  |---|---:|
  | statement instances across 44 APIs | 513 |
  | distinct SQL texts | 27 |
  | **distinct (SQL, params) pairs — the sweep unit** | **115** |

  By verb the 27 texts are 19 SELECT, 4 DELETE, 3 INSERT, 1 UPDATE; by table,
  `entities` 18, `grant_records` 4, `principal_authentication_data` 3,
  `policy_mapping_record` 2.

- **So the measurement is 115 × 2 index states = 230 plain EXPLAINs.** Still
  minutes, still free next to the seed. Every one of the 513 instances maps to
  one of the 115, so every API's every statement gets a plan.

- **The matrix is a LOWER BOUND on the API surface, and the gap is measured.**
  `reports/doc-api-sql-matrix-latest.md` holds **40 operations, only 19 of them
  GET/HEAD**. The harness's own full read surface is **29–30**, and the
  privilege scan reaches all of them. So **10 read APIs appear nowhere in the
  matrix**:

  ```
  GET /applicable-policies                     GET /policies
  GET /catalog-roles/{r}/principal-roles       GET /policies/{p}
  GET /catalogs/{c}/catalog-roles/{r}          GET /principal-roles/{n}/catalog-roles/{c}
  GET /generic-tables                          GET /principals/{p}/principal-roles
  GET /generic-tables/{gt}                     GET /namespaces/{ns}/tables/{t}/credentials
  ```

  This is the *same* class of fault as last session's classifier frozen at 13
  ops, one layer up: notebook 01's operation list is narrower than
  `api_sweep.full_read_operations`, and nothing said so. `coverage_gap` /
  `coverage_from_evidence` exist precisely to make that disagreement visible —
  they report `observed_not_driven = 0` and `driven_unverified = 10` against this
  matrix right now.

  **For writes there is no independent inventory at all.** A call log proves what
  was called and says nothing about what was not, and Polaris 8181/8182 serves no
  OpenAPI document to check against. So write coverage stays a lower bound, and
  the report must say so rather than implying 44 is the surface.

- **Notebook 01 refreshes `-latest` itself** — it writes `<stem>-<stamp>.md` and
  re-points `<stem>-latest.md`. So "regenerate the matrix" is a re-run of 01, not
  new code.
- **`explain_n(conn, sql, params, analyze=False)` already exists** in
  `src/api_trace.py`. Dropping ANALYZE is what makes the write path safe to plan:
  a plain `EXPLAIN` produces a plan and **does not execute the statement**.

---

## 1. The deliverable

`reports/doc-api-index-matrix-<stamp>.md` (+ `-latest`), containing:

1. **The measured volume** (`count(*)` per table) and **both index states read from
   live `pg_indexes`**. Every plan in the report is relative to these two facts.
2. **The headline table — 44 rows, one per API:** does any statement it issues
   perform a sequential scan; on which relations; which indexes are used. Both
   index states, side by side.
3. **Per-shape detail — 27 rows:** relation, scan node type, index name or none,
   in both states. APIs cross-reference into this table rather than repeating it,
   because the shapes are shared and repeating them would imply 513 independent
   measurements where there are 27.
4. **A note the three INSERT shapes get to themselves.** `INSERT … VALUES (?,…)`
   plans to a `Result` node. It has no scan, so there is no index to detect. An
   index's cost to an INSERT is *maintenance on write*, not a lookup — printing
   "no index used" on those rows would read as a finding when it is a category
   error.
5. **What this does not establish**, stated plainly: no latency, no throughput,
   nothing about concurrency or contention. Plan shape at *this* volume with
   *these* parameters, and nothing further.
6. `verify_api_index_matrix.py`, re-deriving every figure in the report from the
   run JSON. This pattern caught two reporting bugs last session; the report is
   not done until its verifier is green.

---

## 2. Phases

### Phase 0 — dump the database first (Kade)

Per your instruction, and it is the right call: even though plain EXPLAIN does not
execute, the write sweep is the first time this audit has pointed EXPLAIN at
INSERT/UPDATE/DELETE at all, and a restore point costs minutes.

```bash
kubectl exec -n <ns> postgresql-1 -- \
    pg_dump -U polaris -Fc -d polaris -f /tmp/polaris-preexplain-<stamp>.dump
# copy it off the pod
```

Two conditions before Phase 4 proceeds:

- **The restore command is written down before the sweep, not after.**
- **The dump is proven restorable** — restore it into a throwaway database and
  count one table. A dump nobody has restored is a belief, not a backup. This
  repo has already lost a clean 9,000-request pass to a capture nobody checked
  and 178 MB of capture to a rotate that was a restart; the same discipline
  applies here.

`postgresql-1` is the primary, not `-0` — earlier manual resets hit a read-only
replica.

### Phase 1 — seed (Kade)

**Resolved 2026-08-31: no real Iceberg tables.** The goal is SQL inspection, so
the fixture exists to supply *volume*, not API targets. Coverage comes from
somewhere else entirely — notebook 01 creates and tears down its **own** probe
catalog (`apiprofile<ts>_cat`, `probe_ns`, `probe_tbl`, `probe_tbl2`,
`probe_view`) and drives all 44 APIs against those. So `--tables` (10,000 Iceberg
tables, slow) buys nothing this task needs.

```bash
python3 seed_polaris.py --users 1000 \
    --views-per-namespace 5 \
    --generic-tables-per-namespace 5 \
    --policies-per-namespace 2
#   no --tables; --grants-per-role stays at the default 50
```

### Why those numbers — each one is picked to make a table's shapes readable

The 27 shapes are not evenly spread. 18 of them hit `entities`, and a fixture
that leaves `entities` thin makes two thirds of the report unreadable for the
reason in §3.

| table | shapes | rows at this fixture | comment |
|---|---:|---:|---|
| `entities` | 18 | **~30,000** | 1,000 × (principal + principal_role + catalog + catalog_role + 2 ns) ≈ 6,000, **plus** 2 ns × 5 views × 1,000 = 10,000 and the same again in generic tables |
| `grant_records` | 4 | **~52,000** | 52/principal at the default 50 grants/role — already far past the ~3–5K crossover measured 2026-08-22 |
| `policy_mapping_record` | 2 | ~4,000 | **only if policies actually seed — see the warning below** |
| `principal_authentication_data` | 3 | **1,000** | 1:1 with principals and cannot be grown independently |

Without the views and generic tables, `entities` lands near ~6,000 — inside the
band where `entities_pkey` / `idx_entities` can cover a query by accident of
width, which is precisely the 02c failure in §3. 5 and 5 per namespace is the
cheapest lever that pushes it clear.

**`principal_authentication_data` stays small by construction.** It holds one row
per principal, so at 1,000 principals it is 1,000 rows and no fixture choice
changes that. Its 3 shapes must be reported as *volume-limited*: a trivial plan
there is a statement about a 1,000-row table, not about Polaris.

**Policies are a known unknown — probe before trusting the number.** Policies are
feature-flagged in 1.3, and this repo has already seen them seed as **zero** while
`GET /policies` answered 200 (feature on, payload wrong). Run
`seed_polaris.py --probe-policy` first to find the `type` string this build
accepts. If policies cannot be seeded, `policy_mapping_record` stays empty and its
2 shapes must be reported as **not measurable at this fixture** — never as a plan,
because every plan against an empty table looks the same and means nothing.

Other traps, unchanged:

- **A short ledger silently writes nothing.** `seed()` skips every user in
  `Ledger.done_users`, and the ledger records only *that* a user was built, never
  how many grants it got. `refuse_on_short_ledger()` guards the known case; a
  fresh `--prefix` avoids the question entirely.
- **The seeder discards credentials.** Seeded client_ids exist only in
  `principal_authentication_data`.
- **Record the measured volume**, `count(*)` per table, not the projected one —
  and take it *after* Phase 2, since 01 leaks 4 entities per run.

### Phase 2 — regenerate the matrix at the seeded volume (Kade)

**Resolved: yes — but archive the current matrix first, and the archive has to be
a TRACKED file.**

`reports/.gitignore` is `*.md` with `!doc-*-latest.md`, so **only
`doc-api-sql-matrix-latest.md` is tracked**. The timestamped twin
`doc-api-sql-matrix-20260820-172931.md` is byte-identical (same md5) but
**gitignored**, so it would not survive a clean checkout. Notebook 01 overwrites
`-latest` in place. Git history would still hold the old blob, but recovering the
pre-reseed matrix would mean knowing to go looking for it in a past revision —
and the two matrices are worth sitting side by side, since the whole point of
regenerating is that the volume and parameters differ.

So, before running 01:

```bash
cd diagnostics/api-sql-profile/reports
# un-ignore the pinned baseline, then force-add it
printf '!doc-api-sql-matrix-20260820-172931.md\n' >> .gitignore
git add -f doc-api-sql-matrix-20260820-172931.md .gitignore
```

Commit that as its own change *before* 01 runs. Then the 2026-08-20 root-driven
matrix is pinned in the tree under its own timestamp, and `-latest` is free to be
overwritten.

Re-run `01_api_access_map.ipynb`. It refreshes
`reports/doc-api-sql-matrix-latest.md` with the same 44 APIs, now with **live
parameters**.

**Why this is not optional busywork.** Today's `-latest` was generated
2026-08-20 against ~7K entities, and its params reference entity IDs that the
realm no longer contains. PostgreSQL uses parameter *values* for selectivity
estimation: a parameter matching zero rows estimates one row and can be planned
with an index scan that the real value would never get. Sweeping the stale
params would produce a plan shape that is a fiction — precisely the class of
error `--index-state` was built to prevent, arriving through the other door.

**And 01's op list must be widened before it is re-run**, or the regenerated
matrix reproduces the same 19-of-29 read coverage. The 10 missing operations are
listed in §0; `api_sweep.full_read_operations` already names them. Without this
the sweep cannot claim to cover all API requests — it would cover all the API
requests *one notebook happens to drive*, which is the circularity
`probe_api_surface.py` was written to break.

Two known costs, both recorded:

- **01 drives as root**, the least representative identity in the realm — root's
  authorization resolves 2 grant rows where a seeded principal resolves 50. That
  affects the *grantee lookup's* selectivity specifically. Flag it in the report;
  the seeded-identity numbers for the read surface already exist in the six
  banked captures if a contrast is wanted.
- **01 leaks exactly 4 entities per run** (open issue, `find_probe_leak.py` still
  unrun). Harmless to plan shape; it moves `count(*)` by 4, so take the volume
  reading *after* this phase, not before.

**Fallback if you would rather not re-run 01:** keep the existing matrix and
re-parameterize the 27 shapes from the live metastore instead. That is more code
and more judgement calls than re-running the notebook, and it is the option I'd
take only if 01 turns out to be broken.

### Phase 3 — build the sweep (Claude, offline — no cluster needed)

Extend what exists; do not rewrite it. Four gaps, all small:

| # | gap | fix |
|---|---|---|
| 1 | `_summarise_plan` returns **one** chosen scan node (it was built to answer a question about `grant_records` alone). Per-API detection needs every scan in the plan. | add `scans: [{relation, node_type, index_name}]` alongside the existing chosen-node fields — additive, existing callers unaffected |
| 2 | Nothing reads the matrix doc's fenced SQL+params blocks. `query_profile.parse_api_matrix` reads only the API/method/path headings. | new `parse_api_statements(text)` → `(api, idx, table, verb, sql, params)` |
| 3 | `explain_statements` hardcodes `analyze=True`. | thread `analyze=False` — this is what makes writes safe and removes timing from the deliverable entirely |
| 4 | The report renderer is Seq-vs-Index / `grant_records` shaped. | new renderer for the API × shape × index-state matrix |

New runner: `explain_api_matrix.py --matrix <doc> --index-state {present|absent}`,
writing `runs/apiexplain-<stamp>.json`.

**All of this is built and unit-tested against the six banked captures and the
existing matrix doc before it ever touches the cluster.** Mocked tests, in the
existing suites. Nothing in Phase 3 needs Postgres.

### Phase 4 — the sweep (Kade runs it; two passes)

```bash
python3 explain_api_matrix.py --matrix reports/doc-api-sql-matrix-latest.md \
    --index-state present          # current state first

python3 drop_grantee_index.py
#   on the PRIMARY: ANALYZE polaris_schema.grant_records;

python3 explain_api_matrix.py --matrix reports/doc-api-sql-matrix-latest.md \
    --index-state absent

#   restore:
#   CREATE INDEX CONCURRENTLY idx_grant_records_grantee
#       ON polaris_schema.grant_records (realm_id, grantee_catalog_id, grantee_id);
#   ANALYZE polaris_schema.grant_records;
```

- **`--index-state` is required and checked against live `pg_indexes`.** EXPLAIN
  replays against the database as it *is*, not as the matrix was captured. Last
  session this check was one command away from stapling Index Scan plans onto a
  Seq Scan drive.
- **`ANALYZE` after every toggle is not optional.** A planner working from stale
  `reltuples` chooses a path for a table size that no longer exists.
- **Writes are plain EXPLAIN, never ANALYZE.** The Phase 0 dump is the belt to
  that braces.

### Phase 5 — the report + verifier (Claude)

As specified in §1. Then `black` (last) / `isort` / `pytest`, `MEMORY.md` *Now*,
`.memory/roadmap.md`, `.memory/sessions/`, and one commit — automatic, per
CLAUDE.md.

---

## 3. The trap that most threatens this specific task

**Index detection is volume-dependent, and a plan shape is not a verdict on a
schema.** The 02c smoke run is the precedent: at 3,064 `grant_records` the
primary key *covered* the grantee query, every cell planned an Index-Only-Scan,
and the Seq Scan the whole audit was about never appeared — the index toggle was
a no-op and the run looked clean.

So the report must say, in its own voice:

- a **Seq Scan at low volume is not evidence of a missing index** — the planner
  is choosing correctly for the table it has;
- an **Index Scan at low volume is not evidence of a good one** — the PK may be
  covering the query by accident of width;
- and every row is therefore stamped with the volume it was measured at.

This is why the 1,000-principal seed is load-bearing rather than incidental.
`grant_records` at ~60K sits well past the ~3–5K crossover measured on
2026-08-22; `entities` at the seeded shape is where the 18 `entities` shapes
become worth reading at all.

---

## 4. Division of labour

Measured today: the VM Claude's shell runs in has **no `kubectl`, no `psql` and no
route to the cluster**. PyPI *is* reachable, so tests and formatters run there.

| phase | who |
|---|---|
| 0 dump + prove the restore | Kade |
| 1 seed | Kade |
| 2 regenerate the matrix | Kade |
| 3 build + unit-test the sweep | **Claude** — offline, can start immediately |
| 4 run the two EXPLAIN passes | Kade |
| 5 report, verifier, tests, commit | **Claude** |

Phase 3 does not depend on Phases 0–2. If you sign off, Claude can build and test
the tooling against the banked captures while you seed.

---

## 5. Definition of done

- A proven-restorable dump, taken before any write EXPLAIN, with its restore
  command recorded.
- Measured volume per table, at the seeded shape.
- `runs/apiexplain-<stamp>.json` × 2, each recording the live `pg_indexes` state
  it was taken in.
- All **44+ APIs** covered — including the 10 read operations absent from
  today's matrix — and all **115 (SQL, params) pairs** either planned or
  explicitly accounted for (the INSERT pairs are accounted for, not planned).
- A coverage section stating what the surface is *known* to be versus what was
  swept, with `driven_unverified` at zero for reads and the write surface
  labelled a lower bound.
- `reports/doc-api-index-matrix-<stamp>.md` + `-latest`, every figure re-derived
  green by its verifier, volume stamped on every row, no timing anywhere.
- `black` (last) and `isort` clean, `pytest` green.
- `MEMORY.md` *Now* + `.memory/` updated; one commit, subject stating the finding.

---

## 6. Sign-off — resolved 2026-08-31

1. **Real Iceberg tables?** No. SQL inspection only; the fixture supplies volume
   and notebook 01's own probe entities supply API coverage. `--tables` dropped.
2. **N per namespace?** Chosen here rather than asked back: **5 views, 5 generic
   tables, 2 policies**, reasoned per table in Phase 1. Change any of them and the
   only thing that moves is how readable that table's shapes are.
3. **Regenerate the matrix?** Yes — with the pinned archive committed first, per
   Phase 2.

**Still needs Kade before Phase 4:** a proven-restorable dump (Phase 0), and the
`--probe-policy` result, which decides whether `policy_mapping_record`'s 2 shapes
are measurable at all.
