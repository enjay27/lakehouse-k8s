# Privilege Tests

## Concept
A measured **authorization truth table** for Apache Polaris 1.3.0: for each namespace/table/view mutation, what is the *minimum fine-grained privilege* actually required — verified empirically rather than inferred from the documented privilege hierarchy.

## Purpose
Replace assumptions about the privilege tree with facts. The harness scaffolds with a full-privilege master identity, then challenges each action with a single-privilege **worker principal**, classifying every response through a six-way outcome taxonomy instead of a fragile "403 = blocked / 2xx = allowed" binary.

## Notebooks
- `polaris_privilege_matrix_test.ipynb` — builds the **minimum-privilege matrix** (which single fine-grained privilege each action requires) using `case_scaffold` + `worker_principal` from `../src/polaris_test_utils.py`.
- `polaris_privilege_hierarchy_test.ipynb` — verifies the **privilege hierarchy** (doc §1): the coarse-master → fine-grained *cascade* (`CATALOG_MANAGE_CONTENT` / `CATALOG_MANAGE_METADATA`) and *securable inheritance* (a catalog-scoped grant reaching nested entities). Grants only the master to a worker and checks every action in/out of branch, rendering a cascade truth table that confirms or refutes each claimed edge.
- `polaris_use_case_roles_test.ipynb` — validates the four **real-world role profiles** (doc §3): Data Engineer, BI Analyst, Auditor, Tenant Admin. Provisions each as a multi-privilege worker and asserts both sides of its boundary (capabilities → `AUTHORIZED`, restrictions → `BLOCKED_PRIV`), plus a cross-catalog isolation test for the Tenant Admin. Footprint privilege names are treated as hypotheses — any the build rejects surface as `GRANT_INVALID`.

All three share the same six-way taxonomy and the `case_scaffold` / single-use-worker lifecycle; root only bootstraps and tears down. They bootstrap with `init_env("local")` + `require_not_prod(...)`, so they refuse to run against company PROD.

## How to run
1. Confirm services are reachable per the active env config (`../src/config/local.yaml`; switch `init_env("dev")` for the shared cluster).
2. **Restart & Run All**. The first cell bootstraps `../src` and imports the utils.
3. Review the emitted tables: in the matrix, `GRANT_INVALID` rows reveal privilege names this build rejects; in the hierarchy notebook, ❗ cells flag edges that refute the doc's cascade claim; in the roles notebook, each role gets a PASS/FAIL card with its allow/deny assertions.

## Result / findings (gotchas the harness controls for)
- **Config gate contaminates DROP tests** — neutralize `drop-with-purge.enabled=true` first, or a correctly-privileged drop is mis-recorded as blocked.
- **A 403 may come from OPA, not Polaris** — workers use role-scoped tokens (`scope=PRINCIPAL_ROLE:{role}`) and 403s are classified by error body.
- **Privilege names in the source plan are hypotheses** — only `CATALOG_MANAGE_CONTENT`, `TABLE_CREATE/LIST/DROP`, `VIEW_CREATE/LIST/DROP` are confirmed for this build.
- **Read-after-write 500s (`LAG_500`) are not authz results** — they are retried/settled, never recorded as allow/deny.

## Reference docs
- `doc-privilege-matrix-plan.md` — full test plan and the six-way outcome taxonomy.
- `doc-privilege-test.md` — the privilege hierarchy tree (§1), minimal-privilege action matrix (§2), and the four real-world role profiles (§3) that the hierarchy/role notebooks verify.
