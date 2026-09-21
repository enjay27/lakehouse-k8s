# HANDOFF — split the logging test: `local-k8s` verifies, `polaris-learning` makes traffic

**Written 2026-09-10 for a session starting cold, with BOTH folders connected.** Standalone: you
should not need to read the session that produced it.

**Connect both:** `~/hynix/polaris-practice/polaris-learning` **and** `~/hynix/local-k8s`. The
work is in the second and the traffic module is in the first; a session with only one of them
can do steps 0–1 and nothing after.

---

## 1. Where things stand in one paragraph

`polaris-learning/log-coverage/polaris_log_coverage_v2.ipynb` drives **63 Polaris operations ×
every reachable status = 286 cells**, in window-aligned phases, and verifies the result against
the **OpenSearch** side of the log pipeline with the gates from `GUIDE-schema-v3-testing.md`. It
runs. Run `1789008899` was the first whose verdicts were about the pipeline rather than about the
harness: **227/286 cells covered, correlation 286/286, four gates PASS, three FAIL, and the three
failures are real.** The decision now taken is to **split it**: traffic stays here, verification
moves to `local-k8s`, and `local-k8s` drives the whole test by calling in.

Read in this order:

1. `log-coverage/SCENARIO-logging-test.md` — **the design you are implementing.** 15 tests, the
   module contract, the report shape.
2. `log-coverage/PLAN-split-traffic-and-verification.md` — why the line falls where it does;
   §3.1 (request-id-keyed claims) is load-bearing and unchanged.
3. `log-coverage/PLAN-api-status-matrix.md` — how the 286-cell grid is built, and the corrections
   its own predictions earned.
4. `log-coverage/doc-api-status-matrix-results.md` — the last run of record.

---

## 2. What is already built, and where

| in `polaris-learning` | what it is | tests |
|---|---|---|
| `src/api_status_matrix.py` | the spec parser, the 286-cell grid, the request shaper, the executor | 53 |
| `src/os_report.py` | the OpenSearch query layer — **this is the file that moves** | 63 |
| `test_notebook_calls.py` | binds every client call in the notebook to its real signature | 3 |
| `log-coverage/polaris_log_coverage_v2.ipynb` | 43 cells: preflight, Gate 7, Gate 0, phases A–I, gates 1–6, two reports | — |
| `log-coverage/spec/` | the vendored 1.3.0 OpenAPI documents — the run's denominator | — |

`pytest` at the repo root: **120 passing, no cluster needed.** Every one of them is negative-
tested; if you change any of these files, break it deliberately once and check the suite notices.

---

## 3. The four findings the last run produced, and their status

**Real, and they belong to `local-k8s`:**

1. **`/api/catalog/v1/{cat}/transactions/commit` has no `RESOURCE_PATTERNS` rule.** Two rows,
   keeping its real path under `resource_kind: other`. That is the maintenance signal working;
   add the rule and re-run Gate 6.
2. **`min_record_time` is mapped `text`** in `polaris-report-2026.09.10`, permanently for that
   index — the Lua writes `""` on idle windows and OpenSearch typed the field from the first one.
   **An index template for `polaris-report-*` typing `min_record_time` / `max_record_time` as
   `date` fixes every future index and survives the `""`;** waiting for a fresh index does not,
   because at 30-second windows the first window of a day is almost always idle.
3. **Gate 4 failed twice:** `writes=1` after three successful grants (201, 201, 201), and
   `auth_denied=0` after a 403 on that same role in the same window — so the `ROLE_KINDS`
   exemption did not force the row. **Do not act on this yet:** Gate 7's Lua unit test asserts
   both behaviours pass in isolation, and the gate printed one number off one row. §5 below.

**Real, and they belong to Polaris, not to the pipeline** — the report currently mis-files these:

4. `createNamespace` and `createView` answer **500** (the PG-HA read-after-write signature, which
   `.memory/roadmap.md` calls "not provokable on demand" — provoked four times in one run).
   Malformed bodies produce 500 on six endpoints. `reportMetrics` answers **204 for a principal
   with no grants and for a table that does not exist**. `getConfig` answers 200 unauthorised.
   `planTableScan` / `fetchPlanningResult` / `cancelPlanning` / `fetchScanTasks` are **not routed
   on this build** — 404 to every cell including the unauthenticated one.

---

## 4. Do these first, in this order

### Step 0 — re-run the notebook as it now stands (30 minutes, needs only `polaris-learning`)

Three diagnostics were added after the last run and have **never executed**:

- **Gate 2** now prints every resource row in the commit's window, so it can finally say whether
  the field is missing from a row that exists or there is no table row at all. Those have
  opposite remedies and the old output could not tell them apart.
- **Gate 4** now prints every catalog-role row in scope plus what was driven, instead of one
  number off `_mine[0]`.
- **The 500 trace verdicts** now print record counts, loggers, levels and the raw vs flattened
  key sets.

```bash
cd ~/hynix/polaris-practice/polaris-learning/log-coverage
export OPENSEARCH_PASS=...
# reload the notebook in Jupyter, Restart & Run All
```

### Step 1 — settle the `absent` question with the output of step 0

Run `1789008899` reported `trace_verdict: absent` for **all eight** 500s — no application line at
all, which rule 2 forbids and which would be a serious pipeline finding.

**It is almost certainly not.** `lc.error_record_pair` filters records with
`r.get("mdc.requestId")`. VictoriaLogs flattens nested JSON on ingest; **OpenSearch keeps the
nesting in `_source`**, so that key is absent and the filter matched nothing. A *query* addresses
`mdc.requestId` either way, which is exactly why correlation reported 286/286 and hid it.
`os_report.Result.sources` now flattens at the boundary, and `raw_sources` prints the unflattened
shape beside it.

**Confirm from step 0's output** — the `record shape for nb-…` block. If the flattened keys carry
`mdc.requestId` and the verdicts move off `absent`, it was the dict access. If they stay `absent`
with records matched > 0, it is a real finding and it is serious.

### Step 2 — `make_traffic`, extracted from the notebook (in `polaris-learning`)

`src/make_traffic.py`, exactly the contract in `SCENARIO-logging-test.md` §3. It is a lift of
notebook cells 10–30 and 42; nothing in it is new logic.

Non-negotiables, each already paid for in this session:

- `window_seconds` is an **argument**. The traffic side never reads the ConfigMap.
- It imports **no** logging module. Add the test that asserts its import graph is clean —
  the boundary should fail in CI, not in review.
- `CONTRACT_VERSION = 1`.
- `incomplete` is returned, and cleanup runs in `finally`.
- The `TrafficRun` is written to `runs/traffic-<run>.json` as evidence, not as an interface.

### Step 3 — `logging/tests/` in `local-k8s`

`os_report.py` and its 63 tests move over as-is. The `Sink` interface, the 15 tests, the report
hook — `SCENARIO-logging-test.md` §§4–6.

**The gate on the whole plan:** it must reproduce **run `1789008899`'s verdicts exactly**, from
the same index, before a single verification cell is deleted here. Never remove the working thing
until the replacement matches it.

### Step 4 — only then, cut the notebook down

`polaris_log_coverage_v2.ipynb` → `polaris_api_traffic.ipynb`: a thin driver over `make_traffic`
with no gates in it. Update `CLAUDE.md` here to say where verification lives now, and both memory
trees.

---

## 5. Traps that have already cost a run each

- **A gate that reads an empty scope must be VOID, not PASS.** Two gates reported PASS on zero
  rows in run 1789007773. The gates cell now prints the scope count first. Carry this into
  `local-k8s`: UNPROVEN is a skip with a reason that reaches the report, never a silent green.
- **Field names are read, never assumed.** `window_start` is date-mapped, so
  `window_start.keyword` does not exist and every window-scoped query matched nothing;
  `min_record_time` is text in the same index. Two fields, same value shape, different mappings.
  `os_report.learn_field_names()` resolves them at preflight.
- **The oracle must be told which shipper it is measuring.** The DaemonSet runs `SCHEMA_VERSION`
  **3** and the Deployment runs **2**. `load_policy(FB_VALUES_PATH)` reads the Deployment's file.
- **Gate 7 is two commands.** It runs the *deployed script text*, read from `/tmp/polaris.lua`;
  without the extraction it reports "the filter is broken" and means "you gave me no filter".
  The notebook now extracts from the running ConfigMap, finding the key by content.
- **Check the request id echoed back.** Polaris returns `Polaris-Request-Id` unchanged (measured
  2026-09-09). An id that did not echo never reached the server as sent — a traffic fault — and
  without the check it looks exactly like a record the pipeline lost.
- **Never write a signature from memory.** Three of four were wrong once, including an argument
  order that does not raise. `test_notebook_calls.py` binds all 99 calls in 0.13s.
- **The Cowork file bridge can report a write it did not land.** `git status` is the check.
- **`\n` through a heredoc into a generator string into a notebook cell** produced a syntax error
  four times. The generator reads awkward cells from plain files (`nbgen/cell_gate7.txt`); do the
  same rather than fighting the escaping.

## 6. Environment

```bash
kubectl -n <os-ns> port-forward svc/<opensearch> 9200:9200
export OPENSEARCH_PASS=...          # never in a config file
```

`local` env only, and the drive **mutates**: a catalog, principals, roles, namespaces, a table
and a view are created and deleted. `WINDOW_SECONDS` is **30** and `Interval_Sec` **5** — both
TEMPORARY fast-run settings; revert them together when the run of record is done, and *after*
the matrix work, because the phase schedule depends on 30-second windows.

`pytest` runs from the repo root; every test file bootstraps `src/` onto `sys.path` itself, since
there is no `conftest.py`.
