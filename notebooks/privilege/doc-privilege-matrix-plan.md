# Polaris Privilege Matrix — Test Plan (`polaris_privilege_matrix_test.ipynb`)

**Date:** 2026-06-30
**Goal:** Programmatically determine the **minimum fine-grained privilege** required for each namespace/table/view mutation under Apache Polaris 1.3.0, producing a verified authorization truth table — replacing the assumed privilege hierarchy with measured facts.
**Status:** Phase 2 of `polaris-test-refactor-plan.md`, sharpened by the "Authority" strategy document.
**Foundation:** builds on the Phase 0 scaff/worker lifecycle (`case_scaffold`, `worker_principal` in `polaris_test_utils.py`).

---

## 1. What the source strategy gets right

- The 3-stage lifecycle (master scaffolds → single-privilege worker challenges → `finally` sterilizes) is exactly the `case_scaffold` pattern already built. We reuse it directly.
- The CREATE_NAMESPACE 403 diagnosis is correct and matches the scaffolding bug already fixed: a worker holding only `[TABLE_LIST, VIEW_LIST, VIEW_CREATE]` cannot create a namespace, so scaffolding must be done by a full-privilege identity.
- Securables (namespace / table / view) and the create/list/get/drop/commit verb set are the right coverage axes.

## 2. Gaps in the source strategy (must fix, or the matrix is wrong)

These would corrupt results if the document were followed literally. Most were hit earlier this session.

1. **Config gate contaminates every DROP test.** A view/table DROP returns 403 from *either* the **config gate** (`drop-with-purge.enabled=false` → *"Unable to purge entity"*) or the **privilege gate** (*"is not authorized"*). Every DROP test must first neutralize the config gate (`drop-with-purge.enabled=true`, `purge-view-metadata-on-drop=false`) so privilege is the only thing that can gate it. Otherwise a perfectly-privileged `VIEW_DROP` is mis-recorded as "blocked."
2. **A 403 is not automatically a privilege result — OPA fronts Polaris.** An OPA/ext_authz layer returns its own 403 when a principal's role isn't activated in the token. Each worker needs a role-scoped token (`scope=PRINCIPAL_ROLE:{role}`), and the harness must classify the 403 by error body: Polaris privilege (*"is not authorized for op …"*) vs OPA (ext_authz/"OPA denied").
3. **The document's privilege names are hypotheses, not facts.** Only `CATALOG_MANAGE_CONTENT`, `TABLE_CREATE/LIST/DROP`, `VIEW_CREATE/LIST/DROP` are confirmed for this build. `NAMESPACE_CREATE/DROP/LIST`, `TABLE_READ_DATA`, `TABLE_WRITE_DATA`, `CATALOG_MANAGE_METADATA` may be rejected at grant time. Record `GRANT_INVALID` (grant PUT 400s) as a distinct outcome — discovering the real privilege vocabulary is itself a deliverable.
   > **MEASURED (2026-07-02):** all 16 names were **accepted** — zero `GRANT_INVALID`. The hypothesis that `NAMESPACE_*` / `TABLE_READ_DATA` / `TABLE_WRITE_DATA` might be rejected did not hold. Full vocabulary + minimal-privilege map in `doc-privilege-results.md` §1–§2. One correction to the plan's §5 table: **View GET's minimal privilege is `VIEW_READ_PROPERTIES`, not `VIEW_LIST`** (`VIEW_LIST` → 403 on a single-view GET).
4. **Some hierarchy claims look wrong; verify, don't encode.** The doc places `TABLE_WRITE_DATA` (snapshot/schema commits) under `CATALOG_MANAGE_METADATA` rather than a content/write master, and claims a single-view GET needs only `VIEW_LIST`. Treat the whole tree as claims the matrix confirms or refutes.
5. **Read-after-write 500s are not authz results.** Setup and challenge can both throw the documented lag-500. Setup trusts-the-commit; the challenge treats a 500-with-`metadata`/NPE as `LAG_500` (retry/settle), never authorized-or-blocked.
6. **Sufficiency without necessity is half the proof.** The doc tests only sufficiency (grant one privilege → does the action succeed). To call a privilege *minimal required*, add an optional necessity pass (grant all-but-one → action should still fail).
7. **Per-action setup differs.** Namespace-create needs only the catalog; namespace-drop needs an empty namespace; table/view drop needs the entity pre-built; list/get need something to list. Each action supplies its own `build` function to `case_scaffold`.

## 3. Central design decision: a six-way outcome taxonomy

The document's binary (403 = blocked, 2xx = authorized) is what makes it fragile. Replace it with:

```
AUTHORIZED      2xx                         → privilege sufficient
BLOCKED_PRIV    403 "is not authorized"     → privilege insufficient (clean gate)
BLOCKED_OPA     403 OPA/ext_authz body      → token/role not activated, NOT a Polaris result
BLOCKED_CONFIG  403 "Unable to purge"       → config gate leaked into a drop test (HARNESS BUG)
GRANT_INVALID   400 at grant time           → privilege name not accepted by this build
LAG_500         500 metadata/NPE            → read-after-write lag, retry (not an authz result)
```

`BLOCKED_OPA` and `BLOCKED_CONFIG` should essentially never appear in a correct run. If they do, they flag a **harness bug** (bad token scope, or un-neutralized config), not a real privilege boundary. This is the safety net the source strategy lacks.

## 4. Notebook structure

```
Cell 0  setup: reload utils, init_env (DEV banner)
Cell 1  MATRIX SPEC — list of (target, action, verb, endpoint, candidate_privs,
        coarse_overrides, build_fn). Mark each privilege confirmed/unconfirmed.
Cell 2  probe_privilege(spec, privilege):
          • fresh unique catalog (root)                       [Vector B: per-cat naming]
          • if action is a DROP → neutralize config gate      [gap 1]
          • case_scaffold(destroy_scaff=True):
              scaff builds prereq entity (trust-the-commit)   [gap 5]
              scaff destroyed
              worker granted EXACTLY `privilege`
                 └─ grant PUT 400? → GRANT_INVALID            [gap 3]
              worker fires the action → classify via taxonomy [section 3]
          • teardown via __exit__                             [Phase 0]
Cell 3  run full matrix: specs × (each candidate priv + coarse overrides)
Cell 4  pandas DataFrame → Markdown truth table (rows=action, cols=privilege)
Cell 5  summary: derived minimal privilege per action; discovered GRANT_INVALID
        vocabulary; any BLOCKED_OPA/BLOCKED_CONFIG flags (= harness bugs to fix)
Cell 6  (optional) necessity pass: grant all-but-one, expect BLOCKED_PRIV  [gap 6]
```

## 5. Coverage

Three securables × actions, each candidate privilege tested in isolation, plus the two coarse masters to verify the cascade claims.

| Target | Action (verb) | Candidate minimal privileges (to verify) | Coarse overrides |
|---|---|---|---|
| Namespace | CREATE (POST) | `NAMESPACE_CREATE` | `CATALOG_MANAGE_CONTENT` |
| Namespace | LIST (GET) | `NAMESPACE_LIST` | `CATALOG_MANAGE_METADATA` |
| Namespace | DROP (DELETE) | `NAMESPACE_DROP` | `CATALOG_MANAGE_CONTENT` |
| Table | CREATE (POST) | `TABLE_CREATE` ✓ | `CATALOG_MANAGE_CONTENT` |
| Table | LIST (GET) | `TABLE_LIST` ✓ | `CATALOG_MANAGE_METADATA` |
| Table | COMMIT (POST snapshot/schema) | `TABLE_WRITE_DATA` | `CATALOG_MANAGE_METADATA` / content master |
| Table | READ (GET metadata) | `TABLE_READ_DATA` | `CATALOG_MANAGE_METADATA` |
| Table | DROP, plain (DELETE) | `TABLE_DROP` ✓ | `CATALOG_MANAGE_CONTENT` |
| Table | DROP **WITH PURGE** (DELETE `?purgeRequested=true`) | ⚠️ `TABLE_DROP` ✓ alone is NOT sufficient — measured 2026-07-06, see `doc-privilege-results.md` §1 addendum and `purge/table_purge_privilege_test.ipynb` | `CATALOG_MANAGE_CONTENT` (confirmed sufficient) |
| View | CREATE (POST) | `VIEW_CREATE` ✓ | `CATALOG_MANAGE_CONTENT` |
| View | GET (GET one view) | `VIEW_LIST` ✓ (verify vs a read priv) | `CATALOG_MANAGE_METADATA` |
| View | DROP (DELETE) | `VIEW_DROP` ✓ | `CATALOG_MANAGE_CONTENT` |

(✓ = privilege name already confirmed accepted by this build. Unmarked names are hypotheses the matrix will confirm or return `GRANT_INVALID`.)

## 6. Reused invariants (already solved upstream)

- **Non-root rule** — root only bootstraps/destroys; all challenges run as workers. Note (added 2026-07-06): this rule means the original matrix runs never actually tested root against `DROP_TABLE_WITH_PURGE` specifically — turns out root does NOT bypass that one op (unlike every other op tested here, where root would). See `doc-privilege-results.md`.
- **Scoped token** — `scope=PRINCIPAL_ROLE:{role}` (avoids the OPA "no role activated" 403).
- **No catalog_admin grant** — service_admin can't `ADD_CATALOG_*` here; workers get grants on their own catalog-roles instead.
- **Per-catalog namespace** — `ns-{catalog}` via `_ns()` (Vector B).
- **Trust-the-commit** — create-500 with `metadata`/NPE accepted; `_RAW_SETTLE` settle.
- **Atomic teardown** — `case_scaffold.__exit__` (recursive bottom-up + MinIO sweep + principal cleanup).

## 7. Validation approach

Before running the full matrix, validate the classifier against a **known** result: the View DROP with baseline-only privileges must classify as `BLOCKED_PRIV` (matches C9). A View DROP with `VIEW_DROP` granted must classify as `AUTHORIZED`. If either returns `BLOCKED_OPA` or `BLOCKED_CONFIG`, the harness (token scope or config neutralization) is wrong — fix before trusting any other cell.

## 8. Definition of done

- Notebook renders a Markdown truth table: each cell ∈ {`AUTHORIZED`, `BLOCKED_PRIV`, `GRANT_INVALID`} under normal operation.
- Zero `BLOCKED_OPA` / `BLOCKED_CONFIG` cells (their presence = harness bug, surfaced explicitly).
- A derived "minimal privilege per action" summary, plus the discovered list of valid vs `GRANT_INVALID` privilege names for this Polaris build.
- Optional necessity pass confirms each identified minimal privilege is actually necessary (all-but-one → `BLOCKED_PRIV`).
