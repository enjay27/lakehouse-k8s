# REVIEW — the whole Polaris log pipeline, end to end (2026-09-16)

**Scope:** every step a Polaris log line goes through, from the container log file to OpenSearch. That covers Fluent Bit's
input, chunk, filter and routing stages, the config (`fluent-bit/values.yaml`), the Lua, the index templates, the deploy
path, the verification scripts and the docs.
**Status: DECIDED 2026-09-16 (Kade) — P1, P2, P3, P4, P6, P7, P8, P11, P12 applied in the repo as schema v6, NOT ROLLED (`#32`).**
P5 not decided. P9 is practice (use step10/step11). P10: the shipper exists; Kade uninstalls it manually later.
P6 decision on the raw access line: **keep it, renamed `message`** (and the report summary sentence renamed the same way); `app` dropped.
Measurements: M1 unknown · M2 **~1,800 Fluent Bit docs per traffic notebook run** · M3 yes (tier-1 docs with `log` exist — they are
lines no parser handled; P4's JSON filters repeat Merge_Log's decode and cannot succeed where it failed; see `#32` for the one gate on
the Polaris text parser) · M4 yes · M5 out of scope (tier 2/3 only).
The Lua itself was reviewed and refactored earlier the same day (`REVIEW-lua-refactor-2026-09-16.md`, `#31`, rolled).
Retention/ISM is **out of scope**: the Monitoring team owns it (Kade, 2026-09-16).

**Evidence used:** the live values file and Lua at `7ecb65d`, and Kade's exports from 2026-09-16:
- `k8s-logs` 14:43:35–14:44:13Z, 870 docs;
- `polaris-logs-*` 15:00:34–15:01:13Z, 386 docs;
- the `polaris-report-*` 15:01:00Z window, 67 rows.

Byte shares below are **`_source` JSON bytes**. OpenSearch on-disk size also depends on mappings and compression, so every
storage claim ends with a measurement to run (§4).

---

## 0. Findings, ranked

| # | layer | finding | proposal | gain | risk | effort | needs |
|---|---|---|---|---|---|---|---|
| **P1** | Fluent Bit core, tier 2 | Every Polaris record enters the Lua filter carrying **16 keys / ~717 B**. **7 keys (~32 % of bytes) are removed right after** by FILTER 4, and 58 % of records are dropped by the Lua anyway | Move `polaris_field_trim` **before** the Lua; add `app` **after** it | ~44 % fewer keys and ~32 % fewer bytes through every Lua conversion (both directions); no output change | low | S | K decide → values roll |
| **P2** | Fluent Bit core, tier 1 | **OUTPUT 1 has never indexed a record** (`#18`). Every Polaris tier-1 chunk is still routed to it, formatted, and each record logged as `skipping record … unsafe Id_Key` | Delete OUTPUT 1 (`PLAN-tier1-dedup` option B) | removes a second output per Polaris chunk and a warn line per record | low (it stores nothing today) | S | K decide (tier 1) |
| **P3** | Fluent Bit core, tier 1 | The tier-1 tail reads `/var/log/containers/*.log` **including Fluent Bit's own log**. P2's warn lines, `Trace_Error` bulk dumps and retry messages are fed back into `k8s-logs` | `Exclude_Path` for the `benchmarks-fluent-bit` container log | ends the feedback loop | low: the pod log is still there via `kubectl logs` | S | measure (§4 M2) → K decide |
| **P4** | Fluent Bit core, tier 1 | Three parser filters run on tier-1 records and should find nothing to do: `polaris_json` (**all** containers), `polaris_text` and `datahub_json`. The `kubernetes` filter (`Merge_Log On`, `Keep_Log Off`) has already parsed and removed `log` for JSON lines. For plain-text containers `polaris_json` attempts a JSON parse of every line | Remove the three filters | one filter pass per record fewer for every pod on the node | medium: tier 1 is node-wide | S | measure (§4 M3) → K decide |
| **P5** | Deploy path | The Lua (kustomize ConfigMap) and the config (Helm release) are **two deploy units**. Their order is manual and a wrong order is harmful (`#31`: one order stops every input, the other stores every access line as a parse error). `apply-lua.sh`'s restart logic and step3's "container started after the ConfigMap" check exist only because of this split | **A:** one Helm release: chart `luaScripts` fed from the file (`--set-file` locally, Argo CD `fileParameters` in prod), and the chart's `checksum/luascripts` restarts on any Lua change. **B:** keep the ConfigMap and put its sha in a pod annotation in values | one atomic deploy; ordering hazard gone; fits the GitOps port (3.5) | low | M | K decide (reverses the 09-16 ConfigMap choice, whose main reason, hot reload, is gone) |
| **P6** | Stored docs, tier 2 | Constant fields on every detail doc: `flb_tag` "polaris.logs" (3.4 %), `stream` "stdout" (2.4 %), `app` "polaris" (2.1 %). Parsed access docs also keep the raw `_msg` (**21.8 %**) next to the fields parsed from it | Drop `flb_tag` (`Include_Tag_Key Off`) and `stream`. **Decide** on `_msg` for parsed access lines | ~8 % always; ~+20 % of access docs if `_msg` goes | low / **audit decision** for `_msg` | S | K decide |
| **P7** | Stored docs, tier 3 | `_msg` is **25.5 %** of report bytes and only repeats the numeric fields as a sentence. `app` and `level` are constants | Keep `_msg` on `summary` only; drop `app`/`level` from rows | ~25 % of report bytes | low (Discover readability for rows) | S (Lua) | K decide |
| **P8** | Index mappings | Every undeclared string is dynamic-mapped as **`text` + `.keyword`**, so each is indexed twice. That includes high-cardinality `_msg`, `api_path`, `resource` and every report string | Declare categorical fields `keyword` (keeping the `.keyword` path queries use), `client_ip` as `ip`, `_msg` as `text` only, report `_msg` `index: false` | measurable only on store size (§4 M5) | medium: query field names | M | measure → K decide (templates are ours; lifecycle is Monitoring's) |
| **P9** | Verification process | Readouts come from Dev Tools panel copies. They are not JSON (triple-quoted strings), need the fix script, once came from the wrong index, and never include tier 1, so step11 cannot run. This session needed 3 round trips for 2 windows | Always `step10 <window_start>` then `step11` (curl, exact JSON, window cut by the tick `#26`). Optionally one `readout.sh` that finds the latest summary window itself | 1 command instead of 3–4 exports; step11 always possible | none | S | none (use what exists) |
| **P10** | Flow level | A **second pipeline for the same logs may still run**: `fb-polaris-shipper` → VictoriaLogs from the Polaris log PVC. The cutover plan said to uninstall it "after this cutover", and nothing records that it happened. Polaris is also configured to write file JSON (`QUARKUS_LOG_FILE_JSON_ENABLED`) | Confirm with `helm list -A`; if running, decide uninstall | a whole release, a sink and a write path | depends on who still reads VictoriaLogs | S | K confirm |
| **P11** | Scripts & docs | `logging/scripts` carries 22 files named after old plan steps (`step0`–`step12`); 7 describe finished or superseded work (§2 P11). `logging/` has 25 docs, most of them superseded PLAN/HANDOFF files with no index | Move obsolete scripts to `logging/scripts/attic/`; add `logging/README.md` as a status index | faster cold start, fewer wrong reads | none | S | K OK for the moves (Cowork cannot delete) |
| P12 | Buffering | Tier-2/3 outputs have `storage.total_limit_size` 400M / 200M. When exceeded (OpenSearch down for long), Fluent Bit **drops the oldest chunks silently**. For tier 3 that is the only record of counted reads | No config change; give the Monitoring team the metric to alert on (`fluentbit_output_dropped_records_total`, storage chunk metrics) | visibility | none | S | hand-over note |

**Suggested order:** P9 (no change, use now) → **P1 + P6-constants** (one values roll, tier 2 only, verifiable with step11) →
P2 + P3 + P4 after M2/M3 (one tier-1 roll) → P5 before the GitOps port → P7/P8 after measuring → P10/P11 housekeeping.

---

## 1. The flow as it runs today

```
/var/log/containers/benchmarks-polaris-…log   (docker json-file lines, one Polaris JSON log line inside each)
│
├── INPUT tail  Tag kube.*          (tier 1, ALL containers, memory buffer, Mem_Buf_Limit 50MB)
│     multiline docker,cri → chunk
│     FILTER kubernetes      Merge_Log On / Keep_Log Off   → parses the JSON, adds pod metadata (API lookup, cached)
│     FILTER parser polaris_json   kube.*                  → `log` already gone: nothing to do            [P4]
│     FILTER record_modifier       environment, cluster
│     FILTER parser polaris_text   kube.*benchmarks-polaris* → nothing to do (JSON already merged)        [P4]
│     FILTER parser datahub_json   kube.*datahub-*         → nothing to do                                [P4]
│     ROUTER ─┬─ OUTPUT 1 opensearch  Match kube.*benchmarks-polaris*  Id_Key sequence  → skips 100 %      [P2]
│             └─ OUTPUT 2 opensearch  Match kube.*   Generate_ID      → k8s-logs-*
│     (Fluent Bit's own container log is also under kube.*: its warnings come back through this path)   [P3]
│
├── INPUT tail  Tag polaris.logs    (tier 2, same file, own DB, storage.type filesystem)
│     multiline docker,cri → chunk (filesystem)
│     FILTER 0 parser polaris_stdout_json  (log → fields, Reserve_Data)          16 keys / ~717 B per record
│     FILTER 1 modify   Add app polaris; Rename message→_msg, timestamp→_time
│     FILTER 3 lua polaris_noise_filter    msgpack→Lua table→(decide)→msgpack    58 % return -1           [P1]
│     FILTER 4 record_modifier  Remove_key ×8 (7 present on Polaris records)   (after the Lua)           [P1]
│     ROUTER → OUTPUT opensearch polaris-logs-*  Generate_ID, Trace_Error, total_limit 400M               [P6][P12]
│
└── INPUT dummy  Tag polaris.report  every 5 s
      FILTER 3 lua (same instance: the counters live there) → -1, or the window's report rows at a boundary
      ROUTER → OUTPUT opensearch polaris-report-*  Generate_ID, Trace_Error, total_limit 200M             [P7][P12]
```

**Per window (14:44Z / 15:01Z, identical):** 720 Polaris records in, 355 access lines. The Lua stores 300 detail docs and
drops 420 (58 %); 67 report rows come out. Tier 1 stores all 720 (plus the start-up lines outside the window).

---

## 2. Findings in detail: current vs proposed

### P1 — trim before the Lua, not after

**Current** (values FILTER order): `parser → modify(Add app, Rename) → lua → record_modifier(Remove_key ×8)`.
**Proposed:** `parser → modify(Rename only) → record_modifier(Remove_key) → lua → record_modifier(Record app polaris)`.

What enters FILTER 3 today, measured on the 870 Polaris records of the 14:43Z export (tier-1 copy minus Kubernetes
metadata, renamed as FILTER 1 does):

| key | share of bytes | read by the Lua? | stored? |
|---|---|---|---|
| `_msg` | 21.1 % | yes | yes |
| `mdc` | 12.0 % | yes (`requestId`) | yes |
| **`processName`** | **11.0 %** | no | removed by FILTER 4 |
| `loggerName` | 7.7 % | yes | yes |
| `hostName` | 6.7 % | no | yes |
| **`loggerClassName`** | **6.4 %** | no | removed |
| `_time` | 5.6 % | yes | yes |
| **`time`** (CRI) | **5.4 %** | no | removed |
| **`threadName`** | **4.7 %** | no | removed (`#30`) |
| `exception` | 3.6 % | no | yes |
| `stream`, `sequence`, `level` | 6.6 % | `level` yes | yes |
| `app` | 2.1 % | **no** | yes |
| **`threadId`, `processId`, `ndc`** | **4.7 %** | no | removed |

- Keys per record: **16.0 → 9.0**, bytes −32 %. Moving `app` after the Lua saves another 2.1 % and one key.
- Fluent Bit converts each record msgpack → Lua table on the way in, and back to msgpack for every kept record. That work
  scales with keys and string bytes, and today it is spent on 7 keys the next filter throws away, for 58 % of records the Lua
  throws away too.
- **Why it is safe:** the Lua reads only `loggerName level _msg _time mdc` (and the test-only `_now_override`). Held and
  orphan records are emitted as they were received, so they would carry the trimmed shape. That is what FILTER 4 gives them
  today anyway.
- **Verification:** step2 (order of `Alias` lines in the render), step3, one traffic window, then step11. The report rows
  and the detail-by-logger counts must be unchanged, and the stored field list must be identical except `app` still present.
- **Cannot be measured from Cowork:** CPU. It is a phase 3.1 load-test number. The byte and key reduction is exact.

### P2 — OUTPUT 1 (tier 1, `Id_Key sequence`)

**Current:** `Match kube.*benchmarks-polaris*`, `Id_Key sequence`, `Write_Operation upsert`. Polaris' `sequence` is a JSON
integer, and the plugin requires a string, so every record is skipped with a warn line (`#18`, measured 13,737/13,737 on
2026-09-09). Each Polaris chunk still costs this output a flush: format, skip, log. OUTPUT 2 already stores every record.
**Proposed:** delete the block. Stored data does not change. `PLAN-tier1-dedup-2026-09-09.md` option A (a real composed
dedup key) stays possible later; option B is this.
**Still to measure (M1):** whether 5.1.1 still logs the skip per record. #18 was read on 3.2.2.

### P3 — Fluent Bit reads its own log

**Current:** tier-1 `Path /var/log/containers/*.log`, no `Exclude_Path`. Fluent Bit's container log sits in that directory.
Everything it prints (`skipping record`, `Trace_Error` bulk responses, retry warnings, `#29`'s chunk messages) becomes
`k8s-logs` documents. Under an error storm, each failure line creates more output.
**Proposed:** `Exclude_Path /var/log/containers/benchmarks-fluent-bit-*.log`.
**Trade-off:** Fluent Bit's own history is no longer searchable in OpenSearch; `kubectl logs` and the metrics endpoint remain.
**Measure first (M2):** how many `k8s-logs` docs per hour come from the Fluent Bit container.

### P4 — tier-1 parser filters with nothing to parse

**Current:** after `kubernetes` with `Merge_Log On` + `Keep_Log Off`, a JSON line's `log` key is already parsed and removed.
- `polaris_json` (Match `kube.*`, every container) is commented in the values file itself as "near no-op". On plain-text
  containers it tries a JSON parse of every line and fails.
- `polaris_text` (Polaris, only for a non-JSON Polaris) and `datahub_json` (DataHub JSON, already merged) should find nothing.

**Proposed:** remove all three.
**Measure first (M3):** in `k8s-logs`, count Polaris/DataHub docs that still have a `log` field or no `loggerName`. If both
are 0, the filters did nothing in that period.

### P5 — one deploy unit instead of two

| | **C (current)**: ConfigMap via kustomize + Helm | **A**: chart `luaScripts` in the same release | **B**: ConfigMap + checksum annotation |
|---|---|---|---|
| Lua reaches the pod | `kubectl apply -k` then a restart (`apply-lua.sh`) | `helm upgrade --set-file luaScripts.polaris_access_log\.lua=fluent-bit/polaris_access_log.lua`; Argo CD `helm.fileParameters` | `apply -k`, then `helm upgrade` with `podAnnotations.checksum/polaris-lua: <sha>` written into values by a script or CI |
| Restart on Lua change | manual (apply-lua.sh) | automatic (`checksum/luascripts`, chart 0.57.6 renders it only when `luaScripts` is set, per step2's source read) | automatic (annotation change) |
| Lua + config change together | **manual order**, harmful either way if wrong (`#31`) | one render, one rollout: atomic | still two commands, but the second always carries both |
| "Is the pod running this script?" | step3 compares container start with ConfigMap change time | the pod template hash says it | the annotation says it |
| Lua visible in `helm get values` / rollback with `helm rollback` | no | **yes** | no |
| GitOps (3.5) | two Argo CD sources and sync-wave ordering | one Application | one Application plus a generated annotation |
| Downsides | the ordering hazard; extra scripts | the Lua renders as one escaped line (step2's content checks become a sha check, as in v4) | a generated value in a committed file |

The ConfigMap was chosen on 2026-09-16 so the script could load **without a restart** (hot reload). Hot reload was removed the
same day, so every Lua change is a restart anyway, and the remaining property of C is the separation that creates the
ordering hazard. **Recommendation: A**, done together with the GitOps port or before it. *Not verified:* Argo CD
`fileParameters` behaviour on this chart; chart 0.57.6's `checksum/luascripts` on a real render.

### P6 — constant fields in `polaris-logs-*`

Measured on 243 access and 143 app detail docs from 15:01Z:

| field | value | share (access / app docs) | used by any query in the repo? |
|---|---|---|---|
| `flb_tag` | `polaris.logs` on every doc | 3.4 % / 3.0 % | no (only the retired heartbeat plan) |
| `stream` | `stdout` on every doc | 2.4 % / 2.1 % | no |
| `app` | `polaris` on every doc | 2.1 % / 1.9 % | no; the index already isolates the stream |
| `hostName` | the Polaris pod | 6.8 % / 6.0 % | **keep**: distinguishes replicas in prod |
| `mdc.realmId` | `POLARIS` on all 386 | inside `mdc` 12 % | keep: prod may use several realms |
| **`_msg` on parsed access lines** | the raw CLF line, fully parsed into 6 fields | **21.8 %** | proposal §7 recipes read parsed fields |

- **Proposed, no audit impact:** `Include_Tag_Key Off` on the tier-2 output; `Remove_key stream`. Keep `app` only if
  dashboards want it; otherwise drop the `modify Add` entirely (P1 then has nothing to add back).
- **Decision, not a tidy-up:** dropping `_msg` from successfully parsed access lines. The Lua comment keeps it as "the
  only evidence when parsing is wrong". The alternative evidence is `access_log_parse_error` (lines that fail to parse keep
  `_msg`) plus tier 1 (5 days, raw). The raw line also carries the timestamp format and the HTTP version, which are not parsed.

### P7 — report rows

- 67 rows per window; `_msg` is **25.5 %** of the bytes (resource rows 26.2 %, summary 25.5 %). It is a sentence
  built from the fields on the same doc.
- The envelope is 31.6 %, of which `app` + `level` are constants.
- **Proposed:** `_msg` on `summary` only; drop `app`/`level` from all rows.
- At 1800 s windows the report is small in absolute terms (48 windows/day), so this matters mostly for 365-day retention,
  which the Monitoring team now sizes.
- Needs a Lua change with a `SCHEMA_VERSION` bump (a field disappears), and `SCHEMA-report.md`.

### P8 — mappings

- `polaris-logs-template.json` declares 7 typed fields and leaves every other string to dynamic mapping, on purpose (queries
  use `.keyword`). `polaris-report-template.json` does the same for strings.
- Dynamic strings become `text` (analysed, positions) **plus** `keyword` (`ignore_above` 256), so each string is indexed twice:
  `_msg`, `api_path`, `user_principal_name`, `loggerName`, `resource`, `window_start`, …
- **Proposed shape:** categorical → `keyword` only, keeping a `.keyword` alias or updating the few queries; `client_ip` →
  `ip`; `_msg` → `text` only (no keyword; nobody runs terms on 1 KB strings); report `_msg` → `index: false`.
- **Measure first (M5):** `_cat/indices/polaris-*?v&h=index,docs.count,store.size` and `_stats/fielddata`. Without a size
  number this stays a proposal.

### P9 — readouts

| | today | proposed |
|---|---|---|
| how | Dev Tools queries, copy the response panel, upload | `bash logging/scripts/step10-v4-window-readout.sh <window_start>` → `.scratch/readout-*/` |
| format | not JSON (`"""` strings), needs `devtools-json-fix.py`, whitespace lost inside strings | exact JSON from curl |
| window cut | by hand, on the label; the tick skew `#26` is ignored | from the summary row's emit time (`#26` built in) |
| tier 1 | usually missing, so step11 cannot run | always included |
| this session | 3 round trips for 2 windows, one export from the wrong index | 1 command per window |

### P10 — is the old pipeline still running?

`CLAUDE.md` still lists `fb-polaris-shipper` (Deployment, Polaris PVC → VictoriaLogs), and `PLAN-opensearch-cutover-2026-09-08.md`
says to uninstall it after the cutover. Nothing since records either state. `polaris/values.yaml` sets
`QUARKUS_LOG_FILE_JSON_ENABLED=true` next to `logging.file.enabled: false`; which one wins on the running pod is `#5`'s
open question. If the shipper runs, the same logs are written twice by Polaris, read twice and stored twice (VictoriaLogs).
**Ask:** `helm list -A | grep -i shipper` and `kubectl -n datahub-hynix exec deploy/benchmarks-polaris -- ls -la /deployments/logs`.
Uninstall is a destructive command: explicit OK at the time of running.

### P11 — scripts and docs

Scripts that describe finished or superseded work:

| script | written for | status |
|---|---|---|
| `step0-preflight.sh` | cutover v4 step 1 (2026-09-08) | done |
| `step4-report-readout.sh` | "why is polaris-logs empty", VictoriaLogs comparison | superseded by step10 |
| `step5-probe-apply-verify.sh` | helm-then-restart trap `#20` (2026-09-09) | superseded by step2/step3 + chart `checksum/config` |
| `step6-tier2-readout.sh` | multiline fault probe (2026-09-09) | done |
| `step7-dedup-check.sh` | `#16` vs `#18` | settled |
| `step8-subset-proof.sh` | tier 2 ⊆ tier 1 under policy v3 | done (still runnable) |
| `test-polaris-filters.py` | the shipper's Lua inside `logging/fb-values.yaml` | tests a script that is not deployed here |

Live: step2, step3, step9, step10, step11, step12, `test-schema-v3/v4/v5`, `test-first-tick`, `test-raw-access-shim`,
`devtools-json-fix.py`. The numbers no longer mean an order, so renaming them to what they do (`render-gate`, `postupgrade`,
`window-readout`, `replay-window`, …) is optional and touches every doc that cites them. **Recommendation: move, don't rename.**

Docs: the current set is `PROPOSAL-…ko.md`, `SCHEMA-report.md`, the two REVIEWs, the latest HANDOFF and PLAN-audit-log-todo.
The architecture spec (2026-09-03) describes the PVC → VictoriaLogs design, and `POLARIS-LOGGING-GUIDE.ko.md` (09-07)
predates OpenSearch. A `logging/README.md` index says so in one place instead of editing 20 headers.

---

## 3. Reviewed and deliberately kept

| item | why it stays |
|---|---|
| **Two tails of the same Polaris file** (tier 1 and tier 2) instead of one tail + `rewrite_tag` | With one tail, a tier-1 backlog (memory buffer, `Mem_Buf_Limit` 50 MB, OpenSearch slow) **pauses the shared input and stalls tier 2 too**. Separate tails isolate the audit stream. The cost is a second read of a page-cached file and a second JSON decode per line. `rewrite_tag` would also re-emit through an internal emitter with its own buffer |
| Report tick as a `dummy` input every 5 s | 17,280 Lua calls/day of a one-key record. The 5 s interval bounds the window label skew (`#26`) |
| `multiline.parser docker, cri` on tier 2 | Measured: `cri` alone left the parser with nothing (2026-09-09). `docker` rejoins lines the runtime split at 16 KB. Largest Polaris line in the export 6.8 KB (an ERROR with a stack trace) |
| `Skip_Long_Lines On` (default `Buffer_Max_Size` 32 KB) | The runtime splits log content at 16 KB before the tail sees it, so a single file line stays well under 32 KB. It could only bite on quote-dense content whose JSON escaping doubles it. Low; known |
| `Generate_ID On` on tier 2/3 | makes a retried chunk idempotent at the cost of one hash per record |
| `Flush 5` | the report window is 30 s now and 1800 s in production; 5 s latency is irrelevant to both |
| The Lua | reviewed and refactored separately (`#31`): one filter, ~2.8× less Lua time, start-up records counted |
| Polaris log level and application-line volume | a lever at the source (15:01Z window: 365 of 720 Polaris records were application lines, 155 of them dropped by the Lua after full parsing), but **Polaris is not changed from here** (standing rule); phase 3.7 |

---

## 4. Measurements to run (read-only, Kade)

```bash
NS=datahub-hynix; POD=$(kubectl -n $NS get pods -l app.kubernetes.io/instance=benchmarks-fluent-bit -o jsonpath='{.items[0].metadata.name}')
# M1  P2: does 5.1.1 still skip-and-log every Polaris record on OUTPUT 1?
kubectl -n $NS logs "$POD" -c fluent-bit --since=10m | grep -c 'unsafe Id_Key'
# M2  P3: how much of k8s-logs is Fluent Bit writing about itself? (field name assumes dynamic mapping of kubernetes.*)
curl -sk -u "$OS_USER:$OS_PASSWORD" "$OS_URL/k8s-logs-*/_count" -H 'Content-Type: application/json' \
  -d '{"query":{"bool":{"filter":[{"range":{"@timestamp":{"gte":"now-1h"}}},{"wildcard":{"kubernetes.pod_name.keyword":"benchmarks-fluent-bit-*"}}]}}}'
# M3  P4: do the three parser filters ever find a `log` key?
curl -sk -u "$OS_USER:$OS_PASSWORD" "$OS_URL/k8s-logs-*/_count" -H 'Content-Type: application/json' \
  -d '{"query":{"bool":{"filter":[{"range":{"@timestamp":{"gte":"now-24h"}}},{"exists":{"field":"log"}},{"wildcard":{"kubernetes.pod_name.keyword":"*polaris*"}}]}}}'
curl -sk -u "$OS_USER:$OS_PASSWORD" "$OS_URL/k8s-logs-*/_count" -H 'Content-Type: application/json' \
  -d '{"query":{"bool":{"filter":[{"range":{"@timestamp":{"gte":"now-24h"}}},{"exists":{"field":"log"}},{"wildcard":{"kubernetes.pod_name.keyword":"*datahub*"}}]}}}'
# M4  P10: is the old pipeline still there?
helm list -A | grep -i -E 'shipper|victoria'
# M5  P8/P6/P7: what the indices actually cost
curl -sk -u "$OS_USER:$OS_PASSWORD" "$OS_URL/_cat/indices/polaris-*,k8s-logs-*?v&h=index,docs.count,store.size,pri.store.size&s=index"
# Readout for any window (P9)
bash logging/scripts/step10-v4-window-readout.sh <window_start> && python3 logging/scripts/step11-replay-window.py .scratch/readout-<…>
```
