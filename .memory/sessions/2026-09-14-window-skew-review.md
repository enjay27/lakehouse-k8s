# Review of run `1789370776` — the window offset is a fixed 3.673s tick skew, not an inconsistent 30s shift

Reviewed: `REPORT-for-local-k8s.md` and `doc-api-status-matrix-results.md` (both from
`log-coverage/polaris_log_coverage_v2.ipynb`, run `1789370776`, 2026-09-14 07:29Z), against two
OpenSearch exports Kade pulled the same morning — the report index (`seq` 184..194, 235 docs) and
the Polaris log index (756 docs, of which 343 access lines).

**The exports are the first independent witness this pipeline has had.** Everything below is
measured from them; nothing is reasoned from configuration alone, which is how `#16` went wrong.

## 1. The finding that has to be withdrawn: "no single offset can correct it"

The report's headline warning — *window attribution is INCONSISTENT across rows (`{-30: 5, 0: 1}`);
no single offset can correct it, so window-scoped gates must not be quoted* — **is not supported by
the data, and the statistic it rests on cannot distinguish the two cases.**

What is actually happening is documented in `logging/fb-values.yaml` and was designed in:

> *"records arriving between a boundary and the tick that notices it are counted into the window
> just closed. A summary, not a ledger."* — `report_tick`
> *"5s against the temporary 30s window bounds edge skew at 5s."* — the dummy INPUT

**Measured skew: a constant 3.673s.** Every one of the 11 report rows was emitted at
`window_end + 3.673s` (σ below 2ms, seq 184..194). It does not drift because `Interval_Sec 5`
**divides** `WINDOW_SECONDS 30` — the tick phase relative to the window grid is fixed for the life
of the process. So the row labelled `[W, W+30)` actually covers roughly `[W+3.7, W+33.7)`.

**And every phase of the matrix fires its whole burst inside that 3.673s dead zone:**

| real 30s window | access lines | first | last | span |
|---|---|---|---|---|
| 07:26:00 | 45 | 07:26:16.937 | 07:26:19.061 | 2.124s |
| 07:26:30 | 31 | 07:26:30.609 | 07:26:31.552 | 0.943s |
| 07:27:00 | 177 | 07:27:00.522 | 07:27:01.512 | 0.990s |
| 07:27:30 | 39 | 07:27:30.530 | 07:27:31.039 | 0.509s |
| 07:28:30 | 1 | 07:28:30.544 | — | 0.000s |
| 07:29:00 | 4 | 07:29:00.551 | 07:29:00.626 | 0.075s |
| 07:29:30 | 46 | 07:29:30.594 | 07:29:31.569 | 0.975s |

Traffic starts **0.52–0.61s** after each boundary and is over within a second. A 3.673s skew
therefore captures **100%** of every boundary-aligned burst into the previous row — deterministically,
not erratically.

### The `{0: 1}` row is the proof, not the exception

`lead_s = window_start − min_record_time` is a distance to the **label**, so it reports −30 for a
burst that fires just after a boundary and ≈0 for one that fires mid-window — **the same skew,
two different numbers.** Reconstructed per row:

| seq | label | its traffic | lead_s | bucket |
|---|---|---|---|---|
| 185 | 07:26:00 | 07:26:16.937 (setup, **not** boundary-aligned) | −16.9 | → `0` |
| 186 | 07:26:30 | 07:27:00.522 | −30.5 | −30 |
| 187 | 07:27:00 | 07:27:30.530 | −30.5 | −30 |
| 188 | 07:27:30 | 1 line, 0 kept → no `min_record_time` | — | excluded |
| 189 | 07:28:00 | 07:28:30.544 | −30.5 | −30 |
| 190 | 07:28:30 | 07:29:00.551 | −30.5 | −30 |
| 191 | 07:29:00 | 07:29:30.594 | −30.6 | −30 |

Six checked, `{-30: 5, 0: 1}` — reproduced exactly. The single outlier is the **one burst in the
run that did not start on a boundary**: the notebook's setup phase, which began at :16.9 and so
landed inside its own label. Same 3.673s skew as every other row.

### The skew is bounded, not inferred

For `seq=186` the export pins it from three sides: it must contain 07:27:00.522–07:27:01.512, must
**not** contain 07:26:31.552 (that is `seq=185`), is 30s wide, and was emitted at 07:27:03.673 — so
its coverage cannot end later than that. Coverage start therefore lies in
**(07:26:31.55, 07:26:33.67]**, i.e. **+1.55s to +3.67s past its own label**. A 30-second shift is
arithmetically excluded by the emit timestamp.

### `access_kept` matches the log index exactly, 7 windows out of 7

Shift by one row and the two independently-shipped pipelines agree to the record:

| report row (label) | `access_seen` | `access_kept` | access docs in the real window |
|---|---|---|---|
| 185 (07:26:00) | 147 | **76** | 45 + 31 = **76** |
| 186 (07:26:30) | 180 | **177** | **177** |
| 187 (07:27:00) | 44 | **39** | **39** |
| 188 (07:27:30) | 1 | **0** | **0** |
| 189 (07:28:00) | 1 | **1** | **1** |
| 190 (07:28:30) | 7 | **4** | **4** |
| 191 (07:29:00) | 53 | **46** | **46** |
| | | **343** | **343** |

Also confirms the export is complete — an export truncated at the old end could not reproduce
`seq=185`'s 76.

## 2. Two of the three failing gates are this skew, and one report hypothesis is wrong

**Gate 4 privilege count — `writes=1 granted=3`.** Both numbers are real; they are one row apart.
The three grants are `PUT .../catalog-roles/mx_1789370776_crole/grants` → 201 at 07:29:00.551,
.583, .613 (row labelled **07:28:30**). The single write is the teardown
`DELETE .../catalog-roles/mx_1789370776_crole` → 204 at 07:29:31.352 (row labelled **07:29:00**).
The gate read the 07:29:00 row. Not a privilege-accounting fault.

**Gate 4 denial — `auth_denied=0`.** The report attributes this to "the ROLE_KINDS exemption; 0
means the 403 fell to `__errors__`". **That hypothesis should be withdrawn.** The denial exists and
is on the role row: `GET .../catalog-roles/mx_1789370776_crole` → 403 as `mx_1789370776_denied` at
07:29:00.626, carried by the row labelled **07:28:30**, which reports `auth_denied=1`. Nothing fell
anywhere.

**Gate 2 `last_write_bytes` VOID** is the same class — the gate's own text already says "check
WHICH window was read before blaming the filter". It was read one row off, like the others.

Also measured, as a by-product: `auth_denied` is exactly 401+403 (**101 = 59 + 42** in the 07:27:00
burst) and is a **subset** of `errors_4xx`, not disjoint from it (`seq=187`: 4xx=32 = 31 + the one
403). That matches the Lua's comment and is now checked against traffic.

## 3. What the report got right

**The four 500s are confirmed, and `#24` now reproduces across two runs.** All four in the
07:27:30 burst — `POST /api/catalog/v1/oauth/tokens` .545, `.../namespaces` .584,
`.../tables/rename` .826, `.../views/rename` .876 — each paired with an ERROR from
`org.apache.polaris.service.exception.IcebergExceptionMapper`: *"Unhandled exception returning
INTERNAL_SERVER_ERROR"*. Same four operations as run `1789026666`; the shape in `#24` (malformed
input on an operation whose 400 handler does not cover it) survives a second run. Still missing for
an upstream report: `exception.frames` per operation.

**Item 1's remedy is right in direction** — a row should be stamped with the window its records
fall in. But note it **contradicts a deliberate decision** in the Lua (*"os.time() is used for the
report window and deliberately NOT for anything about a record: a replayed record must not be
re-dated"*). It is a design change with a replay consequence, not a bug fix, and it should be
argued on those terms.

## 4. Item 2 is not new work — it is `#25`, still not rolled

The report proposes an index template for `polaris-report-*` typing `min/max_record_time` as
`date`. That template already exists at `logging/opensearch/polaris-report-template.json`, the Lua
change already exists in `fluent-bit/values.yaml`, and **neither is applied** — `#25`, order
load-bearing (Lua first), applied with `logging/scripts/step9-report-index-template.sh`.

Its *revised* cause — nine fractional digits defeat dynamic date detection — is **asserted, not
measured**, and the exports carry only `@timestamp`/`level`/`loggerName`/`_msg`, so nothing here
tests it. The report proposes waiting for the next day's index. There is a 30-second test instead:

```
PUT  /zz-datedetect-probe/_doc/1   {"t":"2026-09-14T07:29:30.587684196Z"}
GET  /zz-datedetect-probe/_mapping/field/t
DELETE /zz-datedetect-probe
```

`text` reproduces it; `date` means the cause is something else and the empty-string theory the
report already abandoned may not have been the wrong one.

## 5. Gate 5's fix is right; its stated reason is probably wrong

The report says `{"term": {"resource": "__errors__"}}` cannot match because the standard analyser
turns `__errors__` into the token `errors`. **Underscore is `ExtendNumLet` under UAX#29**, so
StandardTokenizer joins rather than splits and emits `__errors__` as a single token — a `term`
query for `__errors__` would then match. The run's own gate table agrees with that reading: *Gate 5
`__errors__` holds only errors — PASS, requests=68 over 4 doc(s)*, which is not what a filter
matching nothing produces.

`.keyword` is still the correct fix, and it is correct for the reason `MEMORY.md` already records —
case (`POST` → `post`). Keeping a wrong mechanism next to a right fix is how the mechanism gets
applied somewhere it does not hold. Settle it with `_analyze` on the field, one call.

## 6. Wrong turn, kept

First pass through the counts I concluded the offset was a **constant one-window (−30s) shift** and
that rows could simply be read one row late. Every count fits that model — because the traffic is
absent everywhere except the first second of each window, so "shifted 1.6s" and "shifted 30s" are
indistinguishable from counts alone. What breaks the tie is the **emit timestamp**: a row emitted
3.673s after its label ended cannot be carrying a window that has not finished yet. The lesson is
the one this repo keeps re-learning — a model that explains every data point can still be wrong by
an order of magnitude, and the disproof came from a field nobody was looking at.

## 7. What to do, cheapest first

1. **Offset the notebook's phase starts by ~5s past each boundary** (> `Interval_Sec`). No pipeline
   change, and every window-scoped gate becomes readable in the next run. This alone re-enables
   Gate 2, Gate 4 and the invariant.
2. **Re-drive Gate 2 in a named window** with that offset — still the outstanding question from
   2026-09-10, and still not answered by this run.
3. **Roll `#25`** (Lua, then template), then re-run the invariant against `date`-typed fields.
4. **Decide item 1 on its merits** as a replay-safety trade, not as a defect.
5. Withdraw the `__errors__` tokenisation claim from `GUIDE-schema-v3-testing.md`, keep `.keyword`.

**NOT VERIFIED:** no cluster reach from this session — no `kubectl`, `helm`, `curl` to OpenSearch.
Everything above is derived from the two exports, the two report documents, and
`logging/fb-values.yaml` as committed.
