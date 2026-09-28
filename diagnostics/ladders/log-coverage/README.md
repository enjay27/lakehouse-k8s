# `log-coverage/` — Polaris API traffic, and what the log pipeline keeps of it

Drives every Polaris operation the vendored OpenAPI specs name, at every status this build can
produce (a **286-cell grid**), and checks what reached OpenSearch through the Fluent Bit
DaemonSet (`benchmarks-fluent-bit`, schema v6). The logging side of the pipeline is described in
[`../../../logging/README.md`](../../../logging/README.md).

**History.** Until 2026-09-18 a second pipeline (`fb-polaris-shipper` → VictoriaLogs) ran beside the
DaemonSet, and the v1 notebook `polaris_log_coverage.ipynb` measured that one. Both are gone; the
v1 notebook and its documents were deleted on 2026-09-29 (see
[`../../../docs/DELETED-2026-09-29.md`](../../../docs/DELETED-2026-09-29.md)).

## The two halves

The run is split on purpose: **traffic** knows nothing about logging, and **verification** knows
nothing about how the traffic was made. `src/make_traffic.py` and `src/traffic_helpers.py` never
import `log_coverage` or `os_report`; `tests/test_make_traffic.py` asserts that import graph.
Why: [`PLAN-split-traffic-and-verification.md`](PLAN-split-traffic-and-verification.md).

| file | |
|---|---|
| `polaris_api_traffic_v1.ipynb` | **traffic only** — drives the grid (phases B–J), waits once for a window boundary, and prints the run id, phase times and request ids the verifier needs |
| `run_traffic.py` | the same traffic from a shell: `--dry-run` builds all 286 requests and contacts nothing; `--profile smoke` / `full` drive Polaris (**mutates**) |
| `polaris_log_coverage_v2.ipynb` | traffic **and** verification against OpenSearch, phased on report-window boundaries |
| `preflight_os_report.sh` | read-only: do the `polaris-*` indices exist, which report schema is flowing, which Lua is running |
| `fetch_specs.sh` | vendors the OpenAPI documents into `spec/` (**gitignored** — a fresh clone must run it before `pytest`, or 13 tests fail and 49 error on `SpecUnavailable`); `spec/inventory.json` is tracked |

## Documents

| file | |
|---|---|
| [`SCENARIO-logging-test.md`](SCENARIO-logging-test.md) | the test scenario both halves implement — cited by `make_traffic`, `traffic_helpers` and `log_coverage` |
| [`PLAN-split-traffic-and-verification.md`](PLAN-split-traffic-and-verification.md) | the boundary between the halves |
| [`PLAN-api-status-matrix.md`](PLAN-api-status-matrix.md) | the design of the 286-cell grid (the v2 notebook's plan) |
| [`PLAN-log-coverage.md`](PLAN-log-coverage.md) | how the oracle in `src/log_coverage.py` works |
| [`REPORT-for-local-k8s.md`](REPORT-for-local-k8s.md) | the traffic run's report format, as the verifier reads it |
| [`doc-what-this-test-measures.md`](doc-what-this-test-measures.md) | what the 286 cells cover, what is logged, what is summarised |
| [`doc-api-status-matrix-results.md`](doc-api-status-matrix-results.md) | results of v2 run `1789436277` |

## How to run

```bash
./fetch_specs.sh                                                   # once per clone
uv run python diagnostics/ladders/log-coverage/run_traffic.py --dry-run
export OPENSEARCH_PASS=...          # v2 notebook only; never in a config file
uv run jupyter lab      # Restart & Run All on polaris_api_traffic_v1.ipynb or the v2 notebook
```

`local` env only. Both notebooks **mutate**: a catalog, principals, roles, namespaces, a table and a
view are created and deleted, and 500s are provoked (~300 calls). The cleanup DELETEs are part of
the measurement.

Pin Polaris to one replica first: the HPA can scale it mid-run (`active-issues` `#39`).

## The oracle and its fixture

`src/log_coverage.py` computes the **expected** column by running the real Lua in a Lua interpreter
rather than a Python port: a port that agrees with itself is not evidence. Its Lua comes from
`tests/fixtures/fb-values-shipper.yaml`, the uninstalled shipper's values (policy v2/v3), which is
**not** the live DaemonSet's `releases/fluent-bit/polaris_access_log.lua` (v6). Moving the oracle
onto the live Lua is open as merge seam M3. Needs `luajit`, `lua` or `luatex --luaonly`
(`brew install luajit`).
