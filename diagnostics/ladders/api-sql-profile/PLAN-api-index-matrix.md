# PLAN — EXPLAIN every API in the report, under three identities

Proposed 2026-08-31. **Plan-first: nothing is built or run until Kade signs off.**
Third revision; supersedes the single-identity draft.

---

## 1. The task

For every API defined in `reports/doc-api-sql-matrix-latest.md`, EXPLAIN every SQL
statement that API issues, and record **whether an index is used** — presence,
not performance.

Driven under **three identity cases**, each from a cold Polaris:

| case | identity | grant rows its lookup resolves | expected outcome |
|---|---|---:|---|
| **admin** | seeded `admin{N}`, holds `service_admin` | **~1,100** | reads + writes 2xx |
| **authorized** | seeded `authz{N}`, catalog-scoped | **52** | 21 of 29 reads 2xx; mgmt writes 403 |
| **unauthorized** | new principal, **zero grants** | **0** | every call 403 |

### Why the identity axis is the point

The same SQL text plans differently depending on how many rows its parameter
matches. The grantee lookup is the case in point — one statement, four different
selectivities (root 2, unauthorized 0, authorized 52, admin ~1,100). **Sweeping
one identity's parameters and calling the result "the plan for this API" would be
a statement about that identity, not about the API.** Three cases spanning the
authorization outcomes is what makes the answer general, and it is why "admin" is
a seeded `service_admin` principal rather than root: root resolves 2 grant rows
and is the least representative identity in the realm.

The unauthorized case is not a null result. Measured last session: **a 403 pays
the FULL authorization prelude** — same statement shapes, including 1.00
`grant_records` grantee lookup, before the authorization decision is made. So the
denial path issues real queries with a zero-row parameter, and that is exactly the
selectivity extreme nothing has measured.

### Scope boundary

The report defines the API list, and the deliverable must say so in its own voice.
Out of scope, by decision: the 10 read APIs the harness drives but this report
does not contain (`/applicable-policies`, `/policies`, `/policies/{p}`,
`/generic-tables`, `/generic-tables/{gt}`,
`/catalog-roles/{r}/principal-roles`, `/catalogs/{c}/catalog-roles/{r}`,
`/principal-roles/{n}/catalog-roles/{c}`, `/principals/{p}/principal-roles`,
`/namespaces/{ns}/tables/{t}/credentials`); whether the write surface is complete
(unknowable — a call log proves what was called and nothing about what was not,
and Polaris serves no OpenAPI document); and latency.

---

## 2. What the report contains — measured, not assumed

| | count |
|---|---:|
| `###` headings | 44 |
| real APIs (`preflight` dropped) | **43** |
| statement instances | **505** |
| distinct SQL texts | 27 |
| distinct (SQL, params) pairs, **root only** | 115 |

Statements per API: min 6, median 11, max 24 (`mgmt.grant_privilege`). No API has
zero statements. The 27 texts: 19 SELECT, 4 DELETE, 3 INSERT, 1 UPDATE; by table
`entities` 18, `grant_records` 4, `principal_authentication_data` 3,
`policy_mapping_record` 2.

**115 is the single-identity figure.** Under three identities the sweep unit
becomes each case's own (SQL, params) pairs: admin ≈ 115 (full surface),
authorized fewer (reads + catalog-scoped writes only), unauthorized small (the
prelude, repeated). Estimate **~250 pairs → ~500 plain EXPLAINs across two index
states.** Still minutes. The drives and restarts are the expensive part now, not
the EXPLAINs.

`doc-api-sql-matrix-latest.md` carries **full untruncated SQL and bound params**
for every statement — verified. (The top-level `doc-api-sql-matrix.md` is a
different, older render: SQL truncated at ~150 chars, and it logs Pgpool-II
health-check traffic as though Polaris issued it. Do not use it.)

---

## 3. THE BLOCKER — 01 is root-hardcoded and builds its own fixtures

Notebook 01 creates a probe catalog, namespace, tables and views; drives the 43
APIs; tears down. **Two of the three identities cannot run that flow at all:**

- the **unauthorized** principal 403s on the setup itself;
- the **authorized** catalog-scoped principal cannot create catalogs — 1.3.0 has
  no service-level grant type, so catalog creation needs `service_admin`.

So "run 01 three times" is not achievable as written. **Setup and driving must be
separated:** fixtures are created ONCE as admin, and each identity then drives
against fixtures that already exist. This is what `privilege_scan.drive()` +
`resolve_entities` already do for the read surface; the work is extending the same
idea to 01's write statements.

Per case, what is actually driveable:

| case | reads | writes |
|---|---|---|
| admin | all | all — **the only case that yields write statements** |
| authorized | 21 of 29 2xx, rest 403 | catalog-scoped writes in its own catalog; mgmt writes 403 |
| unauthorized | all 403 | all 403 |

**A 403 is data, not a gap.** Each refusal still issues the prelude, and its
statements go in the matrix under that case with the 403 recorded. What must NOT
happen is a case quietly reporting fewer APIs because its refusals were dropped —
`privilege_scan` already has the `malformed` vs `refused` distinction for exactly
this (a `GET /v1/config` 400 for a missing parameter was once filed as `refused`,
which read as a claim about Polaris).

---

## 4. Phases

### Phase 0 — dump, and prove the dump restores (Kade)

```bash
kubectl exec -n <ns> postgresql-1 -- \
    pg_dump -U polaris -Fc -d polaris -f /tmp/polaris-preexplain-<stamp>.dump
```

Restore command written down **before** the sweep. Dump **proven restorable** into
a throwaway database — a dump nobody has restored is a belief, not a backup.
`postgresql-1` is the primary, not `-0`.

### Phase 1 — fixtures (Kade)

```bash
python3 seed_polaris.py --probe-policy            # FIRST — policies are feature-flagged
python3 seed_polaris.py --users 1000 --views-per-namespace 5 \
    --generic-tables-per-namespace 5 --policies-per-namespace 2
python3 seed_polaris.py --users 5 --prefix admin --service-admin
#   plus ONE principal with zero grants — the unauthorized case
```

Sized so each table's statements are readable rather than trivial:

| table | texts | rows | note |
|---|---:|---:|---|
| `entities` | 18 | ~30,000 | 1,000 identities ≈ 6,000, plus 10,000 views + 10,000 generic tables |
| `grant_records` | 4 | ~52,000 | far past the ~3–5K crossover measured 2026-08-22 |
| `policy_mapping_record` | 2 | ~4,000 | **only if policies seed** |
| `principal_authentication_data` | 3 | **1,000** | 1:1 with principals; **volume-limited by construction** — a trivial plan there is a statement about a 1,000-row table, not about Polaris |

Without views and generic tables `entities` lands near 6,000 — inside the band
where `entities_pkey`/`idx_entities` can cover a query by accident of width (§6).

**The zero-grant principal must be verified to hold nothing** beyond its own
principal-role chain — count its `grant_records` rows before using it. A principal
accidentally holding grants would make the unauthorized case a second copy of the
authorized one, and the two would look consistent.

**Policies are a known unknown.** Feature-flagged in 1.3; this repo has seen them
seed as **zero** while `GET /policies` answered 200. If they cannot be seeded,
`policy_mapping_record`'s 2 texts are reported **not measurable at this fixture**
— never as a plan, since every plan against an empty table looks the same.

### Phase 2 — archive the current report as a TRACKED file (Kade)

`reports/.gitignore` is `*.md` with `!doc-*-latest.md`, so **only
`doc-api-sql-matrix-latest.md` is tracked**. Its timestamped twin
`doc-api-sql-matrix-20260820-172931.md` is byte-identical (same md5) but
gitignored, and 01 overwrites `-latest` in place.

```bash
cd reports
printf '!doc-api-sql-matrix-20260820-172931.md\n' >> .gitignore
git add -f doc-api-sql-matrix-20260820-172931.md .gitignore
# commit on its own, BEFORE any drive
```

### Phase 3 — make the drive identity-aware (Claude, offline) — **NOW ON THE CRITICAL PATH**

This used to be parallel work. It is not: Phase 4's drives cannot run until it
exists. Five pieces, all additive:

| # | gap | fix |
|---|---|---|
| 1 | 01 is root-hardcoded | accept an identity (client_id/secret from `principal_authentication_data`, as `privilege_scan.load_identities` already does); **setup stays as admin, driving uses the target identity** |
| 2 | 01 tears down its own fixtures | make setup/teardown separable so three cases share one fixture set |
| 3 | `_summarise_plan` returns ONE chosen scan node (built for `grant_records` alone) | add `scans: [{relation, node_type, index_name}]` — additive |
| 4 | nothing reads the report's fenced SQL+params blocks | `parse_api_statements(text)` → `(api, idx, table, verb, sql, params)`, keyed to the **(sql, params) pair** |
| 5 | `explain_statements` hardcodes `analyze=True` | thread `analyze=False` — makes writes safe to plan and removes timing |

Plus the runner `explain_api_matrix.py --matrix <doc> --case {admin,authorized,unauthorized} --index-state {present|absent}` → `runs/apiexplain-<case>-<stamp>.json`.

Built and unit-tested against the existing report and the six banked captures
before it touches the cluster. Nothing here needs Postgres.

### Phase 4 — three drives, each from a cold Polaris (Kade)

**Per case, in this order.** The restart is what makes the three comparable.

```bash
# 1. restart Polaris — cold InMemoryEntityCache
kubectl rollout restart deploy/<polaris> -n <ns>
#    WAIT for .status.observedGeneration to catch the patch, THEN rollout status.
#    `rollout restart` only patches the template, so `rollout status` immediately
#    after can report the PREVIOUS rollout complete. Then wait until 8181
#    answers a token — NOT 8182 /q/health/ready. reset_realm.sh's token gate is
#    the pattern; reuse it rather than reinventing it.

# 2. statement logging ON, into a fresh capture dir
./capture.sh pgon
./capture.sh rotate capture-<case>-<stamp>
#    `rotate` is do_stop; do_start and does NOT touch log_statement. `pgon` is
#    separate. That mistake cost a clean 9,000-request pass on 2026-08-24.

# 3. drive the 43 APIs as this identity
# 4. VERIFY the capture is live before trusting the pass
python3 scan_privileges.py --capture capture-<case>-<stamp>
#    One capture in this repo's history held 410 bytes and one line,
#    "Apache Polaris Server stopped", after a clean 9,000-request pass.
```

Then regenerate the per-case matrix and take each statement's SQL + params.

### Phase 5 — EXPLAIN each case with its own parameters (Kade)

Each case's pairs, both index states, one index toggle between the halves:

```bash
for case in admin authorized unauthorized; do
  python3 explain_api_matrix.py --case $case --index-state present
done
python3 drop_grantee_index.py
#   on the PRIMARY: ANALYZE polaris_schema.grant_records;
for case in admin authorized unauthorized; do
  python3 explain_api_matrix.py --case $case --index-state absent
done
#   restore: CREATE INDEX CONCURRENTLY idx_grant_records_grantee
#            ON polaris_schema.grant_records (realm_id, grantee_catalog_id, grantee_id);
#            ANALYZE polaris_schema.grant_records;
```

- **`--index-state` is required and checked against live `pg_indexes`.** EXPLAIN
  replays against the database as it *is*; last session this check was one command
  away from stapling Index Scan plans onto a Seq Scan drive.
- **`ANALYZE` after every toggle** — a planner on stale `reltuples` picks a path
  for a table size that no longer exists.
- **Writes: plain EXPLAIN, never ANALYZE.** It does not execute. Phase 0's dump is
  the belt to those braces.
- **A case's parameters are never used for another case's EXPLAIN.** That
  substitution would silently undo the entire experiment.

### Phase 6 — report + verifier (Claude)

`reports/doc-api-index-matrix-<stamp>.md`:

1. Scope statement; measured volume per table; both index states from live
   `pg_indexes`; the three identities and their measured grant footprints.
2. **Headline: 43 APIs × 3 identities × 2 index states** — does any statement
   sequentially scan; which relations; which indexes.
3. **Per-pair detail**, grouped by case. Every statement instance maps to a pair.
4. **The grantee lookup across four selectivities** (0 / 52 / ~1,100, plus root
   from the archived matrix) — one statement, and the clearest thing this design
   produces.
5. **The 3 INSERT texts get their own note:** `INSERT … VALUES` plans to a
   `Result` node. No scan, so no index to detect — an index's cost to an INSERT is
   maintenance on write, not a lookup. "No index used" there would read as a
   finding when it is a category error.
6. **Cold-cache and custom-plan caveats** (§6).
7. What this does not establish.
8. `verify_api_index_matrix.py` re-deriving every figure. Not done until green.

---

## 5. Division of labour

Claude's shell has **no `kubectl`, no `psql`, no route to the cluster** (measured
2026-08-31). PyPI *is* reachable, so tests and formatters run there.

| phase | who |
|---|---|
| 0 dump + prove restore | Kade |
| 1 seed + zero-grant principal | Kade |
| 2 archive-commit | Kade |
| **3 identity-aware drive + sweep tooling** | **Claude — blocks Phase 4** |
| 4 three cold drives | Kade |
| 5 EXPLAIN, per case, both states | Kade |
| 6 report + verifier | Claude |

---

## 6. What the restarts mean for the result — must be in the report

**A cold cache yields the MAXIMAL statement set.** Every API issues its cold-path
queries, so the capture shows every query an API *can* issue. Good for coverage —
and it means the report describes cold-cache behaviour; a warm Polaris issues
fewer. This is not hypothetical: last session measured 122,010 vs 109,010
statements between two passes and could not attribute the difference, with entity-
cache warmth the leading unproven explanation. **Restarting before every case is
what makes the three cases comparable to each other**, and it removes that
confound from this task rather than inheriting it.

**A restart also resets pgjdbc.** PostgreSQL promotes a server-side prepared
statement to a **generic plan after five executions** (`prepareThreshold=5`). From
cold, the plans captured are **custom plans**, which use the actual parameter
values for selectivity — exactly what a per-identity comparison needs, and the
reason this design works at all. But a long-running Polaris will eventually plan
the hot statements generically, and a generic plan does not vary with the
identity. The report must say the plans are custom-plan plans.

**Index detection is volume-dependent.** The 02c precedent: at 3,064
`grant_records` the primary key *covered* the grantee query, every cell planned an
Index-Only-Scan, and the Seq Scan the audit existed for never appeared. So a Seq
Scan at low volume is not evidence of a missing index, an Index Scan at low volume
is not evidence of a good one, and every row is stamped with its volume.

---

## 7. Definition of done

- Proven-restorable dump; restore command recorded.
- Three identities with **measured** grant footprints — including the
  zero-grant principal verified to hold zero.
- Three captures, each **verified live**, each taken from a restarted Polaris.
- `runs/apiexplain-<case>-<stamp>.json` × 3 × 2 index states, each recording the
  live `pg_indexes` state it was taken in.
- **All 43 APIs covered in every case**, with 403s recorded as outcomes rather
  than dropped. Every statement instance maps to a planned pair, zero unmapped.
- INSERT pairs accounted for, not planned; `policy_mapping_record` pairs planned
  or explicitly not-measurable.
- Report + verifier green; volume on every row; no timing anywhere.
- `black` (last), `isort`, `pytest` green; `MEMORY.md` *Now* + `.memory/`; one
  commit, automatic.
