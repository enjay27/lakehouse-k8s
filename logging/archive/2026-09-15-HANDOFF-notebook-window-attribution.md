# HANDOFF — the window offset is `lag=0.5`, not a pipeline defect. Two edits in the notebook, none in the cluster.

**Written 2026-09-15 from `local-k8s`, for whoever runs
`polaris-learning/log-coverage/polaris_log_coverage_v2.ipynb`.**
Read §1 and §3. §5 and §6 are two sentences the notebook prints that should not be quoted again.

Basis: the notebook as uploaded 2026-09-15 (cells 2–8 executed, 10–44 unrun), run
`1789370776`'s two output documents, and two OpenSearch exports of 2026-09-14 — the report index
(`seq` 184..194) and the Polaris log index (343 access lines). Derivation:
[`.memory/sessions/2026-09-14-window-skew-review.md`](../.memory/sessions/2026-09-14-window-skew-review.md),
issue [`#26`](../.memory/active-issues.md).

---

## 1. In sixty seconds

The notebook prints, and run `1789370776` shipped to `local-k8s`:

> Window attribution is INCONSISTENT across rows (`{-30: 5, 0: 1}`); no single offset can correct
> it, so window-scoped gates were read unshifted and must not be quoted.

**That is wrong, and the notebook caused the condition it is reporting.**

`run_phase` and the four hand-rolled phases all call
`osr.seconds_to_boundary(WINDOW_SECONDS, lag=0.5)`. Every phase therefore fires **0.5 s after a
window boundary** — measured in the export: bursts start 0.52–0.61 s past the boundary and finish
within ~1 s.

The shipper closes a window only when the 5 s report tick notices the boundary. Measured across
all 11 report rows of that run, the tick lands at **window_end + 3.673 s**, σ < 2 ms, and it cannot
drift because `Interval_Sec 5` **divides** `WINDOW_SECONDS 30` — the tick's phase against the
window grid is fixed for the life of the pod. So the row labelled `[W, W+30)` really covers about
`[W+3.7, W+33.7)`.

**Every phase fires into that 3.673 s blind spot, so 100 % of every burst is booked to the previous
row — deterministically, not erratically.** The displacement is bounded independently for `seq=186`
to **+1.55 s … +3.67 s** by its own emit timestamp: a row emitted 3.673 s after its label ended
cannot be carrying a window that has not finished. A 30-second shift is arithmetically excluded.

Fix the lag and the whole class of failure goes away, including the invariant. No cluster change.

---

## 2. Why the notebook's own measurement said INCONSISTENT

Cell 32, the offset probe:

```python
_lo_floor = _rfc3339(osr.window_bounds(_lo.timestamp(), _secs)[0])
_seen[round((_ws - _lo_floor).total_seconds())] += 1
```

It **floors `min_record_time` to a window** before differencing. For a burst that fires 0.5 s after
a boundary, the floor is the *next* window, so the row reports −30. For the one burst that started
mid-window, the floor is its own window and the row reports 0. **Same displacement, two different
numbers** — and `len(_seen) > 1` then takes the "refusing to guess" branch.

Reconstructed from the export, this reproduces exactly:

| seq | label | its traffic | raw `min − window_start` | floored bucket |
|---|---|---|---|---|
| 185 | 07:26:00 | 07:26:16.937 — setup, **not** boundary-aligned | +16.9 s | `0` |
| 186 | 07:26:30 | 07:27:00.522 | +30.5 s | `-30` |
| 187 | 07:27:00 | 07:27:30.530 | +30.5 s | `-30` |
| 188 | 07:27:30 | 1 line, 0 kept → no `min_record_time` | — | excluded |
| 189 | 07:28:00 | 07:28:30.544 | +30.5 s | `-30` |
| 190 | 07:28:30 | 07:29:00.551 | +30.5 s | `-30` |
| 191 | 07:29:00 | 07:29:30.594 | +30.6 s | `-30` |

Six checked, `{-30: 5, 0: 1}`. The single outlier is the only traffic in the run that did not start
on a boundary.

Cross-check that the mapping is real: shift by one row and `access_kept` equals the access
documents in the true window in **7 of 7** windows, 343 == 343 in total.

---

## 3. The two edits

### 3a. `lag` must exceed the tick interval — five call sites

The tick's phase lies in `[0, Interval_Sec)`. Fire later than that and the burst lands
unambiguously inside one row, whatever the phase happens to be.

Cell 6 already parses the running ConfigMap; add the tick interval beside the Lua constants. Search
the **raw** `cm`, not `body` — `body` has `--…` stripped for Lua and the tick lives in the Fluent
Bit config block:

```python
    m = re.search(r"Alias\s+polaris_report_tick.*?Interval_Sec\s+(\d+)", cm, flags=re.S)
    info["TICK_INTERVAL_S"] = int(m.group(1)) if m else None
```

then, beside `WINDOW_SECONDS`:

```python
TICK_INTERVAL_S = TARGET["TICK_INTERVAL_S"]
if not TICK_INTERVAL_S:
    raise RuntimeError(
        "could not read Interval_Sec out of the running ConfigMap. Phases must start later "
        "than the tick period or every burst is booked to the previous window -- and the "
        "failure is silent, it looks like a pipeline defect.")
PHASE_LAG = TICK_INTERVAL_S + 1.5
assert PHASE_LAG < WINDOW_SECONDS / 2, (
    f"PHASE_LAG {PHASE_LAG}s leaves too little of a {WINDOW_SECONDS}s window to drive a phase")
print(f"  report tick every {TICK_INTERVAL_S}s -> phases start {PHASE_LAG}s past the boundary")
```

Then replace `lag=0.5` with `lag=PHASE_LAG` in **all five** places: cell 14 (`run_phase`), 22
(phase E), 24 (F), 26 (G), 28 (H). At 30 s / 5 s that is 6.5 s, leaving 23.5 s of window; at the
steady-state 1800 s / 30 s it is 31.5 s, which is nothing.

**Do not hardcode 6.5.** The tick's phase is arbitrary per pod, and `Interval_Sec` changes with the
1800/30 revert. The constant that matters is `Interval_Sec`, and it is readable.

### 3b. Select report rows by their records, not by their label

`lbl()` and `WINDOW_OFFSET_S` exist only because rows are looked up by label. They do not have to
be. Every summary row carries `min_record_time` / `max_record_time`, the notebook already knows the
exact wall-clock interval it drove (`_t0`, `_t1`), and `_rfc3339` already parses these fields
**client-side** — so this works today, on a `text` mapping, and **does not wait on `#25`**.

```python
def row_for(t0, t1, rows):
    """The summary row whose RECORDS bracket the interval we drove. Label-independent."""
    lo_t = _dt.datetime.fromtimestamp(t0, _dt.timezone.utc)
    hi_t = _dt.datetime.fromtimestamp(t1, _dt.timezone.utc)
    hits = [r for r in rows
            if (lo := _rfc3339(r.get("min_record_time"))) and (hi := _rfc3339(r.get("max_record_time")))
            and lo <= hi_t and hi >= lo_t]
    return hits[0] if len(hits) == 1 else None   # 0 or >1 is a finding, not a row
```

Probe a range of ±3 windows (cell 32 already does), then resolve each phase once and carry the
resolved `window_start` forward instead of `lbl(...)`. After 3a, `row_for` should return exactly one
row per phase; **0 or more than 1 is itself the finding** and should be reported as such rather than
silently picking `[0]`.

With 3b in place, 3a becomes belt-and-braces — but keep both: 3a is what makes the *pipeline's own*
per-window numbers correct, not just the notebook's reading of them.

---

## 4. Fix the offset statistic, or delete it

If cell 32 stays, stop flooring:

```python
_seen[round((_lo - _ws).total_seconds(), 1)] += 1   # RAW displacement
```

and read it as: values clustering inside `[0, Interval_Sec)` are **the tick phase, which is
expected and harmless**; a value at or beyond `window_seconds` is a real stamping fault. The
current branch text — *"no single offset can correct it"* — should be withdrawn; it is the sentence
that told every reader of `REPORT-for-local-k8s.md` not to trust a single window-scoped gate.

---

## 5. The invariant is named for a property it does not measure

```
inv("record times fall INSIDE their own window", ...
    "   -- outside means the window is assigned by PROCESSING time, not record time")
```

The conclusion is true of the pipeline but it is **not what the check detects**. After 3a,
`min_record_time` = `W + 6.5` and `max` ≈ `W + 7.5`, both inside `[window_start, +window_seconds)`
— **the invariant goes green with no pipeline change at all**, because what it actually measures is
whether the harness fired inside the tick's blind spot.

That matters downstream: `WINDOWS_TRUSTED = bool(_checked) and not _outside` gates whether cell 42
reports Gate 2 / Gate 4 failures as pipeline faults. Left as is, it would keep suppressing them
forever against a pipeline that is behaving as designed. Keep the check — it is a good canary — but
reword it to what it proves, e.g. *"no record fell outside its row's label window (harness lag
`PHASE_LAG`s, tick `Interval_Sec`s)"*, and let `WINDOWS_TRUSTED` mean that.

---

## 6. Two sentences the notebook asserts and did not measure

**Gate 4 denial.** The verdict string is

```python
f"auth_denied={_denied} (the ROLE_KINDS exemption; 0 means the 403 fell to __errors__)"
```

It did not. Checked in the export: the denial is
`GET .../catalog-roles/mx_1789370776_crole` → **403** as `mx_1789370776_denied` at
**07:29:00.626**, and it sits on the role row in the row labelled **07:28:30**, which reports
`auth_denied=1`. The gate read the 07:29:00 row, which carries the teardown. Nothing fell anywhere.

Same for **Gate 4 privilege count** — `writes=1 granted=3` is two adjacent rows, not an
undercounting filter: three `PUT .../mx_1789370776_crole/grants` → 201 at 07:29:00.55–.61, and the
teardown `DELETE .../mx_1789370776_crole` → 204 at 07:29:31.35.

A verdict string should carry **the measurement**, not a candidate cause. When a cause is
worth recording it belongs in `GATE_REMEDIES`, where it reads as a hypothesis. Both of these were
copied verbatim into `REPORT-for-local-k8s.md` and arrived here as work items for the pipeline.

**Gate 5 / the guide's `__errors__` claim.** `GUIDE-schema-v3-testing.md` says
`{"term": {"resource": "__errors__"}}` cannot match because the standard analyser turns
`__errors__` into `errors`. Underscore is `ExtendNumLet` under UAX#29, so `StandardTokenizer`
**joins rather than splits** and emits `__errors__` whole — a `term` query for it would match. The
run's own table agrees: *Gate 5 `__errors__` holds only errors — PASS, requests=68 over 4 doc(s)*,
which is not what a filter matching nothing produces.

`.keyword` is still the right fix, for the reason already recorded — case, `POST` → `post`. Settle
the mechanism with one call before the wrong one propagates:

```
GET polaris-report-*/_analyze
{ "field": "resource", "text": "__errors__" }
```

---

## 7. Not the notebook's problem — do not "fix" these here

- **`#25`** — the report index template is written and not applied, and the Lua change is written
  and not rolled. Order is load-bearing: **Lua first**, then
  `logging/scripts/step9-report-index-template.sh`. `§3b` deliberately does not depend on it.
- **The run's "index mapping" item** is `#25`, not new work. Its nine-fractional-digits cause is
  still asserted; a throwaway probe index settles it in 30 seconds rather than waiting a day.
- **`REPORT-for-local-k8s.md` item 1** — *"a report row must be stamped with the window its records
  fall in"* — contradicts a deliberate decision in the Lua (*"os.time() is used for the report
  window and deliberately NOT for anything about a record: a replayed record must not be
  re-dated"*). It is a design change with a replay consequence and should be argued as one. **After
  §3 the notebook does not need it.**
- **`#24`** — the four operations answering 500 to a malformed request (`getToken`,
  `createNamespace`, `renameTable`, `renameView`) reproduce across runs `1789026666` and
  `1789370776`, each with an `IcebergExceptionMapper` *"Unhandled exception"*. What is still
  missing before it goes upstream is `exception.frames` per operation.
- **The 30 s window** is temporary. The revert to 1800/30 is the cutover's last step, and note it
  changes §3a's arithmetic — 30 still divides 1800, so the phase stays fixed, but `PHASE_LAG`
  becomes 31.5 s. Re-check that the tick still divides the window after any change to either.

---

## 8. What a good next run looks like

1. Cell 6 prints a tick interval and a `PHASE_LAG` derived from it.
2. Cell 32's offset probe reports a raw displacement inside `[0, Interval_Sec)`, or says
   "no offset" — **not** "INCONSISTENT".
3. `record times fall INSIDE their own window` **PASSES**, and `WINDOWS_TRUSTED` is true.
4. `row_for` resolves exactly one summary row per phase.
5. **Gate 2 `last_write_bytes` finally answers.** It has been VOID for two runs and it is the
   feature; a VOID after §3 means the commit really did not reach the filter, which is worth
   sending here.
6. Gate 4's two FAILs are expected to turn PASS. If either still fails **with the invariant green**,
   that is the first window-scoped finding this project has had that is safe to quote.

Report back what §8-5 and §8-6 say. Those two are the only open questions on this side.
