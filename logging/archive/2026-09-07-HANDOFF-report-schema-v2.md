# HANDOFF — nine changes to the flush report's schema, and why two of them are corrections

**Status: IMPLEMENTED AND DEPLOYED 2026-09-07**, minus `top_error_path`. The running
ConfigMap carries this script (sha256 `d58b9203a8304030`, confirmed by the notebook's own
gate) and run `1788755035` measured it end to end — every margin exact, including the new
fields' own. The harness has not caught up: `2026-09-07-HANDOFF-harness-schema-v2.md`. Results at the foot of
this document; the decisions and their reasoning are in
[`.memory/sessions/2026-09-07-report-schema-v2.md`](../../.memory/sessions/2026-09-07-report-schema-v2.md).
Step 1 of the repo's plan-first protocol; step 2 is Kade's confirmation. Written 2026-09-07 to
be read cold in a new session.

**Scope: the report schema only.** Policy v3 — the keep/count rules — is not touched by any of
this and is not in question. Three runs verified it end to end; see the companion document.

**Read alongside** [`2026-09-07-HANDOFF-polaris-log-coverage.md`](2026-09-07-HANDOFF-polaris-log-coverage.md),
which owns the three *operational* items (revert the fast-run settings, the stack-trace
correction, the volume mix) and the list of what is settled about the filter. This document
owns the *schema*. They share one `helm upgrade` — see §Sequencing.

**Status markers.** **[verified]** observed in a real record or a running object.
**[from source]** read out of the deployed `fb-values.yaml`. **[assumed]** not checked.

**How this was produced, and its limits.** Every line number and every claim about what the
filter computes is **[from source]** — `logging/fb-values.yaml`, sha256 `063c184df3f9f475`,
read directly. The live behaviour is **[verified]** from a report-stream tail Kade pasted on
2026-09-07 (seq 327–335, windows `02:31:30Z`–`02:36:00Z`), and from run `1788748008`'s results
document. **No `kubectl`, `helm` or Lua interpreter was run** — a Cowork session has no cluster
reach and the bridge VM has no Lua. Nothing below has been executed; it has been read.

---

## 0. The evidence, in nine lines

This is the tail that produced most of what follows. Read it before the sections.

```
seq=335 02:35:30Z..02:36:00Z: 0 access lines, 0 kept, 0 counted (0 GET, 0 POST), 0 errors kept, 0 resources, 0 principals
seq=334 02:35:00Z..02:35:30Z: 0 access lines, 0 kept, 0 counted (0 GET, 0 POST), 0 errors kept, 2 resources, 2 principals
        principal watchdog-principal: 0 requests, 0 reads, 0 writes, 0 errors
        principal -: 0 requests, 0 reads, 0 writes, 0 errors
        resource /api/catalog/v1/oauth/tokens (other): 0 requests, ...
        resource __other__ (other): 0 requests, ...
seq=333 02:34:30Z..02:35:00Z: 3 access lines, 2 kept, 1 counted (0 GET, 1 POST), 2 errors kept, 3 resources, 3 principals
        principal watchdog-principal: 2 requests, 2 reads, 0 writes, 2 errors
        principal root: 0 requests, 0 reads, 0 writes, 0 errors
        principal -: 1 requests, 0 reads, 1 writes, 0 errors
        resource /api/catalog/v1/oauth/tokens (other): 1 requests, 0 reads, 1 writes, 0 errors
        resource __other__ (other): 2 requests, 2 reads, 0 writes, 2 errors
        resource /api/management/v1/principals (management): 0 requests, ...
seq=332 02:34:00Z..02:34:30Z: 4 access lines, 3 kept, 1 counted (0 GET, 1 POST), 2 errors kept, 3 resources, 2 principals
```

The margins are exact in every window (`seq=333`: resources 1+2+0 = 3, principals 2+0+1 = 3,
`access_seen` 3). Zero-carry and decay behave. **The schema's self-check passes and the schema
still misreports two things and cannot answer three questions.** That is what this is about.

---

## 1. Two fields are wrong — these are corrections, not additions

### 1.1 `distinct_resources` / `distinct_principals` count carried zeros

**[from source]** `new_window` (lines 274–280) increments the counters for every carried key:

```lua
for key, kind in pairs(carry_res or {}) do
    w.resources[key] = new_row(); w.kinds[key] = kind
    w.n_resources = w.n_resources + 1
end
```

and `build_report` reports them verbatim (lines 395–396):

```lua
s.distinct_resources  = counts.n_resources
s.distinct_principals = counts.n_principals
```

**[verified]** `seq=334` — *zero* access lines, **2 resources, 2 principals**.

A window that saw no traffic at all reports two distinct resources. Any "resources touched per
window" panel grows a phantom one-window tail after every burst and never reads zero on the
window following activity. The number is not a count of resources touched; it is a count of
rows emitted, and the field name promises the first.

**Change:** count rows with `requests > 0`. Add **`carried_rows`** as its own field so
zero-carry stays visible without polluting the cardinality number. Roughly:

```lua
local n_active_res, n_carried = 0, 0
for _, r in pairs(counts.resources) do
    if r.requests > 0 then n_active_res = n_active_res + 1 else n_carried = n_carried + 1 end
end
```

— computed in the loop `build_report` already runs at line 412, so it costs nothing extra.

**This also removes a disagreement between the filter and the oracle.** The test repo's
`PLAN-log-coverage-v3.md` §11b states `distinct_resources` is "recomputed as a union, never
summed, and a carried zero row does not create a key." The harness and the shipper therefore
compute this field by **different rules today**, which is a latent diff mismatch. Whichever way
this is decided, both sides must move together.

### 1.2 `counted_get` counts HEAD as well

**[from source]** line 527 sits inside the `READ_METHODS` branch:

```lua
if READ_METHODS[method] then
    if counts ~= nil then
        counts.counted_get    = counts.counted_get + 1
```

`READ_METHODS` is GET **and** HEAD, and the summary message (lines 402–407) prints the number
as `(%d GET, %d POST)`. Run `1788748008` drove five HEADs; all five were reported as GET.

**Change:** rename to **`counted_read`**, and print it as `read`. Or, if the rename is not
wanted, add `counted_head` alongside and leave the misnomer documented. The rename is cleaner
and this is the upgrade to do it in — see §4.

---

## 2. Three questions the summary cannot answer, and each one has come up

### 2.1 `errors` cannot distinguish a 404 from a 500

**[from source]** `errors_kept` is one integer (line 393); per-row `errors` is one integer,
incremented at line 353's `is_error = (status == nil or status >= 400)`.

**[verified]** `seq=332` and `seq=333` each report **2 errors kept**, and neither says what
kind. Run `1788748008` had two real unhandled 500s (`iceberg.create_namespace`,
`iceberg.create_view`, both with ~60-frame stack traces) sitting in the same undifferentiated
integer as routine 404s for tables that do not exist.

A 404 is traffic. A 500 is an incident. An alert cannot be written against a field that mixes
them, which is an odd place to end up for a report whose entire justification is that
individual successful reads no longer exist.

**Change**, on the summary and on every resource/principal row:

| field | |
|---|---|
| `errors_4xx` | client errors — expected volume |
| `errors_5xx` | server errors — the alertable one |
| `auth_denied` | 401 + 403 specifically — the security question, today buried under 404s |

`status` is already in hand at the counting site (`count_record`, line 353). Three comparisons.
`errors` stays as the total, so nothing that reads it breaks.

### 2.2 A skipped window is silent in the stream

**[from source]** `report_tick` (line 453) computes `idx` from the clock, reports
`counts.window`, and opens `new_window(idx)`. Intermediate indices are **never built**. So
`report_seq` increments by exactly **1** across a gap of any size, and any records that arrived
during the gap were accumulated into the still-open old window and are reported as one window's
worth of traffic.

**[verified]** Run `1788748008` recorded `window gaps (a skipped window) | [(1788741330,
1788741450)]` — 120 s, four windows that never emitted.

**Read the companion handoff before acting on this.** Its falsified-claims section establishes
that gaps on this cluster are usually **the OrbStack VM suspending with the MacBook**, not the
filter stalling — the tick timer does not fire and a window that never opened cannot be
reported. That diagnosis took a metrics reconciliation to reach.

**Which is the argument for the field, not against it.** A `windows_skipped` value distinguishes
the two cases immediately:

- **host slept** — large `windows_skipped`, and `access_seen` 0 with no `min_record_time`;
- **tick under-fired while traffic continued** — `windows_skipped` ≥ 1 *and* a
  `min_record_time`/`max_record_time` span wider than `window_seconds`, which is the same
  detector already used for a `helm upgrade` replay.

**Change:** `s.windows_skipped = idx - counts.window - 1` (clamped at 0), passed into
`build_report`. One subtraction. It converts a silent mis-attribution into a stated one.

**Expect it to be routinely non-zero on this cluster** — that is honest, and it must be said in
the same commit, or the first person to build an alert on it will page themselves every time
the laptop sleeps.

### 2.3 `__other__` discards the path of exactly the errors worth investigating

**[from source]** `touch_resource` (lines 285–311) is called with `create = not is_error`, so an
error against a resource never successfully read is folded into `__other__`. `resources_other`
(line 397) reports `counts.resources_over` — a count of **requests folded**, not of distinct
paths.

**[verified]** In both active windows of the tail, `__other__` **is** the signal:

```
seq=332  resource __other__ (other): 2 requests, 0 reads, 2 writes, 2 errors
seq=333  resource __other__ (other): 2 requests, 2 reads, 0 writes, 2 errors
```

The design reason is sound and should not be reversed: it is what stops a client walking
invented table names from filling the key space, and it is what keeps the margins exact. Every
one of those requests is also stored as a full record by rule 3, so nothing is lost from the
log. But the *summary* cannot tell one broken client hammering one URL from a scanner walking
twenty names — both produce `resources_other: 20`.

**Change (minimum):** add **`resources_other_distinct`** — the size of a capped set of folded
keys. One `if seen[key] == nil` inside `touch_resource`'s `create == false` branch, bounded by
the existing `REPORT_MAX_RESOURCES`. It separates the security question from the noise question
at negligible cost and adds no high-cardinality field.

**Change (optional, decide separately):** a bounded `top_error_path` string on the summary. More
useful, more opinionated, and it puts a path into a field that has so far been free of them.

---

## 3. Four smaller things

| # | what | where | change |
|---|---|---|---|
| 3.1 | `response_bytes` is accumulated on every row and surfaced in **no** `_msg`, and there is no summary total | rows 418, 429; summary 388–401 | add `bytes_total` to the summary and `%d bytes` to both row messages — egress per window is the one capacity number this pipeline gets free. If it is not worth printing, stop collecting it |
| 3.2 | resource and principal `_msg` carry **no window identity** | 418, 429 | add `seq=%d` to both format strings. In the §0 tail the only thing tying four rows to `seq=334` is the timestamp column; a grepped line is unattributable on its own |
| 3.3 | the summary `_msg` names neither `hostname` nor `window_seconds` | 402–407 | `seq=%d@%s`. Irrelevant with one shipper — but `report_seq` restarting at 1 **is** the documented restart signature, and today that reads as a counter going backwards rather than as a restart |
| 3.4 | `level = "REPORT"` is not a severity any viewer recognises | 378 | **[verified]** every row in the tail renders as `OTHER`, so severity filtering and colouring are dead for this stream. Either `level: INFO` plus `report_type` as the discriminator, or keep `REPORT` as the stream selector and accept that the severity column is meaningless here. A decision, not a defect |

---

## 4. THE TRAP: every new numeric field must be added to `type_int_key`

**Line 660** of `fb-values.yaml` carries the list that stops Fluent Bit encoding these as
doubles:

```
type_int_key  schema_version report_seq window_seconds access_seen access_kept access_counted
              counted_get counted_post errors_kept parse_errors distinct_resources
              distinct_principals resources_other principals_other requests reads writes
              errors response_bytes
```

**A new numeric field omitted from this list is stored as a string**, `requests:>0`-style range
filters silently return nothing, and the failure is invisible until someone writes a query. This
is precisely what the v3 gate's `type_int_key` check exists to catch.

Every field proposed here goes in that list:

```
carried_rows  errors_4xx  errors_5xx  auth_denied  windows_skipped
resources_other_distinct  bytes_total  counted_read
```

and `counted_get` comes **out** if §1.2 is taken as a rename.

**Add the gate check for it too** — the notebook's cell 0b already asserts
`report_type:resource requests:>0` matches numerically. It should assert the same for every
field in the list, not one representative.

---

## 5. Schema versioning — this is what the field was put there for

`SCHEMA_VERSION = 1` at line 186 has never been changed.

- **§1.1 and §1.2 change the meaning of shipped field names.** That is the case the version
  field exists for. → **bump `SCHEMA_VERSION` to 2.**
- **Everything else is purely additive** and would be safe at v1.

Ship them together at v2 regardless — a consumer that has to handle two field-set variants at
the same version has been given the worst of both.

**The conservative alternative, if the rename is unwanted:** leave `distinct_resources` and
`counted_get` as they are, add `active_resources` / `active_principals` / `counted_head`
alongside, stay at v1, and document the two misnomers permanently. Cheaper today, and it means
carrying two names for one thing forever. **My recommendation is the bump** — nothing consumes
this data yet except the test harness, which is the one consumer that can be changed in the
same commit. This is decision 1 below.

---

## 6. Sequencing — one `helm upgrade`, and it is shared

The companion handoff's item 1 is **revert the fast-run settings** (`WINDOW_SECONDS` 30 → 1800
at line 187, `Interval_Sec` 5 → 30 at line 596, together). That is also a `fb-values.yaml`
change needing a `helm upgrade`. **Decide both in one pass** rather than upgrading the shipper
twice.

Two interactions worth naming:

1. **Reverting `Interval_Sec` to 30 widens the startup blind spot from 5 s to 30 s** — already
   noted in the companion handoff. Unchanged by anything here.
2. **At `WINDOW_SECONDS 1800`, §2.2's `windows_skipped` becomes far more valuable and far less
   noisy.** A 30-minute window skipped by a laptop sleep is a much larger hole than a 30-second
   one, and there are 48 windows a day rather than 2,880.

**Suggested order:** schema changes and the revert in **one** commit and one upgrade, then
cells 0–0b of the notebook (minutes, not the ~90 a full drive at 1800 costs) to confirm the
ConfigMap carries the new script and the tick/window relationship holds.

---

## 7. What the test repo has to learn — not this repo's change

`polaris-practice/polaris-learning/` is not mounted in a Cowork session; these are listed so
they are not discovered late. Every one of them is a consequence of a change above.

- `src/log_coverage.py`: `SUMMARY_FIELDS` / `RESOURCE_FIELDS` / `PRINCIPAL_FIELDS` gain the new
  names — they are frozen sets precisely so a missing or extra field is a named failure.
- `check_invariants`: the margin pair is **untouched** by all nine changes (nothing here alters
  `requests`), but it should gain `errors_4xx + errors_5xx <= errors` and
  `auth_denied <= errors_4xx` per row.
- **`distinct_resources` reconciliation (§1.1)** — the harness's union rule and the filter's row
  count must agree. This is the one change that can move the oracle diff.
- `diff_reports`: the exclusion list keeps `hostname` / `report_seq` / `_msg`; `windows_skipped`
  is a property of the emitting process's clock and the oracle cannot predict it — **exclude
  it**, like `partial_window`.
- The characterization test goes red on `SCHEMA_VERSION` 2. That is correct and expected. Read
  the diff, then update it — the repo's standing rule.
- Cell 0b: assert `type_int_key` for **every** numeric field, per §4.

---

## 8. Decisions needed before anything is edited

1. **Bump to `SCHEMA_VERSION` 2 with the two renames (§1.1, §1.2), or stay at v1 and add
   parallel names?** Recommendation: bump. Nothing consumes the stream but the harness.
2. **`top_error_path` (§2.3, optional half) — in or out?** `resources_other_distinct` alone is
   the safe answer; the path string is more useful and is the first free-text field on a
   summary that has none.
3. **`level: INFO` or keep `level: REPORT` (§3.4)?** Changing it changes the stream selector
   `{app="polaris-shipper-report", level="REPORT"}` that every existing query and
   `src/vlogs.py` helper uses. Cheap now, annoying later. Keeping it means the severity column
   stays meaningless for this stream forever.
4. **One upgrade with the fast-run revert, or two (§6)?**
5. **Is `windows_skipped` wanted at all**, given it will be routinely non-zero on a laptop that
   sleeps? It is the only in-stream signal for a real tick failure, and a real tick failure
   silently mis-attributes counts. Recommendation: yes, with the caveat stated in the commit.

---

## 9. Definition of Done

1. `helm lint ./` and `helm upgrade --install ... --dry-run --debug` for the shipper release —
   per CLAUDE.md, lint is not a render, both are required. **Not runnable from Cowork**; if the
   session that does this cannot run them, the commit body says
   `NOT VERIFIED: helm lint/--dry-run could not be run, no cluster reach from this session`.
2. `logging/scripts/test-polaris-filters.py` green — it runs the Lua extracted from the values
   file and is the only gate reachable without a cluster. New cases for: carried rows excluded
   from `distinct_resources`; a HEAD increments `counted_read`; a 404 and a 500 land in
   `errors_4xx` and `errors_5xx` respectively; `auth_denied` counts 401 and 403 and nothing
   else; `windows_skipped` on a tick that jumps two indices; `resources_other_distinct` counts
   distinct folded keys, not folded requests.
3. **Verify against the running object, not the values file** — the ConfigMap carries the new
   script (sha), and a real report record shows `schema_version: 2` and the new fields as
   *numbers*, not strings. That last one is §4 and it is the whole reason the check exists.
4. `MEMORY.md` *Now* updated (≤40 lines); a numbered finding in `.memory/roadmap.md`;
   the narrative including the wrong turns in `.memory/sessions/2026-09-07-report-schema-v2.md`.
5. One commit, this document included, subject line stating the finding — not the files touched.
   Suggested: `The report counted carried zeros as resources touched, and could not tell a 404
   from a 500`.

---

## RESULT — 2026-09-07

- **Decisions 1–5:** (1) **bump to v2** with both renames; (2) `top_error_path` **out**;
  (3) **keep `level: REPORT`**, cost documented in the Lua; (4) **two upgrades** — schema
  first, fast-run revert after the coverage run (Kade); (5) `windows_skipped` **in**, with the
  sleep caveat in the code and the commit body.
- **`SCHEMA_VERSION` as shipped in the file:** 2. **Not deployed.**
- **Fields added, all present in `type_int_key`:** `carried_rows`, `errors_4xx`, `errors_5xx`,
  `auth_denied`, `windows_skipped`, `resources_other_distinct`, `bytes_total`, `counted_read`;
  `counted_get` removed from the directive with the rename. Checked mechanically, not by eye —
  see the next line.
- **`helm lint` / `--dry-run`:** NOT RUN — no cluster reach from a Cowork session.
- **`test-polaris-filters.py`:** **60/60**, on Lua 5.4 in the Cowork container. Eight new
  report cases covering every §9 requirement, plus a **new suite 4** that reads `type_int_key`
  and the emitted field names out of the same values file and fails on a missing *or* stale
  entry. Verified to fail by removing `auth_denied` from the directive.
- **ConfigMap sha after upgrade:** `d58b9203a8304030`; the notebook's preflight confirms the
  running ConfigMap carries this exact script.
- **A real record showing the new fields as numbers:** yes — run `1788755035`,
  `http_status:>=400 -> 41` and `http_status:"404" -> 25` scoped to the run, and the report
  stream's own numbers reconcile as numbers. Window `04:24:00Z` (`seq=6`), summed independently
  from 44 resource rows and 4 principal rows: `requests` **158 = 158 = access_seen**;
  `errors_4xx` 41 = 41 = 41; `auth_denied` 12 = 12 = 12; `response_bytes` 1,186,348 = 1,186,348
  = `bytes_total`. **The v2 fields carry their own margins** — v1's only self-check was the
  request margin. Cardinality: 38 active + 4 principals + 6 carried = 48 rows emitted; the next
  window carries exactly 42 (the active ones) and decays to 0 in the one after. `seq=7` reports
  `0 resources, 0 principals, 42 carried` — the v1 defect, visibly fixed.
- **Fast-run settings reverted in the same upgrade:** **no, by decision.** `WINDOW_SECONDS 30`
  / `Interval_Sec 5` stay live for one fast run against v2; revert both to 1800/30 after it.
- **Harness updated (§7), characterization test read and updated:** **not yet** — run
  `1788755035` reports 34 fixture mismatches and a violated invariant, and **none of them is a
  filter fault**. The three, with evidence, are in
  [`2026-09-07-HANDOFF-harness-schema-v2.md`](2026-09-07-HANDOFF-harness-schema-v2.md): the
  window merge does not sum fields it does not know (so a v2 field reads as one window, not the
  merge — a wrong number, not an error); `distinct_resources=38 but 44 rows emitted` is now
  correct and needs the stronger invariant `distinct + distinct + carried == rows - 1`; and the
  oracle must compute the new fields while excluding `windows_skipped`, which no oracle can
  predict.
- **Still to ride with the fast-run revert (one upgrade, not two):** `resources_other` and
  `resources_other_distinct` are queryable fields but appear in **no** `_msg`, so the folded-key
  count is invisible to anyone reading the stream as text — 24 of `seq=6`'s requests folded into
  `__other__`, all of them errors. Add both to the summary message then, not before: keeping the
  repo file byte-identical to the deployed ConfigMap is what makes the notebook's gate mean
  anything.
