# PLAN — the Polaris API → VictoriaLogs coverage notebook

**Task plan. Nothing is built yet.** Both `CLAUDE.md` files run Strict Plan-First Mode, so this
document is the whole of turn one: it says what will be written, what it will reuse, what it
corrects in the source plan, and what needs a decision before any code exists.

**Source plan:** `$HOME/hynix/local-k8s/POLARIS-API-LOG-COVERAGE-NOTEBOOK.md`
(the handoff from `local-k8s` roadmap step 2). Read it first — this document does not restate it,
it *amends* it. Everything in §2 below is a correction or a settlement of something that plan
marked **[assumed]**.

**Status vocabulary, same as the source plan.** **[verified]** — observed in a real record or a
running object. **[from values]** — read from a values file or a rendered ConfigMap. **[assumed]**
— reasoning not yet checked. **[from repo]** — established by code in `polaris-learning` that
demonstrably runs against this cluster; weaker than [verified], stronger than [assumed].

---

## 0. Read order for someone starting cold

1. `local-k8s/POLARIS-API-LOG-COVERAGE-NOTEBOOK.md` — what the notebook is for, and the retention
   policy it tests.
2. `local-k8s/logging/fb-values.yaml`, the `luaScripts` block — the policy itself. **This file is
   the authority for every "expected" value in the matrix**, and §4.2 below makes the notebook read
   it rather than paraphrase it.
3. This document.
4. `polaris-learning/src/api_surface.py` — the 43-operation drive surface that will do the calling.

---

## 1. What this task produces

| deliverable | path | new? |
|---|---|---|
| the notebook | `log-coverage/polaris_log_coverage.ipynb` | new |
| dir readme (concept / purpose / how-to-run / result) | `log-coverage/README.md` | new |
| findings report, written for someone who was not there | `log-coverage/doc-log-coverage-results.md` | new, written after the run |
| VictoriaLogs query client | `src/vlogs.py` | new module |
| coverage-matrix logic + the deployed-Lua oracle | `src/log_coverage.py` | new module |
| spec vendoring + the three-way denominator | `log-coverage/fetch_specs.sh`, `log-coverage/spec/` | new |
| per-call request-id header | small change to `src/polaris_rest.py` | **modifies an existing module — needs sign-off** |
| `victorialogs_url`, `fluentbit_metrics_url`, `fb_values_path` | `src/config/common.yaml`, `local.example.yaml`, `init_env()` in `src/polaris_test_utils.py` | **modifies an existing module — needs sign-off** |
| tests for both new modules | `test_vlogs.py`, `test_log_coverage.py` | new, offline-testable |

Nothing in `local-k8s` is touched. Its one follow-up is §8.4.

---

## 2. Corrections to the source plan

### 2.1 Four of the plan's `[assumed]`s are already settled by this repo

The source plan says to confirm these "with one call before building anything on it". Three of
them do not need a call — `polaris-learning` has been driving this cluster for weeks and the
answer is in the code that works.

| source plan says | actually | evidence |
|---|---|---|
| both APIs on 8181 is **[assumed]**; "a whole notebook aimed at the wrong port is a bad afternoon" | **8181 is right.** `PolarisREST` builds *both* `/api/management/v1` and `/api/catalog/v1` off one base URL, and `local.yaml` sets that base to `:8181` | **[from repo]** `src/polaris_rest.py:88-89`, `src/config/local.example.yaml` |
| realm header name is **[assumed]** `Polaris-Realm` | **correct.** Every request the suite makes sends `Polaris-Realm`, and the suite passes | **[from repo]** `src/polaris_rest.py:_h()` |
| `8182` is the Quarkus management interface, not the Polaris Management API | **confirmed, and it is a known trap here** — `diagnostics/api-sql-profile/probe_api_surface.py` keeps `POLARIS_MGMT_URL` on 8182 purely for `/q/*` | **[from repo]** |
| `Polaris-Request-Id` round-trip is **[assumed]** | **still open, and still the first thing the notebook does.** What is known: Polaris *emits* the header on responses (`get_request_id()` reads it). Whether it *honours* a client-supplied one is unproven | **[from repo]** + **[from values]** `logging.requestIdHeaderName` |

Only the fourth is genuinely open. Cell 1 still verifies it, and §4.1 says what changes if it fails.

### 2.2 The OpenAPI plan cannot be followed as written — this Polaris serves no document

Source plan §4: *"Do not hand-write the endpoint list. Two OpenAPI documents define the surface;
parse them."* The instinct is right; the mechanism named is not available.

**Measured 2026-08-31 [verified]:** Polaris 8181 and 8182 serve **no** OpenAPI document — every
`/q/openapi*` and `/openapi*` candidate came back empty. `probe_api_surface.py` records this and
the reasoning: *a document describes what a build INTENDS to serve; the captured matrix records
what it actually served.*

So the denominator is built from **three sources at once, kept separate, and diffed** — the
decision taken for this task:

1. **VENDORED SPEC** — `polaris-management-service.yml` and `rest-catalog-open-api.yaml` fetched at
   tag `apache-polaris-1.3.0-incubating` by `fetch_specs.sh`. This is what the source plan asked
   for and it is worth having: it is the only source that can name an endpoint *nobody here has
   ever called*. It is a statement about a **version**.
2. **CAPTURED** — `diagnostics/api-sql-profile/reports/doc-api-sql-matrix-*.md`, every API a live
   run has actually issued against **this deployment**. Strongest evidence, but a lower bound.
3. **DRIVEN** — `api_surface.operations()`, the 43 operations this notebook will itself call.

The matrix carries all three columns and the verdicts stay three-way, deliberately, exactly as
`probe_api_surface.py` argues: **confirmed gap** (served here, not driven), **unverified** (driven,
never observed here), **candidate** (spec names it, nothing observed, nothing drives it). Collapsing
those into one percentage lets a feature-flagged endpoint this build does not serve count as a
failure, and lets a genuinely missing one hide behind the same asterisk.

Vendored spec files are **gitignored**; `fetch_specs.sh` and the derived inventory
(`log-coverage/spec/inventory.json`, with the spec files' SHA-256) are committed. The inventory is
the durable artifact; the YAML is a download.

### 2.3 The audit gap is larger than "principals are created invisibly"

Source plan §5 rule 5 names one asymmetry — `POST /v1/principals` dropped while its DELETE is kept —
and calls demonstrating it *"the most persuasive output this notebook can produce"*. It is more than
that. Running the deployed rules over the 43 driven operations by hand (§3) gives **eight dropped
mutations inside the drive surface**, plus two more the fixture issues outside it:

| dropped mutation | why it matters |
|---|---|
| `POST /v1/principals` | the named asymmetry — created invisibly, deleted visibly |
| `POST /v1/principal-roles` | same |
| `POST /v1/catalogs/{cat}/catalog-roles` | same |
| `POST /v1/catalogs` *(fixture)* | a whole catalog appears with no record |
| **`POST /v1/principals/{p}/reset`** | **a credential reset leaves no trace.** This is a security event, not a bookkeeping one, and it is not mentioned in the source plan at all |
| `POST /v1/{cat}/tables/rename` | a table rename is invisible — the path has no `/namespaces/{ns}/tables` segment, so it misses `KEEP_POST_PATTERNS` |
| `POST /v1/{cat}/views/rename` | same, for views |
| `POST /v1/{cat}/namespaces` | namespace creation (the source plan does name this one) |
| `POST /v1/{cat}/namespaces/{ns}/properties` | the only way to set namespace properties, and it is a POST |
| `POST /api/catalog/v1/oauth/tokens` | dropped by design — successful auth is unanswerable |

Rule 5's comment says the drop was *"aimed at the OAuth token endpoint"*. The two rename endpoints
and `/reset` show the blast radius was never bounded to that. **The notebook's headline is not one
asymmetry; it is a count.** Roadmap 4b should be re-scoped accordingly.

### 2.4 The sample record in the source plan may predate `type_int_key`

Source plan §2.4's **[verified]** record has `"http_status": "404"` and `"response_size": "113"` —
**strings**. `fb-values.yaml` sets `type_int_key http_status response_size` on the Lua filter
precisely so VictoriaLogs stores them as numbers, with the note that without it *"VictoriaLogs
stores 404.0 and numeric LogsQL filters miss"*.

Both cannot be true of the same deployment. Either the sample predates the filter, or `type_int_key`
is not taking effect. **Every LogsQL query in this notebook that filters on status depends on the
answer**, so cell 0 settles it by reading one stored record's raw JSON and reporting the type, and
every query is written against whichever it turns out to be. This is the §2.4-shaped trap the
`local-k8s` memory keeps warning about: a rendered view is not the record.

### 2.5 "Provoke a 500 and check for stack traces" needs a known 500, and this repo has several

The source plan calls stack-trace survival *"the single most valuable thing this notebook could
find"* but does not say how to cause one. `error-cases/` already has working, committed provocations:
`09_500_null_pointer.ipynb`, `16_500_entity_version_mismatch.ipynb`,
`18_500_concurrent_modification_conflict.ipynb`, `23_500_minio_bucket_not_found.ipynb`. The notebook
reuses the cheapest reliable one rather than inventing a new way to break Polaris. Which one is
§8.2.

---

## 3. The predicted matrix — computed offline from the deployed Lua

**This is a prediction, not a result.** It is here so the run has something to falsify: a
notebook that only reports what it saw cannot tell you the pipeline surprised you. Every row is the
first matching rule in `polaris_noise_filter` applied to the 43 operations in
`api_surface.operations()`, assuming a 2xx unless stated.

Legend: **✓** stored every call · **1/day** stored once per KST day per key · **✗ DROPPED**.

### Iceberg REST (24 ops)

| op | method | path | rule | stored |
|---|---|---|---|---|
| get_config | GET | `/v1/config` | 7 | ✓ — polled on every client connect (the noise rule 7 exists to be narrowed against) |
| list_namespaces | GET | `/v1/{cat}/namespaces` | 7 | ✓ every call |
| load_namespace | GET | `.../namespaces/{ns}` | 7 | ✓ every call |
| head_namespace | HEAD | `.../namespaces/{ns}` | 7 | ✓ every call |
| update_namespace_properties | POST | `.../namespaces/{ns}/properties` | 5 | **✗ DROPPED** |
| create_namespace | POST | `/v1/{cat}/namespaces` | 5 | **✗ DROPPED** |
| drop_namespace | DELETE | `.../namespaces/{ns}` | 4 | ✓ |
| list_tables | GET | `.../namespaces/{ns}/tables` | 7 | ✓ every call — **LIST is not deduplicated** |
| load_table | GET | `.../tables/{tbl}` | 6 | 1/day |
| load_table?snapshots=refs | GET | `.../tables/{tbl}?snapshots=refs` | 6 | 1/day, **separate key** → 2 records total with the row above |
| head_table | HEAD | `.../tables/{tbl}` | 6 | 1/day, **separate key from GET** |
| create_table | POST | `.../namespaces/{ns}/tables` | 5 | ✓ kept |
| stage_create_table | POST | `.../namespaces/{ns}/tables` | 5 | ✓ kept |
| commit_table | POST | `.../tables/{tbl}` | 5 | ✓ kept — **but what was committed is not in the record** |
| rename_table | POST | `/v1/{cat}/tables/rename` | 5 | **✗ DROPPED** |
| report_metrics | POST | `.../tables/{tbl}/metrics` | 5 | ✓ kept |
| load_table[missing] | GET | `.../tables/{missing}` → 404 | **3** | ✓ **every call** — errors outrank dedup |
| drop_table | DELETE | `.../tables/{tbl}` | 4 | ✓ |
| create_view | POST | `.../namespaces/{ns}/views` | 5 | ✓ kept |
| list_views | GET | `.../namespaces/{ns}/views` | 7 | ✓ every call |
| load_view | GET | `.../views/{view}` | 6 | 1/day |
| head_view | HEAD | `.../views/{view}` | 6 | 1/day, separate key |
| rename_view | POST | `/v1/{cat}/views/rename` | 5 | **✗ DROPPED** |
| drop_view | DELETE | `.../views/{view}` | 4 | ✓ |

### Management API (19 ops)

| op | method | path | rule | stored |
|---|---|---|---|---|
| list_catalogs | GET | `/v1/catalogs` | 7 | ✓ |
| get_catalog | GET | `/v1/catalogs/{cat}` | 7 | ✓ |
| create_principal | POST | `/v1/principals` | 5 | **✗ DROPPED** ← the headline |
| get_principal / list_principals | GET | `/v1/principals[/{p}]` | 7 | ✓ |
| create_principal_role | POST | `/v1/principal-roles` | 5 | **✗ DROPPED** |
| get / list principal_roles | GET | `/v1/principal-roles[/{r}]` | 7 | ✓ |
| assign_principal_role | PUT | `/v1/principals/{p}/principal-roles` | 4 | ✓ — **which role is in the body, so not recorded** |
| create_catalog_role | POST | `/v1/catalogs/{cat}/catalog-roles` | 5 | **✗ DROPPED** |
| list_catalog_roles | GET | `/v1/catalogs/{cat}/catalog-roles` | 7 | ✓ |
| assign_catalog_role | PUT | `/v1/principal-roles/{r}/catalog-roles/{cat}` | 4 | ✓ — assignee in the path, so *this* one is legible |
| **grant_privilege** | PUT | `/v1/catalogs/{cat}/catalog-roles/{cr}/grants` | 4 | ✓ — **the privilege name is in the body. "Who granted what" is unanswerable from this pipeline** |
| list_grants | GET | `.../grants` | 7 | ✓ |
| list_principals_for_principal_role | GET | `/v1/principal-roles/{r}/principals` | 7 | ✓ |
| **reset_principal_credentials** | POST | `/v1/principals/{p}/reset` | 5 | **✗ DROPPED — a credential reset leaves no record** |
| delete_catalog_role | DELETE | `.../catalog-roles/{cr}` | 4 | ✓ |
| delete_principal_role | DELETE | `/v1/principal-roles/{r}` | 4 | ✓ |
| delete_principal | DELETE | `/v1/principals/{p}` | 4 | ✓ |

### Issued by the fixture, outside the 43

| op | method | path | rule | stored |
|---|---|---|---|---|
| create_catalog | POST | `/v1/catalogs` | 5 | **✗ DROPPED** |
| delete_catalog | DELETE | `/v1/catalogs/{cat}` | 4 | ✓ |
| oauth token | POST | `/api/catalog/v1/oauth/tokens` | 5 | **✗ DROPPED** (by design) |
| oauth token, bad secret → 401 | POST | same | **3** | ✓ |

**Predicted totals to check the run against:** 8 of 43 driven operations produce no record at all;
10 including the fixture's catalog create and the token exchange. 5 operations are deduplicated
(3 table/view read keys + 2 more from the query-string and HEAD splits). Everything else is stored
on every call.

---

## 4. What has to be built, and why each piece is a module rather than a cell

CLAUDE.md: *notebooks hold visualization; `src/` holds logic that wants a test.*

### 4.1 `src/polaris_rest.py` — per-call extra headers *(modifies an existing module)*

`_h()` returns a fixed three-key dict and there is no hook for a fourth. The whole correlation
design in source-plan §3 needs `Polaris-Request-Id: nb-<run>-<case>-<n>` on every call.

Proposed change, additive and non-breaking: `PolarisREST.__init__(..., default_headers=None)` plus
`self.extra_headers` merged inside `_h()`, so the notebook sets one attribute before each operation
and every existing call site is untouched. `get_token()` builds its headers separately and gets the
same treatment. **This is the only edit to a shipped module and it wants explicit sign-off.**

**If the round-trip does not work** — Polaris ignores or rewrites the id — the notebook falls back to
`user_principal_name`, which is `%u` from the access log **[verified]** and needs no code change at
all: create `nb_<epoch>_principal`, authenticate as it, and select the whole run with
`user_principal_name:"nb_<epoch>_principal"`. Coarser: per-run, not per-call, so the per-endpoint
rows in the matrix become per-endpoint-per-path rather than exact. Cell 1 decides which mode the
rest of the notebook runs in, and the report says which was used.

### 4.2 `src/log_coverage.py` — the expected column comes from the deployed Lua, not from a paraphrase

The §3 table above is hand-computed and is therefore exactly the kind of artifact this pair of repos
distrusts. The module removes the hand:

`predict(record) -> "keep" | "drop"` extracts `polaris_noise_filter` **out of
`local-k8s/logging/fb-values.yaml`** and executes it over a synthetic record with a real Lua
interpreter — the identical mechanism `logging/scripts/test-polaris-filters.py` already uses
(`subprocess`, trying `lua`, `lua5.4`, `lua5.3`, `luajit`, `luatex --luaonly`). The expected column
then cannot drift from what ships, and a policy change in `local-k8s` shows up as a matrix
difference rather than as a stale table.

Path comes from a new config key `fb_values_path` (default `~/hynix/local-k8s/logging/fb-values.yaml`).
If the file or a Lua binary is missing, the notebook **fails loudly** and says the expected column is
unavailable — it does not fall back to a Python re-implementation, because a re-implementation that
agrees with itself is not evidence. The file's SHA-256 goes in the report.

Also in this module: `matrix(driven, observed, inventory)` producing one row per endpoint with
`called? · status · expected · stored · discrepancy`, and the three-way verdict from §2.2.

### 4.3 `src/vlogs.py` — a VictoriaLogs client, because none exists

`polaris_test_utils` has `search_logs`, `search_4xx_errors`, … and every one of them talks to
**OpenSearch**. That is the other pipeline (the DaemonSet, container stdout). Nothing in this repo
has ever queried VictoriaLogs. New module:

- `query(logsql, start, end, limit)` → `POST /select/logsql/query`, ndjson response parsed to dicts.
- `poll_until(logsql, expect_at_least, timeout=30, interval=1)` — ingest is asynchronous; the source
  plan's rule is *poll, do not sleep-and-hope*. Returns what it got and how long it waited.
- `count(logsql)`, `records_for_run(principal)`, `record_for_request_id(rid)`.
- `stats()` → `fluentbit_filter_drop_records_total` from the shipper's `/api/v1/metrics`, for the
  before/after volume numbers the source plan §8.6 asks for. Needs a port-forward — **degrades to a
  reported gap rather than an exception when unreachable**.

Every parser takes text and returns records, so the module is testable against fixtures with no
cluster, matching `api_trace.py`'s design.

### 4.4 Config keys *(modifies `init_env`)*

`common.yaml`: `victorialogs_url: http://localhost:9428`, `fluentbit_metrics_url: http://localhost:2020`.
`local.example.yaml`: `fb_values_path`. `init_env()` exposes `VLOGS_URL`, `FB_METRICS_URL`,
`FB_VALUES_PATH`. Non-secret, so they belong in the tracked files. No new secret is introduced —
**VictoriaLogs on 9428 is unauthenticated**, which is `local-k8s` active-issue #7 and is noted in
the README rather than worked around.

---

## 5. Notebook cell map — `log-coverage/polaris_log_coverage.ipynb`

Linear, `Restart & Run All`-clean, one concern per cell.

| # | cell | what it must do, and what makes it abort |
|---|---|---|
| 0 | **Preflight** | `init_env("local")`, `require_not_prod(...)`. Polaris reachable on 8181; VictoriaLogs reachable on 9428; **the shipper's pod name and start time recorded** so a mid-run restart is detectable (source plan §6: dedup state is per-pod); `fluentbit_filter_drop_records_total` **before**; the HPA replica count **before** (§7 — do not drive enough load to scale Polaris to 3 pods on one shared log file). Read one existing stored record raw and report whether `http_status` is a number or a string (§2.4). **Abort loudly on any failure** — a coverage matrix from a half-working pipeline is worse than none. |
| 1 | **Correlation mode** | Send one call with `Polaris-Request-Id: nb-<run>-probe`, poll VictoriaLogs for `mdc.requestId:"nb-<run>-probe"`. Prints **EXACT** or **FALLBACK** and sets the mode every later cell reads. §4.1. |
| 2 | **Denominator** | `fetch_specs.sh` if `spec/` is empty → spec inventory; captured inventory from the newest parsing `doc-api-sql-matrix-*.md`; driven list from `api_surface.operations()`. Diff all three, print the three-way counts. §2.2. |
| 3 | **Happy path** | `setup_fixture()` → `drive()` over the 43 operations, each tagged with its own request id. Dependency order is already `api_surface`'s; it is not re-derived here. |
| 4 | **Negative cases** | 404 (missing table — already an op), 401 (bad secret at the token endpoint), 403 (an unauthorized principal — `authorize_on_fixture` makes this cheap), 409 (concurrent commit, two writers on one table), 400 (malformed body), 405, and **an attempted client-side timeout**, whose expected result is *no record at all* — the blind spot documented rather than assumed. |
| 5 | **Policy probes** | The seven from source-plan §5, each an explicit assertion with an expected count: table GET ×20 → **1**; ±`?snapshots=all` → **2**; missing-table GET ×20 → **20**; HEAD-then-GET → **2**; create-then-delete a principal → **delete only**; successful token → **0**; table LIST ×20 → **20**. Plus two this plan adds: **rename a table → 0 records**, and **reset a principal's credentials → 0 records** (§2.3). |
| 6 | **The grant-body question** | Grant a privilege, then search VictoriaLogs for *any* record carrying the privilege name. Expected: nothing. Then say plainly where it *is* — the `eventListener`'s PostgreSQL `events` table is already modelled in this repo (`api_trace.EVENT_LISTENER_TABLES = {"events"}`, `ASYNC_WRITE_TABLES` — 5s flush [from values]). Query it directly with the existing PG connection and report whether it is the real audit channel. **That answer changes where you go during an incident**, which is the point. |
| 7 | **Collection** | `poll_until` for the whole run by run tag, then per-call by `mdc.requestId`. **Deduplicate by `mdc.requestId` when counting** — source-plan §6: the tail DB is on an `emptyDir`, so a shipper `helm upgrade` legitimately replays records. |
| 8 | **The coverage matrix** | One row per endpoint from cell 2, joined to what cell 7 found, with `expected` from `log_coverage.predict()` (§4.2). Plus every distinct WARN/ERROR message seen, and whether **any** record carried an `exception` object. |
| 9 | **Cleanup** | `teardown_fixture()` + `sweep_instance_principals()`. **The cleanup DELETEs are themselves part of the test** — they are driven inside the tagged run, not after it. Then close the PG connection and `engine.dispose()` per CLAUDE.md. |
| 10 | **Findings** | Renders `doc-log-coverage-results.md`: the seven answers source-plan §8 asks for, the `fluentbit_filter_drop_records_total` delta, a client-side latency table (evidence for adding `%D`), the shipper pod identity before and after, and the `fb-values.yaml` SHA-256 the expected column was computed from. |

---

## 6. Guards this notebook needs that the existing suites do not

- **Do not trip the HPA.** `maxReplicas: 3` at 80% CPU, every replica appending to one
  `polaris.log` (`local-k8s` #8). Cell 5's ×20 loops are the only volume, and they are two orders of
  magnitude below anything that would scale Polaris. Replica count is recorded before and after and
  a change **invalidates the run** — say so in the report rather than quietly reporting the numbers.
- **A shipper restart invalidates the dedup assertions**, not the whole run. Pod name + start time
  before and after; if it moved, cell 5's expected counts are reported as void, not as failures.
- **Never print a token or a client secret.** Notebooks get committed. `api_trace.redact_params()`
  exists for the SQL side; the HTTP side needs the same discipline by hand.
- **Do not change Polaris configuration.** `local-k8s` #11/#12: it works and ships continuously,
  and the `quarkus.log.file.enabled=false` discrepancy is recorded as *unexplained, not pursued*.
  Nothing in this task touches it.
- **Clean up what you create** — and note that a failed run must still leave the cluster usable.

---

## 7. What runs where

The notebook needs the cluster. **A Cowork session has no `kubectl` / `helm` / `docker` reach**
(`local-k8s/.memory/environments.md`), so Claude writes the notebook and the modules and runs their
offline tests; **Kade runs the notebook**, and anything requiring a live cluster is reported
`NOT VERIFIED` until he does. The two port-forwards he will need:

```bash
kubectl -n logging        port-forward svc/vlsingle-victoria-logs-single-server 9428:9428
kubectl -n datahub-hynix  port-forward deploy/fb-polaris-shipper 2020:2020   # metrics only
```

VictoriaLogs is a `LoadBalancer` and may already be reachable without the first.

---

## 8. Decisions needed before building

1. **`src/polaris_rest.py` header change (§4.1)** — additive, but it is a shipped module with many
   call sites. Approve, or should the notebook subclass `PolarisREST` locally instead and leave the
   module alone?
2. **Which 500 to provoke (§2.5)** — `09_500_null_pointer` is the cheapest;
   `23_500_minio_bucket_not_found` is the most realistic. Stack-trace survival is the source plan's
   highest-value unknown, so it is worth picking the one most likely to produce a real throwable.
3. **Vendored specs: gitignored or committed?** This plan says gitignored, with `fetch_specs.sh` and
   `spec/inventory.json` committed. They are ASF-licensed, so committing them is permitted — it is a
   noise judgement, not a licence one.
4. **A one-line clarification in `local-k8s/CLAUDE.md`** — "Management port **8182**" reads as *the
   Polaris Management API*, which is what the source plan spends a paragraph warning against. It
   means the Quarkus management interface. Worth a separate one-line commit in that repo; not part
   of this task.
5. **Roadmap 4b re-scope (§2.3)** — it currently names the create/delete asymmetry. The measured
   count is 8-of-43, including a credential reset. Rewrite it after the run, with the number.

---

## 9. Definition of Done for this task

1. The notebook runs top to bottom from `Restart & Run All` with zero errors — **on Kade's machine,
   against the live cluster**. Until then the tree is marked `NOT VERIFIED: notebook not executed,
   no cluster reach from this session`.
2. `pytest` green, including the new `test_vlogs.py` and `test_log_coverage.py`, both offline.
3. `black . && isort .` (black last — no isort profile is set).
4. `doc-log-coverage-results.md` answers all seven questions in source-plan §8, and says explicitly
   where an answer is missing and why.
5. `MEMORY.md` *Now* updated; the numbers into `.memory/roadmap.md`; anything not to be trusted into
   `.memory/active-issues.md`; the blow-by-blow including the wrong turns into
   `.memory/sessions/<date>-log-coverage.md`.
6. One commit, subject line stating the finding — not the files.
