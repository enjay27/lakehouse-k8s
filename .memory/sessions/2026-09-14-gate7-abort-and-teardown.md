# 2026-09-14 — Gate 7 aborted the run, and it hid the failure it aborted on

Asked to review `log-coverage/polaris_log_coverage_v2.ipynb`, "which doesn't work well".

## What it actually was

Not a subtle bug. The notebook **stops at cell 4** and has done since run `1789029836`
(2026-09-10). Cells 0-4 have outputs; **cells 5-42 have `execution_count: None`**. So "doesn't
work well" understated it: 38 of 43 cells have never executed in this file, and nothing behind
cell 4 has ever been exercised — the review can say what is wrong with cell 4 and cannot say
what is wrong with the rest, because nothing has ever looked.

Preflight (cell 2) was clean: Polaris up, OpenSearch 3.5.0 up, all four indices present. The
stop is Gate 7 — the Lua unit test against the deployed script text — failing 3 assertions.

## Three defects in one cell, and they compound

1. **The abort was disproportionate, and that was checkable.** Cell 4 raised on ANY Gate 7
   failure. The failures were `min_record_time ABSENT` / `max_record_time ABSENT` on an idle
   window. Gates 1-6 read `requests`, `writes`, `last_write_bytes`, `auth_denied`. The
   intersection is empty. The cell aborted the whole run over a defect that bears on none of
   what it was protecting.
2. **It could not show what it aborted on.** `detail = _out.strip()[-2500:]`, then
   `print(splitlines()[-20:])`. The harness printed `3 FAILURE(S)`; two were visible; the
   exception was raised about the third, which the cell had truncated away moments earlier.
   **The third failure is still unknown.** The fix makes it visible; it does not tell us what
   it is.
3. **The instrument built to answer the cell's own question never worked.** The markdown
   argues carefully that `SCHEMA-report.md` says 16 assertions and the guide says 46 and that
   whatever is printed is recorded verbatim. The regex was `(\d+)\s+assertion` — a word this
   harness does not print. It recorded `None` on every run it has ever made.

And a fourth: `GATE7` was **read by no other cell**, though cell 4's own text promises "the
findings cell records that the filter's own unit test never executed".

## What was changed

- Cell 4 rewritten: `[FAIL]` lines selected by CONTENT wherever they sit; assertions counted
  from the `[PASS]`/`[FAIL]` lines; failures classified against `GATE7_SCOPED`. Scoped-only ->
  `FAIL (scoped)`, carried into findings, run continues. Unscoped -> raise. **A reported count
  that does not match the visible `[FAIL]` lines -> raise**, because a failure you cannot read
  is a failure you cannot classify — which is exactly the state the old cell was in when it
  raised.
- `GATE7_SCOPED` is a list of defects **already measured and already in
  `REPORT-for-local-k8s.md`**. It is not an exemption list, and the raise message says so.
- Cell 12 registers `teardown_all` (idempotent, `atexit`) the moment the fixture exists. Cell 30
  delegates to it. Cleanup was previously reachable only by running every cell between the two,
  which is where `apimatrix1789031469_cat` and `probe_ns` came from.
- Cell 40 produces a Gate 7 finding, and the mapping finding now names the hypothesis below.

## The wrong turn worth recording

The plan said "add the Lua fix to `REPORT-for-local-k8s.md`". **That file is generated** by
cell 40 and would have been overwritten on the next run. The fix belongs in a `finding()` call,
not in the file. Anything written by hand into `REPORT-for-local-k8s.md` or
`doc-api-status-matrix-results.md` is temporary by construction.

Also checked and cleared, because it would have been easy to misattribute: the "coverage figure
that cannot fail" (`_row_from` stamping `verdict: "covered"`) is in `src/make_traffic.py`, on
the `run_traffic.py --profile` path. **v2 drives `mx.drive` -> `adjudicate`, which handles
MISSED correctly.** Do not "fix" it here.

## The hypothesis this produced

`min_record_time` has been carried in MEMORY.md as mapped `text`, "only an index template fixes
it". Gate 7 says the filter writes `""` there on idle windows. OpenSearch types a field from the
first document it ever indexes; at 30s windows the first window of a day is almost always idle;
`""` is not a parseable date. **So the empty string may be the CAUSE of the text mapping, not a
separate nuisance** — which would make the template a workaround and the Lua the fix, and would
mean any future index is one idle first-window away from the same thing on any field the filter
can empty.

Unsettled. The check needs no run: oldest `polaris-report-*`, oldest document, read
`min_record_time`. `""` confirms; a real timestamp refutes and sends the cause elsewhere.

## Verification

`911 passed, 45 skipped` in the Linux VM (unchanged; Kade's macOS run of the same tree: 956
passed). `black` 26.5.1 leaves `src/` unchanged and skips `.ipynb`. Every code cell byte-compiles
and the classifier was simulated against three shapes of harness output — all-scoped (continues),
one-hidden (raises), unscoped (raises).

**The notebook itself was NOT re-run.** No Cowork session can: no `kubectl`, no `lua5.4`, no
cluster reachability, `local-k8s` not mounted. Cell 4 needs Kade's machine.
