# Test scenario — `local-k8s` runs the logging test, `polaris-learning` supplies the traffic

**Status: PROPOSED.** Scenario first, no code. Supersedes the two-step manifest handoff in
`PLAN-split-traffic-and-verification.md` §3 — see §8 for what changed and why.

Kade, 2026-09-10:

> run logging test → it will call polaris project's `make_traffic` module → test will verify
> logs in its expected module (either OpenSearch or Victoria, **Polaris doesn't care**) → make a
> report of this test

That is the right shape, and the parenthesis is the part that makes it right.

---

## 1. Why this beats the manifest handoff

| | two-step manifest | one test, calling in |
|---|---|---|
| entry points | two, in two repos, with an ingest wait between | **one**: `pytest` in `local-k8s` |
| stale input | a verifier can run against yesterday's manifest and not know | impossible — it drove the traffic itself |
| who picks the sink | the traffic side had to know it wrote for OpenSearch | **the test does. The traffic side has no logging concept at all** |
| `window_seconds` | traffic read it from the ConfigMap (a pipeline fact, on the wrong side) | **passed in by the caller**, which owns it |
| dependency | a file format both sides must track | a module API, versioned, checked at import |

**And one consequence that may not have been intended, which is the strongest argument for it:**
the same test suite can run against **both shippers**. `benchmarks-fluent-bit` (DaemonSet →
OpenSearch, v3) and `fb-polaris-shipper` (Deployment → PVC → VictoriaLogs, v2) currently run
different schema versions and have never been tested by the same code. Behind a `Sink`
interface they are two parameters of one test run, and a divergence between them becomes a test
failure instead of a discovery six weeks later.

---

## 2. The one thing to keep from the manifest

The `TrafficRun` is still **written to disk** as it is returned. Not as a contract between the
repos — as evidence. A run that is only a Python object cannot be re-verified after a gate is
fixed, cannot be compared against last week's, and cannot be looked at when someone asks why
the report said what it said. `src/run_manifest.py` already says it: *the manifest carries
values, the live cluster carries truth, never one without the other.*

So: `drive()` returns the object **and** writes `runs/traffic-<run>.json`. Re-verifying an old
run against a live index is then a supported thing to do, and the sink can even be a different
one than the run was verified against first.

---

## 3. The module contract

`polaris-learning/src/make_traffic.py` — the only thing `local-k8s` imports.

```python
CONTRACT_VERSION = 1          # local-k8s asserts on this at import. A row-shape change
                              # bumps it and breaks LOUDLY at collection, not at assertion.

def config_from_env(env="local") -> dict
    """Polaris URL, realm, credentials, MinIO, bucket -- via this repo's own init_env,
    so secrets stay in this repo's gitignored config and local-k8s never holds them."""

PROFILES = {
    "full":  "all 63 operations x every reachable status -- 286 cells, ~9 windows",
    "smoke": "~12 cells, one window: is the pipeline answering at all",
    "gate2": "one commit alone, then one DELETE alone -- the feature and its negative half",
    "gate4": "three grants and a denial on one role, one window",
}

def drive(config, *, window_seconds, profile="full", run=None,
          on_row=None, dry_run=False) -> TrafficRun
```

`window_seconds` **is an argument.** The traffic side never reads the ConfigMap, never learns
what a report window is, and never imports `os_report` or `vlogs`. It is told "align your phases
to a 30-second grid" by the side that knows why.

### `TrafficRun`

```python
contract_version, run, driven_at, profile
polaris        {url, realm, version}
fixture        {catalog, namespace, table, view, doomed_*}
identities     {admin, runner, denied}   # names, never secrets
window_seconds                            # echoed back, so the record says what it aligned to
windows        {first, last, distinct}
phases         [{name, start, end, straddled, cells, seconds}]
calls          [{request_id, echoed, echo_ok, op_id, method, path, api, target,
                 status, response_bytes, principal, phase, window, issued_at, verdict}]
claims         [ ... request-id-keyed, see PLAN §3.1 ... ]
coverage       {covered, missed, error, by_target: {...}}
build_findings [ ... Polaris facts: the 500s, the unrouted endpoints, the authz oddities ... ]
incomplete     None | "why the drive stopped early"
```

**Three rules about that shape, each of which this session has already paid for:**

1. **No keep/drop expectation.** Which calls are counted is a fact about the deployed Lua. The
   test computes it from the filter it owns; the traffic side does not get an opinion, so the
   two repos cannot hold two answers about one policy.
2. **`incomplete` is a first-class field.** A drive that dies at call 40 must still return what
   it drove and clean up. Every downstream check then reports UNPROVEN rather than FAIL — a
   half-run is not evidence of a broken pipeline.
3. **`build_findings` belong to Polaris, not to the pipeline.** `createNamespace` answering 500,
   `reportMetrics` answering 204 unauthorised, four endpoints unrouted: those are facts about
   the build. The report shows them as context, clearly labelled, and `local-k8s` never gets
   handed them as work.

**A guard, not a convention:** a test in `polaris-learning` asserts that `make_traffic`'s import
graph contains no logging module. The boundary should fail at CI, not at review.

---

## 4. The scenario, end to end

```
$ cd ~/hynix/local-k8s && pytest logging/tests -q --sink=opensearch --profile=full
```

**Arrange** — before a single call is driven:

| step | fails how |
|---|---|
| resolve the sink from `--sink` | unknown name → error at collection |
| read the deployed Lua from the running ConfigMap | no ConfigMap → **abort**: nothing below is interpretable |
| `WINDOW_SECONDS`, `SCHEMA_VERSION` from that text | unreadable → **abort** |
| the pod is not older than the ConfigMap | older → **abort**: the file is deployed, the policy is not |
| the sink answers, indices exist, fields resolve | not → **abort** with which check failed |
| `import make_traffic; assert CONTRACT_VERSION == 1` | mismatch → **abort** at collection |
| the target is not PROD | → **abort**. The drive mutates. |

**Act** — one session-scoped fixture:

```python
traffic = make_traffic.drive(cfg, window_seconds=WINDOW_SECONDS, profile=profile)
```

**Settle** — the sink waits for its own ingest to stop moving. Not a sleep: poll until the count
for this run's ids is stable, and record how long that took. "0 records after 30s" and "0 records
after 0.4s" are different claims.

**Assert** — §5.

**Report** — §6.

---

## 5. The tests, and what makes each one fail

Every one has a stated failure mode; a check whose failure you cannot state is not a check. Each
resolves to **PASS**, **FAIL** or **UNPROVEN** — and UNPROVEN is a `skip` with a reason that
reaches the report, never a silent green.

| # | test | PASS | FAIL | UNPROVEN |
|---|---|---|---|---|
| T0 | the running policy is the file's policy | ConfigMap text matches `values.yaml` | differs | no kubectl |
| T1 | the filter passes its own unit test | `test-schema-v3.lua` green against the ConfigMap text | any assertion | no `lua5.4` |
| T2 | the index carries the deployed schema version | a row at `SCHEMA_VERSION` exists | none | — |
| T3 | the numbers are numbers, the names resolve | `requests`/`errors`/`response_bytes` numeric; every term field resolvable | text-typed numeric | field never carried |
| T4 | **every error call is stored in full** (rule 3) | each 4xx/5xx `request_id` found | any missing | `echo_ok` false → traffic fault, not pipeline |
| T5 | **every counted call is absent** (rule 6) | no individual record for calls the filter counts | one present | filter says nothing was counted |
| T6 | margins reconcile, per window | `sum(resource)==sum(principal)==access_seen-parse_errors` | any window off | no window had traffic |
| T7 | the array splits into three record types | `{summary, resource, principal}` | fewer | no window with `access_seen>0` |
| T8 | `last_write_bytes` == the claimed commit | equals the `response_size` of the claim's `request_id` | differs / absent after a commit | claim's window straddled |
| T9 | a delete-only window leaves it **absent** | field absent | present, or `0` | no delete-only window in the run |
| T10 | classification | `api_kind` ∈ {management, catalog, mixed}; `resource_kind` never `management` | either violated | no resource row |
| T11 | role `writes` == privileges granted | equals the claim's id count | differs | no catalog-role row |
| T12 | a denial forces the role row | `auth_denied ≥ 1` on that role | falls to `__errors__` | no denial in the run |
| T13 | the two synthetic buckets differ | `__errors__` requests==errors; `__other__` absent or 0 | mixed | neither present |
| T14 | every path has a classification rule | only synthetic keys under `resource_kind: other` | a real path appears | no resource row |
| T15 | the schema's own invariants | `report_seq` contiguous per host; record span ≤ window | a gap; a span over | fields absent |

**T4 and T5 are the pair that matters** and neither means anything alone: rule 3 promises every
error is kept, rule 6 promises successful reads are not. Testing only the first reports a policy
that stores everything as perfect.

**T4's UNPROVEN condition is the boundary doing its job.** If `echo_ok` is false for a call, its
id never reached the server as sent — a traffic fault, in the other repo, and the test says so
instead of reporting a lost record.

---

## 6. The report

`logging/reports/REPORT-<run>-<sink>.md`, written by a `conftest.py` hook so it is produced even
when tests fail.

```
# Logging pipeline test -- run <id>, sink <opensearch|victorialogs>

Policy      sha256 ..., SCHEMA_VERSION 3, WINDOW_SECONDS 30, pod ...@<start>
Traffic     profile full, 286 calls, 63 operations, 7 windows, incomplete: no
Settled     3,325 records after 6s

## Results          15 tests: 11 pass, 2 fail, 2 unproven
| test | verdict | detail |

## Pipeline findings          <- what local-k8s must change
## Unproven, and why          <- never silently green
## Build findings, from the traffic side   <- Polaris facts, NOT local-k8s's work
## Coverage of the API surface             <- context: 227/286 cells
```

Two report sections that must never merge: **pipeline findings** are this repo's work,
**build findings** are Polaris's. Today's `REPORT-for-local-k8s.md` mixes them and sends four
Polaris facts to the wrong repo.

---

## 7. Risks, each with its handling

1. **Import coupling between two checkouts.** `local-k8s` must find `make_traffic`. Handling:
   an explicit configured path (`polaris_learning_path` in the test config), plus the
   `CONTRACT_VERSION` assert at collection. Never a bare `sys.path` guess — a silently-missing
   module becomes a skipped test suite, and this session has already lost a run to a check that
   passed by being unable to look.
2. **Version skew.** Handled by (1)'s assert. A row-shape change bumps the constant.
3. **Secrets.** `config_from_env()` runs inside `polaris-learning` and reads its gitignored
   config. `local-k8s` never holds a Polaris credential.
4. **The drive mutates.** `require_not_prod` on the traffic side is not enough once another repo
   is the caller; the test asserts the target too, before importing.
5. **Fixture leakage on failure.** `drive()` cleans up in `finally` and reports `incomplete`. A
   test session that dies must not leave a catalog behind.
6. **A slow drive across a settling sink.** Settle polls to stability and records the wait; the
   phases already record whether one straddled a window boundary.

---

## 8. What this changes in `PLAN-split-traffic-and-verification.md`

- §3's manifest stops being a **contract between two runs** and becomes a **record of one**.
  Still written, still versioned, no longer the interface.
- §3.1 (request-id-keyed claims) is unchanged and is now load-bearing: `claims` is how the test
  knows what the traffic meant without knowing Polaris.
- §7's migration order changes: steps 3–5 become "extract `make_traffic` from the notebook's
  traffic cells" and "stand up `logging/tests/` calling it", with the same equivalence gate —
  it must reproduce run 1789008899's verdicts before the notebook's verification cells are cut.
- The notebook here does not disappear. It becomes a thin driver over `make_traffic` for driving
  traffic by hand, with no gates in it.

## 9. Sign-off

1. Scenario as written — one `pytest` entry point in `local-k8s`, `make_traffic` as a library?
2. `Sink` abstraction with both OpenSearch and VictoriaLogs implementations, so the same tests
   run against both shippers — worth it now, or OpenSearch only and add the second later?
3. `--profile` (full / smoke / gate2 / gate4) as proposed, so a two-minute smoke run exists?
4. `TrafficRun` still written to `runs/` as evidence?
