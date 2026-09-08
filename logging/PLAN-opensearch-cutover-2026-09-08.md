# PLAN v3 — ship Polaris from **stdout** into the existing OpenSearch as a three-tier retention ladder

**Written 2026-09-08. Plan only — no values file has been edited. Nothing here is deployed.**

**This plan got smaller twice.** v1 was reviewed adversarially and three of its claims were false
in ways that would each have cost a run. v2 fixed those. Then Kade asked *"can I ship it from
stdout, so stdout covers all tiers?"* — and the answer removed most of the remaining machinery.
**§9 records what each version got wrong**, because the pattern matters more than the corrections.

---

## 1. The decision, as taken

Kade, 2026-09-08:

1. **VictoriaLogs is not necessary** — the existing OpenSearch (Docker on the Mac,
   `192.168.194.1:9200`) is the sink.
2. **No new Fluent Bit is to be deployed.**
3. **Three indices, three retentions.** The current index keeps its config untouched.
4. **Source everything from Polaris stdout.** The log-file PVC stops being read.

### 1.1 The retention ladder

| tier | tag → output | index | retention | contents |
|---|---|---|---|---|
| **1** | DaemonSet, `kube.*` | `k8s-logs` | **5d — UNTOUCHED** | everything, unfiltered |
| **2** | shipper, `polaris.logs` | `polaris-logs-*` | **30d** | policy v3 filtered |
| **3** | shipper, `polaris.report` | `polaris-report-*` | **365d** | report schema v2 rows |

Fluent Bit routes a record to **every** OUTPUT whose `Match` fits its tag, and each names its own
index — so a separate index is a separate mapping and a separate ISM policy.

**The ladder is the design.** Polaris lands in OpenSearch twice on purpose: cheap and short-lived
in tier 1, and the audit-relevant subset surviving to day 29 in tier 2 because the filter chose it.
This also restates #14a — policy v3 was never buying storage, tier 1's 5-day expiry is. **The
filter buys longevity:** it decides what is still there on day 29.

### 1.2 Both Fluent Bits now read the same bytes — and that is a feature

**Settled 2026-09-08 (Kade, from `k8s-logs`):** access-log records are present on stdout. The
2026-09-03 audit's *"the access log does not exist"* is superseded — #5 already records that the
lines arrive from a config source this repo still cannot account for; what is new is that they
arrive on **stdout**, not only in the file.

So tier 2 can be sourced from the container log instead of the PVC, which makes **tier 2 a provable
subset of tier 1** — joinable exactly on `sequence` + pod rather than approximately. §6's
reconciliation becomes an assertion rather than an argument.

**Present is not complete.** That query proves stdout carries *some* access-log lines, not that it
carries the same set as the file. §5 step 0 gates on the denominator; §8 Q1 keeps the PVC path as
the documented fallback if it fails.

---

## 2. What changes — the whole of it

### 2.1 The INPUT moves from the PVC to the container log

```ini
[INPUT]
    Name              tail
    Path              /var/log/containers/*benchmarks-polaris*.log
    Tag               polaris.logs            # renamed from polaris.vlogs — §8 Q2
    multiline.parser  cri                     # reassembles CRI-split lines — §4.2
    DB                /var/log/flb-polaris-shipper.db     # ← hostPath. THE point. §2.2
    DB.sync           normal
    Skip_Long_Lines   On
    Refresh_Interval  5
    storage.type      filesystem

[FILTER]
    Name          parser
    Alias         polaris_cri_unwrap
    Match         polaris.logs
    Key_Name      log                         # the CRI wrapper's payload
    Parser        polaris_file_json
    Reserve_Data  On
```

with the volume swapped from the PVC to a hostPath on `/var/log`. **No `kubernetes` filter and no
RBAC change** — the Polaris JSON already carries `hostName`, which is the pod name, so the metadata
the pipeline actually uses is already in the record.

### 2.2 The offset DB moves to a host path — and that is what deletes most of this plan

The shipper's DB lives on an `emptyDir` today, which `helm upgrade` destroys; with
`Read_from_Head true` the whole file is then re-read. The values file documents this at lines 14–22
and proposes a PVC. **The container-log path gets it for free**: the DaemonSet already keeps its DB
at `/var/log/flb_kube.db` on the host, and the same mount gives the shipper a DB that survives pod
replacement.

Consequences, and they are the reason to prefer this architecture:

- **Replay on upgrade stops.** With it goes the notebook's *"records can legitimately appear twice —
  deduplicate by `mdc.requestId`"* caveat.
- **Therefore no document-id scheme is needed.** `Generate_ID On` is adequate. v2's composed
  `_doc_id` in Lua is **dropped** — so **`polaris_access_log.lua` stays byte-identical** and the
  notebook's sha gate never re-baselines. (v2 §3.2 is retained as §8 Q1's fallback, because if the
  DB ever becomes non-persistent the replay returns.)
- **`sequence` stops being load-bearing as an identity**, so the unresolved string-vs-number
  question stops blocking anything. It still matters as a *join* key (§6).
- **First-run replay is bounded** by kubelet's rotation (default ~50Mi) rather than by the
  unbounded PVC file.

### 2.3 The timestamp — still the trap, now with a proven reference

The old tail used the stock `Parser json`, whose `Time_Key` is `time`; Polaris' field is
`timestamp`, so **nothing extracted it** and Fluent Bit's record time was *read* time. Harmless
under VictoriaLogs (`_time_field=_time` read the body); fatal under `Logstash_Format`, which dates
both `@timestamp` and the index name.

The DaemonSet already does this correctly (`fluent-bit/values.yaml:130-133`), so copy it — but two
traps remain and both fail silently:

```ini
[SERVICE]
    Parsers_File  parsers.conf
    Parsers_File  /fluent-bit/etc/conf/custom_parsers.conf   # TRAP 1

[PARSER]
    Name        polaris_file_json
    Format      json
    Time_Key    timestamp
    Time_Format %Y-%m-%dT%H:%M:%S.%L%z
    Time_Keep   On                                           # TRAP 2
```

**Trap 1 — `customParsers` is written to disk and never loaded.** `[SERVICE]` declares
`Parsers_File parsers.conf` and nothing else (`fb-values.yaml:644`); the 2026-09-03 audit found
this. The second line is not optional. Confirm the chart's path from the render, not from the
DaemonSet — the chart versions differ.

**Trap 2 — `Time_Keep On` is load-bearing.** A parser *consumes* its time key by default. Without
it, `timestamp` is removed, filter 1's `Rename timestamp _time` no-ops, `_time` never exists, and
filter 3 — which reads `_time` at `fb-values.yaml:370` — hits `if type(t) == "string"` and **skips
without erroring**. Every summary row loses `min_record_time`/`max_record_time` permanently, with
no symptom. Same silent-skip shape as `type_int_key`.

**Verify, do not assume:** `_time` is nanosecond precision (`…24.504420706Z`). Whether `%L` accepts
9 fractional digits, and whether the value needs `date` or `date_nanos`, is a render-and-test
question.

### 2.4 The two outputs

```ini
# TIER 2
[OUTPUT]
    Name                opensearch
    Match               polaris.logs
    Host                192.168.194.1
    Port                9200
    HTTP_User           ${OS_USER}          # needs env plumbing — §4.5
    HTTP_Passwd         ${OS_PASSWORD}
    Logstash_Format     On
    Logstash_Prefix     polaris-logs
    Logstash_DateFormat %Y.%m.%d
    Suppress_Type_Name  On
    tls                 On
    tls.verify          Off
    Generate_ID         On                  # §2.2 — no composed id needed
    Trace_Error         On                  # §4.1 — without this the drops are invisible
    Retry_Limit              5
    storage.total_limit_size 400M           # §4.4

# TIER 3
[OUTPUT]
    Name                opensearch
    Match               polaris.report
    ... Logstash_Prefix polaris-report      (or a rollover alias — §2.6)
    Generate_ID         On
    Trace_Error         On
    storage.total_limit_size 200M
```

**No `Time_Key` line.** With §2.3's parser, Fluent Bit's record time *is* the event time and the
plugin injects `@timestamp` itself. **Setting `Time_Key` to a name the record already carries
produces two `@timestamp` keys in one JSON object** → per-item 400 inside a bulk returning HTTP 200
(§4.1). `json_date_key false` goes away — the plugin ignores it.

### 2.5 `_msg` / `_time`: do not rename

Filter 1 renames `message → _msg` and `timestamp → _time` because **VictoriaLogs reserves those
names**. v1 proposed renaming them back; that filter would have **broken VictoriaLogs during the
dual-write window**, since filters are per-tag, not per-output — v1's verification step would have
corrupted the sink it verified against.

**Keep the names.** Dual-write works, there is one fewer filter to drop a stream, and **guide §7
keeps its field names** — only the query *language* changes, which materially shrinks the largest
chunk of doc churn. Step 0 tests that this OpenSearch accepts a top-level `_msg`; modern versions
reject only real metadata names (`_id`, `_index`, `_source`, …) and `_msg` is not one, but that is
a `curl`, not an assumption. If rejected, the rename lands in the **cutover** commit only, never in
the dual-write one.

### 2.6 Templates and retention

OpenSearch locks a field's type on first write, per index, and defaults strings to `text` +
`.keyword`. **A template written after the first write does nothing to the index already created.**

- explicit **`long`** for `http_status`, `response_size`, `sequence`, and every field in filter 3's
  `type_int_key` list — that list is the inventory, **plus `sequence`, which is in neither list**;
- `dynamic_templates` mapping strings to **`keyword`**, `text` only for `_msg`;
- `boolean` for `access_log_parse_error` — but `partial_window` is the **string** `"true"`/`"false"`
  (`fb-values.yaml:514`), so map it `keyword` or fix the Lua, deliberately either way;
- `_time` as `date` (or `date_nanos` — §2.3).

**Aggregations move to `.keyword`.** `stats by (loggerName)` becomes a terms agg on
`loggerName.keyword`; on `loggerName` itself it aggregates *analysed tokens* (`org`, `apache`,
`polaris`) and returns a plausible, completely wrong histogram.

| tier | retention mechanism |
|---|---|
| 1 | **unchanged** — already 5d, which tells us ISM is live here |
| 2 | daily index + ISM delete after 30d |
| 3 | **rollover alias** + delete after 365d — ~48 rows per window does not justify an index per day |

**A trap the ladder introduces.** Tier 3 is long-retention and **the 30s window is still live**:
~2,300 report docs/day at 1800s, ~138,000/day at 30s. Anything written at 30s density sits in the
long-lived index for a year. **Revert to 1800/30 before tier 3 gets its ISM policy** — the revert
is a prerequisite, not cleanup.

**#7 does not close here.** It is retired by the VictoriaLogs *uninstall*, not by ISM — and its
uglier half, an unauthenticated LoadBalancer serving ingest and query on 9428, goes away with the
release rather than being fixed by anything here.

---

## 3. What this deletes from the repo's risk surface

Sourcing from stdout is not a lateral move. It removes four things outright:

- **`polaris-shared-logs-pvc`** — the PVC no manifest in this repo creates (#5) — stops being a
  dependency of the pipeline.
- **#8's shared-file hazard.** Three HPA replicas appending to one file with independent rotation
  was the scariest open issue; each pod's stdout is its own file, so it does not arise. *(Polaris
  still writes the shared file — #8 is defanged for the pipeline, not fixed for Polaris.)*
- **The `emptyDir` replay** (§2.2), and with it the composed-id Lua edit and the `mdc.requestId`
  dedup caveat.
- **`Read_from_Head true` on an unbounded file** — the replay is now bounded by kubelet rotation.

**One thing it creates:** the log file keeps being written with nobody reading it, so the PVC fills.
Turning the file handler off runs straight into #11 (*it reads as off and writes anyway*). Follow-up,
not a blocker — but it should be watched, not forgotten.

---

## 4. The sharp edges

**4.1 OpenSearch can delete a document and report success.** A bulk returning HTTP 200 can carry
per-item `mapper_parsing_exception`. Fluent Bit treats the flush as successful: documents gone,
`Retry_Limit` never fires, and **none of `fluentbit_output_{errors,retries,dropped}_total`
increments** — exactly the health check guide §8.1 relies on. VictoriaLogs could not produce this
failure at all. So §2.6's mapping conflicts do not return a wrong number; **they delete the record.**
Countermeasure: `Trace_Error On`, and §6's record-count gate.

**4.2 CRI splits lines over ~16KB** into partial fragments that `multiline.parser cri` must
reassemble. **Stack traces are the long lines** — the shipper's own tail comments say so. The file
tail simply read them; this path depends on reassembly. New failure mode, and one the DaemonSet
already lives with. Gate on it: a record with an `exception` object and a long `_msg` must arrive
whole.

**4.3 `.keyword`, the 10,000-hit cap, and `sum()` on empty groups.** `_search` **stops at 10,000
hits and does not say so**, against a notebook that queries with `limit=0` — use `search_after`
with a PIT, or `_count` first and assert (guide §7.4 trap 1 in a new sink). And LogsQL returns
`NaN` on an empty `sum` (trap 5) where OpenSearch returns `0.0`, which is indistinguishable from a
real zero — **"absence is not zero"** is the guide's closing lesson and OpenSearch removes the
signal that made it visible. Pair every `sum` with `value_count`.

**4.4 Buffer sizing can evict the pod.** `flb-storage` is an `emptyDir` with `sizeLimit: 2Gi`; three
outputs coexist during dual-write. **Kubelet evicts on `sizeLimit`** — at precisely the moment you
are measuring. Hold them at 400M/400M/200M, or move the buffer to the same host path as the DB.

**4.5 `${OS_USER}` has no plumbing, and fails as a silent 401.** `fb-values.yaml` has **no `env:`
and no `envFrom:`**, and no Secret manifest in this repo creates the credential. An undefined
`${VAR}` expands to the **empty string** → 401 → `Retry_Limit` exhausts → chunks drop, past every
gate that only greps the render. Needs a `secretKeyRef` env pair and a Secret created out of band —
**which invalidates the file's own header** (`fb-values.yaml:20`, *"no `--set` flags, everything is
in this file"*). Update it in the same commit.

**Ordering hazard.** #4 wants `Str0ngP@ssw0rd123!` rotated, and `fluent-bit/values.yaml:159,183`
still carries the literal. **Rotating before the DaemonSet's copy is fixed stops node-wide
collection** — including tier 1. Fix the DaemonSet's credential handling, *then* rotate.

---

## 5. Sequencing

**Cut over before fixing the harness** — its bugs are in code that queries the sink, so fixing them
against VictoriaLogs and again against OpenSearch is the same work twice; bug 1's real fix (*derive
the summable set from the row's own numeric keys*) is sink-independent and matters more under
OpenSearch mappings. And **the 30s window is an asset** — ~2 minutes per verification run against
~90 — so use it, then revert before tier 3 goes long.

| # | step | gate |
|---|---|---|
| **0** | Denominator check: `k8s-logs` access-log count for a window (**deduped on `sequence`** — tier 1 double-writes, #16) vs the shipper report's `access_seen` for the same window. Plus: OpenSearch version; `admin` can PUT a template; a doc with a `_msg` field is accepted; `curl` 9200 **from inside a `datahub-hynix` pod** | counts equal → stdout ⊇ file, proceed. **Unequal → stop and take §8 Q1's fallback.** Everything else recorded, not assumed |
| **1** | Secret created; DaemonSet credential handling fixed; **then** rotate | tier 1 still ingesting after the rotation |
| **2** | Two index templates PUT | `GET _index_template/polaris-*` returns both; **no `polaris-*` index exists yet** |
| **3** | INPUT swap + parser fix + both outputs, **alongside** the existing http output | render greps: `Parsers_File` == 2; `Time_Keep   On` == 1; `Name  *opensearch` == 2; `Name  *http` == 1; `polaris.vlogs` == **0**; plus the unchanged guide §4.7 greps |
| **4** | `helm upgrade`; read the pod log first | no Lua rejection, no crashloop; **`polaris_access_log.lua` sha unchanged** from the deployed ConfigMap |
| **5** | **Skip one full window**, then reconcile (§6) | the first window after an upgrade is a replay, not traffic (#14d) |
| **6** | Remove the http output (+ the rename, if step 0 said `_msg` is rejected) | `Name  *http` == 0 |
| **7** | Harness + notebook collection ported to `_search` | a coverage run reproduces run `1788755035`'s arithmetic (158 / 41 / 12 / 1,186,348) **from OpenSearch** |
| **8** | Revert `WINDOW_SECONDS` 30→1800, `Interval_Sec` 5→30, riding `resources_other`/`_distinct` into the summary `_msg` | `shipper-v3-upgrade-runbook.md` |
| **9** | ISM applied — tier 3's **after** step 8 | — |
| **10** | VictoriaLogs uninstall proposed **separately** | destructive; its own authorisation |

**Why step 5 skips a window.** #14d: *"the first window after the `helm upgrade` is a replay, not
traffic… at 30s the entire replay lands in one window as a spike. Do not trust it."* v1 reconciled
immediately after the upgrade, against exactly that spike. Gate on the report's own replay
detector: `max_record_time − min_record_time` ≤ `window_seconds`.

**Step 6 is a second pod replacement**, and whatever was still disk-buffered for the http output is
discarded — VictoriaLogs' last chunks are lost at cutover. Acceptable; state it rather than
discover it.

---

## 6. The reconciliation gate — built to fail

v1's gate was built to pass: *"a **shipper** restart produces no duplicate `sequence`"* replays the
same file from the same JVM, so it collapses cleanly and tests nothing. This version tries to
falsify.

| assertion | what it can catch |
|---|---|
| **tier 2 ⊆ tier 1**, joined on `sequence` + `hostName`, tier 1 deduped | the new architecture's strongest available claim — both read the same bytes |
| `fluentbit_output_proc_records_total` for the window **equals** OpenSearch `_count` | **4.1's silent per-document drop** — the only check that sees it |
| `access_seen` on the summary row is **identical** in both sinks | the report is generated once and fanned out — a difference is transport, not filter |
| `max_record_time − min_record_time` ≤ `window_seconds` | the window is traffic, not a replay (#14d) |
| `http_status` answers a `range: {gte: 500}` query | the mapping locked numeric, not `float`/`text` |
| `stats by (loggerName)` and the `.keyword` terms agg return the **same** group set | 4.3, caught rather than assumed |
| `errors_4xx` / `auth_denied` / `bytes_total` reconcile across resource rows, principal rows and summary | the v2 self-check that passed on VictoriaLogs must still pass |
| a record with an `exception` object and a >16KB `_msg` arrives **whole** | 4.2's CRI reassembly |
| **restart the shipper**, then confirm the document count does not grow | §2.2's persistent DB — the claim that replaced the whole id scheme |

---

## 7. Documentation churn

| file | what goes stale |
|---|---|
| `logging/POLARIS-LOGGING-GUIDE.ko.md` | §2.1 flow diagram (**the source changes, not just the sink**), §2.2's two-Fluent-Bit table and its diagnostic sentence, §2.3 inventory, §4.2 volumes, §4.6 OUTPUT, **all of §5**, **all of §7**, §8.1–8.2, §9.1 |
| `CLAUDE.md` | Tech Stack — the shipper no longer tails a PVC; the `logging` namespace exception goes empty on uninstall |
| `MEMORY.md` | *Now* |
| `.memory/environments.md` | the 9428 line and the sink topology |
| `.memory/active-issues.md` | **#5** (the PVC stops being a dependency), **#8** (defanged for the pipeline), #2, #16 |
| `logging/polaris-logging-architecture-spec.md` | §7 LogsQL recipes |
| `POLARIS-API-LOG-COVERAGE-NOTEBOOK.md` | the limitations table — **5 of 8 rows change**, including the replay-duplicate caveat, which is deleted outright |
| `POLARIS-LOG-COVERAGE-V3-HANDOFF.md`, `shipper-v3-upgrade-runbook.md` | verification commands |

**Docs follow the reconciliation, not the edit.** Rewriting §7 against a query layer nobody has run
is how a guide acquires recipes that have never executed. §5 and §7 get rewritten in the step-7
commit, from queries that actually ran.

---

## 8. Open questions

**Q1 — does stdout carry the *same set* as the file?** Step 0's denominator. **Fallback if not:**
keep the PVC tail, and reinstate v2's composed `_doc_id` (`hostName/sequence/_time`, `string.format`
with `%d`, in a **separate** `luaScripts` key with `type_int_key sequence` on the filter, so
`polaris_access_log.lua` stays byte-identical). That path is fully specified in git history at
`fb91949`; it is not lost, only unpreferred.

**Q2 — the tag rename is now safe, and was not.** `polaris.vlogs` is `Match`ed in three filters
(`:708, 731, 773`) **and *defined* at the INPUT (`:661`)**, which v1's checklist omitted — renaming
the `Match` lines alone would drop the whole log stream while filter 3's `polaris.*` kept reports
flowing. v3 rewrites the INPUT anyway, so all four move together. **Verify with a render grep for
zero remaining `polaris.vlogs`**, not by reading the diff.

**Q3 — is `192.168.194.1:9200` reachable from a Deployment pod in `datahub-hynix`?** The DaemonSet
reaches it from a host-network context; the shipper does not. Step 0.

**Q4 — does the chart render hostPath volumes in Deployment mode?** The DaemonSet gets `/var/log`
by default; a Deployment needs it declared explicitly. Confirm in the render — **this is what makes
the offset DB persistent, and §2.2 rests entirely on it.**

**Q5 — is tier 1's 5-day retention ISM or a manual curator?** One `curl`; it decides tiers 2 and 3.

**Q6 — OpenSearch version.** Recorded nowhere (CLAUDE.md:19-20 — it is outside this repo).
Composable-template body shape and the ISM API path both depend on it.

**Single-node dependency.** A Deployment tailing host logs sees only its own node. Correct for this
cluster — CLAUDE.md pins exactly one single-node OrbStack cluster — but it must be a **comment in
the values file**, not an assumption in a plan.

---

## 9. What earlier versions got wrong

1. **`Id_Key sequence` sold as the headline gain** (v1). It is data loss: a per-JVM counter that
   resets on restart, with `doc_as_upsert` field-unioning the collision into one fictional document.
2. **`Rename _time @timestamp` beside `Logstash_Format` + `Time_Key @timestamp`** (v1) — two
   `@timestamp` keys in one object, rejected per-item inside an HTTP 200.
3. **Never noticed the tail does not parse Polaris' `timestamp`** (v1) — every document dated on
   arrival.
4. **"Filters 2 and 3 both read `_msg`"** (v1). Filter 3 reads **`_time`** (`:370`). Right
   conclusion, wrong constraint — and the wrong constraint would lead a later reader to rename
   `_time` early and silently zero the replay detector.
5. **`json_date_key` called "a VictoriaLogs-specific artifact"** (v1). It is Fluent Bit injecting
   its own ingest stamp — *the same mechanism* as (2) and (3). Having the one prior instance in hand
   and filing it as sink-specific is why (2) and (3) were missed.
6. **The tag-rename checklist omitted the INPUT** (v1) — following it literally drops the log stream.
7. **"The sharp edges are all on the query side"** (v1). §4.1 is a data-plane edge and the worst one.
8. **"#7 closes"** (v1). Retired by the uninstall, not by ISM.
9. **Dual-write was impossible as designed** (v1) — the rename filter would have broken the sink it
   was verifying against.
10. **Reconciliation scheduled on the replay window** #14d says not to trust (v1).
11. **Both v1 and v2 assumed the PVC file was the only possible source** and never asked whether
    stdout could serve. It can, and asking deleted a Lua edit, a PVC dependency, an `emptyDir`
    hazard and an open issue's teeth. **The cheapest question in this whole exercise was the one
    nobody asked for three revisions.**

Six of these return *a plausible wrong result with no error* — now four occurrences in this
pipeline's history alongside `type_int_key`, #13 and harness bug 1. **The countermeasure that keeps
working is the same: gate on a number that can come back wrong, not a command that can come back
clean.**

---

## What this plan does NOT authorise

No values file has been edited. Steps 0–10 need explicit approval, and step 10's
`helm uninstall vlsingle` / PVC deletion needs its own authorisation **at the moment of execution**
— approval of this plan is not approval to run it.

**NOT VERIFIED: nothing here was checked against the cluster.** This is a Cowork session with no
`kubectl`, `helm` or `docker` reach. Every claim about running state is read from the repo, its
memory tree, and what Kade reported from OpenSearch.
