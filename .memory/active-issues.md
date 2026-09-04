# Active issues — check here before trusting a value or a runbook

Status vocabulary: **OPEN** (will bite you), **OPEN QUESTION** (unknown, cheap to
settle), **RESOLVED-INSTRUCTIVE** (fixed, kept because the failure mode recurs).

## Open

**#14 — The noise filter governs 4.5% of the volume, and policy v2 is not running yet. OPEN.**

Two things, from the second coverage run (`polaris-learning/log-coverage`, 2026-09-04, run
`1788498536`, against `fb-values.yaml` sha256 `b56c135b87d6281b`).

**a. The measurement.** 122 calls stored 2,026 records. Counting the coverage matrix rather
than its summary: **90 access-log records and 1,928 application lines.** The filter can only
act on the first group — rules 1 and 2 keep every application line untouched — so dropping 34
of them removed **1.7%** of what would otherwise be stored. Rules 3–7 are an *audit-fidelity*
control. Anyone tuning them for storage is tuning the wrong 4.5%; the volume lever is the
DEBUG SQL records in #5b, and #5b already says **route them, do not turn them down**.
Settle where the 1,928 come from with one `stats by (loggerName)` before designing that.

**One number in that report does not agree with itself.** Question 5 says "34 of 122 calls
produce no record at all", but those same 34 calls carry **628 application lines**, and
`90 + 1,928 ≈ 2,026` implies the `app_lines` column is counted from VictoriaLogs. If it is,
a dropped `create_principal` still leaves 13 correlated records and only the access-log line
— method, path, status, principal — is lost. Real, but not "invisible". Settle which source
that column reads before repeating the stronger claim.

**b. Policy v2, written 2026-09-04, NOT RUNNING.** Deliberately this time, and it is #13's
shape again, so treat the upgrade as a change:

- **Rule 5 inverted.** It was a keep-list (POST on the table/view API kept, every other
  successful POST dropped) whose own comment said the drop was aimed at the OAuth token
  endpoint. It was never bounded to it. The run measured the cost: `create_principal`,
  `create_principal_role`, `create_catalog_role`, `create_namespace`,
  `update_namespace_properties`, `rename_table`, `rename_view` and
  `reset_principal_credentials` each left no access-log record. Now every POST is kept
  except `ONCE_PER_DAY_POST_PATTERNS` — currently `/oauth/tokens$` alone, kept once per
  principal per KST day, so "who authenticated today" is answerable. Cost in that profile:
  **+10 records per 122 calls, 0.5%.**
- **The dedup key carries the principal.** It was `method .. path`, so the second principal
  to read a table today was invisible — unanswerable "who read what", on an authorization
  catalog.
- **The dedup key drops the query string.** `probe_tbl`, `?snapshots=refs` and
  `?snapshots=all` were three keys for one table on one day. `test-polaris-filters.py:90`
  asserted that as KEEP; the assertion is now DROP.
- **`Alias` on all four filters.** Two `lua` filters are indistinguishable in
  `fluentbit_filter_drop_records_total` without it, which is why the run reported the drop
  delta as *unknown*.

- **A flush report, every 30 minutes on the :00/:30 boundary.** A `dummy` INPUT tagged
  `polaris.report` ticks every 30s and reaches the *same* Lua filter instance (state is
  per-instance, so `Match` widened to `polaris.*`); on a window boundary the filter returns an
  **array** of records instead of the tick — one summary, one per table, one per principal —
  and resets the counters. Array return from a Lua filter is documented behaviour: "this value
  can be an array of tables... the input record is effectively split into multiple records".
  The tick rate is not the report period, so over-ticking is harmless and the window stays
  aligned across a restart. Lands on `{app="polaris-shipper-report", level="REPORT"}`, its own
  stream, so `app:polaris` queries are unaffected.

  **Two margins, never the cross product** — `table -> count` and `principal -> count`, so
  state is |tables| + |principals| rather than |tables| x |principals|. The consequence is
  stated in the source because someone will otherwise read a count as an audit trail: the
  report answers *which tables are hot* and *who is generating the load*, and **cannot** answer
  *who read which table*. That question is what rule 6's principal-keyed record is for. Table
  names are client-controlled (the run hammered a table called `nope`), so the map is capped at
  500 with an `__other__` bucket — totals stay exact, only per-table detail is capped.

  **Why it matters more than the records it saves:** suppression that leaves no number behind
  is erasure, and that is exactly why the three deferred items below are deferred. With a count
  in the report, capping repeated 404s or deduplicating collection listings stops hiding
  volume. The report is the prerequisite, not a side quest.

**The cap on the dedup table is undecided and is Kade's call.** Keying on the principal
multiplies the table by distinct principals per day, in the shipper's 512Mi, and nothing
bounded it before or now. A **placeholder** `DEDUP_MAX_KEYS = 50000` fail-open guard stands
in: above it the filter stops deduplicating and keeps everything, which can only store more,
never lose a record. Replace it with the decided policy — and the summary record now carries
`dedup_keys`, the live size of that table, so the choice can be made against a week of
measurements instead of a guess.

**Deferred, measured, not done** — each has a number behind it in that run:

| | evidence | why deferred |
|---|---|---|
| collection listings are not deduped at all | 20 identical `GET .../tables` → 20 records | changes the rule table's shape; `test-polaris-filters.py:100-101` asserts it as KEEP today |
| repeated 4xx have no cap | 20 identical 404s → 20 records | "errors outrank dedup" is deliberate; capping 401/403/404 but never 5xx/429 is a judgement call |
| `report_metrics` is kept unbounded | `POST .../tables/{t}/metrics` matches the table pattern | Iceberg sends one per scan; the pipeline keeps scan telemetry and used to drop credential resets |
| no `%D`, no stack traces | question 3: 0 of 5 ERROR records carried an `exception` | both are Polaris-side, and **Polaris is not to be changed** (#11) |
| `neg.client_timeout` "EXPECTED DROPPED, PRESENT" | the run's only matrix discrepancy | oracle artefact — a call with no client-side status is not predictable and should not be scored `drop`. Harness fix, in `polaris-learning` |

**#1 — The repo has not been reconciled against the live cluster. OPEN.**
Kade reset and rebuilt the cluster on 2026-09-03 without following
`RESET-AND-CLEAN-INSTALL.md`, and resolved the four config blockers during the
install. Those fixes are in the running releases; whether they are also in the
`values.yaml` files here is **unknown**. Until someone diffs them, nothing on disk
is evidence of what is deployed:

```bash
helm -n datahub-hynix list
helm -n datahub-hynix get values <release> > /tmp/<release>-live.yaml   # then diff
```

The four blockers this closes out — Polaris `bootstrapCredentials` rendering `""`,
three conflicting MinIO credential sets (one of them plaintext at
`spark/values.yaml:30`), the stale `polaris-persistence-secret.yaml`, and the
unpinned images in `kafka/` / `schema-registry/` / `datahub/` — are **resolved in
the cluster**. Two of them are worth checking on disk regardless: a plaintext
secret key stays a leaked secret even after the cluster stops using it, and an
unpinned image is still unpinned for the next install.

**#2 — Which sink does Fluent Bit ship to? SETTLED for the shipper.**
Not one shipper choosing a sink — **two releases**. Confirmed from `helm list` on
2026-09-03: **`fb-polaris-shipper`**, namespace **`datahub-hynix`**, chart
`fluent-bit-0.58.1` / app **5.1.1**, **revision 10**, deployed 2026-08-22 — the Deployment
that tails the Polaris log PVC into VictoriaLogs (`logging/fb-values.yaml`). The DaemonSet
release (`fluent-bit/values.yaml`) ships container logs to OpenSearch in Docker; its release
name has not been quoted yet. `CLAUDE.md`'s tech stack now says so.

Two things that follow. The shipper is in `datahub-hynix`, which is the only namespace it
could be in — #6 was a real constraint and is already satisfied. And **revision 10** on a
file that has never matched the cluster is the shape of #5: ten upgrades of configuration
this repo cannot account for.

**#3 — `minio/values.yaml` defeats its own chart's credential guard. OPEN (low).**
`minio/templates/secret.yaml` refuses to render when `auth.rootPassword` is empty —
CLAUDE.md's Zero Hardcoded Credentials rule, enforced at install time, which is the
right place for it. But the committed values carry `rootUser: "minio"` /
`rootPassword: "minio"` as defaults, so the guard never fires and an install with no
`--set-string` quietly comes up with a publicly known password. Either blank the
defaults so the guard does its job, or accept that this cluster's object store has a
guessable root credential. Cheap either way; just pick one deliberately.

**#4 — `fluent-bit/values.yaml` carries a plaintext OpenSearch password. OPEN.**
`HTTP_Passwd Str0ngP@ssw0rd123!` appears twice, in a **committed** file — the Zero
Hardcoded Credentials rule broken in tracked history. Rewriting the file does not unleak
it; the credential has to be rotated on the OpenSearch side as well. The fix in the values
is a Secret plus `${VAR}` expansion in the Fluent Bit config, not a different literal.
`polaris/values.yaml:408-409` (`minioadmin`/`minioadmin`) is the same class of problem and
should go the same way.

**#5 — `polaris/values.yaml` does not describe the running Polaris. OPEN — and NARROWER
than it was written.**

Filed first as "the VictoriaLogs path has no input" (wrong — it runs), then rewritten as
"the repo and the cluster disagree", which over-reached: it said *the repo*, on evidence
about *one file*. The `helm get values fb-polaris-shipper` diff on 2026-09-03 settles that
half and it went the other way.

**`logging/fb-values.yaml` is RECONCILED.** Live revision 10 matched it line for line apart
from `helm`'s alphabetical key ordering and **one** real difference: the live output streams
on `_stream_fields=app,level` where the file asked for `app,level,loggerName`. The file now
says `app,level`. Nothing else about the shipper was ever divergent — the tail with no `DB`,
`Read_from_Head true` and `Skip_Long_Lines Off` are all genuinely deployed, so #5b's
open questions about them are answered: they are live, and they are still worth changing.

What remains open is narrower and still real:

- **`polaris/values.yaml`** says `logging.file.enabled: false`, sets
  `quarkus.http.access-log.enabled` nowhere, and carries `logging.mdc: {}` — yet the file is
  written, access-log lines arrive, and `mdc.requestId` / `mdc.realmId` are on every record.
  That configuration is somewhere else. `helm -n datahub-hynix get values benchmarks-polaris`
  has not been run. **Do it before editing that file.**
- **`polaris-shared-logs-pvc`** is mounted by both releases and created by no manifest here.
  It exists in the cluster; the repo cannot rebuild it.

The generalisable part: a claim about "the repo" needed evidence about the repo. One file
diffing clean is exactly the outcome that a broad claim could not have predicted.

**#8 — HPA can scale Polaris to 3 pods sharing one log file. OPEN.**
`autoscaling.enabled: true`, `maxReplicas: 3` at 80% CPU — and every replica mounts
`polaris-shared-logs-pvc` and appends to the same `/deployments/logs/polaris.log`.
`ReadWriteOnce` does **not** prevent this: RWO allows many pods on the *same node*, and this
is a single-node cluster with `ScheduleAnyway` spreading. Two JBoss file handlers with
independent descriptors and independent rotation state on one file means interleaved records,
and a rotation by one pod pulling the file out from under the other and from under the
shipper's inode. Unbitten only because nothing has pushed Polaris past 80% CPU. Fix: pin
`replicaCount` and disable autoscaling while the shared-file design stands, or give each pod
its own filename and let the shipper glob.

**#9 — A plaintext database password in the live release. OPEN.**
`persistence.relationalJdbc.secret.password: polaris` in `helm get values` output. Same class
as #3 and #4. Separately, `minio.accessKeyId`/`secretAccessKey: minioadmin` sit beside
`minio.existingSecret: benchmarks-minio-credentials` — two credential sources for one client,
which is how #1's "three conflicting MinIO credential sets" began.

**#10 — RESOLVED-INSTRUCTIVE: there was never a hidden config source.**
The ConfigMap and pod env, read directly, say `quarkus.log.file.enabled=false` — matching the
live release values *and* `polaris/values.yaml` on disk. Everything agrees. The divergence
story that ran through five readings of this pipeline was wrong at every level; **the repo
does describe this cluster.**

**And the belief it rested on is backwards.** Kade's read was that the chart's
`logging.console` / `logging.file` blocks "are not applied at all, just extraEnv applied".
His own ConfigMap disproves it: `quarkus.log.file.enabled=false` is rendered by
`templates/configmap.yaml:132-147` *from* `logging.file.enabled: false`. The block is not
inert — **it is the switch holding the pipeline off.** It reads as inert precisely because
the only value it has ever written is the one with no visible effect. `QUARKUS_LOG_FILE_JSON_*`
is real but orthogonal: JSON formatting for a handler that is disabled.

**#11 — Unexplained, NOT pursued: file logging reads as off, and ships anyway.**
The running config says `quarkus.log.file.enabled=false`, and Polaris is nonetheless writing
a file that the shipper tails — **Kade confirms the pipeline works and ships continuously**,
which is an observation, where the prediction that it would break at the next restart was an
inference. This session's inferences about this pipeline were wrong four times; his
observation wins. **Polaris config is not to be changed.**

Left here because it is genuinely unexplained, not because it needs action. Whoever picks it
up: `ls -l --full-time /deployments/logs/` twice, thirty seconds apart, says whether the file
is live or stale, and the Polaris pod's start time against the ConfigMap's last write says
whether the JVM predates it. Do not turn it into a change on the strength of the reasoning
alone.

**#12 — WITHDRAWN.** Proposed flipping `logging.file.enabled: true` and deleting the
`extraVolumes` pair. Kade's call: Polaris works, leave it. The reasoning behind it is in the
session file if the situation ever changes; the mount-path collision it warns about
(`logging.file.enabled: true` makes the chart mount `logs-storage` at `logsDir`, colliding
with the existing `extraVolumeMounts` on the same path) stays true and would bite anyone who
enables that flag without removing the pair.

**#5b — What is actually wrong in the shipped records. OPEN.**
Established from two raw records off the VMUI JSON tab, after two earlier readings of the
same pipeline from a *rendered* view were both wrong. `_time` is **not** an ingest stamp —
it is the record's own Quarkus time (`...13.911654221Z`), 178µs *earlier* than Fluent Bit's
own `date` (`...13.911832Z`), which an ingest stamp cannot be; the nanoseconds are the JBoss
JSON formatter printing the full `Instant`. And every record **does** carry `loggerName` —
the stream-fields panel was showing the *stream* (`{app, level}`), not the field list.
**A `_stream` is not a field list and a histogram bucket is not a clock. Read the record.**

Working, and not to be "fixed": Quarkus JSON file logging, `_time`, `_msg`, `_stream` on
`{app, level}` (low-cardinality, the right choice), and **`mdc.requestId` + `mdc.realmId`,
which make the spec's §7 end-to-end trace query work today**. Note `polaris/values.yaml` has
`logging.mdc: {}` and `_stream_fields=app,level,loggerName` — the cluster is right and the
repo is wrong on both, which is #5 again.

Actually wrong:

| what | evidence | fix |
|---|---|---|
| `date` duplicates `_time` on every record | `"date": "1788417313.911832"` beside `_time` | `json_date_key false` on the HTTP output |
| `processName` is a 60-byte JVM path on every record; `loggerClassName`, `processId` near-valueless | in every record | `record_modifier` `Remove_key` |
| **DEBUG SQL records are ~1.5KB each** — full statement, every bound parameter, an embedded JSON blob escaped four deep — and are nearly every row | the sample `_msg` | **Do NOT just set `DatasourceOperations` to INFO.** `polaris-learning` depends on that logger being at DEBUG (`roadmap.md`, *Handing back*: `check_sql_logging.py` must print *SQL DEBUG logging is WORKING*). Turning it down to save space breaks the only consumer this platform exists for. Route it instead — its own stream, or leave it to the console→OpenSearch path and keep VictoriaLogs for the rest. |
| bound parameter values are written to the log | S3 paths and internal properties in the sample | same fix; worth knowing before this pattern reaches anything with real data in it |
| `response_size` is `-` for zero-byte responses | `"... 200 -"` | regex `[\d-]+`, not `\d+` |
| no latency token in the access-log pattern | the access-log `_msg` | add `%D`; the spec's own P99 panels need it |

The tail `DB`, `Skip_Long_Lines Off` and the absent buffering are now **confirmed live** by
the revision-10 diff, not merely suspected. Unchanged as faults: a restart replays the file
from byte 0, and a line over `Buffer_Max_Size` stops the tail rather than being skipped.

**#6 — A shared PVC cannot cross namespaces. OPEN (design constraint, decide before building).**
PVCs are namespaced. Polaris runs in `datahub-hynix`, so the file-tailing shipper must run
in `datahub-hynix` too — only VictoriaLogs stays in `logging`, which is what
`environments.md` already says that namespace is for. `ReadWriteOnce` is survivable only
because OrbStack is one node; it stops being survivable the moment anything is scheduled
elsewhere. The alternative that avoids the PVC entirely is to add a second OUTPUT to the
existing DaemonSet and drop the Deployment — at the cost of the access-log field extraction
and the dedup filter, which need the file path to be worth building.

**#7 — `logging/victoria-values.yaml` is sized for the spec's peak, not for this laptop. OPEN (low).**
50Gi PV and a 4Gi memory limit come from the 140M-records/day column of the design doc, on
the single OrbStack node that already needs >7GB for the full platform set. Two specific
gaps rather than just the sizing: there is **no `retention.maxDiskSpaceUsageBytes`**, so
30-day retention alone does not stop the PV filling and wedging the pod; and
`service.type: LoadBalancer` on 9428 publishes an **unauthenticated ingest *and* query**
endpoint onto the Mac, since VictoriaLogs single has no auth. **`persistence.size` is
now-or-never** — if the PVC is already bound at 50Gi, that is what this cluster has.


## Resolved, kept because they recur

**#13 — RESOLVED. `polaris_noise_filter` was written and not running; it runs now.**
Measured absent on 2026-09-04 (0 of 34 expected drops dropped; twenty identical
`GET .../tables/probe_tbl` stored twenty records). The filter entered `fb-values.yaml` in
**2120ed9, 08:26:18Z 2026-09-03**; the shipper pod had run since **08:04:06Z** from
**60b94d9**, which carries the parser and no filter. `helm upgrade` had never been run.
It was run: the shipper pod dates from **04:57:36Z 2026-09-04**, the second coverage run
reports *retention policy deployed? True — the running ConfigMap carries this exact script*,
and **34 of 34 expected drops dropped.**

**Kept because the pattern is the repo's whole failure mode.** This was #F1 in a different
file: configuration written correctly, five documents describing it as built, and nothing
warning that none of it was the running object. What caught it was not a review — it was a
harness that ran the *deployed* Lua and compared it against what the pipeline actually
stored. **#14b is the same state again**, entered knowingly.

**#F1 — An entire values block was inert for months. RESOLVED-INSTRUCTIVE.**
`postgresql/` is an umbrella chart. Helm passes values to a subchart only when
nested under the subchart's name — everything at the top level was silently
ignored, and the cluster ran on subchart defaults:

| intended | actually in effect |
|---|---|
| `max_connections = 200` | **100** |
| `shared_buffers = 384MB` | 128MB |
| `log_min_duration_statement = 1000` | -1 (off) |
| `persistence.size: 10Gi` | 8Gi |
| explicit 2Gi resources | `resourcesPreset: micro` |
| `disableLoadBalancingOnWrite: always` | `transaction` |
| `/dev/shm` emptyDir | not mounted (64MB default) |

Detected by comparing a value against the **subchart default**, not against the
values file: `pgpool.replicaCount: 3` with one pgpool pod running proved the block
was dead. `postgresql.replicaCount: 3` matched only because 3 is also the default —
a coincidence, not evidence. **Verify against defaults, never against intent.**
This is also why #1 above matters: the rebuild is exactly the moment that gap
reopens.

**#F2 — `0.0.0.0/0` does not match IPv6. RESOLVED-INSTRUCTIVE.**
The custom `pgHbaConfiguration` was IPv4-only; OrbStack's pod network is IPv6
(`fd00::/8`), so repmgr's pod-to-pod connection was rejected and a standby went
into CrashLoopBackOff. It never bit while #F1 was in force, because Bitnami's
*default* pg_hba includes `::/0`. **Un-inerting configuration that has never
executed is a change, not a fix** — review it line by line against the defaults it
replaces.

## Standing constraints

- **`persistence.size` is now-or-never.** A PVC cannot be grown in place after
  install. Whatever the rebuild set is what this cluster has.
- **Resource footprint.** The full set (DataHub + prerequisites + Kafka + Spark +
  Airflow) needs >7GB RAM on the daemon node.
- **`ALTER SYSTEM SET shared_preload_libraries` replaces, it does not append.**
  Running it bare drops `repmgr` and silently disables automatic failover.
  `postgresql.auto.conf` lives on each pod's PVC and does not replicate.
- **`git status` hygiene.** `.gitignore` covers `.idea`, `node_modules`,
  `postgresql-ha-*.tgz` and `.DS_Store`. Still check `git status` **before**
  `git add -A`, never after — chart tarballs and `helm get values` exports are not
  covered by any pattern.
