# PLAN — report schema v3: latest response body size per resource

**Status: PROPOSED. Nothing changed.** Three decisions are marked **DECIDE** and the plan should
not be applied until they are answered — each one changes what the number means.

**Requirement (manager, via Kade):** the *latest* response body size for each resource, especially
**table commit** and **get table**.

## 1. What the schema already has, and why it is not the answer

Resource rows carry `response_bytes` — a **sum over the window**. A sum cannot answer "how big was
the last commit response"; a table with 40 reads and one commit reports one number containing both.

What makes this cheap: **commit and get are not different resources.** Both hit
`^.-/namespaces/[^/]+/tables/[^/]+`, so `resource_kind = "table"` with the same resource key. They
differ by **method** — the Lua already splits `READ_METHODS = {GET, HEAD}` from
`WRITE_METHODS = {POST, PUT, DELETE, PATCH}`, and `response_size` is already parsed per record
(`fluent-bit/values.yaml:161`). So the data is in hand at filter time; only the accumulator changes.

Note this holds even though **policy v3 stores no individual record for a successful GET** — it is
*counted only*. The filter still sees it, so the size is capturable. This is the one place the
report can carry information that exists nowhere else, which is exactly why `access_counted` was
worth having.

## 2. Proposed fields on the `resource` row

```
last_read_bytes      last successful-or-not GET/HEAD response size in this window
last_read_status     the HTTP status that produced it
last_write_bytes     last POST/PUT/DELETE/PATCH response size in this window
last_write_status    the HTTP status that produced it
last_write_method    POST | PUT | DELETE | PATCH  -- see DECIDE 2
```

`last_write_method` is what separates a **commit** (`POST` on a table) from a **drop**
(`DELETE`, typically an empty 204). Without it, `last_write_bytes` silently blends them and the
manager's number is sometimes a commit and sometimes a zero-length delete, with nothing to say
which. **Same field for principals** if wanted; the row shapes are parallel. *Not proposed* —
the request is about resources.

## 3. DECIDED (Kade, 2026-09-09) — and the rule set collapses the schema

**Two fields only. No status, no method.**

```
last_read_bytes     last GET/HEAD response size in this window
last_write_bytes    last POST/PUT/DELETE/PATCH response size in this window
```

Sampling rule, applied per record, last-wins:

1. **overwrite on every qualifying request** — no averaging, no first-wins;
2. **2xx only** — an error document's length is not "the response size";
3. **size > 0 only** — and if nothing in the window qualified, **the field is absent**, never `0`.

### Why dropping `last_write_method` is right, not a compromise

I proposed it to stop a commit blending with a drop. **Rule 3 removes that problem at the source**,
and the resource patterns show why:

| on a `resource_kind = "table"` row | verb | body | in `last_write_bytes`? |
|---|---|---|---|
| commit — `POST .../tables/{table}` | POST | table metadata | **yes** |
| drop — `DELETE .../tables/{table}` | DELETE | 204, empty | no — size 0 |
| create — `POST .../tables` | POST | metadata | no — that is `kind = "collection"`, a different row |

So on a table row **`last_write_bytes` *is* the last successful commit**, with no method field
needed. The same rule does the same favour on the read side: `HEAD` (tableExists) carries no body
by definition, so `last_read_bytes` on a table row is the last successful **loadTable**, with HEADs
excluded automatically.

`RESOURCE_PATTERNS` (`fluent-bit/values.yaml:246`) is what makes this hold — create hits the
`tables$` collection pattern, commit hits `tables/[^/]+`. This is read off the repo, not off the
Iceberg spec.

### Why dropping the status fields costs nothing

The worry was distinguishing "no traffic" from "all traffic errored" from "all bodies empty". **The
row already answers that**: it carries `requests`, `reads`, `writes`, `errors`, `errors_4xx`,
`errors_5xx`. So `writes > 0` with `last_write_bytes` absent means every write was an error or
empty-bodied — recoverable from fields that already exist. No new field earns its place.

### Zero-carry rows follow from rule 3, and are hereby decided

A carried row has no requests, so nothing qualifies, so **both fields are absent**. That is
option (a) from the original draft: *absence is not zero*, and "latest ever" stays a query —
sort by `@timestamp` desc, take the first row where the field exists.

### One residue, not a blocker

**"Last" means last-processed.** For a single Polaris pod that equals last-logged, because the tail
reads one file in order. If `#8`'s HPA ever became live, three replicas would write three files and
the DaemonSet would interleave them arbitrarily — "last" would then be ill-defined across replicas.
The HPA currently reports `cpu: <unknown>` and cannot scale, so this is dormant. Worth knowing
before anyone re-enables it.

## 6. Consequences that are not the Lua

- **`SCHEMA_VERSION` 2 -> 3.** There will then be **three** versions in `polaris-report-*`. Trap #4
  in the guide already says an unfiltered aggregation over mixed versions silently reduces sums —
  with v3 that gets worse, not better. **Every consumer query must filter `schema_version`**, and
  `GUIDE-opensearch-notebook.md` §4 needs the new fields before the notebook is written.
- **`type_int_key` must list every new integer field** (`last_read_bytes`, `last_read_status`,
  `last_write_bytes`, `last_write_status`) on *both* Lua filter blocks. Omit one and Fluent Bit
  encodes it as a double — the `404.0` bug that made numeric filters silently match nothing.
  `last_write_method` is a string and must **not** be listed.
- **Sequencing.** The Lua lives in `polaris_access_log.lua`, shared by both releases. Editing it
  breaks byte-identity with `fb-polaris-shipper`. That constraint existed to keep the stdout-vs-file
  comparison valid — **that comparison is banked (265 == 265)**, so it no longer binds. Cleanest
  order is still: uninstall the shipper, then this. If this lands first, the two releases diverge
  and any further shipper comparison is void.
- **Do this BEFORE the new notebook**, which is why the request arrived now. Writing the notebook
  against v2 and then changing the schema means writing it twice.
- **Volume.** Four to five more fields on every resource row, and resource rows are the bulk of the
  report stream. At the temporary 30s window that is ~60x the steady-state row rate — another
  reason the 1800/30 revert should not drift.

## 7. Gates

1. **`schema_version` reads 3 from a stored document**, not from the file.
2. **The margin equality still holds**: `sum(resource.requests) == sum(principal.requests) ==
   access_seen - parse_errors`. Adding fields should not disturb it; run it because "should not" is
   how this week went.
3. **The number is right, checked by hand.** Drive one table commit, find the access-log record for
   it, and confirm `last_write_bytes` on that resource's row **equals the `response_size` on that
   record**. This is the only gate that tests the feature rather than its plumbing, and it can fail.
4. **Carry behaviour matches DECIDE 1.** Drive traffic to a table, then leave it idle one window,
   and confirm the carried row does what was chosen — absent, or carried with its window stamp.
5. `report_seq` continuity unbroken across the change (`hi - lo + 1 == n`, one hostname).

## 8. Not verifiable from a Cowork session
No `helm lint`, no `--dry-run`, no cluster reach. Apply with
`logging/scripts/step5-probe-apply-verify.sh --apply`, which renders, confirms the ConfigMap, rolls,
and confirms the running process.

---

# v3 part 2 — classification, exclusion, and a finding in the sample data

Kade supplied real `resource` rows on 2026-09-09. Three requested changes, one consequence that
must be decided, and **one thing the sample reveals that nobody asked about.**

## A. Paths falling to `resource_kind = "other"`

`RESOURCE_PATTERNS` (`fluent-bit/values.yaml:246`) has no rule for these, so they key on their own
raw path with kind `other`:

| path | requested kind | note |
|---|---|---|
| `/api/catalog/v1/oauth/tokens` | **auth** | 7 requests/window in the sample, all writes |
| `/api/catalog/v1/{cat}/tables/rename` | **table** | Iceberg rename has **no `/namespaces/` segment**, which is why the existing table pattern misses it |
| `/api/catalog/v1/{cat}/views/rename` | **view** | same shape |
| `/api/catalog/v1/{cat}/namespaces/{ns}/properties` | **namespace** | the existing namespace rule is `^.-/namespaces/[^/]+$` — anchored, so `/properties` cannot match it |
| `/api/catalog/v1/config` | **config** *(proposed, not requested)* | 5 requests/window in the sample; leaving it `other` keeps a busy endpoint unclassified |

New patterns, ordered — **`properties` must precede the anchored namespace rule**:

```lua
{ kind = "auth",      pattern = "^.-/oauth/tokens$" },
{ kind = "config",    pattern = "^.-/v1/config$" },
{ kind = "table",     pattern = "^.-/tables/rename$" },
{ kind = "view",      pattern = "^.-/views/rename$" },
{ kind = "namespace", pattern = "^.-/namespaces/[^/]+/properties$" },
```

### DECIDE 4 — "namespace/properties -> namespace **read**"

The request lists rename as *write* and properties as *read*. But the sample row for
`.../probe_ns/properties` shows **`writes: 1, reads: 0`** — it was a POST. So:

- **(a) kind only — recommended.** These rules set `resource_kind`; `reads`/`writes` keep coming
  from the HTTP method exactly as they do for every other resource. A `GET /properties` counts as
  a read, a `POST /properties` as a write, which is what the sample actually shows.
- **(b) force the label.** Classify `properties` as a read regardless of method. This makes the row
  disagree with the request that produced it, and `reads + writes` would no longer reconcile with
  the access log. **Not recommended** — the sample already contradicts it.

If the intent was "a rename is conceptually a write on the table", (a) delivers that for free,
because rename *is* a POST.

## B. DECIDE 5 — excluding `principal-roles`, and the invariant it breaks

Manager: `/api/management/v1/principal-roles/...` rows are not currently required.

**Dropping a resource row silently breaks a documented invariant:**

```
sum(resource.requests) == sum(principal.requests) == access_seen - parse_errors
```

That equality is one of the pipeline's five standing gates. Suppressing rows makes the left side
smaller with nothing to say why, so the gate starts failing on a *correct* config — this week's
recurring shape, deliberately introduced.

Three ways out:

- **(a) Suppress the row at emit, add `excluded_requests` to the summary — recommended.** The
  invariant becomes `sum(resource.requests) + excluded_requests == access_seen - parse_errors`,
  still exact, still checkable, and the excluded volume stays visible instead of vanishing.
- **(b) Route them into `__other__`.** Invariant intact, zero new fields — but `__other__` already
  carries a different meaning (see C) and this would add a third.
- **(c) Suppress and drop the invariant.** Cheapest, and it removes a gate that has caught real
  faults. No.

**Scope question inside this:** suppress only the `resource` row, or also stop counting these
requests toward `principal` rows? If only the resource side is suppressed, the two margins stop
being equal to each other as well. **(a) assumes resource-side only, with the counter making both
sides reconcilable.**

## C. NOT REQUESTED — `__other__` is mostly **errors**, and that is by design

From the sample, unprompted:

| seq | `__other__` requests | errors |
|---|---|---|
| 1758 | 37 | **37** |
| 1747 | 25 | **25** |
| 1748 | 13 | **13** |

Every `__other__` request in these windows is an error. That is not overflow — `REPORT_MAX_RESOURCES`
is 500 and nothing is near it. It is this line:

```lua
local rows = { touch_resource(key, kind, not is_error), touch_principal(user) }
```

`create = not is_error`. **An errored request whose resource is not already in this window's map
does not create a row — it is bucketed into `__other__`.** Sensible as cardinality defence: a 404
scanner cannot explode the report. But the cost is real and undocumented:

**4xx/5xx lose their resource attribution.** "Which table was that 403 on" is unanswerable from the
report whenever that table had no successful request in the same 30s window — and a denied
principal usually has *no* successful requests. The security question the `auth_denied` field was
added for is exactly the one this bucketing erases.

It also means `__other__` currently conflates two unrelated populations: **overflow beyond 500
resources**, and **errors on otherwise-unseen resources**. `resources_other` counts both.

**Not proposed as part of v3** — it is a policy question, not a schema one, and it deserves its own
decision. Options if pursued: allow creation for 4xx/5xx up to a separate smaller cap; or split
`__other__` into `__other__` and `__errors__`; or add `errors_unattributed` to the summary so the
size of the blind spot is at least visible.

## D. `user_principal_name: "-"`

`-` is the access log's empty field: **unauthenticated, or authentication failed.** The sample row
shows it carrying real traffic (9 requests, 1 auth_denied), so it is a meaningful population, not
missing data.

**Recommend documenting rather than renaming.** `-` is what the access log writes and what every
existing query and stored document already uses; renaming it to `__unauthenticated__` would split
the field's history across the rename with no gain. Recorded in `SCHEMA-report.md` instead.

---

# v3 DRY-RUN against real v2 data — 117 rows, seq 1876-1879, 2026-09-09 09:02-09:04

v3's actual rules, extracted from the values file and executed in Lua, run over a real v2 export.
Not a description of what should happen: the rules, on the data.

## The margin invariant holds on every window

| seq | v2 `sum(res)` | v3 `sum(res)` | `excluded_requests` | `seen - parse` | | rows |
|---|---|---|---|---|---|---|
| 1876 | 244 | 239 | 5 | 244 | **EXACT** | 38 -> 34 |
| 1877 | 24 | 21 | 3 | 24 | **EXACT** | 46 -> 40 |
| 1878 | 0 | 0 | 0 | 0 | **EXACT** | 20 -> 17 |
| 1879 | 0 | 0 | 0 | 0 | **EXACT** | 0 -> 0 |

`sum(resource.requests) + excluded_requests == access_seen - parse_errors` on all four. The v2
invariant also held on all four before the change, so nothing regressed.

## 10 rows reclassify, and every one was `other`

`oauth/tokens` -> `auth`, `v1/config` -> `config`, `tables/rename` -> `table`,
`views/rename` -> `view`, `namespaces/{ns}/properties` -> `namespace`. **No row that already had a
real kind changed** — `table`, `view`, `namespace`, `collection` and `management` rows are all
untouched. That is the safety property worth having checked: the new rules are additive over the
`other` bucket and cannot silently re-label existing data.

## ⚠ The exclusion catches more than the rows you showed me — DECIDE 6

13 rows / 8 requests excluded. Beyond the `/principal-roles/{name}` rows in the sample, the pattern
`^.-/principal%-roles/` also removes:

```
/api/management/v1/principal-roles/{pr}/catalog-roles/{cat}    grants of a catalog role
/api/management/v1/principal-roles/{pr}/principals             who holds this role
```

Defensible — they are principal-role administration. But they were **not** what the manager pointed
at, and the second is arguably the security-relevant one.

**And it does NOT exclude** the mirror-image path, which is present in this data:

```
/api/management/v1/principals/{p}/principal-roles              roles held by a principal
```

because the pattern requires a `/` *after* `principal-roles`. A bare
`/api/management/v1/principal-roles` collection listing would also survive, for the same reason.

So the current rule excludes **sub-resources of a principal-role** but keeps **a principal's role
list**. That may be exactly right — or exactly backwards. It needs a decision, and it is invisible
unless someone runs the rule over real paths, which is why this dry-run exists.

## Finding C, confirmed on real data

`__other__` in the busy window: **37 requests, 37 errors, 37 4xx, 1 denied** — and 24 of them were
reads. Every single `__other__` request was an error, exactly as `touch_resource(key, kind, not
is_error)` predicts. The one auth-denied request in that window has **no resource attribution at
all**. v3 does not change this and was not asked to.

## Two things this data corrects in `SCHEMA-report.md`

**`min_record_time`/`max_record_time` are ABSENT on idle windows here, not `""`.** VictoriaLogs
does not store empty values, so the `""` the Lua writes never lands. **That is a property of the
sink, not of the pipeline** — OpenSearch *will* store the empty string and dynamic-map the field as
**text**, permanently for that index. So v2's clean behaviour in VictoriaLogs gives false
confidence about the OpenSearch tier, and the mapping must be checked there:

```bash
curl -sk -u "$OS_USER:$OS_PASSWORD" "$OS_URL/polaris-report-*/_mapping/field/min_record_time?pretty"
```

**`resource_kind` has a `management` value that is not in `RESOURCE_PATTERNS`** — `classify` falls
back to `if path:find(MGMT_PREFIX) then return path, "management"`. The reference table listed it;
the mechanism is worth knowing before anyone adds a management rule to the pattern list and wonders
why it never fires.

---

# SUPERSEDES DECIDE 5 and DECIDE 6 — authorization folding

Kade, 2026-09-09: *don't exclude principal-roles; summarise all role requests in an authorization
row — read, write, error counts for total requests — and the same for catalog-roles grant-privilege
requests.*

**This is a better design than the one it replaces, and it deletes machinery.** Excluding needed a
new summary field (`excluded_requests`) and a modified margin invariant, purely to stop a standing
gate failing on a correct config. Folding needs neither: the requests stay in a resource row, so

```
sum(resource.requests) == sum(principal.requests) == access_seen - parse_errors
```

is unchanged from v2. `EXCLUDED_PATTERNS`, `is_excluded` and `excluded_requests` are **removed**.

## The rule

`classify` checks first: any path containing `/principal-roles`, `/catalog-roles` or `/grants`
returns the single key `__authorization__` with `resource_kind = "authorization"`.

**Measured on the real v2 export: 16 distinct paths, 80 requests, collapse into 1 row** — the
principal-role CRUD, the catalog-role CRUD, the grants endpoints, and both directions of the
principal↔role join. The DECIDE 6 asymmetry disappears with it: `/principals/{p}/principal-roles`
and `/principal-roles/{pr}/principals` now both fold, because the rule matches the segment
anywhere rather than requiring a trailing slash.

## The one non-obvious part

`touch_resource(key, kind, create)` takes `create = not is_error`, so an errored request whose
resource is not already known lands in `__other__`. For `__authorization__` that guard is both
pointless and harmful — it is **one bounded key**, so it cannot inflate cardinality, and **a denied
grant is exactly what an authorization row exists to record.** v3 forces `create = true` for this
key alone. Measured on real data, every `__other__` request in the busy window was an error,
including that window's only `auth_denied` — which is the attribution this fixes.

## Verified

`logging/scripts/test-schema-v3.lua`, 24 assertions, all passing against the deployed script text:
the fold captures 5 role/grant requests as reads 2 / writes 3 / errors 1 / auth_denied 1; a plain
`/principals/{p}` stays `management`; the denial does **not** appear in `__other__`; and both
margin invariants are exact with no `excluded_requests` field present.

## Reconstructed v3 rows from the real v2 export — and what the reconstruction cannot show

Re-aggregating the 104 v2 resource rows under v3's keys, busiest window (seq 1876, 244 requests):

| kind | resource | req | rd | wr | err | denied | bytes |
|---|---|---|---|---|---|---|---|
| **authorization** | `__authorization__` | **73** | 33 | 40 | 0* | 0* | 188,541 |
| table | `…/namespaces/probe_ns/tables/probe_tbl` | 47 | 38 | 9 | 10 | 10 | 76,124 |
| other | `__other__` | 37 | 24 | 13 | **37** | 1 | 5,715 |
| collection | `…/namespaces/probe_ns/tables` | 25 | 21 | 4 | 1 | 0 | 4,913 |
| management | `/api/management/v1/catalogs` | 8 | 3 | 5 | 0 | 0 | 1,181,599 |
| auth | `/api/catalog/v1/oauth/tokens` | 7 | 0 | 7 | 1 | 1 | 4,796 |

**Authorization is the single largest row — 73 of 244 requests, 30% of the traffic.** Worth knowing
before anyone treats it as a minor category.

Row counts fall: **38 -> 26** (seq 1876) and **46 -> 31** (seq 1877). Margin invariant **EXACT** on
every window.

### \* Two things this reconstruction cannot show, and both understate v3

1. **`last_read_bytes` / `last_write_bytes` are absent.** The export carries per-window *sums*, not
   individual records, so a "last" value cannot be derived from it. Those fields need a live run.
2. **The authorization row's errors read 0, and that is an artefact of v2, not a prediction.** In
   v2 an errored authz request fell into `__other__` under the `create=false` guard, and an
   aggregate row cannot be split back out. `__other__` in this window holds **37 errors and 1
   auth_denied** — some of which are authz. Under real v3 those move into `__authorization__`.
   **So the live authz row will show more errors and denials than the table above** — which is
   precisely the blind spot the forced-create change exists to close.

---

# ROLLED BACK: no `__authorization__` fold. Grants key to their catalog role.

Kade, 2026-09-09: *roll this back so I can see which role was granted what on which catalog;
instead summarise privilege requests per catalog role.*

The fold is removed. `AUTHZ_PATTERNS`, `is_authz`, the `__authorization__` key and the forced-create
special case are all gone.

## The mechanism — no new machinery at all

`classify` already returns the **matched span** as the resource key. So a rule that stops at the
role makes everything deeper fold into that role's row automatically, exactly as the existing table
rule folds sub-paths into a table:

```lua
{ kind = "principal-role", pattern = "^.-/principal%-roles/[^/]+" },
{ kind = "collection",     pattern = "^.-/principal%-roles$" },
{ kind = "catalog-role",   pattern = "^.-/catalog%-roles/[^/]+" },
{ kind = "collection",     pattern = "^.-/catalog%-roles$" },
```

**`writes` on a `catalog-role` row is the number of privileges granted in that window.** `reads` are
grant listings plus reads of the role itself. Principal-role rules are ordered first so
`/principal-roles/{pr}/catalog-roles/{cat}` keys to the **principal** role being assigned to, not to
the catalog role.

## Measured on the real export

| kind | resource | req | rd | wr | err | bytes |
|---|---|---|---|---|---|---|
| **catalog-role** | `…/catalog-roles/{id}_shared` | **51** | 25 | **26** | 0 | 16,205 |
| principal-role | `/principal-roles/{id}_pr` | 5 | 2 | 3 | 1 | 475 |
| collection | `…/catalog-roles` | 5 | 3 | 2 | 0 | 1,109 |
| collection | `/principal-roles` | 4 | 1 | 3 | 0 | 170,972 |
| catalog-role | `…/catalog-roles/catalog_admin` | 4 | 2 | 2 | 0 | 304 |
| catalog-role | `…/catalog-roles/{id}_cr` | 4 | 2 | 2 | 0 | 74 |
| principal-role | `/principal-roles/{id}_prole` | 2 | 0 | 2 | 0 | 0 |
| | **total role traffic** | **80** | 35 | 45 | 1 | 189,139 |

The `_shared` catalog role is the one the manager is describing: **51 requests on it, of which 26
were writes — the privilege grants — and 25 were listings.** Same 80 requests as the fold covered,
now attributable per role.

## ⚠ The cost of rolling back, and it is real

The fold made `__authorization__` the one key that bypassed `create=false`, so a **denied** grant
was recorded there. Per-role keys cannot take that shortcut — the guard exists to stop a client
walking invented role names from filling the key space, and role names are now unbounded input.

So with the rollback: **a 403 on a catalog role that had no successful request in the same 30s
window lands in `__other__`, with no role attribution.** "Which role was granted what" is now
answerable; **"which role was DENIED what" is not**, unless that role also succeeded at something
in the same window.

That is finding C (`§C`) landing squarely on the case the manager cares about. Options, none applied:

- allow creation for `catalog-role` / `principal-role` kinds only, capped separately — bounded by
  the number of real roles, and these are the security-relevant rows;
- split `__other__` into `__other__` and `__errors_unattributed__` so the blind spot is at least
  measurable;
- leave it, and read denials from the individual records in `polaris-logs-*`, which rule 3 keeps in
  full.

## Verified

`test-schema-v3.lua`, 26 assertions, all passing: three grants plus one CRUD read on one catalog
role give `requests 4 / writes 3 / reads 1`, `last_write_bytes` is the last grant, no separate
`/grants` row exists, a second catalog role is a separate row, the assignment path keys to the
principal role, no `__authorization__` row remains, and both margin invariants are exact.

---

# Option 1 applied, and what is left in `other` / `management`

## Denied grants keep their role row

`ROLE_KINDS = { catalog-role, principal-role }` may create a row on an **error**, under
`REPORT_MAX_ROLE_KEYS = 100` — its own cap, because role names are unbounded client input and that
is exactly what `create=false` defends against. `role_keys_forced` on the summary counts rows
created this way, so **hitting the cap is visible rather than a silent truncation**. Verified:
a 403 on a catalog role with no successful request in the window keeps its own row with
`auth_denied 1`, does not appear in `__other__`, and increments `role_keys_forced`.

## v3 traffic by kind, whole export (268 requests)

| kind | req | share |
|---|---|---|
| catalog-role | 59 | 22.0% |
| collection | 57 | 21.3% |
| table | 52 | 19.4% |
| **other** | **38** | **14.2%** |
| management | 30 | 11.2% |
| principal-role | 8 | 3.0% |
| namespace / auth / config / view | 24 | 8.9% |

## `other` is now ONLY `__other__` — and it is 100% errors

**38 requests, 38 errors.** Every path that used to sit in `other` with its own raw key is now
classified; there is no unclassified *surface* left. What remains in `other` is entirely traffic
that **lost its key** to the `create=false` guard. So no new `RESOURCE_PATTERNS` rule would move
the needle — the only lever on this 14.2% is the guard itself, and option 1 has just taken the
role-shaped slice of it. The rest is 404s and 4xx on tables and namespaces that had no successful
request in the same 30s window.

## `management` is two families, and both are legitimately not roles

| resource | req | rd | wr | err | bytes |
|---|---|---|---|---|---|
| `MG/catalogs` | 8 | 3 | 5 | 0 | **1,181,599** |
| `MG/principals` | 7 | 3 | 4 | 0 | **536,175** |
| `MG/catalogs/{id}stale` | 5 | 1 | 4 | 3 | 944 |
| `MG/principals/{id}_p` | 3 | 1 | 2 | 1 | 298 |
| `MG/catalogs/{id}_cat` | 3 | 2 | 1 | 0 | 1,068 |
| `MG/principals/{id}_asym/reset` | 1 | 0 | 1 | 0 | 271 |
| *(3 more principal rows)* | 3 | 0 | 3 | 0 | 0 |

Catalogs and principals are **identity and containers**, not authorization, so leaving them as
`management` is right. Two observations worth acting on separately:

- **The two collection endpoints are by far the heaviest responses in the export** — 1.18 MB over
  8 requests (~148 KB each) and 536 KB over 7. That is 91% of the export's total response bytes in
  15 requests. `last_read_bytes` will now show this per window, which may be the most actionable
  new signal in v3 outside tables.
- **A cosmetic asymmetry, not proposed:** a catalog-role is `catalog-role` but a catalog is
  `management`. Giving catalogs and principals their own kinds (`catalog`, `principal`) would be
  consistent — but `management` is still accurate, and renaming a kind splits query history. Left
  alone unless asked.
