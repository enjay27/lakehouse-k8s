# Privilege Tests

## Concept
A measured **authorization truth table** for Apache Polaris 1.3.0: for each namespace/table/view mutation, what is the *minimum fine-grained privilege* actually required — verified empirically rather than inferred from the documented privilege hierarchy.

## Purpose
Replace assumptions about the privilege tree with facts. The harness scaffolds with a full-privilege master identity, then challenges each action with a single-privilege **worker principal**, classifying every response through a six-way outcome taxonomy instead of a fragile "403 = blocked / 2xx = allowed" binary.

## Notebooks
- `polaris_privilege_matrix_test.ipynb` — builds the privilege matrix using `case_scaffold` + `worker_principal` from `../src/polaris_test_utils.py`.

## How to run
1. Confirm services are reachable per `../src/config/dev.yaml`.
2. **Restart & Run All**. The first cell bootstraps `../src` and imports the utils.
3. Review the emitted matrix; `GRANT_INVALID` rows reveal which privilege names this build does **not** accept (a deliverable in itself).

## Result / findings (gotchas the harness controls for)
- **Config gate contaminates DROP tests** — neutralize `drop-with-purge.enabled=true` first, or a correctly-privileged drop is mis-recorded as blocked.
- **A 403 may come from OPA, not Polaris** — workers use role-scoped tokens (`scope=PRINCIPAL_ROLE:{role}`) and 403s are classified by error body.
- **Privilege names in the source plan are hypotheses** — only `CATALOG_MANAGE_CONTENT`, `TABLE_CREATE/LIST/DROP`, `VIEW_CREATE/LIST/DROP` are confirmed for this build.
- **Read-after-write 500s (`LAG_500`) are not authz results** — they are retried/settled, never recorded as allow/deny.

## Reference docs
- `doc-privilege-matrix-plan.md` — full test plan and the six-way outcome taxonomy.
- `doc-privilege-test.md` — supporting notes.
