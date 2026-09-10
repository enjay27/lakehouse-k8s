# PLAN — every API, every reachable status, every log it leaves

**Status: PROPOSED, not started.** Plan-first per `CLAUDE.md`; nothing is written until this
is signed off.

**The question this run answers.** `polaris_log_coverage.ipynb` asks *"if something went wrong
on this endpoint tomorrow, would there be a record of it?"* and answers it for **43 of 63**
operations, at whatever status those calls happened to return. This plan widens both axes:
**every operation the two vendored specs name**, driven **at every status code this build can
actually produce**, with the report-schema gates of `GUIDE-schema-v3-testing.md` applied to the
result.

Four decisions taken 2026-09-10, before any code:

| decision | choice |
|---|---|
| sink | **OpenSearch only**, per the guide — `polaris-report-*` / `polaris-logs-*` |
| status scope | **reachable-only, plus the extras** the spec never declares (405, the provoked 500) |
| where | **`polaris_log_coverage_v2.ipynb`**, new. v1 stays the run of record and is *referred to*, not edited |
| the Lua oracle | **read out of the cluster with `kubectl`** from inside the notebook — no `local-k8s` checkout needed |

---

## 0. Read this before anything else: five contradictions between the docs

These are not nitpicks. Each one changes what the run means, and four of them can make a gate
pass vacuously — this pipeline's recurring defect.

**0.1 The sink conflict is real and is now a deliberate split.** `log-coverage/README.md` says
the OpenSearch shipper is a *second, unrelated* Fluent Bit — a DaemonSet shipping container
stdout — and that "a line present in OpenSearch and absent from VictoriaLogs is that DaemonSet,
not a finding here". The guide queries OpenSearch indices `polaris-report-*` and
`polaris-logs-*`, which are **not** `k8s-logs-*` (the DaemonSet stream `src/config/common.yaml`
points at). So one of two things is true, and **preflight must decide which before driving**:

- the polaris shipper gained an OpenSearch OUTPUT in addition to VictoriaLogs — then both
  sinks carry the same records and the guide's indices exist; or
- `polaris-report-*` does not exist, and **there is nothing for gates 0–6 to read**.

`_cat/indices/polaris-*` answers it in one call. If the indices are absent, this run stops at
preflight rather than reporting empty aggregations as passes.

**0.2 The report schema v3 is *written, not deployed*.** `SCHEMA-report.md` says so in its own
title, and that "everything stored so far" is **schema v2**. The guide's **Gate 0 requires a
v3 document to come back**. Both cannot hold today. So Gate 0 is expected to FAIL on first run,
and the plan treats that as the gate working: everything v3-only —`last_read_bytes`,
`last_write_bytes`, `role_keys_forced`, the `catalog-role`/`principal-role`/`auth`/`config`
kinds, the `__errors__` / `__other__` split — is **VOID, not failed**, and the matrix still runs
at v2. **Decision needed from you:** deploy report v3 before the run, or accept a v2 run with
Gates 2, 4 (denial half) and 5 recorded as UNAVAILABLE.

**0.3 Two different values files.** The repo reads `~/hynix/local-k8s/logging/fb-values.yaml`
(`local.yaml: fb_values_path`); `SCHEMA-report.md` reads `fluent-bit/values.yaml` (`build_report`
at ~line 447). Whichever is right on disk, **neither is authority**: the guide says it itself —
"reading `schema_version` out of `fluent-bit/values.yaml` proves nothing". This plan reads the
**ConfigMap out of the cluster** and treats the file only as a cross-check.

**0.4 Gate 7's assertion count disagrees with itself.** `SCHEMA-report.md`: "16 assertions, all
passing". `GUIDE-schema-v3-testing.md` Gate 7: "46 assertions". Whichever number the harness
prints, the notebook records it verbatim and flags the mismatch instead of asserting a count.

**0.5 The OpenSearch address.** The guide hardcodes `https://192.168.194.1:9200`;
`src/config/local.yaml` has `opensearch_host: localhost` (a port-forward). Same cluster, two
routes. New config keys — `opensearch_report_index`, `opensearch_logs_index` — go in
`common.yaml`; the host stays per-env. No hardcoded address in the notebook.

---

## 1. The denominator: 63 operations, machine-read from `log-coverage/spec/`

Read 2026-09-10 out of the vendored documents, not typed:

| document | operations | codes it declares |
|---|---|---|
| `polaris-management-service.yml` | 33 | 200, 201, 204, 403, 404, 409 |
| `rest-catalog-open-api.yaml` | 30 | 200, 204, 304, 400, 401, 403, 404, 406, 409, 419, 422, 500, 502, 503, 504, 5XX |

`lc.spec_inventory()` already parses both and `lc.coverage_rows()` already adjudicates
spec / captured / driven. **The gap is measured, not estimated** — running today's
`api_surface.operations()` against the spec gives `driven 40, spec 63`, and these **24 spec
operations have no driver at all**:

```
catalog     POST   /{}/namespaces/{}/register           POST   /{}/namespaces/{}/tables/{}/metrics
            POST   /{}/namespaces/{}/tables/{}/plan     GET    /{}/namespaces/{}/tables/{}/plan/{}
            DELETE /{}/namespaces/{}/tables/{}/plan/{}  POST   /{}/namespaces/{}/tables/{}/tasks
            GET    /{}/namespaces/{}/tables/{}/credentials
            POST   /{}/namespaces/{}/views/{}           POST   /{}/transactions/commit
            POST   /oauth/tokens
management  POST   /catalogs                            PUT    /catalogs/{}
            DELETE /catalogs/{}                         GET    /catalogs/{}/catalog-roles/{}
            PUT    /catalogs/{}/catalog-roles/{}        POST   /catalogs/{}/catalog-roles/{}/grants
            GET    /catalogs/{}/catalog-roles/{}/principal-roles
            GET    /principal-roles/{}/catalog-roles/{} DELETE /principal-roles/{}/catalog-roles/{}/{}
            PUT    /principal-roles/{}                  PUT    /principals/{}
            GET    /principals/{}/principal-roles       DELETE /principals/{}/principal-roles/{}
            POST   /principals/{}/rotate
```

Several of these are driven *incidentally* by v1's fixture setup and probe cells (`POST
/catalogs`, `POST /oauth/tokens`, the grants) — but not as **inventory**, so they never appear
in the coverage verdict. v2 drives them by name.

**These are also exactly the endpoints the classifier has never seen**, which makes Gate 6 the
gate most likely to produce a real finding: `/credentials`, `/plan`, `/plan/{id}`, `/tasks`,
`/register`, `/transactions/commit` almost certainly have no `RESOURCE_PATTERNS` entry, so they
should surface with their real paths under `resource_kind: other`. **Predicted finding, stated
before the run so it can be wrong.**

---

## 2. The status axis: a rule per code, applied to all 63

"Reachable-only" is a decision about *what to drive*, not permission to skip quietly. Every
code below is either driven by a mechanical rule, or lands in the **NOT-REACHABLE ledger with a
measured reason** — the `NOT_CALLABLE` pattern v1 already uses for 429.

### Driven, by rule

| code | how it is provoked, on every operation the rule applies to | cells |
|---|---|---|
| **2xx** (200/201/204) | the happy path, in dependency order, against the run fixture | 63 |
| **401** | the same call with a garbage bearer token (and, for `getToken`, a real client id + wrong secret) | 63 |
| **403** | the same call issued by `nb_<run>_denied` — a principal with a role and no grants | 62 (all but `getToken`) |
| **404** | a name that does not exist substituted into the last path parameter | 50 (ops with a non-`{prefix}` param) |
| **409** | create-twice, or a stale `entityVersion` on the management PUTs | 15 (ops declaring 409) |
| **400** | a request body missing a required field; `GET /v1/config` with no `warehouse` | 28 (27 with a body + config) |
| **422** | measured 2026-09-07: a broken storage endpoint (`127.0.0.1:1` or `.svc.invalid`) — a **client** error on this build | 2 |
| **405** | *extra, undeclared*: `DELETE /v1/config` and two siblings | 3 |
| **500** | `lc.provokers_500` — the four-rung ladder, in its own pure window | 1 (≤12 calls) |

**≈293 cells, ≈305 calls.** Comparable to v1's 157 and well inside one sitting.

### Probe-then-adjudicate — assumed unreachable, *measured* anyway

A gate whose failure mode you cannot state is not a gate, and "unreachable" written from a spec
is exactly that. Each of these gets **one** probe call whose result is recorded either way:

| code | the probe | what today's belief is |
|---|---|---|
| **304** | `loadTable` with `If-None-Match` from a prior `ETag` | probably unsupported → 200 |
| **406** | `Accept: application/xml` on a JSON endpoint | probably ignored → 200 |
| **419** | any catalog call with an expired token | Iceberg's credential-refresh code; Polaris likely returns 401 |
| **502 / 504** | none — there is no proxy in front of Polaris here | a port-forward is not a gateway |
| **503** | none — the only route is scaling Polaris, and **HPA movement invalidates the run** (`local-k8s` #8) | structurally excluded |
| **429** | none — `rateLimiter.type: no-op` | carried over from v1, unchanged |
| **5XX** | — | a spec placeholder, not a status |

Each probe prints `provoked` / `NOT PROVOKED` with the status it actually got. An honest gap
beats a fabricated pass.

### The rule for a cell that misses

If a cell targeting 404 returns 403, it is recorded as **MISSED, actual=403** and the 404 stays
uncovered. It is never silently relabelled as coverage of 403 — that is how a matrix comes to
agree with itself and with nothing else.

---

## 3. Windows: the run has to be scheduled, not just executed

Every gate in the guide is **per window**, and the fast-run `WINDOW_SECONDS` is **30**
(temporary, sha `d58b9203a8304030`, revert-together with `Interval_Sec` 5). 305 calls will
straddle a dozen boundaries, and a burst that straddles a boundary makes the window-level
checks VOID — v1 §11c already handles exactly this and prints `straddled=`.

So the drive is **phased, each phase aligned to a boundary** (`seconds_to_boundary`, as §5c
does), and each call records its `window_start`:

| phase | contents | why it is alone in its window |
|---|---|---|
| A | fixture setup | fixture noise must not pollute a measured window |
| B | 2xx sweep, all 63 | the margin equality (Gate 1) on a busy, clean window |
| C | 404 + 403 + 401 sweep | Gate 5: `__errors__` should take these, and `resources_other` should stay 0 |
| D | 409 + 400 + 422 | mixed client errors |
| **E** | **one commit, and nothing else** | **Gate 2 is the feature.** "The *last* 2xx POST in that window" is only unambiguous when there is one |
| **F** | **one DELETE, and nothing else** | Gate 2's negative half: `last_write_bytes` must be **ABSENT**, not 0 |
| **G** | **grants + one 403 on a catalog role** | Gate 4: `writes == N privileges`, and the denial forces the role row + `role_keys_forced` |
| H | the 500 ladder | §5c's pure-500 window, so `errors_4xx == 0` is a *prediction* |
| I | cleanup DELETEs | part of the test, per v1 |

Phases E, F and G are the ones that do not exist in v1 and are the reason this is a new
notebook rather than more cells in the old one.

---

## 4. What gets built

### `src/os_report.py` — new, the OpenSearch sibling of `vlogs.py`
`vlogs.VLogs` speaks LogsQL to VictoriaLogs; nothing in `src/` speaks to `polaris-report-*`.
`polaris_test_utils.os_client()` exists but is pinned to `k8s-logs-*` (the DaemonSet stream).
New, small, and mirroring the vlogs surface so the notebook reads the same:
`ping()`, `report_window(ws)`, `report_types(ws)`, `latest_summary(with_traffic=True)`,
`by_request_id(rid)`, `settle()`, `seconds_to_boundary()`, and **`V3` baked into every query**
(the guide's first trap). Two guards it must carry from the guide:
- **every `sum` is paired with a `value_count`** — absence is not zero, and `0 == 0` is the
  tidiest false pass there is;
- **`mapping_of(field, index)`**, because `min_record_time` is mapped as **text** in
  `polaris-report-2026.09.09` and no date maths works on it there.

### `src/api_status_matrix.py` — new, the grid
- `cells(spec, fixture, clients)` → one `Cell(op_id, method, path, target_status, driver,
  phase, why_not_reachable)` per planned cell, built **from the parsed spec**, not typed.
- the six status rules from §2 as composable transforms of a happy-path call.
- `adjudicate(cells, results)` → `covered / missed / not-reachable`, per operation and per code.
- No test logic in the notebook (`CLAUDE.md` §Strict Logic Separation).

### `src/log_coverage.py` — one addition
`policy_from_cluster(namespace, selector)`: `kubectl get cm -o yaml` → extract the Lua →
write a values-shaped temp file → hand it to the existing `load_policy()`. **This removes the
`local-k8s` checkout from the critical path** and makes the oracle read what is *running*,
which `deployed_policy_status()` currently checks only after the fact.

### `log-coverage/polaris_log_coverage_v2.ipynb` — new
Reuses v1's helpers wholesale (`lc.call_once`, `drive_tagged`, `expected_for`,
`check_invariants`, `provokers_500`, `surf.ProbeFixture`, `elect_drive_identity`). Cell order
follows the guide, **Gate 7 first**:

| cell | content | fails if |
|---|---|---|
| 0 | preflight: Polaris, OpenSearch, `_cat/indices/polaris-*`, `lua5.4`, kubectl, HPA/shipper snapshot | §0.1 — indices absent |
| 0a | **Gate 7** — the Lua unit test against the deployed script text | it does not run, or an assertion fails; the count is recorded, not asserted (§0.4) |
| 0b | policy from the cluster; `WINDOW_SECONDS`, `SCHEMA_VERSION`, tick rate — all read, never assumed | oracle a schema behind the filter (v1's cell 0b, kept verbatim) |
| 0c | **Gate 0** — is report v3 running | **expected to fail today** (§0.2) → v3-only assertions marked VOID |
| 1 | identities: root, run principal, denied principal, unauthenticated, wrong-secret | one identity drove everything → per-principal margin is unfalsifiable |
| 2 | the grid, printed **before driving**: cells, phases, not-reachable ledger | — |
| 3–11 | phases A–I | any phase straddling a boundary marks its window's checks VOID |
| 12 | collection: `polaris-logs-*` by `mdc.requestId`, settle, dedup | correlation < 100% on KEPT calls |
| 13 | **the matrix**: operation × status × {target, actual, stored, expected-by-oracle, resource_row, window} | a `keep` verdict with 0 stored |
| 14 | **Gates 1–6**, verbatim from the guide, each with its stated failure mode | see the guide |
| 15 | invariants from `SCHEMA-report.md` §"Invariants worth asserting" | any of the four |
| 16 | findings, and the coverage verdict against the spec denominator | — |

### `test_log_coverage.py` — extended
Two kinds, as the README insists: **invariants** (every 4xx is stored; a cell that misses is
never counted as coverage; `V3` present in every generated query) and **characterization**
(the grid's shape today — expected to fail when the spec is re-vendored, which is the signal to
re-run `fetch_specs.sh` and read the diff).

---

## 5. What could make this run worthless — stated up front

1. **`polaris-report-*` does not exist** → gates 0–6 have no source. Preflight stops the run.
2. **Report v3 is not deployed** (likely, §0.2) → Gates 2, 4-denial and 5 are UNAVAILABLE.
3. **Polaris scales mid-run** (HPA, 3 replicas → one log file) → the whole run is invalid.
4. **The shipper restarts mid-run** → `report_seq` gaps, per-pod counters reset.
5. **The fast-run settings are reverted mid-plan** → 30s windows become 1800s and the phase
   schedule stops working. Revert *after* the run of record, both settings together.
6. **A phase straddles a boundary** → that phase's window checks are VOID, not failed. Re-drive.

---

## 6. Definition of done

1. `polaris_log_coverage_v2.ipynb` runs top-to-bottom (`Restart & Run All`), zero errors.
2. Every one of the 63 operations appears in the matrix with at least its 2xx cell adjudicated;
   every planned cell is covered, missed-with-actual, or in the not-reachable ledger with a
   reason. **No blank cells.**
3. Gates 0–7 each print PASS / FAIL / VOID **with the reason**, never a bare number.
4. `black . && isort .`; `pytest` green (note: `pytest` could not be run from this side on
   2026-09-08 — macOS `.venv` unusable in the VM, PyPI 403; if that holds, the commit says
   `NOT VERIFIED` and why).
5. `doc-api-status-matrix-results.md` written beside this plan; `MEMORY.md` *Now* updated;
   `.memory/roadmap.md` gets the finding with its number.
6. One commit, by Claude, carrying code + notebook + docs together.

---

## 7. Sign-off needed on three points

1. **Report v3**: deploy before the run, or accept a v2 run with three gates UNAVAILABLE?
2. **`polaris-logs-*`**: does the polaris shipper actually write to OpenSearch, or is the guide
   describing a pipeline that is not wired here yet? (Preflight will tell us; better to know now.)
3. **305 calls against `local`** — creates and deletes a catalog, several principals, roles, a
   namespace, a table and a view, and deliberately provokes 500s. Confirm `local` is the target
   and nothing else is using that realm.
