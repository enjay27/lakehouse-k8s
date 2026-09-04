# `log-coverage/` — what the Polaris log pipeline keeps, and what it throws away

## Concept

Polaris writes JSON to `/deployments/logs/polaris.log` on a PVC. A Fluent Bit Deployment
(`fb-polaris-shipper`, in `datahub-hynix`) tails it, splits the Quarkus access-log line into
typed fields, applies a **retention policy** written in Lua, and posts what survives to
VictoriaLogs.

```
Polaris (Quarkus, JDK21)
  └─ JSON per line → /deployments/logs/polaris.log        on PVC polaris-shared-logs-pvc
       └─ fb-polaris-shipper tails it read-only
            ├─ [modify]          message→_msg, timestamp→_time, add app=polaris
            ├─ [lua] polaris_access_log    parse the access-log line into fields
            ├─ [lua] polaris_noise_filter  decide what is kept      ← the thing under test
            ├─ [record_modifier] drop processName, loggerClassName, processId
            └─ [http] → VictoriaLogs /insert/jsonline
```

The policy — **v3, deployed 2026-09-04** (`fb-values.yaml` sha256 `89aa2624f1f5…`), first
match wins:

| # | rule | effect |
|---|---|---|
| 0 | tag `polaris.report` | becomes the **flush report** — see below |
| 1 | `level` is ERROR or WARN | keep |
| 2 | not an access-log record | keep, untouched |
| — | *every access-log record is **counted** here, before any decision* | |
| 3 | `http_status >= 400`, or unparseable | keep — **all of them, no cap** |
| 4 | PUT / DELETE / PATCH | keep |
| 5 | POST under `/api/management/` | keep — **all**; POST anywhere else, counted only |
| 6 | GET / HEAD, 2xx | counted only |
| 7 | anything else | keep |

**Per-day deduplication is gone.** No dedup keys, no KST buckets, no cap, and no per-pod state
for a shipper restart to lose. v3 closes the audit hole v2's first run measured — ten mutations
that produced no record at all, including a credential reset — because **in Polaris POST is the
create verb**, and rule 5 now keeps every management POST. It pays for that by turning
successful reads into counts.

### The scheduled flush report

A `dummy` INPUT tagged `polaris.report` ticks every 30 s into the same Lua filter instance. On
each `WINDOW_SECONDS` boundary the filter replaces the tick with an **array** of records and
resets its counters; they land on their own stream, `{app="polaris-shipper-report",
level="REPORT"}`, so `app:polaris` queries are unaffected.

**The tick rate is not the report period.** A tick inside the current window is dropped; only
the boundary emits. Schema v1: three record types (`summary`, `resource`, `principal`) on one
envelope, and the field names are contract.

The margin equality — `sum(resource.requests) == sum(principal.requests) == access_seen -
parse_errors` — is the schema's only real self-check, because `errors` deliberately overlaps
`reads` and `writes` (reads/writes counted by method, errors by status). `access_kept +
access_counted == access_seen` looks like a second check but is **tautological**: the filter
computes `access_kept` by subtraction. It is worth asserting only end to end, where it becomes
a transport check on Fluent Bit's array split and VictoriaLogs' ingest.

There is a **second, unrelated** Fluent Bit — a DaemonSet shipping container stdout to an
OpenSearch in Docker. It is not part of this test. A line present in OpenSearch and absent
from VictoriaLogs is that DaemonSet, not a finding here. `polaris_test_utils.search_logs` and
its siblings all talk to OpenSearch; `src/vlogs.py` is the one that talks to VictoriaLogs.

## Purpose

For every Polaris API: *if something went wrong on this endpoint tomorrow, would there be a
record of it?* The notebook drives the whole surface, then reports what was stored against
what the deployed policy says should have been.

Under **v2** the answer was "no" for ten endpoints before the notebook started, and
demonstrating that concretely was the point. **v3 closes that list** — every one of the
management mutations below is now stored — so the table is kept as the record of what was
wrong and what the fix had to reach:

| dropped, and it is a mutation | consequence |
|---|---|
| `POST /v1/principals` | a principal is created invisibly and deleted visibly |
| `POST /v1/principal-roles`, `POST /v1/catalogs/{c}/catalog-roles`, `POST /v1/catalogs` | same shape |
| **`POST /v1/principals/{p}/reset`** | **a credential reset leaves no trace at all** |
| `POST /v1/{c}/tables/rename`, `POST /v1/{c}/views/rename` | the path carries no `/namespaces/{ns}/tables` segment, so it misses the kept-POST patterns |
| `POST /v1/{c}/namespaces`, `POST /v1/{c}/namespaces/{ns}/properties` | namespace creation and property changes |
| `POST /api/catalog/v1/oauth/tokens` | by design — so "who authenticated" is unanswerable, only "who failed" |

Rule 5's own comment said the drop was *aimed at the OAuth token endpoint*; the blast radius
was never bounded to it. v3 bounds it by prefix instead — `POST` under `/api/management/` is
kept, everything else is counted — so the OAuth token endpoint is still dropped by design and
"who authenticated" is still unanswerable, while "who created a principal" now is.

**What v3 gave up to get there:** a successful read leaves no individual record, so per-call
access frequency and the timestamp of any single read are gone. They survive only as counts in
the window aggregate. That is the trade, and the notebook reports both halves.

And two things the pipeline cannot tell you whatever the policy says: **there is no `%D`**, so
no request's duration is recorded anywhere; and the access log is written when the response
is, so **a request that hangs leaves no line at all**.

## How to run

```bash
kubectl -n logging       port-forward svc/vlsingle-victoria-logs-single-server 9428:9428
kubectl -n datahub-hynix port-forward deploy/fb-polaris-shipper 2020:2020        # metrics
# optional, for the eventListener `events` table in cell 6:
kubectl -n datahub-hynix port-forward pod/benchmarks-postgresql-postgresql-ha-postgresql-0 5433:5432

./fetch_specs.sh          # once — vendors the 1.3.0 OpenAPI documents
uv run jupyter lab        # then Restart & Run All on polaris_log_coverage.ipynb
```

`local` env only, and it mutates: a catalog, principals, roles, namespaces, a table and a
view are created and then deleted. **The cleanup DELETEs are part of the test** — cell 9 is a
measurement, not tidying.

Two things invalidate a run and are recorded before and after: **Polaris scaling** (the HPA
allows 3 replicas appending to one log file — `local-k8s` #8) and **the shipper restarting**
(rule 6's dedup state is per-pod and in memory, so a restart re-logs the first hit per table).

### Prerequisites the notebook checks for you

- `victorialogs_url`, `fluentbit_metrics_url` in `src/config/common.yaml`; `fb_values_path` in
  `src/config/local.yaml` (see `local.example.yaml`).
- **A Lua interpreter.** macOS ships none — `brew install lua`, or a TeX install already
  provides `luatex --luaonly`. Cell 0 aborts without one, and says so.

## Why a Lua interpreter is a hard requirement

The "expected" column is not a table anyone typed. `log_coverage.Policy` extracts
`polaris_noise_filter` out of the **deployed** `local-k8s/logging/fb-values.yaml` and runs it,
over synthetic records shaped exactly like the ones Fluent Bit tails, in one interpreter so
rule 6's day-buckets build up in issue order. Same mechanism as
`local-k8s/logging/scripts/test-polaris-filters.py`, for the same reason: *the tests cannot
drift from what ships*.

There is deliberately **no Python re-implementation to fall back on**. A port that agrees with
itself is not evidence, and the first time it disagreed with the Lua the notebook would report
a pipeline finding that was really a translation bug.

This is also why `test_log_coverage.py` has two kinds of test. The **invariants** must hold
under any policy worth shipping — an error is never deduplicated away, every DELETE is kept, a
line that will not parse is kept rather than dropped. The **characterization** test records
what today's policy does and is *expected to fail when the policy changes*. When it does, read
the diff it prints, decide the change was intended, and update the test and
`doc-log-coverage-results.md` together — a report nobody updated is worse than no report.

## Status — 2026-09-04: v3 is deployed, the harness covers it, the run has not happened

**Run 1's finding is resolved.** The v2 policy was never installed — written 2026-09-03T08:26Z,
shipper pod up since 08:04Z, `helm upgrade` never run, 0 of 34 expected drops dropped. That is
history: the running ConfigMap now carries **v3** and matches the file (`89aa2624f1f5…`).

**What has been verified here, offline, against the deployed Lua:**

- **Every one of 14 representative records gets its v3 disposition.** Management POSTs are
  KEPT — the hole v2 left open is closed. Successful reads, `/config`, table LISTs, renames and
  the token exchange are COUNTED only.
- **The report's three record types, its margins, zero-carry and carry decay all hold**, driven
  through `_now_override` across three simulated windows without waiting for a boundary.
- **All six `resource_kind` values are reachable**, and `/namespaces/ns/tables/t/metrics`
  normalises onto `/namespaces/ns/tables/t` — v2 emitted two rows for one table.
- **An error never creates a resource key.** A 404 on a table nobody read lands in `__other__`,
  which is what keeps the margins exact, and the request is still stored in full by rule 3.
- **67 tests green** (`test_log_coverage` 40, `test_vlogs` 27).

**Two findings from building it, both about the filter rather than the harness:**

1. **A startup blind spot.** `report_tick` opens its first window on the FIRST tick, and
   `count_record()` returns immediately while `counts` is nil. Records processed between shipper
   start and that first tick are routed correctly but appear in **no report at all**. Bounded by
   the tick interval (30 s), and the window they land in is flagged `partial_window: true`. That
   is exactly the first report observed: seq=1, `access_seen: 0`, `partial_window: true`, for a
   pod that started at 07:12:37 inside the 07:00–07:30 window.
2. **`WINDOW_SECONDS` is not a parameter you can pass in.** The filter indexes windows with its
   own constant, so a caller that assumes 60 while the shipper runs 1800 crosses no boundary and
   gets an empty result rather than an error. `Policy.report_windows` now refuses a mismatch.

**Still open, and only the cluster can answer it: does Fluent Bit split the array?** The oracle
proves the filter *returns* three record types; only the running pipeline proves Fluent Bit
splits them into three records and that VictoriaLogs indexes their numbers as numbers. The one
window flushed so far had `access_seen: 0` — no traffic, so no resource or principal rows to
split into. **Cell 0b gates on it and cell 11 settles it**, because the run itself makes the
traffic.

**Next:** run the notebook. At the deployed 1800 that is ~3 boundaries and roughly 90 minutes of
mostly waiting; redeploy `local-k8s` with `WINDOW_SECONDS: 30` (and drop the dummy INPUT's
`Interval_Sec` to 5 alongside it, so a late tick cannot skip a whole window) and the same
notebook completes in minutes with every assertion unchanged.

## Files

| file | |
|---|---|
| `PLAN-log-coverage-v3.md` | **read this first** — policy v3, the scheduled report, and what the notebook must prove about both |
| `PLAN-log-coverage.md` | the v2 plan. Still the right description of how the oracle works; its policy table is superseded |
| `polaris_log_coverage.ipynb` | the run. Cells 0–15, linear, `Restart & Run All`. Cells 11–14 are the scheduled report and need real boundaries. |
| `fetch_specs.sh` | vendors the 1.3.0 OpenAPI documents (this Polaris serves none of its own) |
| `spec/` | the vendored documents — gitignored; `spec/inventory.json` is tracked |
| `doc-log-coverage-results.md` | written by cell 10, for someone who was not there |
| `../src/vlogs.py` | the VictoriaLogs client |
| `../src/log_coverage.py` | the deployed-Lua oracle, the three-way inventory, the tagged driver |
