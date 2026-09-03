# 2026-09-03 — Polaris → VictoriaLogs pipeline: read of the design spec, audit of the tree

Kade brought in `polaris_logging_detailed_architecture_spec.md` (his own prior design work,
now filed at `logging/polaris-logging-architecture-spec.md`) and asked for enhancements to
the deployed VictoriaLogs + Fluent Bit. Nothing was changed this session — plan-first, and
this session has no cluster reach.

## What the spec designs

A dedicated log path for Apache Polaris, deliberately separate from the cluster-wide console
forwarder: Polaris writes NDJSON to a **shared PVC** (`/logs/polaris.log`), a **single-replica
Fluent Bit `Deployment`** tails that file, parses the Quarkus access-log line into typed
fields, **drops repeat `GET .../tables/{t}` hits inside a 24h window with a stateful Lua
filter** (~11M/day of the ~140M/day peak), and posts NDJSON to **VictoriaLogs**
`/insert/jsonline`. Sized for 10M–140M records/day at 30d retention. §8 also sketches
`vmalert` alerting and log→metric downsampling; none of §8 exists yet.

The dedup filter is the interesting part of the design and the part the tree has none of.

## The audit — read of the tree as committed at `6d21056`

**The VictoriaLogs path currently carries nothing, and it is a chain of three, not one bug.**

1. `polaris/values.yaml` has `logging.file.enabled: false`. `polaris/templates/configmap.yaml:132-147`
   turns that into an explicit `quarkus.log.file.enabled=false` in `application.properties`.
   The `QUARKUS_LOG_FILE_JSON_ENABLED=true` env var at `values.yaml:193` sets the *format* of
   a handler that is switched off; it does not switch it on. **No `polaris.log` is written.**
2. Same flag gates `polaris/templates/storage.yaml`, so the chart's own log PVC does not
   render either. Both `polaris/values.yaml:200` and `logging/fb-values.yaml:15` name
   `polaris-shared-logs-pvc` — **nothing in this repo creates a PVC by that name.** The
   chart, if enabled, would render `benchmarks-polaris-logs` instead.
3. `quarkus.http.access-log.enabled` is never set anywhere. `polaris/values.yaml:302` sets
   the *category level* `io.quarkus.http.access-log: INFO`, which is not the same switch.
   **So the access log the spec's regex parser and Lua deduplicator consume does not exist.**

Consequence: everything that reaches OpenSearch today does so by the *console* path — Polaris
stdout (JSON, via `QUARKUS_LOG_CONSOLE_JSON_ENABLED=true`) → container log → the Fluent Bit
DaemonSet. That is why the DaemonSet is confirmed working while the VictoriaLogs half is not.

**A PVC cannot be shared across namespaces.** PVCs are namespaced objects. Polaris runs in
`datahub-hynix`; if the shipper Deployment is installed into `logging`, it cannot mount
`polaris-shared-logs-pvc` at all, whatever the name resolves to. The shared-file design
forces the shipper into `datahub-hynix` and leaves only VictoriaLogs in `logging` — which is
what `environments.md` already says the `logging` namespace is for.

## Other findings, in the values as written

- `logging/fb-values.yaml` tail has **no `DB`** and `Read_from_Head true`. Every restart
  re-reads the file from byte 0 and re-posts it. VictoriaLogs does not deduplicate on
  ingest, so restarts multiply records.
- `Skip_Long_Lines Off` with `Buffer_Max_Size 10MB`: in Fluent Bit that combination makes
  the tail **stop on the file** when a line exceeds the buffer, rather than skip the line.
  JSON records carrying a stack trace are exactly the ones that get long.
- The `[SERVICE]` block loads `parsers.conf` only — no `custom_parsers.conf`. Any parser
  added under `config.customParsers` would be written to disk and never loaded.
- `_stream_fields=app,level,loggerName`: with ~12 categories at DEBUG in
  `polaris/values.yaml`, `loggerName` is a high-cardinality stream field. VictoriaLogs
  charges for stream count, not for field count — `loggerName` stays fully searchable as an
  ordinary field.
- No `storage.type filesystem` and no output-side buffer limit: a VictoriaLogs restart drops
  whatever is in the memory queue.
- `logging/victoria-values.yaml` sets `retentionPeriod: 30d` but no
  `retention.maxDiskSpaceUsageBytes`. Retention by age alone does not protect a 50Gi PV;
  a full PV wedges the pod, and **`persistence.size` is now-or-never** (standing constraint).
- `type: LoadBalancer` on 9428 publishes an **unauthenticated ingest *and* query endpoint**
  onto the Mac. VictoriaLogs single has no auth of its own.
- Sizing is the spec's, i.e. sized for 140M records/day: 50Gi PV, 4Gi memory limit. This is
  one OrbStack node that already needs >7GB for the full platform set.

## Security, found while reading

`fluent-bit/values.yaml` carries `HTTP_Passwd Str0ngP@ssw0rd123!` in the clear, twice, and
it is committed. That is the Zero Hardcoded Credentials rule, broken in a tracked file.
Filed as active issue #4. `polaris/values.yaml:408-409` carries `minioadmin/minioadmin` the
same way.

## What this settles

`active-issues.md` #2 asked which sink Fluent Bit ships to. From the repo the answer is
**both, from two different releases**: `fluent-bit/values.yaml` is the DaemonSet → OpenSearch
in Docker, `logging/fb-values.yaml` is a single-replica Deployment → VictoriaLogs. It is not
one shipper choosing a sink. Still to be confirmed against the cluster that both releases are
actually installed — that is a `helm list` away and this session cannot run it.

## Not done

No values file was edited. No cluster command was run and none could be — `device_bash` is an
isolated VM with only the repo mounted. Every conclusion above is a read of the tree, not an
observation of the cluster.

---

## CORRECTION, same session — the audit above is wrong about the cluster

Kade produced a VMUI screenshot: **1,636 records over 30 minutes, `_stream:{app, level}`,
Polaris DEBUG SQL and INFO lines, and a Quarkus access-log line among them.** The pipeline
works. "The VictoriaLogs path has no input" is false as a statement about the cluster.

What it is *not* wrong about is the tree: `logging.file.enabled: false` is still what
`polaris/values.yaml` says, and `quarkus.http.access-log.enabled` still appears nowhere in
it. So the live release was configured somewhere other than these files — an overlay, a
`--set`, or a hand edit. **This is active-issues #1 caught in the act**: the repo is not
evidence of what is deployed, and I treated it as evidence. The lesson the repo already
carries — verify against the running object, never against the values file — applies to
reading just as much as to writing, and I read.

#5 is rewritten accordingly: not a dead pipeline, a repo/cluster divergence.

## What the screenshot does establish, on its own terms

- **`loggerName` is absent.** The stream-fields panel lists `app` (1.6K) and `level` (1.6K)
  and nothing else, while the output URI asks for `_stream_fields=app,level,loggerName`.
  No record carries it. Whatever shape these records have, it is not the Quarkus JSON
  formatter's, which always emits `loggerName`.
- **All 1,636 land in a single 15s bucket** at 15:35 with 30 empty minutes behind them,
  and their `_time` values carry **nanosecond** precision (`15:35:13.911654221`) where
  Quarkus emits milliseconds. Both point the same way: `_time` is being assigned at
  **ingest**, not taken from the record — so `Rename timestamp _time` is not landing, real
  event time is lost, and a shipper restart re-stamps everything to "now". Consistent with
  the missing tail `DB` replaying the file from byte 0.
- **The access log's `%b` emits `-`** for zero-byte responses — visible as `... 200 -`.
  The spec's regex ends `(?<response_size>\d+)`, which cannot match `-`, so exactly the
  responses with no body would fail to parse. Needs `[\d-]+`.
- **The local volume driver is not the table-poll traffic the spec's Lua dedup targets.**
  It is DEBUG SQL from `org.apache.polaris.persistence.relational.jdbc.DatasourceOperations`
  (`polaris/values.yaml:290`) — nearly every row in the capture. ~1.6K per 30min of catalog
  activity. The 11M/day `GET /tables/` figure is a production number with no local analogue.

Unsettled, and one VMUI JSON-tab click away: the actual field shape of a record, which
decides whether `loggerName` and event time are recoverable by fixing the shipper or need
the file format changed at Polaris.

---

## SECOND CORRECTION — the raw record, and two more of my inferences falsified

Kade pulled two records from the VMUI JSON tab. They settle the shape question and overturn
two claims from the first correction, both of which were inferred from the histogram rather
than observed.

```json
{ "_msg": "query: INSERT INTO POLARIS_SCHEMA.ENTITIES (...) VALUES (?, ...)\n  5790236183908929095\n  ...",
  "_stream": "{app=\"polaris\",level=\"DEBUG\"}",
  "_time": "2026-09-03T06:35:13.911654221Z",
  "date": "1788417313.911832",
  "app": "polaris", "level": "DEBUG",
  "hostName": "benchmarks-polaris-585587454b-nhzdr",
  "loggerName": "org.apache.polaris.persistence.relational.jdbc.DatasourceOperations",
  "loggerClassName": "org.slf4j.spi.DefaultLoggingEventBuilder",
  "mdc.realmId": "POLARIS",
  "mdc.requestId": "dce356e7-539d-444f-a854-c9b17cf4a0a2_0000000000000000107",
  "processId": "1", "processName": "/usr/lib/jvm/java-21-openjdk-.../bin/java",
  "sequence": "3724", "threadId": "27", "threadName": "executor-thread-1" }
```

**Wrong: "`_time` is stamped at ingest."** It is the record's own time.
`_time` = `...13.911654221Z`; Fluent Bit's own `date` = `1788417313.911832` =
`...13.911832Z`. They differ by **178µs**, with `_time` the *earlier* of the two — an ingest
stamp cannot precede the shipper's own read. So `Rename timestamp _time` works, and the
nanosecond precision is Quarkus's: the JBoss JSON formatter prints the `Instant` at full
precision, not milliseconds as I assumed. The single 15:35 histogram bar is simply
**15:35 KST = 06:35 UTC** — a real burst of catalog activity (`sequence` 3723/3724, so
~3.7k records since JVM start), not a replay.

**Wrong: "no record carries `loggerName`."** Every record carries it. What the stream-fields
panel showed was the *stream* — `{app, level}` — and the live output is therefore configured
`_stream_fields=app,level`, **not** the `app,level,loggerName` in `logging/fb-values.yaml`.
Another repo/cluster divergence, and one where the cluster is already right: `loggerName`
belongs as a searchable field, not a stream field.

The lesson, twice over in one session: a rendered UI is a projection. `_stream` is not the
field list, and a histogram bucket is not a clock. Read the record.

## What the record actually establishes

Working, and better than either the repo or the first audit implied:

- **Quarkus JSON file logging is on and correct** — this is unmistakably the JBoss JSON
  formatter's shape.
- **`mdc.requestId` and `mdc.realmId` are both present.** The spec's §7 end-to-end trace
  query works *today*. `polaris/values.yaml` has `logging.mdc: {}`, so this too came from
  outside the repo.
- `_msg`, `_time`, `_stream`, `hostName`, `threadName`, `sequence` all sound.

Genuinely wrong, now on evidence rather than inference:

- **`date` duplicates `_time` on every record.** Fluent Bit's `json_date_key` default.
  `json_date_key false` removes it.
- **`processName` is a 60-byte absolute JVM path repeated on every record**; `loggerClassName`
  and `processId` are near-valueless too. A `record_modifier` `Remove_key` pays for itself at
  volume.
- **The DEBUG SQL records are enormous** — the sample `_msg` is ~1.5KB: full statement, every
  bound parameter, and an embedded JSON blob escaped four levels deep. This is the volume
  driver, and it puts **bound parameter values into the log** — S3 paths and internal
  properties here, which is the shape of a leak even where this instance's contents are dull.
- **`response_size` is `-`** (`"... 200 -"`), so the spec's `(?<response_size>\d+)` cannot
  match a zero-byte response. Needs `[\d-]+`.
- **No latency token** in the access-log pattern, so the spec's own P99-by-endpoint panels
  cannot be built from it.

Still unverified either way: the tail `DB`, `Skip_Long_Lines`, and buffering settings — the
records give no evidence about them, and the repo's copy of `fb-values.yaml` has now been
shown twice not to be the live config.

---

## Built: access-log field extraction

Kade's ask: split the Quarkus access-log line into fields, only for records from
`io.quarkus.http.access-log`, keeping IP, user, method, path, status and body size, and
dropping the timestamp and the HTTP version. (He said "loggerClass" — the value lives in
**`loggerName`**; `loggerClassName` on those records is `org.jboss.logging.Logger`, which
identifies nothing.) DEBUG SQL is being turned off in production, so the volume question
is closed and did not need routing after all.

**Why Lua and not the spec's `parser` filter.** Fluent Bit's `parser` filter matches on
**tag**, not on a field value, so restricting it to one logger needs `rewrite_tag` plus an
emitter plus a second tag in the output `Match` — three moving parts to express one
condition. A Lua filter expresses it directly and, unlike a regex parser, can normalise
`%b`'s `-` to `0` (CLF means zero bytes, not unknown) and emit real integers. Two bugs in
the spec's §4.3 also argued against reusing it: `Inline` is not a Fluent Bit key (the
option is `code`, or `script`), and `Reserve_Data On` without `Preserve_Key On` consumes
`message`, so every access-log record would have reached VictoriaLogs with an empty `_msg`.

`logging/scripts/polaris_access_log.lua`, applied via
`--set-file luaScripts."polaris_access_log\.lua"=...`. Deliberately **not** inlined into
`fb-values.yaml`: one authoritative copy, and one that can be run directly — which it was.
The container has no Lua, but the device VM ships `luatex`, and `luatex --luaonly` is a
standalone Lua 5.3. Six cases, all passing:

| input | result |
|---|---|
| `... "DELETE /api/management/v1/principals/... HTTP/1.1" 404 133` | all six fields, `http_status=404`, `response_size=133` |
| `... 200 -` (zero-byte body) | `response_size=0` — the case the spec's `(?<response_size>\d+)` could never match |
| `10.0.0.5 - - [...] "GET /...tables/t1?snapshots=all HTTP/1.1" 200 51234` | query string kept in `api_path`, `user_principal_name=-` |
| IPv6 client, `HTTP/2.0` | parsed; version consumed and discarded |
| access-log line in an unknown format | `access_log_parse_error: true`, record kept |
| a `DatasourceOperations` record | returned untouched, return code 0 |

Field names are the spec's (`client_ip`, `user_principal_name`, `http_method`, `api_path`,
`http_status`, `response_size`) so §7's LogsQL recipes work unchanged. `type_int_key` is
set on the two numeric fields — without it Fluent Bit encodes Lua numbers as doubles and
VictoriaLogs stores `404.0`, which `http_status:>=500` then misses.

Two decisions worth keeping: `_msg` is preserved rather than consumed, because the raw line
is what you read when the parse is wrong; and a non-matching line from that logger is
**tagged, not dropped** — `access_log_parse_error:true` is findable, a silent drop is not.
Every fault in this session was silent, which is the argument.

Still not reconciled: `fb-values.yaml` carries this change as *intent*. The live release has
differed three times, so `helm get values` before installing.

---

## The reconciliation, and a third correction — this one narrowing a claim, not reversing it

Kade ran the diff. `helm -n datahub-hynix get values fb-polaris-shipper` against
`logging/fb-values.yaml`: **identical**, apart from `helm`'s alphabetical key ordering and
exactly one real difference — the live output streams on `_stream_fields=app,level` where
the file asked for `app,level,loggerName`. That one line had already been fixed here, from
reading the `_stream` in a record.

So the file matched revision 10 all along. The claim in the previous two commits — "the repo
has been shown three times not to match the live release" — was **over-reach**: it said *the
repo* on evidence about *`polaris/values.yaml`*. One file diffing clean is precisely the
outcome a claim that broad could not have predicted. #5 is narrowed to what is actually
unaccounted for: `polaris/values.yaml`, and `polaris-shared-logs-pvc`.

A useful side effect: the shipper's tail settings are now **confirmed deployed** rather than
suspected. `Read_from_Head true` with no `DB`, and `Skip_Long_Lines Off`, are what is
running. Both are still worth changing, and now on evidence.

## Everything in the values file, no `--set`

Kade's rule: no `--set` flags, the values file is the definition. So the Lua moved inline
into `luaScripts:` in `fb-values.yaml` and the standalone `.lua` was deleted — chart 0.58.1
renders `luaScripts` into a ConfigMap at `/fluent-bit/scripts/<key>`, which is where the
filter's `script` path already pointed, so the filter block is unchanged.

That would normally cost the testability that justified the separate file. It does not,
because the test now reads the Lua **out of the values file**:
`logging/scripts/test-access-log-parser.py` loads `fb-values.yaml`, pulls
`luaScripts["polaris_access_log.lua"]`, generates a harness and runs it under whichever Lua
it can find (`luatex --luaonly` on this Mac). One authoritative copy, still executable, and
the tests cannot drift from what ships. 6/6 pass.

The install is now a single command with no flags to forget:

```bash
helm upgrade --install fb-polaris-shipper fluent/fluent-bit \
  --version 0.58.1 -n datahub-hynix -f logging/fb-values.yaml
```

---

## `helm get values benchmarks-polaris` — and a fourth correction, plus a question it cannot answer

Kade supplied the live Polaris values. **`helm get values` shows user-supplied *inputs*, not
the running object** — so it is still an intent artifact, one level closer to the truth than
the repo but not the truth itself. Asking for it was the right first step and the wrong last
one.

**Correction: `logging.mdc: {}` was never a divergence.** I listed it three times as
evidence that the live config came from outside the repo, because `mdc.requestId` and
`mdc.realmId` are on every record. They are put there by **Polaris itself** — the chart's
`logging.mdc` block adds *additional static* MDC entries via `polaris.log.mdc."<k>"`, it does
not switch MDC on. `{}` is the correct and expected value. Nothing to reconcile; the claim
was mine, not the repo's.

**Confirmed, and it deepens rather than settles the question.** `quarkus.log.file.enabled` is
the real Quarkus property (default **false**), and `quarkus.log.console.enabled` (default
true) — so the chart's ConfigMap writes *valid* keys, and `logging.file.enabled: false`
renders `quarkus.log.file.enabled=false`. Meanwhile the live values contain **no**
`QUARKUS_LOG_FILE_ENABLED` and **no** `QUARKUS_HTTP_ACCESS_LOG_ENABLED` env var, and the
chart templates `quarkus.http.access-log.*` nowhere at all.

So on these inputs the file handler is off and the access log is off — and both are
demonstrably on. **Something is configuring this pod that `helm get values` cannot show.**
The two candidates, and both are settled by reading the pod rather than the release:

```bash
kubectl -n datahub-hynix get cm benchmarks-polaris \
  -o jsonpath='{.data.application\.properties}' | grep -E 'log\.(file|console)|access-log'
kubectl -n datahub-hynix exec deploy/benchmarks-polaris -- env | grep -i 'quarkus_log\|access_log'
kubectl -n datahub-hynix exec deploy/benchmarks-polaris -- ls -l /deployments/logs/
```

If the ConfigMap says `enabled=true` while the values say `false`, it was **hand-edited after
install** — and then **the next `helm upgrade` of Polaris silently reverts it and kills the
log pipeline**, with no error and no failing pod. That is the single most dangerous thing
currently known about this setup, and it is one `kubectl get cm` from being confirmed or
dismissed.

## Two real faults in the live Polaris values, independent of the above

**#8 — HPA can scale Polaris to 3 pods that share one log file. OPEN.**
`autoscaling.enabled: true`, `minReplicas: 1`, `maxReplicas: 3`, at 80% CPU against a 1000m
limit — and every replica mounts the same `polaris-shared-logs-pvc` and appends to the same
`/deployments/logs/polaris.log`. `ReadWriteOnce` does not prevent this: RWO permits many pods
on the *same* node, and `topologySpreadConstraints` is `ScheduleAnyway` on a single-node
cluster, so they all land together. Two JBoss file handlers with independent descriptors and
independent rotation state, appending and rotating the same file: interleaved records, and a
rotation by one pod pulling the file out from under the other and from under the shipper's
inode. It has not bitten because nothing has driven Polaris past 80% CPU. Either pin
`replicaCount` with autoscaling off while the shared-file design stands, or give each pod its
own file (`%h`-style suffix) and let the shipper glob.

**#9 — `persistence.relationalJdbc.secret.password: polaris` is a plaintext DB password in
the release's user-supplied values. OPEN.**
Same class as #4 and #3. Also `minio.accessKeyId/secretAccessKey: minioadmin` sit *beside*
`existingSecret: benchmarks-minio-credentials` — two credential sources for one client, which
is how #1's "three conflicting MinIO credential sets" started.
