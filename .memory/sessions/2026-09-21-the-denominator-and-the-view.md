# 2026-09-21 (session 17) — the denominator moved, the fixture had no view, and phase I was never tagged

Started as a review of `log-coverage/polaris_api_traffic_v1.ipynb` against Kade's OpenSearch export
for run `1789950539` (report `seq=238`, window `00:29:30Z`–`00:30:00Z`, 61 report docs + 281 log
docs). It turned into six commits, and the first finding was in this repo's own bookkeeping rather
than in Polaris.

## The export reconciles exactly, and that is worth saying first

Four independent identities close on run `1789950539`, with no slack:

- `auth_denied = 107` = the notebook's own 59×401 + 48×403.
- `errors_4xx = 235` = 101×404 + 59 + 48 + 19×400 + 8×409.
- `errors_5xx = 7` = 4 grid 500s + 3 ladder 500s. Runner carries 6, `-` carries 1 (`getToken` has
  no bearer, so no principal).
- `access_seen = 337` = Σ principal requests = Σ resource requests (276 real + 61 `__errors__`).

`access_kept` (186) and `access_counted` (151 = 30 read + 20 POST + 101 404) **partition** the 337 —
they are not nested, and the summary sentence "337 access lines, 186 kept, 151 counted" reads as if
they were. `polaris-logs-*` holds exactly 186 access docs for the window, which confirms the
partition from the other side. `errors_kept` 141 = 242 − 101: the 404s are counted, never kept.

**Gate 2's positive half is answered.** `probe_tbl`'s resource row carries `last_write_bytes = 1941`,
byte-identical to what the client recorded for `nb-1789950539-3001-gate2-the-commit`. The negative
half leaves the field **absent**, not `0`, on the 204 — so a gate asserting `== 0` VOIDs a third
time. That is the shape to assert.

## Part 1 — the denominator moved 19 minutes after the run, and nothing on disk knew

`load_spec('log-coverage/spec')` answers **65 operations / 297 cells** today. The run printed
**63 / 286**. The difference is exactly `registerView` and `signRequest` (+6 and +5 cells).

`spec/*.y*ml` have mtime `2026-09-21 01:00`; the run finished `00:29:41`. `fetch_specs.sh` carried an
uncommitted bump, `apache-polaris-1.3.0-incubating` → `apache-polaris-1.6.0`, while its header still
said "Vendor the Apache Polaris 1.3.0 OpenAPI documents". `spec/inventory.json` — the one file
`.gitignore` deliberately keeps in that directory, and the designated durable record — **did not
exist**. The only surviving trace of the 63/286 grid was cell 8's printed output inside the
uncommitted `.ipynb`, which is why that notebook was committed first.

**THE RE-FETCH HAD ALREADY BROKEN THE SUITE AND WOULD HAVE STOPPED THE NEXT DRIVE AT CALL 0.**
`registerView` and `signRequest` carry a `requestBody` and had no `PAYLOADS` entry, so `request_for`
raised `KeyError` — 8 tests red, and cell 8's dry run builds all 297 requests before any is issued.
The guard the notebook advertises would have fired; nobody had run it.

Landed: `spec_fingerprint` / `read_inventory` / `inventory_drift` / `assert_denominator` /
`write_inventory` in `api_status_matrix`; `inventory.json` written with the 1.3.0 fingerprint pushed
onto its `history` (shas `null`, because the bytes are gone and guessing them would be worse than
admitting it); `fetch_specs.sh` writes the inventory itself; cell 8 hard-fails on drift.

### Two wrong turns here, both corrected by Kade

1. **I read the mtimes and the default tag and concluded `spec/` had been 1.6.0 all along** — so the
   run had measured a 1.6.0 *denominator* against a 1.3.0 *server*. Exactly backwards. The documents
   were overwritten AFTER the run.
2. **I recommended restoring the 1.3.0 spec** so the next run would stay comparable with
   `1789950539`. Wrong premise: Kade had upgraded the cluster on **2026-09-18 17:33 KST** (helm
   revision 9, chart `benchmarks-polaris-1.6.0`). The 1.6.0 documents are the RIGHT denominator and
   were already in place. Nothing to restore.

The reason I got both wrong is the same reason the run is mislabelled: **`init_env` prints
`polaris_version` out of `src/config/<env>.yaml`, and nothing measures the server.** The run's banner
says `Polaris 1.3.0` on a cluster that had been 1.6.0 for three days, so every output of
`1789950539` carries a version label that is a stale config string. Config updated to 1.6.0 and
marked as a label; cell 8 now warns when it disagrees with the inventory.

**This also re-reads the 500 ladder.** `black_hole_endpoint` PROVOKED 3/3, where on 2026-09-07 every
rung answered 4xx. That is not a mystery about "this build" — it is a 1.3.0 → 1.6.0 difference, and
`errors_5xx` is now deliberately exercisable.

## Part 2 — the fixture never built its view

`api_surface.setup_fixture` creates the catalog, the grant, both namespaces and the table, and no
view. The grid binds `fx.view` into eleven cells. Run `1789950539` paid eight times: `loadView`,
`viewExists`, `replaceView` MISSED at 2xx with 404, the same three at 403 with 404, and `replaceView`
again at 409 and 400. Every one printed as a status Polaris returned. **The teardown said so in the
same run — `drop view probe_view 404` — and nothing read it.**

The reason it was missing is real: `api_surface.operations()` creates `c.view` itself as a measured
operation, so a fixture that pre-built it would 409 the sweep that `diagnostics/api-sql-profile` and
`make_traffic` drive. The sweep now uses a disposable view (`probe_view2` → `probe_view3`), exactly as
it already used `probe_tbl2` → `probe_tbl3` beside it. `build_view_payload` is module-level so both
paths build one shape — two spellings of that payload is how a view came to exist on one path and not
the other.

## Part 3 — phase I was never tagged, on any run

Section 11 has always claimed the cleanup DELETEs ARE the test. In `1789950539` not one carried
`nb-<run>-…`: **19 of the 186 kept access lines** went out with a Quarkus id
(`a8fdbd69-…_0000000000000000224`), plus every 404ing attempt. The ladder had the same hole on both
sides of its rungs — `POST /api/management/v1/catalogs` and the 400 on `DELETE
/api/management/v1/catalogs/nb1789950539bh` were untagged, so the catalog the ladder leaks could not
be tied to the ladder from the log.

`tag_around` + `TEARDOWN_IDS`, and section 13 now prints `ISSUED` per phase with the complete set of
request ids. **The ids are the check and the count is not** — a total can agree by accident. The
fixture setup is excluded on purpose: it runs before section 3b's single wait and lands in an
earlier window. This is what makes `access_seen == issued` assertable in `local-k8s`.

## Part 4 — two catalogs leaked from every run and both cleanups reported success

`delete catalog apimatrix1789950539_cat 400` and `delete catalog nb1789950539bh 400`, both printed,
neither read. Two deterministic causes, and **neither is the `createNamespace` 500 that "COMMITTED
anyway"** which the teardown comment blames:

- `authorize_on_fixture` creates the catalog role `{prefix}_shared` INSIDE the fixture catalog, and
  the teardown deleted three catalog roles by name, none of them that one. Polaris refuses to delete
  a catalog holding a catalog role. `shared_role_name(fx)` puts the name in one place.
- Every ladder rung's cleanup deleted a catalog whose namespace was still in it. Polaris answered
  400 and `except Exception: pass` never fired, **because a 400 is a response, not an exception**.
  `drop_catalog_tree` empties first and returns every status; `ladder[i]["cleanup"]["leaked"]` is
  the flag, and section 11 prints CATALOGS LEFT ON THE CLUSTER.

## Part 5 — phase B renamed away what phase D's 409 cells needed

`renameTable`/`renameView` took `new_table`/`new_view` as their source, in phase B, at their 2xx
cells. By phase D the thing `createTable` and `createView` were meant to conflict with had been
moved. `createView missed [409] got {409: 200}` is the tell: it SUCCEEDED, because the name was free.
Neither cell could have passed behind any build. They now move their own `rename_table`/`rename_view`,
created in setup.

Still MISSED for unrelated reasons and not to be confused with this: `updateTable` 409/400 (the
commit carries no stale requirement), `dropNamespace` 409 (needs a non-empty namespace),
`commitTransaction` 409.

## What the export says about the report that is NOT this repo's to fix

- **`__errors__` holds 61 of 337 lines (18%).** From the kept half alone, 46 have paths with no
  resource row, in six shapes: `…/catalog-roles/<r>/grants`, `…/namespaces/<ns>/register`,
  `…/tables/<t>/credentials`, `…/tables/<t>/metrics`, `…/principals/<p>/reset`,
  `…/principals/<p>/rotate`, plus `…/principal-roles/<pr>/catalog-roles/<cat>` and
  `…/principal-roles/<pr>/principals`. **The asymmetry is the finding:** the 7 non-error lines on
  those shapes fold into the parent row; the error lines on the same shapes fall to `__errors__`.
  That is the mechanism behind the old `writes=3 / auth_denied=0` confusion — window attribution was
  only half of it. Roughly 9 of the 65 operations produce error traffic that cannot be attributed to
  a resource.
- **rung 1's design claim is CONFIRMED.** `/nb1789950539bh/namespaces` got a clean row (1 write, 0
  errors) and `/namespaces/bh_ns/tables` got no row at all, with all three 500s in `__errors__`.
  Only the bucket's name in the docstring was wrong: `__errors__`, not `__other__` —
  `resources_other` was 0.
- **`renameTable`/`renameView` 400 → 500 is an event-listener fault, not validation.** The app log
  shows `PolarisEventListeners ERROR … BEFORE_RENAME_TABLE … listener 'persistence-in-memory-buffer'
  (InMemoryBuffer…)` 0.4 ms before each `IcebergExceptionMapper` 500. On 1.6.0. Worth reporting
  upstream; the notebook records it only as "MISS got 500".
- Report-side labelling: `distinct_resources = 52` counts `__errors__` (51 real);
  `app_dropped_404 = 111` exceeds `app_dropped_total = 74`, so they cannot both mean "app lines
  dropped"; the summary's `141 errors kept (235 4xx, 7 5xx, 107 denied)` prints the 242 population
  as if it broke down the 141.

## Next

1. **Run it.** Every change here is unverified against the cluster. Expect: the eight view cells
   become measurements, the two 409 cells can conflict, phase I appears under `nb-<run>-9xxx`, and
   section 11 prints either "teardown left nothing behind" or a named leak.
2. **`registerView` and `signRequest` have never been driven.** Both are pointed at deliberate dead
   ends. Their first real statuses are new information.
3. **Use `GET /v1/config`'s `endpoints` list as the reachability oracle.** The Iceberg 1.11.0 spec
   defines it, and it would replace the guesswork about scan planning: in `1789950539` all four
   scan-planning operations answered 404 **even at their 401 cells**, i.e. the router 404s before
   authentication, so the route is absent. `loadView` etc. answered a correct 401, which is what
   separated a missing route from a missing fixture. A `401 → 404` cell is a route-absent signature;
   the `endpoints` list would make it a fact rather than an inference.
4. `src/api_report.py:307` still hardcodes `polaris_version="1.3.0-incubating"`.

Verified: `pytest` 939 passed / 45 skipped at every commit (VM venv outside the repo — the repo's
`.venv` points at the Mac's Python). `black`/`isort` clean on every file touched. **Nothing in this
session was run against the cluster.**
