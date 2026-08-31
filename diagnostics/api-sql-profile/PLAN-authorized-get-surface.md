# PLAN — the FULL GET surface, driven by a fully-authorized principal

Written 2026-08-24, after the Pass A correlation. **Nothing has been modified** —
`CLAUDE.md`'s Strict Plan-First rule applies. Decisions taken with Kade:
small privileged sub-fixture, all 29 GET/HEAD operations including the Polaris
extensions, one harness with two identity profiles.

---

## 0. Answering the question directly: no, it does not cover all GET APIs

The completed scan drives **13 operations**. The 1.3.0 spec defines **29
GET/HEAD operations** across the two services. So the suite covers **45%** of
the readable surface, and the report should never have implied otherwise —
§5 fixes that wording too.

### What is covered, and what is not

**Management service — 13 GET operations, 9 driven, 4 missing.**

| operation | in suite |
|---|---|
| `listCatalogs`, `getCatalog` | yes |
| `listPrincipals`, `getPrincipal` | yes |
| `listPrincipalRoles`, `getPrincipalRole` | yes |
| `listAssigneePrincipalsForPrincipalRole` | yes |
| `listCatalogRoles`, `listGrantsForCatalogRole` | yes |
| **`listPrincipalRolesAssigned`** `/principals/{p}/principal-roles` | **no** |
| **`listCatalogRolesForPrincipalRole`** `/principal-roles/{pr}/catalog-roles/{c}` | **no** |
| **`getCatalogRole`** `/catalogs/{c}/catalog-roles/{cr}` | **no** |
| **`listAssigneePrincipalRolesForCatalogRole`** `/catalogs/{c}/catalog-roles/{cr}/principal-roles` | **no** |

The four missing ones are exactly the **role-graph traversals** — principal →
principal-role → catalog-role. That is the shape of the authorization model
itself, and it is the part of the surface most likely to touch
`grant_records` more than once. Leaving it out is not a rounding error in
coverage; it omits the queries closest to the thing under audit.

**Iceberg catalog service — 11 GET/HEAD, 4 driven, 7 missing.**

| operation | in suite |
|---|---|
| `listNamespaces`, `loadNamespaceMetadata` | yes |
| `listTables`, `listViews` | yes — **but see §0.1** |
| **`getConfig`** `GET /v1/config` | **no** |
| **`loadTable`** `/namespaces/{ns}/tables/{t}` | **no** |
| **`loadView`** `/namespaces/{ns}/views/{v}` | **no** |
| **`loadCredentials`** `/tables/{t}/credentials` | **no** |
| **`namespaceExists`** (HEAD), **`tableExists`** (HEAD), **`viewExists`** (HEAD) | **no** |

**Polaris extensions — 5 GET, 0 driven.** `listGenericTables`,
`loadGenericTable`, `listPolicies`, `loadPolicy`, `getApplicablePolicies`.
Feature-flagged in 1.3 — §2.3.

### 0.1 The two collection endpoints that ARE driven were driven EMPTY

`capture/seed_ledger.json` records `create_tables: False`. The fixture has
1,000 catalogs × 2 namespaces and **zero tables, zero views**.

So `GET /namespaces/{ns}/tables` and `.../views` answered 200 with an empty
list, 1,000 times each. Their measured 8.00 statements/request is the cost of
listing **nothing**. A listing that returns rows may issue more; it certainly
does not issue fewer. Two of the four Iceberg operations in the current report
are therefore measured at a volume the fixture cannot produce, and that has to
be said out loud in the existing report, not only fixed in the next one.

It is also why `loadTable`, `headTable`, `loadView` and `loadCredentials` are
not merely untested but **undriveable today**: there is no table to load.

---

## 1. The framing correction: this is not an "unauthorized" suite

Worth being precise, because the naming decides what the two reports claim.

The completed run is **not** an unauthorized principal. It is a
**catalog-scoped** principal — `user{N}_principal`, holding `owner_principal`
on its own catalog and nothing at service level. It got **8,000 × 200 and
6,000 × 403**: a majority of its requests succeeded. "Unauthorized" describes
six of its thirteen operations, not the identity.

There are three identity tiers here and they measure different things:

| tier | grants resolved | what it is |
|---|---|---|
| **root** | ~2 rows | the LEAST representative identity in the realm |
| **catalog-scoped** (`user{N}`) | ~50 rows | today's suite |
| **service-scoped** (new) | must be ~50 rows — §3.2 | the new suite |

`api_sweep.bind_identity`'s docstring already records why this matters: Seq Scan
cost is flat regardless of how many rows the grantee owns, while index-scan cost
tracks rows **returned**. So grant-set size barely moves the index-absent column
and dominates the index-present one — which is why 02 measured ~100x for a small
grantee and single digits for a large one.

**Consequence for this plan, and it is the single most important design
constraint in it:** if the fully-authorized principal is granted service access
and little else, it will resolve a handful of rows, and its numbers will not be
comparable to the catalog-scoped suite's. The privileged principal must carry a
**comparable grant footprint** — measured with
`api_sweep.identity_grant_footprint`, not assumed — or the two suites are
measuring two different points on a curve and the diff between them is
meaningless.

**Do not use root for this.** Root is authorized for everything and resolves
two rows; a suite built on it would sweep the whole surface and report the
least representative identity in the realm as if it were typical.

---

## 2. The full surface, and how it gets enumerated

### 2.1 Enumerate from the LIVE server, not from this document

The inventory in §0 comes from the 1.3.0 spec on GitHub. That makes it a
**transcription**, and this repo has a scar for exactly that: the 25-privilege
retraction, where `CATALOG_PRIVILEGES` was transcribed from the spec and a
rejected name cost 1,000 rows and read as a Polaris behaviour. `MEMORY` states
the rule — *a constant inferred rather than asked for is a hypothesis*.

So step one of the build is `probe_openapi.py`: fetch the running server's own
OpenAPI document, extract every GET and HEAD path, and **diff it against the op
list the harness drives**. The diff is a permanent artifact: any operation in
the server and not in the harness is printed as a coverage gap, every run. That
turns "does this cover everything?" from a question someone has to ask into
something the runner answers itself.

If the server does not serve a spec document, fall back to the spec files
pinned at the deployed version and record in the report that the surface was
transcribed rather than probed.

### 2.2 Op definitions live in ONE place, as they already do

`api_sweep.read_operations` is the single definition of the surface, and
`query_profile.operation_templates()` already derives URL templates from it by
driving a real `PolarisREST` against a recorder. Both properties must survive:

- new operations go into **`api_sweep`**, as `full_read_operations(fx)`,
  beside the existing 13 — not into a second list in the scan module;
- `polaris_rest` / `iceberg_rest` gain the client methods they lack, so
  templates keep coming from the client rather than a string in the harness.

`src/iceberg_rest.py` already has `get_config`, `head_namespace`, `load_table`,
`head_table`, `load_view`, `head_view` — six of the seven missing Iceberg ops
need **no new client code at all**, only wiring into the op list.
`loadCredentials` and the five Polaris-extension GETs are new client methods.

### 2.3 Feature-flagged endpoints get probed, not assumed

Generic tables and policies are gated by feature flags in 1.3. They may answer
404 or 501 on this deployment. That is a **measured fact worth reporting**, not
a reason to leave them out or a failure — the existing `--probe` mechanism
already classifies an op by what it actually returns, and the same rule applies:
13 calls settle what would otherwise be an assumption baked into thousands of
requests.

The report states, per operation: driven / refused (403) / unavailable
(404-501) / undriveable (no such entity in the fixture).

---

## 3. The privileged sub-fixture

### 3.1 Shape

**~50 principals**, `authz{N}_principal`, each with:

- its own catalog, 2 namespaces (matching the existing fixture's shape);
- **real tables and views** — 5 tables + 2 views per namespace, so `listTables`
  returns rows, and `loadTable` / `headTable` / `loadCredentials` have a target;
- policies and generic tables **if §2.3's probe says the features are on**;
- a **service-scoped principal-role** carrying `SERVICE_MANAGE_ACCESS` (§3.3);
- a catalog-role grant footprint **tuned to match the catalog-scoped tier**.

50 × (1 catalog + 2 ns + 10 tables + 4 views) ≈ 850 new entities and a few
thousand `grant_records`. Against 55,004 that is a small perturbation — but it
IS a perturbation, so: **re-count `grant_records` after seeding and quote the
new number.** The Pass A capture already taken describes the 55,004 state and
must keep saying 55,004.

### 3.2 The footprint must be measured, not designed

After seeding, before driving:

```
python3 scan_privileges.py --footprint --prefix authz --sample 50
```

`api_sweep.identity_grant_footprint` reports the real distribution. If the
privileged tier's p50 differs materially from the catalog-scoped tier's, either
tune the grant count and re-measure, or **state both footprints in the report
and stop claiming the two suites are directly comparable**. Both are honest;
silently comparing them is not.

### 3.3 "Fully authorized" is a hypothesis until probed

The repo's privilege constants include `SERVICE_MANAGE_ACCESS` and
`PRINCIPAL_ROLE_USAGE`; there is no `PRINCIPAL_LIST_*` style privilege in the
list. The plausible mechanism is `SERVICE_MANAGE_ACCESS` granted on the root
container to the principal's principal-role, which should open the six
service-level reads that 403 today.

**Plausible is not measured.** So:

1. `seed_polaris.py --probe-privileges` — which privilege names does this build
   actually accept? (This is the step whose absence caused the 25-privilege
   retraction.)
2. Provision one `authz1_principal`, then run `--probe --prefix authz` — all 29
   operations, once, statuses recorded.
3. **The pass/fail gate:** if any operation still 403s, the principal is not
   fully authorized and the grant set is wrong. Fix it before driving 50 × 29.
   A suite named "fully authorized" that quietly contains 403s is the same
   error as a 403 in a column headed "ms".

The probe result is written to disk exactly as `privscan_probe.json` is today,
so the report can state which operations were in the denominator.

---

## 4. The build

One harness, two profiles. **No existing behaviour changes** — the
catalog-scoped path must keep producing byte-identical results, since Pass A's
capture is already correlated against it.

### 4.1 `src/privilege_scan.py` — add a profile, change no default

```python
PROFILES = {
    "catalog-scoped": Profile(prefix="user",  ops=api_sweep.read_operations),
    "service-scoped": Profile(prefix="authz", ops=api_sweep.full_read_operations),
}
```

`load_identities` already takes `prefix`. `drive` already takes `ops_for`.
The profile is a named bundle of what the two runs already parameterise
separately — nothing in the driver needs to change.

### 4.2 `src/api_sweep.py` — `full_read_operations(fx)`

The 29, in spec order, each bound to the fixture. Additive; `read_operations`
is untouched so the existing tests, notebooks 01/02/02b/02c and the Pass A
correlation all keep working.

### 4.3 `src/polaris_rest.py` / `src/iceberg_rest.py` — the missing methods

Management: `list_principal_roles_assigned`, `list_catalog_roles_for_principal_role`,
`get_catalog_role`, `list_assignee_principal_roles_for_catalog_role`.
Iceberg: `load_credentials`.
Polaris extensions: `list_generic_tables`, `load_generic_table`, `list_policies`,
`load_policy`, `get_applicable_policies`.

Ten methods, all GET, all thin — and each one is what keeps
`operation_templates()` deriving paths from the client instead of a string
literal in the harness.

### 4.4 `src/query_profile.py` — HEAD, and a coverage diff

- `operation_templates()` records the method already, so HEAD needs only that
  the recorder accept `head` (it does).
- **new** `coverage_gap(templates, server_paths)` → operations the server
  exposes that the harness does not drive. Rendered in every report.

### 4.5 Tests

Mirroring the existing style, mocked, no live cluster: every one of the 29 gets
a template; every one round-trips concrete → label; HEAD and GET on the same
path do not collide; the coverage diff reports a missing op; a profile change
does not alter `read_operations`' 13.

---

## 5. Correcting the existing report

Two sentences, in `doc-privilege-query-performance-20260824-123408.md`, under
"What this pass does not establish":

- it covers **13 of 29** GET/HEAD operations — 45% of the readable surface,
  and the four missing management ops are the role-graph traversals;
- `listTables` and `listViews` were driven against a fixture with
  `create_tables: False`, so their per-request statement counts are the cost of
  listing an **empty** collection.

Both are corrections to what that report implies about its own scope, and they
land before anyone quotes it.

---

## 6. Order of work

```
0.  probe_openapi.py                  the server's own GET/HEAD list; diff vs harness
1.  seed_polaris.py --probe-privileges     which privilege names this build accepts
2.  build full_read_operations + the 10 client methods + tests   (offline, no cluster)
3.  seed the ~50 authz principals WITH tables/views; re-count grant_records
4.  scan_privileges.py --footprint --prefix authz    compare to the user tier
5.  scan_privileges.py --probe --profile service-scoped
        GATE: any 403 here means not fully authorized. Stop and fix.
6.  capture.sh rotate capture-authz-noindex
    scan_privileges.py --drive --profile service-scoped --capture capture-authz-noindex
7.  profile_queries.py --capture capture-authz-noindex --run <id> --explain --report
```

Cost at step 6: 50 identities × 29 ops ≈ **1,450 requests + 50 tokens**. An
order of magnitude smaller than the 15,000-request catalog-scoped pass, because
the variable being swept here is the **surface**, not the identity count. If a
per-identity distribution across the full surface is wanted later, the same
harness scales by raising the fixture.

---

## 7. Definition of done

- Every one of the 29 operations classified: driven / refused / unavailable /
  undriveable — none silently absent.
- `coverage_gap` printed in the report, and empty.
- Both identity tiers' grant footprints measured and stated; comparability
  claimed only if they match.
- The probe gate passed with zero 403s, or the suite renamed to what it is.
- `grant_records` re-counted after seeding; the new figure quoted, and the
  existing Pass A report still saying 55,004.
- Existing report corrected per §5.
- `black`/`isort`/`pytest` green — **black last** (isort profile still unset).
- `MEMORY.md` updated.

---

## 8. Decisions still open

1. **Sign off §4's shape** — additive `full_read_operations` + 10 client
   methods + a profile enum, with `read_operations` frozen.
2. **50 principals, or fewer/more?** 50 is chosen to keep the fixture
   perturbation small against 55,004 while giving a distribution rather than a
   single probe. Say if you want a different n.
3. **`loadCredentials`** vends storage credentials. It is a GET and it is on
   the surface, but it touches credential vending and MinIO rather than only
   the metastore. Include it in the sweep, or record it as deliberately
   out-of-scope? (The privilege matrix work already notes credential-vending as
   a separate gate.)
4. **The index-present passes.** This adds a second fixture, so the
   Seq→Index contrast now has two suites to run it against. Do both, or
   establish the contrast on the catalog-scoped suite only and use the
   service-scoped one purely for coverage?
