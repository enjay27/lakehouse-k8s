# REVIEW — `polaris_access_log.lua` refactor (policy v5, schema v5 unchanged)

**Status: PROMOTED in the repo 2026-09-16 (Kade: "proceed deploy refactor"), NOT YET ROLLED.** The candidate was moved to
`fluent-bit/polaris_access_log.lua` (sha `2fbcfa47c513f5a0`; before: `bfff86db220036c2`, recoverable with
`git show 0e9c37e:fluent-bit/polaris_access_log.lua`), `r1-values-step2.patch` applied, `test-r4-first-tick.lua` → `logging/scripts/test-first-tick.lua`
(in `apply-lua.sh`). Paths below that name `logging/candidates/polaris_access_log.refactor.lua` / `test-r4-first-tick.lua` mean those files now.
Roll: §3 steps 2–4.
Decisions (Kade, 2026-09-16): R1 merge **yes**, R4 fix **yes** (a partial first window is visible anyway, because
`partial_window` is `"true"` and `window_start` / `min_record_time` disagree), thread fields out of `polaris-logs-*` only
(done separately, `#30`, commit `5315e0d`), `ndc` out too.

## 0. Result in one table

| gate | current | candidate |
|---|---|---|
| `test-schema-v3/v4/v5.lua` (now fed raw `_msg` lines through the shim) | ALL PASS | ALL PASS |
| `diff-refactor.lua`, real input: 2,136 tier-1 records from 3 readouts, a tick every 5 s | — | **0 diffs** / 18,953 calls |
| `diff-refactor.lua`, fuzz: 300k records, 2 tick rates | — | **0 diffs** (coverage below) |
| harness sensitivity: 5 one-line mutants of the candidate | — | all 5 caught by the fuzz (55–174 diffs each) |
| `step11` replay of `084100Z` (the v5 window) | PASS 67×34 | PASS 67×34 |
| `test-r4-first-tick.lua` | **6 FAIL** (the bug) | ALL PASS |
| Lua CPU per record, `bench-refactor.lua` (LuaJIT 2.1) | ~5.8 µs | **~2.1 µs (2.7–2.8×)** |
| code lines (no comments/blank) | 588 | 585 |

"0 diffs" means for every input: same drop/keep decision, and the same emitted records compared field by field
(including held and orphan records released in arrays, `_msg` rewrites and `secret_redacted`). For reports it means
the same report rows. Return code 0 and 2 count as equal when the record content is equal (see R1).

Fuzz coverage (report windows or docs where each was non-zero): `resources_other` 29, `principals_other` 32, `__other__`
app_dropped row 13, `__errors__` row 44+, `role_keys_forced` 44+, `held_orphans` 41+, `held_pending` 44+,
`app_dropped_404` 41+, `counted_404` 44+, `parse_errors` 44+, `windows_skipped` 14+, commit rows 1,904+,
`secret_redacted` docs 8,494+.

**What the CPU number is and is not.** It is Lua time only. At ~580 lines/s (phase 3.1's estimate) that is ~3.4 ms/s → ~1.2 ms/s,
about 0.2 % of one core. **The bigger R1 saving is outside Lua:** Fluent Bit converts every record msgpack → Lua table → msgpack
once *per Lua filter*, so dropping FILTER 2 removes one of those round trips per Polaris record. That cost lives in C and can
only be measured as pod CPU in the 3.1 load test. Until then it is a hypothesis.

## 1. Findings and what changed

### R1 — two Lua filters per record → one *(efficiency; needs values change)*

```lua
-- current: FILTER 2 (call polaris_access_log) then FILTER 3 (call polaris_noise_filter), both Lua
function polaris_access_log(tag, timestamp, record)
    if record["loggerName"] ~= ACCESS_LOGGER then return 0, timestamp, record end
    ... string.match(msg, PATTERN) ... return 2, timestamp, record
end
-- candidate: one local function, called inside polaris_noise_filter
local function parse_access(record) ... return true|false end
...
if is_access then parsed = parse_access(record); keep = 2 end   -- before rule 1, as FILTER 2 was
```
- Parsing still happens **before** rule 1, so WARN/ERROR access lines are stored with their parsed fields, same as today.
- A kept access line now returns 2 from FILTER 3 instead of 2 from FILTER 2 + 0 from FILTER 3. Same bytes.
- Values: FILTER 2 is deleted and `http_status response_size` go to the front of FILTER 3's `type_int_key`.
  step2: the "script" line count goes 2 → 1, `call polaris_access_log` must be 0, `type_int_key` count 3 → 1.
  All of this is in **`logging/candidates/r1-values-step2.patch`** (`git apply` from the repo root).
- `step11-replay-window.py` now calls `polaris_access_log` only if the script still defines it, and takes
  `POLARIS_LUA=<file>` to replay a candidate. This works for both the current and the merged script, so it is committed as is.

### R2 — `classify()`: up to 21 `^.-` scans per access line *(efficiency)*

```lua
-- current
for _, r in ipairs(RESOURCE_PATTERNS) do
    local span = path:match(r.pattern)          -- ".-" retries from every position of the path
    if span then return span, r.kind end
end
-- candidate: same table, same order, plus a literal each pattern must contain, plus a per-window cache
local key = counts.c_key[path]; if key ~= nil then return key, counts.c_kind[path] end
for i = 1, N_PATTERNS do
    local r = RESOURCE_PATTERNS[i]
    if find(path, r.lit, 1, true) then            -- plain find; no literal -> the pattern cannot match
        local span = match(path, r.pattern)
        if span then key, kind = span, r.kind; break end
    end
end
-- cache up to CLASSIFY_CACHE_MAX (4000) paths, cleared with the window
```
Four alternatives were benchmarked on the 1,059 real paths plus 40 edge cases (empty segments, trailing `/`, repeated keywords,
no leading slash). All five, including the current one, give identical keys (`bench-classify.lua`):

| variant | ns/call | risk |
|---|---|---|
| current | ~5,250 | — |
| literal guard | ~1,950 | none by construction: the guard only checks a necessary condition |
| cache only | ~1,600 | none |
| **guard + cache (chosen)** | **~620** | none. The cache is capped because paths come from clients |
| segment tokenizer (rules rewritten on `/`-split segments) | ~2,350 | rules re-expressed by hand; slower than the guard and easy to get subtly wrong. **Rejected** |

The cache is measured with the real hit rate (275 distinct paths per 1,059 lines, reset every round). A 30-minute production
window repeats far more, so the real saving is probably larger. A load-time `assert` fails the script if a `lit` is not
inside its pattern, so a future rule edit cannot quietly disable a rule. That failure would show at filter init, and the
LuaJIT tests in `apply-lua.sh` run before any apply.

Ablation on the full filter: guard removed → candidate only 1.07× faster; cache removed → 2.35×. **R2 is most of the Lua-side gain.**

### R3 — table allocations per record *(efficiency, GC)*

| current | candidate |
|---|---|
| `local extra = {}` on **every** polaris.logs record | `take_orphans` returns `nil` when there is nothing to release; `emit` handles `nil` |
| `local rows = { touch_resource(...), touch_principal(user) }` + `ipairs` per access line | `bump(row, …)` called twice |
| `memo_q[i] = { rid = rid, t = now }` and `memo[rid] = { status, t }` per access line with a request id | parallel arrays `memo_q_rid/memo_q_t`, `memo_status/memo_t` |
| `held_q[i] = { rid, t }`, `held[rid] = { t, recs }` | `held_q_rid/held_q_t`, `held_recs/held_t` |

The queue semantics are unchanged, including "a stale queue entry is skipped when its `t` no longer matches". The fuzz reuses
request ids on purpose (1 in 3), so this path is exercised.

### R4 — records before the first tick were dropped without being counted *(correctness)*

```lua
-- current: counts == nil until the first tick; every counter is guarded and silently skipped
local function count_record(...) if counts == nil then return end ...
if counts ~= nil then counts.counted_read = counts.counted_read + 1 end   -- x10
-- candidate: the window opens on the first tick OR the first record
if counts == nil then counts = new_window(floor(now / WINDOW_SECONDS), true) end
```
On every pod start (and every Lua change is now a restart) up to `Interval_Sec` (5 s) of successful GETs, catalog POSTs and
404s were dropped **and** missing from every counter. That breaks the pipeline's one guarantee: anything not stored is counted.
`test-r4-first-tick.lua` shows it: the current script reports `access_seen` 0 for 3 lines. Behaviour change: that start-up
window now reports those records, still `partial_window: "true"`. The ten `counts ~= nil` guards are gone.
`diff-refactor.lua` sends its first tick before any record, so R4 does not show up as a diff there.

### R5 — conditions that can never change the result *(cleanup)*

| current | why it is dead | candidate |
|---|---|---|
| `status == 404 and not parse_failed` (×2) | a failed parse never sets `http_status`, so `status` is nil | `status == 404` |
| `parse_failed or status == nil or status >= 400` | `status == nil` ⇔ parse failed | `status == nil or status >= 400` |
| `is_error = (status == nil or status >= 400)` in `count_record` | parse failures return earlier | `status >= 400` |
| `tonumber(record["http_status"])`, `tonumber(record["response_size"]) or 0` | the parser already stores numbers | read directly |
| `if r.requests > 0` on principal rows, `if n > 0` on dropped loggers | these rows are created and incremented in the same call | removed (comment says why) |
| `last_read_bytes = nil, …` in `new_row()` | assigning nil in a constructor does nothing | removed (comment keeps the fact) |
| `touch_resource`: the same four lines repeated three times | — | `add_resource()` |
| `commit_key`: a second table for the namespace parts | — | `table.concat(parts, sep, 2, n-1)` |

### R6 — report assembly *(cleanup)*
`build_report` filled `rows` and then copied them into `out` after the summary. Now `out = { s }` and rows are appended
directly; summary fields are filled afterwards through the same table reference. The order stays summary first.

### Reviewed, not changed
- `redact_secret` on every record: a plain `find("clientSecret")` first. It is deliberate, since the guard runs before the decision.
- `os.time()` per record: cheap, and the tick needs the same clock.
- Orphans leave only with the next `polaris.logs` record. The tick's return goes to `polaris.report`, so orphans cannot ride on it.
  `held_pending` shows what is waiting.
- `COMMIT_PATTERN`, allow-list, role-row forcing, row caps: correct, untouched.

## 2. Files

| file | role |
|---|---|
| `logging/candidates/polaris_access_log.refactor.lua` | the candidate |
| `logging/candidates/r1-values-step2.patch` | FILTER 2 removal + `type_int_key` + step2 expectations (apply **with** promotion, not before) |
| `logging/candidates/diff-refactor.lua` | current vs candidate differential (real + fuzz, coverage print) |
| `logging/candidates/bench-refactor.lua` · `bench-classify.lua` | CPU comparison · classify variants |
| `logging/candidates/test-r4-first-tick.lua` | R4 regression test (current FAILs by design) |
| `logging/candidates/tier1-to-lua.py` | builds `/tmp/tier1_all.lua` and `/tmp/paths.txt` from `.scratch/readout-*` |
| `logging/scripts/test-raw-access-shim.lua` | tests v3/v4/v5 now send raw `_msg` lines through split *or* merged scripts |
| `logging/scripts/step11-replay-window.py` | parser call optional, `POLARIS_LUA=` override |

Reproduce (repo root, needs `luajit`):
```bash
python3 logging/candidates/tier1-to-lua.py
for s in fluent-bit/polaris_access_log.lua logging/candidates/polaris_access_log.refactor.lua; do
  cp $s /tmp/polaris.lua; for t in v3 v4 v5; do luajit logging/scripts/test-schema-$t.lua | tail -1; done
  luajit logging/candidates/test-r4-first-tick.lua | tail -1; done
luajit logging/candidates/diff-refactor.lua fluent-bit/polaris_access_log.lua logging/candidates/polaris_access_log.refactor.lua /tmp/tier1_all.lua 300000 1
luajit logging/candidates/bench-refactor.lua fluent-bit/polaris_access_log.lua logging/candidates/polaris_access_log.refactor.lua /tmp/tier1_all.lua 100
luajit logging/candidates/bench-classify.lua /tmp/paths.txt 2000
POLARIS_LUA=logging/candidates/polaris_access_log.refactor.lua python3 logging/scripts/step11-replay-window.py .scratch/readout-2026-09-16T084100Z
```

## 3. Promotion — after Kade's comparison

**Order matters because of R1.** FILTER 2 calls `polaris_access_log`. If a pod starts with the new Lua and the old config, that
filter fails at init, and a failed Lua init stops **all** inputs, tier 1 included (2026-09-15). If it starts with the new config and
the old Lua, every access line becomes a parse error and is stored. The one safe sequence restarts the pod once with both:

1. `cp logging/candidates/polaris_access_log.refactor.lua fluent-bit/polaris_access_log.lua && git apply logging/candidates/r1-values-step2.patch`.
   Add `test-r4-first-tick.lua` to `apply-lua.sh`'s test loop, update the header of `values.yaml` and step3's expected sha, and commit.
2. `bash fluent-bit/apply-lua.sh --no-restart` (tests → diff → apply; the running pod keeps the old script and config)
3. **Immediately after:** step2 on a fresh render → `helm upgrade` (the `checksum/config` restart reads the new ConfigMap *and* config)
4. step3 → step12 (if not done for `#30`) → one traffic run → step10/step11 on a window after the restart.
   Expect step11 PASS and `detail docs by logger` equal.

`#30` (thread/ndc trim) is a values-only change. It can ride in step 3's `helm upgrade` or go first on its own.

**Relative to the handoff:** do this **before D** (1800 s window). D is also a Lua roll, and bundling them hides which one changed what.

## 4. Not verified

- No helm render: `r1-values-step2.patch`'s step2 numbers (script 1, call 0, `type_int_key` 1) were counted on the values
  file's `filters:` block, not on a real render. The block renders verbatim, but that is the rule step2 exists to check.
- Fluent Bit 5.1.1 accepting `http_status response_size` in FILTER 3's `type_int_key` for records returned **inside arrays**.
  The 403 path already returns access lines in arrays from FILTER 3 today; they got their ints from FILTER 2 before that.
- The C-side marshalling saving of R1 (phase 3.1).
- The cache hit rate at 1800 s windows in production.
