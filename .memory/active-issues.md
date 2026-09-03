# Active issues — check here before trusting a value or a runbook

Status vocabulary: **OPEN** (will bite you), **OPEN QUESTION** (unknown, cheap to
settle), **RESOLVED-INSTRUCTIVE** (fixed, kept because the failure mode recurs).

## Open

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

**#2 — Which sink does Fluent Bit ship to? ANSWERED FROM THE REPO, not yet from the cluster.**
It is not one shipper choosing a sink — it is **two releases**:
`fluent-bit/values.yaml` is a **DaemonSet** tailing `/var/log/containers/*.log` into
**OpenSearch in Docker** (`192.168.194.1:9200`), and `logging/fb-values.yaml` is a
**single-replica Deployment** tailing a shared PVC into **VictoriaLogs** in `logging`.
Confirmed by reading both files; **not** confirmed that both releases are installed —
`helm list -A` settles that and this session has no cluster reach. Once confirmed, say it
plainly in `CLAUDE.md`'s tech stack. Note #5 below: today the VictoriaLogs release has no
input, so everything that lands anywhere lands in OpenSearch.

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

**#5 — The repo says the Polaris log path is off; the cluster shows it running. OPEN.**
Corrected within the session it was filed in. The first version of this issue claimed the
VictoriaLogs path had no input, reasoning from the tree. A VMUI capture then showed
**1,636 records in 30 minutes, streams `{app, level}`, Polaris DEBUG SQL and INFO lines, and
a Quarkus access-log line**. The pipeline works.

The tree still says otherwise, and that is the actual issue — this is **#1 demonstrated**:

| what the repo says | what the cluster shows |
|---|---|
| `polaris/values.yaml` `logging.file.enabled: false`, so `configmap.yaml:132-147` renders `quarkus.log.file.enabled=false` | a file is being tailed and shipped |
| `quarkus.http.access-log.enabled` appears nowhere; `values.yaml:302` only sets the category level | access-log lines are arriving |
| `polaris/values.yaml:200` and `logging/fb-values.yaml:15` mount `polaris-shared-logs-pvc`; **nothing in this repo creates it** | the mount evidently resolves |

So the live release was configured outside these files — an overlay, a `--set`, or a hand
edit — and `helm -n datahub-hynix get values benchmarks-polaris` is the only thing that says
which. Until that diff is done, **editing `polaris/values.yaml` risks reverting whatever is
actually running.** Do the diff before the edit, not after.

The read-side lesson: *verify against the running object, never against the values file*
applies to reading the repo as much as to writing it.

**#5b — Faults visible in the VMUI capture itself. OPEN.**
Independent of the divergence above, and each one silent rather than an error:

- **`_time` is assigned at ingest, not taken from the record.** All 1,636 records sit in one
  15s bucket with 30 empty minutes behind them, and carry nanosecond precision
  (`15:35:13.911654221`) where Quarkus emits milliseconds. `Rename timestamp _time` is not
  landing. Real event time is lost and every shipper restart re-stamps history to "now".
- **No `loggerName` on any record**, though the output URI asks for it as a stream field.
  The Quarkus JSON formatter always emits it, so these records are not in that shape.
  Either the file is not JSON, or the tail's `Parser json` is not applying.
- **No tail `DB` with `Read_from_Head true`** — the single burst is the expected signature.
- **The access-log regex cannot match a zero-byte response.** `%b` emits `-`
  (`... 200 -` in the capture); the spec ends `(?<response_size>\d+)`. Needs `[\d-]+`.
- **The local volume driver is DEBUG SQL**, from
  `org.apache.polaris.persistence.relational.jdbc.DatasourceOperations` at
  `polaris/values.yaml:290` — nearly every row. The spec's 11M/day `GET /tables/` poll
  traffic, which the Lua deduplicator exists to remove, has no local analogue. **Dedup is
  the wrong first lever on this cluster; the category level is the right one.**

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
