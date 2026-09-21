# 2026-09-04 — policy v3 and the scheduled flush report, built (session 7)

Standalone plan: `log-coverage/PLAN-log-coverage-v3.md`. This is the narrative, including the
wrong turns, which is the part that does not survive summarising.

## What changed under us

v2 was never deployed — that was run 1's whole finding. v3 **is** deployed (ConfigMap carries
`89aa2624f1f5…`, confirmed by cell 0 on Kade's machine). It deletes per-day dedup entirely,
keeps every `POST` under `/api/management/`, counts every successful read, and adds a scheduled
flush report on its own stream.

## The wrong turns, in order

1. **I grepped the Lua for `DEDUP_MAX_KEYS` without stripping comments** and reported the v2
   constant as surviving into v3. It is a comment saying the machinery was *removed*. Cost one
   round trip. The gate cell now strips comments before grepping.
2. **My first oracle driver ticked only at the END.** No array came back and I nearly reported
   the array-split gate as failed. The cause is real and is now a documented property:
   `report_tick` opens its first window on the FIRST tick, and `count_record()` returns
   immediately while `counts` is nil — so records fed before any tick are routed by the policy
   but counted into no window. In production that is a startup blind spot bounded by the tick
   interval, and it explains the first observed report exactly (seq=1, `access_seen: 0`,
   `partial_window: true`, pod started 07:12:37 inside the 07:00–07:30 window).
   `Policy.run` takes an ordered event list *because* of this.
3. **`Policy.report_windows(seconds=...)` silently did nothing when `seconds` disagreed with the
   deployed constant.** The filter indexes windows with its own `WINDOW_SECONDS`, so asking for
   60s windows against an 1800s filter crosses no boundary and returns an empty dict — an empty
   result, not an error. Now `window_seconds` is read off the script and a mismatch raises.
4. **`classify_paths` returned `(None, None)` for every path but the first**, because from the
   second window on the report also carries the PREVIOUS window's keys at zero. "The only
   resource row" was the wrong selector; the row with a non-zero request count is the right one.
   Zero-carry biting the code that was written to test zero-carry.
5. **My own tick-rate test placed a tick ON the boundary** (`30*i + 60` reaching 1830 > 1800) and
   reported `mid58`, which reads as a filter fault. Ticks now stop strictly inside the window.
6. **The margin invariant I planned was partly decorative.** `build_report` computes
   `access_kept = access_seen - access_counted`, so that identity cannot fail in the oracle. The
   only real self-check is the resource/principal margin pair. Kept the first one anyway, but
   only as an end-to-end transport check, and said so in the docstring.

## What is verified, and what is not

**Verified offline, against the deployed Lua** (`luatex`, `local-k8s` mounted read-only):
14/14 record dispositions match v3; three report types with agreeing margins; zero-carry and
carry decay across three simulated windows; all six `resource_kind` values; `/metrics` folding
onto its table; errors landing in `__other__` without creating a key; `partial_window` as the
string `"true"`. 67 tests green.

**NOT verified:** that Fluent Bit splits the filter's array return into separate records, and
that VictoriaLogs indexes their numbers as numbers. Only the running pipeline can answer it. The
one window flushed so far had `access_seen: 0` — no traffic, so nothing to split into. Cell 0b
gates on it; cell 11 settles it.

## Gate discipline, unchanged

`pytest` / `black` / `isort` are still not runnable from Cowork: the device VM has no network to
install them and `.venv` is macOS. Tests ran under a stand-in runner in `/tmp` (a `pytest` shim
providing `fixture`/`skip`/`raises`) over the two changed files only — the other suites need
`monkeypatch` and `tmp_path`, which the shim does not provide, so their failures under it are
shim artefacts and were not counted. Line lengths were brought under 88 by hand in place of
`black`. **The real gate is Kade's `pytest`.**

## Verified live, 08:23–08:25Z, and what that cost to learn

`verify_v3_settings.ipynb` (throwaway, deleted after) ran the five DoD questions against the
deployed fast-run settings. 20 of 22 checks passed first time; **both failures were mine**, and
neither would have been visible from oracle output alone:

1. **`check_invariants` read `_stream` and `_stream_id` as schema drift.** VictoriaLogs stamps
   them onto every record it returns. Against oracle rows the strict field check was correct;
   against STORED rows it flagged all six as carrying unexpected fields. It would have fired on
   every window of the real run, and it would have read as the report drifting from its own
   schema — the exact failure the check exists to catch, produced by the check itself.
2. **The skipped-window check compared across a restart and a settings change.** It flagged
   `07:30:00Z -> 08:14:00Z`, which is the 1800→30 switch and the shipper restart that carried
   it, not a late tick. A gap only means a skipped window **within one process at one window
   length**; it now filters on `hostname` and `window_seconds` before believing one.

The lesson is the same one this repo keeps relearning in different clothes: **an oracle that
agrees with itself is not evidence.** Both bugs live exactly at the seam between what the filter
emits and what the pipeline stores, which is the one place the offline oracle cannot look.

Everything else held. The array splits, the numbers are indexed as numbers, zero-carry and decay
work end to end, and 68 tests pass under real `pytest` — closing the `NOT VERIFIED` line on the
two previous commits. Incidental but worth remembering: the OAuth token exchange is attributed
to principal `-`, because `%u` writes a dash when nothing is authenticated yet.

## Run 1 of the v3 notebook, and the same mistake twice

The report is good: 132 calls, correlation exact on all of them, 5 of 5 management POSTs stored,
zero-carry and decay confirmed live, no gaps, invariants clean. What is worth writing down is
the shape of the four defects, because three of them are the same kind of mistake.

**The 403 probe went out untagged.** `probe()` tagged `[pc, ic, adm_pc, adm_ic]`; the call used
`denied_ic`. Run 1 found precisely this fault in the negative cell, and the fix there was to add
the client to the tag list. I then wrote a NEW probe using the same untagged client and the
matrix reported `EXPECTED STORED, ABSENT` — a harness gap wearing a finding's clothes, for the
second time in two sessions. The fix is now structural: `TAGGABLE` is built once from every live
client, and `probe()` uses it.

**Two probes tested something other than their label.** `get_config()` with no warehouse returns
400, so three calls labelled "counted" were kept by rule 3; and the view probe reads a view the
happy path has already renamed and dropped. Neither is a pipeline fault and both would have been
quoted as one.

**The 500 probe stopped provoking a 500**, so the run produced no WARN or ERROR record at all and
the report printed "0 seen" and "0 of 0 carried an exception object". Those read as answers. They
are absences of evidence, and the difference matters most for the stack-trace question, which is
the single most valuable thing this notebook could settle. The report now says NOT ANSWERED and
names the probe.

The pattern in all four: **a probe whose label asserts what it is testing, while the call it
makes has drifted away from that.** The oracle cannot catch this class at all — it predicts what
the deployed Lua does with the record the call PRODUCED, so a call that produced the wrong record
gets a perfectly correct prediction. Only reading the status column against the label catches it,
which is what this review was.
