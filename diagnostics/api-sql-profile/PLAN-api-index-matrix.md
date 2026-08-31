# PLAN — EXPLAIN every API defined in `doc-api-sql-matrix-latest.md`

Proposed 2026-08-31. **Plan-first: nothing is built or run until Kade signs off.**
Supersedes the earlier draft of this file, which had the sweep unit wrong.

---

## 1. The task, and its boundary

**For every API defined in `reports/doc-api-sql-matrix-latest.md`, EXPLAIN every
SQL statement that API issues, and record whether an index is used.** Presence,
not performance. No timings anywhere in the deliverable.

**The report defines the scope.** That is a deliberate boundary, not an
oversight, and the deliverable must say so in its own voice — otherwise a reader
six months out takes it for a statement about Polaris rather than about this
document. Explicitly OUT of scope:

- **The 10 read APIs the harness drives but this report does not contain**
  (`/applicable-policies`, `/policies`, `/policies/{p}`, `/generic-tables`,
  `/generic-tables/{gt}`, `/catalog-roles/{r}/principal-roles`,
  `/catalogs/{c}/catalog-roles/{r}`, `/principal-roles/{n}/catalog-roles/{c}`,
  `/principals/{p}/principal-roles`,
  `/namespaces/{ns}/tables/{t}/credentials`). Measured with
  `coverage_from_evidence`; recorded here so the gap is a decision on the record.
- **Whether the report's write surface is complete.** A call log proves what was
  called and says nothing about what was not, and Polaris serves no OpenAPI
  document to check against. Unknowable from here.
- **Latency, throughput, concurrency.** Not measured, not implied.

---

## 2. What the report contains — measured 2026-08-31, not assumed

| | count |
|---|---:|
| `###` headings | 44 |
| real APIs (`preflight` excluded) | **43** |
| base APIs (2 `load_table` variants folded) | 41 |
| statement instances across the 43 | **505** |
| distinct SQL texts | 27 |
| **distinct (SQL, params) pairs — the sweep unit** | **115** |

Statements per API: min 6, median 11, max 24 (`mgmt.grant_privilege`).
**No API has zero statements**, so all 43 are coverable.

**Why 115 and not 27.** 20 of the 27 SQL texts carry more than one parameter set
— one carries 13. PostgreSQL estimates selectivity from parameter *values*, so
the same SQL can plan as a Seq Scan with one parameter and an Index Scan with
another. Sweeping 27 would answer "each distinct SQL text once, with an arbitrary
parameter", and the 88 missing plans would not show anywhere in the report. The
unit is the pair.

The 27 texts by verb: 19 SELECT, 4 DELETE, 3 INSERT, 1 UPDATE.
By table: `entities` 18, `grant_records` 4, `principal_authentication_data` 3,
`policy_mapping_record` 2.

**So the measurement is 115 × 2 index states = 230 plain EXPLAINs.** Minutes. The
seed is the expensive phase; the thing being asked for is nearly free once the
fixture exists.

Two properties of the source that make this tractable at all, both verified:
`reports/doc-api-sql-matrix-latest.md` carries **full untruncated SQL** in fenced
blocks **and** the bound `params:` line for every statement. (The top-level
`doc-api-sql-matrix.md` is a different, older render — SQL truncated at ~150
chars, and it logs Pgpool-II health-check traffic as though Polaris issued it.
Do not use it.)

---

## 3. The deliverable

`reports/doc-api-index-matrix-<stamp>.md` (+ `-latest`):

1. **Scope statement, first.** 43 APIs as defined by
   `doc-api-sql-matrix-latest.md`; what is out of scope, per §1; the measured
   volume per table; both index states read from live `pg_indexes`.
2. **Headline table — 43 rows, one per API.** Does any statement it issues
   perform a sequential scan; on which relations; which indexes are used. Both
   index states side by side.
3. **Per-statement detail — 115 rows.** Relation, scan node type, index name or
   none, both states. Each of the 505 instances maps to one of these, and each
   API section cross-references into it rather than repeating plans — repeating
   them would imply 505 independent measurements where there are 115.
4. **A note the 3 INSERT texts get to themselves.** `INSERT … VALUES (?,…)` plans
   to a `Result` node. There is no scan, so there is no index to detect. An
   index's cost to an INSERT is *maintenance on write*, not a lookup — printing
   "no index used" would read as a finding when it is a category error.
5. **What this does not establish**, verbatim from §1.
6. `verify_api_index_matrix.py`, re-deriving every figure from the run JSON. The
   report is not done until its verifier is green — this pattern caught two
   reporting bugs last session.

---

## 4. Phases

### Phase 0 — dump the database, and prove the dump restores (Kade)

Per Kade's instruction. Plain EXPLAIN does not execute, but this is the first
time this audit points EXPLAIN at INSERT/UPDATE/DELETE at all, and a restore
point costs minutes.

```bash
kubectl exec -n <ns> postgresql-1 -- \
    pg_dump -U polaris -Fc -d polaris -f /tmp/polaris-preexplain-<stamp>.dump
# copy it off the pod
```

Two conditions before Phase 4 runs:

- **The restore command is written down before the sweep, not after.**
- **The dump is proven restorable** — restore into a throwaway database and count
  one table. A dump nobody has restored is a belief, not a backup. This repo has
  already lost a clean 9,000-request pass to a capture nobody checked, and 178 MB
  of capture to a `rotate` that was a restart.

`postgresql-1` is the primary, not `-0`.

### Phase 1 — seed for volume (Kade)

The fixture supplies **volume**, not API targets: notebook 01 creates and tears
down its own probe catalog (`apiprofile<ts>_cat`, `probe_ns`, `probe_tbl`,
`probe_tbl2`, `probe_view`) and drives the 43 APIs against those. So no real
Iceberg tables are needed.

```bash
python3 seed_polaris.py --probe-policy          # FIRST -- see the warning below
python3 seed_polaris.py --users 1000 \
    --views-per-namespace 5 \
    --generic-tables-per-namespace 5 \
    --policies-per-namespace 2
#   no --tables; --grants-per-role stays at the default 50
```

Sized per table, because the 27 texts are lopsided and a thin fixture makes two
thirds of the report unreadable for the reason in §5:

| table | texts | rows at this fixture | note |
|---|---:|---:|---|
| `entities` | 18 | **~30,000** | 1,000 × (principal + principal_role + catalog + catalog_role + 2 ns) ≈ 6,000, plus 10,000 views and 10,000 generic tables |
| `grant_records` | 4 | **~52,000** | 52/principal at 50 grants/role — far past the ~3–5K crossover measured 2026-08-22 |
| `policy_mapping_record` | 2 | ~4,000 | **only if policies seed — see below** |
| `principal_authentication_data` | 3 | **1,000** | 1:1 with principals; cannot be grown independently |

Without views and generic tables, `entities` lands near 6,000 — inside the band
where `entities_pkey`/`idx_entities` can cover a query by accident of width,
which is the 02c failure in §5. 5 and 5 per namespace is the cheapest lever clear
of it.

**`principal_authentication_data` is 1,000 rows by construction.** Its 3 texts
must be reported as *volume-limited*: a trivial plan there is a statement about a
1,000-row table, not about Polaris.

**Policies are a known unknown.** Feature-flagged in 1.3, and this repo has seen
them seed as **zero** while `GET /policies` answered 200 (feature on, payload
wrong). `--probe-policy` finds the `type` string this build accepts. If policies
cannot be seeded, `policy_mapping_record` stays empty and its 2 texts are reported
**not measurable at this fixture** — never as a plan, because every plan against
an empty table looks the same and means nothing.

Also: a short ledger silently writes nothing (`seed()` skips `Ledger.done_users`,
which records only *that* a user was built) — `refuse_on_short_ledger()` guards
the known case, a fresh `--prefix` avoids the question. And the seeder discards
credentials; seeded client_ids exist only in `principal_authentication_data`.

### Phase 2 — archive the current report, then regenerate it (Kade)

**Archive first, and the archive must be a TRACKED file.** `reports/.gitignore`
is `*.md` with `!doc-*-latest.md`, so **only `doc-api-sql-matrix-latest.md` is
tracked**. Its timestamped twin `doc-api-sql-matrix-20260820-172931.md` is
byte-identical (verified, same md5) but **gitignored**, so it would not survive a
clean checkout — and notebook 01 overwrites `-latest` in place.

```bash
cd reports
printf '!doc-api-sql-matrix-20260820-172931.md\n' >> .gitignore
git add -f doc-api-sql-matrix-20260820-172931.md .gitignore
# commit this on its own, BEFORE 01 runs
```

**Then re-run `01_api_access_map.ipynb`**, which refreshes `-latest` with the
same 43 APIs at the seeded volume, with **live parameters**.

Why regeneration is not optional busywork: today's params were captured
2026-08-20 against ~7K entities and reference entity IDs the realm no longer
holds. PostgreSQL estimates selectivity from parameter values — a parameter
matching zero rows estimates one row and can be planned with an index scan the
real value would never get. Sweeping stale params produces a plan shape that is a
fiction.

Two known costs, recorded: **01 drives as root**, whose authorization resolves 2
grant rows where a seeded principal resolves 50 (this affects the grantee lookup's
selectivity specifically — flag it in the report); and **01 leaks exactly 4
entities per run** (open issue), so take the volume reading *after* this phase.

01's operation list is **not** widened — the 10 absent read APIs are out of scope
per §1.

### Phase 3 — build the sweep (Claude, offline, no cluster)

Extend what exists; four gaps, all small and additive:

| # | gap | fix |
|---|---|---|
| 1 | `_summarise_plan` returns **one** chosen scan node (built to answer a question about `grant_records` alone) | add `scans: [{relation, node_type, index_name}]` — additive, existing callers unaffected |
| 2 | nothing reads the report's fenced SQL+params blocks (`parse_api_matrix` reads only the API/method/path headings) | new `parse_api_statements(text)` → `(api, idx, table, verb, sql, params)`, keyed to the **(sql, params) pair** |
| 3 | `explain_statements` hardcodes `analyze=True` | thread `analyze=False` — makes writes safe and removes timing from the deliverable |
| 4 | the report renderer is Seq-vs-Index / `grant_records` shaped | new renderer for the API × pair × index-state matrix |

New runner `explain_api_matrix.py --matrix <doc> --index-state {present|absent}`,
writing `runs/apiexplain-<stamp>.json`.

**All of it is built and unit-tested against the existing report and the six
banked captures before it touches the cluster.** Mocked tests in the existing
suites. Nothing here needs Postgres, and nothing here depends on Phases 0–2 — it
can proceed in parallel with the seed.

### Phase 4 — the sweep (Kade; two passes)

```bash
python3 explain_api_matrix.py --matrix reports/doc-api-sql-matrix-latest.md \
    --index-state present

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
  replays against the database as it *is*. Last session this check was one
  command away from stapling Index Scan plans onto a Seq Scan drive.
- **`ANALYZE` after every toggle.** A planner on stale `reltuples` chooses a path
  for a table size that no longer exists.
- **Writes are plain EXPLAIN, never ANALYZE.** Phase 0's dump is the belt to that
  braces.

### Phase 5 — report + verifier (Claude)

Per §3. Then `black` (last), `isort`, `pytest`; `MEMORY.md` *Now*,
`.memory/roadmap.md`, `.memory/sessions/`; one commit, automatic.

---

## 5. The trap that most threatens this task

**Index detection is volume-dependent, and a plan shape is not a verdict on a
schema.** The 02c smoke run is the precedent: at 3,064 `grant_records` the primary
key *covered* the grantee query, every cell planned an Index-Only-Scan, and the
Seq Scan the audit existed for never appeared — the index toggle was a no-op and
the run looked clean.

So the report must say, in its own voice:

- a **Seq Scan at low volume is not evidence of a missing index** — the planner is
  choosing correctly for the table it has;
- an **Index Scan at low volume is not evidence of a good one** — the PK may be
  covering the query by accident of width;
- every row is stamped with the volume it was measured at.

This is why Phase 1 is load-bearing rather than incidental.

Two smaller ones, carried from the last session: **a capture's name is not its
content** (resolve by content), and **errors that net out survive
reconciliation** (read per-row composition, never the summary line).

---

## 6. Division of labour

The VM Claude's shell runs in has **no `kubectl`, no `psql`, no route to the
cluster** (measured 2026-08-31). PyPI *is* reachable, so tests and formatters run
there.

| phase | who |
|---|---|
| 0 dump + prove the restore | Kade |
| 1 `--probe-policy`, then seed | Kade |
| 2 archive-commit, then re-run 01 | Kade |
| 3 build + unit-test the sweep | **Claude** — offline, can start now |
| 4 the two EXPLAIN passes | Kade |
| 5 report, verifier, tests, commit | **Claude** |

---

## 7. Definition of done

- A proven-restorable dump, taken before any write EXPLAIN, restore command
  recorded.
- Measured volume per table, taken after Phase 2.
- `runs/apiexplain-<stamp>.json` × 2, each recording the live `pg_indexes` state
  it was taken in.
- **All 43 APIs covered. All 115 (SQL, params) pairs either planned or explicitly
  accounted for** — the INSERT pairs are accounted for, not planned; the
  `policy_mapping_record` pairs may be not-measurable, and say so.
- Every one of the 505 statement instances maps to a planned pair, with zero
  unmapped.
- `reports/doc-api-index-matrix-<stamp>.md` + `-latest`: scope statement first,
  volume stamped on every row, no timing anywhere, verifier green.
- `black` (last) and `isort` clean, `pytest` green.
- `MEMORY.md` *Now* + `.memory/` updated; one commit, subject stating the finding.
