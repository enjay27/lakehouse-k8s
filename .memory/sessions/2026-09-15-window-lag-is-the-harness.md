# 2026-09-15 — the window offset was `lag=0.5`, and the notebook was reporting its own defect

**Input:** `HANDOFF-notebook-window-attribution-2026-09-15.md`, written from `local-k8s`
against the notebook as uploaded 2026-09-15, run `1789370776`'s two output documents, and
two OpenSearch exports of 2026-09-14. **Output:** five commits, `29179ee`..`0b6898b`, all
in `log-coverage/polaris_log_coverage_v2.ipynb` except the first. **No cluster change.**

## What was actually wrong

A window is not closed when it ends. It is closed when the 5 s report tick next notices the
boundary, and that tick lands at **`window_end + 3.673 s`, σ < 2 ms** across all 11 report
rows of run `1789370776`. It cannot drift, because `Interval_Sec 5` **divides**
`WINDOW_SECONDS 30` — the tick's phase against the window grid is fixed for the life of the
pod. So the row labelled `[W, W+30)` really covers about `[W+3.7, W+33.7)`.

`run_phase` and the four hand-rolled phases all called
`osr.seconds_to_boundary(WINDOW_SECONDS, lag=0.5)`. Every phase therefore fired **0.5 s past
a boundary — inside that 3.673 s blind spot** — and 100 % of every burst was booked to the
previous row. **Deterministically.** For `seq=186` the displacement is bounded independently
to **+1.55 s … +3.67 s** by the row's own emit time: a row emitted 3.673 s after its label
ended cannot be carrying a window that has not finished. **A 30-second shift is
arithmetically excluded.**

So the "−30 s window attribution" this repo reported to `local-k8s` across three runs, and
which `.memory/active-issues.md` carried as an open pipeline defect, was the harness's own
lag. The instrument was measuring itself.

## The `{-30: 5, 0: 1}` that looked like inconsistency

Cell 32 **floored `min_record_time` to a window** before differencing. For a burst 0.5 s past
a boundary the floor is the *next* window, so the row reports −30; for the one burst that
started mid-window the floor is its own, so it reports 0. **Same displacement, two different
numbers.** `len(_seen) > 1` then took the "refusing to guess" branch and printed

> Window attribution is INCONSISTENT across rows (`{-30: 5, 0: 1}`); no single offset can
> correct it, so window-scoped gates were read unshifted and must not be quoted.

into `REPORT-for-local-k8s.md`. That is the sentence that told every reader not to trust a
single window-scoped gate, and there was no inconsistency behind it. Measured raw the same
run is `{30.5: 5, 16.9: 1}` — five rows carrying a record from after their window closed, and
one legitimate mid-window burst (the fixture setup, the only traffic in the run that did not
start on a boundary). **Verified by exercising the new classifier standalone against the
handoff's own §2 table before trusting it.**

## The five commits, each revertable on its own

| commit | what |
|---|---|
| `29179ee` | park the pre-existing dirty tree (see the credential note below) |
| `8280885` | §3a — `PHASE_LAG = Interval_Sec + 1.5`, read from the running ConfigMap; five call sites |
| `a20e1b6` | §3b — `row_for()`; gates resolve by RECORDS, `lbl()` / `WINDOW_OFFSET_S` deleted |
| `b78fff6` | §4 + §5 — raw displacement; the invariant renamed to what it measures |
| `0b6898b` | §6 — verdict strings carry the measurement, not a candidate cause |

`PHASE_LAG` is **not** hardcoded to 6.5. The tick's phase is arbitrary per pod and
`Interval_Sec` changes with the 1800/30 revert, where `PHASE_LAG` becomes 31.5 s of an 1800 s
window. 30 still divides 1800 so the phase stays fixed — **re-check that the tick still
divides the window after any change to either.**

§3b is kept even though §3a makes it belt-and-braces: §3a makes the *pipeline's* per-window
numbers right, §3b makes the notebook's *reading* of them right even if the lag is ever wrong
again. It also does not wait on `#25` — `_rfc3339` parses `min_record_time` client-side, so
it works today on a `text` mapping.

## Three things found while doing it, none of them in the handoff

1. **Gate 2's negative half compared two different windows.** `_absent` (rows *without*
   `last_write_bytes`) asked the **wall-clock** window while `_present` (rows *with* it)
   asked the **shifted label**, and the verdict compared the two totals anyway. Both now read
   the resolved label. A real bug, latent behind the offset.
2. **`INVARIANT_REMEDIES` is keyed by the invariant's name string, and the lookup has a
   default.** Renaming the invariant in cell 40 without re-keying cell 42 would have silently
   downgraded its remedy to *"see SCHEMA-report.md"* without complaining. The rename and the
   re-key must land in the same commit, which is why §4 and §5 are one.
3. **The handoff's §8-2 acceptance check is wrong and would fail a correct run.** It expects
   the fixed run's raw displacement "inside `[0, Interval_Sec)`". It will not be:
   `PHASE_LAG = Interval_Sec + 1.5`, so a correct run lands just **past** `Interval_Sec` by
   construction — 6.5 s against a 5 s tick. **The band that means anything is
   `[0, window_seconds)`**, and that is what the cell now asserts.

## The general shape, which is the part worth keeping

Three sentences went to another team as work items for a pipeline that had done nothing
wrong: the INCONSISTENT verdict, `auth_denied=0 (… the 403 fell to __errors__)`, and
`writes=1 granted=3`. The last two were **adjacent rows**, checked in the 2026-09-14 export:
the 403 at 07:29:00.626 sits on the role row labelled 07:28:30 reporting `auth_denied=1`, and
the three grant PUTs answered 201 at 07:29:00.55–.61 against a teardown DELETE at 07:29:31.35.

**A verdict string that appends a candidate cause will have that cause quoted as a
measurement.** Causes belong in `GATE_REMEDIES`, where they read as hypotheses. Both Gate 4
remedies now *lead* with "check the resolved window — it was this both times".

The same applies to the invariant: `record times fall INSIDE their own window` concluded
"outside means the window is assigned by PROCESSING time". True of the pipeline, but **not
what the check detects** — with `PHASE_LAG` it goes green with no pipeline change at all,
because what it measures is whether the *harness* fired inside the blind spot. Left under the
old name, `WINDOWS_TRUSTED` would have suppressed Gate 2 and Gate 4 findings forever against
a pipeline behaving as designed.

## Not touched, deliberately

`#25` (index template written and not applied, Lua written and not rolled — **Lua first**),
`#24` (`exception.frames` still missing), `REPORT-for-local-k8s.md` item 1 (**not needed
after §3**, and it contradicts the Lua's deliberate no-re-dating decision), and the 1800/30
revert.

## Open, and the only questions for the next run

1. **Gate 2 `last_write_bytes` must finally answer.** VOID for two runs and it is the
   feature; a VOID *after* §3a means the commit really did not reach the filter.
2. **Gate 4's two FAILs are expected to turn PASS.** If either still fails with the invariant
   green, that is the first window-scoped finding this project has had that is safe to quote.
3. **Settle the `__errors__` analyser question with one call** —
   `GET polaris-report-*/_analyze {"field": "resource", "text": "__errors__"}`. The guide says
   the standard analyser splits `__errors__` into `errors`; underscore is `ExtendNumLet` under
   UAX#29, so `StandardTokenizer` should emit it whole, and this run's own Gate 5 returned
   `requests=68 over 4 doc(s)`, which is not what a filter matching nothing produces.
   `.keyword` is still the right fix — on the case-folding grounds (`POST` → `post`), which
   were never in doubt.

## Verification, and its limits

`pytest` **911 passed, 45 skipped** before each of the five commits; every code cell compiles;
no `lbl(` call site remains. Run under a throwaway 3.12 venv — **the repo `.venv` symlinks its
interpreter outside the mounted folder and cannot be executed from a Cowork session.**
**The notebook itself was NOT executed: it needs the cluster.** Nothing here is evidence that
the fixed notebook runs end to end.

## Held back from the tree, needs Kade

- **`availability/polaris_availability_test.ipynb` carries a REAL principal credential** in
  cell 2 — `WATCHDOG_CLIENT_ID` / `WATCHDOG_SECRET` pasted over the `user11_client`
  placeholder. Not committed; it needs to go through `init_env` / an env var.
- **`diagnostics/api-sql-profile/04_explain_sweep.ipynb`** changes `latest_report()`'s
  `hits[-1]` to `hits[-2]`, making "latest" the second-newest report. Reads as a debugging
  leftover. Not committed.
- **Pre-existing, already in `HEAD`:** `03_api_index_matrix.ipynb` cell 3 line 76 carries a
  literal `clientSecret`. Wants its own scrub.
- **The `.git/index.lock` blocker returned** and was cleared the way `CLAUDE.md` says — by
  re-granting delete permission on the repo folder, not by handing the commit back.
