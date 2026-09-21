# Privilege Tests

## Concept
A measured **authorization truth table** for Apache Polaris 1.3.0: for each namespace/table/view mutation, what is the *minimum fine-grained privilege* actually required — verified empirically rather than inferred from the documented privilege hierarchy.

## Purpose
Replace assumptions about the privilege tree with facts. The harness scaffolds with a full-privilege master identity, then challenges each action with a single-privilege **worker principal**, classifying every response through a six-way outcome taxonomy instead of a fragile "403 = blocked / 2xx = allowed" binary.

## Notebooks
- `polaris_privilege_matrix_test.ipynb` — builds the **minimum-privilege matrix** (which single fine-grained privilege each action requires) using `case_scaffold` + `worker_principal` from `../src/polaris_test_utils.py`.
- `polaris_privilege_hierarchy_test.ipynb` — verifies the **privilege hierarchy** (doc §1): the coarse-master → fine-grained *cascade* (`CATALOG_MANAGE_CONTENT` / `CATALOG_MANAGE_METADATA`) and *securable inheritance* (a catalog-scoped grant reaching nested entities). Grants only the master to a worker and checks every action in/out of branch, rendering a cascade truth table that confirms or refutes each claimed edge.
- `polaris_use_case_roles_test.ipynb` — validates the four **real-world role profiles** (doc §3): Data Engineer, BI Analyst, Auditor, Tenant Admin. Provisions each as a multi-privilege worker and asserts both sides of its boundary (capabilities → `AUTHORIZED`, restrictions → `BLOCKED_PRIV`), plus a cross-catalog isolation test for the Tenant Admin. Footprint privilege names are treated as hypotheses — any the build rejects surface as `GRANT_INVALID`.

All three share the same six-way taxonomy and single-use-worker lifecycle; root only bootstraps and tears down. They bootstrap with `init_env("local")` + `require_not_prod(...)`, so they refuse to run against company PROD.

### Case structure (`run_case`)

The hierarchy and role notebooks are built on a four-part **arrange / act / assert / cleanup** contract in `src/polaris_test_utils.py`, composed by `run_case(name, suite_fn, execute_fn, result_fn)`:

- **Suite** — `build_suite(...)` (common): fresh catalog → scaffold prereqs with a full-privilege scaff principal (then destroyed for isolation) → provision a worker holding exactly the footprint. It **records every entity it creates** into an `Entities` ledger.
- **Execute** — per-cell: fires the action under test as the worker; returns the response.
- **Result** — `classify(...)` (pure): derives the six-way outcome; changes no state.
- **Cleaner** — `clean(*entities)` (common): deletes the *recorded* entities (principals/roles first, then catalogs via recursive purge) in a `finally`, so cleanup is guaranteed and no case can leak into another.

A case with non-standard setup (e.g. the cross-catalog isolation test) supplies its own `suite_fn` but reuses the same orchestrator, so its resources are still reclaimed. Each notebook also ends with a belt-and-suspenders sweep for any stragglers.

## How to run
1. Confirm services are reachable per the active env config (`../src/config/local.yaml`; switch `init_env("dev")` for the shared cluster).
2. **Restart & Run All**. The first cell bootstraps `../src` and imports the utils.
3. Review the emitted tables: in the matrix, `GRANT_INVALID` rows reveal privilege names this build rejects; in the hierarchy notebook, ❗ cells flag edges that refute the doc's cascade claim; in the roles notebook, each role gets a PASS/FAIL card with its allow/deny assertions.

## Measured findings (Polaris 1.3.0, 2026-07-02)

Full results in **`doc-privilege-results.md`**. Headlines:

- **Reading a single view needs `VIEW_READ_PROPERTIES`, not `VIEW_LIST`** — `VIEW_LIST` returns `403` on `GET /views/{view}` (it only authorizes *listing*). This is the one BI-Analyst boundary miss.
- **`CATALOG_MANAGE_METADATA` is NOT read-only** on this build — it authorizes CREATE/DROP/COMMIT on namespaces/tables/views, same as `CATALOG_MANAGE_CONTENT`. Both coarse masters authorize all 11 actions. An Auditor role built on CMM therefore gets full read-write, not read-only (4/10).
- **All 16 privilege names are accepted** at grant time — zero `GRANT_INVALID` (earlier "may be rejected" hypotheses were wrong).
- **Confirmed:** minimal granular privilege per action (+ necessity 11/11), securable inheritance (catalog → nested entity), per-catalog isolation (cross-catalog drop → `403`), Data Engineer 8/8, Tenant Admin 7/7.

### Harness gotchas (still controlled for)
- **Config gate contaminates DROP tests** — DROP catalogs set `drop-with-purge.enabled=true` first, or a correctly-privileged drop is mis-recorded as blocked.
- **A 403 may come from OPA, not Polaris** — workers use role-scoped tokens (`scope=PRINCIPAL_ROLE:{role}`) and 403s are classified by error body.
- **Read-after-write lag** — grant `404`s and read `404`s are retried/settled (not recorded as authz results); `LAG_500`s likewise.

## Reference docs
- `doc-privilege-results.md` — **measured results (source of truth)**: truth table, cascade, role verdicts, refutations.
- `doc-privilege-matrix-plan.md` — the test plan and the six-way outcome taxonomy.
- `doc-privilege-test.md` — the original privilege tree (§1), minimal-privilege matrix (§2), and role profiles (§3) — **hypotheses**, since partly refuted by the measured results (see the callouts in that file).
