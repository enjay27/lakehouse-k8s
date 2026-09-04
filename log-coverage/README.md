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

The policy, first match wins:

| # | rule | effect |
|---|---|---|
| 1 | `level` is ERROR or WARN | keep |
| 2 | not an access-log record | keep, untouched |
| 3 | `http_status >= 400` | keep — **outranks dedup, deliberately** |
| 4 | PUT / DELETE / PATCH | keep |
| 5 | POST on the table/view API | keep; **every other successful POST is DROPPED** |
| 6 | GET / HEAD on a table or view | first per **KST** day, rest dropped |
| 7 | everything else | keep |

There is a **second, unrelated** Fluent Bit — a DaemonSet shipping container stdout to an
OpenSearch in Docker. It is not part of this test. A line present in OpenSearch and absent
from VictoriaLogs is that DaemonSet, not a finding here. `polaris_test_utils.search_logs` and
its siblings all talk to OpenSearch; `src/vlogs.py` is the one that talks to VictoriaLogs.

## Purpose

For every Polaris API: *if something went wrong on this endpoint tomorrow, would there be a
record of it?* The notebook drives the whole surface, then reports what was stored against
what the deployed policy says should have been.

**The answer is "no" for ten endpoints before it starts**, and demonstrating that concretely
is the point:

| dropped, and it is a mutation | consequence |
|---|---|
| `POST /v1/principals` | a principal is created invisibly and deleted visibly |
| `POST /v1/principal-roles`, `POST /v1/catalogs/{c}/catalog-roles`, `POST /v1/catalogs` | same shape |
| **`POST /v1/principals/{p}/reset`** | **a credential reset leaves no trace at all** |
| `POST /v1/{c}/tables/rename`, `POST /v1/{c}/views/rename` | the path carries no `/namespaces/{ns}/tables` segment, so it misses the kept-POST patterns |
| `POST /v1/{c}/namespaces`, `POST /v1/{c}/namespaces/{ns}/properties` | namespace creation and property changes |
| `POST /api/catalog/v1/oauth/tokens` | by design — so "who authenticated" is unanswerable, only "who failed" |

Rule 5's own comment says the drop was *aimed at the OAuth token endpoint*. The blast radius
was never bounded to it.

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

## Result — run 1, 2026-09-04: the policy is not running

**Nothing is dropped.** 0 of 34 expected drops dropped: 20 identical table GETs → 20 stored,
three successful token requests → 3 stored, every create / rename / credential reset → stored.

The policy is not broken; it has never been installed. `logging/fb-values.yaml` gained
`polaris_noise_filter` in `local-k8s` commit `2120ed9` at **08:26:18Z on 2026-09-03**. The
shipper pod has been running since **08:04:06Z**, from `60b94d9` — which carries the access-log
parser and `record_modifier` and no noise filter. That predicts exactly what was measured:
parsed fields present, nothing dropped. `helm upgrade` was never run.

So the table above is still what the policy *says*; none of it is what the pipeline *does*.
**Cell 0 now aborts** when the running ConfigMap does not carry the policy, rather than leaving
it to be inferred from the shape of the results.

Settled by the same run, and these do not depend on the policy:

- **`Polaris-Request-Id` is honoured end to end** — correlation is EXACT. One `list_catalogs`
  produces **15 records** sharing the id: its access-log line plus 14 application lines. The
  architecture spec's §7 end-to-end trace query works today.
- **Client-side latency**, the only source there is with no `%D`: 122 calls, median ~18 ms,
  slowest ~77 ms. Ingest lag to first record: **2.0 s**.
- **8 ERROR records, none carrying an `exception` object.** Not yet a verdict — it does not
  separate "Quarkus never logged the throwable" from "the pipeline dropped it". Settle it
  against the raw file:
  `kubectl -n datahub-hynix exec deploy/benchmarks-polaris -- grep -c stackTrace /deployments/logs/polaris.log`
- **`mgmt.reset_principal_credentials` → 403 even as root**, reproducing the "admin is not a
  superset" finding — and it is also one of the calls the policy would discard.

Three of run 1's apparent findings were harness bugs and are fixed: the replay dedup keyed on
`mdc.requestId` (one call is many records, so 2,049 collapsed to 122 and every `stored` capped
at 1), the 403 case used a client that was never tagged, and the `http_status` type check was
meaningless because VictoriaLogs returns every field as a string. 117 tests green.

**Next:** `helm upgrade` the shipper, then re-run. Treat that upgrade as a change, not a fix —
it switches on a filter that has never executed once.

## Files

| file | |
|---|---|
| `PLAN-log-coverage.md` | the task plan, and the corrections it makes to `local-k8s/POLARIS-API-LOG-COVERAGE-NOTEBOOK.md`. **Read this first.** |
| `polaris_log_coverage.ipynb` | the run. Cells 0–10, linear, `Restart & Run All`. |
| `fetch_specs.sh` | vendors the 1.3.0 OpenAPI documents (this Polaris serves none of its own) |
| `spec/` | the vendored documents — gitignored; `spec/inventory.json` is tracked |
| `doc-log-coverage-results.md` | written by cell 10, for someone who was not there |
| `../src/vlogs.py` | the VictoriaLogs client |
| `../src/log_coverage.py` | the deployed-Lua oracle, the three-way inventory, the tagged driver |
