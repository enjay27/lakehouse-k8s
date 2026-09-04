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
