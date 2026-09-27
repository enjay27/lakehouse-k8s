# Active issues — check here before trusting a value or a runbook

Status vocabulary: **OPEN** (will bite you), **OPEN QUESTION** (unknown, cheap to
settle), **RESOLVED-INSTRUCTIVE** (fixed, kept because the failure mode recurs).

## Open

**#48 — OPEN. File logging is back on with ONE `polaris.log` shared by every replica, so `#8`'s
hazard returns the moment a second Polaris JVM exists.** 2026-09-27. **ROLLED ~18:34 KST, and a second
JVM existed by 22:21 the same day.**

**Evidence (Kade, 2026-09-27 ~22:25 KST):** two pods of ONE ReplicaSet (`6f86777d49-l5q8m`, age 3h49m;
`6f86777d49-nvj5j`, age 3m28s) — same pod-template hash, so HPA scale-out, not a rollout. In the PVC:
`polaris.log.2026-09-27-18.gz` (gzip -t ok; JSON; first/last `timestamp` 18:35:07 / 18:51:18 +09:00)
and `polaris.log` (first line 22:21:43 `Installed features` — the new pod's startup), both mtime 22:21.
So the NEW pod's first write rolled the OLD pod's file. The old pod still holds its own rotation state
(next roll due 19:00, suffix -18): its next write goes to the renamed inode, and its first write then
rolls the new pod's `polaris.log` to the same `-18.gz` name. HPA trigger NOT the memory baseline, as I
first guessed: `kubectl get hpa` at ~22:25 showed cpu 1%/80%, memory 32%/80%, replicas 2 — a transient
spike, cause unknown. At that load it scales back to 1 after the 5-min stabilisation window; the
ReplicaSet usually deletes the NEWER pod, which leaves the old one with the stale rotation state.

**CONFIRMED BY EXPERIMENT (Kade, 2026-09-27 ~22:35 KST).** One request port-forwarded to the OLD pod
(`l5q8m`, 401 on `/api/catalog/v1/config`). Afterwards `polaris.log.2026-09-27-18.gz` held only
`22:21:43.086…` .. `22:21:43.579…` +09:00 — the NEW pod's startup lines — and none of the 18:35–18:51
content it held minutes earlier. The old pod's first write after its stale 19:00 deadline rolled the
new pod's file onto the existing `-18` name: the real hour 18 is overwritten and 22:xx is labelled 18.
"Pods only append, so one file is safe" (the premise of the one-file decision) is false here: appends
are fine, the per-JVM rename-and-reopen is not. Until fixed it recurs every hour while 2+ pods run.

**FIX WRITTEN, NOT ROLLED (2026-09-27, Kade chose it):** `logging.file.fileName: polaris-${HOSTNAME}.log`
— one file per pod, the batch job merges them per hour and seals files of deleted pods. Open until the
pod's `ls` shows per-pod names after the upgrade. Shared-era leftovers (`polaris.log`,
`polaris.log.2026-09-27-18.gz` — now mislabelled 22:21 content) go to `legacy-shared/`, not to the job.

**ROLLED ~22:37 KST (Kade).** `ls` shows one file per pod, named after the pod: `polaris-benchmarks-polaris-
7f4d69c67c-{2tklb,bmt4t,rz56d}.log` (~3.58 KB each, startup lines) — `${HOSTNAME}` expanded. Three pods came
up in the new ReplicaSet, so the HPA scaled out during the roll again (a JVM-startup CPU spike is the likely
trigger, unconfirmed). `legacy-shared/` holds the shared-era `polaris.log` (15229 B, last write 22:37 when the
old pods stopped) and `polaris.log.2026-09-27-18.gz` — now 942 B with mtime 22:30, down from 1241 B at 22:21:
**overwritten a second time** before the move, more evidence for this entry. Open until each pod's first
hourly `.gz` appears under its own name; closing it also needs the batch job's orphan sealing, because the
HPA scaling back from 3 leaves unrotated `polaris-<pod>.log` files that nothing else will ever roll.


`logging.file.enabled: true` (hourly `.yyyy-MM-dd-HH.gz`, PVC `polaris-logs-pvc` created before the release by
`logging/k8s/polaris-logs-pvc.yaml` and mounted via `logging.file.storage.existingClaim`) for the
batch pipeline in `logging/PLAN-polaris-log-batch-2026-09-27.md`. Kade chose one file for the whole
Deployment over per-pod files. Checked from the chart, not the cluster: every replica renders the same
ConfigMap, `quarkus.log.file.path = /deployments/logs/polaris.log`, and nothing in `templates/` or
`values.yaml` puts a pod name in it — **the HPA does not create per-pod files.**

One writer is safe. Two are not: HPA scale-out (max 3) or a RollingUpdate's surge pod each open the
same path with independent JBoss rotation state — one renames the file while the other keeps writing
into the renamed inode, or rolls the other's fresh lines under the previous hour's name. `#40`'s
bursts of same-size `.1`–`.14` rolls minutes apart are the shape this produces, and were never ruled
out. **Watch for it:** records from two `hostName`s inside one rotated file, or an hour with two
same-name rolls. **The fix is one line** — `fileName: polaris-${HOSTNAME}.log` (Kubernetes sets
`HOSTNAME` to the pod name) — plus the batch job sealing a deleted pod's last file. The other safe
shape is `replicaCount: 1`, HPA off, `strategy: Recreate`.

Also written with it, each to be confirmed from the running pod (PLAN step 2):
`QUARKUS_LOG_FILE_JSON_ENABLED=true` (the variable `#38` deleted, live again now the handler is on),
`QUARKUS_LOG_FILE_ROTATION_ROTATE_ON_BOOT=false`, `TZ=Asia/Seoul` (the suffix is formatted in the JVM
zone; `timestamp`/`_time` gain `+09:00`, which the `_time` date mapping accepts), `maxFileSize: 2Gi`
(size roll made unreachable — it cannot be disabled once a suffix is set), `maxBackupIndex: 50`,
the claim outside the release (first cut used the chart's own `<fullname>-logs`; Kade's first check found
no such claim — `NotFound` — and asked for the PVC to exist first). **NOT VERIFIED: no helm, no kubectl from the Cowork session that wrote it.**

**#47 — The operational report window is 1 hour, not 30 minutes. Decided 2026-09-21, not rolled, and
the thing to watch after it rolls is not size but the per-window caps.** 2026-09-21.

Kade's manager set `WINDOW_SECONDS` to **3600**. This supersedes the 1800 that every document since
2026-09-04 has called "the revert" — it is not a revert to a previous operational value, because 1800
never ran either. **It is explicitly retunable after deployment during monitoring; 1 h and 2 h are the
two candidates.** So nothing should hardcode it: read `window_seconds` off a report row.

Still unrolled. It lives in `fluent-bit/polaris_access_log.lua` L162, so it is a Lua change —
`bash fluent-bit/apply-lua.sh` (tests → apply → restart), not a Helm upgrade. `Interval_Sec` stays **5**
(720 ticks per window is harmless: a tick inside the window is one Lua call and is discarded; keeping it
at 5 holds label skew at 0–5 s, which is 0.14 % of an hour). The old note in `logging/fb-values.yaml`
telling you to put `Interval_Sec` back to 30 belongs to the shipper and is history.

**What actually changes, and it is not the byte count.** Windows per day go 2880 → 24. Total rows fall,
but by much less than 120×, because the row counts are driven by *distinct keys per window* and a longer
window accumulates more of them. The caps are per window and do not scale with it:

    REPORT_MAX_RESOURCES  500      REPORT_MAX_PRINCIPALS 200      REPORT_MAX_ROLE_KEYS 100

At 1 hour a window accumulates roughly twice what a 30-minute window did against those caps; at 2 hours,
four times. Overflow is not data loss — the totals stay exact and the overflow lands in `__other__` — but
per-key trend is what tier 3 exists for, and `__other__` is where trend goes to die. **First window after
the roll, check `resources_other`, `resources_other_distinct`, `principals_other` and `role_keys_forced`.**
Non-zero means choose: shorter window, or higher cap (traded against Lua memory).

Second-order, worth a decision before dashboards get built (`PLAN-audit-log-todo` 3.8): the collection-gap
alert is "no new `polaris-report-*` document in a window". At 30 s that fires in a minute; **at 1 hour the
worst case is two hours.** That alert should probably watch tier 1 (`k8s-logs-*`) flow instead — the
pipeline stopping is exactly the case where no report will ever arrive to be missed. Spec §11-22.

Verification cost changes too: one verification window is now an hour, so `step10`/`step11` runs are no
longer something you iterate on casually. `PLAN-audit-log-todo` phase 0, 1.4 and 1.5 were already
sequenced to finish before this for that reason.

**#46 — A 5xx can be missing from its resource row and present in the summary, and that is by
design. The intentional 500 probes landed in `__errors__`.** 2026-09-21.

From the `polaris-report-2026.09.21` export. Kade's changed traffic includes a deliberate 500
generator: catalog `nb1789965827bh` with its S3 endpoint pointed at `127.0.0.1:1`, so
`create_table` fails with `SdkClientException: Connect to 127.0.0.1:1 ... Connection refused`.
Three of them fired (`rid nb-1789965827-3201..3203-probe-500-black_hole_endpoint-create_table_N`).

**They are not on the resource row for their path.** `/api/catalog/v1/nb1789965827bh/namespaces/
bh_ns/tables` exists as a row in that window with `requests: 1, errors: 0` — the row a later
successful read created. The three 500s are in `__errors__` (`requests: 56, errors_4xx: 53,
errors_5xx: 3`).

This is the `create=false` rule doing its job (Lua L292-296): **an errored request may not create
a resource row**, so a client walking nonexistent table names cannot fill the key space. The row
that does exist was created *after* the failures, and the rule is evaluated per record — "was
there a row at that moment", not "is there one by the end of the window".

Nothing is lost that the design promised: `summary.errors_5xx` is 7 and correct, the margin
`summary == sum(resource rows)` holds, and all seven 500s are stored as full documents by rule 3.
**Only the attribution is gone.** If a probe's whole point is to see a 5xx attributed to one
endpoint, send one 2xx to that path first, in the same window.

Worth deciding, not urgent: whether `__errors__` should carry a `resource_kind` breakdown, or
whether errored requests should be allowed to create a row when the path matches a
`RESOURCE_PATTERNS` entry (bounded key space, unlike arbitrary table names).

**#45 — Polaris 1.6.0's event listener throws on the same null path as `#24`, and the pipeline
keeps it only because of rule 1.** 2026-09-21.

Two ERROR documents in the 09-21 export from `org.apache.polaris.service.events.PolarisEventListeners`:

    Error while delivering BEFORE_RENAME_TABLE event to listener 'persistence-in-memory-buffer'
    (InMemoryBufferEventListener_Subclass@3cfbe489)
    java.lang.NullPointerException: Cannot invoke "...TableIdentifier.toString()" because the
    return value of "...()" is null

and the same for `BEFORE_RENAME_VIEW`. Both coincide with `#24`'s rename-with-null-identifier
probes, so the null reaches the event listener as well as the handler. **New in 1.6.0** — the
plural `event-listener.types` that the upgrade enabled is what makes this listener run at all.

**For the pipeline this is a non-event, and that is the interesting part.** `PolarisEventListeners`
is **not** in `APP_ALLOW` (which holds exactly `IcebergExceptionMapper` and `PolarisServiceImpl`).
It is stored because rule 1 keeps every `ERROR`/`WARN` regardless of the allowlist — the guard
against a new logger disappearing silently. It worked on its first real test.

To decide: whether an in-memory buffer listener failing on every null rename matters to Polaris
(it is a buffer, and the request already 500s), and whether `event-listener.types` should keep
`persistence-in-memory-buffer` enabled locally at all.

Also from the same export, not new issues: `org.apache.polaris.service.catalog.iceberg.LocalIcebergCatalog`
dropped **42** lines in 25 seconds, which is the condition the Lua's own L556 says should trigger an
`APP_ALLOW` review (`a new org.apache.polaris.service.* in app_dropped`). Full drop tally:
`CatalogUtil` 43, `LocalIcebergCatalog` 42, `BaseMetastoreCatalog` 30, `BaseMetastoreViewCatalog` 9.

**#44 — Quarkus cannot express a log retention TTL, and the PVC archive is the proof. The
27 MB reaching back to 08-21 is ORPHANED: no rotation setting will ever delete it.** 2026-09-18.

Kade asked for "remove logs older than 3 days" on the Polaris log PVC and, when told a sweeper
would be needed, answered *"max index count rather than day, since this count means day."* It
does not, and the evidence was already in this repo.

**What JBoss actually does.** `quarkus.log.file.rotation` offers `max-file-size`,
`max-backup-index` and `file-suffix`. There is **no age-based deletion anywhere in it**. With a
suffix set, the handler is `PeriodicSizeRotatingFileHandler`: `max-backup-index` bounds only the
numeric index **inside one day** (`polaris.log.2026-09-16.1 .. .N`), while the daily roll mints a
new basename and **nothing deletes the previous day**. That is exactly how a bound of 5 coexists
with ~130 files over a month — the bound was real, it was not bounding days.

**Two readings from the live listing (Kade, 2026-09-18) that settle the live config:**

```
polaris.log.2026-09-16.4.gz  458929  Sep 16 08:41
polaris.log.2026-09-16.gz    201788  Sep 18 01:27   <- periodic roll, no numeric index
polaris.log.2026-09-18.1.gz    1225  Sep 18 01:35
polaris.log.2026-09-18.2.gz    1017  Sep 18 01:35
polaris.log.2026-09-18.3.gz     307  Sep 18 01:34
```

1. **The live pod rotated with `.yyyy-MM-dd.gz`** while `polaris/values.yaml` says
   `fileSuffix: ~`. A dated file with *no* numeric index is the periodic roll's signature. So
   the file's value has **never been in effect** — `#20`'s shape again, and the same finding
   `#40` reached from the `.14`-vs-5 direction. `#40` can stop asking whether the bound is
   per-day: it is.
2. **Three rotations of ~1 KB files within 2 minutes at 01:34–01:35**, when `maxFileSize` is
   10Mi. Size did not trigger those. That is either pod shutdown or `#8`'s rotation storm.
   **Not established** — recorded because it is the first sighting of the shape on a day whose
   replica history is known (`#8` fired `REPLICAS 3` that morning).

**The change (2026-09-18):** `polaris/values.yaml` now states the retention contract as a **byte
cap**, which is the only thing this handler can enforce: `fileSuffix` stays null (so the handler
is the plain `SizeRotatingFileHandler` and the ring is `polaris.log.1 .. .N`, nothing
accumulating across days), and `maxBackupIndex` 5 → **45**, giving `10Mi x 46 = 460Mi` on the
5Gi PVC. Sized from the archive's own rotation rate: 11–14 rotations on busy days, so ~3 busy
days or a fortnight of quiet ones. **The cost is gzip** — compression came from the suffix
ending in `.gz`, so the ring is 460Mi of plaintext where the old scheme held ~23MB compressed.

**DONE 2026-09-18: THE PVC WAS REMOVED.** Runbook executed in full — shipper and VictoriaLogs
uninstalled, Polaris upgraded without the mount (verified: `ls /deployments/logs` → *No such
file or directory*), `polaris-shared-logs-pvc` deleted, 27 MB archive gone as chosen. **The
other half of `#44` — the ISM policies — is still unapplied.** Original note follows:

**SUPERSEDED IN PART, SAME DAY (2026-09-18, Kade): THE PVC IS BEING REMOVED ALTOGETHER.**
Its only two consumers are going — `fb-polaris-shipper` (which tailed it into VictoriaLogs) and
the Polaris mount itself. So:

- **The orphan problem below is resolved by deletion, not by a sweep.** Deleting the claim takes
  the ~130 dated `.gz` files with it. Kade chose explicitly not to keep a copy.
- **`maxBackupIndex` is back to 5**, reversing the 45 committed hours earlier. 45 (a 460Mi ring)
  was sized against a 5Gi PVC; with no PVC, `logsDir` is the container's writable layer — node
  disk on the single OrbStack node — where 460Mi is worse than the 60Mi it replaced.
- **`extraVolumes` / `extraVolumeMounts` are now `[]`**, and the two `QUARKUS_LOG_FILE_JSON_*`
  variables `#38` called dead config are deleted.
- **A trap went with them, and it had never fired.** The chart mounts its own `logs-storage`
  volume at `.Values.logging.file.logsDir` when `logging.file.enabled` is true — the *same*
  `/deployments/logs` that `extraVolumeMounts` claimed. Both at once is a duplicate mountPath,
  which the API server rejects outright. `enabled: false` is the only reason nobody hit it. So
  **`#38`'s "the handler is off" was also load-bearing for the deployment rendering at all.**
- Sequence, finalizer trap and per-step verification:
  [`logging/RUNBOOK-log-pvc-removal-2026-09-18.md`](../logging/RUNBOOK-log-pvc-removal-2026-09-18.md).
  **Nothing has been run** — the repo no longer mounts the PVC, the cluster still does.

**The finding above is unaffected.** Quarkus still has no age-based retention; that is why "3
days" could never have been a rotation setting in the first place, whichever volume it wrote to.

**`step13` apply defect, found by Kade on first `--apply` (2026-09-18) — the script destroyed the
evidence of its own failure.** Sections 3 and 4 were written as `python3 -c '...'` containing
`\"` escapes. Single-quoted shell passes the backslashes through verbatim, and a backslash inside
an f-string expression is a `SyntaxError`, so both blocks crashed **after their `curl` had already
run** — at precisely the point where they were meant to report what OpenSearch replied. Section 5
then correctly found 0/5 indices managed, with no way to tell why.

**Why it escaped the offline test:** the smoke run could not reach a cluster, so the section-1
preflight (correctly, by design) aborted before sections 3–5 ever executed. **The hardening that
prevents a false pass also hid everything behind it.** A gate that stops early tests nothing
downstream of itself.

**Fixed:** all embedded Python is now heredocs (`python3 - "$ARG" <<'PY'`), no `python3 -c`
anywhere; failures print the **whole** OpenSearch error, not a 300-char truncation; a new
**section 3b** reads the policy list back so storage is confirmed independently of what the PUT
replied; and a failed PUT now **aborts before section 4** instead of attaching policies that may
not exist. A **self-check compiles every embedded Python block at start-up, with no cluster, on
every run** and refuses to proceed otherwise — verified by reintroducing the exact bug
(`f-string expression part cannot include a backslash`, refuses, exit 1) and removing it again.

**CONFIRMED LIVE 2026-09-18T08:45Z, with the readout, and the ISM half of `#44` is DONE.**
`GET _plugins/_ism/policies` returns all three (`_seq_no` 0/1/2, `_primary_term` 1,
`schema_version` 27, `ism_template` priority 100). `explain` shows `polaris-logs-2026.09.18`
managed and in state `hot`, action `transition`, step `attempt_transition_step`,
`step_status: condition_not_met` — **that last line is the one that matters: ISM is actively
evaluating the age condition, not merely attached.** Figures and dates in
[`roadmap.md`](roadmap.md).

**ISM stores more than we wrote, and it is not drift.** The stored `delete` action carries a
`retry: {count: 3, backoff: exponential, delay: 1m}` block, plus `error_notification: null`,
`last_updated_time` and `schema_version: 27`. Those are **server-side defaults applied at PUT**.
The repo JSONs deliberately do **not** chase them: a re-PUT of the file is still idempotent and
ISM re-adds them. Anyone diffing `logging/opensearch/ism-*.json` against
`GET _plugins/_ism/policies` will see this difference and it is expected.

**Task E's targets are now identified**, and both are 30 s-window indices:
`polaris-report-2026.09.17` (58 docs) and `polaris-report-2026.09.18` (1,050 docs). At 30d they
survive to **2026-10-17 / 10-18**. Everything older is already gone. Deleting them early is
manual, by name (`devtools-ism.console` §D).

**ANSWERED on the re-run: the PUT had never failed.** Section 1 and 2 of the 2026-09-18 re-run
show all three policies stored and all five indices managed — `polaris-logs-2026.09.18`,
`polaris-report-2026.09.17/18`, `k8s-logs-2026.09.17/18`. **The first `--apply` worked; only its
reporting crashed**, and section 5's `0/5` was read before the attach had settled. So the visible
failure was entirely manufactured by the broken error path. My guess about `policy_id` in the
body was wrong too: this cluster accepts and stores it (the docs put the id in the URL, which is
authoritative if they ever disagree).

**A SECOND BUG, mine, introduced by the fix itself (`ffc11a2`) and caught by Kade's re-run.** I
rewrote section 3 through a Python `%`-format template, which collapsed `${spec%%:*}` to
`${spec%:*}` — shortest-suffix instead of longest. `PID` became
`polaris-logs-3d:/Users/kade/.../ism-polaris-logs-3d.json` and OpenSearch answered *no handler
found for uri*. Fixed and proved by parsing the three specs and printing the triples. **The
self-check could not catch this**: it compiles embedded Python, and this was shell. A fix
delivered under time pressure introduced a defect of a kind the new guard does not cover.

**ISM API confirmed for 3.5.0** — `PUT _plugins/_ism/policies/<id>` (update needs
`if_seq_no`+`if_primary_term`), `POST _plugins/_ism/add/<pattern>`,
`GET _plugins/_ism/explain/<pattern>`, `POST _plugins/_ism/remove`, `POST _plugins/_ism/change_policy`.
Unchanged since 1.x, and two of them answered on this cluster. Dev Tools equivalents, generated
from the policy files and checked body-for-body against them:
`logging/opensearch/devtools-ism.console`.

**AND A THIRD ERROR, in prose rather than code: `handoff task E is NOT subsumed by F`.** I wrote
that the report policy would sweep the 30 s-window verification indices "on the first sweep".
That was true when the figure was **3 d** and became false the moment Kade set **30 d** — they now
survive thirty days from creation. I carried the sentence across the change without rechecking
it. Corrected in the handoff, the proposal §5.3 and the console file §D; deleting them is still
manual, by name, never by wildcard.

**Gate defect, found by Kade on first run and fixed the same day.** The runbook's step-3 gate
grepped the whole `--dry-run=client --debug` output for `/deployments/logs` and wanted 0. It
returns **2** on a correct chart: `--debug` echoes USER-SUPPLIED VALUES and COMPUTED VALUES
before the manifest, and `logging.file.logsDir` is still a legitimate *value* — it is simply
mounted nowhere. Both template uses (`deployment.yaml:268`, `configmap.yaml:135`) are inside
`{{- if .Values.logging.file.enabled }}`, which is false, so the manifest carries neither. The
gate now slices from `MANIFEST:` first, checks it found a Deployment before trusting a zero
(`#43`), and carries a **positive control** (`quarkus.log.file.enabled=false`, want 1) so that
a mistyped pattern cannot score 0/0 and read as a pass. `PROPOSAL §9.3` already said to gate
without `--debug`; this repeats `#43`'s lesson in a third place.

**WHAT REMAINS OPEN (the original list, minus what deletion settles):**

- ~~The ~130 dated `.gz` orphans need a one-time `find -delete`.~~ **Closed by the PVC removal**
  — the claim takes them with it (runbook step 4). The `find -delete` is only wanted if you
  want them gone *before* the teardown.
- **None of it runs while `logging.file.enabled: false`** (`#38`, settled), and after the
  teardown there is no volume either. The ring is config for a handler that is off writing to a
  disk that would now be the node's. **If file logging ever comes back, set
  `logging.file.storage` and let the chart provision its own claim** — do not point it at node
  ephemeral storage, and pin `replicaCount` first (`#39`).
- **Never confirm the ring from this values file.** It is the file that was wrong for a month:
  `exec ... grep rotation /deployments/config/application.properties`.

**#43 relevance:** the first draft of `step13-ism-apply.sh` had the same self-arming fault —
an unreachable cluster printed "could not list policies" and the script still offered `--apply`.
An unreachable preflight now exits 2 and blocks the write.

**#42 — `threadName` / `threadId` RESTORED to `polaris-logs-*`, REVERSING `#30`: ROLLED AND
VERIFIED ON TRAFFIC 2026-09-18.** Decision B (Kade), taken on the cost analysis below rather
than on the original premise, which was half wrong.

**ROLLED (Kade), pod `benchmarks-fluent-bit` started 2026-09-18T07:23:34Z, image 5.1.1,
`restartCount 0`.** Values-only path as planned; the Lua ConfigMap sha is `f92bb6d4dbbfc346`,
**unchanged** and last written 2026-09-16T15:59:12Z, which is the positive proof that this roll
touched values only and no `apply-lua.sh` ran.

**VERIFIED — the assertion is the exact inverse of `#30`'s.** `#30` recorded *"0 of 386
`polaris-logs-*` docs carry `threadName`, `threadId` or `ndc`."* step3 after traffic:

```
PASS  polaris-logs-*: 367 docs carry message since pod start
PASS  polaris-logs-*: 367 docs carry threadName.keyword since pod start
PASS  polaris-logs-*: 367 docs carry threadId since pod start
PASS  polaris-logs-*: 0 docs with ndc since pod start
```

367/367 on all three, `ndc` 0, and every schema-v6 absence still holds (`processName`, `stream`,
`flb_tag`, `app`, `_msg` all 0; report envelope clean; P3 `Exclude_Path` holding at 0 docs from
Fluent Bit's own pod). Pre-traffic run was clean too, with the three presence checks at `????`
(0 docs, no traffic yet) — see the caveat on that below.

**No per-item rejection, and that settles the mapping question empirically.** Tier-2 output
`ok=367 errors=0 retries_failed=0`, and section 2 found no parser/Lua complaint in the pod log —
which is where a per-item OpenSearch rejection inside an HTTP 200 would land, since it increments
none of the counters. **Today's index was shaped by DYNAMIC mapping, not by the template** (the
template is not retroactive; `polaris-logs-2026.09.18` predates it), and `threadId` indexed
cleanly anyway. That is direct confirmation of this entry's claim below that the explicit
`threadId: long` mapping is **defensive, not load-bearing**.

**The Lua policy is unchanged, as intended.** `polaris_noise_filter dropped=497 added=164`, so
367 stored + 497 dropped = 864 records in, a **57.5 % drop rate** against the 58 % the v5 policy
has held since `#31`. The two extra fields changed what each record carries, not what the filter
decides.

**`step12` RUN AND PASSED 2026-09-18** — `{"acknowledged":true}`, **11/11 declared fields** stored
and simulated, `dynamic_templates` 1/1. *"tomorrow's `polaris-logs-*` index is the first one
shaped by it."*

**My prediction of "8/8" was wrong, and the way it was wrong matters.** I extrapolated from
`#30`'s 7/7 by adding `threadId`. But `#32` (schema v6) expanded this template *after* `#30` —
`client_ip`, `message`, `exception.message` were added — so the file has declared **10** leaf
fields since v6, and 11 with `threadId` back. **Never carry a count forward across a schema
change**; count the file.

**The `BEFORE` block closed `#32`'s open item, negatively — this is the real find.** It printed
today's index mappings:

```
polaris-logs-2026.09.18   _time=date  access_log_parse_error=boolean  client_ip=text
  exception.message=text  exception.refId=long  http_status=long  message=text
  response_size=long  secret_redacted=boolean  sequence=long  threadId=long
```

**`client_ip` is `text`, but the v6 template declares it `ip`.** Today's index was created at
00:00Z on 2026-09-18, long after the 09-16 rolls, so if the v6 template had been stored it would
be `ip`. It is not. Therefore **the v6 detail template was never actually applied to the cluster
until this run** — today's index is still shaped by the **7-field pre-v6 template** `#30` stored
on 2026-09-16, which declared no `client_ip`, no `message` and no `exception.message` (the three
that now show as plain dynamic `text`). That is exactly the count: 7.

`#32` said as much and nobody read it: *"NOT verified: … OpenSearch acceptance of the v6 mappings
(step9/step12 on the cluster)"* and *"Not read: … step9/step12 output"*. **It was not verified
because it had not happened.** This is the repo's own recurring lesson — an intent artifact
(the file) mistaken for an applied state — caught this time by a diagnostic block printed for a
different purpose.

**Consequence worth knowing: `dynamic_templates.strings_keyword_only` is a v6 addition, so it is
NOT on today's index either.** Undeclared strings there are ordinary dynamic `text` + `.keyword`,
i.e. analysed — so on `polaris-logs-2026.09.18` a bare `threadName` query *does* work. From
tomorrow's index it will not. **`threadName.keyword` is correct on both**, which is why step3's
check is written that way; do not let today's permissiveness teach the wrong habit.

**`step9` RUN AND PASSED 2026-09-18** — `{"acknowledged":true}`, **42/42 fields** stored and
simulated as declared, `dynamic_templates` matching, the six v4 integer fields confirmed `long`.
**Both v6 templates are now on the cluster**, which as of this morning neither was.

**Unlike `step12`, step9's output cannot say whether the report template had been applied
before.** Its informational block prints only `min_record_time` for existing indices (the `#25`
field), not the full mapping, so there is no `client_ip`-style giveaway. `polaris-report-2026.09.17`
and `.09.18` both show `min_record_time: date`, which is correct but is what dynamic mapping
produces anyway since the Lua stopped writing `""` on 2026-09-10 — it discriminates nothing.
**Treat the report side's prior state as unknown, not as "fine".** Given `#32`'s single unread
sentence covered both, the likeliest answer is that it was equally un-applied.

**SETTLED 2026-09-18: v6 was NOT applied to the report index either.**
`GET polaris-report-2026.09.18/_mapping/field/report_type` returned:

```
"report_type": { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } }
```

**Two independent discriminators, same answer.** No `"index": false` — the v6
`strings_keyword_only` template sets it. And `ignore_above: 256` where the template says
**1024**: 256 is OpenSearch's *built-in* default for dynamically mapped strings, so this is the
engine's own mapping, not ours, with no room for a "maybe it was partly applied" reading.

**So `#32`'s unread sentence was uniformly true of both templates: neither had ever been
stored.** The v6 mappings existed only in this repo from 2026-09-16 until `step12` and `step9`
ran on 2026-09-18. Every `polaris-logs-*` and `polaris-report-*` index created in between —
09-17 and 09-18 — is on pre-v6 mappings **for life**, and today's two are the last of them.

**The cost of the two-day gap is small and bounded**, which is worth stating so nobody
over-reacts to it: on those indices report `message` is analysed where v6 wanted it
`index: false`, categoricals are analysed where v6 wanted `keyword`-only, and `client_ip` is
`text` where v6 wanted `ip` (so no IP range queries on 09-17/09-18 detail indices). **No data is
lost, nothing is unqueryable, and no query in the repo changes shape** — every one already goes
through `.keyword`, which exists under both mappings. **From 2026-09-19 both index families are
v6.**
- helm revision number (expected 21) — not recorded.
- `step10`/`step11` window readout — not run; the detail-by-logger and report-row equality
  checks of `#32`/`#31` were therefore not re-established on this roll.
- Average document size before/after — **deliberately not measured**, see the withdrawal below.
  `#39`'s replica count at each reading was likewise not needed, for the same reason.

**A gate defect found in the process, still OPEN at the time of this roll.** step3's `huh()`
prints `????` and does **not** increment `FAIL`, so `RESULT: post-upgrade checks passed` was
compatible with both thread fields being absent — the pre-traffic run proves it, having printed
`????` on all three presence checks and still passed. The verification above is sound because the
`PASS` lines were read directly, not inferred from the RESULT line. **The fix is `#43`.**



**The premise that produced the request was wrong in its second half.** Kade asked for the
fields back reasoning *"I had them removed believing the Lua parsed them; they cost no CPU to
ship."* The first half holds — the Lua reads only `loggerName`, `level`, `message`, `_time`,
`mdc`, and `5315e0d` dropped these in the `record_modifier`, not in Lua. **The second half does
not:** `REVIEW-pipeline-2026-09-16.md` P1 moved `polaris_field_trim` *ahead* of the Lua
precisely because the Lua converts every record msgpack -> Lua table -> msgpack, so every
surviving field is paid for in that conversion whether the Lua reads it or not. Shipping them
is a cost; the decision was taken anyway, with the cost quantified and accepted.

**The cost, derived - not guessed, and not worth re-measuring on the cluster.** `#30`'s handoff
called the per-field share "never measured separately." It effectively was: P1's table breaks
the 717 B pre-trim record down per key.

| field | P1 share | bytes | literal JSON check |
|---|---|---|---|
| `threadName` | 4.7 % | **~34 B** | `"threadName":"executor-thread-3",` = 33 B |
| `threadId` | (in the 4.7 % shared with `processId`, `ndc`) | **~13 B** | `"threadId":46,` = 14 B |

- **Stored detail doc: +47 B -> +7.2 % (access, 649 B) / +6.3 % (app, 743 B).** That is
  almost exactly the -7...8 % schema v6 bought (`#32`). **This change gives back the v6
  document-size win.** Accepted knowingly.
- **Into the Lua:** post-trim record ~488 B / 9 keys -> **~535 B / 11 keys (+9.6 % bytes,
  +22 % keys)**, on all ~720 records per window (the inbound conversion runs on every record;
  the return trip only on the 42 % kept).
- **On disk this is an over-estimate.** `threadName` falls to `text index:false` + `.keyword`,
  i.e. one keyword index over ~5 distinct values (`executor-thread-N`, `vert.x-eventloop-thread-N`),
  ordinal-compressed doc_values; `_source` is stored compressed. The `_source` figure is the
  honest ceiling, not the disk number.

**Why the handoff's before/after measurement is NOT being run - this is the part to keep.** The
handoff made the measurement "the point of the exercise." Worked through, it cannot deliver:

1. **`_source` bytes** - already derived above to within ~5 B; a live reading reproduces it
   while fighting `#39`'s replica flapping.
2. **On-disk store size** - *not obtainable on a same-day roll.* The template shapes only
   tomorrow's index, so before- and after-shaped docs land in the **same** index and
   `_index/_stats` store size cannot be attributed to a subset of documents. A trustworthy
   figure needs a full day's separation.
3. **Lua CPU** - out of reach by `REVIEW-pipeline` P1's own words (*"Cannot be measured from
   Cowork: CPU. It is a phase 3.1 load-test number."*), and the `helm upgrade` restarts Fluent
   Bit, so the first window after the roll is `#31`'s R4 partial window and unusable as the
   "after" reading anyway.

So this was decided as **decide-then-accept-47 B**, not measure-then-decide. Building the
scaffolding would have cost more than the information.

**`ndc` stays removed** - different reason, not a cost one: `""` on all 300 sampled detail docs
(`084100Z`) and `""` in 1.6.0's console output too. An always-empty field on every document.

**`threadId` is redundant with `threadName` here, and Kade took B knowing that.** Both are
per-thread identifiers and they are strictly 1:1 in every sample in this repo
(`executor-thread-3`<->`44`, `executor-thread-6`<->`48`, `vert.x-eventloop-thread-1`<->`33`,
`-0`<->`32`). Option A (name only, 34 B, no template edit) was offered and declined in favour of
matching the handoff as written.

**What it buys, which `#30` did not weigh.** Not "tracing value" in the abstract -
`mdc.requestId` is already the correct per-request key. Two things it does not cover:
1. **Records with no MDC at all** - start-up, background tasks, pool and JVM-adjacent logs.
   `threadName` is their only correlation handle in tier 2.
2. **Thread identity joined to the parsed access fields.** Tier 1 `k8s-logs-*` carries the
   thread fields on 870/870 records, but only on the raw line - it has no `api_path`,
   `http_status` or `user_principal_name`. *"Which thread served the 404s for principal X"* is
   answerable in **tier 2 only.** That is the real argument, and it is stronger than the one
   the request arrived with.

**Changed (all committed, none applied):**
- `fluent-bit/values.yaml` - the two `Remove_key` lines deleted from `polaris_field_trim`;
  `Remove_key ndc` kept. Korean comment rewritten: it stated the 2026-09-16 decision and would
  have been false the moment the lines went.
- `logging/opensearch/polaris-logs-template.json` - `threadId: long` restored;
  `_meta.removed_2026-09-16` replaced by `_meta.restored_2026-09-18`; `measured_from` no longer
  says "(removed 2026-09-16)".
- **`logging/scripts/step2-render-gate.sh` and `step3-postupgrade.sh` - the `#30` assertions
  INVERTED.** This is the part that would have broken the roll silently: step2 asserted
  `Remove_key threadName|threadId` present **1**, step3 asserted 0 docs carrying either field.
  Both would now FAIL on a correct change. step2 expects **0** for the two lines (kept as
  counts, so a silent reappearance is still caught) and 1 for `ndc`; step3 drops them from its
  absence loop and asserts them **present** instead.
- `step12` needed **no** change - it iterates the file's declared fields, so it picks `threadId`
  up on its own and should now report 8/8 where `#30` recorded 7/7.

**`threadName` must be queried as `threadName.keyword`, never bare.** It gets no explicit
mapping (and must not get one), so under the v6 template it is `text` with `index:false` plus a
`.keyword` sub-field: a `term`, `exists` or `match` on the bare field finds nothing. step3's new
presence check names `threadName.keyword` for exactly this reason - the bare field would have
failed it for the wrong reason. `threadId` is mapped `long`, so the bare field is right for it.

**The `threadId: long` mapping is defensive, not load-bearing** - a correction to the handoff,
which implied otherwise. `threadId` arrives as a JSON integer (template `_meta.measured_from`,
508-doc readout) and `dynamic_templates.strings_keyword_only` matches `match_mapping_type:
string` only, so dynamic mapping reaches `long` unaided. It is declared because this file exists
so that a daily index's types are not decided by whichever document arrives first.

**Apply path - values-only, NOT `apply-lua.sh`:** `step2` -> `helm upgrade` -> `step3`. The Lua is
untouched. If `WINDOW_SECONDS 30 -> 1800` is landed too, that *is* a Lua change and the pair takes
`apply-lua.sh --no-restart` -> `step2` -> `helm upgrade` with **no restart between** (`#31`);
**prefer landing them separately.** The template is not retroactive - `threadId`'s mapping
arrives with the next daily index, and indices created 2026-09-16...18 simply lack both fields.

**NOT VERIFIED:** no `helm lint`, no `--dry-run` render, no cluster command of any kind - this
was written in a Cowork session with no `helm`/`kubectl`/`docker` reach (CLAUDE.md). The
inverted gates have had `bash -n` only; neither has been run against a render or a cluster.

**#43 — step3's presence checks could pass while asserting nothing: FIXED, NOT RE-RUN.**
2026-09-18. Found while verifying `#42`, on this session's own defect.

`step3-postupgrade.sh` has three verdict functions and only one of them counts:

```
ok()  -> PASS
bad() -> FAIL, FAIL=$((FAIL+1))     <- the only one RESULT reads
huh() -> ????                        <- does not
```

The `#42` presence checks called `huh` on zero documents, copying the existing `message` idiom,
which is non-fatal because a pre-traffic run legitimately has none. **So `RESULT: post-upgrade
checks passed` was compatible with both thread fields being completely absent** — and the
pre-traffic run of the `#42` roll demonstrates it exactly: `????` on all three presence checks,
`RESULT: post-upgrade checks passed`. A gate that passes for the wrong reason, which is the same
class of bug as querying bare `threadName` under the v6 template.

**`#42` is verified regardless, because the `PASS` lines were read directly** (367/367) rather
than inferred from the RESULT line. The hole was in what a *future* reader of that RESULT line
would have been entitled to conclude.

**Fixed: the checks are now self-arming.** `$M`, the count of documents carrying `message`, is
the arming signal. If documents are being written since pod start and the thread fields are
absent *from those documents*, that is a real `bad` — not a "run traffic and re-try". Only when
nothing has been written at all is 0 uninformative, and only then does it stay `huh`.

**The general shape is still there and is deliberate**, so do not "fix" it wholesale: `huh`
exists for checks that genuinely cannot distinguish "broken" from "not yet". The rule that came
out of this: **a presence check needs an arming signal, or it is not a check.** Any future
presence assertion added to step3 should name what makes its zero meaningful.

**NOT VERIFIED:** `bash -n` only. The new `bad` branch has never been exercised — it fires only
when `message > 0` and the field count is 0, which is precisely the state the `#42` roll did not
produce. Re-running step3 as-is should reproduce the same all-`PASS` section 5.

**#41 — OPEN. A 1.6.0 pod crashed three times at rollout: `Reason: Error`, exit code 1, dead
four seconds after start. NOT an OOMKill.** 2026-09-18.

```
Last State:  Terminated   Reason: Error   Exit Code: 1
Started:     Fri, 18 Sep 2026 14:41:12 +0900
Finished:    Fri, 18 Sep 2026 14:41:16 +0900      <- four seconds
```

`benchmarks-polaris-6dcf6758f9-5vpmc` carries `restartCount 3`; its sibling `…-fl8jd` has 0.
14:41 KST is 05:41 UTC, which is the rollout minute, so the three crashes were at start-up and
the pod has been `Running` since. **The upgrade is verified regardless** — the pod that
serves traffic is this one, and the listener, console JSON and metastore checks all passed on
it. This is about an unexplained crash loop, not a broken upgrade.

**OOMKill was my first suspect and it is wrong.** `Reason: Error` with exit code 1 is the
process exiting, not the kernel killing it; an OOMKill reports `OOMKilled` and exit 137. So the
`1.33Gi` max heap in a `2Gi` limit is not implicated by this evidence, and the memory-pressure
story belongs to `#39` alone.

**Four seconds is the useful number.** It is too fast for a JDBC connect timeout and too slow
for the JVM rejecting a VM option outright, which lands in well under a second. That points at
Quarkus starting and then failing — a config validation error, a bind failure, or something the
application does at boot.

**Candidates, in the order the evidence favours them:**

1. **A start-up race between simultaneously starting pods against the metastore.** Three pods
   came up within the same minute and Polaris does metastore work at boot. This repo already
   has an entry for intermittent duplicate-key/500s from PG replica lag, and three concurrent
   bootstraps of realm `POLARIS` is the shape that provokes it. That the *second* pod never
   crashed fits a race that one loser hits.
2. **An unrecognized VM option.** `-XX:+ZGenerational` is valid on JDK 21 and the running image
   is `java-21-openjdk-21.0.11`, so this *should* be clean — but **the runbook's own
   `Unrecognized VM option` check was never run**, and the runbook predicted precisely this
   presentation ("CrashLoopBackOff with nothing useful in the Polaris log"). Cheap to exclude.
3. **A Quarkus config validation failure** on one of the changed keys — the plural
   `event-listener.types` is read successfully by the surviving pod, so this is unlikely, but a
   validation error is exit 1 at about this latency.

**One command answers it**, and it also covers candidate 2:

```bash
kubectl -n datahub-hynix logs benchmarks-polaris-6dcf6758f9-5vpmc --previous
kubectl -n datahub-hynix logs benchmarks-polaris-6dcf6758f9-5vpmc --previous \
  | grep -iE 'unrecognized vm option|error|exception|caused by' | head -30
```

**Run it before that pod is replaced.** `--previous` keeps only the most recent terminated
container, and `#39`'s flapping means pods come and go on their own — this reading is
perishable in the same way step 0's were, and the replica count is already back to 1.

**#40 — CLOSED UNANSWERED 2026-09-18, AND IT CANNOT BE REOPENED: THE EVIDENCE WAS DELETED
WITH THE PVC.** Half of it was answered — `#44` established the bound was per-day, because the
live pod ran `file-suffix: .yyyy-MM-dd.gz` while `values.yaml` said `~`, so `.14` against a
declared 5 is not a contradiction. **The other half is gone.** Whether the bursts of same-size
rotations minutes apart were `#8`'s rotation storm or one busy writer needed the rotated files
themselves, and they were destroyed at runbook step 4. `#8` is closed by removal rather than by
diagnosis, so nobody will ever know whether it had already bitten.

**That was a known, accepted cost** — the archive deletion was put to Kade with this consequence
stated and he chose it (2026-09-18). Recorded because "we closed it" and "we made it
unknowable" are different endings, and only one of them should be reused as a precedent.
Original entry:

**#40 — OPEN QUESTION. The Polaris log archive carries per-day rotation suffixes up to `.14`
while `values.yaml` sets `maxBackupIndex: 5`, and several days show a burst of same-size
rotations minutes apart — which is the shape `#8` predicted.** 2026-09-18.

From the `/deployments/logs/` listing (see `#38`): `polaris.log.2026-09-09.1.gz` through
`.11.gz`, each ~400 KB, with mtimes at 06:03, 06:11, 06:29, 06:35, 06:53, 07:16, 07:21, 07:58,
09:02 — and the same pattern on 08-21 (`.1`–`.14`), 08-24 (`.1`–`.14`), 08-31 (`.1`–`.14`),
09-15 (`.1`–`.12`).

Two things to explain, and they may be the same thing:

1. **`rotation.maxBackupIndex: 5`** is set in `polaris/values.yaml`, yet indexes reach `.14`.
   Either the setting is not in effect (this repo's recurring fault — and `#38`'s finding that
   the pod ran an older ConfigMap for days makes "not in effect" easy to believe), or the
   index is per-day rather than global and `maxBackupIndex` bounds something else.
2. **`#8`'s predicted mechanism is a rotation storm**: several pods with independent JBoss file
   handlers and independent rotation state on one `ReadWriteOnce` file, each rotating out from
   under the others. A cluster of same-size rotations minutes apart is what that would look
   like. **If so, `#8` has already bitten** — repeatedly, from Aug 21 onward — and was recorded
   as a hypothetical for a month while the evidence sat in the PVC.

**Do not treat this as established.** A single busy writer at `maxFileSize: 10Mi` will also
rotate many times in a morning, and those dates coincide with heavy notebook ladder runs, which
is the innocent explanation. The discriminator is **whether more than one pod was running on
those days** and whether records interleave inside one file:

```bash
# Were there multiple Polaris pods on 2026-09-09? (#8 needs that; the HPA had no metrics then)
kubectl -n datahub-hynix get events --field-selector reason=ScalingReplicaSet | head
# Do records from two hostNames appear inside ONE rotated file?
# NOT zcat -- the UBI9 runtime image has no zcat (tried 2026-09-18, `command not found`), and
# probably no gunzip or tar either, which also rules out `kubectl cp`. Stream the bytes out and
# decompress on the Mac:
kubectl -n datahub-hynix exec deploy/benchmarks-polaris -- \
  cat /deployments/logs/polaris.log.2026-09-09.5.gz > /tmp/polaris-0909-5.gz
gunzip -c /tmp/polaris-0909-5.gz | grep -o '"hostName":"[^"]*"' | sort -u
```

Two distinct `hostName` values inside one file is direct proof of interleaved writers and
closes `#8` as *bitten*. One value means the rotation burst was volume, and only the
`maxBackupIndex` question remains. **Note `#8`'s 2026-09-09 entry says the HPA had no metrics
then and could not scale at all** — so on that date one pod is the more likely answer, which
would make this volume rather than interleaving. Check rather than assume; the same entry's
metrics claim has already been overtaken once today.

**#39 — OPEN, and it has already fired. `targetMemoryUtilizationPercentage: 80` against a
`1Gi` memory request is a ratchet, not an autoscaler: this JVM exceeds the target at idle, so
the HPA pins Polaris at `maxReplicas` and cannot come back down.** 2026-09-18, measured minutes
after step 4.

```
benchmarks-polaris   cpu: 2%/80%   memory: 88%/80%   MINPODS 1   MAXPODS 3   REPLICAS 3
```

**Three pods at 2% CPU.** The scale-up was entirely the memory metric, and the arithmetic says
it was inevitable:

| quantity | value | source |
|---|---|---|
| memory **request** | `1Gi` | `values.yaml` `resources.requests.memory` — **HPA utilisation is measured against the REQUEST**, not the limit |
| memory **limit** | `2Gi` | `resources.limits.memory` — this is what the JVM sees as available |
| JVM **initial** heap | 50% of the limit = **`1Gi`** | `JAVA_TOOL_OPTIONS: -XX:InitialRAMPercentage=50.0` |
| JVM **max** heap | 65% of the limit = **`1.33Gi`** | `-XX:MaxRAMPercentage=65.0` |

The JVM commits a **1Gi initial heap — exactly the whole memory request — before serving a
single API call**, and then adds metaspace, code cache, thread stacks and direct buffers on
top. So memory utilisation starts near or above 100% of the request and stays there. The
observed 88% is a working-set figure and slightly under that estimate, which fits; the
direction is what matters. **The target is exceeded at idle.**

Two consequences:

1. ~~**It will not scale back down.**~~ **WRONG, and corrected within the hour: it scaled
   3 → 2.** The next `get pods` showed **two** pods. So utilisation *does* fall back below the
   target, and the reason is that **ZGC uncommits unused heap by default** (`-XX:+ZUncommit`,
   after `ZUncommitDelay`) — `InitialRAMPercentage` sizes the heap at start but does not pin
   the resident set there for ever. The memory metric is therefore **not monotonic**, and the
   "ratchet" reasoning was too strong.

   **What replaces it is not better news, just a different failure.** The metric still has
   nothing to do with load — it tracks JVM heap behaviour — so the HPA **flaps**: up on
   warm-up and GC pressure, down after ZGC returns pages, at `cpu: 2%` throughout. Pod churn
   rather than a stuck maximum. For `#15` that is worse, not better: replica count changes
   under a running ladder, so hypothesis C is **intermittently** live and a run can straddle a
   scale event.

   **The full observed sequence, 2026-09-18, inside about one hour:**
   `0` (step 2d) → `1` (step 4's explicit scale) → **`3`** (HPA, on memory at 2% CPU) → `2` →
   **`1`**. It is back at `minReplicas` with the cluster idle. So the resting state is 1, the
   scale-up is a warm-up artefact, and **hypothesis C is live only during the up-phases** —
   which is exactly the condition under which a ladder run gives an irreproducible answer.
2. **It was at `maxReplicas` with its target unmet at the moment it was measured**, so at that
   instant it had no headroom for a genuine CPU-load event. Given the flapping above, treat
   this as a recurring condition rather than a permanent one.

**What it drags in:** `#15` hypothesis C is **alive again** (three entity caches to diverge —
see that entry's 2026-09-18 note); three writers into `events`; three times the JDBC
connections through Pgpool. `#8`'s *specific* hazard — three pods appending one shared log
file — is the one thing that is **not** live, because `#38` establishes the file handler is off.
**`#8`'s prediction was right and its stated mechanism was wrong**, which is worth more than
either fact alone.

**Watch for OOMKills.** Max heap is 1.33Gi against a 2Gi limit, which leaves ~0.67Gi for
everything non-heap. That is not obviously enough, and three pods on one OrbStack node
multiplies the node-level pressure. Check `restartCount` and `lastState.terminated.reason`.

**Do not fix this mid-verification.** *Polaris is not to be changed* still stands, and this is a
values change that needs its own plan. The options, for that plan and not for now:

- **drop `targetMemoryUtilizationPercentage` entirely** and keep CPU only — scaling a JVM on
  memory is the anti-pattern that produced this, since a JVM's footprint reflects its heap
  settings rather than its load;
- **raise `requests.memory`** to above the real footprint (≥`1.5Gi`) so the ratio means
  something;
- **`autoscaling.enabled: false` with `replicaCount: 1`**, which is what `#8` recommended
  before any of this and would have prevented it.

Note `replicaCount: 1` *is* already in `values.yaml` and does nothing: `deployment.yaml` emits
`replicas:` only when autoscaling is disabled. That is correct chart behaviour, not a bug — but
it is why "replicaCount is 1" must never be read as "there is one pod".

**#37 — OPEN. The Polaris chart's `pre-upgrade` hook runs `bitnami/kubectl:latest`, pulled
`Always`, from a catalog Bitnami retired. It is the most likely cause of a step-4 failure and
it has nothing to do with Polaris.** 2026-09-18, found by reading the step 3 render.

`polaris/templates/secret-rsa-key-hook.yaml` registers four `pre-install,pre-upgrade` objects:
ServiceAccount / Role / RoleBinding at hook-weight `-10`, then a **Job at weight `0` running
`bitnami/kubectl:latest`** that creates `polaris-rsa-key-pair-secret`. `backoffLimit: 3`.

- **No `imagePullPolicy` on that Job, and the tag is `:latest`** → Kubernetes defaults to
  `Always`, so every `helm upgrade` performs a live registry pull. The image cached on the node
  from the install 30 days ago does not help.
- **Bitnami moved its public Docker Hub catalog to `bitnamilegacy/` on 2025-08-28**, leaving
  community users "a reduced number of hardened images … published only under the `latest` tag
  and intended for development purposes". `bitnami/kubectl` went unavailable, came back, and
  upstream has left its future availability unresolved (bitnami/containers#86977).

**Failure mode is safe but misleading:** the upgrade stops at the hook with nothing changed,
and the symptom is `ImagePullBackOff` on a Job named `benchmarks-polaris-rsa-keygen` — it does
not look like a Polaris problem at all. Pre-check with `docker pull bitnami/kubectl:latest`.

**Fallback if it will not pull:** the Job's script is idempotent and self-skipping (secret
exists → `exit 0`), so with `polaris-rsa-key-pair-secret` present, `--no-hooks` changes nothing.
**Verify the secret exists first** — without it, `--no-hooks` leaves the token broker
unbootstrapped and the failure presents as an auth error, which is
`RESET-AND-CLEAN-INSTALL.md` §2.3's trap from the other side.

**CHECKED 2026-09-18: it pulls.** `Status: Image is up to date for bitnami/kubectl:latest`,
digest **`sha256:b29d8c1665b70817259ceecaea16ab27aab6368b48daf485d19436c809067492`**. So step 4
was cleared to run with hooks. **Record that digest — it is the known-good pin**, captured
while `:latest` still resolved to a working image, and it is what the fix should point at:

```yaml
image: bitnami/kubectl@sha256:b29d8c1665b70817259ceecaea16ab27aab6368b48daf485d19436c809067492
```

A digest pin also makes `imagePullPolicy: Always` harmless, since a digest cannot move.

**The fix is to pin the image, and it was NOT a step-4 decision** — the chart must not be
edited mid-upgrade. Still OPEN afterwards: this hook runs on **every** future upgrade of this
chart, so a green pull today is not a green pull next month; that is the standing fragility,
and one successful check does not close it. Related: `#2` (charts that pin no image at all).

**#38 — CLOSED 2026-09-18 by removal.** The two `QUARKUS_LOG_FILE_JSON_*` variables are deleted
from `polaris/values.yaml`, the PVC they nominally fed is deleted, and `logging.file.enabled`
stays `false` with no volume behind it. The entry's one lasting contribution is not the dead
config: it is that **`enabled: false` was silently load-bearing** — the chart's own
`logs-storage` volume mounts at the same `/deployments/logs` that `extraVolumes` claimed, so
turning the handler on would have produced a duplicate mountPath the API server rejects
outright. Nobody knew that until the mount was removed (`#44`). Original entry:

**#38 — OPEN QUESTION. The file log handler is off, so `extraEnv`'s two file-JSON variables are
inert, nothing writes the log PVC, and `#8`'s interleaved-write hazard may be inert with it.**
2026-09-18.

`logging.file.enabled: false` in `polaris/values.yaml`, and the step 3 diff shows
`quarkus.log.file.enabled=false` in **both** the live ConfigMap and the render — unchanged, so
this is the live state, not a pending one. No `QUARKUS_LOG_FILE_ENABLED` environment variable
exists to override it (the console's `QUARKUS_LOG_CONSOLE_JSON_ENABLED` trick works at ordinal
300, but there is no equivalent here). So Quarkus writes **no log file**.

Three consequences, the first settled and the others to check:

1. **Settled: `extraEnv`'s `QUARKUS_LOG_FILE_JSON_ENABLED=true` and
   `QUARKUS_LOG_FILE_JSON_PRETTY_PRINT=false` are dead config.** They configure the JSON
   formatting of a handler that is switched off. This is the **third** instance of the pattern
   in this one chart — after `logging.console.json`/`format` (inert because the env var wins,
   `#33`) and the `topologySpreadConstraints` selector matching nothing (`#8`). The pattern is
   the repo's signature fault, and it is worth counting.
2. **To check: nothing writes `/deployments/logs/polaris.log`**, although
   `polaris-shared-logs-pvc` is still mounted there via `extraVolumes`/`extraVolumeMounts`.
3. **To check: `#8`'s hazard may be inert.** `#8` is about three replicas appending to one
   `ReadWriteOnce` file with independent rotation state. With no file handler there are no
   writes to interleave. **Do not close `#8` on this** — the PVC may hold content from a period
   when file logging was on, and this says nothing about the 1 → 3 scaling itself.

Also bears on the **`fb-polaris-shipper`**, which tails that PVC into VictoriaLogs: if nothing
writes the file, the shipper tails nothing. Independent support for "Kade uninstalls the
shipper" (MEMORY.md) — and a reason to look before assuming it was ever delivering data.

**RAN 2026-09-18 — `#38` AS WRITTEN IS REFUTED. The directory is not empty; it holds a month
of log archive.** `/deployments/logs/` contains an active `polaris.log` (9594 bytes, mtime
**Sep 18 01:35**) and ~130 rotated `polaris.log.<date>.N.gz` files running back to **Aug 21**,
27 MB in total. So the file handler has been writing for at least a month. The half of this
entry that said "nothing writes the log PVC" was wrong, and the prediction that the directory
would be empty was wrong.

**What the mtimes do show, and it is the more interesting fact:** `polaris.log` was last
touched at **01:35**, the 1.6.0 pods started at **05:41**, and they served traffic at
**05:47–05:49**. So **under 1.6.0 nothing is writing the file** — which is what
`file.enabled=false` predicts. The writing stopped today, when the old pod died.

**Leading hypothesis, and it is `#20` exactly:** the step 3 diff showed
`quarkus.log.file.enabled=false` in the **R5 ConfigMap as well as the render** — unchanged. Yet
the R5 pod was writing the file. A `helm upgrade` can change a ConfigMap **without restarting
the pod**, and Polaris reads `application.properties` only at start. So R5 most likely turned
file logging off in the ConfigMap while the running pod carried on with the older config, for
days, until `2d`'s scale-to-0 finally killed it. If so, this upgrade did not disable file
logging — **it delivered a change that had been sitting inert in the ConfigMap**, which is this
repo's signature fault arriving from the opposite direction: not config that never executed,
but config that executed only when something unrelated restarted the pod.

**Settle it with two commands:**

```bash
kubectl -n datahub-hynix exec deploy/benchmarks-polaris -- env | grep -i quarkus_log
helm -n datahub-hynix get values benchmarks-polaris --revision 4   # and 3, 5 -- when did file.enabled go false?
```

**RAN 2026-09-18. The running container's environment carries exactly three `QUARKUS_LOG_*`
variables:**

```
QUARKUS_LOG_FILE_JSON_ENABLED=true
QUARKUS_LOG_FILE_JSON_PRETTY_PRINT=false
QUARKUS_LOG_CONSOLE_JSON_ENABLED=true
```

**No `QUARKUS_LOG_FILE_ENABLED`.** So nothing overrides the property at ordinal 300, and
`quarkus.log.file.enabled=false` stands: **the file handler is genuinely off on 1.6.0** and
nothing writes the PVC from here on. The two `..._FILE_JSON_...` variables are confirmed
**inert** — they format a handler that does not exist, which was this entry's one surviving
original claim.

It also leaves `#20` as the **only remaining explanation** for the month of archive: the R5 pod
must have been running a ConfigMap older than the one `0c` captured. Still not directly proven
— `helm -n datahub-hynix get values benchmarks-polaris --revision 3|4|5`, looking for when
`logging.file.enabled` went false, would close it.

**Consequence for the shipper, corrected:** `fb-polaris-shipper` has **not** been tailing an
empty file — it had real content until today. Uninstalling it now loses nothing *going
forward*, because nothing writes the file any more, but that is a different statement from the
one this entry made and the difference matters if anyone is looking for recent Polaris file
logs in VictoriaLogs.

**And a new question the archive raises — see `#40`.** The per-day suffixes run to `.14` while
`values.yaml` sets `rotation.maxBackupIndex: 5`.

**#36 — OPEN QUESTION, cheap to settle, no structural risk. The live metastore was not
bootstrapped from a file carrying v3's table comments, and `schema.sql` is the exact shape of
what it was.** 2026-09-18.

`obj_description` over `polaris_schema` after the migration: `scan_metrics_report` and
`commit_metrics_report` carry their comments (so the script that ran was post-`935c7ed` or the
shipped file — that part is confirmed good). But **all four comments v3 defines are absent** —
`version`, `entities`, `grant_records`, `principal_authentication_data`. Not a random subset:
it is exactly the set. (`events` and `policy_mapping_record` are correctly blank; v3 never
comments them.)

**No structural risk, and this is the part to read first.** Compared object by object with the
verifier's parser, `postgresql/schema/schema.sql` and `schema_v3.sql` declare the **same 10
objects, 0 differing**, both version 3. The difference between them is **24 `COMMENT ON`
statements and nothing else** — `schema.sql` has zero, `bootstrap.sql` has zero and declares no
version at all. The live database is structurally complete v3: all 21 indexes present,
including v3's `idx_entities`, `idx_locations`, `idx_policy_mapping_record` and the
`CONSTRAINT constraint_name` unique index on `entities` (an upstream naming wart, in both
files — not a defect here). So the v3 → v4 migration was applied to a correct baseline and
`#34`'s finding is unaffected.

**What is open is provenance, and there are two candidates:**

1. the metastore was bootstrapped by applying `postgresql/schema/schema.sql` by hand — it is
   *precisely* v3-minus-comments, which is *precisely* the live shape; or
2. Polaris 1.3.0 bootstrapped it from its own jar's `schema-v3.sql`, and upstream added those
   comments between 1.3.0 and 1.6.0 — the file we diffed in `#34` came from the **1.6.0** jar.

`RESET-AND-CLEAN-INSTALL.md` points at (2): it bootstraps through `bootstrapCredentials` and
`persistence.relationalJdbc` and **never applies a repo SQL file**. No chart template, values
file or script in this repo references any of the three SQL files either. But (1) matches the
observed shape exactly, so neither is settled.

**The discriminator, three commands, worth doing at the next `docker pull` and not before:**
extract `postgres/schema-v3.sql` from the **1.3.0** image and count its `COMMENT ON` lines.
24 → the database came from `schema.sql`, and `schema.sql` is load-bearing history rather than
a "local variant". 0 → upstream added them after 1.3.0, and `schema.sql` is probably a copy of
1.3.0's own v3.

**Either way, two things to fix in the docs once known:** `CLAUDE.md` calls `schema.sql` and
`bootstrap.sql` "the local variants" without saying that one of them is v3 minus comments and
may be what built this database; and `RESET-AND-CLEAN-INSTALL.md` never names a schema file, so
the next clean install cannot reproduce this one deliberately. **Do not add the four missing
comments to the live database** — they are the evidence, and cosmetic.

**#35 — OPEN. The metastore is at schema v4 and the running Polaris is 1.3.0. Upstream
documents no behaviour for a server older than its schema.** 2026-09-18.

Step 2 executed: `version_value = 4` read back from primary pg-1, nine tables in
`polaris_schema`. The chart carrying 1.6.0 is committed but **not applied** (`#33`), so until
step 3–4 run, the database is ahead of the server.

Not expected to bite, and the reason is `#34`: the v3 → v4 delta is additive-only and verified
as such against the shipped files, so every table, column, constraint and index 1.3.0 reads is
present and byte-identical. Nothing it needs moved. **The open part is whether 1.3.0 asserts
`version_value = 3` at bootstrap and refuses on 4.** Upstream's relational-JDBC docs describe
only the other direction — a newer server detecting an older schema (the v5 placeholder case) —
and otherwise say only that Polaris runs no automated migrations, so the operator owns the
ordering. No documented answer, so do not assume one.

**MEASURED 2026-09-18 — the clean case, and the question stays unanswered by design.**
`deployment 0/0`, HPA `REPLICAS 0`. No 1.3.0 pod ever came up against the v4 metastore, so
nothing exercised the combination and nothing needs to: the window is empty rather than
survived. Whether 1.3.0 asserts `version_value = 3` is therefore **still unknown, and now
unknowable without deliberately provoking it** — which is not worth doing. Recorded so a
future reader does not mistake "no incident" for "tested".

The one thing that follows for the **rollback path**: `helm rollback` to 1.3.0 alone is not
known to be sufficient from here, because the metastore would stay at v4 under a 1.3.0 server —
the untested combination. A rollback should assume the `2b` dump has to be restored with it.

**Closes when step 4 puts 1.6.0 on the cluster.** Note also that the migration's guard now
refuses a v4 database by design, so re-running it is not the way to fix anything from here.

**#34 — RESOLVED-INSTRUCTIVE. The v3 → v4 transcription is verified against the shipped
schema, and `schema_v3.sql` really is the ASF file. But the verifier's PASS was narrower than
its wording, and the gap held two real omissions.** 2026-09-18.

Three things were settled in one run, all by Kade on his machine (this session has no Docker or
cluster reach and ran none of it):

1. **The baseline. `CLAUDE.md` calls `postgresql/schema/schema_v3.sql` "the ASF-shipped file
   and the authority"; nothing had ever tested that.** `diff` against
   `/tmp/schema-v3.shipped.sql`, extracted from the 1.6.0 jar: **indentation only**, plus a
   missing trailing newline on the repo copy. No column, type, constraint, index or version
   value differs. The claim holds, and `#F1`'s mistake is not in the baseline. Everything the
   runbook concluded about the delta — which was all computed against that file — stands.
2. **The transcription. PASS.** v3 10 objects, v4 21, v4 adds 11, `migrate_v3_to_v4.sql` has
   those 11 and nothing else; the 10 shared objects are declared identically. Additive-only is
   now measured against the distribution rather than against our own copy of it, which was the
   circularity `ce72bde` was written to remove.
3. **The instructive part: a PASS on those two claims was not what it appeared to be.** Both
   claims only inspect `CREATE TABLE/INDEX/SCHEMA/VIEW`. **In the shipped v3, 26 of 36
   statements are neither** — `COMMENT ON`, `SET search_path`, the version `INSERT`. So the
   PASS line "the transcription agrees with the shipped schema" described the DDL objects, not
   the file. Checking the rest by hand found **two `COMMENT ON TABLE` statements the migration
   omitted** (shipped v4 lines 226 and 295, on `scan_metrics_report` and
   `commit_metrics_report`; `idempotency_records` has none upstream). Also confirmed absent
   from shipped v4: any `CREATE FUNCTION`/`SEQUENCE`/`TYPE`/`TRIGGER`, any `GRANT`, any
   `ALTER`, and any `INSERT` but the version row — so additive-only survives the wider look.

The two comments are cosmetic. **That is the reason to keep this entry**, not a reason to shrug
at it: the blind spot that hid two table comments would have hidden a `CREATE FUNCTION` just as
completely, and the verifier would have printed PASS either way. Both are fixed —
`migrate_v3_to_v4.sql` carries the comments, and `verify_v4_transcription.py` has a **CLAIM 3**
that compares residual statements and fails on a v4-added function, grant, alter or seed insert
the migration omits (an omitted `COMMENT ON` is a note, not a failure). Self-tested with a
round trip and two negative controls.

**The generalisation, which is this repo's recurring one:** a verifier's PASS is scoped to what
its parser can see, and that scope is rarely what the PASS line says. `verify_v4_transcription.py`
had already caught itself once this way — its first version read zero statements because an
apostrophe in a comment swallowed every semicolon. Same lesson at the level up: **ask what the
check cannot see before trusting what it says.**

**Step 2 has since RUN (2026-09-18) — `version_value = 4`, nine tables.** Not vendoring the
shipped files into the repo: the baseline diff removes the reason to, and this repo already has
a duplicate-files problem. One loose end from this entry: `\dt` lists tables only, so the 8 new
indexes were never listed — they are implied by the version write being the transaction's last
statement, and the runbook now carries a `pg_indexes` query that confirms them directly, along
with whether the two table comments made it in (absent if the script that ran predates
`935c7ed`). See `#35` for the state step 2 leaves behind.

**#33 — Polaris 1.6.0 is committed to the chart and NOT applied. The cluster still runs 1.3.0-incubating.** 2026-09-18.

`polaris/values.yaml` now pins `image.tag: "1.6.0"`, `polaris/Chart.yaml` says
`version`/`appVersion` 1.6.0, `polaris/templates/configmap.yaml` emits the plural
`polaris.event-listener.types`, all 13 DEBUG log categories are INFO and console threshold is
INFO (Kade's decision). **None of it has been rendered, linted or applied** — prepared in a
Cowork session with no `kubectl`/`helm`/`psql` reach. This is written-not-running
configuration, which in this repo is the whole game. Until step 3–5 of
[`polaris/RUNBOOK-upgrade-1.6.0.md`](../polaris/RUNBOOK-upgrade-1.6.0.md) have been run and
read back from the running object, **the running Polaris is 1.3.0 with DEBUG console output**
and the values file describes something else. Do not answer "what log level is Polaris at"
from the file.

**RETRACTION, same day.** The block below called the console-threshold discrepancy "`#5`
caught in the act". **It is not.** `helm get values` has since been run and the working tree
matched the live release on all 210 keys; the committed file lagged by one uncommitted edit
Kade had already applied at R5. See `#5`, now RESOLVED and refuted. What survives below is
correct and still matters: the threshold was already INFO, so `afc88e2`'s logging half does
not change the cluster, and the DEBUG categories were measurably inert.

**THE CONSOLE THRESHOLD WAS ALREADY INFO IN THE RUNNING RELEASE. The logging half of
`afc88e2` changes the FILE, not the cluster.** 2026-09-18, read from the live ConfigMap
`benchmarks-polaris` (revision 5, deployed 2026-09-15 17:34):

```
quarkus.log.console.level=INFO          <-- already INFO, while the committed file said DEBUG
quarkus.log.level=INFO
quarkus.log.console.enabled=true
quarkus.log.file.enabled=false
```

So the repo's `threshold: DEBUG` had not described the running Polaris since at least
revision 5. **This is `#5` caught in the act** — not a nesting error this time, just a values
file that drifted from a release nobody diffed. `afc88e2`'s logging change is a
**reconciliation of the file to reality**, not a change of behaviour, and it should be
described that way.

**And the inference about the DEBUG categories is now CONFIRMED from the running object, not
argued.** The same ConfigMap carries all ten `…level=DEBUG` category lines live —
`org.apache.polaris.service.auth`, `.service.context`, `.service.catalog`,
`.service.catalog.IcebergRestCatalogAdapter`, `.service.admin`, `core.persistence`,
`core.storage`, `.service.storage`, `DatasourceOperations`, plus `io.polaris{,.core,.service}`
— *underneath* `quarkus.log.console.level=INFO`. Quarkus takes the stricter of the two, so
**every one of them has been emitting nothing for at least three days.** Thirteen lines of
configuration, live, doing nothing.

**Consequence that must not be missed: the upgrade will NOT reduce `polaris-logs-*` volume.**
Stdout has been INFO-only since revision 5, so there is no DEBUG traffic left to remove.
Runbook step 5 originally said to expect a materially smaller window after the upgrade —
**that expectation was wrong and has been corrected.** If a window *does* shrink, something
else changed and it needs explaining, not celebrating.

**Also confirmed live, and matching the values file exactly:**
`polaris.event-listener.type=persistence-in-memory-buffer`, `buffer-time=PT5S`,
`max-buffer-size=1000`. So the plural-`types` rename in `afc88e2` is a **real** change to the
rendered config, unlike the logging half. And `quarkus.log.file.enabled=false` is live again,
which is `#11` (file logging reads as off and ships anyway) still unexplained.

**Release history:** 5 revisions, not the "ten upgrades of configuration" `#5` refers to.
R1 install 2026-08-19, R5 `deployed` 2026-09-15 17:34, chart `benchmarks-polaris-1.3.0`
throughout. The pod is 39m old against a 30d deployment with `RESTARTS 0`, so it was
**recreated** recently without a Helm revision — the running config was loaded from R5's
ConfigMap 39 minutes before the capture, not in September. Worth knowing before concluding
that a config change did or did not take (`#20`).

**THE CONSOLE IS EMITTING JSON, AND `values.yaml` SAYS IT IS NOT.** This is the inert-config
finding the threshold scare was mistaken for, and it is real. `extraEnv` carries:

```
QUARKUS_LOG_CONSOLE_JSON_ENABLED=true      # "JSON logging for Fluent Bit (Quarkus 3.29.4 new key)"
QUARKUS_LOG_FILE_JSON_ENABLED=true
QUARKUS_LOG_FILE_JSON_PRETTY_PRINT=false
```

Environment variables sit at SmallRye Config ordinal **300**; `application.properties` sits at
**250**. So the env var wins, and **`logging.console.json: false` plus the entire
`logging.console.format` string are dead configuration** — the ConfigMap dutifully renders
`quarkus.log.console.format=%d{...} %-5p [%c{2.}] (%t) [%X{requestId}] %s%e%n` and the running
Polaris ignores it. The tier-2 Lua and report schema v6 parse JSON, so the pipeline depends on
the env var, not on the two values-file keys that appear to govern it. **Anyone editing
`logging.console.format` is editing nothing.**

*Good news for the upgrade, and it is checked rather than hoped:* upstream's own 1.6.0 chart
emits `quarkus.log.console.json.enabled`, which is exactly the property
`QUARKUS_LOG_CONSOLE_JSON_ENABLED` maps to, and 1.6.0 pins **Quarkus 3.36.3** — later than the
3.29.4 the repo comment cites, same key family. So JSON console output survives 1.6.0. Confirm
from the running pod anyway; if it ever silently reverts to plain text, the entire tier-2
pipeline breaks and the report counters go quiet rather than wrong.

**THE `topologySpreadConstraints` SELECTOR MATCHES NOTHING.** In both the file and the live
release:

```
topologySpreadConstraints:
  - labelSelector:
      matchLabels:
        app.kubernetes.io/name: polaris      # <-- the label is `benchmarks-polaris`
```

The chart labels its pods `app.kubernetes.io/name: benchmarks-polaris` (`polaris.name` =
`default .Chart.Name`). So this constraint has selected zero pods for its entire life and has
never influenced scheduling. **This matters to `#8`**, whose text reasons about "a single-node
cluster with `ScheduleAnyway` spreading" — the spreading it invokes is not in effect. Same bug
class as the `=polaris` runbook selector fixed in `82525c3`; the pattern is that
`app.kubernetes.io/name` here is the *chart* name, and nothing errors when it matches nothing.
**Not changed in `afc88e2`** — it is Polaris runtime shape, and fixing it would arm a
constraint that has never run, which CLAUDE.md's Configuration Policy says to review line by
line first.

**JVM FLAGS: CHECKED, AND NOT A RISK FOR 1.6.0.** `extraEnv` sets
`GC_CONTAINER_OPTIONS=-XX:+UseZGC -XX:+ZGenerational`. `-XX:+ZGenerational` was introduced in
JDK 21, deprecated in 23, obsolete in 24 and **removed in 25** — on a JDK 25 image it is an
unrecognized VM option and the JVM refuses to start, which would present as CrashLoopBackOff
with nothing useful in the Polaris log. Polaris 1.6.0's image is
`registry.access.redhat.com/ubi9/openjdk-21-runtime` (`Dockerfile.jvm` at tag
`apache-polaris-1.6.0`), the same JDK 21 family as 1.3.0, so the flag stays valid. **Forward
watch item:** any future Polaris release that moves its base image to JDK 25 turns this env
var into a hard startup failure.

**`bootstrapCredentials` RENDERS EMPTY.** `polaris/values.yaml` has `bootstrapCredentials`
commented out while `persistence.relationalJdbc.createSecret: true`, so the rendered Secret
carries the key with no value (`bootstrapCredentials:` in the manifest) and
`POLARIS_BOOTSTRAP_CREDENTIALS` resolves to an empty string. Harmless while the metastore is
already bootstrapped; **relevant if the v3 → v4 migration ever goes wrong badly enough to
want a re-bootstrap**, because the credentials would have to be supplied at that moment. The
same manifest confirms `#9` — `password: "polaris"` in plaintext in the rendered Secret.

**`QUARKUS_DATASOURCE_JDBC_MAX_SIZE=300` per pod, MIN_SIZE 10 — this strengthens `#15`
hypothesis A.** With up to 300 Agroal connections, a write and the read that immediately
follows it are almost certainly on *different* connections, and pgpool's
`disable_load_balance_on_write = always` pins only *within* one session. So the one mechanism
that would have protected the create-then-resolve path does not cover it, and with
`delay_threshold` unset (pgpool default 0, checked nowhere) lag is never consulted before a
read is balanced onto a standby. The handoff's remedy A —
`database_redirect_preference_list = 'polaris:primary'` — addresses exactly this.

**The v4 diff is now mechanical: `postgresql/schema/verify_v4_transcription.py`.** 2026-09-18.

A plain `diff` of the shipped `schema-v4.sql` against our `migrate_v3_to_v4.sql` is useless —
the shipped file is a full schema, ours is a delta plus a guard, so they differ almost
everywhere while agreeing on everything that matters. The script checks the two claims the
transcription rests on: **(1) additive-only** — every object v3 and v4 share is declared
identically; **(2) faithful** — every object v4 adds appears in ours, normalised-identical. It
also rejects wrong declared versions, any `ALTER TABLE`, a missing transaction, and any object
ours creates that is in neither file.

**Self-tested, and the self-test mattered.** Round trip (synthetic v4 = v3 + the migration's
additive statements) → PASS; column type changed in a new table → claim 2 trips; column type
changed in a *shared* table → claim 1 trips. The first version of the script parsed **zero**
statements out of the migration: an apostrophe inside a `--` comment ("1.6.0's backend") opened
a bogus string literal and swallowed every following semicolon. It printed eleven CLAIM 2
failures, which reads exactly like a bad transcription rather than a bad parser. **A verifier
not shown to fail on a known-bad input is not evidence** — that is the lesson, and it is the
same shape as the entity-name screen whose clean result came from a broken predicate.

A PASS means three text files agree. It does not run SQL and does not predict the migration
will succeed; step 2f still reads `version_value` back from the database.

**STEP 2c ASKED A 1.3.0 POD FOR A 1.6.0 FILE.** 2026-09-18, found by Kade running it.

`kubectl exec deploy/benchmarks-polaris -- sh -c 'unzip -l /deployments/*.jar | grep schema-v'`
hung past 30s and was abandoned, correctly, under CLAUDE.md's *Timeout & Hang Guard*. **The
hang is the lesser fault.** The command could not have answered its question if it had
returned: the running pod is 1.3.0 and `schema-v4.sql` is a **1.6.0** resource. I wrote that
caveat into a parenthetical *below* the command and left the command first — which is exactly
how a step that cannot work gets run anyway. Two further faults: `unzip` is not guaranteed in a
UBI9 runtime image, and `/deployments/*.jar` is the Quarkus thin jar, with resources under
`/deployments/lib/`, so the glob is the wrong target even on a 1.6.0 pod.

Replaced with a Docker route against the 1.6.0 image — `docker create` + `docker cp
/deployments`, then `unzip` on the Mac, which has it. It reads the right image, needs nothing
installed in the container, touches no cluster object, and **pre-pulls the image the upgrade is
about to need**, which removes a cold-pull stall from step 4. OrbStack supplies the daemon.

Standing note: **do not retry the exec form.** If Docker is unavailable, skip the verification,
run the transcribed script (guarded, additive, refuses on a non-v3 database) and diff the
shipped file after the upgrade from a 1.6.0 pod, looking in `/deployments/lib/`.

**STEP 2's SQL INVOCATION WAS WRONG, AND IT BROKE A CLAUDE.md RULE.** 2026-09-18, found by
Kade running it.

The runbook's step 2e said:

```
kubectl -n datahub-hynix port-forward pod/...postgresql-1 5433:5432
psql -h localhost -p 5433 -U polaris -d polaris -f postgresql/schema/migrate_v3_to_v4.sql
```

Three faults. **`port-forward` is a blocking command** — CLAUDE.md's *Persistent Server Block*
prohibits exactly this, and in a runbook it turns a paste-able sequence into one that stops dead
at that line with no error. **It assumes a `psql` on the Mac**, of unknown version. And it was
inconsistent with the `kubectl exec -i … env PGPASSWORD=polaris psql` pattern that had already
been proven to work in step 0c and step 1 — I had the working pattern in front of me and wrote a
different one for the step that mutates the database.

Every SQL step in the runbook and the migration script's own header now use
`kubectl exec -i …` with the statements on stdin. **`-i`, never `-it`:** a TTY adds carriage
returns and can corrupt piped SQL. `PGPASSWORD` must be passed or psql prompts and the exec
hangs with no output. Step 5's `curl` health check had the same port-forward fault and is now an
`exec`, with the note that a pod reporting `READY 1/1` has already passed its readiness probe.

Note CLAUDE.md's *Direct PostgreSQL* line does give `port-forward` — that is for an interactive
session a human drives, not for scripted runbook steps. The rule and the example are not in
conflict; I read the example as licence and skipped the rule.

**STEP 1 CORRECTED: the entity-name tightening is NOT an upgrade blocker, and the first screen
asked the wrong question.** 2026-09-18.

The runbook's step 1 said 1.6.0's stricter name validation "can block the upgrade", taken from
the Snowflake 1.6 blog's *"you'll need to rename them before upgrading"*. Upstream's entities
doc is narrower and wins: **"These constraints apply to create, register, and rename operations
only. Entities predating this validation are unaffected by read or update operations."** So
existing entities do not gate the upgrade. What they break is future create/register/rename —
which still matters, because the post-upgrade `#15` ladder creates catalogs and namespaces and
`polaris-learning` phase J drives a nested namespace.

**The rule, from the doc.** A valid name: not empty; not `.` or `..` (the *whole* name); no ISO
control characters (U+0000-U+001F or U+007F-U+009F); none of `/ : * ? " < > | # +`; no leading
or trailing whitespace. Policy names stricter still: letters, digits, `-`, `_` only. **A
backslash is not forbidden** — the blog's character list is an escaping artifact.

**The screen returned 0 rows, and the screen was wrong in both directions.** Kade ran it; the
result is real for what it tested and is reassuring. But:

- `name LIKE '%.%'` flagged any name *containing* a dot, far broader than `.`/`..`. 0 rows
  there is stronger than needed, not wrong.
- `name LIKE '%\%'` was a **bug**: backslash is LIKE's default escape character, so it matched
  names ending in a literal `%`, not names containing a backslash. Backslash was covered
  anyway by the regex clause — and is not forbidden, so it never mattered.
- **`#`, `+`, the C1 range U+0080-U+009F and edge whitespace were never tested at all.**

Corrected query in the runbook's step 1, using `[[:cntrl:]]` and a `chr(128)`/`chr(159)` range
rather than backslash-u escapes. **Re-run it before the ladder.** Two lessons worth keeping:
a screen written from prose instead of the spec tests the prose, and a 0-row result is only as
good as the predicate.

**Watch backslash-u escapes in this repo's markdown.** Writing `[\u0000-\u001F]` into the
runbook produced *real* NUL / 0x1F / 0x7F / 0x9F bytes in the file, which silently killed two
edit attempts before the cause was found. Any SQL or Lua pattern committed here should use
POSIX classes or `chr()` instead.

**Step 0 progress, 2026-09-18 (Kade ran these; this session cannot):**
`0c` **DONE — the live metastore is at schema version 3**, read from primary pg-1:
`SELECT * FROM polaris_schema.version` → `version|3`. The repo's `schema_v3.sql` and the
database agree, which is now measured rather than assumed (`#F1`'s mistake avoided). So the
v3 → v4 migration is the correct one. `0b` **DONE** — one pod, `REPLICAS 1`, HPA idle at `cpu: 1%/80%, memory: 30%/80%`,
`MAXPODS 3`. This killed `#15` hypothesis C and re-armed `#8` — **both reversed the same day: the HPA went to `REPLICAS 3` after step 4, so C is live again and `#8` has fired (`#39`).**
`0d` **DONE** — the live log/event-listener config, above.
**`0a` DONE — all three captures.** `helm get values` (plain and `--all`) and
`helm get manifest`, plus `helm history` (5 revisions). This closes `#5` (refuted, see above)
and is where the JSON-console, topology-selector, ZGC and pool-size findings came from.
**Step 0 is now complete.** Next is step 1, the entity-name screen — the only remaining
pre-flight that can block the upgrade.

**Two command corrections, both mine, both worth keeping:**

* The label selector is **`app.kubernetes.io/name=benchmarks-polaris`**, not `=polaris`.
  `_helpers.tpl`'s `polaris.name` is `default .Chart.Name`, and this chart's `Chart.yaml`
  `name:` is `benchmarks-polaris` — so the label follows the chart name, not the upstream
  project name. `=polaris` returns empty, silently. Fixed everywhere in the runbook and the
  roadmap assertions.
* Read the metastore by **exec'ing the primary pod directly with `env PGPASSWORD=...`**, not
  through pgpool. Through pgpool the read can be load-balanced onto a standby (the whole
  subject of `#15` hypothesis A), and without `PGPASSWORD` psql prompts and the exec hangs.

Three corrections to `polaris/HANDOFF-upgrade-1.6.0-2026-09-17.md`, all established by
reading upstream at tag `apache-polaris-1.6.0` (not from the cluster):

1. **1.6.0 requires schema v4, not v5.** `DatabaseType.java` declares latest schema version 4
   for Postgres/CockroachDB/H2. The v5 step that alters `events.catalog_id` is a **1.7.0**
   concern; on 1.6.0 that column stays `TEXT NOT NULL`. The handoff's headline risk does not
   apply to this upgrade.
2. **The v3 → v4 delta is additive only** — 3 indexes on existing tables, plus
   `idempotency_records`, `scan_metrics_report`, `commit_metrics_report` and their indexes.
   No `ALTER`, no column change, no data rewrite; `entities`, `grant_records`,
   `principal_authentication_data`, `policy_mapping_record` and `events` are byte-identical
   between our `schema_v3.sql` and upstream `schema-v4.sql`. Script:
   `postgresql/schema/migrate_v3_to_v4.sql` — transcribed from upstream, not the shipped file.
   **CHECKED against the shipped files 2026-09-18 — PASS. See `#34`.**
3. **The handoff claimed the working tree already carried `maxReplicas 3 → 1` uncommitted. It
   did not.** The only uncommitted change on 2026-09-18 was the console threshold. So `#8`
   (HPA can scale Polaris to 3 pods sharing one log PVC) is **still open and still armed**:
   `autoscaling.enabled: true`, `maxReplicas: 3`, unchanged. This also matters mid-upgrade —
   scaling the deployment to 0 for the migration may be undone by the HPA.

**New, and absent from the handoff: 1.6.0 tightened entity-name validation.** Upstream says
entities whose names contain control characters, dots, backslashes, colons and similar must be
**renamed before upgrading**. The catalogs and namespaces here were made by test ladders, so
this can block the upgrade. Screen query in the runbook, step 1 — and it is a screen written
from prose, not from 1.6.0's validation code; confirm the real character set before renaming.

**Consequence of the INFO decision, recorded so it is not rediscovered:** Quarkus applies the
stricter of category level and handler level, so while `console.threshold: INFO` no category
can emit DEBUG. `#15` and `#24` were both characterised with those DEBUG categories on.
Re-running either needs the `--set` override written out in the `categories:` comment in
`polaris/values.yaml`. The NPE stack trace itself is ERROR and survives INFO.

---

**#32 — Schema v6 + pipeline review P1/P2/P3/P4/P6/P7/P8/P11/P12: ROLLED 2026-09-16 (~16:01Z) and VERIFIED on traffic (tier 2/3).** 2026-09-16.
- **Verified from Kade's exports of window 16:02:30Z** (pod `benchmarks-fluent-bit-62klp`, report seq 4; `.scratch/readout-2026-09-16T160230Z/`):
  67 report rows, all `schema_version` 6, same row keys as the v5 window 15:01Z and **every count field equal** (access 355 / kept 200 /
  counted 155, 404 counted 100, app_dropped_404 110, errors 247 / 4, denied 104, commit_count per row). No row carries `app`, `level`,
  `_msg`; `message` only on the summary. Detail (386 docs, 16:02:07–16:02:42Z): field set exactly `@timestamp _time api_path client_ip
  exception hostName http_method http_status level loggerName mdc message response_size sequence user_principal_name` — no `_msg`,
  `app`, `stream`, `flb_tag`, thread/process fields; in-window 200 / 22 / 78; 0 stored 404, 0 parse errors, all 243 access docs with
  every parsed field and `message`, `http_status` integer. JSON doc size vs 15:01Z: access 705 → 649 B (−8 %), app 799 → 743 B (−7 %),
  report row 755 → 518 B (−31 %).
- **Not read:** P4 gate count, step2/step3/step9/step12 output, helm revision, any `k8s-logs` doc after the roll (P2/P3/P4 effects).
Original record:
Decisions (Kade, 2026-09-16): apply P1 P2 P3 P4 P6/7 P8 P11/12; keep the raw access line but **rename `_msg` → `message`**; drop `app`.
M2 measured by Kade: ~1,800 Fluent Bit self-log docs per traffic notebook run. M3: tier-1 docs with a `log` field exist. M4: shipper
exists, Kade uninstalls manually. M5/tier 1 sizing out of scope.
- **Lua** (`fluent-bit/polaris_access_log.lua`, schema **6**): reads `message`; report rows lose `app`/`level`; sentence only on summary,
  as `message`. Policy unchanged.
- **values**: tier 2 = parser → modify(Rename timestamp _time only) → **record_modifier trim (+`stream`) BEFORE the Lua** → Lua; no
  `Add app`, no `Rename message _msg`, no `Include_Tag_Key` on the tier-2 output. Tier 1: **OUTPUT 1 (`Id_Key sequence`) deleted**,
  **`Exclude_Path /var/log/containers/benchmarks-fluent-bit-*.log`**, parser filters and definitions `polaris_json` / `polaris_text` /
  `datahub_json` deleted.
- **templates** (v6 mappings): undeclared strings `text` `index:false` + `.keyword`; `message`, `exception.message` text; `client_ip` ip;
  report `message` text. step9/step12 now also compare `dynamic_templates`.
- step2: new block (trim-before-Lua order, no rename/app, one `Include_Tag_Key`, no `Id_Key`, `Exclude_Path`, no tier-1 parsers,
  3 outputs, schema constant 6). step3: absence of `threadName threadId ndc processName stream flb_tag app _msg` in `polaris-logs-*`,
  of `app level _msg` in `polaris-report-*`, no row with `message`, no `k8s-logs` doc from the Fluent Bit pod — all since pod start.
- P11: 8 scripts `git mv` to `logging/scripts/attic/`. P12: `logging/NOTE-monitoring-team-handover-2026-09-16.md`.
- **Verified off-cluster (Cowork):** LuaJIT tests v3/v4/v5/v6 + first-tick ALL PASS (the loop from `apply-lua.sh`); step11 PASS 67×34 with
  detail 200/22/78 on `084100Z` and `144400Z`; `diff-v5-v6.lua` 0 diffs on real + 200k fuzz after normalising only the intended changes
  (and 24 diffs when `schema_version` is not normalised — the harness sees reports); step2 on a stand-in render built from the values
  blocks: all PASS; step9/step12 comparers PASS against the template files; YAML/JSON valid.
- **NOT verified:** no helm render; OpenSearch acceptance of the v6 mappings (step9/step12 on the cluster); anything on traffic.
- **RESOLVED 2026-09-18, and the answer was no (`#42`):** the v6 **detail** template was never applied. `polaris-logs-2026.09.18`
  carried `client_ip=text` against the template's `ip`, which means it was still shaped by `#30`'s 7-field pre-v6 template.
  `step12` on 2026-09-18 stored v6 for the first time (11/11); **tomorrow's index is the first with v6 mappings at all.**
  **`step9` also ran 2026-09-18: PASS 42/42**, and a direct mapping query settled the report side too — `report_type` came back
  as plain dynamic `text` + `.keyword` at `ignore_above: 256` (OpenSearch's default, not the template's 1024, and with no
  `index: false`). **NEITHER v6 template had ever been stored.** They existed only in this repo from 09-16 until 09-18.
  Indices created 09-17 and 09-18 keep pre-v6 mappings for life; from 09-19 both families are v6. See `#42`.
- **Gate before the roll, for P4's Polaris text parser only** (the two JSON parsers repeat Merge_Log's JSON decode and cannot succeed
  where it failed): if `k8s-logs` holds Polaris docs with the regex's capture field `logger`, that parser did work — then restore its
  filter + definition before rolling:
  `curl -sk -u "$OS_USER:$OS_PASSWORD" "$OS_URL/k8s-logs-*/_count" -H 'Content-Type: application/json' -d '{"query":{"bool":{"filter":[{"exists":{"field":"logger"}},{"wildcard":{"kubernetes.pod_name.keyword":"benchmarks-polaris-*"}}]}}}'` → expect `"count":0`.
- **Roll (one restart):** gate → `bash fluent-bit/apply-lua.sh --no-restart` → step2 on a fresh render → `helm upgrade` → step3 →
  traffic notebook → step3 again (field checks need docs) → `step12` + `step9` (v6 mappings; shape tomorrow's indices) →
  `step10 <window_start>` → `step11`. Expect the report counts of `144400Z`/`15:01Z` (355/200/155, 404 100/110) and detail 200/22/78.
  Dashboards/queries reading `_msg`, `app`, `level` or bare string fields need the new names.

**#31 — Lua refactor (R1–R6) and the pre-first-tick counting gap: ROLLED 2026-09-16 (~15:00Z) and VERIFIED on traffic.** 2026-09-16.
- **Rolled (Kade):** `apply-lua.sh --no-restart` → step2 → `helm upgrade` → step3 (their outputs were not pasted; helm revision not
  recorded, expected 20). New pod `benchmarks-fluent-bit-qr4br`.
- **Verified from Kade's exports of window 15:01:00Z (report seq 4 on qr4br):** summary 355 / 200 / 155, `counted_404` 100,
  `app_dropped_404` 110, errors 247 / 4, denied 104, 57 resources, 4 principals, 5 app_dropped rows, schema 5 — **every count equal to the
  14:44Z (old script) and 08:41Z windows; same 67 row keys.** The only field differences vs 14:44Z are run-to-run timing and name
  lengths (`commit_ms_*`, `response_bytes` / `last_read_bytes` of listings that embed the run id), not pipeline behaviour.
  `polaris-logs-*` (386 docs, 15:00:34–15:01:13Z): in-window detail 200 / 22 / 78 (access / PolarisServiceImpl / IcebergExceptionMapper)
  = the replay prediction; all 243 access docs carry every parsed field (so the merged parser is what runs — old Lua + new config would
  have stored parse errors, new Lua + old config would have stopped the pipeline); `access_log_parse_error` 0, 404 docs 0,
  `held_orphan` 0; `http_status` is a JSON integer on all 243 (the moved `type_int_key` works, including access lines released in arrays
  with held app logs); no `threadName` / `threadId` / `ndc`.
- **Not observed:** R4 itself (the first window after the restart was not exported); step11 on this window (no tier-1 export); pod CPU.
- **Promoted (Kade's go, 2026-09-16):** candidate → `fluent-bit/polaris_access_log.lua` (sha `2fbcfa47c513f5a0`), values FILTER 2 removed +
  `http_status response_size` in FILTER 3's int list, step2 expectations, `test-first-tick.lua` in `apply-lua.sh`. Re-checked on the
  promoted file (Cowork): apply-lua.sh's test loop ALL PASS (v3/v4/v5/first-tick); step11 PASS on `084100Z` and `144400Z` (with detail);
  differential vs the pre-refactor script 0 diffs; step2's Lua and filter-block counts on the files (script 1, call 0, int-list lines 1,
  trims present).
Review: `logging/REVIEW-lua-refactor-2026-09-16.md`. Candidate: `logging/candidates/polaris_access_log.refactor.lua`.
- **The live v5 script has a real counting gap (R4):** `counts` is nil until the first report tick, so after every pod start up
  to `Interval_Sec` (5 s) of successful GETs, catalog POSTs and 404s are dropped **and** in no counter
  (`test-r4-first-tick.lua`: current script reports `access_seen` 0 for 3 lines). Every Lua change is a restart. Fixed in the
  candidate by opening the window on the first record (decision: Kade; that window stays `partial_window: "true"`).
- **R1 (Kade: merge):** the parser moves into `polaris_noise_filter`; FILTER 2 goes away (`logging/candidates/r1-values-step2.patch`).
  **Promotion order is load-bearing:** new Lua + old config = FILTER 2 fails init and all inputs stop (tier 1 too); old Lua + new
  config = every access line becomes a stored parse error. Only `apply-lua.sh --no-restart` → `helm upgrade` (one restart) is safe.
- R2 classify guard + per-window cache, R3 allocations, R5/R6 dead conditions.
- **Verified off-cluster (Cowork, LuaJIT 2.1):** tests v3/v4/v5 ALL PASS on both scripts, now fed raw `_msg` lines
  (`test-raw-access-shim.lua`). Differential current vs candidate: 0 diffs on 2,136 real tier-1 records and 300k fuzz records.
  5 mutants are all caught. step11 on `084100Z` PASS for both. Lua CPU ~5.8 → ~2.1 µs/record.
- **NOT verified:** no helm render of the patch; the C-side marshalling saving of R1 (phase 3.1); cache hit rate at 1800 s.

**#30 — `threadName` / `threadId` / `ndc` removed from `polaris-logs-*`: ROLLED as REVISION 19 (2026-09-16 23:38:14 KST) and VERIFIED on traffic.** 2026-09-16.
**PARTLY REVERSED 2026-09-18 by `#42`: `threadName` and `threadId` are shipped again (written, not applied); `ndc` stays removed.** The decision line below — "thread name and id carry no tracing value" — is what `#42` overturned; read it as the 2026-09-16 belief, not as current. Everything else here still stands, including the verification method, which `#42` inverts rather than discards.
- **Rolled (Kade):** `helm upgrade` from the committed values (`5315e0d`) → **rev 19**, 23:38:14 KST = 14:38:14Z (`helm history`:
  17 17:35:46 v5 with reloader, **18 18:07:08 = the hot-reload removal** (closes handoff task B), 19 = this). Pod `benchmarks-fluent-bit-4bxsn`.
  The Lua was NOT changed (apply-lua.sh: ConfigMap unchanged). step3: `RESULT: post-upgrade checks passed` (only the RESULT line recorded).
  **step12: PASS** — template stored and simulated 7/7 fields (no `threadId`); applies from tomorrow's index.
- **Traffic run 14:44:00Z window (readout `.scratch/readout-2026-09-16T144400Z/`, cut by Claude from Kade's Dev Tools export):**
  summary seq 13, schema 5, access 355 / kept 200 / counted 155, `counted_404` 100, `app_dropped_404` 110, errors 247/4, denied 104 —
  **identical to the 08:41Z window.** step11 on the 720 tier-1 records in the window: **PASS 67×34 for the live script AND the
  refactor candidate (`#31`).** No detail export, so the by-logger detail check did not run.
- **VERIFIED from `polaris-logs-*` (Kade's second export, 386 docs, 14:43:35–14:44:13Z, all `polaris-logs-2026.09.16`):**
  `threadName` 0, `threadId` 0, `ndc` 0 — and the earlier trims still hold (`processName`, `loggerClassName`, `processId`, `logtag`,
  `time` all 0). Remaining fields: `@timestamp _msg _time api_path app client_ip exception flb_tag hostName http_method http_status level
  loggerName mdc response_size sequence stream user_principal_name`. No 404 access doc stored. (The first export, `k8s-logs`, is tier 1
  where the fields stay by design: 870/870 carry them.)
- **step11 with detail, 14:44:00Z window:** detail 200 / 22 / 78 (access / PolarisServiceImpl / IcebergExceptionMapper) stored ==
  replay-emitted, for the live script **and** the `#31` candidate; 67×34 rows PASS for both.
Decision (Kade): thread name and id carry no tracing value; `ndc` was `""` on all 300 detail docs of readout
`084100Z`. Scope **tier 2 only** — tier 1 `k8s-logs` and the VictoriaLogs shipper keep them.
- `fluent-bit/values.yaml` FILTER 4 `polaris_field_trim`: three `Remove_key` lines (C filter, after the Lua, so
  held/orphan records are trimmed too; removing in Lua would force return code 2 on every stored record).
- `polaris-logs-template.json`: `threadId: long` dropped (re-PUT with step12; not retroactive).
- step2: three render checks. step3 section 5: `exists` count of each field on docs newer than the container
  start must be 0 (older docs in the same daily index still carry them).
- Originally written with no render; the roll above supersedes that. The R1 filter merge (`#31`) is a separate, later upgrade.

**#16 — RESOLVED-INSTRUCTIVE 2026-09-09: the double write DOES NOT HAPPEN. The reasoning was
sound and the conclusion was wrong.**

Measured: 13,796 documents carrying `sequence` over 13,797 distinct values in 30 minutes, ratio
**1.000**, and the *busiest* `sequence` buckets each hold exactly one document — a duplicate would
sort above them. `logging/scripts/step7-dedup-check.sh`.

**Why the config reasoning failed.** It was right that Fluent Bit routes a record to every matching
output, and right that both outputs match Polaris. What it could not see is that **OUTPUT 1 never
indexes anything**: Polaris emits `sequence` as a JSON integer, the OpenSearch plugin requires the
`Id_Key` value to be a *string*, and it drops the record instead (#18). So the second copy is
discarded before it reaches the index, and everything downstream of the "twice" claim goes with it:

- **counts over `k8s-logs` are NOT ~2x inflated**, and the dedup instruction this issue placed on
  `PLAN-opensearch-cutover` §7 is **void** — deduping there would have halved a count that was
  never doubled. The plan is corrected.
- the `doc_as_upsert` field-union hazard cannot occur, because no upsert is ever sent;
- `sequence`'s per-JVM reset does not matter for dedup, because nothing dedups.

**What remains true and is now `#18`'s problem:** tier 1 has no dedup at all, and never had. A
retried chunk produces duplicates via OUTPUT 2's `Generate_ID On`. The gain `Id_Key sequence` was
sold on has never once been delivered.

*Original entry follows, kept because the failure mode is the instructive part — a claim derived
correctly from configuration, never checked against the data, and cited as fact in a plan for a
month.*

**#16 (original) — The DaemonSet writes every Polaris console line to `k8s-logs` TWICE, and its
dedup key cannot dedup. OPEN (accepted for now).**

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

*2026-09-18 — HYPOTHESIS C IS DEAD for the current cluster.* The handoff gave hypothesis C
(the namespace request lands on a *different* Polaris pod than the catalog create, whose
entity cache never saw it) more weight than A or B, on the grounds that round-robin across
replicas is deterministic in a way replication lag is not, which fits 3-of-3. Runbook step 0b
settles it: **there is exactly one Polaris pod**, `REPLICAS 1` with the HPA idle at 1% CPU,
and the deployment reports `1/1`. With one pod there is no second cache to diverge from. C
cannot be the mechanism here.

Two caveats before this is treated as closed. `#15`'s evidence came from a differently-seeded
cluster (run `1788760757`), so what is settled is that C is not the mechanism *now*, not that
it never was. And the HPA is live again (`#8`, 2026-09-18) — if a future ladder run pushes
Polaris past the target, C comes back. **Pin `replicaCount` / disable autoscaling before the
post-upgrade ladder run if you want C held dead for the duration.**

> ### *2026-09-18, LATER THE SAME DAY — HYPOTHESIS C IS ALIVE AGAIN. This paragraph outlived its truth by about six hours.*
>
> **`REPLICAS 3`.** The HPA scaled Polaris to three pods within minutes of step 4, on
> **memory** (`memory: 88%/80%`) at **`cpu: 2%`** — so not from a ladder run, and not from
> load at all. See `#39`: it is arithmetic, and it will not come back down. The caveat above
> named the right risk and the wrong trigger, and the mitigation it recommended was never
> applied.
>
> **So C is back on the table for any `#15` work from now on**, and it is no longer
> conditional: three pods is the steady state until `#39` is fixed. Anything that reads
> "hypothesis C is dead" — including MEMORY.md as it stood — is stale. **Pin `replicaCount`
> and disable autoscaling before the post-upgrade ladder run**, or the run measures a
> three-cache cluster and cannot distinguish C from A.

That leaves **A** (stale reads through Pgpool — the `database_redirect_preference_list`
remedy in the handoff addresses it) and **B** (a 1.3.0 resolver/entity-cache bug, which the
1.6.0 upgrade is itself the experiment for).
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

**#5 — RESOLVED 2026-09-18, AND THE CLAIM IS REFUTED. `polaris/values.yaml` DOES describe the
running Polaris.**

`helm get values benchmarks-polaris` was finally run — the command this issue waited on since
2026-09-03. Flattened and diffed key by key against the working tree:

| comparison | result |
|---|---|
| repo working tree vs live R5 user-supplied | **identical on all 210 keys** except the 14 `afc88e2` changed |
| live user-supplied vs live computed (`--all`) | **209 of 210 identical**; the only difference is `revisionHistoryLimit: null` present in supplied and absent from computed, which is Helm coalescing a null |

Two conclusions, and the second is the structural one:

1. **The file matched the release.** The 14 differing keys are exactly `image.tag` plus the 13
   log categories from `afc88e2` — i.e. the changes made *after* the capture. Nothing else
   diverged. `logging.console.threshold` does **not** appear in the diff: the working tree said
   INFO and so did the release.
2. **There is no chart-default layer hiding anything.** `--all` adding nothing over the supplied
   values means the release was installed with the whole file, so no setting is being served
   quietly from a chart default. This is the structural fear behind `#F1` and the `postgresql:`
   nesting, and for Polaris it is now measured as absent.

**What the DEBUG-console confusion actually was.** The *committed* file said
`threshold: DEBUG` while the release ran INFO — but the *working tree* said INFO, uncommitted.
So the drift was one uncommitted edit Kade had already applied at revision 5 (2026-09-15) and
not committed, not a file describing something else. An earlier session note in `#33` called
this "`#5` caught in the act"; **that was wrong and is retracted** — it inferred file/cluster
divergence from a ConfigMap reading before the values comparison existed to check it against.

*Historical, kept because the reasoning is instructive:* filed first as "the VictoriaLogs path
has no input" (wrong — it runs), then rewritten as "the repo and the cluster disagree", which
over-reached: it said *the repo*, on evidence about *one file*. Every file it named has now
reconciled. The lesson is not "the repo is fine"; it is that **"the file is probably wrong" is
itself a claim needing evidence**, and three times running it has failed to find any.

Filed first as "the VictoriaLogs path has no input" (wrong — it runs), then rewritten as
"the repo and the cluster disagree", which over-reached: it said *the repo*, on evidence
about *one file*. The `helm get values fb-polaris-shipper` diff on 2026-09-03 settles that
half and it went the other way.

**`fluent-bit/values.yaml` is RECONCILED too, 2026-09-09.** `helm get values
benchmarks-fluent-bit` diffed key by key against the file: **zero differing keys, none present on
one side only**, and the DaemonSet's running container is
`cr.fluentbit.io/fluent/fluent-bit:3.2.2` — exactly what the file pins. So the OpenSearch outputs,
the parsers and the `kube.*` filter chain in that file are all genuinely in effect, which is what
licenses editing it. (Note `helm get metadata` reports `APP_VERSION 5.0.6`; that is the *chart's*
appVersion, not the image.) **Both Fluent Bit values files now match their releases**, and
CLAUDE.md's "neither values file matches its live release" has been corrected.

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

**#8 — RESOLVED-INSTRUCTIVE 2026-09-18. The shared log mount is gone from the running pod;
three replicas can no longer share a log file because there is no log file.**

Verified the strong way, not by reading a values file: `kubectl exec deploy/benchmarks-polaris
-- ls /deployments/logs` returns **`No such file or directory`, exit 2**. An *empty* directory
would have proven nothing — that is what a still-mounted, unwritten volume looks like, and it is
exactly the state this pipeline was in all morning.

**Correcting my own note from hours earlier in the same day:** I wrote that `#8` closes when the
PVC is deleted (runbook step 4). Wrong. The hazard was three JBoss handlers with independent
rotation state on one **mount**; removing the mount ends it regardless of whether the claim
still exists. Step 4 disposes of an unused object, which is housekeeping, not the fix. Filing the
close one step later than it happened would have left a live-looking issue describing something
already impossible.

**What this does NOT close:** `#39`, the HPA flapping on memory at 2% CPU, which is the same
`maxReplicas: 3` and is untouched by any of this. `#8` fired on 2026-09-18 (`REPLICAS 3`) before
the mount came out; that it never corrupted a log file is luck plus `#38`'s handler being off,
not design.

**Kept because the failure mode recurs:** a `ReadWriteOnce` claim does **not** serialise writers.
RWO restricts a volume to one *node*, and many pods on that node may mount it — which on a
single-node cluster is every pod. Anyone reading "ReadWriteOnce" as "one writer" will build this
again. Original entry:
`autoscaling.enabled: true`, `maxReplicas: 3` at 80% CPU — and every replica mounts
`polaris-shared-logs-pvc` and appends to the same `/deployments/logs/polaris.log`.
`ReadWriteOnce` does **not** prevent this: RWO allows many pods on the *same node*, and this
is a single-node cluster with `ScheduleAnyway` spreading. Two JBoss file handlers with
independent descriptors and independent rotation state on one file means interleaved records,
and a rotation by one pod pulling the file out from under the other and from under the
shipper's inode. Unbitten only because nothing has pushed Polaris past 80% CPU. Fix: pin
`replicaCount` and disable autoscaling while the shared-file design stands, or give each pod
its own filename and let the shipper glob.

**FIRED 2026-09-18, minutes after step 4: `REPLICAS 3` — then 2 within the hour.** The
prediction was right. It scaled on **memory at 2% CPU**, which is JVM heap behaviour and not
load (`#39`), and it **flaps** rather than sticking. So the replica count now moves on its own,
which is what matters for `#15` hypothesis C.

**Two corrections to what was written here earlier today, both mine:**

- I called the shared-log-file hazard **inert** on the strength of `file.enabled=false`.
  **`#38` is refuted** — the PVC holds a month of rotated archive and an active `polaris.log`
  written until 01:35 today. The handler was on for at least a month; it appears to be off only
  from this upgrade onward, and likely only because the pod finally restarted (`#20`). So this
  entry's mechanism was **live for the whole period it was filed as hypothetical**, and
  `#40` asks whether the archive already contains its fingerprints.
- "Three pods is the steady state" — no; see `#39`. It oscillates.

The fix this entry has always recommended (pin `replicaCount`, disable autoscaling) is also
`#39`'s fix.

*2026-09-09:* the HPA currently reports `cpu: <unknown>/80%, memory: <unknown>/80%` at
`REPLICAS 1`, age 21d — **no metrics, so it cannot scale at all**. That removes the hazard
from the notebook run in progress, and it is not a fix: the autoscaler has been inert for an
unknown span, and the interleaved-write hazard returns the moment metrics come back. Still OPEN.

*2026-09-18, and this retires one worry that was repeated in three documents:* the runbook's
step 2d and step 4 both warned that the HPA (`minReplicas: 1`) might undo the scale-to-0.
**It did not, and it could not.** Measured after `2d`: `deployment 0/0`, HPA `REPLICAS 0`,
`cpu: <unknown>/80%`. **A HorizontalPodAutoscaler does not scale a workload up from 0
replicas** — scaling to zero is the documented way to take a workload out of an HPA's hands,
and scaling *from* zero needs the alpha `HPAScaleToZero` feature gate, which is off on this
cluster as on any default one. `<unknown>` here is a consequence, not the 09-09 metrics
regression: there are no pods to collect metrics from. **So scale-to-0 is a safe, reversible
way to hold Polaris down for a migration**, and the warning has been corrected in the runbook.
`#8` itself is untouched and still OPEN: the hazard is the HPA going 1 → 3 once a pod is back
and CPU crosses 80%, which has nothing to do with zero.

*2026-09-18 — THE METRICS ARE BACK, so the hazard is armed again.* Measured:
`cpu: 1%/80%, memory: 30%/80%`, `MINPODS 1  MAXPODS 3  REPLICAS 1`, age 30d, one pod
(`benchmarks-polaris-777c948595-c2zzg`). The 2026-09-09 reading is superseded: the autoscaler
can scale now, it simply has no reason to — 1% CPU against an 80% target is enormous
headroom, and memory at 30% is the closer of the two. So `#8` is **armed but not firing**,
and it is not "removed by lack of metrics" any more. Unchanged in the 1.6.0 commit
(`afc88e2`) by choice: `autoscaling.enabled: true`, `maxReplicas: 3`. **This also bites
mid-upgrade** — runbook step 2d scales the deployment to 0 for the migration and the HPA
`minReplicas: 1` may scale it straight back up. Check after scaling, do not assume.

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


**#26 — Report rows are stamped by a tick that fires 3.673s late, and the matrix fires every phase
on the boundary. OPEN, LIVE, and it is the reason three gates in run `1789370776` did not mean what
they said.** 2026-09-14. Measured from the OpenSearch report + log exports, not from config:

- **The skew is constant, not erratic.** All 11 rows (`seq` 184..194) emitted at
  `window_end + 3.673s`, σ < 2ms. It cannot drift: `Interval_Sec 5` **divides** `WINDOW_SECONDS 30`,
  so the tick phase against the window grid is fixed for the life of the process. Row `[W, W+30)`
  really covers about `[W+3.7, W+33.7)`. Bounded independently to **+1.55s..+3.67s** for `seq=186`
  by its own emit timestamp — a 30s shift is arithmetically excluded.
- **The notebook lands every burst inside that dead zone.** Traffic starts 0.52–0.61s after each
  boundary and finishes within ~1s, so 100% of a phase is attributed to the previous row.
- **`{-30: 5, 0: 1}` is one rule, not two.** `lead_s` measures distance to the *label*, so it reads
  −30 for a boundary-aligned burst and ≈0 for a mid-window one. The single `0` row is `seq=185`,
  the setup burst at 07:26:16.9 — the only traffic in the run that did not start on a boundary.
  **The report's "no single offset can correct it, do not quote window-scoped gates" is withdrawn.**
- **Confirmed against the other pipeline:** `access_kept` equals the access docs in the real window
  in **7 of 7** windows, 343 == 343 total.
- **Consequences already visible:** Gate 4 `writes=1 granted=3` is two adjacent rows (3 grants at
  07:29:00.55–.61; the teardown DELETE at 07:29:31.35). Gate 4 `auth_denied=0` is **not** the
  ROLE_KINDS exemption and the 403 did **not** fall to `__errors__` — it is on the role row in the
  neighbouring report row (`auth_denied=1`). Gate 2's VOID is the same class.
- **Cheapest fix is in the notebook, not the pipeline:** start each phase ~5s past the boundary
  (> `Interval_Sec`). Re-typing the window from record times is a *design change* — the Lua refuses
  it deliberately, so a replayed record is not re-dated — and must be argued as one.

Full derivation, including the wrong turn that nearly filed this as a constant 30s shift, in
[`sessions/2026-09-14-window-skew-review.md`](sessions/2026-09-14-window-skew-review.md).

**2026-09-15 — FIX CONFIRMED by run `1789460891`; two corrections.** Bursts started +11.5s and
+6.6s past the boundary; errors per row 2 / 251 == detail docs, by label, no shift. (a) **The tick
does drift**: same pod, `seq` unbroken 440→854, offset 3.673s → 2.77s — divisibility fixes the grid,
not the timer. The `Interval_Sec + 1.5` lag is immune; a hardcoded 3.673 is not. (b) The run put
**every phase in one window**, so per-phase window gates (Gate 4's grant count on a busy role) read
the whole matrix. Downgrade to MONITOR once phases are one-per-window again.
[`sessions/2026-09-15-rerun-1789460891-review.md`](sessions/2026-09-15-rerun-1789460891-review.md).

**#27 — Policy v4 / report schema v4. CLOSED: rolled 2026-09-15, superseded by v5 (`#28`, rev 17) and the refactor (`#31`).** 2026-09-15.
*(Header corrected 2026-09-16; the body below is the original record, "WRITTEN AND NOT ROLLED" as of 2026-09-15.)*
`fluent-bit/polaris_access_log.lua` carries it (split out of `values.yaml`'s `luaScripts` the same day;
**every `helm upgrade` needs `--set-file 'luaScripts.polaris_access_log\.lua=fluent-bit/polaris_access_log.lua'`**,
or the Lua filters lose their script and the pod CrashLoops). The running pod is v3.
**2026-09-15 09:14 UTC — that happened.** The first v4 roll ran without `--set-file`:
`helm get values` showed `luaScripts: {}`, the pod logged `cannot access script
'/fluent-bit/scripts/polaris_access_log.lua'` → `filter initialization failed`, and every input
paused — **tier 1 (`k8s-logs`) stopped with it**, not only Polaris. step2 was not run on that
render; its APP_ALLOW check would have failed. Fix is the full command with the flag.
**Rolled correctly the same day (pod `benchmarks-fluent-bit-rvm49`). First run `1789463971`, exports
`…-7` (598 polaris-logs docs) / `…-8` (report `seq` 3–4 only):**
- detail is exactly the replay's prediction: 598 docs = 343 access + 180 IcebergExceptionMapper (4 ERROR)
  + 75 PolarisServiceImpl; **no dropped logger present**; `clientSecret` all `*`.
- `schema_version 4`; `app_dropped` rows present (seq 4: 7+4+4+4+2 = `app_dropped_total` 21).
- seq 3 / 4: `access_kept` 6 / 39 == detail docs between tick emits (18:19:01.765–31.765–01.769 KST);
  errors 2 / 0 match; resource == principal == access lines (8, 76); management writes 39 == 39 docs;
  `catalog_admin` + `_shared` writes 1 + 25 == 26 `Adding grant` lines. No zero rows without commits.
- Commit-only rows (3 in seq 4) are **creates** (`POST …/tables`, `…/views` keys to the collection, the
  commit to the table) — plan gate G7 corrected; not a fault.
- New pod, new tick phase **1.765s**; the setup burst started +1.57s, so 6 lines went to seq 3.
- **NOT checked:** seq 5 (the matrix window: 298 access lines, 251 errors) was not in the export, and
  `commit_*` / `dropped` were not export columns, so their `long` mapping is unseen.
**2026-09-16 — the matrix window (seq 5) checked: ALL PASS.** Replaying its 696 raw tier-1 docs through the
repo Lua reproduces all 64 report rows with 0 mismatches over 30 fields; G1–G6, G8 and **Gate 2** pass
(`probe_tbl` 1941 == last 2xx write). v4 integers map `long`. #27 stays open only for template (#25), the
1800 revert and ISM. **2026-09-16 later: template applied (37/37), nested-namespace key PASS (run 1789535345,
one row, commit_count 2) — #27 open only for the 1800 revert and ISM.** [`sessions/2026-09-16-v4-phase0-matrix-window.md`](sessions/2026-09-16-v4-phase0-matrix-window.md). What changes when it rolls:
app-log allow-list (`IcebergExceptionMapper`, `PolarisServiceImpl`; WARN/ERROR exempt), dropped lines
counted as `report_type: app_dropped`, `commit_count/commit_ms_*` on table/view rows, zero-carry
deleted (`carried_rows` gone), clientSecret guard. `WINDOW_SECONDS` stays **30** — the 1800 revert is
still its own last step.

- **Verified off-cluster only:** v3 tests + v4 tests pass on LuaJIT and Lua 5.1 against the extracted
  script; a replay of run `1789460891`'s export keeps 598 / drops 158 exactly by logger, errors per
  window 2 / 251 as the real report, commit keys equal the real report's resource keys; every numeric
  field the Lua emits is in `type_int_key`.
- **NOT verified:** no `helm lint` / `--dry-run` render (no helm in the Cowork session);
  `step2-render-gate.sh` updated for v4 but never run against a real render. Nested-namespace `%1F`
  key never seen in real traffic. Deployed ConfigMap sha must read **`f364c89653dfe481`**
  (`step3-postupgrade.sh`).
- **Order:** roll the Lua, THEN apply `polaris-report-template.json` (#25) — it now also types the
  v4 integers as `long`.
- **After rolling, the plan's gates G1–G8** (`logging/archive/2026-09-15-PLAN-audit-allowlist.md` §5).
  Any v3 dashboard reading `carried_rows` or counting zero rows breaks by design; filter `schema_version`.

## Resolved, kept because they recur

**#29 — Tier 1 OUTPUT 2 (`opensearch.1`, `kube.*` → k8s-logs) still discards chunks under traffic, on 5.1.1. DROPPED by Kade 2026-09-16 — not diagnosed, not fixed.** 2026-09-16.
**Dropped (Kade, 2026-09-16 late: "drop #29, since task done"):** no further diagnosis is planned. The fault was never read: the
diagnosis commands' output directory `.scratch/issue29-1356Z/` came out empty, so the cause (mapping reject / 429 / buffer) is unknown
and nothing was changed. It concerns tier 1 only; the Polaris tier-2/3 pipeline was intact in every checked window. If it matters
again (e.g. phase 3.1's load test shows more drops), restart from the commands in `logging/archive/2026-09-16-HANDOFF-audit-log-next.md` §3 A.
Original record:
One chunk per traffic run, twice today, **before and after the v5 roll**, so not caused by v5:
- `1-1789535377` (05:09:37 UTC, v4 pod `rvm49`, traffic window readout `050930Z`): warn 05:09:46, 05:10:07, `cannot be retried` 05:10:45.
- `1-1789548067` (08:41:07 UTC, v5 pod, step-7 traffic window `084100Z`): warn 08:41:19, 08:41:38, `cannot be retried` 08:41:52.
`Retry_Limit 3` exhausts and the chunk is dropped. **It is not `#19`'s signature as far as step3 shows:** step3's
grep matches `cannot`, and no `cannot increase buffer` line appeared — but step3 does not print the lines that say
*why* a flush failed (`[output:opensearch:opensearch.1] http_do=… / HTTP status=…`), and OUTPUT 2 has no `Trace_Error`,
so per-item `_bulk` rejections are invisible. Candidates, none measured: a per-item mapping rejection (deterministic,
so every retry fails — fits "one chunk, all retries fail"), OpenSearch 429 under the burst, or `Buffer_Size False`
behaving differently on 5.1.1 than on 3.2.2 where `#19`'s 7 → 0 gate was taken.
**What it did not hit (measured from `.scratch/readout-2026-09-16T084100Z/tier1.json`):** the 720 Polaris tier-1 docs
in the step-7 interval have 720 distinct `sequence`, 0 duplicates, and step11 replays them to the pipeline's exact
rows — so no Polaris record in that window was lost or duplicated. Fluent Bit chunks are per tag (= per container log
file), so the dropped chunk is most likely another container's. Which one is unknown. Still real tier-1 loss.

**#28 — Policy v5 (404 counted, not stored) + Lua as its own ConfigMap: ROLLED 2026-09-16 (rev 17) and verified. Hot reload REMOVED and ROLLED the same day.** 2026-09-16.
Decisions (Kade): 404 access lines count into `errors_4xx`/`counted_404` and are not stored; the allow-listed
app lines of a 404 request are dropped too, **matched by `mdc.requestId`** (hold until the access line, 30 s
orphan timeout → stored with `held_orphan: true`). Lua ships as ConfigMap `polaris-fluent-bit-lua`
(`fluent-bit/kustomization.yaml`), mounted via `extraVolumes`, reloaded by the chart's `hotReload` sidecar;
**no `--set-file`**. Also: `/namespaces/{ns}/register` → kind `collection`.
- **Verified off-cluster only:** v3/v4/v5 Lua tests ALL PASS on LuaJIT and Lua 5.1; `kustomize build` (v5.4.3)
  output byte-identical to the file (sha `80119adc…` before the header-title fix — step3 recomputes); step2
  run against a **simulated** render built from chart 0.57.6 templates + values.yaml: all PASS. step11 replay
  of the 2026-09-16 window predicts detail 300/32/178 → 200/22/78 (access / ServiceImpl / ExceptionMapper).
- **Pre-roll re-check (2nd Cowork session, 2026-09-16), still off-cluster:** v3/v4/v5 ALL PASS again on LuaJIT
  2.1 against the committed script (sha256 `bfff86db220036c2`). Chart **source** for 0.57.6 read from
  `fluent/helm-charts` tag `fluent-bit-0.57.6` (`79fa0f4`): every v5-wiring expectation in step2 is what the
  templates emit — `--enable-hot-reload` appended to the default args, one `reloader` container
  (`ghcr.io/jimmidyson/configmap-reload:v0.15.0`, must be pullable on OrbStack) posting to
  `localhost:2020/api/v2/reload` (values' `HTTP_Server On` / `HTTP_Port 2020` satisfy it), `-volume-dir=/watch/extra-0`
  mounting `polaris-lua`, `checksum/*` annotations omitted, an empty `-luascripts` CM mounted at `/fluent-bit/scripts`.
  The reloader also watches `/watch/config`, so a Helm config change reloads rather than restarts. Still **no real
  render**: get.helm.sh, fluent.github.io and proxy.golang.org are all blocked from Cowork, so helm cannot be
  obtained or built; step2 on Kade's real render remains the first real run.
- **step3 run by Kade, 2026-09-16 (~17:2x KST): the DaemonSet is NOT on v5.** `ds/benchmarks-fluent-bit` has no
  `reloader` container and no `--enable-hot-reload` — per the 0.57.6 template source both are unconditional under
  `hotReload.enabled: true`, so the live pod template was not rendered from the committed values. ConfigMap
  `polaris-fluent-bit-lua` IS applied (sha `bfff86db220036c2` == repo). restartCount 0, and the pod log still holds
  engine lines from 05:09 UTC (before v5 was written), so the pod was not replaced either. The in-pod script sha
  (`8c1fb607…`) is unexplained — not any committed version of the Lua; possibly an exec error string (5.1.1 image
  may lack `cat`). **Cause established the same afternoon: step 5 (`helm upgrade`) was never run.** `helm history`
  tops out at **rev 16, 2026-09-15 18:18 KST, deployed, SSA** (no failed revision, so no SSA conflict);
  `get values` still has `luaScripts:`; DS volumes are `config luascripts varlog varlibdockercontainers
  etcmachineid` (no `polaris-lua`); generation 25 == observed; pod `benchmarks-fluent-bit-rvm49`, 23h, 0 restarts.
  So the running pod is v4 and the in-pod sha was of a path that does not exist (step3 mislabels that as "not synced"). Tier 1 alive (k8s-logs 22874/10m); report 20 docs/10m.
  Separately: a tier-1 chunk (tail.0 → opensearch.1, k8s-logs `kube.*`) was dropped after retries at 05:10:45 UTC.
- **ROLLED, 2026-09-16 ~17:35 KST (08:35 UTC pod start).** step2 on the **first real helm render**: all PASS
  (41 checks, including every v5-wiring expectation written against the simulated render). `helm upgrade` →
  rev 17. step3: rollout complete; containers `fluent-bit` (5.1.1) + `reloader` (configmap-reload v0.15.0), 0/0
  restarts; `--enable-hot-reload` present; ConfigMap sha `bfff86db220036c2` == repo; no error/lua/parser lines in
  the pod log; **tier 1 alive (k8s-logs 23012 docs/10m)**; polaris-report 20 docs/10m (may include pre-restart
  windows — `schema_version` 5 not yet read); polaris-logs 0/10m (idle Polaris, expected); `hot_reload_count` 0.
  The one FAIL (image) and the `????` (in-pod sha) were **step3 bugs**, fixed in the same commit: the image
  check read both containers' images; the in-pod check hashed the runtime's "cat not found" message
  (`8c1fb607ef937f3a`, identical on the v4 pod where the path did not exist) — the image is distroless. Also
  fixed: section 6 had printed "could not parse metrics" on every run ever — backslashes inside f-string
  braces are a SyntaxError before Python 3.12. **Re-run with the fixed step3: `post-upgrade checks passed`. step9:
  `PASS -- template stored and every field simulates as declared` (41 fields).**
  **step7 (Kade): step11 `PASS: 0 field mismatch(es) over 67 rows x 34 fields`** — 34 = v4's 30 + the four v5
  fields; PASS also requires the row sets and the detail-docs-by-logger counts to be equal, so the running
  pipeline reproduces the repo v5 Lua exactly on its own raw tier-1 input. **`polaris-logs-*` docs with
  `http_status: 404` since 08:36 UTC: 0.** Read by Claude from `.scratch/readout-2026-09-16T084100Z/`: window
  **08:41:00Z** (17:41 KST), `schema_version` **5**, `report_seq` 12, access_seen 355 / kept 200 / counted 155,
  errors_4xx 247, **`counted_404` 100, `app_dropped_404` 110**, app_dropped_total 155, held_orphans 0,
  held_pending 0; record span 08:41:06.56–08:41:15.14 (8.6 s ≤ 30). Detail docs: **200 / 22 / 78** (access /
  PolarisServiceImpl / IcebergExceptionMapper) — **exactly the replay prediction made before the roll**; no 404
  among detail statuses (401 59, 403 45, 204 27, 400 26, 201 17, 409 11, 422 6, 200 5, 500 4); 0 held_orphan docs.
  **So the 404 policy and the request-id drop are verified on live traffic; step 7 PASS.**
- **HOT RELOAD REMOVED — ROLLED 2026-09-16 (Kade): step3 `RESULT: post-upgrade checks passed`** — with the new
  checks that means one container (no reloader), no `--enable-hot-reload`, container start ≥ ConfigMap change,
  CM sha == repo, tier 1 receiving. Only the RESULT line was pasted: step2's output and the new revision
  number (expected 18) are not recorded. `apply-lua.sh` has still never run for real. Decision record follows.
- **Re-verified on the no-reload pod `benchmarks-fluent-bit-fjdjb` from Discover exports (`…-3.csv` detail, `…-4.csv`
  report), run `1789549828`, 18:10–18:11:30 KST, report seq 7/8/9:** seq 9 (09:11:00Z) is **identical** to the 08:41Z
  window — 355 seen / 200 kept / 155 counted (100 × 404), 247 4xx, 4 5xx, 104 denied, 57 resources, 4 principals,
  155 app lines dropped, 1,035,369 bytes; detail 200 / 22 / 78 (access / ServiceImpl / ExceptionMapper), 0 × 404
  stored. In every window: detail access docs == `access_kept` (35 / 8 / 200); resource totals == principal totals
  == access lines, bytes included (21,643 / 183,509 / 1,035,369); `app_dropped` rows sum to the summary; all 143 app
  docs join an access doc by `mdc.requestId`, no duplicate request ids. The run spans three windows (seq 7–8 are
  setup: 201s and grants). Not checkable from these CSVs: `counted_404` / `app_dropped_404` / `held_*` columns were
  not selected in Discover, and numbers export with thousands separators (`1,898`).
- **Same run from Dev Tools JSON (`polaris-summary.json` = request 2 for 09:11:00Z, 67 rows; `polaris-log.json` = 386
  polaris-logs docs 09:10:28–09:11:12Z)** — the fields the CSV lacked: `counted_404` 100, `app_dropped_404` 110,
  `held_orphans` 0, `held_pending` 0, `partial_window` `"false"` (a string), `role_keys_forced` 4, span 09:11:06.57–12.92.
  Identities hold: `access_kept` 200 = 355 − 155; `access_counted` 155 = 100 (404) + 31 read + 24 POST;
  `errors_kept` 151 = 247 + 4 − 100 (404s not kept); `app_dropped_404` outside `app_dropped_total`. Commit fields on 5
  table/view rows, incl. `probe_ns%1Fnested/…/mx_1789549828_deep` commit_count 2 (TODO 1.5 shape again). Detail: all
  numerics typed int; no duplicate `_id`; every app doc joins an access doc; `exception` is an object with a
  `frames` array of {class, method, line}; `clientSecret: *` (Polaris' own mask) on 4 docs, `secret_redacted` never
  set; held PolarisServiceImpl lines carry `@timestamp` up to 21 ms after `_time` (v5's documented behaviour).
  **Found: the Dev Tools response panel is not JSON** — multi-line strings print as triple-quoted blocks with
  re-indented continuation lines (300 `_msg` + 4 `exception.message`; 53 messages differ in whitespace, identical
  after normalising). `devtools-export.console` now says so; `logging/scripts/devtools-json-fix.py` repairs a panel copy.
- *(as written, Kade's decision 2026-09-16)* Wanted: no reloader, Lua and
  config read at start only, simple config. Choice among two: *Helm `--set-file`* (one command, chart checksum
  restarts; the 09-15 outage risk) vs **separate ConfigMap + restart** — **chosen**. Changes:
  `values.yaml` drops the `hotReload` block (chart default false → no `reloader`, no `--enable-hot-reload`, no
  empty `-luascripts` CM/mount, `checksum/config` back on the pod template — chart 0.57.6 source);
  new **`fluent-bit/apply-lua.sh`** = context guard → LuaJIT tests v3–v5 → `kubectl diff -k` (unchanged + pod
  newer than CM → nothing to do) → `apply -k` → `rollout restart` → `rollout status` → Lua load errors in the
  new pod's log → CM sha == repo (`--no-restart` for a change that also needs `helm upgrade`; `--restart` to
  force). step2 flipped (flag 0, reloader 0, `configmap-reload` 0, `luascripts` 0, `checksum/config` 1);
  step3 drops reloader/args/reload-counter checks and the meaningless in-pod file check, and adds **fluent-bit
  container `startedAt` ≥ the ConfigMap's last `managedFields` time** — the only outside evidence the process
  loaded the current script. apply-lua.sh's control flow was exercised with a mocked kubectl/luajit only.
  Runbook B/C dropped (never run, nothing measured); D becomes "tier-1 gaps across a restart".
  **Roll (Kade):** step2 on a fresh render → `helm upgrade` (no `--set-file`) → pod restarts once, 1 container
  → step3. Rollback: `helm rollback benchmarks-fluent-bit 17`. Leaves ConfigMap `polaris-fluent-bit-lua` as is.
- **NOT verified (as originally written; hot-reload items moot since its removal):** any real `helm` render (no helm in Cowork); hot reload itself; **what 5.1.1 does when a
  reloaded script is invalid** (runbook C — may stop tier 1 like #27); reload loss (runbook D); whether
  Polaris assigns `requestId` without a client header (production question — if not, 404 app lines are kept).
- **Order:** tests → `kubectl kustomize` + helm dry-run → step2 (two args) → **`kubectl apply -k fluent-bit/`
  BEFORE `helm upgrade`** (missing ConfigMap = ContainerCreating) → step3 → step9 re-apply (41 fields) →
  traffic → step10/11 → runbook B/C/D. [`logging/archive/2026-09-16-RUNBOOK-lua-hot-reload.md`](../logging/archive/2026-09-16-RUNBOOK-lua-hot-reload.md).
- **Until it rolls, #27's rule stands:** the running release is v4 and any `helm upgrade` of the *old* values
  still needs `--set-file`. After v5 is rolled, `--set-file` must NOT be used (it would re-add a luascripts key
  nobody reads, harmless, but a sign the wrong runbook is being followed).

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

**#21 — RESOLVED 2026-09-09 (REVISION 7).** *(filed as #16 by mistake — #16 was taken; renumbered.)* Cause: `multiline.parser cri` alone on the tier 2
tail; `docker, cri` fixes it. Verified on post-fix documents — 4,403/4,403 with `loggerName`, 0
with `log` — and by the `unwrap -> rename` delta moving 12.00 -> 6.97 B/rec. The ~29,800 raw
documents already in `polaris-logs-*` predate the fix, are not rewritten, and age out under the
30d policy. Mechanism unknown; measurement unambiguous. Original entry follows.

**#21 (original) — Policy v3 is INERT on tier 2: `polaris-logs-*` is storing unfiltered stdout. OPEN, LIVE.**
Measured 2026-09-09. The notebook run put **4,718 docs / 2.7 MB** into `polaris-logs-2026.09.09`
for roughly 270 requests, while the DaemonSet's own report said `access_seen 0` for the same
windows. Both are true: records traverse the chain and index fine, but **none is recognised as an
access-log line** (`loggerName ~= "io.quarkus.http.access-log"`), so every record takes the keep
path and no retention rule applies. The tier advertised as "30d, policy-v3 filtered" is currently
a firehose with a 30d retention on it, and it looks healthy — no errors, no restarts, no drop
counters. Storage grows with traffic until fixed. **Not a values-file fault**: the
`polaris_cri_unwrap` filter, `Parsers_File custom_parsers.conf` and `Time_Keep On` were each
checked and are present. **ROOT CAUSE FOUND 2026-09-09:** `polaris_stdout_json` carried
`Time_Key timestamp` / `Time_Format %Y-%m-%dT%H:%M:%S.%L%z` / `Time_Keep On` and its parse failed
on every record — measured at the filter, `records 5030 / drop 0 / add 0`, byte delta 12.00 B per
record. Those three lines are now **removed from `fluent-bit/values.yaml`, and NOT YET DEPLOYED**.
Until `helm upgrade` runs and §A's gate passes, this issue is live exactly as described.
Evidence: `sessions/2026-09-09-stdout-not-equivalent.md`; change and gate:
`logging/archive/2026-09-09-PLAN-tier2-parse-fault.md`.

**#22 — RESOLVED 2026-09-09, AND THE ORIGINAL FINDING WAS WRONG.** *(filed as #17; renumbered with #21.)* Re-measured after the
`multiline.parser` fix, one burst, matched windows: **`access_seen` 265 (stdout) == 265 (file)**
and **`access_kept` 126 == 126**. Per-window differences (+15, -17, +2) sum to zero — records fall
in adjacent 30s buckets, none is lost. Stdout carries the same access-log set as the file AND
policy v3 decides identically on both. The original "file 270, stdout 0" was taken while the CRI
unwrap was silently not parsing, so the stdout side could not count anything: **the disproof was
an artefact of `#21`, not a property of stdout.** Cutover step 7 is unblocked; `helm uninstall` of
the shipper still needs authorisation at the moment of execution and destroys the ability to
repeat this. Original entry follows.

**#22 (original, SUPERSEDED) —**
The cutover assumed Polaris stdout carries the same access-log set as the log file. Measured on
matched windows 2026-09-09: file 226 + 44 = **270**, stdout **0**. Until #16 is resolved,
`fb-polaris-shipper` and `polaris-shared-logs-pvc` are the ONLY path that recognises an access-log
record. Uninstalling the shipper — cutover step 7 — would destroy the capability, not just the
duplicate. Fallback specified in git at `fb91949`.

**#18 — `Id_Key sequence` skips every record it was meant to dedup. CLOSED 2026-09-16: the output was deleted (review P2, schema v6
roll `#32`); tier 1 keeps no dedup (option B of `PLAN-tier1-dedup`). Original: OPEN, LIVE, and it defeats
the dedup it exists for.** Pod log, 2026-09-09 05:07:
`[output:opensearch:opensearch.0] the value of sequence is not string` followed by
`skipping record with missing or unsafe Id_Key value`, repeating continuously.
`opensearch.0` is OUTPUT 1 (`Match kube.*benchmarks-polaris*`, `Id_Key sequence`,
`Write_Operation upsert`). Polaris emits `sequence` as a JSON **integer** (`"sequence":49687`);
the OpenSearch plugin requires the `Id_Key` value to be a **string** and drops the record
otherwise. So OUTPUT 1 has been indexing **nothing** — and the records survive only because
OUTPUT 2 (`Match kube.*`, `Generate_ID On`) matches the same records and indexes them with a
generated id. Net effect: the upsert-by-sequence dedup has never once operated, and a retried
chunk produces **duplicates** instead of upserts. `repository-map`/roadmap's "sequence in
particular makes a gap in ingestion visible" describes a mechanism that is not running.
Fix is `type_int_key`-style coercion to string, or `Id_Key` on a string field, or drop OUTPUT 1
and let OUTPUT 2 own the tag.

**SETTLED 2026-09-09: `#18` IS RIGHT, `#16` IS NOT.** Ratio 1.000 over 13,796 documents; the
busiest `sequence` buckets hold one document each. OUTPUT 1 indexes nothing, so the record really
is dropped rather than merely losing its `_id`, and `#16`'s double-write claim is disproved. The
contradiction as it stood is kept below.

**THIS CONTRADICTS `#16`, AND ONE OF THEM IS WRONG.** `#16` states every Polaris stdout line
exists in `k8s-logs` **twice** — both outputs match the tag — and instructs every comparison
against tier 1 to deduplicate on `sequence` first, calling an undeduplicated count "~2x wrong".
But if OUTPUT 1 skips each record for an unusable `Id_Key`, **only OUTPUT 2 ever indexes it and
there is no second copy.** `#16` was reasoned from the config; `#18` is read from the pod log.
Neither has been measured against the index, and `#18`'s "skips the record" is my reading of the
message text, not a proven drop.

**One query settles both**, and until it is run neither number should be used in a measurement:
```bash
curl -sk -u "$OS_USER:$OS_PASSWORD" -H 'Content-Type: application/json' \
  "$OS_URL/k8s-logs-*/_search?pretty" -d '{"size":0,"query":{"exists":{"field":"sequence"}},
   "aggs":{"per_seq":{"terms":{"field":"sequence","size":5},
     "aggs":{"n":{"value_count":{"field":"sequence"}}}}}}'
```
2 docs per `sequence` -> `#16` is right, `#18`'s drop reading is wrong. 1 doc -> `#18` is right and
`#16`'s 2x-inflation warning is void, along with the dedup instruction in
`PLAN-opensearch-cutover` §7.

**#19 — RESOLVED 2026-09-09 (REVISION 10).** `Buffer_Size False` on all four OpenSearch outputs.
**Gate passed against a real baseline: 7 -> 0** occurrences of
`cannot increase buffer|cannot be retried` in a 10-minute window, both windows containing a
notebook run so the load is comparable. A zero measured while idle would have proved nothing;
the 7 is what made this a gate.

**One thing this DID NOT settle, and cannot any more.** Whether the historical failures lost
records or duplicated them is now unanswerable: the fix removed the failures, so the window that
was both *loaded* and *failing* no longer exists. The dedup ratio measured after the fix, under
load — 13,737 documents over 13,737 distinct `sequence`, ratio **1.000**, busiest buckets one
document each — says the steady state is clean, which is what matters going forward. It says
nothing about what happened during the four dropped chunks on 2026-09-09. Do not cite it as
evidence those chunks did not duplicate.

*Original entry follows.*

**#19 (original) — Tier 1 is LOSING CHUNKS: the OpenSearch response exceeds the output's buffer.**
```
[warn ] [http_client] cannot increase buffer: current=512000 requested=544768 max=512000
[warn ] [output:opensearch:opensearch.1] http_do=-1 URI=/_bulk
[error] [engine] chunk '1-1788930438.635329228.flb' cannot be retried: task_id=11,
        input=tail.0 > output=opensearch.1
```
Four distinct chunks unretryable in ~90 seconds on 2026-09-09. `opensearch.1` is OUTPUT 2, the
node-wide k8s-logs sink. The `_bulk` **response** is larger than the plugin's 512000-byte read
buffer, the flush fails with `http_do=-1`, `Retry_Limit 3` exhausts, and the chunk is
**discarded**. This is unacknowledged data loss on tier 1, happening now, and it is invisible to
every gate used so far: `k8s-logs` doc counts keep rising because most chunks still succeed.
**FIX APPLIED 2026-09-09, NOT DEPLOYED:** `Buffer_Size False` on all four OpenSearch outputs.
Plan, mechanism and gate: `logging/archive/2026-09-09-PLAN-bulk-response-buffer.md`. Not a bulk-size
reduction — that treats the symptom. Not a cutover regression by evidence; no before/after
measurement exists.

**BASELINE RECORDED 2026-09-09, under load, BEFORE the fix: `7`** occurrences of
`cannot increase buffer|cannot be retried` in a 10-minute window containing a notebook run. The
fix is deployed as **REVISION 10** (ConfigMap and running process both confirmed). **The AFTER
number is not taken yet** — it requires a second notebook run so the load is comparable. Until
then `#19` is fixed-but-unverified, not fixed.

**`#18` AND `#19` COMPOSE, and it changes what `#19` costs.** The plugin cannot read the reply, so
it does not know whether the batch was indexed. If it *was*, each retry writes it again — and tier
1 has **no dedup at all** (`#18`: `Id_Key sequence` drops every record, so only OUTPUT 2 stores
anything and `Generate_ID On` mints a fresh `_id` per attempt), giving up to 3 duplicate copies per
failing chunk. If it *was not*, the records are lost when the chunk is discarded. Nothing
distinguishes the two afterwards. So `#19` is not simply data loss: it is **an unbounded mixture of
loss and duplication, under load, with no signal either way** — the duplicate-generating machine
`#16` feared, reached by a route `#16` did not propose.

**This is also why the `sequence` ratio of 1.000 does not clear it.** That window was quiet, and
these failures only occur under load. A duplicate-ratio measured while idle cannot see `#19`.
Re-measure `step7-dedup-check.sh` immediately after a notebook run, before the fix is deployed, if
a number is wanted for the record.

**#20 — A `helm upgrade` may update the ConfigMap without restarting the pod, so committed config
is not running config. SUSPECTED, not yet confirmed.** 2026-09-09: after `6dfa0d0` the filter map
shows `hb_parse_probe: null` and `_cat/indices/fb-heartbeat-*` is empty — the heartbeat blocks are
not in the running instance. Meanwhile `polaris_cri_unwrap`'s cumulative record counter went
**5,030 -> 5,009**, and cumulative counters only decrease across a process restart, so the pod
*has* restarted at some point. The fluent-bit chart does not necessarily stamp a
`checksum/config` pod annotation, and **a DaemonSet does not roll on a ConfigMap change by
itself** — so `helm upgrade` can report success while every pod keeps serving the previous config
until something else restarts it.

If true this is not a new fault, it is the explanation for an existing one: **Fault A's gate
failure (`has_logger 0` after `4788294`) would mean the fix was never running when it was
measured.** That must be settled before the fix is judged.

Split it with:
```bash
helm -n datahub-hynix history benchmarks-fluent-bit | tail -3
kubectl -n datahub-hynix get cm benchmarks-fluent-bit -o json \
  | jq -r '.data["fluent-bit.conf"]' | grep -c heartbeat
kubectl -n datahub-hynix get pods -l app.kubernetes.io/name=fluent-bit \
  -o custom-columns=NAME:.metadata.name,START:.status.startTime,RESTARTS:.status.containerStatuses[0].restartCount
```
- ConfigMap **contains** `heartbeat`, pod does not -> config deployed, pods never rolled.
  `kubectl -n datahub-hynix rollout restart ds/benchmarks-fluent-bit`.
- ConfigMap **lacks** it -> the upgrade did not run.

Durable fix either way: a `checksum/config` pod annotation so a values change always rolls the
pods, instead of "deployed" and "running" being two different facts nobody checks.

**#23 — Two documents in a post-fix window still carry a raw `log`. OPEN (low), unexplained.**
2026-09-09, `polaris-logs-*` split by time: the newest bucket is 3,575/3,575 parsed with **0** raw,
but the bucket before it holds **2 raw documents out of 4,576 — 0.04%**. Not a failure of the
`multiline.parser` fix, which is working on everything else in the same window, and far too rare to
be a parser regression.

Most likely a Polaris stdout line that **is not JSON** — a JVM or container message, or a
stack-trace fragment the multiline parser did not join — which `polaris_stdout_json` correctly
declines, leaving `log` intact via `Reserve_Data On`. That would be right behaviour, not a bug.
**Unverified**; nobody has looked at the two documents.

*A `now-30m` window does NOT find them* — tried 2026-09-09 and it returned far too many, because
30 minutes reaches back past the roll into the 29,803 pre-fix raw documents that share the index.
Do not filter by a window at all. **Sort by time descending and take the newest raw documents**,
which answers "when" and "what" at once:

```bash
curl -sk -u "$OS_USER:$OS_PASSWORD" -H 'Content-Type: application/json' \
  "$OS_URL/polaris-logs-*/_search?pretty" -d '{"size":3,
    "query":{"exists":{"field":"log"}},
    "sort":[{"@timestamp":"desc"}],
    "_source":["@timestamp","log","stream","flb_tag"]}'
```
If the newest raw document predates the roll, there are no post-fix ones and this closes itself.
If it postdates the roll, its `log` value says immediately whether it is a non-JSON line — which
would be `polaris_stdout_json` correctly declining, and right behaviour.
Worth knowing because if they are NOT stray non-JSON lines, the tier 2 parse has a rare failure
mode and the 0.04% is the only place it shows.
**#24 — Four Polaris operations answer 500 to a malformed request. OPEN, and it makes `errors_5xx`
drivable on demand.** API matrix run `1789026666`, 2026-09-10: `getToken`, `createNamespace`,
`renameTable` and `renameView` each returned **500 where the matrix targeted 400**, trace verdict
`unhandled` on all four — a throwable survived to the transport. 4 five-hundreds in 286 cells, 0
transport errors.

**2026-09-21: all four reproduce on Polaris 1.6.0.** From the `polaris-logs-2026.09.21` export
(391 detail docs, requestIds `nb-1789965827-2253-getToken-400`, `-2255-createNamespace-400`,
`-2275-renameTable-400`, `-2279-renameView-400`): four 500s, one per operation, every one an NPE
surfaced by `IcebergExceptionMapper` — `Cannot invoke "Object.equals(Object)" because "o" is null`
(getToken), `Namespace.levels() because "namespace" is null` (createNamespace), and
`TableIdentifier.namespace() because "identifier" is null` (both renames). The 1.6.0 upgrade did
not touch this. **So `errors_5xx` still cannot be read as a service-health signal without
excluding these four** — a client sending a malformed request drives it at will.

Two consequences, and the second is the useful one:

- **It widens `#15`.** That issue says Polaris 500s on the create path and reads as an NPE on
  create-then-resolve. Three of these four are not creates and one (`getToken`) is not even a
  catalog operation, so "the create path" is not the shape of the fault. What the four share is
  **malformed input on an operation whose 400 handler does not cover it**.
- **`errors_5xx` can now be exercised without cluster surgery**, which is the standing question in
  `roadmap.md` — no scaling, no HPA movement, no `503` route that invalidates the run. Four named
  operations, reachable through the API alone.

Not chased, deliberately: the run's job was coverage, and Polaris is not to be changed (`MEMORY.md`
standing). What is missing before anyone files this upstream is the **stack trace per operation**,
which `polaris-logs-*` holds in full by rule 3 (`http_status >= 400` over the run's windows, field
`exception.frames` — not `exception`).
**Stack traces now in hand (2026-09-16, run `1789549828`, window 09:11:00Z, Discover export
`opensearch_export_2026-09-16-3.csv`).** Reproduced a third time: the same four operations, 4 × 500, each with one
ERROR `IcebergExceptionMapper` "Unhandled exception returning INTERNAL_SERVER_ERROR" joined by `mdc.requestId`, all
`java.lang.NullPointerException`, top frames:
- `POST …/tables/rename` and `POST …/views/rename`: *"identifier" is null* —
  `PolarisCatalogHelpers.tableIdentifierToList:38` ← `CatalogHandler.authorizeRenameTableLikeOperationOrThrow:339`
  ← `IcebergCatalogHandler.renameTable:956` / `renameView:1135` (58 frames). A null source/destination reaches
  authorization before validation.
- `POST …/namespaces` (createNamespace): *"namespace" is null* — `IcebergCatalogHandler.createNamespace:284` (56 frames).
- `POST /api/catalog/v1/oauth/tokens` (getToken): *"o" is null* — `ImmutableCollections$Set12.contains:817` ←
  `JWTBroker.supportsGrantType:169` (42 frames): a request without `grant_type`.
Polaris 1.3.0-incubating. Enough to file upstream; not filed (Polaris is not to be changed from here).

**#25 — The report index template and the `""`-free Lua. CLOSED 2026-09-16: template applied (step9 PASS), Lua rolled.** 2026-09-10.
*(Header corrected 2026-09-16; the body keeps the original "WRITTEN AND NOT APPLIED" record and the APPLIED note.)* `logging/opensearch/polaris-report-template.json` exists in the
repo; nothing has PUT it to OpenSearch. `fluent-bit/values.yaml` no longer writes `""` for
`min/max_record_time`; the running pod still does. Until both land:
**2026-09-16 — APPLIED.** `PUT _index_template/polaris-report` acknowledged; a simulated new index maps
`min/max_record_time` as `date`. Existing indices as expected: 09.09 / 09.10 / 09.14 `text` for life; 09.15 / 09.16
already `date` by dynamic mapping (the Lua has omitted `""` since 09-10). step9's read-back was a `grep | head -20`
that showed 19 of 35 `long` fields — rewritten to compare all 37 fields. **Rerun PASS: 37/37 stored and simulated.** #25 is closed for new indices; 09.09/09.10/09.14 stay text.

- `polaris-report-2026.09.10` and every earlier index keep `min_record_time` as **`text`** — no
  range query, no date histogram, for the life of those indices. The invariant
  `max - min <= window_seconds` is still checkable client-side, because RFC3339 parses.
- **Order is load-bearing.** The Lua must be rolled *before or with* the template. With the fields
  typed `date`, a document carrying `""` is rejected **per item inside a `_bulk` that returns HTTP
  200** — the silent failure mode this pipeline has already produced twice. `ignore_malformed: true`
  is set on both fields as the backstop; it costs the field, never the document.
- Applying the template is `bash logging/scripts/step9-report-index-template.sh`, and it is **not
  retroactive** — the first correctly-mapped index is the next day's.
