# 2026-09-10 (session 10) — the traffic side could not be written without importing the thing the boundary forbids

Step 2 of `log-coverage/HANDOFF-split-logging-test-2026-09-10.md`, and only step 2.
`local-k8s` was not connected, so steps 3 and 4 were out of reach by construction;
step 0 (re-run the notebook) needs a `kubectl port-forward` this session cannot see.
Kade signed off on step 2 alone before any file was touched.

## What the plan did not know, and the session had to measure first

**The import-graph guard could not have been written.** `SCENARIO-logging-test.md` §3
asks for a test asserting that `make_traffic` imports no logging module. But every
function the traffic cells call — `tag_clients`, `request_id`,
`provision_run_principal`, `elect_drive_identity`, `deprovision_run_principal`,
`provokers_500`, `drive_500`, `classify_500s` — lived in `log_coverage.py`: 3,099
lines and 70 defs that is the v1 VictoriaLogs verification module *and* half a
traffic module. The guard would have failed on day one, and the only honest fixes
were to move the traffic half out or to scope the guard until it meant nothing.

So **792 lines moved to `src/traffic_helpers.py`, verbatim**, and `log_coverage`
re-imports every name. The dependency runs one way — `log_coverage -> traffic_helpers`,
never back — and `polaris_log_coverage.ipynb`, the v1 RUN OF RECORD, keeps working
unedited. The test for that (`test_log_coverage_still_re_exports_every_moved_name`)
is what makes the claim checkable rather than hopeful.

`window_bounds` and `seconds_to_boundary` are the other half of the same problem:
twelve lines of epoch `//` that live in `os_report`, so importing them would have put
the whole OpenSearch client in the traffic side's graph. They are duplicated on
purpose, and a parametrised test compares the two copies — two copies drift, and the
drift here would be invisible until a window-scoped query matched nothing.

## The wrong turn, and it compiled

The extraction was done by an AST script computing line spans. Deleting `_as_int`
afterwards, **the span arithmetic ate one extra line: `def _epoch_of(iso_z):`.** Its
body — an indented `try:` — was then absorbed as dead code after `disposition`'s
`return`, because Python allows blank lines inside a function body. **`py_compile`
passed. `_epoch_of` simply ceased to exist**, and `check_invariants` would have
raised `NameError` at the first window-bounds check of the next run.

Caught by a check that was not about that at all: comparing the set of top-level
names in `git show HEAD:src/log_coverage.py` against the new file. It reported one
lost name. The lesson is the cheap one — **after moving code, diff the names, not the
line count** — and there is now a stronger version of it in the session's method: a
`difflib` comparison asserting every unmoved line survived in order, which found two
blank-line discrepancies and nothing else.

## What was built

| file | what | tests |
|---|---|---|
| `src/traffic_helpers.py` | the traffic half of `log_coverage`, moved verbatim | (its callers') |
| `src/make_traffic.py` | `CONTRACT_VERSION`, `config_from_env`, `PROFILES`, `TrafficRun`, `drive()` | 62 |
| `test_make_traffic.py` | the boundary, the contract, the twins, cleanup | — |
| `test_notebook_calls.py` | the signature binder now walks `make_traffic` too, not only the notebook | +1 |

`response_bytes` was added to BOTH driver row shapes (`api_status_matrix.execute` and
`traffic_helpers.call_once`). The contract lists it per call and the
`last_write_bytes` claim is a comparison against a size; neither driver recorded one.

**`drive()` is a lift of notebook cells 10–30 and 42.** What is new is small and
worth reviewing: the claims in `PLAN §3.1`'s request-id-keyed shape, `incomplete`
plus `finally`-cleanup, `build_findings` (Polaris facts, kept out of the pipeline's
work list per SCENARIO §6), and profile selection.

Two judgements made while lifting, both of which a reviewer should agree with or
overturn:

- **The delete phase makes no claim when the DELETE returns a body.** The `size > 0`
  rule is what separates a commit from a drop, so a non-empty 204 makes the negative
  case VOID. `incomplete` says so. A claim nobody can resolve is worse than no claim.
- **The `auth_denied` claim is only made if the denial actually came back 401/403.**
  A denial that was not denied cannot force the role row, and asserting on it would
  report a traffic fault as a pipeline fault — the same shape as the `echo_ok` split.

## Verification, and what it is not

**`pytest` was not run, on either machine, and that is a constraint rather than a
choice.** The `.venv` is macOS-aarch64 (`#!/Users/kade/...`) and cannot execute in the
Cowork Linux VM; that VM has no egress (`uv` fails to reach both `pypi.org` and
`github.com`); the cloud container has no `pytest` and **`pypi.org` answers 403 through
the org egress policy**, so it cannot be installed there either.

So the suite ran under a **~150-line stand-in** implementing only what this repo uses
(`raises`, `mark.parametrize`, `mark.skipif`, `fixture` with module scope / autouse /
yield-teardown, `skip`, `tmp_path`), over a staged copy: **222 passed, 0 failed, 45
skipped** — the 45 are `test_log_coverage`'s Lua tests, which need
`local-k8s/logging/fb-values.yaml`. Before this session the same files were 120.

**Every new check was then broken deliberately, one at a time — 12 mutants, all 12
caught**, including the two that matter most: a logging import at module scope in
`make_traffic`, and one hidden *inside a function* of `traffic_helpers`. A guard that
only walks module-scope imports would pass the second, and `make_traffic` imports its
clients inside `drive()`.

**What this does not establish:** that real `pytest` agrees with the stand-in, and that
`drive()` drives. Nothing here has touched Polaris. The first real run tests the
module as much as the pipeline — the same sentence session 9 wrote about the notebook.

`black` was run (version **26.3.1** in the container; `pyproject.toml` pins
`>=26.5.1`, so `black .` on Kade's machine may still produce a small diff). `isort`
was not available; per `CLAUDE.md` black runs last anyway.

## Open, in order

1. Kade runs `uv run pytest` — the real gate.
2. Step 0/1 of the handoff: re-run `polaris_log_coverage_v2.ipynb` and settle whether
   the eight `trace_verdict: absent` were the dict access or a real finding.
3. Step 3: `logging/tests/` in `local-k8s`, calling `make_traffic.drive`. Needs both
   folders connected. The gate on the whole plan is unchanged: it must reproduce run
   `1789008899`'s verdicts exactly before a verification cell is deleted here.
4. Step 4: cut the notebook down to a thin driver. Not before 3.
