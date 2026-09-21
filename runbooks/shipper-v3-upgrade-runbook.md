# Upgrading `fb-polaris-shipper` to policy v3 — a runbook

**Written to be read cold.** You need no context from the session that produced it.

**What this does:** installs a Fluent Bit retention policy and a flush report that are written
in `logging/fb-values.yaml` and **have never executed**. That makes this a *change*, not a fix.
The last time this repo installed configuration that had never run, it did so without noticing
for a day (`.memory/active-issues.md` #13) — so every phase below verifies against the running
object rather than against the file.

**v2 was never deployed.** It was superseded by v3 before installation; nothing in the cluster
has ever run either. Do not look for a v2 baseline.

**Who runs it:** a human with `kubectl` and `helm`. Cowork sessions have no cluster reach.

**Roughly:** 10 minutes of commands, then a 30-minute wait for the first report, then the
coverage re-run.

---

## The policy being switched on

```
0. the report tick (tag polaris.report) ....... becomes the flush report
1. level ERROR or WARN ........................ keep
2. not an access-log record ................... keep (untouched)
--- every access-log record is COUNTED here, before any decision ---
3. http_status >= 400, or unparseable ......... keep — ALL of them, no cap
4. PUT / DELETE / PATCH ....................... keep — all
5. POST under /api/management/ ................ keep — all
   POST anywhere else .........................  counted only
6. GET / HEAD, 2xx ............................  counted only
7. anything else .............................. keep
```

It preserves **100% of authorization failures** (every 401 and 403 is a full record via rule 3)
and **100% of identity and grant mutations** (management POST, every PUT, every DELETE). What
becomes a count is traffic that succeeded routinely. Rule 5 is split that way because in
Polaris **POST is the create verb** — `create_principal`, `create_principal_role`,
`create_catalog_role` and `reset_principal_credentials` are all POSTs.

Alongside it, a **flush report** every 30 minutes on the :00/:30 boundary: a `dummy` INPUT
tagged `polaris.report` ticks every 30s, reaches the same Lua filter instance, and on a window
boundary is replaced by an array of records — one `summary`, one `resource` per resource, one
`principal` per principal — on the stream `{app="polaris-shipper-report", level="REPORT"}`.
Schema v1; `schema_version` is on every row.

## Three runtime consequences that are expected, not faults

**The Fluent Bit counters reset.** They are per-process and `helm upgrade` replaces the pod. The
`Alias` change also renames the metric series. **You cannot subtract across the upgrade** — the
pre-upgrade sample in Phase 0 is a *rate baseline over a known interval*, nothing more.

**The whole log file replays.** The tail offset DB lives on an `emptyDir` (#5b), pod replacement
empties it, `Read_from_Head true` re-reads from byte 0, and VictoriaLogs does not deduplicate on
ingest. Under v3 most of the replay is absorbed — every successful read and catalog POST becomes
a count rather than a record — but **every error and every mutation in the file replays as a
full record.** Expect duplicates of exactly those.

**The first report window is unrepresentative, and says so.** It carries `partial_window=true`.
The replay is counted into whichever wall-clock window it happens to land in, which is why the
summary carries `min_record_time` / `max_record_time`: a replay window spans days, so it is
self-evidently a replay rather than an unexplained spike.

---

## Phase 0 — record the before-state

```bash
kubectl config current-context                    # must be exactly `orbstack`. Anything else: stop.
git -C ~/hynix/local-k8s status --short           # must be clean
helm -n datahub-hynix list                        # NOTE THE REVISION NUMBER — the rollback target
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

grep -c RESOURCE_PATTERNS          /tmp/render.txt   # expect >= 1  (v3 Lua present)
grep -c 'MGMT_PREFIX'              /tmp/render.txt   # expect >= 1  (rule 5 split)
grep -c 'Name              dummy'  /tmp/render.txt   # expect 1     (the report tick)
grep -c 'Match         polaris\.\*' /tmp/render.txt  # expect 2     (noise filter + output)
grep -c type_int_key               /tmp/render.txt   # expect 2
grep -c DEDUP_MAX_KEYS             /tmp/render.txt   # expect 0     (v2 leftovers absent)
```

**Any of the first five returning 0, or the last returning non-zero: stop.** The values did not
reach the template, or an older revision is being rendered, and nothing below is meaningful.

## Phase 2 — upgrade

```bash
helm upgrade --install fb-polaris-shipper fluent/fluent-bit --version 0.58.1 \
  -n datahub-hynix -f logging/fb-values.yaml

kubectl -n datahub-hynix rollout status deploy/fb-polaris-shipper
kubectl -n datahub-hynix logs deploy/fb-polaris-shipper | head -60
```

**Read those logs before anything else.** A Lua syntax error or a rejected `type_int_key` line
appears here, and the pod either crash-loops or runs with the filter inert. An inert filter is
#13 again, and from the outside it looks like success.

## Phase 3 — verify against the running object

```bash
kubectl -n datahub-hynix get cm | grep fb-polaris-shipper
kubectl -n datahub-hynix get cm <name-from-above> -o jsonpath='{.data}' \
  | grep -c RESOURCE_PATTERNS                 # expect >= 1
```

Then confirm the tick is firing, and at what rate — `Rate 1` and `Interval_Sec 30` interact
confusingly in the `dummy` plugin and this was **not** verified before shipping:

```bash
curl -s localhost:2020/api/v1/metrics | grep polaris_report_tick
```

If it ticks once a second rather than once per 30s, that is **harmless** — a tick inside the
current window is dropped, so the report is unaffected — but it is ~86k no-op records a day
through the filter and worth correcting in `Interval_Sec`. That the design tolerates it is the
reason the tick was made idempotent.

## Phase 4 — the two things no test could reach

Wait for one :00 or :30 boundary, then:

```bash
kubectl -n logging port-forward svc/vlsingle-victoria-logs-single-server 9428:9428 &
```

| check | LogsQL | pass |
|---|---|---|
| the tick reaches the filter at all | `app:polaris-shipper-report \| stats count()` | ≥ 1 |
| **the array return splits into records** | `app:polaris-shipper-report \| stats by (report_type) count()` | three types: `summary`, `resource`, `principal` |
| `type_int_key` worked | `app:polaris-shipper-report report_type:resource requests:>0` | matches — i.e. not stored as `"482.0"` |
| the tick is not leaking raw | `tick:polaris-report` | **zero**. A hit means the Lua errored and the dummy record passed straight through |
| **the margins agree** | compare `sum(requests)` over `report_type:resource` and over `report_type:principal` for one `_time` | equal, and equal to `access_seen - parse_errors` |

That last row is the schema's own self-check. If the two margins disagree, the report is
miscounting and no trend built on it can be trusted — find out before anyone builds a dashboard.

**If the second row returns one record per window** carrying numeric-keyed fields instead of
three record types, this Fluent Bit build does not split an array return. It is documented
behaviour but was never run here. Fall back to a single summary record with the top-K resources
inline — about twenty lines in `build_report`.

Useful once it works:

```
report_type:resource  | stats by (resource) sum(reads)                    -- hot resources
report_type:resource  | stats by (_time, resource) sum(reads)             -- the trend, per resource
report_type:principal | stats by (_time, user_principal_name) sum(reads)  -- the trend, per user
report_type:resource resource_kind:table errors:>0 | stats by (resource) sum(errors)
report_type:summary   | fields _time access_seen access_counted partial_window min_record_time max_record_time
```

`user_principal_name` is deliberately the same field name the access-log records use, so one
filter spans a principal's stored 403s and their per-window counts.

## Phase 5 — re-run the coverage notebook

`polaris-learning/log-coverage`, per that project's README. Three things to expect, so that none
of them reads as a regression:

- **The characterization test fails. It is built to.** Read the diff it prints, confirm it
  matches the rule table above, then update the test and `doc-log-coverage-results.md`
  **together** — a report nobody updated is worse than no report.
- The matrix flips in a checkable way: all successful GET/HEAD move **keep → drop**; catalog
  POSTs (`create_table`, `commit_table`, both renames, `report_metrics`, `oauth/tokens`) move
  **keep → drop**; management POSTs (`create_principal`, `create_principal_role`,
  `create_catalog_role`, `reset_principal_credentials`) move **drop → keep**; every 4xx/5xx,
  PUT and DELETE is unchanged.
- **Settle the `app_lines` question in the same run.** One `stats by (loggerName)` says whether
  that column is read from VictoriaLogs — which decides whether "34 calls produce no record at
  all" was ever true — and simultaneously says where the ~1,928 application lines come from,
  which is the input to the only remaining volume lever (`.memory/active-issues.md` #14a, #5b).

## Rollback

```bash
helm -n datahub-hynix rollback fb-polaris-shipper <revision from Phase 0>
```

**Rollback replaces the pod again, so it costs a second full replay.** Know that before deciding
a first-window anomaly is worth reverting for — the first window is flagged
`partial_window=true` precisely because it is expected to look wrong.

## What becomes decidable afterwards

- **Retention.** Once successful reads live only as counts, the report is the thing worth
  keeping and the access logs are the thing you can afford to lose. VictoriaLogs single has one
  global retention and still no disk cap (#7), so multi-month trend eventually wants these
  counts in a TSDB — roadmap step 7.
- **The 95.5%.** Every rule above governs the access log, which is ~4.5% of stored records. The
  remaining volume is application lines, and #5b already fixes the direction: route the DEBUG
  SQL records, never turn them down. The `loggerName` distribution from Phase 5 is what starts
  that design.

There is **no dedup cap to decide.** v2 would have needed one; v3 stores no successful read
individually, so there is no per-key state and nothing to bound.
