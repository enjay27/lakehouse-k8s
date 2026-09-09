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
