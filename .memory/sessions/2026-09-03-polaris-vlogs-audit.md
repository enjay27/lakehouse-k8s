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
