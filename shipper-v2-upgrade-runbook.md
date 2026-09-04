# Upgrading `fb-polaris-shipper` to policy v2 — a runbook

**Written to be read cold.** You need no context from the session that produced it.

**What this does:** installs a Fluent Bit retention policy and a flush report that are written
in `logging/fb-values.yaml` and **have never executed**. That makes this a *change*, not a fix.
The last time this repo installed configuration that had never run, it did so without noticing
for a day (`.memory/active-issues.md` #13) — so every phase below verifies against the running
object rather than against the file.

**Who runs it:** a human with `kubectl` and `helm`. Cowork sessions have no cluster reach.

**Roughly:** 10 minutes of commands, then a 30-minute wait for the first report, then the
coverage re-run.

---

## What is being switched on

Four changes to `logging/fb-values.yaml`, committed in `1eb0c99` and `854ec5d`:

1. **Rule 5 inverted.** Every POST is kept except `/oauth/tokens`, which is kept once per
   principal per KST day. Previously only POSTs on the table/view API were kept and every other
   successful POST was dropped — which silently discarded principal, role and catalog creation,
   both renames, namespace creation and property changes, and credential resets.
2. **The dedup key carries the principal and drops the query string.**
3. **`Alias` on all four filters**, so `fluentbit_filter_drop_records_total` is attributable.
4. **A flush report.** A `dummy` INPUT ticks every 30s; on each :00/:30 boundary the Lua filter
   replaces the tick with a summary record plus one record per table and per principal, on the
   stream `{app="polaris-shipper-report", level="REPORT"}`.

## Three runtime consequences that are expected, not faults

**The Fluent Bit counters reset.** They are per-process and `helm upgrade` replaces the pod. The
`Alias` change also renames the metric series. **You therefore cannot subtract across the
upgrade** — the pre-upgrade sample in Phase 0 is a *rate baseline over a known interval*, and
nothing more.

**The whole log file replays.** The tail offset DB lives on an `emptyDir` (#5b), pod replacement
empties it, `Read_from_Head true` re-reads from byte 0, and VictoriaLogs does not deduplicate on
ingest. Two things soften it, both by design: the replay runs *through* policy v2, so dedup
collapses much of it; and `kst_day` reads each record's own `_time`, so a replay spanning three
days is bucketed into three days rather than collapsed into one.

**The first report is not representative.** The replay lands in the first window, and dedup state
starts empty so the first read of every object that day is logged again. That window is emitted
with `partial_window=true` — it labels itself.

---

## Phase 0 — record the before-state

```bash
kubectl config current-context                    # must be exactly `orbstack`. Anything else: stop.
git -C ~/hynix/local-k8s status --short           # must be clean
helm -n datahub-hynix list                        # NOTE THE REVISION NUMBER — it is the rollback target
kubectl -n datahub-hynix get pod -l app.kubernetes.io/instance=fb-polaris-shipper -o wide
kubectl -n datahub-hynix exec deploy/benchmarks-polaris -- ls -l /deployments/logs/polaris.log
```

That last line is the size of the replay you are about to take.

A rate baseline needs two samples, not one:

```bash
kubectl -n datahub-hynix port-forward deploy/fb-polaris-shipper 2020:2020 &
curl -s localhost:2020/api/v1/metrics > /tmp/fb-before-t0.json
sleep 300
curl -s localhost:2020/api/v1/metrics > /tmp/fb-before-t1.json
```

## Phase 1 — render before installing

`helm lint` is not a render. This step is the one that would have caught #13.

```bash
cd ~/hynix/local-k8s
helm upgrade --install fb-polaris-shipper fluent/fluent-bit --version 0.58.1 \
  -n datahub-hynix -f logging/fb-values.yaml --dry-run --debug > /tmp/render.txt

grep -c ONCE_PER_DAY_POST_PATTERNS /tmp/render.txt   # expect >= 1
grep -c 'Name              dummy'   /tmp/render.txt   # expect 1
grep -c 'Match         polaris\.\*' /tmp/render.txt   # expect 2  (noise filter + output)
grep -c type_int_key                /tmp/render.txt   # expect 2
```

**Any of those returning 0: stop.** The values did not reach the template and nothing below is
meaningful.

## Phase 2 — upgrade

```bash
helm upgrade --install fb-polaris-shipper fluent/fluent-bit --version 0.58.1 \
  -n datahub-hynix -f logging/fb-values.yaml

kubectl -n datahub-hynix rollout status deploy/fb-polaris-shipper
kubectl -n datahub-hynix logs deploy/fb-polaris-shipper | head -60
```

**Read those logs before anything else.** A Lua syntax error or a rejected `type_int_key` line
appears here, and the pod either crash-loops or runs with the filter inert. An inert filter is
exactly #13 again, and it looks like success from the outside.

## Phase 3 — verify against the running object

```bash
kubectl -n datahub-hynix get cm | grep fb-polaris-shipper
kubectl -n datahub-hynix get cm <name-from-above> -o jsonpath='{.data}' \
  | grep -c ONCE_PER_DAY_POST_PATTERNS          # expect >= 1
```

Then confirm the tick is firing, and at what rate — `Rate 1` and `Interval_Sec 30` interact
confusingly in the `dummy` plugin and this was **not** verified before shipping:

```bash
curl -s localhost:2020/api/v1/metrics | grep polaris_report_tick
```

If it ticks once a second rather than once per 30s, that is **harmless** — a tick inside the
current window is dropped, so the report is unaffected — but it is ~86k no-op records a day
through the filter, and worth correcting in `Interval_Sec`. That the design tolerates it is the
reason the tick was made idempotent.

## Phase 4 — the two things no test could reach

Wait for one :00 or :30 boundary. Then, against VictoriaLogs:

```bash
kubectl -n logging port-forward svc/vlsingle-victoria-logs-single-server 9428:9428 &
```

| check | LogsQL | pass |
|---|---|---|
| the tick reaches the filter at all | `app:polaris-shipper-report \| stats count()` | ≥ 1 |
| **the array return splits into records** | `app:polaris-shipper-report \| stats by (report_type) count()` | three types: `summary`, `table`, `principal` |
| `type_int_key` worked | `app:polaris-shipper-report report_type:table reads:>0` | matches — i.e. not stored as `"482.0"` |
| the tick is not leaking raw | `tick:polaris-report` | **zero**. A hit means the Lua errored and the dummy record passed straight through |

**If the second row returns one record per window** carrying numeric-keyed fields instead of
three record types, this Fluent Bit build does not split an array return. It is documented
behaviour but was never run here. Fall back to a single summary record with the top-K tables
inline — about twenty lines in `build_report`.

Useful once it works:

```
app:polaris-shipper-report report_type:table     | stats by (table_path) sum(reads)
app:polaris-shipper-report report_type:principal | stats by (principal) sum(requests)
app:polaris-shipper-report report_type:summary   | fields window_start access_seen access_suppressed dedup_keys
```

## Phase 5 — re-run the coverage notebook

`polaris-learning/log-coverage`, per that project's README. Three things to expect so that none
of them reads as a regression:

- **The characterization test fails. It is built to.** Read the diff it prints, confirm it
  matches the four changes above, then update the test and `doc-log-coverage-results.md`
  **together** — a report nobody updated is worse than no report.
- The matrix flips in a checkable way: the eight mutations move **drop → keep**; query-string
  variants of a table read move **keep → drop**; second-and-later tokens per principal move
  **keep → drop**.
- **Settle the `app_lines` question in the same run.** One `stats by (loggerName)` says whether
  that column is read from VictoriaLogs — which decides whether "34 calls produce no record at
  all" was ever true — and simultaneously says where the 1,928 application lines come from,
  which is the input to the only remaining volume lever (`.memory/active-issues.md` #14a, #5b).

## Rollback

```bash
helm -n datahub-hynix rollback fb-polaris-shipper <revision from Phase 0>
```

**Rollback replaces the pod again, so it costs a second full replay.** Know that before deciding
a first-window anomaly is worth reverting for — the first window is flagged `partial_window=true`
precisely because it is expected to look wrong.

## What becomes decidable afterwards

- **The dedup cap.** The summary record carries `dedup_keys`, the live size of the
  principal-keyed dedup table. A week of it turns the placeholder `DEDUP_MAX_KEYS = 50000`
  fail-open guard into a measured choice.
- **The deferred P1 work** (`.memory/active-issues.md` #14): capping repeated 4xx and
  deduplicating collection listings were deferred because capping would hide volume. With
  per-table counts flowing, it no longer does — and the report says which of the two is worth
  doing first.
