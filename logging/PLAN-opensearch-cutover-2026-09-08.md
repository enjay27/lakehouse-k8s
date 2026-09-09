# PLAN v4 — the Fluent Bit change: tail Polaris **stdout**, ship to OpenSearch

**Written 2026-09-08. Plan only — `logging/fb-values.yaml` has NOT been edited.**

**Scope, narrowed by Kade 2026-09-08: this document is the Fluent Bit logic and nothing else.**
Duplicate documents are explicitly out of scope — an engineer handles them downstream. Everything
OpenSearch-side is listed in §6 and owned by someone else.

**Dropping dedup removes less than it sounds like.** Of the eleven defects found across three
review rounds, **eight are inside the Fluent Bit config** and five of those fail *silently* — a
healthy pod, clean `helm` output, and wrong or missing data. Those are §3.

---

## 1. The change in one paragraph

`fb-polaris-shipper` stops tailing the Polaris log PVC and tails the **container log** instead
(Polaris stdout, confirmed to carry access-log records). Its `http` → VictoriaLogs output is
replaced by **two `opensearch` outputs**, tag-routed: filtered logs to `polaris-logs-*`, report
rows to `polaris-report-*`. The DaemonSet release is **not touched**. Policy v3, report schema v2
and `polaris_access_log.lua` are **byte-identical** — no Lua edit anywhere in this change.

---

## 2. The config, block by block

### 2.1 `[SERVICE]` — the second `Parsers_File` line

```ini
[SERVICE]
    Flush         1
    Log_Level     info
    Parsers_File  parsers.conf
    Parsers_File  /fluent-bit/etc/conf/custom_parsers.conf   # ← NEW. §3.1
    HTTP_Server   On
    HTTP_Listen   0.0.0.0
    HTTP_Port     2020
    storage.path              /var/log/flb-storage/
    storage.sync              normal
    storage.checksum          off
    storage.max_chunks_up     64
    storage.backlog.mem_limit 32M
```

**CONFIRMED FROM THE RENDER, 2026-09-09** — this path is no longer copied from the DaemonSet on
faith, which §3.1 warned against:

- the ConfigMap `fb-polaris-shipper-fluent-bit` already carries a **`custom_parsers.conf`** key
  (it holds the chart's default `docker_no_time` parser);
- that ConfigMap is mounted at **`/fluent-bit/etc/conf`** (`volumeMounts: name: config`);
- so the file exists in the container at **`/fluent-bit/etc/conf/custom_parsers.conf`**;
- and `[SERVICE]` declares only `Parsers_File parsers.conf`, which — with the container's
  `--workdir=/fluent-bit/etc` — resolves to `/fluent-bit/etc/parsers.conf`, **the stock image
  file, not the ConfigMap one**.

**So `custom_parsers.conf` is rendered, mounted, and never read.** The chart even ships a default
parser inside it that has never once been loaded. §3.1 is not a hypothesis; it is the current state
of the deployed ConfigMap. The absolute path above is the fix.

*A detail worth noticing:* that unread default parser is
`Name docker_no_time … Time_Keep Off`. **The chart's own example carries the exact setting §3.2
says is mandatory to invert** — a worked demonstration of the trap, sitting unloaded in the file.

### 2.2 `customParsers` — new

```ini
[PARSER]
    Name        polaris_json
    Format      json
    Time_Key    timestamp
    Time_Format %Y-%m-%dT%H:%M:%S.%L%z
    Time_Keep   On                     # ← MANDATORY. §3.2
```

Copied from the DaemonSet (`fluent-bit/values.yaml:130-133`), which is a **working reference** for
this exact log format — with `Time_Keep On` added, which the DaemonSet does not need and this
pipeline does.

### 2.3 `[INPUT]` — the source moves

```ini
[INPUT]
    Name              tail
    Path              /var/log/containers/*benchmarks-polaris*.log
    Tag               polaris.logs            # was polaris.vlogs — §3.3
    multiline.parser  cri                     # §3.5
    DB                /var/log/flb-polaris-shipper.db
    DB.sync           normal
    Skip_Long_Lines   On
    Refresh_Interval  5
    Buffer_Chunk_Size 256k
    Buffer_Max_Size   10MB
    storage.type      filesystem
```

The `dummy` report tick INPUT is **unchanged** (`Tag polaris.report`, `Interval_Sec 5`).

**Volumes.** Drop the `polaris-logs` PVC volume and mount `/var/log` from the host instead:

```yaml
extraVolumes:
  - name: varlog
    hostPath: {path: /var/log}
  - name: flb-storage
    emptyDir: {sizeLimit: 2Gi}
extraVolumeMounts:
  - name: varlog
    mountPath: /var/log
```

`/var/log/containers/*.log` are symlinks into `/var/log/pods/`, both under this one mount.
**Confirm the chart renders hostPath volumes in Deployment mode** — §5 Q1.

**The DB now sits on the host path, so it survives `helm upgrade`** and the tail stops re-reading
from byte 0. With duplicates out of scope this is no longer load-bearing — it is just free, and it
keeps a `helm upgrade` from re-shipping the whole retained container log.

### 2.4 The filter chain — one addition, everything else untouched

| # | alias | change |
|---|---|---|
| **0** | `polaris_cri_unwrap` | **NEW** — extracts the Polaris JSON from CRI's `log` field |
| 1 | `polaris_key_rename` | `Match` retagged only |
| 2 | `polaris_access_log` | `Match` retagged only |
| 3 | `polaris_noise_filter` | **unchanged** (`Match polaris.*` — load-bearing, the report tick reaches this instance) |
| 4 | `polaris_field_trim` | `Match` retagged only |

```ini
[FILTER]
    Name          parser
    Alias         polaris_cri_unwrap
    Match         polaris.logs
    Key_Name      log
    Parser        polaris_json
    Reserve_Data  On
```

It must run **first** — filter 1 renames `message`/`timestamp`, which do not exist until the JSON
is unwrapped.

**No `_msg` / `_time` rename filter.** §3.4.

### 2.5 The outputs

```ini
[OUTPUT]
    Name                opensearch
    Match               polaris.logs
    Host                192.168.194.1
    Port                9200
    HTTP_User           ${OS_USER}          # §3.6
    HTTP_Passwd         ${OS_PASSWORD}
    Logstash_Format     On
    Logstash_Prefix     polaris-logs
    Logstash_DateFormat %Y.%m.%d
    Suppress_Type_Name  On
    tls                 On
    tls.verify          Off
    Generate_ID         On
    Trace_Error         On                  # §3.7
    Retry_Limit              5
    storage.total_limit_size 400M           # §3.8

[OUTPUT]
    Name                opensearch
    Match               polaris.report
    ...same, Logstash_Prefix polaris-report, storage.total_limit_size 200M
```

**No `Type` line** — `Suppress_Type_Name On` makes it dead config. **No `Time_Key` line** — §3.4.

During dual-write the existing `http` → VictoriaLogs output stays, with its
`storage.total_limit_size` reduced to **400M** (§3.8).

### 2.6 Credentials

```yaml
env:
  - name: OS_USER
    valueFrom: {secretKeyRef: {name: opensearch-shipper-credentials, key: username}}
  - name: OS_PASSWORD
    valueFrom: {secretKeyRef: {name: opensearch-shipper-credentials, key: password}}
```

The Secret is created out of band. **This invalidates the file's own header** at
`fb-values.yaml:20` — *"Install — no `--set` flags, everything is in this file"*. Update it in the
same commit.

---

## 3. The eight Fluent Bit traps — five fail silently

**3.1 `customParsers` is written to disk and never loaded.** `[SERVICE]` declares
`Parsers_File parsers.conf` and nothing else (`fb-values.yaml:644`). A parser added under
`config.customParsers` exists as a file and is silently unused — the 2026-09-03 audit found this.
**Silent:** the parser simply never applies. Confirm the chart's path from the render; the chart
versions differ from the DaemonSet's.

**3.2 `Time_Keep On` is mandatory.** A Fluent Bit parser *consumes* its time key by default.
Without it, `timestamp` is removed, filter 1's `Rename timestamp _time` no-ops, `_time` never
exists, and filter 3 — which reads `_time` at `fb-values.yaml:370` — hits
`if type(t) == "string"` and **skips without erroring**. Every summary row loses
`min_record_time`/`max_record_time` permanently. **Silent, and permanent.**

**3.3 The tag rename must include the INPUT.** `polaris.vlogs` is `Match`ed at `:708`, `:731`,
`:773` **and *defined* at `:661`**. Rename the `Match` lines alone and filters 1/2/4 stop matching,
the tier-2 output matches nothing, and **the whole log stream disappears while filter 3's
`polaris.*` keeps the report stream flowing normally** — healthy pod, reports arriving, logs gone.
**Silent.** Gate: a render grep for **zero** remaining `polaris.vlogs`.

**3.4 Two `@timestamp` keys reject every document.** With `Logstash_Format On` the plugin packs
`Time_Key` *plus* every existing key. If the record already carries `@timestamp` — which it would
if a filter renamed `_time` to it — the bulk body has **two `@timestamp` keys in one JSON object**,
which OpenSearch rejects per-item **inside a bulk that returns HTTP 200**. **Silent.**
Countermeasure: no `Time_Key` on the output and no rename filter. Keeping `_msg`/`_time` as names
also keeps the VictoriaLogs output working through dual-write — filters are per-tag, not
per-output — and keeps guide §7's field names, so only the query *language* changes downstream.
*(One `curl` first: this OpenSearch must accept a top-level `_msg`. Modern versions reject only
real metadata names — `_id`, `_index`, `_source` — and `_msg` is not one.)*

**3.5 CRI splits lines over ~16KB.** The runtime fragments long lines and `multiline.parser cri`
reassembles them. **Stack traces are the long lines** — the shipper's own tail comments say so. The
old file tail simply read them. Not silent (a bad reassembly breaks the JSON parse and the record
is tagged), but new. Gate: a record with an `exception` object and a long `_msg` arrives whole.

**3.6 An undefined `${VAR}` expands to the empty string.** `fb-values.yaml` has **no `env:` and no
`envFrom:`** today, and no Secret manifest in this repo creates the credential. Omit §2.6 and
OpenSearch returns 401, `Retry_Limit` exhausts, chunks drop — **past every gate that only greps
the render.** **Silent.**

**3.7 Fluent Bit counts a rejected document as a successful flush.** A bulk returning HTTP 200 can
carry per-item errors. The documents are gone, `Retry_Limit` never fires, and **none of
`fluentbit_output_{errors,retries,dropped}_total` increments** — exactly the health check guide
§8.1 relies on. `Trace_Error On` is the only thing that makes it visible in the pod log.

**3.8 Buffer sizing can evict the pod.** `flb-storage` is an `emptyDir` with `sizeLimit: 2Gi`
(`fb-values.yaml:23-25`). Three outputs coexist during dual-write; the existing `http` output alone
holds `1G`. **Kubelet evicts on `sizeLimit`** — at precisely the moment you are measuring. Hold
them at 400M / 400M / 200M.

---

## 4. Steps and gates

| # | step | gate |
|---|---|---|
| **1** | **DONE 2026-09-08** — OpenSearch `3.5.0` recorded; `_msg` accepted (so §2.4 stands); Secret `opensearch-shipper-credentials` created; reachability closed by §5 Q2 on the DaemonSet's own evidence | ✅ |
| **2** | Edit `fb-values.yaml`: §2.1–§2.6, keeping the `http` output | **render greps** below |
| **3** | `helm upgrade`; **read the pod log first** | no parser/Lua rejection, no crashloop; `Trace_Error` shows no per-item errors; **`polaris_access_log.lua` sha unchanged** vs the deployed ConfigMap |
| **4** | **Skip one full window**, then check | see below |
| **5** | Remove the `http` output; restore `storage.total_limit_size` | render grep `Name  *http` == 0 |
| **6** | **LAST — revert `WINDOW_SECONDS` 30→1800 and `Interval_Sec` 5→30**, and verify the pipeline at production cadence | see §4.1. Nothing else in this plan runs after it |

**Capture the BEFORE render first.** A dry-run of an *unedited* `fb-values.yaml` renders the old
VictoriaLogs config — it proves nothing about this change, and its guide-§4.7 greps all pass, which
is easy to misread as progress. Run it anyway and keep it: the diff of two renders is stronger
evidence than any count of greps.

```bash
# BEFORE — with fb-values.yaml unedited
helm upgrade --install fb-polaris-shipper fluent/fluent-bit --version 0.58.1 \
  -n datahub-hynix -f logging/fb-values.yaml --dry-run=client --debug > /tmp/render-before.txt 2>/dev/null
# ... make the step 2 edit ...
helm upgrade --install fb-polaris-shipper fluent/fluent-bit --version 0.58.1 \
  -n datahub-hynix -f logging/fb-values.yaml --dry-run=client --debug > /tmp/render-after.txt  2>/dev/null
diff /tmp/render-before.txt /tmp/render-after.txt        # ← read this, then run the greps
```

**`--dry-run=client`, not `--dry-run`** — Helm 4 deprecates the bare form (see CLAUDE.md's stack
line). Send `--debug` to `/dev/null` on stderr so the render is the file's only content.

**Render greps for step 2**, against `/tmp/render-after.txt`:

```bash
grep -c 'Parsers_File'              /tmp/render-after.txt   # 2   (3.1)
grep -c 'Time_Keep   On'            /tmp/render-after.txt   # 1   (3.2)
grep -c 'polaris\.vlogs'            /tmp/render-after.txt   # 0   (3.3)
grep -c 'Time_Key'                  /tmp/render-after.txt   # 1   (parser only, NOT the outputs — 3.4)
grep -c 'Name  *opensearch'         /tmp/render-after.txt   # 2
grep -c 'Name  *http'               /tmp/render-after.txt   # 1   (0 after step 5)
grep -c 'OS_PASSWORD'               /tmp/render-after.txt   # 2   (env + output — 3.6)
grep -c 'Trace_Error'               /tmp/render-after.txt   # 2   (3.7)
# and the UNCHANGED guide §4.7 greps: RESOURCE_PATTERNS, MGMT_PREFIX,
# 'Name              dummy' == 1, type_int_key == 2, DEDUP_MAX_KEYS == 0
```

**Step 4's checks — the ones that can come back wrong rather than clean:**

- `access_seen` on the summary row is **identical** in VictoriaLogs and OpenSearch — the report is
  generated once and fanned out, so a difference is transport, not filter.
- `max_record_time − min_record_time` ≤ `window_seconds` — proves the window is traffic, not the
  post-upgrade replay. **#14d: the first window after a `helm upgrade` is a replay; do not trust
  it.** That is why step 4 skips one.
- `http_status` answers a numeric range query — the mapping locked numeric.
- A record with `exception` and a long `_msg` arrived whole (3.5).
- `fluentbit_output_proc_records_total` for the window ≈ what landed (3.7).

---

### 4.1 Step 6 — the revert is the final verification, not cleanup

**Kade, 2026-09-09: the 30s window stays until every other step is done.** It is what makes each
verification round cost ~2 minutes instead of ~90, so reverting early would tax steps 3–5 for no
gain. Step 6 is therefore the **last** step of this change, and it is a *gate*, not tidying: it is
the only point at which the pipeline is observed at the cadence it will actually run.

Reverting earlier is also what the earlier draft got wrong by listing it beside the credential
rotation — that read as "do it soon". It is the opposite: **do it last.**

**What step 6 must prove**, at 1800/30, over at least two consecutive windows:

- a report is emitted on the **:00 / :30 wall-clock boundary**, and `report_seq` increments by
  exactly 1 across the pair — a gap means a boundary was missed at the new tick ratio;
- `window_seconds` on the row reads **1800** — the deployed Lua, not the file's intent;
- `max_record_time − min_record_time` ≤ `window_seconds` — the same replay detector as step 4,
  now over a window 60× longer;
- `access_seen` for a window is **~60× the 30s figure** for comparable traffic. A number far below
  that is the tick ratio silently dropping boundaries (`Interval_Sec 30` against a 1800s window is
  the intended 60:1; the current 5:30 is 6:1).

**Ride the one change that has been waiting on this revert:** `resources_other` /
`resources_other_distinct` into the summary `_msg`. They are in the JSON and absent from the
human-readable sentence. `shipper-v3-upgrade-runbook.md` is the procedure.

**One hygiene item the revert does not fix by itself.** Steps 3–5 write report rows into
`polaris-report-*` at 30s density (~138k/day against ~2.3k). Applying tier 3's long ISM policy
afterwards governs *deletion*, not what is already written — so the dense verification band stays
for the policy's lifetime. It is verification data, not production data: **delete the
`polaris-report-*` indices created during steps 3–5 after the revert**, and let clean ones be
created at 1800s. Cheap now, permanent if skipped.

---

## 5. Open — Fluent Bit side only

**Q1 — CLOSED 2026-09-09 from the before-render.** Chart 0.58.1 passes `extraVolumes` /
`extraVolumeMounts` straight through in Deployment mode: the rendered pod spec carries
`polaris-logs` (a PVC) and `flb-storage` (an `emptyDir`) in `volumes:`, with their mounts in
`volumeMounts:`. A `hostPath` is just another volume source and renders the same way. §2.3 stands
without waiting for step 2.

**One trap this exposed, which §2.3's snippet could walk into.** The chart has a **top-level
`volumeMounts:` value** — defaulting to `[{mountPath: /fluent-bit/etc/conf, name: config}]` — that
is *separate* from `extraVolumeMounts:`. The new hostPath mount goes in **`extraVolumeMounts`**.
Putting it in `volumeMounts` overwrites that default, unmounts the config ConfigMap, and the pod
comes up with no `fluent-bit.conf` at all.

**Q2 — CLOSED 2026-09-08, and the question was built on a false premise.** Earlier revisions of
this plan asserted that *"the DaemonSet reaches it from a host-network context, so the shipper's
reach is unproven"*. **That was never checked and it is wrong.** Neither Fluent Bit values file
sets `hostNetwork`, so the chart default (`false`) applies: the DaemonSet is an ordinary pod on the
same CNI, in the same namespace, on the same node as the shipper — and it has been shipping to
`192.168.194.1:9200` continuously. The shipper has the same egress. Corroborating: `docker ps`
shows `0.0.0.0:9200->9200/tcp`, and `192.168.194.1` appears as `client_ip` in Polaris access logs,
so the address routes both ways.

**Measured 2026-09-08**, with a denominator rather than a bare jsonpath (an empty
`{.items[*]…}` is silent about whether the field is unset or the list is empty):
`kubectl get ds -A -o custom-columns=NS:…,NAME:…,HOSTNET:.spec.template.spec.hostNetwork` returns
**`datahub-hynix / benchmarks-fluent-bit / <none>`** — the DaemonSet exists, in the namespace
CLAUDE.md claimed, with `hostNetwork` unset. **Note the Fluent Bit image carries no `curl`**, so `kubectl exec` into the shipper
cannot probe this; use a throwaway `curlimages/curl` pod if a direct test is still wanted.

*The lesson is the repo's own: a claim about the running object needed evidence about the running
object. This one shaped three revisions of a plan and cost a gate that could never have passed.*

**Q3 — nanosecond timestamps: PARTLY ANSWERED 2026-09-08.** A probe document carrying
`_time: "2026-09-08T00:00:00.123456789Z"` was **accepted** by OpenSearch 3.5.0 and dynamically
mapped as `date`. So 9 fractional digits do not fail on ingest — they are **truncated to
milliseconds**. Harmless for the Lua replay detector, which compares `_time` as a *string* on the
record and never reads the indexed date. Whether tier 2 should pin `date_nanos` instead is §6's
call, not a blocker for this change. **Still open on the Fluent Bit side:** whether the parser's
`%L` accepts 9 digits when setting the *record* timestamp — that is a render-and-test question and
a different mechanism from the one the probe exercised.

**Q4 — single-node dependency.** A Deployment tailing host logs sees only its own node. Correct
here — CLAUDE.md pins exactly one single-node OrbStack cluster — but it belongs as a **comment in
the values file**, not as an assumption in a plan.

**Not a Fluent Bit question, but it will bite the change:** #4 wants `Str0ngP@ssw0rd123!` rotated,
and `fluent-bit/values.yaml:159,183` still carries the literal. **Rotating before the DaemonSet's
copy is fixed stops node-wide collection.** Fix that first.

---

## 6. Handed off — NOT this change

Owned downstream, listed so nothing is assumed done:

- **Duplicate documents** — explicitly out of scope per Kade. This change uses `Generate_ID On`
  and makes no dedup claim.
- **Index templates and mappings** — `long` for `http_status` / `response_size` / the filter-3
  `type_int_key` fields, strings to `keyword`, `text` only for `_msg`, `date` or `date_nanos` for
  `_time`. **They must exist before the first document**, because OpenSearch locks a field's type
  on first write and a template written afterwards does nothing to the index already created.
- **ISM / retention** — `polaris-logs-*` 30d, `polaris-report-*` 365d. **Blocked on our step 6,
  and that is a hard ordering, not a preference:** the temporary 30s window stays live through
  steps 3–5 because it makes each verification round ~2 minutes instead of ~90, and it produces
  ~138k report docs/day against ~2.3k at 1800s. **Do not apply tier 3's long policy until step 6
  has landed** — and note the policy governs deletion, not what is already written, so the
  verification band must be dropped by hand (§4.1).
- **Query layer** — `.keyword` for aggregations; `_search` silently caps at 10,000 hits;
  OpenSearch returns `0.0` where LogsQL returned `NaN`, so pair every `sum` with `value_count`.
- **`k8s-logs` double-write** (#16) — the DaemonSet's two outputs both match Polaris, so tier-1
  counts are ~2x inflated and must be deduplicated on `sequence` before any comparison.
- **VictoriaLogs decommission** — destructive; separate authorisation at the moment of execution.

---

## 7. What earlier revisions of this plan got wrong

Kept because the failure mode recurs, and because six of these returned *a plausible wrong result
with no error* — now the fourth such episode in this pipeline alongside `type_int_key`, #13 and
harness bug 1.

1. **`Id_Key sequence` sold as the headline gain.** A per-JVM counter that resets on restart, with
   `doc_as_upsert` field-unioning collisions into one fictional document. Moot now that duplicates
   are out of scope, and it was never dedup.
2. **`Rename _time @timestamp` beside `Time_Key @timestamp`** — two keys, per-item rejection (3.4).
3. **Never noticed the tail does not parse `timestamp`** — every document would have been dated on
   arrival (2.2).
4. **"Filters 2 and 3 both read `_msg`."** Filter 3 reads **`_time`** (`:370`).
5. **`json_date_key` called VictoriaLogs-specific.** It is Fluent Bit injecting its own ingest
   stamp — the *same mechanism* as (2) and (3), which is why they were missed.
6. **The tag-rename checklist omitted the INPUT** (3.3).
7. **"The sharp edges are all on the query side."** Five of the eight are in this config.
8. **Dual-write was impossible as designed** — the rename filter would have broken the sink it was
   verifying against (3.4).
9. **Reconciliation scheduled on the replay window** #14d says not to trust (step 4).
10. **Three revisions assumed the log PVC was the only possible source** and never asked whether
    stdout would serve. It does — and asking deleted a Lua edit, a PVC dependency and #8's teeth.

**The countermeasure that keeps working: gate on a number that can come back wrong, not a command
that can come back clean.**

---

## What this plan does NOT authorise

`logging/fb-values.yaml` has not been edited. Steps 1–5 need explicit approval.

**NOT VERIFIED: nothing here was checked against the cluster.** This is a Cowork session with no
`kubectl`, `helm` or `docker` reach.
