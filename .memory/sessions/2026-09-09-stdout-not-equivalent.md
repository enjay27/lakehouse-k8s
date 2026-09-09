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
