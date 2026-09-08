# Active issues — check here before trusting a value or a runbook

Status vocabulary: **OPEN** (will bite you), **OPEN QUESTION** (unknown, cheap to
settle), **RESOLVED-INSTRUCTIVE** (fixed, kept because the failure mode recurs).

## Open

**#16 — The DaemonSet writes every Polaris console line to `k8s-logs` TWICE, and its dedup key
cannot dedup. OPEN (accepted for now).**

**Update 2026-09-08:** this issue got more load-bearing, not less. The cutover plan now sources
**tier 2 from stdout as well**, so `k8s-logs` is the denominator for proving tier 2 is a subset of
tier 1 — and an undeduplicated denominator is ~2x wrong. Every comparison against tier 1
deduplicates on `sequence` first.

`fluent-bit/values.yaml:155` OUTPUT 1 matches `kube.*benchmarks-polaris*`; `:179` OUTPUT 2
matches `kube.*`. **Fluent Bit routes a record to every matching output** and both target
`k8s-logs` — one copy keyed `Id_Key sequence` + `Write_Operation upsert`, one with
`Generate_ID On`. So every Polaris stdout line exists twice.

**Consequence for measurement, which is why this is filed rather than just fixed:** any count
over `k8s-logs` is **~2x inflated**, so it must be deduplicated on `sequence` before it is
compared with anything — including the tier-1 vs tier-2 comparison in
[`PLAN-opensearch-cutover`](../logging/PLAN-opensearch-cutover-2026-09-08.md) §7.

**And `sequence` cannot carry that load either.** It is the JBoss per-`ExtLogRecord` counter,
**per JVM from JVM start** (2026-09-03 audit: 3723/3724 = ~3.7k records since JVM start). It
resets on every Polaris restart, and #8's three HPA replicas would each run their own. Worse,
`upsert` sends `doc_as_upsert`, so a collision does not overwrite — it produces a **field-union
of two unrelated log lines**, an access record's `http_status` stapled onto an application
record's `exception.*`. Plausible, fictional, no error.

**Kade's call 2026-09-08: leave tier 1's config alone.** Defensible at 5-day retention and
unfiltered. **It must not become the precedent** — the plan gives tiers 2 and 3 a composed
`_doc_id` instead. Testable prediction if it ever matters: `k8s-logs`' Polaris count for a day
spanning a Polaris restart should be near `max(sequence)`, not the true line count. Nobody has
run it.

**#15 — Polaris 500s on create-then-resolve, and it is a NullPointerException, not a
"PG-HA read-after-write signature". OPEN.**

Every 500 this cluster has stored is a `java.lang.NullPointerException` logged by
`org.apache.polaris.service.exception.IcebergExceptionMapper`. Eight of them in run
`1788760757`, `05:59:20Z .. 05:59:33Z`, in three signatures:

| exception.message | n | on |
|---|---|---|
| `…getPassthroughResolvedPath(Object)" is null` | 6 | `POST …/{catalog}/namespaces` |
| `grantee_not_found: grantee={}, [… name='catalog_admin' …]` | 1 | `POST /api/management/v1/catalogs` |
| `metadata` | 1 | `POST …/namespaces/probe_ns/views` |

**The trigger is a fresh parent entity, not load.** Three of the six namespace NPEs are the
`polaris-learning` 500-ladder's *setup* step — one per rung, `nb1788760757bh`, `…dns`,
`…nobkt`, **3 of 3 brand-new catalogs**, each 500ing on the first namespace created in it.
The catalog-create NPE is the same shape one level up: the `catalog_admin` role is created
and immediately looked up as a grantee, and the lookup returns nothing.

**Read-after-write against a standby remains the plausible mechanism** — an entity written
on the primary and resolved microseconds later — but that label had been treated as settled
and it never was. What the log carries is an unresolved entity and an NPE. Do not write
"PG-HA read-after-write" into a document again without the replication evidence beside it.

**The denominator cannot be read from this pipeline, by construction.** Scoped to the window,
`POST …/namespaces` stored **6 x 500** — 3 on the fixture catalog, 1 each on `nb1788760757bh`,
`…dns`, `…nobkt` — **and 1 x 409, and nothing else**. No 2xx, at any scope: that path is not
under `/api/management/`, so rule 5 does not keep it and a **successful namespace create leaves
no individual record**. Rule 3 keeps the failures. So `stats by (http_status)` over stored
access records for this path can only ever return errors, and its zero is the policy working,
not a measurement. The per-resource `writes` counter cannot supply it either: two of the three
fixture 500s were charged to `__other__` because the key did not exist yet, so the key's own
`writes` is 2 for 4 error POSTs.

**It exists in the driver.** The notebook knows every call it made and its status; the ladder
simply throws its setup statuses away. That single omission is why the three 500s were
invisible AND why the rate is unmeasurable — one fix closes both.

**What is established:** 3 of 3 brand-new catalogs 500 on the first namespace created in them,
and the namespace is usable afterwards — each rung went on to `create_table` and got a 4xx from
the storage layer, which requires the namespace to exist. Consistent with a write that
committed and a resolution that then dereferenced null.

**Two consequences, both real.** For the platform: writes 500 at roughly 3% (8 of 275
requests in 60s) on a single-node cluster, and nothing was watching. For
`polaris-learning`: this is the **repeatable provoker** `HANDOFF-500-coverage` §4.1 says does
not exist — API-only, no `kubectl`, no `pg_wal_replay_pause()`. Detail in
[`sessions/2026-09-07-500-coverage-review.md`](sessions/2026-09-07-500-coverage-review.md).

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

**b. Policy v3, written 2026-09-04, NOT RUNNING.** Deliberately, and it is #13's shape again,
so treat the upgrade as a change: `shipper-v3-upgrade-runbook.md`. **v2 was never deployed** —
it was superseded before installation, so there is no v2 baseline in the cluster and no reason
to look for one.

```
1. ERROR / WARN ........................ keep      (no deprecated exclusion — see below)
2. not an access-log record ............ keep
--- every access-log record is COUNTED here ---
3. status >= 400, or unparseable ....... keep, ALL of them, no cap
4. PUT / DELETE / PATCH ................ keep, all
5. POST under /api/management/ ......... keep, all
   POST anywhere else ..................  counted only
6. GET / HEAD, 2xx .....................  counted only
7. anything else ....................... keep
```

**What it preserves, and this is the point of the shape:** 100% of authorization failures —
every 401 and 403 is a full record via rule 3 — and 100% of identity and grant mutations.
What becomes a count is traffic that succeeded routinely.

**Rule 5 is split, not simplified, because in Polaris POST is the CREATE verb.**
`create_principal`, `create_principal_role`, `create_catalog_role` and
`reset_principal_credentials` are all POSTs; PUT covers only assignment and grants, DELETE only
removal. Summarising POST wholesale — the obvious simplification — would make a principal
invisibly created and visibly deleted, which is the asymmetry this pipeline exists to expose.
Catalog POSTs (`create_table`, `commit_table`, both renames, `report_metrics`, `oauth/tokens`)
are data-plane volume and are counted.

**Rule 1 has no "deprecated config" exclusion and needs none.** `polaris/values.yaml:315` sets
`io.quarkus.config: "OFF"`, so those warnings are never written; the coverage run independently
saw zero across 122 calls. The values file alone would not be evidence here (#5) — the run
agreeing with it is. The TODO is deleted, not deferred.

**The dedup cap question is gone, not answered.** v2 kept one read per principal per object per
KST day and needed a per-key table to do it, which is what `DEDUP_MAX_KEYS` was placeholding
for. v3 never stores a successful read individually, so there is no key to remember. The civil-
day arithmetic, both day buckets, `seen_before` and the cap are all deleted — about 90 lines.

**The flush report, schema v1.** A `dummy` INPUT tagged `polaris.report` ticks and reaches the
*same* Lua filter instance (state is per-instance, so `Match` is `polaris.*`); on a
`WINDOW_SECONDS` boundary the filter returns an **array** of records instead of the tick and
resets the counters. Steady state is a 30-minute window on the :00/:30 wall-clock boundary with
a 30s tick — **but the deployed values file is on the temporary fast-run setting right now, see
d. below before reading a report.** Array return is documented behaviour — "this value can be an array of tables... the
input record is effectively split into multiple records" — but has never run here (#14c).
Lands on `{app="polaris-shipper-report", level="REPORT"}`, its own stream.

Three record types on one envelope (`schema_version`, `report_type`, `report_seq`, `hostname`,
`window_start`/`window_end`/`window_seconds`, `_time` = window end):

| type | carries |
|---|---|
| `summary` | `access_seen` / `access_kept` / `access_counted` (**kept + counted == seen**), `counted_get`, `counted_post`, `errors_kept`, `parse_errors`, `distinct_resources`, `distinct_principals`, `resources_other`, `principals_other`, `min_record_time`, `max_record_time`, `partial_window` |
| `resource` | `resource`, `resource_kind`, `requests`, `reads`, `writes`, `errors`, `response_bytes` |
| `principal` | `user_principal_name`, `requests`, `reads`, `writes`, `errors`, `response_bytes` |

**Two margins, never the cross product** — `resource -> count` and `principal -> count`, so
state is |resources| + |principals| rather than their product. The consequence is in the source
because it will otherwise be misread as an audit trail: the report says *which resources are
hot* and *who is generating load*, and **cannot** say *who read which resource*. Under v3 that
question has no record behind it at all — a deliberate trade, taken knowingly.

Four things worth knowing about the schema:

- **`sum(resource.requests) == sum(principal.requests) == access_seen - parse_errors.** The two
  margins must agree. It is asserted in the test suite and it is Phase 4's last check — a
  dashboard that verifies it knows whether to trust a trend before drawing one.
- **The resource key is the resource, not the URL.** `/tables/t/metrics` counts under
  `/tables/t`. v2 emitted two rows for one table — measured, not supposed — and a trend
  computed on a key that splits is simply wrong.
- **Errors increment an existing resource key but never create one**, so a client walking
  invented table names cannot fill the key space. Their counts are not lost: they land in
  `__other__`, which keeps the margin totals exact, and every one is stored in full by rule 3.
- **Zero-carry, exactly one window.** A resource falling from 100k reads to none emits an
  explicit `0` rather than vanishing from the output, then decays. The fall is the direction
  you most want to see and a missing row cannot express it.

`user_principal_name` deliberately reuses the access-log field name, so one filter spans a
principal's stored 403s and their per-window counts. `resource` is a new name because it is a
normalized identity, not a request path.

**c. What is still unverified, and no test can reach it:** that this Fluent Bit build splits an
array return into separate records, and that the dummy input's tag reaches the filter instance.
Both documented, neither run. Runbook Phase 4 distinguishes them and names the fallback.

**d. TEMPORARY: the report window is 30 seconds, not 30 minutes.** Set 2026-09-04 at Kade's
request so a coverage run crosses three window boundaries in ~2 minutes instead of ~90 — the
handoff's §4 needs three, for `report_seq`, zero-carry and carry decay. In
`logging/fb-values.yaml`: `WINDOW_SECONDS = 30` (was 1800) and the dummy INPUT's
`Interval_Sec 5` (was 30).

**Revert both together.** The tick has to stay well under the window: `report_tick` reports
whatever `counts` holds under the index it was *opened* with, and records accumulate into the
open window regardless of their own timestamps, so if the tick period reaches the window period
ordinary jitter lets a boundary pass unnoticed — the skipped window never opens and its records
are folded into the previous window's index. At 1800/30 the margin is 60×; at 30/30 there is
none. That is why the tick moved too, and it is not cosmetic.

Two consequences while it is set:

- **Report volume is ~60× steady state.** Zero-carry emits every non-zero key once more as an
  explicit `0`, so even an idle pipeline ships a summary plus carried rows every 30s.
- **The first window after the `helm upgrade` is a replay, not traffic.** The tail DB is on an
  `emptyDir` with `Read_from_Head true` and VictoriaLogs does not deduplicate on ingest, so the
  upgrade replays the whole log file — and at 30s the entire replay lands in *one* window as a
  spike. A window whose `min_record_time`/`max_record_time` span far exceeds `window_seconds`
  is a replay. Do not trust it.

Nothing else reads the constant. `logging/scripts/test-polaris-filters.py` now parses
`WINDOW_SECONDS` off the deployed Lua and expresses every tick offset as a multiple of it
(it hardcoded 1800, so `T0 + 900` — "a tick inside the window" — would have become a tick 30
windows later and failed for the wrong reason). 48/48 at 30s. The runbook, roadmap #7 and
`POLARIS-LOG-COVERAGE-V3-HANDOFF.md` still describe the 30-minute steady state on purpose.

**Decided by this policy, and therefore no longer open:** the 4xx cap (there is none — all
errors kept), collection listings (counted, like every other successful read), `report_metrics`
(counted, as a catalog POST), and the dedup cap (deleted with the dedup).

**Still deferred, each with a number behind it:**

| | evidence | why deferred |
|---|---|---|
| the 95.5% — routing the DEBUG SQL records | 1,928 of 2,018 stored records are application lines | needs the `loggerName` distribution first; #5b already fixes the direction — route, never turn down |
| no `%D` — no request duration is recorded anywhere | the access-log pattern carries no latency token | Polaris-side, and **Polaris is not to be changed** (#11). The *no stack traces* half of this row is **CLOSED** — see immediately below |
| retention for the report stream | reads now live only as counts | VictoriaLogs single has one global retention and no disk cap (#7); the counts eventually want a TSDB, roadmap 7 |
| `neg.client_timeout` "EXPECTED DROPPED, PRESENT" | the run's only matrix discrepancy | oracle artefact — a call with no client-side status is not predictable and should not be scored `drop`. Harness fix, in `polaris-learning` |

**CLOSED 2026-09-07 — stack traces DO survive, and the `0 of 5` was a mis-named search.**
Run `1788760757`: **8 of 8** WARN/ERROR records carry an exception payload, stored flattened as
`exception.exceptionType`, `exception.frames`, `exception.message`, `exception.refId`.
VictoriaLogs flattens nested objects, so a query for `exception` matches nothing and a
`grep -c stackTrace` finds nothing — **two searches for a name this build does not emit,
agreeing with each other**, which is what the `0 of 5` was. Query `exception.*`, never
`exception`. The fact with its numbers is in [`roadmap.md`](roadmap.md), *Handing back*; the
review that re-proved it is
[`sessions/2026-09-07-500-coverage-review.md`](sessions/2026-09-07-500-coverage-review.md).
Only the `%D` half of that row is still open, and it is Polaris-side.

**READING THE REPORT STREAM — three false findings came from not doing this.** Every query
against `app:polaris-shipper-report` must carry **`schema_version:2`**, and anything about
sequence continuity must also carry **`hostname:"…"`**.

- **The stream holds v1 AND v2 records side by side.** The shipper pod was replaced at
  `2026-09-07T04:21:30Z` (`…68b4959db4-4f7tf` v1 -> `…55b7bf586d-5kt5l` v2). A `sum(errors_4xx)`
  over any range spanning that instant silently under-counts: the v1 records have no such field,
  and an absent field behaves like a zero inside a sum. Cell 0b gates the POLICY's schema
  version; nothing gates the QUERY's.
- **`report_seq` is per pod and resets to 1 on restart.** `min`/`max`/`count` across two
  generations manufactures a phantom gap — it read as "50 reports lost", then as "a backlog
  draining", and it was neither. The schema's own claim is *one summary per **(host, window)***;
  the host is not decoration.
- **`sum()` over an empty group returns `NaN` in LogsQL; `count()` returns 0.** A v1 summary has
  no `carried_rows`, so summing it yields NaN, which a naive comparison reads as a mismatch.
- **`_time` on a report record is the window END**, not its start. Seq 196 (`window_start
  05:59:00`) appears at `05:59:30`.
- **Every count must carry its denominator.** Ask `stats count()` for the scope first. Three
  times in one session a number arrived with no scope and read like an answer — 25 vs 6 on an
  unfiltered `_time`, a 5-row UI truncation read as a full result, and the cross-pod seq range.
  Each was caught only because an independent number disagreed.

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

**#2 — Which sink does Fluent Bit ship to? SETTLED — both halves, as of 2026-09-08.**
Not one shipper choosing a sink — **two releases**. Confirmed from `helm list` on
2026-09-03: **`fb-polaris-shipper`**, namespace **`datahub-hynix`**, chart
`fluent-bit-0.58.1` / app **5.1.1**, **revision 10**, deployed 2026-08-22 — the Deployment
that tails the Polaris log PVC into VictoriaLogs (`logging/fb-values.yaml`). The DaemonSet
release (`fluent-bit/values.yaml`) ships container logs to OpenSearch in Docker. **Its name is
`benchmarks-fluent-bit`, in `datahub-hynix`** — quoted 2026-09-08 from `kubectl get ds -A`, the
half of this issue that had been open since 2026-09-03. **`hostNetwork` is unset**, so it is an
ordinary pod on the cluster network: reaching `192.168.194.1:9200` is not a host-network
privilege, and any pod in the namespace has the same egress. `CLAUDE.md`'s tech stack now says so.

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
