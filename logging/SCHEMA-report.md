# Report schema reference — v3 tables; v4 deployed 2026-09-15; **v5 deployed 2026-09-16 (running)**; **v6 written 2026-09-16, not rolled** — see the end

Read off `fluent-bit/values.yaml` (`build_report`, ~line 447) on 2026-09-09, not from intent.
Three `report_type` values share one envelope and one `_time`, so `stats by (_time)` — or a terms
agg on `window_start` — groups one window.

## Envelope — on all three row types

| field | type | notes |
|---|---|---|
| `app` | string | `polaris-shipper-report`. In OpenSearch the index already isolates the stream. |
| `level` | string | always `REPORT`. **Severity is meaningless here** — it is a stream selector, not a level. |
| `schema_version` | int | **3** in the file, 2 in everything stored so far. **Always filter it** — three versions will coexist. |
| `report_type` | string | `summary` \| `resource` \| `principal` |
| `report_seq` | int | **per pod.** Resets on pod replacement. Always pair with `hostname`. |
| `hostname` | string | the Fluent Bit pod, not Polaris. |
| `window_start` / `window_end` | string | RFC3339, aligned to the wall-clock `WINDOW_SECONDS` grid. |
| `window_seconds` | int | 30 during the verification band; 1800 in steady state. |
| `_time` | string | **the window's END.** A row with `window_start 05:59:00` carries `_time 05:59:30`. |

## `summary` — one row per window

| field | type | meaning |
|---|---|---|
| `access_seen` | int | access-log lines the filter SAW, **before any keep/drop**. |
| `access_kept` | int | **derived**: `access_seen - access_counted`. Stored redundantly. |
| `access_counted` | int | counted-only — seen, summarised, **not stored individually**. |
| `counted_read` / `counted_post` | int | the counted split by rule 6 / rule 5. |
| `errors_kept` | int | error records kept as individual documents. |
| `parse_errors` | int | recognised as access-log but unparsable. Excluded from the margins. |
| `errors_4xx` / `errors_5xx` / `auth_denied` | int | **summed over `resource` rows only** — the two margins are equal, and doing both would double-count. `auth_denied` (401/403) **overlaps** `errors_4xx` deliberately. |
| `bytes_total` | int | same: summed over resources only. |
| `distinct_resources` / `distinct_principals` | int | **ACTIVE only** (`requests > 0`). Carried rows excluded. |
| `carried_rows` | int | ⚠ **resources AND principals combined** — see review #3. |
| `resources_other` / `principals_other` | int | requests that overflowed the 500 / 200 caps into `__other__`. |
| `resources_other_distinct` | int | distinct keys behind the overflow. |
| `role_keys_forced` | int | **v3.** Role rows created by an **errored** request. Equal to `REPORT_MAX_ROLE_KEYS` (100) means the cap was hit and further denied roles fell to `__other__` unattributed. |
| `windows_skipped` | int | windows that closed with no tick. |
| `min_record_time` / `max_record_time` | string (RFC3339) | **OMITTED when there was no traffic** (2026-09-10) — review #2 fixed. Before that date the Lua wrote `""`, which OpenSearch dynamic-mapped as `text`; indices up to and including `polaris-report-2026.09.10` keep that mapping for their life. New indices are typed `date` by `logging/opensearch/polaris-report-template.json`. |
| `partial_window` | **string** | ⚠ `"true"` / `"false"`, **not a boolean** — see review #1. |
| `_msg` | string | human sentence. |

## `resource` — one row per resource key, per window

| field | type | meaning |
|---|---|---|
| `resource` | string | the matched path span, or `__other__` beyond the cap. |
| `resource_kind` | string | `table` \| `view` \| `collection` \| `namespace` \| `auth` \| `config` \| `transaction` \| `error` \| `other`. **`management` is GONE in v3** — it was an API surface answering a different question and now lives in `api_kind`; `transaction` was added 2026-09-10 for `.../transactions/commit`, the one real path the 63-operation API matrix found unclassified. **v3** added `catalog-role`, `principal-role`, `auth` (`/oauth/tokens`), `config` (`/v1/config`), and rules routing `tables/rename` -> table, `views/rename` -> view, `namespaces/{ns}/properties` -> namespace. These set the **kind only** — `reads`/`writes` still come from the HTTP method, so `POST /properties` is a write. |
| `requests` `reads` `writes` `errors` | int | reads = GET\|HEAD, writes = POST\|PUT\|DELETE\|PATCH, errors = status ≥ 400. ⚠ `errors` **overlaps** reads/writes and the 4xx/5xx split — never sum them together. |
| `errors_4xx` `errors_5xx` `auth_denied` | int | as above; `auth_denied` overlaps `errors_4xx`. |
| `response_bytes` | int | **SUM over the window.** |
| `last_read_bytes` | int | **v3.** Last `GET`/`HEAD` in **this window** with 2xx **and** size > 0. **Absent** if none — never `0`. |
| `last_write_bytes` | int | **v3.** Same for `POST`/`PUT`/`DELETE`/`PATCH`. On a `table` row this is the last successful **commit**: a drop returns 204/empty and falls out, and create is a `collection` row. |
| `_msg` | string | ⚠ does not mention `resources_other` — known gap, rides the 1800/30 revert. |

## `principal` — one row per principal, per window

Identical to `resource` except the key field is `user_principal_name` and there is no
`resource_kind`.

## Invariants worth asserting

```
sum(resource.requests) == sum(principal.requests) == access_seen - parse_errors
count(rows where requests == 0)                   == carried_rows
hi - lo + 1 == n     over report_seq, one hostname, one schema_version
max_record_time - min_record_time  <=  window_seconds
```

---

# Review findings — v2 as deployed

**1. `partial_window` is a string, not a boolean.** `counts.partial and "true" or "false"`.
`{"term":{"partial_window":true}}` will not match; it must be `"true"`. Every other flag-like
value in the schema is an int, so this one reads as a boolean and is not.

**2. `min_record_time` / `max_record_time` default to `""`. FIXED 2026-09-10 — the Lua now omits
the key, and the fault it predicted was measured first: `polaris-report-2026.09.10` mapped
`min_record_time` as `text`, exactly as written below.** If the **first** document written to a
new `polaris-report-*` index carries an empty string, OpenSearch dynamic-maps the field as
**text, permanently for that index** — and no date maths ever works on it. Idle windows produce
exactly that empty string, and a fresh daily index very often opens on an idle window.
**Check the mapping before relying on these two fields**, and prefer omitting the key over writing
`""`. This is the schema's own "absence is not zero" rule, broken in the schema itself.

**3. `carried_rows` merges resources and principals.** `n_carried` is incremented in both loops, so
"how many resources fell to zero" is unanswerable from the summary. `distinct_resources` and
`distinct_principals` are split; their carried counterparts are not.

**3b. `user_principal_name` of `-` is unauthenticated or auth-failed** — the access log's empty
field. It is a real population, not missing data: a sample row carried 9 requests and 1
`auth_denied`. Deliberately **not renamed** — every stored document and existing query uses `-`.

**3a. Grants fold into the role they are granted on.** `classify` returns the **matched span** as
the resource key, so a rule that stops at the role makes everything deeper fold into that role's
row. `/catalogs/{cat}/catalog-roles/{cr}/grants` keys to `/catalogs/{cat}/catalog-roles/{cr}`, and
**`writes` on that row is the number of privileges granted in the window**; `reads` are grant
listings plus role reads. Principal-role rules are ordered first, so
`/principal-roles/{pr}/catalog-roles/{cat}` keys to the *principal* role being assigned to.
**Role kinds are the one exception to the `create=false` guard**: a denied grant creates its own row
rather than falling to `__other__`, capped at `REPORT_MAX_ROLE_KEYS` and counted by
`role_keys_forced`.

**3c. `__other__` is mostly ERRORS, not overflow.** `touch_resource(key, kind, not is_error)` means
an errored request whose resource is not *already* in the window's map gets no row of its own and
lands in `__other__`. Cardinality defence against a 404 scanner — but **4xx/5xx lose their resource
attribution** whenever that resource had no successful request in the same window, and a denied
principal usually has none. `__other__` therefore conflates overflow with unattributed errors.
Unresolved policy question, filed in `PLAN-report-schema-v3` §C.

**4. `errors` deliberately overlaps everything.** It is `status >= 400` regardless of method, so it
overlaps `reads`/`writes`, and `errors_4xx + errors_5xx` overlaps it again, and `auth_denied`
overlaps `errors_4xx`. All intentional and documented — but any dashboard that adds these columns
is wrong, and nothing in the field names says so.

**5. `access_kept` is derived and stored.** Harmless, but it can drift from
`access_seen - access_counted` if anyone ever writes to it directly. Prefer recomputing.

**6. There are TWO synthetic rows, and v3 separates them.**
`__errors__` (`resource_kind: error`) holds errored requests whose resource was not already known —
the attribution is lost, though rule 3 still keeps every one of those records **in full** in
`polaris-logs-*`. `__other__` (`resource_kind: other`) holds only genuine overflow beyond
`REPORT_MAX_RESOURCES`, which is what `resources_other` has always claimed to count. Before v3 both
shared the `__other__` name, and measurement showed the split was 38 errors to 0 overflow — the row
was named after the case that had never occurred. Both carry `api_kind: mixed`, because both
aggregate across API surfaces. Both appear in `distinct_resources`.

**A path no rule matches does NOT go to `__other__`.** It keeps its own row, with its real path as
the key, `resource_kind: other`, and the correct `api_kind`. That is the maintenance signal for a
newly added endpoint — the exact path is visible, not folded away:

```bash
# what needs a classification rule?
curl -sk -u "$OS_USER:$OS_PASSWORD" -H 'Content-Type: application/json' \
  "$OS_URL/polaris-report-*/_search?pretty" -d '{"size":0,"query":{"bool":{"filter":[
     {"term":{"schema_version":3}},{"term":{"resource_kind":"other"}},
     {"range":{"requests":{"gt":0}}}]}},
   "aggs":{"by_api":{"terms":{"field":"api_kind.keyword"},
     "aggs":{"paths":{"terms":{"field":"resource.keyword","size":50}}}}}}'
```
`__errors__` and `__other__` also carry `resource_kind: other`/`error`, so exclude them by name or
read them as the two known synthetic keys.

**7. `bytes_total` is summed over resources only** — by design, since summing both margins would
double-count. It is equal to the principal-side sum by the invariant, so a mismatch there is a
finding, not a rounding difference.

---

# v3 — written, verified, not deployed

Applied to `fluent-bit/values.yaml` on 2026-09-09 and exercised end-to-end through a real Lua
interpreter: `logging/scripts/test-schema-v3.lua`, 16 assertions, all passing. That harness runs the
**deployed script text**, not a retyped copy, and it caught an invalid Lua escape (`%\-`) that would
have failed the whole chunk at load.

See the tables above for the fields. `SCHEMA_VERSION` is 3; `last_read_bytes`, `last_write_bytes`
are in `type_int_key`; `last_write_method` was considered and **dropped** —
the size > 0 rule separates commit from drop without it.

---

# v4 — written 2026-09-15, deployed 2026-09-15 (active-issues #27), verified 2026-09-16

Plan: `logging/PLAN-audit-allowlist-2026-09-15.md`. Script: `fluent-bit/polaris_access_log.lua`, supplied to the chart with `--set-file` (see `fluent-bit/values.yaml`).

| change | field(s) | notes |
|---|---|---|
| new `report_type: app_dropped` | `logger_name` (string), `dropped` (int) | one row per logger with dropped > 0; no zero rows |
| new on `summary` | `app_dropped_total` (int) | |
| new on `resource` rows of kind `table` / `view` | `commit_count`, `commit_ms_sum`, `commit_ms_min`, `commit_ms_max` (int) | from `Successfully committed to table\|view <id> in N ms`; **Iceberg commit time, success only, not request latency**; absent when no commit; mean = `sum(commit_ms_sum)/sum(commit_count)` |
| removed from `summary` | `carried_rows` | zero-carry deleted: a row is emitted only if `requests > 0` or it has commits |

Invariants change: `count(rows where requests == 0) == carried_rows` is gone. A resource row with
`requests: 0` now exists only with `commit_count` (a table changed by `/transactions/commit` only).
`sum(resource.requests) == sum(principal.requests) == access_seen - parse_errors` is unchanged —
commit lines do not touch `requests`. Tests: `test-schema-v3.lua` and `test-schema-v4.lua`, both
passing on LuaJIT and Lua 5.1 against the extracted script.

---

# v5 — written 2026-09-16, rolled and verified the same day (rev 17, window 08:41Z)

Decision (Kade 2026-09-16): **404 is counted, not stored**, and the allow-listed app lines of a 404
request are dropped too, matched by `mdc.requestId`. Proposal §3.9 (Korean) has the rationale.
Script: `fluent-bit/polaris_access_log.lua`, shipped as ConfigMap `polaris-fluent-bit-lua`
(`fluent-bit/kustomization.yaml`), read at pod start — no `--set-file`, no hot reload (removed 2026-09-16);
change it with `bash fluent-bit/apply-lua.sh`.

| change | field(s) | notes |
|---|---|---|
| new on `summary` | `counted_404` (int) | 404 access lines (parsed) counted only. **Included in `access_counted`**, so `access_kept == access_seen - access_counted` still holds. They still count in `errors` / `errors_4xx` on resource and principal rows |
| new on `summary` | `app_dropped_404` (int) | allow-listed INFO app lines dropped because their request answered 404. **Not** in `app_dropped_total` and no `app_dropped` row |
| new on `summary` | `held_orphans` (int) | held app lines whose access line never arrived within `HOLD_MAX_SECONDS` (30) or overflowed `HOLD_MAX_RECORDS` (10000); **stored** with `held_orphan: true` on the detail document |
| new on `summary` | `held_pending` (int) | app lines still held when the window closed. Carries into the next window; a steadily non-zero value with no traffic means orphans are waiting for the next log record to flush |
| new detail field | `held_orphan` (boolean, `polaris-logs-*`) | only on orphans; left to dynamic mapping |
| new resource pattern | `/namespaces/{ns}/register` → `resource_kind: collection` | was `other` / `__errors__` |
| `schema_version` | 5 | |

Behaviour notes:

* Hold only applies to allow-listed INFO lines **with** a request id. WARN/ERROR are kept at once; a
  line with no request id is kept at once (v4 behaviour).
* An app line arriving **after** its access line is decided from a 30 s status memo (`STATUS_MEMO_SECONDS`, max 20000 ids).
* Held lines leave with the access line in one Lua return, so their `@timestamp` becomes the
  access line's (ms later) — orphans take the next record's. The original time stays in `_time`.
* A pod restart (every Lua change) clears all Lua state: window counters (partial next row, `report_seq`
  from 1) **and** held lines.
* Unmeasured for production: whether Polaris assigns `requestId` when the client sends no request-id header.

Invariants added:

```
counted_404 <= errors_4xx                     (per window, summary)
polaris-logs-* holds no http_status 404 access document after the roll
k8s-logs 404 access lines over N whole windows == sum(counted_404)   (boundary lines aside)
```

Tests: `test-schema-v3.lua`, `test-schema-v4.lua` (both now expect `schema_version` 5) and
`test-schema-v5.lua` — all passing on LuaJIT 2.1 and Lua 5.1 on 2026-09-16. Replay preview of the
2026-09-16 matrix window with `step11-replay-window.py`: detail 300 / 32 / 178 → 200 / 22 / 78
(access / PolarisServiceImpl / IcebergExceptionMapper). Template: 4 new `long` fields in
`logging/opensearch/polaris-report-template.json` (41 declared) — re-apply with step9.

---

# v5, refactored — rolled 2026-09-16 (`#31`, `REVIEW-lua-refactor-2026-09-16.md`). No field added, removed or re-typed

`schema_version` stays **5**: every field keeps its meaning. What a reader of the index can notice:

| change | effect on stored rows |
|---|---|
| Access-line parsing moved into `polaris_noise_filter` (one Lua filter instead of two) | none — equal output proven offline (0 diffs on real and fuzz input) and on the cluster (window 15:01Z equals 14:44Z / 08:41Z count for count) |
| **Records before the first tick are now counted** (they were dropped uncounted for up to `Interval_Sec` after every pod start) | the first row after a restart can now carry counts: `partial_window: "true"`, `window_start` is the window the first *record* fell in, and `min_record_time` is later than `window_start`. A partial row is never comparable to a full one |
| `http_status` / `response_size` get their integer type from FILTER 3's `type_int_key` (was FILTER 2's) | none — still JSON integers in `polaris-logs-*`, including access lines released with held app lines |
| Detail docs lose `threadName`, `threadId`, `ndc` (values FILTER 4, `#30`) | `polaris-logs-*` only; not a report-schema change. `polaris-logs-template.json` no longer maps `threadId` |

Tests: `test-schema-v3/v4/v5.lua` now feed raw `_msg` access lines through `logging/scripts/test-raw-access-shim.lua`;
`test-first-tick.lua` covers the start-up counting. All run in `fluent-bit/apply-lua.sh`.

---

# v6 — written 2026-09-16, NOT ROLLED (`active-issues.md` #32, `REVIEW-pipeline-2026-09-16.md` P6/P7/P8)

Decisions (Kade 2026-09-16). **Policy unchanged** — the same records are stored, counted and reported. The document shape changes:

| change | field(s) | notes |
|---|---|---|
| removed from every row | `app`, `level` | constants; the index isolates the stream and `report_type` identifies a report doc. Single-index layout (§5.4 of the proposal) now tells reports apart by `report_type` |
| renamed, summary only | `_msg` → **`message`** | the human sentence stays on `summary` rows |
| removed from `resource` / `principal` / `app_dropped` | `_msg` | it only repeated the numeric fields of the same doc (~25 % of report bytes). The commit min/avg/max text went with it: mean = `sum(commit_ms_sum) / sum(commit_count)` |
| `schema_version` | **6** | v5 and v6 rows share the day of the roll |

Detail index (`polaris-logs-*`), same roll: the raw Polaris line is **`message`** (was `_msg`, value unchanged), no `app`,
`stream`, `flb_tag`. Mappings for indices created after step9/step12 are re-run: undeclared strings are `text` with `index: false`
plus the `.keyword` sub-field (query `.keyword`, never the bare name), `message` / `exception.message` full-text, `client_ip` `ip`.

Tests: `test-schema-v6.lua` (document shape) plus v3/v4/v5/first-tick, all passing on LuaJIT 2.1 against the v6 script;
`logging/candidates/diff-v5-v6.lua`: v5 vs v6 on real and fuzz input, 0 diffs after normalising only the intended changes.
step11 on readouts `084100Z` and `144400Z`: PASS 67×34, detail 200 / 22 / 78.
