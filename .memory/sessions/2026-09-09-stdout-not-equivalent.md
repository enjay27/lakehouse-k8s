# 2026-09-09 — stdout is NOT equivalent to the log file, and tier 2 is storing everything

**§3 of `logging/HANDOFF-notebook-run-2026-09-09.md` is answered. The answer is no.**
Kade ran the `polaris-learning` notebook ~05:07Z and the readout immediately after, while both
sinks still held the windows. This is the measurement that expires; it has now been taken.

## The number

Same `window_start` on both sides, which is what makes it a measurement rather than two
unrelated figures:

| window_start | file-sourced (shipper -> VictoriaLogs) | stdout-sourced (DaemonSet -> OpenSearch) |
|---|---|---|
| `2026-09-09T05:07:00Z` | `access_seen` **226**, kept 99 | **0** |
| `2026-09-09T05:07:30Z` | `access_seen` **44**, kept 33 | **0** |
| every other window in range | 0 | 0 |

**270 access-log lines on the file path, 0 on the stdout path.** That is row 2 of the handoff's
verdict table: stdout is not reaching the filter as access-log records.

`polaris-report-*` went 56 -> 74 docs, so the report stream itself was healthy throughout.

## The part that makes the naive reading wrong

`polaris-logs-2026.09.09` **now exists: 4,718 docs, 2.7 MB.** It was absent from `_cat/indices`
at 04:57Z and appeared during the same run that reported `access_seen 0`.

So "stdout is not reaching the filter" is too strong and would send the next session hunting the
wrong fault. Records reach the chain, pass the Lua, reach the output and get indexed. What fails
is **recognition**: both entry points test `record["loggerName"] ~= ACCESS_LOGGER` where
`ACCESS_LOGGER = "io.quarkus.http.access-log"` (`fluent-bit/values.yaml:127`, checked at :134 and
:613). Not one of ~4,718 records satisfied it.

**Consequence, and it is live right now:** policy v3 is **inert on tier 2**. Every record is
falling through the keep path unfiltered. The 30d "policy-v3 filtered" tier is storing the raw
firehose — 4,718 documents for roughly 270 requests — while every health check stays green. This
is the §7 pattern again: a plausible wrong number, not an error. It also means the ~4,718 figure
is not a stable baseline; it grows with any traffic until this is fixed.

## What is NOT the cause — each checked in the values file this session

The obvious file-level suspects are all clear, which is why the answer has to come from the
running object:

- **The CRI unwrap filter exists.** `[FILTER] Name parser`, `Alias polaris_cri_unwrap`,
  `Match polaris.logs`, `Key_Name log`, `Parser polaris_stdout_json`.
- **The parser is loaded.** `Parsers_File /fluent-bit/etc/conf/custom_parsers.conf` is in the
  `[SERVICE]` block — trap 3.1 was closed and CONFIRMED FROM THE RENDER on 2026-09-09. This is
  not a repeat of `2f51378`.
- **`Time_Keep On` IS present** on `polaris_stdout_json`. Its own comment says it is mandatory;
  an earlier read of this session claimed it missing and that was a truncation artifact, not a
  finding. Recorded because it is exactly the sort of thing that gets filed as a fault twice.
- **The Lua is byte-identical between the two releases** — sha `aa180e90b9f69bda` — so the
  recognition constant cannot differ between them. The difference is in the RECORDS, not the code.

## The decisive query — run this first, everything else is downstream of it

One document settles it:

```bash
curl -sk -u "$OS_USER:$OS_PASSWORD" "$OS_URL/polaris-logs-*/_search?size=1&pretty"
```

Read it as:

- a surviving **`log`** field holding a JSON *string*, and no `loggerName` -> the unwrap did not
  run on these records despite being configured. Then compare the `[FILTER]` order in
  `kubectl -n datahub-hynix get cm benchmarks-fluent-bit -o yaml` against the values file.
- **`loggerName` present but some other value** -> Polaris's console formatter names the logger
  differently from its file formatter. Then `ACCESS_LOGGER` is what is wrong, not the plumbing.
- `loggerName` == `io.quarkus.http.access-log` present and correct -> the records are fine and
  the Lua instance is not seeing them; look at filter ordering and `Match` scoping.

Then the field census and the pod log:

```bash
curl -sk -u "$OS_USER:$OS_PASSWORD" -H 'Content-Type: application/json' \
  "$OS_URL/polaris-logs-*/_search?pretty" -d '{"size":0,"aggs":{
    "has_log":{"filter":{"exists":{"field":"log"}}},
    "has_logger":{"filter":{"exists":{"field":"loggerName"}}},
    "has_msg":{"filter":{"exists":{"field":"_msg"}}}}}'

kubectl -n datahub-hynix logs ds/benchmarks-fluent-bit --tail=300 \
  | grep -iE '\[error\]|\[warn\]|parser|trace|reject'
```

## Standing consequences

- **Do NOT uninstall `fb-polaris-shipper`.** The file path is now the only one that recognises an
  access-log line. The fallback is fully specified in git at `fb91949`.
- **Cutover step 7 (porting the notebook to `_search`) is blocked.** Porting it now would point
  the harness at a tier that is not applying the policy it claims to apply.
- The 30s window revert to 1800/30 remains the cutover's last step, and is now behind this.

NOT VERIFIED from this session: no cluster reach — no `kubectl`, `helm`, or sink access. Every
cluster figure above is Kade's pasted output read back. The values-file checks ARE this session's
own work, read from the repo at `45159f7`.

---

## RESOLVED to a single filter: `polaris_cri_unwrap` is inert. Its neighbours are not.

A document out of `polaris-logs-*` (`_id 940EFA1E…`, `@timestamp 05:07:07.704Z`) settles which of
the three readings applies. It is reading one: **the CRI envelope was never unwrapped.**

```json
{"@timestamp":"2026-09-09T05:07:07.704Z","flb_tag":"polaris.logs","stream":"stdout",
 "app":"polaris",
 "log":"{\"timestamp\":\"2026-09-09T05:07:07.697818537Z\",\"sequence\":49687,
        \"loggerName\":\"org.apache.polaris.service.catalog.api.IcebergRestOAuth2Api\",
        \"level\":\"DEBUG\",\"message\":\"operation=getToken …\", …}\n"}
```

**The Polaris JSON is intact — inside `log`, as a string.** `loggerName` exists in the payload and
does not exist as a field. That is why `record["loggerName"]` is nil, why `access_seen` stayed 0
against 270 real access-log lines, and why every record took the keep path.

### The filters either side of it DID run — so this is one filter, not the chain

- `app: "polaris"` is present -> filter 1 `polaris_key_rename` ran. Its `Rename message _msg` and
  `Rename timestamp _time` no-opped, because those keys are inside the string, not on the record.
- `logtag` and `time` are absent -> filter 4 `polaris_field_trim` ran (`Remove_key logtag`,
  `Remove_key time`).
- `stream: "stdout"` survives -> the CRI envelope is otherwise untouched.

Filter 0 sits between two filters that demonstrably executed, matched the right tag
(`flb_tag: polaris.logs` is exactly its `Match`), and did nothing.

### What that rules out, and what it leaves

The filter's own definition is correct — `Name parser`, `Match polaris.logs`, `Key_Name log`,
`Parser polaris_stdout_json`, **`Reserve_Data On`**. And `Reserve_Data On` is the tell: on a
SUCCESSFUL parse the merged keys appear and `log` is consumed; on a FAILED parse the record passes
through untouched, exactly as observed. So the filter is installed and running, and its parse is
failing (or its parser resolves to nothing) on every record.

Note the trap 3.1 render evidence in `PLAN-opensearch-cutover` §3.1 was taken against the
**`fb-polaris-shipper-fluent-bit`** ConfigMap — the SHIPPER's. It was never re-taken for
`benchmarks-fluent-bit`. `fluent-bit/values.yaml:676` does declare the absolute
`Parsers_File /fluent-bit/etc/conf/custom_parsers.conf`, but that is intent; the DaemonSet's
deployed ConfigMap has not been read. **Verify against the running object.**

### Next command — read the parser Fluent Bit actually loads, not the one we wrote

```bash
kubectl -n datahub-hynix exec ds/benchmarks-fluent-bit -- \
  sh -c 'sed -n "/polaris_stdout_json/,/^$/p" /fluent-bit/etc/conf/custom_parsers.conf'
kubectl -n datahub-hynix logs ds/benchmarks-fluent-bit --tail=400 \
  | grep -iE 'parser|\[error\]|\[warn\]'
```

- parser block **absent or missing `Time_Keep On`** -> the ConfigMap does not carry what the values
  file says. That is trap 3.1 recurring on the release it was never checked on.
- parser block **present and correct** -> it is registered and the parse itself fails. The next
  suspect is the time spec against this payload: `Time_Format %Y-%m-%dT%H:%M:%S.%L%z` against
  `2026-09-09T05:07:07.697818537Z` — **nine** fractional digits and a literal `Z`. Tier 1's
  `polaris_json` carries the identical spec, so whether tier 1's own records are parsed or equally
  raw is then the discriminating question, and it is one query away.

Do not change anything until one of those two is established. Both fixes are small and they are
different fixes.

### One more measured fact

The index grew **4,718 -> 5,030 docs between two commands minutes apart, with no notebook
traffic** — Polaris logs `DEBUG` to stdout continuously. #16 is not a burst that has passed; it
accumulates.

### The image is distroless — `exec` is not a diagnostic here

`kubectl exec ds/benchmarks-fluent-bit -- sh` returns exit 127, `"sh": executable file not
found in $PATH`. `cr.fluentbit.io/fluent/fluent-bit` ships no shell and no coreutils, so `cat`
and `ls` are equally unavailable. **Never reach for exec on this pod.** Everything needed is in
the API objects and in OpenSearch.

### The discriminator that needs neither exec nor a ConfigMap read

`polaris_json` (tier 1) and `polaris_stdout_json` (tier 2/3) live in the **same**
`custom_parsers.conf`. So tier 1's own stored records say whether that file is loaded at all:

```bash
curl -sk -u "$OS_USER:$OS_PASSWORD" -H 'Content-Type: application/json' \
  "$OS_URL/k8s-logs-*/_search?pretty" -d '{"size":0,"aggs":{
    "has_logger":{"filter":{"exists":{"field":"loggerName"}}},
    "has_raw_log":{"filter":{"exists":{"field":"log"}}}}}'
```

- **`has_logger` > 0** -> `custom_parsers.conf` IS loaded and `polaris_json` works. The fault is
  then specific to `polaris_stdout_json` — its block, or its time spec against nine fractional
  digits and a literal `Z`.
- **`has_logger` == 0 and `has_raw_log` == everything** -> the parsers file is not loaded for this
  release, every `parser` filter in it is inert, and **tier 1 has never been parsed either** —
  its ~23k docs/10m are raw CRI envelopes. That would make trap 3.1 a live fault on
  `benchmarks-fluent-bit`, not a closed one, and it would predate the cutover entirely.

The second outcome is the larger finding, and nothing measured so far excludes it: "`k8s-logs`
still taking ~23k docs/10m" counts documents, and a raw envelope is a document.

Direct reads of the deployed config, for after that:

```bash
kubectl -n datahub-hynix get cm benchmarks-fluent-bit -o json | jq -r '.data | keys'
kubectl -n datahub-hynix get cm benchmarks-fluent-bit -o json \
  | jq -r '.data["custom_parsers.conf"]'
kubectl -n datahub-hynix get ds benchmarks-fluent-bit \
  -o jsonpath='{.spec.template.spec.containers[0].volumeMounts}' | jq
kubectl -n datahub-hynix logs ds/benchmarks-fluent-bit --tail=400 | grep -iE 'parser|error|warn'
```

The ConfigMap and the DaemonSet spec together answer both halves of trap 3.1 — whether the file
carries the parser, and whether it is mounted where `[SERVICE]` looks for it.

---

## Trap 3.1 is CLOSED on this release. I was wrong to reopen it.

The deployed `benchmarks-fluent-bit` ConfigMap carries `custom_parsers.conf` with
`polaris_stdout_json` **including `Time_Keep On`**, and `volumeMounts` puts the `config` volume at
`/fluent-bit/etc/conf` — so `[SERVICE] Parsers_File /fluent-bit/etc/conf/custom_parsers.conf`
resolves to a real file containing the parser. The previous commit suspected trap 3.1 had
recurred on the release it was never checked on. It has not. Read from the running objects,
which is what should have happened before the suspicion was recorded.

## And the time spec is exonerated too — by tier 1's own numbers

`k8s-logs-*`: `has_logger` **2,617,097**, `has_raw_log` **21,455,617**. Records with a real
`loggerName` field exist in bulk, so Polaris's nine-fractional-digit, `Z`-suffixed timestamp is
being handled somewhere in this very pod. `%Y-%m-%dT%H:%M:%S.%L%z` is not the fault.

**But those two numbers do NOT prove `polaris_json` works**, and reading them that way would be
the third wrong turn in a row. The tier 1 chain begins with:

```
[FILTER] Name kubernetes  Match kube.*  Merge_Log On  Keep_Log Off
```

**`Merge_Log On` parses the `log` JSON and merges it into the record itself; `Keep_Log Off` then
removes `log`.** That is where tier 1's `loggerName` comes from. By the time the downstream
`parser`/`polaris_json` filter runs there is no `log` key left for it to act on — it is a no-op.
So tier 1 proves the *payload* parses; it says nothing about either custom parser.

**The tier 2/3 chain has no `kubernetes` filter** — deliberately, it matches `polaris.*` only.
So it is the sole consumer of `polaris_stdout_json`, and the only chain whose JSON unwrap is not
being done for it by `Merge_Log`. That is exactly the chain that fails.

## What is still unread — and it is now the only artifact left

The rendered **`fluent-bit.conf`** from the same ConfigMap. Everything about the tier 2/3 filter
block so far comes from the values file, which is intent:

```bash
kubectl -n datahub-hynix get cm benchmarks-fluent-bit -o json \
  | jq -r '.data["fluent-bit.conf"]' | sed -n '/TIER 2\/3/,/OUTPUT/p'
```

Confirm `polaris_cri_unwrap` is present, that it precedes `polaris_key_rename`, and that
`Key_Name log` / `Parser polaris_stdout_json` / `Reserve_Data On` survived rendering. The stored
document proves the filters either side of it ran; only the rendered config can say whether the
unwrap is in the file at all.

Also worth one query, since `Merge_Log` is now known to be the thing that works: whether adding a
`kubernetes` filter is even the right fix, or whether the right fix is to stop hand-rolling the
unwrap and reuse the mechanism tier 1 already proves.

---

## The rendered config is byte-for-byte the intent. Every file-level suspect is now dead.

`.data["fluent-bit.conf"]` from the deployed ConfigMap carries the TIER 2/3 block exactly as
`fluent-bit/values.yaml` writes it: `polaris_cri_unwrap` present, **first** in the block, before
`polaris_key_rename`, with `Match polaris.logs`, `Key_Name log`, `Parser polaris_stdout_json`,
`Reserve_Data On`. Order is intact. The parser it names is in the loaded `custom_parsers.conf`
with `Time_Keep On`. The mount resolves. The filters either side of it demonstrably execute on
this tag. The payload is valid JSON.

**So the configuration is correct and the behaviour is still wrong.** Everything that can be
settled from an artifact has been settled. What is left is runtime.

## Correction: I exonerated the time format on bad reasoning

`ffb0e53` said `%Y-%m-%dT%H:%M:%S.%L%z` was cleared because 2.6M tier 1 docs carry `loggerName`.
In the same commit I established that **`Merge_Log` produces those**, not `polaris_json`. Both
statements are in one message and they contradict each other. `Merge_Log` does no `Time_Key`
handling at all, so it exonerates the JSON payload and says nothing whatever about the time spec.

Follow that through and the correlation is tight:

- `polaris_json` — no-op. `Merge_Log`/`Keep_Log Off` deletes `log` before it runs.
- `polaris_text` — no-op on JSON input, and downstream of the same deletion.
- `datahub_json` — has **no `Time_Key`**.
- `polaris_stdout_json` — the ONLY parser in this deployment that must actually resolve a
  `Time_Key`, and the only one failing.

**No parser with `Time_Format %Y-%m-%dT%H:%M:%S.%L%z` has ever been shown to succeed in this
pod.** The suspect is back, and specifically: `%L` against **nine** fractional digits in
`.697818537Z`. If `%L` consumes only three, `%z` is handed `818537Z` and the time lookup fails.

## The one cheap experiment that splits the remaining space, no config change

Fluent Bit's own metrics say whether the filter is even seeing records:

```bash
kubectl -n datahub-hynix port-forward ds/benchmarks-fluent-bit 2021:2020
curl -s localhost:2021/api/v1/metrics | jq '.filter'
```

- `polaris_cri_unwrap` shows **records processed** -> it runs and the parse fails. The time spec
  is then the leading candidate and the fix is a `Time_Format` that matches nanoseconds, or
  dropping `Time_Key` from this parser and letting filter 1's `Rename timestamp _time` do the
  work `Time_Keep On` was added to enable.
- `polaris_cri_unwrap` shows **nothing** -> it is not receiving records despite matching the tag,
  and the question becomes a Fluent Bit 5.1.1 behaviour change in the `parser` filter — the
  release went 3.2.2 -> 5.1.1 on 2026-09-09 04:21 and this chain has never run on any other build.

Note the second branch has a claim behind it worth stating plainly: **the tier 2/3 chain has never
worked on any version.** It was introduced by this cutover. There is no "it used to parse"
baseline, so a 5.1.1 regression and a config that never worked look identical from here.

## What would have caught this

Nothing in the step-2 or step-3 gates asserted that a stored tier 2 record has a `loggerName`
field. The gates counted documents, checked the Lua sha, and read the pod log for complaints —
all of which pass while every record arrives unparsed. One `exists` query on a stored document,
run once after the cutover, would have caught it in the first minute.

---

## CONFIRMED by the filter metrics: the unwrap runs on every record and transforms none

```
polaris_cri_unwrap    records 5030   drop 0   bytes 10,268,413
polaris_key_rename    records 5030   drop 0   bytes 10,328,773
polaris_access_log    records 5030   drop 0   bytes 10,328,773
polaris_noise_filter  records 5917   drop 739 bytes 10,454,781
polaris_field_trim    records 5030   drop 0   bytes 10,168,343
```

`records 5030` on the unwrap equals the `polaris-logs-*` doc count exactly. It is receiving
everything. `drop_records 0`, `add_records 0`. **Branch one: it runs, and the parse fails on all
5,030.** With `Reserve_Data On` a failed parse passes the record through untouched, which is what
the stored document shows.

### The byte deltas prove the renames no-opped, which proves no fields were produced

- unwrap -> rename: **+60,360 bytes over 5,030 records = exactly 12.00 B/record.** That is the
  msgpack cost of `Add app polaris` and nothing else.
- If the unwrap had produced fields, `Rename message _msg` (+1 B) and `Rename timestamp _time`
  (9 chars -> 5, -4 B) would also have fired, giving **9 B/record**, not 12.00.
  The figure is 12.00 to the byte. **Neither rename found its key**, so `message` and `timestamp`
  did not exist on the record — the JSON was never unpacked.
- rename -> access_log: **delta 0**. The Lua returned every record unmodified, exactly as
  `loggerName == nil` requires.
- rename -> field_trim: **-160,430 B = -31.9 B/record**, i.e. `logtag` and `time` removed. The CRI
  envelope fields were present all along and filter 4 did its job. The chain works; one filter in
  it is inert.

### And it confirms #16 independently of the index count

`polaris_noise_filter` shows `records 5917` = 5,030 logs + 887 ticks, `drop_records 739` = ticks
that did not turn a window over (887 - 739 = 148 report records emitted, ~148 windows, consistent
with a 30s window over the pod's life). **Not one LOG record was dropped.** Policy v3 kept 100% of
them, measured at the filter rather than inferred from storage.

## The fix, and why it is also the diagnostic

`polaris_stdout_json` is the only parser here that resolves a `Time_Key`, and it is the only one
failing. Removing `Time_Key`/`Time_Format` from it removes the sole remaining failure mode and
**loses nothing**:

- `Time_Keep On` exists solely so `timestamp` survives for filter 1's `Rename timestamp _time`.
  With no `Time_Key` at all, `timestamp` is never consumed — same outcome, one fewer thing to fail.
- `_time` still arrives as a **string**, which is what the Lua replay detector requires.
- The record's Fluent Bit timestamp then comes from the CRI envelope's `time`. **This is already
  what happens**: the stored doc's `@timestamp` is `05:07:07.704Z` against a payload `timestamp`
  of `05:07:07.697818537Z` — 7 ms apart, because the parse has been failing all along. So this
  changes nothing about `@timestamp` and cannot regress tier 2/3 time indexing.

The alternative — keeping `Time_Key` and correcting `Time_Format` for nine fractional digits — is
a guess about `%L`'s digit handling that would need its own run to confirm. Prefer the change that
removes the failure mode over the one that tries to satisfy it.

---

## THE PARSER WORKS. Measured, to the byte.

`hb_parse_probe`: **3 records, 390 bytes = 130.0 B/record.** Model the two possible outputs of
that filter on the known probe payload (msgpack, v2+ framing `[[ts_ext, metadata], body]` = 13 B):

| outcome | body | + frame | |
|---|---|---|---|
| **RAW** — parse failed, `log` kept as a 121-char string | 140 | **153** | |
| **PARSED** — `log` consumed, 4 fields merged, `probe` reserved | 117 | **130** | **measured 130** |

Exact. `polaris_stdout_json` parses a CRI-shaped record carrying nine fractional digits and a
literal `Z`, and produces `loggerName` as a field. **The parser filter is not the fault, the
parser definition is not the fault, and the time key never was** — Fault A's removal was harmless
but it was not the cure.

This is the first thing in this investigation measured against a payload whose expected output was
known in advance rather than inferred from live traffic.

## So the fault is in what the real records carry — and it is one character

The real chain is still failing: `polaris_cri_unwrap` reads **2042.2 B/record** after the fix
against **2041.4 B/record** before it. Unchanged. Compare the probe payload against the stored
Polaris document, which is the only place the two differ:

```
probe  "log":"{\"timestamp\":...,\"message\":\"probe\"}"      -> PARSES (130 B/rec)
real   "log":"{\"timestamp\":...,\"processId\":1}\n"           -> does not
                                                        ^^ trailing newline
```

The tail's CRI multiline parser keeps the line terminator inside `log`. Everything else about the
two payloads is the same shape.

**Probe 3 tests exactly that.** `hb_parse_nl_tick` / `heartbeat.parsenl` is byte-identical to
probe 2 except for a trailing `\n` on the `log` value, with its own filter alias
`hb_parse_nl_probe` so its bytes are separately attributable.

- probe 3 **does not parse** (≈154 B/record, the raw model + 1) -> the trailing newline is the
  entire fault. Nothing to do with the parser, the time key, Polaris, or the cutover. Fix is to
  strip the terminator before the unwrap.
- probe 3 **parses** (≈131 B/record) -> the newline is innocent and the difference is elsewhere in
  the real record — next suspects are `Skip_Long_Lines` truncation and the `stream`/`logtag`
  envelope keys.

Either way it is decided by one number, and both numbers are predicted in advance.

---

## The delta is in, and it is 12.00 to the hundredth. Same instance, both results.

Full filter map, one read, one Fluent Bit process:

```
polaris_cri_unwrap  4993 rec  10,196,501 B
polaris_key_rename  4993 rec  10,256,417 B   delta  +59,916 =  12.00 B/rec
polaris_access_log  4993 rec  10,256,417 B   delta        0 =   0.00 B/rec
polaris_field_trim  4993 rec  10,097,219 B   delta -159,198 = -31.88 B/rec
hb_parse_probe         9 rec       1,170 B                  = 130.0  B/rec
```

Predicted in advance: a **working** unwrap gives 9.00 B/rec (`app` +12, `message`->`_msg` +1,
`timestamp`->`_time` -4); a **failed** one gives 12.00 (only `app`; both renames find nothing).
The reading is 12.00.

**So in one process, at the same moment: the probe parses (130.0 = the parsed model exactly) and
the real records do not (12.00 = the failed model exactly).** Same filter type, same parser, same
`Reserve_Data On`. The parser is exonerated by direct comparison, not by inference.

`hb_parse_nl_probe` is **absent from the map** — probe 3 is committed but not running. #20 again:
confirm the roll, do not assume it.

## Probe 4, and an honest caution about probe 3

Probe 3's hypothesis has a problem worth stating before it is tested: **the `kubernetes` filter's
`Merge_Log` parses `log` values that also end in `\n`** — that is exactly where tier 1's 2.6M
`loggerName` docs come from. So a trailing newline is not obviously fatal to Fluent Bit's JSON
parsing, and probe 3 may well pass. That is a reason to test it, not to skip it, but do not expect
it to be the answer.

**Probe 4 (`heartbeat.parsereal`) is the stronger test**: the exact `log` value from the stored
Polaris document, verbatim — nested `mdc` object, integer `sequence` and `threadId`, empty-string
`ndc`, absolute `processName`, 13 keys, trailing newline included.

| probe 4 | conclusion |
|---|---|
| **parses** | the record CONTENT is fully exonerated. The fault is in the tail input path itself — how `multiline.parser cri` hands the record to the filter — and no payload experiment will find it. Next: compare the record shape at the input, not the content. |
| **does not parse** | something in the real payload breaks the parser where the synthetic one does not. Bisect it: drop `mdc`, then the integers, then `ndc`. |

Both probes go in one roll. Payloads validated by round-tripping the parsed YAML through
`json.loads` twice, asserting the newline is a real terminator, and counting keys (4, 4, 13).

---

## ALL THREE PROBES PARSED. The record content is exonerated, and so is the parser.

Measured against models computed before the read (msgpack, v2+ framing 13 B):

| probe | RAW model | PARSED model | measured | verdict |
|---|---|---|---|---|
| `hb_parse_probe` (synthetic, no newline) | 153 | **130** | **130** | PARSED |
| `hb_parse_nl_probe` (+ trailing newline) | 157 | **133** | **133** | PARSED |
| `hb_parse_real_probe` (**verbatim real payload**) | 615 | **553** | **553** | PARSED |

Every one exact. So, definitively **not** the fault:

- the parser filter, and `polaris_stdout_json`'s definition;
- the time key — Fault A's removal was harmless, and never the cure;
- **the trailing newline.** My probe-3 hypothesis was wrong, exactly as the `Merge_Log` counter-
  argument predicted. Recorded as wrong rather than quietly dropped;
- the payload's shape: nested `mdc` object, integer `sequence`/`threadId`, empty-string `ndc`,
  58- and 62-character values, 13 keys. The verbatim record parses.

The eliminations are now total on the content side. **The one thing every passing probe shares is
its source: `dummy`. The one thing the failing records share is theirs: `tail`.**

## Probe 5 — one variable, real data

Same files the tier 2 input tails, same parser filter, differing in exactly one thing:
`multiline.parser docker, cri` instead of `cri`. That is also the only structural difference
between tier 1's input — whose `log` values `Merge_Log` unwraps 2.6M times successfully — and
tier 2's, whose `log` values the parser filter will not touch.

`hb_tail_probe` is otherwise identical to `polaris_cri_unwrap`: same `Key_Name`, same parser, same
`Reserve_Data On`. So a difference in outcome is attributable to the **input**, and nothing else.

- **parses** -> the `cri` multiline parser is the fault and the fix is one word in the tier 2 input.
- **does not parse** -> the fault is `tail` + a `parser` filter generally, not the multiline
  choice. Then stop hand-rolling the unwrap and use the mechanism that demonstrably works on these
  records in this pod — the `kubernetes` filter's `Merge_Log`.

Read it the same way as the real chain, since it now sees the same records: the `hb_tail_probe`
byte delta, not its absolute size.

**VOLUME WARNING:** probe 5 tails every Polaris line into `fb-heartbeat-*`, ~5k records/hour. It is
short-lived. It has its own `DB /var/log/flb_hb_tail.db` — sharing tier 2's would corrupt both
offset stores (verified unique: `flb_kube.db`, `flb_polaris.db`, `flb_hb_tail.db`).

## Also from this run

`step5-probe-apply-verify.sh` worked: the ConfigMap check and the process check both passed on the
same run, and REVISION 5 is the first upgrade this session that is provably *running*. Step 7 read
`0 B over 0 rec` because the pod had just restarted and no Polaris traffic had arrived within the
40s settle — expected, not a failure. Re-read the delta after traffic.

---

## The byte-model method is now validated against ground truth

Two independent readings of the same three probes, and they agree completely:

| tag | docs | `loggerName` | `log` | byte model said |
|---|---|---|---|---|
| `heartbeat.parse` | 44 | **44** | 0 | 130 = PARSED |
| `heartbeat.parsenl` | 19 | **19** | 0 | 133 = PARSED |
| `heartbeat.parsereal` | 19 | **19** | 0 | 553 = PARSED |
| `heartbeat.raw` | 44 | 0 | 0 | control, no `log` key at all |

Every parsed record carries `loggerName` as a field and **no `log`** — the parser consumed it, as
`Reserve_Data On` does on success. This is not another restatement of the same finding: it is a
*different instrument* agreeing with the byte arithmetic on all three cases.

That matters because **the whole diagnosis rests on that arithmetic.** The claim that the real
chain fails is the 12.00 vs 9.00 B/record delta and nothing else. Until now the model had never
been checked against an independent ground truth; now it has been, three times, exactly. The
method can be trusted for the reading that counts.

`heartbeat.raw` showing `log=0` is the control behaving: its payload has no `log` key, so neither
column should light up, and neither does.

## Still blocked on one thing: Polaris is idle

`heartbeat.tail` has **0 docs**, `hb_tail_probe` 0 records, `polaris_cri_unwrap` 0 records. No
Polaris output since the REVISION 6 restart. Probe 5 reads only new lines (fresh DB,
`Read_from_Head` off), so it cannot report until Polaris logs something.

This also settles the earlier question about background volume: **Polaris is genuinely idle when
nothing is calling it.** The probe-5 volume warning (~5k records/hour) applies only under load,
and `3436e5f`'s "logs DEBUG continuously" is now definitively wrong — corrected in `696baef` and
confirmed here by a third empty window.

**One notebook run now yields three things at once:** probe 5's verdict, a re-confirmation of the
real chain's delta on fresh records, and traffic for the §3 stdout-vs-file measurement. Run the
notebook, then `step6-probe-readout.sh` — no config change, no roll.

---

# ROOT CAUSE. `multiline.parser cri` alone; `docker, cri` works.

Probe 5, on real traffic:

```
heartbeat.tail      4,314 docs   loggerName=4,314   log=0     PARSED, every record
hb_tail_probe       4,622 rec    [multiline.parser docker, cri]
polaris_cri_unwrap  4,925 rec    [multiline.parser cri]       delta 12.00 B/rec -- FAILING
```

**Same files. Same parser (`polaris_stdout_json`). Same filter type, same `Key_Name log`, same
`Reserve_Data On`. Same process, same moment. One line different, and it decides everything.**

Tier 1 has always used `docker, cri`, which is why `Merge_Log` has been unwrapping those records
successfully for months while tier 2 — introduced by this cutover with `cri` alone — never once
parsed a record.

**The mechanism is NOT established.** `docker, cri` fixes it on 4,314 of 4,314 records; *why* the
`cri` multiline parser produces a `log` value the `parser` filter declines to touch is unknown,
and nothing here should be read as explaining it. Recorded as an open question rather than
back-filled with a plausible story.

## The fix, applied

`fluent-bit/values.yaml`, tier 2/3 tail input: `multiline.parser cri` -> `multiline.parser
docker, cri`. Verified: YAML parses, and all three real `multiline.parser` directive lines in the
file now read `docker, cri`.

## READING A WAS WRONG, AND WOULD HAVE INVERTED THE CONCLUSION

The ratio heuristic printed `ratio 1.015` under a legend saying *"<1.0 by ~10% => probe 5
PARSED"*. **Probe 5 had parsed. Reading A said it had not.** Taken alone it would have sent the
next step in exactly the wrong direction — the week's signature failure, one more time, in an
instrument I built two commits ago.

Why it was invalid, having thought about it only after it disagreed:

1. **The two inputs do not produce the same envelope.** `docker, cri` and `cri` emit different
   surrounding fields, so their per-record byte totals were never comparable in the first place.
   The ratio assumed a difference that had a second cause.
2. **The samples are different.** 4,622 records against 4,925, over different windows, on
   variable-length records. Averages across unequal populations are not a controlled comparison.
3. **The ~10% figure came from the dummy probes**, whose records carry a single extra key. A tail
   record carries `stream`, `logtag`, `time` and a much longer payload, so the parsed/raw ratio
   there was never going to be 0.9.

Reading B — `loggerName` present, `log` consumed — needed no model, no assumption about envelopes,
and no matched samples. It was right.

**The lesson, and it is the same one the pipeline keeps teaching:** an instrument that requires a
model of what it is measuring inherits every error in that model. Reading B measured the thing
itself. `696baef` said to trust B if the two ever disagreed — that instruction is the only reason
this was caught in one step instead of several, and it was written before there was any reason to
think it would be needed.

Note this does **not** undermine the 12.00-vs-9.00 delta. That one compares two filters *in the
same chain, on the same records, in the same process* — the difference is one filter's own effect,
with no cross-population assumption. It was independently confirmed by reading B on the probes.
The ratio test was a different, weaker construction that should not have been given a verdict line.

## Next

1. Apply and roll: `bash logging/scripts/step5-probe-apply-verify.sh --apply`.
2. Then traffic, then `step6-probe-readout.sh`. **The gate is `unwrap -> rename = 9.00 B/rec`**,
   and `polaris-logs-*` documents indexed after the roll carrying `loggerName`.
3. Then, and only then, the §3 re-measurement: stdout `access_seen` should finally equal the
   file's on matched windows. `fb-polaris-shipper` stays installed until it does.
4. Then remove all five probes — they are scaffolding, and probe 5 duplicates tier 2's tail.

---

## The fix is working — and my "9.00" gate value was arithmetic I got wrong

After the roll, on 3,703 records:

```
unwrap -> rename = 6.98 B/rec      (was 12.00, stable across several reads on ~5,000 records)
hb_tail_probe      3703 rec  2360.8 B/rec
polaris_cri_unwrap 3703 rec  2360.8 B/rec   <- IDENTICAL, to the tenth
```

**The two are now byte-identical because they are now the same pipeline** — same files, same
multiline parser, same parser filter. That equality is itself a check: two independent tails of the
same source agreeing exactly is what a working, deterministic chain looks like.

### Where 6.98 comes from, and why 9.00 was never right

`polaris_key_rename` does three things per record:

| | |
|---|---|
| `Add app polaris` | `app` (1+3) + `polaris` (1+7) = **+12** |
| `Rename message _msg` | key `message` 8 B -> `_msg` 5 B = **-3** |
| `Rename timestamp _time` | key `timestamp` 10 B -> `_time` 6 B = **-4** |
| subtotal | **+5** |

msgpack maps: `fixmap` holds ≤15 entries in a 1-byte header; 16+ needs `map16`, 3 bytes. A parsed
record sitting at 15 entries crosses to 16 when `app` is added: **+2**. So a *working* delta is
**5.00 or 7.00** depending on the record's key count. Measured **6.98** — the working value, with
a ~0.3% residue from records of other shapes.

**I had published 9.00**, in the step5/step6 legends and in several commits, from writing
`message -> _msg` as **+1** when it is **-3**. Wrong number, and it was the stated PASS criterion.
Had the delta landed on 9.00 I would have called a broken chain fixed.

What survives untouched: **12.00 as the FAILING value.** That is `app` alone with neither rename
firing, it needs no key-count assumption, and it is what the entire diagnosis rested on. It was
also confirmed independently by reading B. The error was in the pass threshold, not the fail one.

### Two instrument corrections in two commits

`35c5e5b` retired the ratio heuristic's verdict after it read `1.015` on a chain that had parsed
4,314 of 4,314. This one corrects the delta legend. Both were gates I wrote, both stated a
threshold more confidently than the arithmetic behind them, and in both cases the instrument that
needed no model — reading B, the stored documents — was right. `step6` now carries no verdict on
the ratio at all and the delta legend reads `12.00 = FAILING; 5.00-7.00 = working`.

### READING C added — the gate this script never had

`step6` checked `fb-heartbeat-*` and never once looked at `polaris-logs-*`, the index the whole
cutover exists to fill. It now splits that index by time rather than filtering it, because the
~5,000 pre-fix raw documents share it and would mask the result:

```
older     -> expected to stay raw. That is correct, not a failure.
last_10m  -> PASS = loggerName > 0 and log == 0
```

Only reading C settles tier 2. The delta says the renames fire; reading C says the documents
landed parsed.

### Still open

1. Reading C on `polaris-logs-*` — the actual gate.
2. The §3 re-measurement: stdout `access_seen` vs the file's, on matched windows.
   `fb-polaris-shipper` stays installed until they agree.
3. Remove all five probes. Probe 5 now duplicates tier 2's tail exactly — the identical 2360.8
   B/rec proves it — so it is pure duplicate load and its `fb-heartbeat-*` writes are waste.
4. `#18`, `#19` untouched. Then the 1800/30 revert as the cutover's final gate.

---

## Reading C: tier 2 IS parsing. The mixed bucket is the roll, not a partial failure.

```
older     24,873 docs   loggerName=0       log=24,873
last_10m   9,333 docs   loggerName=4,403   log=4,930
```

`4,403 + 4,930 = 9,333` **exactly**. Every document carries one key or the other — none has both,
none has neither. That is a clean bimodal split, which is the signature of a **cutover instant**;
a partial failure would scatter, with some records parsed and some not for reasons unrelated to
time. The 10-minute window simply straddles the roll.

Corroborated from the other side: `polaris_cri_unwrap` has processed **4,542 records since the
restart** at a **6.97 B/rec** delta, and the parsed bucket holds **4,403 documents**. Those are the
same records. **The parsed half is the post-roll half.**

`older` staying 100% raw is correct and permanent — those 24,873 documents predate the fix and
nothing rewrites them. They age out under the 30d policy.

So tier 2 now: parses, applies policy v3, and stores `loggerName` as a field. Three independent
instruments agree — the delta (6.97, working), reading B (`heartbeat.tail` 9,169/9,169), and
reading C's post-roll bucket.

### Two script defects fixed

1. **A shell bug in my own gate.** The PASS line used backticks inside a double-quoted `echo`, so
   the shell tried to execute `older` and printed `line 75: older: command not found`. Harmless to
   the measurement, but it corrupted the one line that tells the reader how to interpret the
   output. Removed.
2. **A single 10-minute bucket cannot distinguish a transition from a partial failure** — it just
   showed "mixed" and left the reader to guess, which is the failure mode this whole exercise keeps
   hitting. Reading C now splits into four buckets (`>10m`, `10-5m`, `5-2m`, `<2m`) so the
   transition is *visible* rather than inferred, and the instruction is to read the newest bucket
   only.

### Now genuinely open

1. **Re-run reading C** and confirm the newest bucket is `loggerName>0, log=0`. Expected to pass —
   but it has not been read yet, and this session has been wrong about a confident expectation
   before.
2. The **§3 re-measurement**. Stdout `access_seen` should now equal the file's on matched windows.
   `fb-polaris-shipper` stays installed until it does. This is the measurement that expires.
3. **Remove all five probes.** Probe 5 is now an exact duplicate of tier 2's tail — identical
   record counts and identical B/rec, twice over — so it is pure duplicate read load and its
   `fb-heartbeat-*` writes are waste.
4. `#18`, `#19`, then the 1800/30 revert as the cutover's final gate.
