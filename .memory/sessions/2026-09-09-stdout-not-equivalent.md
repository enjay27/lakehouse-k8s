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
