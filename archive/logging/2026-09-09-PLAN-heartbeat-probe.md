# PLAN — a heartbeat pipeline that isolates the parser from Polaris entirely

**Status: PROPOSED. Nothing changed.** Plan-first. Supersedes further blind iteration on the
tier 2/3 chain: build the smallest pipeline that can reproduce the fault with a *known* input,
then add the Polaris logic back one layer at a time.

## Why a bare heartbeat is not enough

Transport, auth, TLS, `${OS_PASSWORD}` expansion and the OpenSearch plugin are **already proven**
— `polaris-logs-*` holds 5,030 docs and `polaris-report-*` is receiving, both through this same
release, host and credential. A tick carrying `{"tick":"..."}` would be indexed whatever is wrong
with the parser, so it would confirm only what is already known. *A gate that cannot fail is not
a gate.*

The probe therefore ships **two** ticks on one pipeline:

| tag | payload | what it proves |
|---|---|---|
| `heartbeat.raw` | a flat object | transport baseline. Expected to pass; it is the control. |
| `heartbeat.parse` | **a CRI-shaped record: the Polaris JSON as a string under `log`** | whether `parser` + `polaris_stdout_json` transforms a known-good input |

`heartbeat.parse` is the experiment. It feeds the parser the exact shape the real records have,
from a source that has nothing to do with the tail input, the CRI multiline parser, Polaris, or
its traffic. **Both outcomes are informative:**

- the stored doc has **`loggerName` as a field** -> the parser filter works. The fault is then in
  what the real records look like when they reach it — the tail/CRI layer — not the parser, and
  the entire investigation moves off the parser for good.
- the stored doc still has **`log` as a string** -> the parser filter is inert in this build, now
  reproduced in ~15 lines with no Polaris dependency. That is a filable upstream reproducer and it
  ends the guessing.

Note this runs against the parser **as committed at `4788294`** — `Name` + `Format json`, no
`Time_Key`. So it also retro-tests Fault A's fix without waiting on Polaris traffic.

## The change — additive only, `fluent-bit/values.yaml`

Tags are `heartbeat.*`. **No existing `Match` catches them**: tier 1 uses `kube.*`, tier 2
`polaris.logs`, tier 3 `polaris.report`, and `polaris_noise_filter` uses `polaris.*`. Nothing
existing is modified.

### `config.inputs` — append

```
    # ══ HEARTBEAT PROBE — isolates the parser from Polaris. REMOVE when done. ══
    [INPUT]
        Name              dummy
        Alias             hb_raw_tick
        Tag               heartbeat.raw
        Dummy             {"probe":"raw"}
        Rate              1
        Interval_Sec      30

    # Same shape the tail produces for Polaris: the JSON as a STRING under `log`.
    # Nine fractional digits and a literal Z are deliberate -- that is the payload
    # the real records carry.
    [INPUT]
        Name              dummy
        Alias             hb_parse_tick
        Tag               heartbeat.parse
        Dummy             {"probe":"parse","log":"{\"timestamp\":\"2026-09-09T05:07:07.697818537Z\",\"loggerName\":\"io.quarkus.http.access-log\",\"level\":\"INFO\",\"message\":\"probe\"}"}
        Rate              1
        Interval_Sec      30
```

### `config.filters` — append, AFTER every existing filter

```
    [FILTER]
        Name          parser
        Alias         hb_parse_probe
        Match         heartbeat.parse
        Key_Name      log
        Parser        polaris_stdout_json
        Reserve_Data  On
```

### `config.outputs` — append

```
    [OUTPUT]
        Name                opensearch
        Match               heartbeat.*
        Host                192.168.194.1
        Port                9200
        HTTP_User           ${OS_USER}
        HTTP_Passwd         ${OS_PASSWORD}
        Logstash_Format     On
        Logstash_Prefix     fb-heartbeat
        Logstash_DateFormat %Y.%m.%d
        Include_Tag_Key     On
        Tag_Key             flb_tag
        Retry_Limit         3
        tls                 On
        tls.verify          Off
        Suppress_Type_Name  On
        Generate_ID         On
        Trace_Error         On
```

## Blast radius, honestly

- **Volume: 2 records / 30 s.** Nothing.
- **The real risk is a config syntax error**, because this pod also does node-wide collection — a
  bad render crashloops tier 1 with it. The `Dummy` line's nested escaping is the fragile part.
  `--dry-run=client --debug` before applying, and watch the pod through the restart.
- **`Interval_Sec 30` here is unrelated to `WINDOW_SECONDS`.** It is a probe cadence, not a report
  period, and it does not touch the temporary 5 s report tick or the pending 1800/30 revert.
- **Removal is deleting three blocks.** Nothing else references these tags.

## Verification

```bash
curl -sk -u "$OS_USER:$OS_PASSWORD" "$OS_URL/_cat/indices/fb-heartbeat-*?v"

curl -sk -u "$OS_USER:$OS_PASSWORD" -H 'Content-Type: application/json' \
  "$OS_URL/fb-heartbeat-*/_search?pretty" -d '{"size":0,"aggs":{
    "by_tag":{"terms":{"field":"flb_tag.keyword"},
      "aggs":{"parsed":{"filter":{"exists":{"field":"loggerName"}}},
              "raw":{"filter":{"exists":{"field":"log"}}}}}}}'
```

PASS for the control: `heartbeat.raw` docs exist. PASS for the experiment: `heartbeat.parse` docs
show `parsed` > 0 and `raw` == 0. Anything else is the second branch above, and it is a result,
not a setback.

Also re-read the filter metrics — `hb_parse_probe` is its own alias, so its record and byte counts
are attributable:

```bash
curl -s localhost:2021/api/v1/metrics | jq '.filter | {hb_parse_probe, polaris_cri_unwrap}'
```

## Then, and only then — stage 2

Once the probe says which layer is at fault, add the Polaris summarization logic back **onto the
heartbeat tag** rather than onto live traffic: point `polaris_access_log` and
`polaris_noise_filter` at `heartbeat.parse` in a copy, and confirm `access_seen` increments on a
record we control. That tests the Lua against a known input with a known expected count — which
no run so far has done, because every run measured Polaris traffic nobody had counted by hand.

## Not verifiable from a Cowork session
No `helm lint`, no `--dry-run`, no cluster reach. The render gate runs on the host.
