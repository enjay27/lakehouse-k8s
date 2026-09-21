# Plan — SEEDING: bring the fixture to production grant volume

Phase A of `PLAN-grant-scale-sweep.md`, replanned. **Supersedes that document's
Phase A entirely** — its premise turned out to be false (see §1). Phases B and C
of it are unaffected.

Status: **awaiting sign-off.** Nothing built. Per `CLAUDE.md` Strict Plan-First
Mode, no module, notebook or config has been touched.

Goal: take each `owner_principal` catalog-role from **25 grants to 50**, additively
and resumably, so `grant_records` goes ~30,009 → ~55,009 and the scaling sweep has
a production-shaped starting point.

---

## 0. The flow this fits into (settled 2026-08-21)

Sweep notebook name: **`02b_grant_scale_sweep.ipynb`**, leaving
`03_read_cache_profile.ipynb` free. 03 is downstream of 02b's result.

| # | step | logging | index | writes |
|---|---|---|---|---|
| 1 | **SEED** — this plan, `--upgrade-grants` | OFF, capture stopped | present (irrelevant) | `grant_records` 30,009 → ~55,009 |
| 2 | **Re-run 01** — access map at production volume | Polaris DEBUG **ON** | **dropped** | probe fixture only |
| 3 | **Run 02b** — the scaling sweep | **OFF** | dropped + rebuilt per grid cell | filler rows, per cell |
| 4 | 03 — read-cache profile | two-pass, its own design | required present | its own fixtures |

Three things this ordering settles, each of which would otherwise be discovered
the hard way:

**The plain 02 re-run comes off the critical path.** `HANDOFF.md` open item 2 says
re-run 02 before 03, to give 03 a manifest matching the cluster. But 02b writes its
own `runs/<run_id>.json` — `load_run` takes the newest by default and
`require_live_match` re-checks it against the live database — so **02b becomes the
manifest producer for 03**, and a 02 re-run in between would be invalidated by step
3 anyway. Two conditions: 02b's manifest must carry the same core keys 03 checks
(index state, table counts) alongside its grid extension, and 02b must **end with
the index present and valid** and assert that before writing.

**The index gets dropped before step 2, not kept.** It is our patch, absent from
upstream `schema-v3.sql` at the 1.3.0 tag — where `grant_records` is declared with a
composite PK and no `CREATE INDEX` at all. The access map exists to answer "which
indexes are missing in Polaris as shipped", so it is captured against stock
behaviour: `check_hypotheses` then returns **CONFIRMED at production volume** rather
than REMEDIED against our own remedy. 02b rebuilds it per cell and leaves it in
place for 03. Cost is negligible — it built in 0.1 s at 30,009 rows.

**Logging flips twice, and the capture must be rotated at each flip.** Step 1 runs
with the capture stopped (26,000 PUTs at DEBUG would produce a large log for no
value and could clobber another). Step 2 needs Polaris DEBUG **on** — 01 is the
standing exception to the logging-off rule because it measures shape and
attribution, not latency. Step 3 needs everything **off**; statement logging on gave
a 4.6x spread on an identical plan. Use `./capture.sh rotate <newdir>` between
steps: a plain restart truncates in place, which is how the 178 MB seeded capture
was lost. The existing 30,009-row reports become the **before** baseline — they are
already timestamped, and `run_id` is the join key between a report and its manifest,
so only `-latest` moves.

**A trap if 02b is copied from 02:** 02's section-5 guard refuses to run when the
index already exists, so that a second run cannot measure a "before" that already
has it. 02b drops and rebuilds per cell by design, so it needs the guard *per cell*
(assert absent immediately before each before-measurement), not once at the top —
inherited unchanged, that guard makes 02b unrunnable from the current state.

---

## 1. The correction that changed this plan

`PLAN-grant-scale-sweep.md` §"Two corrections" states:

> **Polaris has only 25 catalog-scoped privileges.** `FULL_CATALOG_PRIVILEGES` is
> already the complete set... "50 privileges on one catalog role" is therefore only
> reachable across **multiple securables**.

**That is wrong.** `CatalogPrivilege` in `spec/polaris-management-service.yml` at tag
`apache-polaris-1.3.0-incubating` carries ~51 values, not 25. The repo's
`FULL_CATALOG_PRIVILEGES` stops exactly at `VIEW_FULL_METADATA` — the end of the
*pre-policy* enum. Everything after it is missing:

| missing group | names |
|---|---|
| policy | `POLICY_CREATE`, `POLICY_WRITE`, `POLICY_READ`, `POLICY_DROP`, `POLICY_LIST`, `POLICY_FULL_METADATA`, `CATALOG_ATTACH_POLICY`, `CATALOG_DETACH_POLICY` |
| fine-grained table | `TABLE_ASSIGN_UUID`, `TABLE_UPGRADE_FORMAT_VERSION`, `TABLE_ADD_SCHEMA`, `TABLE_SET_CURRENT_SCHEMA`, `TABLE_ADD_PARTITION_SPEC`, `TABLE_ADD_SORT_ORDER`, `TABLE_SET_DEFAULT_SORT_ORDER`, `TABLE_ADD_SNAPSHOT`, `TABLE_SET_SNAPSHOT_REF`, `TABLE_REMOVE_SNAPSHOTS`, `TABLE_REMOVE_SNAPSHOT_REF`, `TABLE_SET_LOCATION`, `TABLE_SET_PROPERTIES`, `TABLE_REMOVE_PROPERTIES`, `TABLE_SET_STATISTICS`, `TABLE_REMOVE_STATISTICS`, `TABLE_REMOVE_PARTITION_SPECS`, `TABLE_MANAGE_STRUCTURE` |

The existing 25 are exactly the first 25 of the spec's own order, so the upgrade to
50 is **purely additive** — no existing grant is disturbed.

Consequence, and the decision taken (2026-08-21): **catalog scope only, 50 names.**
Securable-scoped grants are no longer needed to reach 50, so `polaris_rest.
grant_privilege` is left alone and the `skip_if_present`-must-compare-the-securable
bug that would have "silently halved the fixture" cannot occur. What is lost is
securable diversity — all 50 rows of a role point at the same catalog. That does
**not** affect what the sweep measures: the grantee lookup constrains
`(realm_id, grantee_catalog_id, grantee_id)` and never touches the securable
columns, so grantee row counts are identical either way.

**One caveat, and it is why P3 below exists.** The enum above is read from the spec,
not from the running server. `POLICY_*` may be gated behind the policy feature flag,
and the tail names may post-date this build. The deployed build is the authority,
so the list is *measured* before it is trusted.

---

## 2. Pre-flight gates — in this order, before any bulk write

**P0. Stop or rotate the capture.** `capture-seeded/polaris.log` is 71 MB and the
178 MB seeded capture was already lost once to a run that restarted a capture in
place. 26,000 calls with Polaris DEBUG on will produce a large log and could
clobber another. `./capture.sh rotate <newdir>` or stop it. Confirm PostgreSQL
statement logging stays **off**.

**P1. The notebook-01 entity leak** (HANDOFF open item 1). Decision: fix it first,
but **defer the 02 re-run**. `find_probe_leak.py` is read-only and cheap:

```bash
uv run python diagnostics/api-sql-profile/find_probe_leak.py
```

Read its output before touching teardown — if the survivors are soft-deleted
(`drop_timestamp` set, `purge_timestamp` null) this is a purge question with a
completely different fix. Then add the count-based assertion so teardown cannot
print `no residue` over a leak.

This gate is now **load-bearing rather than tidy-up**: step 2 of the flow re-runs
01, so an unfixed leak adds another 4 entities immediately before 02b takes its
baseline. It does not corrupt the grant measurements — the leak is in `entities`,
which 02b does not measure — but it does break `require_live_match(tolerance=0)`
for anything downstream. **Do not re-run 02:** 02b supersedes it as the manifest
producer (§0), and a fresh 02 manifest would be invalidated by the seed anyway.

**P2. Verify the existing fixture is complete.** `python3 seed_polaris.py --verify`.
A half-created catalog (entity present, no `catalog_admin`) cannot take grants —
25 of 1,000 landed that way last time. Every gap must be filled before the upgrade,
or the pass fails 25 users and the counts come out short.

**P3. Measure the privilege enum against the deployed build.** Create one throwaway
catalog + catalog-role, attempt a grant of every candidate name, record which are
accepted, tear it down. `SeedResult.invalid_privileges` already collects rejections,
so this is the existing machinery pointed at one catalog. **The measured list is
what becomes the constant** — not the spec transcription in §1.

**P4. Baseline accounting, so the after-count is checkable.** One query set,
recorded in the plan's output:

- `SELECT count(*) FROM polaris_schema.grant_records` → expect 30,009.
- Grants per grantee (`GROUP BY grantee_catalog_id, grantee_id`) → the *before*
  distribution: 4,002 grantees, min 1, p50 1, p95 25, max 1,006. **Predicted
  after:** 4,002 grantees unchanged, min 1, **p50 1** (still — the 2,000 principals
  and principal-roles each hold exactly their one role assignment, which is the
  point the sweep plan corrects), **p95 25 → 50**, max 1,006 unchanged (the upgrade
  touches only `owner_principal` roles, not `service_admin`). State this before
  running it, so the after-measurement can disagree.
- The non-privilege overhead. 30,009 − 25,000 = 5,009 decomposes exactly as
  **5 per user + 9 realm-level**. The 5 are believed to be the two role
  assignments plus three `catalog_admin` bootstrap grants — **believed, not
  measured.** Confirm it with a `GROUP BY privilege_code` on one user's ids before
  it goes into `expected_counts()`, or we encode a guess.
- `pg_relation_size` of `grant_records`, its PK, and `idx_grant_records_grantee` —
  the index growth is part of the cost being proposed upstream.

**P5. The Phase B FK gate, taken early because it costs a second.** Confirm
`grant_records` carries no foreign key to `entities`:

```sql
SELECT conname, contype, confrelid::regclass
FROM pg_constraint
WHERE conrelid = 'polaris_schema.grant_records'::regclass;
```

Polaris emits no JOINs anywhere, but that is an inference from query shape. If a FK
exists, Phase B's filler-row design is dead and the sweep ceiling drops to ~110k
REST-created rows — better to know now than after Phase A.

---

## 3. What gets built

### 3.1 `src/polaris_seed.py`

**Constants.** Add `CATALOG_PRIVILEGES` — the full ordered 1.3.0 list, docstringed
with its source (the spec tag) and the fact that P3's measurement overrides it.
Rename `FULL_CATALOG_PRIVILEGES` → `CORE_CATALOG_PRIVILEGES` (the pre-policy 25,
which is what the current fixture holds), keeping `FULL_CATALOG_PRIVILEGES` as an
alias so the recorded ledger spec and any existing caller still resolve. The old
name is actively misleading now and should not survive as the primary.

**`upgrade_grants(pc, spec, ledger_path, ...)`** — additive, resumable, local-only.
Per user:

1. one `list_grants(catalog, "owner_principal")` GET → the set already held;
2. diff against the target list;
3. PUT only what is missing, with **`skip_if_present=False`**, wrapped in
   `call_with_lag_retry`;
4. mark the user in the ledger.

This is the plan's stated optimisation, done in the safe direction. The sweep plan
proposed turning `skip_if_present` off wholesale to save ~25,000 wasted GETs —
correct about the cost, but that also removes the idempotence a resumable pass
depends on. One GET **per role** instead of one per privilege saves 24,000 round
trips *and* keeps the diff exact, so a re-run after an interrupt issues zero writes
instead of 25,000 duplicate-key retries at ~5 s each.

Rejected privilege names go to `invalid_privileges` and do not abort the run — same
contract as `seed()`.

**`revert_grants(...)`** — the mirror, revoking everything above the 25-name
baseline, so the sweep has a real restore step rather than an optional one.

**`SeedSpec`** — no new field. `privileges` stays the single source of truth and
`expected_counts()` already reads `len(self.privileges)`; the CLI sets
`privileges = CATALOG_PRIVILEGES[:50]`. Adding a `grants_per_role` field alongside
`privileges` would create two sources of truth for the same number.

**`expected_counts()` / `verify_counts()`** — model the overhead measured in P4
explicitly (`n * len(privileges) + 5 * n + 9`) and stop printing *"Row counts match
the spec"* off a `>=` comparison (HANDOFF open item 5). Report the surplus as a
number with its explanation, or say it is unexplained. This is the last chance to
fix it before these counts go upstream.

**`Ledger`** — a `grant_upgrades` key (`{"target": 50, "users": [...]}`), flushed
per user like `users`. Also make `Ledger.spec()` tolerant of unknown keys: it does
`SeedSpec(**d)` today, so a ledger written by a newer version raises `TypeError` on
an older one.

### 3.2 `src/polaris_rest.py`

**`revoke_privilege(catalog, catalog_role, privilege, cascade=False, token=None)`.**
Note the shape, which is not the obvious one and is confirmed against the 1.3.0
spec: revocation is **`POST`** to the same `.../grants` URL — not `DELETE` — with
the same `{"grant": {...}}` body and an optional `?cascade=` query parameter.
Returns the response; the caller decides what a 404 means, consistent with the rest
of the module.

`grant_privilege` is **not** touched. Its two measured PG-HA fixes stay verbatim.

### 3.3 `diagnostics/api-sql-profile/seed_polaris.py`

New flags on the existing CLI, for the same reason the seed lives here rather than
in a notebook — a 20-minute run should survive a closed laptop:

```
--upgrade-grants [--grants-per-role 50]   # the additive pass
--revert-grants                           # back to the 25-name baseline
--probe-privileges                        # P3, on one throwaway catalog-role
--dry-run                                 # print the per-user diff, write nothing
```

`--dry-run` on the real cluster is the gate before the bulk run: it proves
`list_grants` returns what the diff logic expects, against live data, at a cost of
one GET.

---

## 4. Test matrix (mocked; no cluster required)

`test_polaris_rest.py` (+4):

1. `revoke_privilege` POSTs to the grants URL with the catalog grant body.
2. `cascade` rides as a query parameter and defaults to false.
3. per-call token override is honoured.
4. a non-2xx is returned, not raised.

`test_polaris_seed.py` (+8), extending `FakePolaris` with grant state:

5. `CATALOG_PRIVILEGES[:25]` equals `CORE_CATALOG_PRIVILEGES` as a set — this is
   what makes the upgrade provably additive; if it ever fails, the upgrade is
   rewriting the existing fixture rather than extending it.
6. a role holding 25 of 50 gets exactly 25 PUTs and exactly one GET.
7. idempotent: an already-upgraded role gets zero PUTs.
8. resumable: users recorded in `grant_upgrades` are skipped on re-run.
9. a rejected privilege name is recorded and the run continues.
10. `upgrade_grants` refuses a non-local host, guard **before** argument validation
    (the ordering fixed in `seed()` this month).
11. `expected_counts()` arithmetic including the P4 overhead term.
12. `revert_grants` revokes exactly the privileges above the baseline and nothing
    else.

---

## 5. Cost, risk, rollback

| | |
|---|---|
| calls | 1,000 GET + ~25,000 PUT ≈ 26,000 |
| wall clock | ~15–25 min at the rates the 1,000-user seed measured |
| writes | `grant_records` only — no `entities`, no MinIO objects |
| after | `grant_records` ~55,009; `entities` unchanged |
| rollback | `--revert-grants`, or `DELETE FROM grant_records WHERE privilege_code IN (...)` as the blunt instrument |

Risks specific to this pass:

- **Lag is a smaller threat here than during the seed.** A grant PUT is a single
  INSERT against a catalog-role that has existed for a day — there is no
  read-after-write prerequisite. `call_with_lag_retry` still wraps it, but 61%-of-
  namespace-creates behaviour is not expected. If it appears anyway, that is a
  finding worth recording.
- **`ANALYZE grant_records` immediately after.** +25,000 rows on stale `reltuples`
  makes the planner choose from data that no longer exists, which would look
  exactly like a result. Record `reltuples` and exact `count(*)` after.
- **The index gets bigger.** `idx_grant_records_grantee` was 2,000 kB against a
  2,744 kB PK. Re-measure both; the ratio is part of the upstream argument.
- **The 188x measurement now describes a fixture that no longer exists.** Every
  report quoting it must say which fixture it was taken on. The sweep's whole point
  is that the number is a point on a surface — but until the sweep runs, the old
  number and the new fixture must not be quoted in the same breath.

---

## 6. Definition of done

1. `pytest` green (131 existing + 12 new).
2. `isort . && black .` — **black last**, until `[tool.isort] profile = "black"` is
   set (HANDOFF open item 4).
3. `--dry-run` clean against the live cluster before the bulk run; `--verify`
   clean after it.
4. P4's counts re-taken after the pass and compared to the projection, with the
   surplus explained rather than tolerated.
5. `MEMORY.md`, `README.md` Result section, and **`PLAN-grant-scale-sweep.md`**
   updated — that document's Phase A and its "only 25 privileges" correction are
   themselves now wrong, and leaving them is exactly the failure mode this repo
   keeps catching. Record the settled name (`02b_grant_scale_sweep.ipynb`) and the
   flow in §0 there too, since its "Open naming decision" section is now closed.
6. The measured privilege list from P3 recorded in the module docstring, with the
   spec transcription marked as its source rather than its authority.

---

## 7. Still open

Both of the previous open items are now settled — the notebook is
`02b_grant_scale_sweep.ipynb` and 03 consumes its result (§0). What remains:

- **What state 03 inherits.** 02b's grid inserts filler rows up to ~500,000. Filler
  is inert for authorization but entirely real to a Seq Scan, so it *would* move
  03's latency numbers, and every one of them would then need the synthetic-rows
  caveat attached. Recommendation: **restore before 03** — delete filler, `ANALYZE`,
  leave the index present — so 03 measures a coherent, wholly REST-created realm at
  55,009 rows. Decide when 02b is planned, not when it finishes.
- **03's design predates the 50-grant fixture.** Its protocol in `MEMORY.md` (R=5,
  N=20, a distinct seeded user unit per round/op) was written against 25 grants per
  role. Nothing about it obviously breaks at 50, but it should be re-read against
  the new shape rather than assumed to carry over.
