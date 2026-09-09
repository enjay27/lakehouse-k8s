# Report schema reference — v2 as deployed, v3 as proposed

Read off `fluent-bit/values.yaml` (`build_report`, ~line 447) on 2026-09-09, not from intent.
Three `report_type` values share one envelope and one `_time`, so `stats by (_time)` — or a terms
agg on `window_start` — groups one window.

## Envelope — on all three row types

| field | type | notes |
|---|---|---|
| `app` | string | `polaris-shipper-report`. In OpenSearch the index already isolates the stream. |
| `level` | string | always `REPORT`. **Severity is meaningless here** — it is a stream selector, not a level. |
| `schema_version` | int | 2 today. **Always filter it.** |
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
| `windows_skipped` | int | windows that closed with no tick. |
| `min_record_time` / `max_record_time` | string | ⚠ default `""`, not absent — see review #2. |
| `partial_window` | **string** | ⚠ `"true"` / `"false"`, **not a boolean** — see review #1. |
| `_msg` | string | human sentence. |

## `resource` — one row per resource key, per window

| field | type | meaning |
|---|---|---|
| `resource` | string | the matched path span, or `__other__` beyond the cap. |
| `resource_kind` | string | `table` \| `view` \| `collection` \| `namespace` \| `other` |
| `requests` `reads` `writes` `errors` | int | reads = GET\|HEAD, writes = POST\|PUT\|DELETE\|PATCH, errors = status ≥ 400. ⚠ `errors` **overlaps** reads/writes and the 4xx/5xx split — never sum them together. |
| `errors_4xx` `errors_5xx` `auth_denied` | int | as above; `auth_denied` overlaps `errors_4xx`. |
| `response_bytes` | int | **SUM over the window.** |
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

**2. `min_record_time` / `max_record_time` default to `""`.** If the **first** document written to a
new `polaris-report-*` index carries an empty string, OpenSearch dynamic-maps the field as
**text, permanently for that index** — and no date maths ever works on it. Idle windows produce
exactly that empty string, and a fresh daily index very often opens on an idle window.
**Check the mapping before relying on these two fields**, and prefer omitting the key over writing
`""`. This is the schema's own "absence is not zero" rule, broken in the schema itself.

**3. `carried_rows` merges resources and principals.** `n_carried` is incremented in both loops, so
"how many resources fell to zero" is unanswerable from the summary. `distinct_resources` and
`distinct_principals` are split; their carried counterparts are not.

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

# v3 — proposed additions

On `resource` rows only:

| field | type | rule |
|---|---|---|
| `last_read_bytes` | int | last GET/HEAD in the window with **2xx** and **size > 0**. Absent if none. |
| `last_write_bytes` | int | last POST/PUT/DELETE/PATCH with **2xx** and **size > 0**. Absent if none. |

Last-wins, per window, **nothing carries forward**. A zero-carry row has both absent. A `0` is
never written, so absence means exactly "no successful non-empty response of that kind this
window".

On a `resource_kind = "table"` row this gives the manager's two numbers directly: `last_write_bytes`
is the last successful **commit** (`DELETE` drops return 204/empty and are excluded; `create` is a
`collection` row), and `last_read_bytes` is the last successful **loadTable** (`HEAD` carries no
body and is excluded).

**Implementation note.** `count_record` builds
`rows = { touch_resource(...), touch_principal(...) }` and updates both in one loop, so the
accumulator will hold these values for principals **for free**. Emitting them on `resource` rows
only is a deliberate choice at `build_report` time, not a limitation — revisit if a per-principal
"last response" is ever wanted.

**Both new fields must be added to `type_int_key`** on both Lua filter blocks, or Fluent Bit
encodes them as doubles and numeric filters silently match nothing.

`SCHEMA_VERSION` becomes **3**, putting three versions in the stream.
