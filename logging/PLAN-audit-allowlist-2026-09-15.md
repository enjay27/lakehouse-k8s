# PLAN — tier 2 audit stream: application logs by ALLOW-LIST, commit time on table rows, no zero rows

**Status: WRITTEN 2026-09-15 into `fluent-bit/values.yaml`, NOT ROLLED (`active-issues #27`).** D1–D3 settled. Kade, 2026-09-15: *"in the audit log part, all I need to store
is clients' behaviour trends and issue tracking — make it a whitelist, so initialization-catalog,
federated-iceberg-table … are not stored any longer."* Also: the `summary` report is not needed
(→ D1: kept, ignored), commit time wanted per table (→ D2), rows with exactly 0 requests not wanted (→ D3).

Evidence: two OpenSearch exports from run `1789436277`, 2026-09-15 10:37:30–10:42:00 KST
(`…export_2026-09-15-4.csv` = `polaris-logs-*`, 759 docs; `…-2.csv` = `polaris-report-*`, 221 rows,
resource + principal only). **Test matrix traffic, error-heavy, ~4 minutes** — it names the loggers
that exist, it does not size production. Nothing in either file was confirmed against the running
ConfigMap; the Lua quoted below is `fluent-bit/values.yaml` at `1724475`.

---

## 1. What the audit stream holds today, and why

`polaris_noise_filter` rule 2 — `if record["loggerName"] ~= ACCESS_LOGGER then return 0` — keeps
**every non-access record untouched**. Rules 3–6 already make the *access* stream selective; the
*application* stream is a block-list with nothing on it.

| level | loggerName | docs | what it is | verdict |
|---|---|---:|---|---|
| INFO | `io.quarkus.http.access-log` | 343 | access lines surviving rules 3–5 | **unchanged** (rules 3–6 stay) |
| INFO | `…service.exception.IcebergExceptionMapper` | 176 | `Handling runtimeException <reason>` — *why* a 4xx/5xx | **ALLOW** — issue tracking |
| ERROR | `…service.exception.IcebergExceptionMapper` | 4 | `Unhandled exception returning INTERNAL_SERVER_ERROR` + `exception.*` | kept by rule 1 anyway |
| INFO | `…service.admin.PolarisServiceImpl` | 75 | `Adding/Revoking grant`, `Created new catalog/principal/principalRole/catalogRole`, `Assigning/Revoking …Role` | **ALLOW** — who changed what |
| INFO | `…catalog.iceberg.IcebergCatalogHandler` | 61 | `Initializing non-federated catalog` (59), `Catalog type:`, `allow external catalog credential vending:` | drop |
| INFO | `org.apache.iceberg.BaseMetastoreCatalog` | 37 | `Table properties set/enforced …: {}`, `Table loaded by catalog` | drop |
| INFO | `org.apache.iceberg.CatalogUtil` | 30 | `Loading custom FileIO implementation` | drop |
| INFO | `…catalog.iceberg.IcebergCatalog` | 24 | `Refreshing table … from new version` (12), `Successfully committed to table/view … in N ms` (12) | drop — **the commit lines are harvested into table/view rows first, §2.4** |
| INFO | `org.apache.iceberg.view.BaseMetastoreViewCatalog` | 6 | `View properties set/enforced …: {}` | drop |
| INFO | `…config.PolarisIcebergObjectMapperCustomizer` | 3 | `Limiting request body size to N bytes` (startup) | drop |

**Effect on this export: 161 of 759 docs dropped (21%), ~10% of `_msg` bytes.** The saving is modest
because this run is 45% access lines and 24% exception reasons, both of which stay. In production —
2xx reads dominating, every one already counted-not-stored — the dropped loggers are a
per-request constant (`Initializing non-federated catalog` fires on ~every catalog call), so the
share grows with traffic. **No DEBUG line appears in the export** (§9 #1 of the retention proposal
is not visible here); the allow-list removes it regardless, whatever its logger.

### Measured: the allow-list orphans nothing

Every doc carries `mdc.requestId` (0 blanks). **100% of the kept `PolarisServiceImpl` and
`IcebergExceptionMapper` docs join to a stored access line on `mdc.requestId`**; the dropped loggers
join 0–54%, the rest belonging to reads/catalog POSTs that are counted, not stored. So the join
*access line (who, status) ⇄ reason / mutation detail (why, what)* survives intact — and it is the
answer to the fact that `PolarisServiceImpl` messages name the grantee but **not the caller**.

### Checked: credentials in `Created new principal`

The message dumps `PrincipalWithCredentials { credentials { clientId, clientSecret } }`. All four
occurrences print `clientSecret: *` — masked by Polaris. Keeping this logger is safe **as long as
that masking holds**; §3 step 4 adds a guard rather than trusting it.

---

## 2. Design

### 2.1 Rule 2 becomes an allow-list (by logger, not by message)

```lua
-- Tunables
local APP_ALLOW = {
  ["org.apache.polaris.service.exception.IcebergExceptionMapper"] = true,  -- why it failed
  ["org.apache.polaris.service.admin.PolarisServiceImpl"]         = true,  -- who/what changed
}

-- 1. level ERROR or WARN ............ keep            (unchanged — never allow-listed)
-- 2. not an access-log record:
--      loggerName in APP_ALLOW ...... keep
--      otherwise .................... count by logger, DROP
-- 3–6 unchanged
```

**Why logger-level, not message-prefix.** `PolarisServiceImpl` is the admin-API audit class and is
low-volume by nature (75 lines in this run, one per mutation). A prefix list (`Adding grant`, `Created
new`, …) would silently drop the first message it does not know — e.g. an `Updating`/`Deleting`
line a Polaris upgrade adds. Note there is **no delete/update line today**: 25 successful DELETEs
produced none. Those mutations are audited by the access line (rule 4), which is why rule 4 must
not be touched by this change.

**Why WARN/ERROR stay outside the list.** An allow-list's failure mode is the unknown logger. A new
WARN is exactly what issue tracking must not lose, and WARN/ERROR volume is not the problem.

### 2.2 Dropped is counted, not vanished

The pipeline's one invariant is *not stored ⇒ counted*. Rule 2's drop would break it, and an
allow-list without a counter cannot tell "Polaris renamed the logger" from "nothing happened".

Add a per-window table `dropped_app[loggerName] = n` and emit it on the tick as
`report_type: app_dropped`, **one row per logger with n > 0** (no zero-carry — this is a health
signal, not a trend). ~5 rows/window at most. If D1 drops the `summary`, this row is also the only
place a lost audit logger can surface: **a new `org.apache.polaris.service.*` logger appearing here
is the review trigger for the list.**

Fields: envelope as §4.4 of the retention proposal + `logger_name` (keyword), `dropped` (long),
`level_seen` (keyword, highest level in the window — always INFO/DEBUG by construction).
`dropped` joins `type_int_key` on filter 3 — **a numeric field missing there stores as a string**.

### 2.3 The summary row — D1: KEEP, ignore in dashboards

The export has no `summary` rows because it was filtered out of it — the running Lua still emits one
per window (`base("summary")`). Dropping it costs:

- **the only invariant that proves the report is complete**:
  `sum(resource.requests) == sum(principal.requests) == access_seen - parse_errors`
  (`GUIDE-schema-v3-testing.md` §76; `access_seen`/`parse_errors` exist nowhere else);
- `windows_skipped`, `resources_other*`, `principals_other`, `role_keys_forced` — the cap and
  tick-loss counters that say whether a resource/principal trend is truncated;
- **the `#26` re-verification** (MEMORY.md *Next* (1)–(2)) reads `access_kept` from it.

Its storage cost is ~48 docs/day at 1800s. **Decided: leave it emitted, hide it from dashboards**
with `NOT report_type:summary`. Its one change in v4 is losing `carried_rows` (§2.5).

### 2.4 Commit time on table and view rows — D2

**What the number is.** `Successfully committed to table|view <id> in N ms` is logged by
`IcebergCatalog` after the Iceberg commit succeeds: metadata-file write plus the metastore
compare-and-swap. It is **not request latency** — auth, parsing, response are outside it — and a
failed commit (409, CommitFailed) logs nothing, so it is **success-only**. Named `commit_ms_*` so no
dashboard reads it as request latency. True request duration needs `%D` in Quarkus's
access-log pattern, a Polaris change, which the standing rule forbids — not in scope.

**Join by the identifier in the message, not by `mdc.requestId`.** In the export 0 of 12 commit lines
has a stored access line with its request id — successful catalog POSTs are counted, not stored —
so a request-id join would need a per-request buffer. The message names the object instead, and
the name maps onto the row key `classify()` already builds:

```
Successfully committed to table apimatrix…_cat.probe_ns.probe_tbl in 20 ms
  → /api/catalog/v1/apimatrix…_cat/namespaces/probe_ns/tables/probe_tbl        (kind table)
Successfully committed to view  apimatrix…_cat.probe_ns.mx_…_vw2  in 32 ms
  → /api/catalog/v1/apimatrix…_cat/namespaces/probe_ns/views/mx_…_vw2          (kind view)
```

Split: first `.`-segment = catalog (Polaris's URL prefix *is* the catalog name — true in every
export row), last = object, middle = namespace. That also credits a **multi-table
`/transactions/commit`** to each table it changed, which the request id could not do (that access
line keys to the transaction row).

**The unverified step — test before it ships.** A multi-level namespace `a.b` is `.`-joined in the
message but `%1F`-joined in the URL, so the middle segments join with `%1F`. Names needing
percent-encoding in a URL differ the same way. Neither occurs in the export. A mismatch does not
fail: it quietly creates a second row, under the same key shape, that no request ever lands on.
**Test case required: `a.b` namespace, and a table name with a `-`.**

**Statistics — four fields, resource rows of kind `table`/`view` only:**

| field | type | meaning |
|---|---|---|
| `commit_count` | long | successful commits in the window |
| `commit_ms_sum` | long | sum of N |
| `commit_ms_min` | long | minimum N |
| `commit_ms_max` | long | maximum N |

- **No stored average.** Averages do not aggregate: a day's mean is
  `sum(commit_ms_sum) / sum(commit_count)`, never the mean of 48 window means.
  `min`/`max` do aggregate (min of mins, max of maxes).
- **No percentiles.** They need histogram buckets in Lua, and at a few commits per table per window a
  p95 is just the max.
- **Alert on the mean, not `commit_ms_max` alone.** The run's two largest values (1,373 ms, 1,101 ms)
  were the **first** table and first view commit — cold-start shaped.
- **Absent, not 0**, when the window had no commit — same rule as `last_write_bytes`.
- Mechanics: the commit line is matched in rule 2 **before** the allow-list decision, feeds
  `touch_resource(key, kind, "catalog", create=true)` (a successful commit proves the object exists,
  so `create=true` is right, and the 500-row cap still applies), then falls through to the drop and
  is counted in `app_dropped` like any other non-allowed line — so G2 stays one simple equality.
- `requests`/`reads`/`writes` are **not** touched by a commit line: those stay access-line counts, so
  `sum(resource.requests) == access_seen - parse_errors` is unchanged.
- The resource row's `_msg` gains `, commits N (min/avg/max a/b/c ms)` when `commit_count` is set.

### 2.5 No rows with nothing in them — D3

A resource or principal row is emitted only if **`requests > 0` or `commit_count` is set**. The
second half exists because of §2.4: a table changed only through `/transactions/commit` has commits
but `requests: 0` on its own row, and must not vanish.

Done by **deleting zero-carry**, not by filtering at emit: `carry_res`/`carry_pri`/`carry_api`,
`new_window`'s carry loops and `n_carried` go. Less state in the filter, and a row with
`requests: 0` can then arise only from §2.4.

Consequences, accepted:

- **A fall to zero is a gap, not a 0.** Dashboard line charts must render missing buckets as zero;
  a "principal went silent" alert is a *no-documents* query, not `requests == 0`.
- `carried_rows` leaves the summary, `type_int_key` and the template — a removed field, part of the
  same v4 bump.
- `distinct_resources` keeps meaning `requests > 0`; a commit-only row is not counted in it.
- Every invariant is unaffected: the removed rows contributed 0 to every sum.

---

## 3. Change set (when approved)

| # | file | change |
|---|---|---|
| 1 | `fluent-bit/values.yaml` — Lua `polaris_noise_filter` | `APP_ALLOW` table; rule 2 → allow-or-count-and-drop; header comment rules 1–7 rewritten |
| 2 | same — Lua report tick | `dropped_app` in `new_window`; `app_dropped` rows emitted in the tick; `SCHEMA_VERSION` 3 → **4** (new `report_type` value, removed `carried_rows`) |
| 2a | same — Lua | §2.4: commit-line match + identifier→key (`%1F` join) before rule 2's decision; `commit_count/ms_sum/ms_min/ms_max` in `new_row`, emitted on table/view rows when set; `_msg` suffix |
| 2b | same — Lua | §2.5: delete zero-carry (`carry_*`, `n_carried`, `carried_rows`); emit condition `requests > 0 or commit_count` |
| 3 | same — filter 3 `type_int_key` | add `dropped commit_count commit_ms_sum commit_ms_min commit_ms_max`; remove `carried_rows` |
| 4 | same — Lua | **credential guard**: if a kept record's `_msg` matches `clientSecret:%s*[^%s*]` (anything but the mask), replace the value with `<redacted>` and set `secret_redacted=true`. Cheap, and it stops a masking regression landing in a 30-day index |
| 5 | `logging/scripts/test-polaris-filters.py`, `test-schema-v3.lua` | cases: allowed logger kept; unknown INFO dropped + counted; unknown WARN kept; mask regression redacted; commit on known table → stats on that row; **`a.b` namespace → `%1F` key equal to the access path's key**; view commit → view row; transaction-only table → row with `requests 0` + commits emitted; idle key → no row next window |
| 6 | `logging/opensearch/polaris-report-template.json` | `logger_name` keyword; `dropped`, `commit_*` long; `carried_rows` removed — **after** the Lua is rolled (`#25` order) |
| 7 | `logging/PROPOSAL-polaris-audit-log-retention.ko.md` §3.5–3.6 | rule 2 text; drop table gets the six loggers; §9 #1 status |
| 8 | `SCHEMA-report.md`, `.memory/active-issues.md`, MEMORY.md *Now* | v4, the allow-list as a watched item |

No Polaris change (standing rule). No change to `kube.*` / `k8s-logs` — the unfiltered copy stays,
and it is what step 5's subset proof compares against.

## 4. Order against what is already queued

1. **Finish `#26` first** (notebook lag fix → Gate 2 re-drive). This plan changes `access_kept`'s
   neighbours and the schema version; landing it mid-verification muddies the one open gate.
2. Lua v4 (steps 1–5), render gate, roll.
3. Template (step 6) — one change with `#25`'s date fix, same `step9` script.
4. 1800/30 revert.
5. D1, if removal is chosen.

## 5. Verification (Kade runs; nothing here was run)

`helm lint` + `--dry-run=client --debug` on the DaemonSet release, then on live traffic:

| gate | pass | a 0-hit result means |
|---|---|---|
| G1 | in `polaris-logs-*` after roll: `terms loggerName.keyword` ⊆ {access-log, the 2 allowed} ∪ {any WARN/ERROR} | **not a pass** if the window had no traffic — check `access_kept > 0` |
| G2 | over ≥10 whole windows (not one — `#26`'s 3.673s edge moves boundary lines): `k8s-logs` count of Polaris INFO non-access docs from other loggers == `sum(app_dropped.dropped)` ± edge lines | the counter or the `kube.*` copy is broken |
| G3 | every kept `PolarisServiceImpl`/`IcebergExceptionMapper` doc has an access doc with the same `mdc.requestId.keyword` (the 100% measured above) | a join key was lost |
| G4 | `_msg:*clientSecret*` in `polaris-logs-*` → only `*` or `<redacted>` | — |
| G5 | `schema_version: 4` on every new report row; `dropped`, `commit_*` mapped `long`; no `carried_rows` | — |
| G6 | over a range: `sum(commit_count)` on table+view rows == `k8s-logs` count of `Successfully committed to` lines ± edge | a key mismatch or a missed pattern |
| G7 | no two resource rows in one window whose keys differ only by `.` vs `%1F`; every row with `commit_count` and `requests: 0` has a `/transactions/commit` row with `writes > 0` in that window | §2.4's mapping is creating phantom rows |
| G8 | no report row with `requests: 0` and no `commit_count` | zero-carry was not fully removed |

## 6. Decisions — settled 2026-09-15

- **D1 — summary.** Keep emitting; dashboards filter `NOT report_type:summary`. (§2.3)
- **D2 — commit time.** Harvest `Successfully committed to table|view` into the row as
  `commit_count / commit_ms_sum / commit_ms_min / commit_ms_max`; mean at query time; success-only
  commit time, not request latency; no percentiles. (§2.4)
- **D3 — zero rows.** Emit a row only if `requests > 0` or it has commits; zero-carry deleted,
  `carried_rows` removed. (§2.5)

Still open: nothing in the design. **Execution waits for an explicit go** (plan-first) and, per §4,
for `#26` / Gate 2 to finish.
