# HANDOFF — current state, read this first

Latest handoff for `diagnostics/api-sql-profile/`. Written 2026-08-21 so a fresh
session can resume without replaying the history.

Historical, still accurate for their own stages:
- `HANDOFF-phase1.md` — stage 1, the API → SQL access map (notebook 01)
- `HANDOFF-02.md` — stage 2, index remediation measured (notebook 02)
- `HANDOFF-20260820.md` — the correctness pass over the toolchain and the reports

This one covers the seeding work: a retracted premise, Phase A built, and a flow
settled end to end.

## The flow, settled

| # | step | logging | index | writes |
|---|---|---|---|---|
| 1 | **SEED to 50 grants/role** — built, not yet run live | OFF, capture stopped | present, irrelevant | `grant_records` 30,009 → 55,009 |
| 2 | **re-run 01** — access map at production volume | Polaris DEBUG **ON** | **dropped** | probe fixture only |
| 3 | **run 02b** — `02b_grant_scale_sweep.ipynb`, not built | **OFF** | dropped + rebuilt per grid cell | filler rows per cell |
| 4 | 03 — read-cache profile | two-pass, its own design | required present | its own fixtures |

Three consequences worth not rediscovering:

- **The plain 02 re-run is off the critical path.** 02b writes its own
  `runs/<run_id>.json`; `load_run` takes the newest and `require_live_match`
  re-checks it live, so **02b is the manifest producer for 03**. A 02 manifest made
  between steps 1 and 3 would be invalidated by step 3 anyway. Conditions: 02b's
  manifest must carry the core keys 03 checks (index state, table counts), and 02b
  must end with the index present and valid, asserted before writing.
- **The index is dropped before step 2, not kept.** It is our patch, not Polaris's
  (confirmed below), so an access map captured with it present documents a patched
  box. Absent, `check_hypotheses` returns CONFIRMED at production volume rather
  than REMEDIED against our own remedy.
- **Rotate the capture at every logging flip.** A plain restart truncates in place —
  that is how the 178 MB seeded capture was lost. The existing 30,009-row reports
  become the *before* baseline; they are already timestamped and `run_id` joins a
  report to its manifest, so only `-latest` moves.

**Trap for whoever builds 02b:** 02's section-5 guard refuses to run when the index
exists, so a second run cannot measure a contaminated "before". 02b drops and
rebuilds per cell by design, so it needs that guard **per cell**, not once at the
top — inherited unchanged it makes 02b unrunnable from the current state.

## Cluster state right now

- `idx_grant_records_grantee` is **PRESENT and VALID**. Step 2 drops it; step 3
  rebuilds it per cell and must leave it present for 03.
- **It is ours, not Polaris's.** Upstream `schema-v3.sql` at tag
  `apache-polaris-1.3.0-incubating` declares `grant_records` with a composite PK and
  no index at all — the file's only `CREATE INDEX`es are `idx_entities`,
  `idx_locations` and `idx_policy_mapping_record`, all on other tables. Upgrading
  Polaris does not supply it. `drop_grantee_index.py` removes it.
- Newest manifest: `runs/20260820-170924.json` — `entities 7277`,
  `grant_records 30009`. **Stale**, and step 1 will move `grant_records` anyway.
- Statement logging is OFF (`pg-*.log` near-empty). Correct for timing; step 2 needs
  Polaris DEBUG back on.
- `capture-seeded/polaris.log` is 71 MB and is the latest 01 run only.

## What changed this session

**A retraction that removed a whole planned phase.** `PLAN-grant-scale-sweep.md`
Phase A rested on "Polaris has only 25 catalog-scoped privileges, so 50 is only
reachable across multiple securables." False. `CatalogPrivilege` at the 1.3.0 tag
carries ~51 values; `FULL_CATALOG_PRIVILEGES` stopped at `VIEW_FULL_METADATA`,
exactly where the enum ended before the policy API landed, missing 8
`POLICY_*`/`CATALOG_*_POLICY` names and 18 fine-grained `TABLE_*` names. 50 grants
per role is reachable at catalog scope alone, so the securable-scoped client work —
and the `skip_if_present` bug that would have "silently halved the fixture" — is
not needed at all. That document is corrected in place; `PLAN-seeding-production-shape.md`
supersedes its Phase A.

**Phase A built** (`PLAN-seeding-production-shape.md`), 233 tests green, `black`
clean:

- `polaris_seed.CATALOG_PRIVILEGES` — the real enum in spec order.
  `catalog_privileges(n)` slices it, so every larger n is a superset of every
  smaller one and the upgrade is provably additive (there is a test pinning that).
  `FULL_CATALOG_PRIVILEGES` → `CORE_CATALOG_PRIVILEGES`, alias kept because existing
  ledgers record the old name under `spec.privileges`.
- `upgrade_grants()` — additive, resumable, local-only. **One `list_grants` GET per
  role**, diff, then PUT only what is missing with `skip_if_present=False`. The plan
  proposed turning `skip_if_present` off wholesale: right about the 24,000 wasted
  GETs, wrong about the consequence, since that also removes the idempotence a
  resumable pass depends on. Diffing per role gets both. Simulated at full scale:
  **1,000 GETs + 25,000 PUTs, 30,009 → 55,009 rows.**
- It distinguishes a **rejected privilege name** (4xx that is not 403/404 — data,
  recorded, pass continues) from an **exhausted retry** (5xx/403/404 — a hole in the
  fixture, so the role is *not* marked done and a re-run retries it). Recording both
  as "invalid privilege" would leave that hole permanently.
- A **changed target invalidates the ledger record**: resuming a 50-grant pass from
  a 40-grant ledger must not skip roles that are ten short.
- `revert_grants()` + `polaris_rest.revoke_privilege()` — the restore path. Revoke is
  **POST** to the grants URL with `?cascade=`, not DELETE, which returns 405.
- `probe_privileges()` / `--probe-privileges` — the spec is the source, the deployed
  build is the authority. `POLICY_*` may be feature-gated.
- `expected_counts()` now projects `grant_records` as granted + Polaris-written
  (`n*len(privileges)` + `5n + 9`, which reproduces the measured 30,009 exactly), and
  `verify_counts` **names an unexplained residual** instead of printing "Row counts
  match the spec" off a `>=` comparison. That closes an open item, but the 5-per-user
  constant is OBSERVED, not derived — see item 3 below.
- `Ledger.spec()` drops unknown keys rather than raising `TypeError` inside
  `teardown()`, which is the worst moment to discover a forward-compatibility
  problem: the ledger is the only record of what needs deleting.

## Open items, most important first

**1. Notebook 01 still leaks exactly 4 entities per run**, and step 2 re-runs 01, so
fix it before then. Measured across five runs: 7273 → 7277 → 7281 → 7285 → 7289,
perfectly linear, on runs with no 5xx too. Teardown prints `no residue` because it
verifies its probe catalog is gone, not that the count returned to baseline. It
corrupts no grant numbers — the leak is in `entities`, which 02b does not measure —
but it breaks `require_live_match(tolerance=0)` for everything downstream.

Diagnostic, read-only, **still not run**:
```bash
uv run python diagnostics/api-sql-profile/find_probe_leak.py
```
It shows whether the survivors are **soft-deleted** (`drop_timestamp` set,
`purge_timestamp` null) — those still count in `count(*)`, which makes this a purge
question with a completely different fix. Do not patch the teardown before reading
that output. Then add a count-based assertion so teardown cannot claim `no residue`
over a leak.

**2. Run the seeding pass.** Nothing has touched the live cluster yet. In order:

```bash
python3 seed_polaris.py --probe-privileges          # does this build accept all 51?
python3 seed_polaris.py --verify                    # is the 1,000-user fixture whole?
python3 seed_polaris.py --upgrade-grants --dry-run  # the per-role diff
python3 seed_polaris.py --upgrade-grants            # ~26,000 calls, ~15-25 min
# then: ANALYZE grant_records
python3 seed_polaris.py --verify --grants-per-role 50
```

Stop or rotate the capture first (`./capture.sh rotate <newdir>`). Take the P4
baseline in `PLAN-seeding-production-shape.md` §2 before and after — grantee
distribution, `reltuples` vs exact `count(*)`, and the sizes of `grant_records`, its
PK and the index. **Predicted after:** 4,002 grantees, p50 **1** (unchanged), p95
25 → **50**, max 1,006 unchanged, 55,009 rows.

**3. The 5-per-user grant overhead is observed, not measured.** 30,009 − 25,000 =
5,009 decomposes exactly as 5 per user + 9 realm-level, and the 5 are *believed* to
be two role assignments plus three `catalog_admin` bootstrap grants. Confirm with a
`GROUP BY privilege_code` on one user's ids. The projection now depends on it, and
`verify_counts` will report any error as an unexplained residual rather than
absorbing it — which is the point, but the constant should still be right.

**4. `grant_records` FK gate, for Phase B.** Confirm no foreign key to `entities`
against `pg_constraint` before any filler insert. Polaris emits no JOINs, but that
is an inference from query shape. One second to check, and a hidden FK kills the
filler design.

**5. `black` and `isort` still disagree.** No `[tool.isort] profile = "black"` in
`pyproject.toml` (verified — there is no `[tool.black]` or `[tool.isort]` section at
all). Run **black last**. Note `test_iceberg_rest.py` is currently **black-dirty in
the repo** from exactly this churn — pre-existing, not from this session's work, and
`black .` will reformat it the next time anyone runs the DoD.

**6. Carried over, unchanged:** the `check_hypotheses` note wording for
`entities_row_constructor_in`; four write statements remain `NO_PARAMS` and
unmeasured; `rbac/lib/` re-dirties itself on every pyvis run (gitignore it).

## Rules worth not relearning

1. **Classify on the WHERE clause**, never the projection or the whole statement.
   Three separate classifiers here have been confidently wrong this way.
2. **Render the evidence.** Both `check_hypotheses` bugs were invisible until the
   report printed the SQL each verdict came from.
3. **Turn statement logging off before timing** — a 4.6x spread on an identical plan.
   01 is exempt: it measures shape, not latency, and needs DEBUG on.
4. **Restart the kernel after any `src/` edit.**
5. **EXPLAIN on the PRIMARY** — `/*NO LOAD BALANCE*/`, `pg_is_in_recovery()` False.
6. **Never let your own remedy read as a refutation.** See REMEDIED.
7. **A constant transcribed from a spec is a hypothesis.** The 25-privilege belief
   survived months and drove a planned phase because nobody asked the server.
