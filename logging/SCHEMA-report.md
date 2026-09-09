# Report schema reference — v3 (written, not yet deployed)

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
| `excluded_requests` | int | **v3.** Requests whose resource row was suppressed by `EXCLUDED_PATTERNS` (currently `/principal-roles/`). They still count toward `principal` rows. |
| `windows_skipped` | int | windows that closed with no tick. |
| `min_record_time` / `max_record_time` | string | ⚠ default `""`, not absent — see review #2. |
| `partial_window` | **string** | ⚠ `"true"` / `"false"`, **not a boolean** — see review #1. |
| `_msg` | string | human sentence. |

## `resource` — one row per resource key, per window

| field | type | meaning |
|---|---|---|
| `resource` | string | the matched path span, or `__other__` beyond the cap. |
| `resource_kind` | string | `table` \| `view` \| `collection` \| `namespace` \| `auth` \| `config` \| `management` \| `other`. **v3** added `auth` (`/oauth/tokens`), `config` (`/v1/config`), and rules routing `tables/rename` -> table, `views/rename` -> view, `namespaces/{ns}/properties` -> namespace. These set the **kind only** — `reads`/`writes` still come from the HTTP method, so `POST /properties` is a write. |
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
sum(resource.requests) + excluded_requests == access_seen - parse_errors   # v3
sum(principal.requests)                    == access_seen - parse_errors
count(rows where requests == 0)                   == carried_rows
hi - lo + 1 == n     over report_seq, one hostname, one schema_version
max_record_time - min_record_time  <=  window_seconds
```

---

# Review findings — v2 as deployed

**1. `partial_window` is a string, not a boolean.** `counts.partial and "true" or "false"`.
`{"term":{"partial_window":true}}` will not match; it must be `"true"`. Every other flag-like
value in the schema is an int, so this one reads as a boolean and is not.

**2. `min_record_time` / `max_record_time` default to `""`.** If the **first** document written to a
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

**6. `__other__` is a real row, not just a counter.** Beyond 500 resources the overflow lands in a
row keyed `__other__` with `resource_kind = "other"`, so it appears in `distinct_resources` and in
per-resource aggregations. `resources_other` counts the requests behind it.

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
and `excluded_requests` are in `type_int_key`; `last_write_method` was considered and **dropped** —
the size > 0 rule separates commit from drop without it.
