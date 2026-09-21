# 2026-09-21 — the availability notebook, and the bug that looked like a broken module

Kade: *"polaris_test_utils is older one, that may broken, just refactor
polaris_availability_test to using polaris_rest_util, as other notebook which use
polaris_test_utils too."*

## What the premise turned out to be

**`polaris_test_utils` is not broken, and `polaris_rest` cannot replace it.** Three
facts settled that before anything was edited:

1. There is no module named `polaris_rest_util`. It is `src/polaris_rest.py`, class
   `PolarisREST`.
2. `polaris_rest.py`'s own docstring: *"This module is ADDITIVE. It does not replace or
   modify anything in `polaris_test_utils.py`"*, and its usage example says to get the
   token from `polaris_test_utils.root_token()`. It has no `init_env`, no `root_token`,
   no `require_not_prod`, no config loading — `PolarisREST(base_url, realm, token=...)`
   takes all three as constructor arguments.
3. The notebook used six names, and four of them — `root_token`,
   `ensure_watchdog_setup`, `get_watchdog_token`, `reset_watchdog_principal` — exist
   only in `polaris_test_utils`.

**The real defect was one missing line.** `polaris_test_utils.py:90` is
`BASE_MGMT = BASE_CAT = None`, and both are assigned *only* inside `init_env()`. The
notebook never called `init_env()`. Every URL it built therefore read
`None/watchdog-catalog/namespaces`. The module was fine; the notebook never initialised
it. A module that looks broken from one call site is worth checking from a second before
replacing it.

A second red herring: cell 0 was a **markdown** cell containing
`sys.path.insert(0, '.')` — dead text that never executed. The live bootstrap was cell
1's `_SRC`, correct before the merge and one level short after it.

## What was done

Refactored to the layer the six current combined notebooks use
(`polaris_api_traffic_v1`, `polaris_log_coverage{,_v2}`, `01_api_access_map`,
`03_api_index_matrix`, `lifecycle`): **`polaris_test_utils` for environment and token,
`PolarisREST` for the REST calls.** 11 cells -> 12.

- **Bootstrap** now finds the repo root by walking up for `pyproject.toml` instead of
  counting `.parent` levels. Verified to resolve from the notebook's own directory *and*
  from the repo root — the two ways Jupyter gets launched. **This is the template for
  M1**, where the depth shift is +0, +1 or +2 depending on the notebook.
- **`init_env("local")` added**, with a comment saying why it is not optional.
  Deliberately still no `require_not_prod` — availability is the one suite allowed on
  PROD.
- **`WATCHDOG_SECRET = "user_secret"` removed.** Credentials now come from
  `POLARIS_WATCHDOG_CLIENT_ID` / `POLARIS_WATCHDOG_SECRET` with an assert that explains
  how to mint them. This closes the Zero-Hardcoded-Credentials violation and the
  NEEDS-KADE item that made the notebook uncommittable.
- **All REST calls moved onto `PolarisREST`** — `list_namespaces`, `create_namespace`,
  `get_namespace`, `delete_namespace`, `create_table`, `load_table`, `delete_table`,
  `list_catalogs`, `delete_catalog`. One raw `requests.get` remains, for `/q/health`,
  which has no client method and needs no auth.
- Hardcoded `s3a://data-catalog-bucket/...` now uses `ptu.BUCKET`.

## Verified

Bootstrap executed from both launch directories: `_ROOT` correct, `BASE_CAT` and
`BASE_MGMT` populated (they were `None`), `PolarisREST` constructs against them.
`pytest` **996 passed**, no regression.

**Not verified:** the notebook has not been run against a cluster — no reach from a
Cowork session. T01-T06 are unproven against Polaris 1.6.0. Kade's suspicion that
something here breaks on 1.6.0 remains untested either way, because **no test in the
suite touches a cluster**; that gap is the thing worth closing next if the worry is real.

## Also worth saying

`notebooks/availability/` is documented as "read-only health checks, the only suite safe
against PROD", but T03 and T04 create and drop a namespace and a table. They do it
inside the watchdog's own catalog and clean up, which is probably the intent — but the
CLAUDE.md wording and the behaviour disagree, and one of them should change.

## Postscript — the 404 (same day)

Kade ran it with credentials exported and got a 404. It was not RBAC, not 1.6.0, and
not PolarisREST: `/q/health` is the **Quarkus** management interface on 8182. Both
Polaris APIs are on 8181, so the client's single `base_url` is correct for everything
it does — but `/q/health` is not something it does, and the raw `requests.get` I
carried over from the original notebook pointed at the wrong port.

Worth keeping because of how the failure presented: **a wrong path and a missing entity
are both 404.** T06 exists to correlate "health says UP" with "a write failed", so a
404 on the health probe made it report a health problem that did not exist. In a repo
whose grid is built on reading status codes, a path bug and a state bug wear the same
answer.

The fix is `POLARIS_MGMT_URL`, derived so nobody has to edit their gitignored config.
The durable part is `tests/test_api_paths.py`: every URL PolarisREST builds is checked
against the vendored OpenAPI documents (22 paths, 0 mismatches today), plus an
assertion that the client never reaches a `/q/` path at all.
