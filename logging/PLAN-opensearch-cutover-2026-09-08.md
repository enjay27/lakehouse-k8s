# PLAN v2 — retire VictoriaLogs; ship the Polaris pipeline into the existing OpenSearch as a three-tier retention ladder

**Written 2026-09-08. Plan only — no values file has been edited. Nothing here is deployed.**

**v1 of this document was reviewed adversarially the same day and three of its claims were
false in ways that would each have cost a run.** §10 records what it got wrong and why, because
the failure mode is the one this repo keeps hitting and the corrections are worth more than a
clean document. Read §10 before trusting anything you remember from v1.

---

## 1. The decision, as taken

Kade, 2026-09-08:

1. **VictoriaLogs is not necessary.** The existing OpenSearch (Docker on the Mac,
   `192.168.194.1:9200`) is the sink.
2. **No new Fluent Bit is to be deployed** — "just add configs for new index in OpenSearch".
3. **Three indices, three retentions.** The current index keeps its config untouched.

`fb-polaris-shipper` is an **existing** release, so re-pointing it satisfies (2) with no new
install. It keeps its own Deployment release and values file. The DaemonSet release
(`fluent-bit/values.yaml`) is **not touched at all**.

**Folding the shipper into the DaemonSet was considered and rejected.** The DaemonSet runs
Fluent Bit **3.2.2**, the shipper **5.1.1**; merging forces a version decision underneath a Lua
chain whose failure mode (#13) was *a disabled filter that looked like success from outside*. It
would also put the report's per-instance Lua state in a per-node DaemonSet. Two releases, one sink.

### 1.1 The retention ladder — this is the design, not an implementation detail

| tier | source | tag → output | index | retention | contents |
|---|---|---|---|---|---|
| **1** | DaemonSet, Polaris **stdout** | `kube.*` | `k8s-logs` | **5d — UNTOUCHED** | everything, unfiltered |
| **2** | shipper, Polaris **log file** (PVC) | `polaris.vlogs` | `polaris-logs-*` | **30d** | policy v3 filtered |
| **3** | shipper, **dummy tick** → Lua | `polaris.report` | `polaris-report-*` | **>30d (365d proposed)** | report schema v2 rows |

**Fluent Bit routes a record to every OUTPUT whose `Match` fits its tag**, and each output names
its own index. A separate index is a separate mapping and a separate ISM policy, so tier 2 cannot
contaminate tier 1's mapping and a mistake in either cannot reach tier 3.

**The ladder retires the double-write worry that v1 raised as an open problem.** Polaris does land
in OpenSearch twice — unfiltered via console into tier 1, curated via the log file into tier 2 —
but that is now *deliberate tiering* rather than accidental overlap: the same event is cheap and
short-lived in tier 1, and the audit-relevant subset survives to day 29 in tier 2 because the
filter chose it.

**It also restates #14a correctly.** Policy v3 was never buying storage — tier 1's 5-day expiry
is what buys storage. **The filter buys longevity:** it decides what is still there on day 29.
Anyone re-reading #14a's "the filter governs 4.5% of the volume" should read it as a statement
about one tier, not about the cluster.

---

## 2. Does this change a lot, or a bit? — more than v1 claimed

v1 answered "a bit of pipeline, a lot of query layer", on the premise that **the Lua and the tail
parser are never touched**. That premise is dead: two of the three defects found in review are
fixed inside them.

| | v1 estimate | actual |
|---|---|---|
| tail INPUT parser | untouched | **a new parser + a second `Parsers_File` line** (§3.1) |
| Lua | untouched | **a new script for the document id** (§3.2) |
| OUTPUT | one block | two blocks (§3.3) |
| index templates | one | **three-tier mapping decision** (§3.5) |
| query layer | ~20 recipes + harness | unchanged, and **possibly cheaper** — see §3.4 |
| docs | ~40% of the guide | unchanged |

**The honest summary: the data plane is no longer a ~40-line edit.** It is a parser change, a new
Lua script, two outputs and three templates — and each of the first two has a silent-failure mode
that has to be gated for. The query layer is the same size as before, and §3.4 may shrink it.

---

## 3. What changes in the pipeline

### 3.1 The tail parser — the shipper has never parsed Polaris' timestamp, and `Logstash_Format` makes that fatal

**The defect.** `logging/fb-values.yaml:663` — the tail INPUT uses `Parser json`, the stock
parser, whose `Time_Key` is `time`. The Polaris field is `timestamp`. **Nothing extracts it**, so
Fluent Bit's record timestamp is *read* time. #5b measured the gap directly: Fluent Bit's own
`date` landed 178µs after Quarkus' `_time` on the same event.

Under VictoriaLogs this cost nothing — the output declared `_time_field=_time`, so the event time
was read from the record body. **Under OpenSearch's `Logstash_Format`, the record timestamp drives
both the injected `@timestamp` and the daily index name.** Every document would be dated on
arrival: wrong `@timestamp`, wrong index on any replay, and no join possible against tier 1, which
dates correctly (`fluent-bit/values.yaml:130-133`).

**The fix, and its two traps.**

```ini
[SERVICE]
    Parsers_File  parsers.conf
    Parsers_File  /fluent-bit/etc/conf/custom_parsers.conf    # TRAP 1

[PARSER]
    Name        polaris_file_json
    Format      json
    Time_Key    timestamp
    Time_Format %Y-%m-%dT%H:%M:%S.%L%z
    Time_Keep   On                                            # TRAP 2

[INPUT]
    Parser      polaris_file_json     # was: json
```

**Trap 1 — `customParsers` is written to disk and never loaded.** `[SERVICE]` currently declares
`Parsers_File parsers.conf` and nothing else (`fb-values.yaml:644`). The 2026-09-03 audit already
found this: a parser added under `config.customParsers` exists as a file and is silently unused.
**The second `Parsers_File` line is not optional.** Confirm the chart's actual path from the
`--dry-run` render rather than copying the DaemonSet's — the chart versions differ.

**Trap 2 — `Time_Keep On` is load-bearing, and omitting it fails silently.** A Fluent Bit parser
*consumes* the time key by default. Without `Time_Keep On`, `timestamp` is removed from the
record, so filter 1's `Rename timestamp _time` becomes a no-op, `_time` never exists, and filter 3
— which reads `_time` at `fb-values.yaml:370` for `min_record_time` / `max_record_time` — hits
`if type(t) == "string"` and **skips without erroring**. Every summary row would lose its replay
detector permanently, with no symptom anywhere. Same silent-skip shape as `type_int_key`.

**Still to verify, not assume:** `_time` is nanosecond precision (`…24.504420706Z`). Whether
Fluent Bit's `%L` accepts 9 fractional digits, and whether the value survives into a `date` field
(millisecond) or needs `date_nanos`, is a render-and-test question, not a default.

### 3.2 A composed document id — `Id_Key sequence` would be data loss, not dedup

**v1's headline gain was false.** `sequence` is the JBoss LogManager per-`ExtLogRecord` counter,
**per JVM from JVM start** — the 2026-09-03 audit measured 3723/3724 as "~3.7k records since JVM
start". It is not a record identity:

- **Polaris restart** → new JVM, counter restarts near 0, records collide with the old JVM's on
  the same day in the same index. Routine.
- **HPA** (#8, `maxReplicas: 3`, all replicas appending to one log file) → three independent
  counters interleaved in the file the shipper tails. *Downgraded for this cluster* — nothing has
  pushed Polaris past 80% CPU — but it is a live config, not a hypothetical.
- **`upsert` merges, it does not replace.** The plugin sends `doc_as_upsert`, so a collision
  produces a **field-union of two unrelated records** — an access record's `http_status` stapled
  onto an application record's `exception.*`. Individually plausible, entirely fictional, no error.

**The fix — a new Lua script in its own ConfigMap key**, which is what keeps the notebook's gate
meaningful:

```lua
-- polaris_docid.lua   (a SEPARATE luaScripts key: polaris_access_log.lua stays byte-identical,
--                      so the notebook's sha gate keeps meaning "policy v3 is what is deployed")
function polaris_doc_id(tag, ts, record)
    if record["report_type"] ~= nil then                       -- tier 3
        record["_doc_id"] = string.format("%s/%s/%s/%s",
            record["hostname"], record["window_start"], record["report_type"],
            record["resource"] or record["user_principal_name"] or "summary")
        return 2, ts, record
    end
    local host, seq, t = record["hostName"], tonumber(record["sequence"]), record["_time"]
    if host == nil or seq == nil or t == nil then return 0, ts, record end
    record["_doc_id"] = string.format("%s/%d/%s", host, seq, t)   -- %d, NOT concatenation
    return 2, ts, record
end
```

```ini
[FILTER]
    Name          lua
    Alias         polaris_doc_id
    Match         polaris.*
    script        /fluent-bit/scripts/polaris_docid.lua
    call          polaris_doc_id
    type_int_key  sequence          # ← see below. Not optional.
```

**Why `%d` and not `..`.** Every record in this repo was read back *through VictoriaLogs*, which
stringifies everything, so **nothing here settles whether Polaris emits `sequence` as `"3724"` or
`3724`.** If it is a number, Lua's repack encodes it as a double and naive concatenation yields
`…/3724.0/…`. Settle the type by reading one raw line off the PVC, not out of a sink.

**Why `type_int_key sequence`.** This filter returns `2`, which **repacks every record** — so
without it, `sequence` is re-encoded as a double *in the stored document* for all records, not
just the access-log ones filter 2 already repacks. That would break any join against tier 1,
which is never repacked. This is `type_int_key`'s original bug reappearing on the field we just
made a primary key; the same one-line countermeasure applies.

**Why `report_type` branches first.** Report rows carry no `sequence`; their stable identity is
`hostname / window_start / report_type / (resource | user_principal_name)`. **Not `report_seq`** —
guide §7.4 trap 3: it is per-pod and resets.

**Placement:** filter 5, after `polaris_field_trim`. It needs `_time` (filter 1) and must not run
before filter 3 reads it.

### 3.3 The two outputs

```ini
# TIER 2 — filtered logs
[OUTPUT]
    Name                opensearch
    Match               polaris.vlogs           # tag rename: see §7 Q1 — and read it, it bites
    Host                192.168.194.1
    Port                9200
    HTTP_User           ${OS_USER}              # needs env plumbing — §4.6
    HTTP_Passwd         ${OS_PASSWORD}
    Logstash_Format     On
    Logstash_Prefix     polaris-logs
    Logstash_DateFormat %Y.%m.%d
    Suppress_Type_Name  On
    tls                 On
    tls.verify          Off
    Id_Key              _doc_id                 # §3.2 — NOT `sequence`
    Write_Operation     upsert
    Trace_Error         On                      # §4.1 — without this the drops are invisible
    Retry_Limit              5
    storage.total_limit_size 400M               # §4.5 — 2Gi emptyDir, three outputs during dual-write

# TIER 3 — summarized documents
[OUTPUT]
    Name                opensearch
    Match               polaris.report
    ... Logstash_Prefix polaris-report   (or a rollover alias — §3.6)
    Id_Key              _doc_id
    Write_Operation     upsert
    Trace_Error         On
    storage.total_limit_size 200M
```

**No `Time_Key` line.** With §3.1's parser fix, Fluent Bit's record time *is* the Polaris event
time, and the plugin injects `@timestamp` itself. **Setting `Time_Key` to a name the record
already carries produces two `@timestamp` keys in one JSON object** → OpenSearch rejects the
document with a per-item 400 inside a bulk that returns HTTP 200. See §4.1.

`json_date_key false` goes away — the es/opensearch plugin ignores it. (v1 justified this wrongly;
§10.)

### 3.4 `_msg` / `_time`: do not rename — pending one test

Filter 1 renames `message → _msg` and `timestamp → _time` because **VictoriaLogs reserves those
names**. v1 proposed a filter to rename them back for OpenSearch. **That filter would break
VictoriaLogs during the dual-write window** — filters are per-tag, not per-output, so the still-live
`http` output's `_msg_field=_msg` would find nothing. v1's verification step would have corrupted
the sink it was verifying against.

**Recommendation: never rename.** Keep `_msg` and `_time` as field names in OpenSearch and let
the parser own `@timestamp`. Three things this buys:

- dual-write works, because the VictoriaLogs output keeps seeing the fields it declares;
- one fewer filter, and one fewer thing that can silently drop a stream;
- **§7 of the guide keeps its field names.** Only the query *language* changes, not the schema —
  which materially reduces the risk in the largest chunk of doc churn.

**The one thing to test first (§6 step 0):** whether this OpenSearch accepts a top-level `_msg`.
Modern versions reject only *actual* metadata names (`_id`, `_index`, `_source`, …) and `_msg` is
not one — but that is a one-`curl` question, not an assumption.

**If it is rejected:** the rename lands in the *cutover* commit that removes the http output, never
in the dual-write commit. Dual-write then verifies delivery and counts only.

### 3.5 Index templates — write them before the first document

OpenSearch locks a field's type on first write, per index, and defaults strings to `text` +
`.keyword`. **A template written after the first write does nothing to the index already created.**
Three templates, one per tier pattern; tier 1's is not ours to touch.

- explicit **`long`** for `http_status`, `response_size`, `sequence`, and every field in filter 3's
  `type_int_key` list — that list is the inventory, **plus `sequence`, which is in neither list**;
- `dynamic_templates` mapping strings to **`keyword`**, with `text` only for `_msg`;
- `boolean` for `access_log_parse_error` — but note `partial_window` is the **string**
  `"true"`/`"false"` (`fb-values.yaml:514`), so a boolean query on it returns nothing. Map it as
  `keyword` or fix it in the Lua, deliberately either way;
- `_time` as `date` (or `date_nanos` — §3.1);
- `_doc_id` as `keyword`, `index: false` — it is an id, not a search field.

**Aggregations move to `.keyword`.** `stats by (loggerName)` becomes a terms agg on
`loggerName.keyword`; on `loggerName` itself it aggregates *analysed tokens* (`org`, `apache`,
`polaris`) and returns a plausible, completely wrong histogram.

### 3.6 Retention per tier

| tier | mechanism | note |
|---|---|---|
| 1 | **unchanged** | already 5d and working — which tells us ISM is live in this OpenSearch |
| 2 | daily index + ISM delete after 30d | consistent with tier 1's existing shape |
| 3 | **rollover alias** + delete after 365d | ~48 rows per window does not justify an index per day |

**A trap the ladder introduces.** Tier 3 is long-retention and **the temporary 30s window is still
live**: ~2,300 report docs/day at 1800s, ~138,000/day at 30s. Anything written while the fast
window runs sits in the long-lived index for its full retention — a permanent 60×-density band
that every long-range `stats` then has to reckon with. **Revert the window to 1800/30 before tier 3
gets its long ISM policy.** The revert is now a prerequisite, not cleanup.

**#7 does not "close" here** (v1 said it did). #7 is *retired by the VictoriaLogs uninstall*, not
by ISM — and its uglier half, an unauthenticated LoadBalancer serving both ingest and query on
9428, goes away with the release rather than being fixed by anything in this plan.

---

## 4. The sharp edges

v1 claimed these were "all on the query side". **False** — 4.1 is a data-plane edge and it is the
worst one.

**4.1 OpenSearch can delete a document and report success.** A bulk request returning HTTP 200 can
carry per-item `mapper_parsing_exception` / `document_parsing_exception`. Fluent Bit treats the
flush as successful: the documents are gone, `Retry_Limit` never fires, and **none of
`fluentbit_output_{errors,retries,dropped}_total` increments** — which is exactly the health check
guide §8.1 relies on. VictoriaLogs, being schemaless, could not produce this failure at all.
So §3.5's mapping conflicts do not return a wrong number; **they delete the record.**
Countermeasure: `Trace_Error On` on both outputs, and §6's record-count gate.

**4.2 `.keyword`.** §3.5. Wrong number, no error.

**4.3 The 10,000-hit cap.** LogsQL is queried with `limit=0`; a plain `_search` **stops at 10,000
hits and does not say so**. The notebook's step 6 pulls every record for a run. Use `search_after`
with a PIT, or `_count` first and assert. This is guide §7.4 trap 1 in a new sink.

**4.4 `sum()` on an empty group.** LogsQL returns `NaN` (trap 5); OpenSearch returns `0.0`, which
is worse — indistinguishable from a real zero. **"Absence is not zero"** is the guide's closing
lesson and OpenSearch removes the signal that made it visible. Pair every `sum` with
`value_count`.

**4.5 Buffer sizing can evict the pod.** `flb-storage` is an `emptyDir` with `sizeLimit: 2Gi`
(`fb-values.yaml:23-25`). The existing http output holds `storage.total_limit_size 1G`; adding two
more outputs during dual-write can exceed the volume, and **kubelet evicts on `sizeLimit`** — at
precisely the moment you are trying to measure. Hold the three at 400M/400M/200M for the window.
The durable fix is the PVC swap the values file already documents at lines 14–22, which also kills
the replay problem at its source rather than at the sink.

**4.6 `${OS_USER}` has no plumbing, and its failure mode is a silent 401.** `fb-values.yaml` has
**no `env:` and no `envFrom:`** (grep: zero hits), and no Secret manifest in this repo creates the
credential. An undefined `${VAR}` expands to the **empty string**; OpenSearch returns 401,
`Retry_Limit` exhausts, chunks drop — past both of v1's gates. Needs:

```yaml
env:
  - name: OS_USER
    valueFrom: {secretKeyRef: {name: opensearch-shipper-credentials, key: username}}
  - name: OS_PASSWORD
    valueFrom: {secretKeyRef: {name: opensearch-shipper-credentials, key: password}}
```

and the Secret created out of band. **This invalidates the file's own header** — `fb-values.yaml:20`
says "Install — no `--set` flags, everything is in this file". Update it in the same commit.

**Ordering hazard.** #4 requires rotating `Str0ngP@ssw0rd123!` on the OpenSearch side, and
`fluent-bit/values.yaml:159,183` still carries the literal. **If the rotation lands before the
DaemonSet's copy is fixed, node-wide log collection stops** — including tier 1. Sequence: fix the
DaemonSet's credential handling, *then* rotate, *then* everything else.

---

## 5. What does NOT change

Polaris config, the PVC, the noise filter policy **v3**, report schema **v2**, the window
arithmetic, carry-and-decay, the access-log parser, `type_int_key` on filters 2 and 3 — all
storage-agnostic, all untouched. **`polaris_access_log.lua` stays byte-identical**, which is what
keeps the notebook's sha gate meaning "policy v3 is what is deployed" (§3.2).

---

## 6. Sequencing

The obvious order is wrong twice over. **Cut over before fixing the harness** — its bugs are in
code that queries the sink, so fixing them against VictoriaLogs and again against OpenSearch is the
same work twice; bug 1's real fix (*derive the summable set from the row's own numeric keys*) is
sink-independent and matters more under OpenSearch mappings. And **the 30s window is an asset for
the migration** — ~2 minutes per verification run against ~90 — so use it, then revert before
tier 3 goes long (§3.6).

| # | step | gate |
|---|---|---|
| **0** | `curl` the OpenSearch version; PUT a throwaway template as `admin`; index a doc with a `_msg` field; `curl` from **inside a `datahub-hynix` pod** to `192.168.194.1:9200` | version recorded; template accepted; `_msg` accepted (→ §3.4 recommendation) or rejected (→ fallback); the shipper's network path proven, not assumed |
| **1** | Secret created; DaemonSet credential handling fixed; **then** rotate the OpenSearch password | tier 1 still ingesting after the rotation |
| **2** | Three index templates PUT | `GET _index_template/polaris-*` returns both new ones; **no `polaris-*` index exists yet** |
| **3** | Parser fix (§3.1) + `polaris_docid.lua` + both outputs, **alongside** the existing http output | render greps: `Parsers_File` == 2; `Time_Keep   On` == 1; `polaris_docid` == 1; `type_int_key  sequence` == 1; `Name  *opensearch` == 2; `Name  *http` == 1; **plus the unchanged guide §4.7 greps** |
| **4** | `helm upgrade`; read the pod log first | no Lua rejection, no crashloop; `polaris_access_log.lua` sha **unchanged** from the deployed ConfigMap |
| **5** | **Skip one full window**, then reconcile (§7) | the replay window is not the measurement — see below |
| **6** | Remove the http output (+ the rename, if §3.4's test said rejected) | render greps; `Name  *http` == 0 |
| **7** | Harness + notebook collection ported to `_search` | a coverage run reproduces run `1788755035`'s arithmetic (158 / 41 / 12 / 1,186,348) **from OpenSearch** |
| **8** | Revert `WINDOW_SECONDS` 30→1800, `Interval_Sec` 5→30, riding `resources_other`/`_distinct` into the summary `_msg` | `shipper-v3-upgrade-runbook.md` |
| **9** | ISM policies applied — tier 3's **after** step 8 (§3.6) | — |
| **10** | VictoriaLogs uninstall proposed **separately** | destructive; needs its own authorisation |

**Why step 5 skips a window.** #14d: *"the first window after the `helm upgrade` is a replay, not
traffic… at 30s the entire replay lands in one window as a spike. Do not trust it."* Step 4
replaces the pod, so the `emptyDir` and the tail DB are gone and `Read_from_Head true` re-reads the
whole file. v1 reconciled immediately after the upgrade — against a replay spike. Gate on the
replay detector the report already carries: `max_record_time - min_record_time` ≤ `window_seconds`.

**Step 6 is a second pod replacement** — a second full replay, and whatever was still disk-buffered
for the http output is discarded. VictoriaLogs' last chunks are lost at cutover; that is acceptable
and should be stated rather than discovered.

---

## 7. The reconciliation gate — rebuilt so it can fail

v1's gate was designed to pass: *"a **shipper** restart produces no duplicate `sequence`"* replays
the same file from the same Polaris JVM, so of course it collapses cleanly. It tested none of the
three real collision modes. This version tries to falsify.

| assertion | what it can catch |
|---|---|
| `access_seen` on the summary row is **identical** in both sinks | the report is generated once and fanned out — a difference is transport, not filter |
| `fluentbit_output_proc_records_total` for the window **equals** OpenSearch `_count` | **4.1's silent per-document drop** — the only check that sees it |
| `max_record_time − min_record_time` ≤ `window_seconds` | the window is traffic, not a replay (#14d) |
| `http_status` answers a `range: {gte: 500}` query | the mapping locked numeric, not `float`/`text` |
| `stats by (loggerName)` and the `.keyword` terms agg return the **same** group set | 4.2, caught rather than assumed |
| `errors_4xx` / `auth_denied` / `bytes_total` reconcile across resource rows, principal rows and summary | the v2 self-check that already passed on VictoriaLogs must still pass |
| **restart Polaris**, then confirm two records with the same `sequence` and different `hostName` are **two documents** | §3.2's real collision mode — a shipper restart cannot test this |
| `sequence` is a JSON **number** in tier 2 and in tier 1, with no `.0` | the repack hazard §3.2 warns about, on the join key |
| tier 1 count for the window, **deduplicated on `sequence`**, vs tier 2 count | tier 1 double-writes (§9) — an undeduplicated denominator is ~2× inflated |

---

## 8. Open questions — settle before step 2

**Q1 — the tag `polaris.vlogs` is now a lie, and renaming it carelessly drops the whole log
stream.** It is `Match`ed in three filters (`fb-values.yaml:708, 731, 773`) — **and *defined* at the
INPUT (`:661`)**, which v1's checklist omitted. Rename the `Match` lines without the `Tag` line and
filters 1/2/4 stop matching, the tier-2 output matches nothing, and **the log stream disappears
while filter 3's `polaris.*` keeps the report stream flowing normally.** Healthy pod, reports
arriving, logs gone — #13's third occurrence. Rename all four together or none.

**Q2 — SETTLED 2026-09-08 (Kade):** the DaemonSet reads **stdout/stderr**, never the log file. The
consequence is §1.1's ladder, not a defect.

**Q3 — is `192.168.194.1:9200` reachable from a Deployment pod in `datahub-hynix`?** The DaemonSet
reaches it from a host-network context; the shipper does not. **Assume nothing** — step 0.

**Q4 — `sequence`: string or number off the PVC?** Every sample in this repo came back through
VictoriaLogs, which stringifies. Read one raw line. §3.2 depends on it.

**Q5 — is tier 1's 5-day retention an ISM policy or a manual curator?** It tells us which mechanism
tiers 2 and 3 can rely on, and it is one `curl`.

**Q6 — OpenSearch version.** Recorded nowhere in this repo (CLAUDE.md:19-20 — it is outside the
repo entirely). Composable-template body shape and the ISM API path both depend on it.

---

## 9. Tier 1 is left alone, and here is what that costs

Kade's call: **do not change the current configs.** Legitimate at 5-day retention, but two facts
should be written down rather than rediscovered.

**The DaemonSet writes each Polaris console line to `k8s-logs` twice.** OUTPUT 1 matches
`kube.*benchmarks-polaris*` (`fluent-bit/values.yaml:155`) and OUTPUT 2 matches `kube.*` (`:179`);
Fluent Bit routes to **every** matching output and both target `k8s-logs` — one copy keyed on
`sequence` + `upsert`, one with `Generate_ID On`. So **any tier-1 count is roughly 2× inflated**
and must be deduplicated on `sequence` before it is compared to anything (§7's last row).

**Tier 1's `Id_Key sequence` + `upsert` carries the same defect §3.2 rejects for tier 2** — per-JVM
counter, resets on restart, `doc_as_upsert` field-unions colliding records. Acceptable at 5 days
and unfiltered. **It must not become the precedent for tiers 2 and 3**, and nobody has ever checked
whether `k8s-logs` is *missing* documents because of it. A testable prediction, if it ever matters:
tier 1's Polaris count for a day spanning a Polaris restart should be near `max(sequence)`, not the
true line count.

---

## 10. What v1 of this document got wrong

Recorded because the pattern matters more than the errors.

1. **`Id_Key sequence` sold as the plan's headline *gain*.** It is data loss (§3.2). The
   verification gate proposed for it was constructed so that it could only pass.
2. **`Rename _time @timestamp` alongside `Logstash_Format` + `Time_Key @timestamp`** — two
   `@timestamp` keys in one object, rejected per-item inside an HTTP 200 (§3.3, §4.1).
3. **Never noticed the tail parser does not read Polaris' `timestamp`** (§3.1), so every document
   would have been dated on arrival.
4. **"Filters 2 and 3 both read `_msg`."** Filter 3 does not read `_msg` — it reads **`_time`**
   (`:370`). Right conclusion, wrong constraint, and the wrong constraint would lead a later reader
   to think `_time` is free to rename early, silently zeroing the replay detector.
5. **`json_date_key` called "a VictoriaLogs-specific artifact."** It is Fluent Bit injecting its own
   ingest timestamp — *the same mechanism* as (2) and (3). Having the one prior instance of the bug
   in hand and filing it as sink-specific is why (2) and (3) were missed.
6. **The tag-rename checklist omitted the INPUT** (§8 Q1) — following it literally drops the log
   stream.
7. **"The sharp edges are all on the query side."** §4.1 is a data-plane edge and the worst one.
8. **"#7 closes."** It is retired by the uninstall, not by ISM (§3.6).
9. **Dual-write was impossible as designed** — the proposed rename filter would have broken the sink
   it was verifying against (§3.4).
10. **Reconciliation was scheduled on the replay window** #14d says explicitly not to trust (§6).

Five of these produce *a plausible wrong result with no error*. That is now four separate
occurrences in this pipeline's history — `type_int_key`, #13, harness bug 1, and this document.
**The countermeasure that keeps working is the same one: gate on a number that can come back wrong,
not on a command that can come back clean.**

---

## What this plan does NOT authorise

No values file has been edited. Steps 0–10 need explicit approval, and step 10's
`helm uninstall vlsingle` / PVC deletion needs its own authorisation **at the moment of execution**
— approval of this plan is not approval to run it.

**NOT VERIFIED: nothing here was checked against the cluster.** This is a Cowork session with no
`kubectl`, `helm` or `docker` reach. Every claim about running state is read from the repo and its
memory tree, not from the objects.
