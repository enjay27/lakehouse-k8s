# PLAN — three faults in `benchmarks-fluent-bit`, one file, one release

**Status: PROPOSED. Nothing has been changed.** Plan-first per CLAUDE.md; this needs explicit
approval before any edit. All three touch `fluent-bit/values.yaml` and the same release, so they
are presented together — but they are **separately approvable and should be separately committed**.

Evidence for all three: [`sessions/2026-09-09-stdout-not-equivalent`](../.memory/sessions/2026-09-09-stdout-not-equivalent.md),
issues [#16-#19](../.memory/active-issues.md).

---

## Fault A — the tier 2/3 CRI unwrap never parses (blocks the cutover)

**Measured.** `polaris_cri_unwrap` processes 5,030 records, drops 0, adds 0, and the byte delta to
the next filter is exactly 12.00 B/record — the cost of `Add app polaris` alone, proving
`Rename message _msg` and `Rename timestamp _time` both found nothing. The Polaris JSON stays a
string in `log`, `loggerName` never becomes a field, `access_seen` reads 0 against 270 real
access-log lines, and policy v3 keeps 100% of records.

**Cause, by elimination.** Filter present and correctly ordered in the *rendered* ConfigMap;
parser present in the *loaded* `custom_parsers.conf` with `Time_Keep On`; mount resolves; payload
is valid JSON; neighbouring filters execute. `polaris_stdout_json` is the only parser in this
deployment that must resolve a `Time_Key` — `polaris_json` and `polaris_text` are no-ops behind
`Merge_Log`/`Keep_Log Off`, and `datahub_json` has no `Time_Key`. The remaining suspect is
`%L` against the nine fractional digits in `.697818537Z`.

### The change

```diff
     [PARSER]
         Name        polaris_stdout_json
         Format      json
-        Time_Key    timestamp
-        Time_Format %Y-%m-%dT%H:%M:%S.%L%z
-        Time_Keep   On
```

**Why removal rather than a corrected format.** `Time_Keep On` exists only so `timestamp` survives
for filter 1's rename. With no `Time_Key` at all, `timestamp` is never consumed — same outcome,
one fewer thing to fail, and no guess about `%L`'s digit handling. `_time` still arrives as a
string, which the Lua replay detector requires.

**Blast radius: tier 2/3 only.** `polaris_stdout_json` has exactly one consumer,
`polaris_cri_unwrap`, `Match polaris.logs`. Tier 1 uses `polaris_json`, untouched.

**What it cannot regress.** `@timestamp` on tier 2/3 already comes from the CRI envelope, not the
payload — the stored doc reads `05:07:07.704Z` against a payload `05:07:07.697818537Z`, 7 ms
apart, precisely because the parse has been failing. Removing the time key changes nothing there.

### Gate — and it must be able to fail

```bash
curl -sk -u "$OS_USER:$OS_PASSWORD" -H 'Content-Type: application/json' \
  "$OS_URL/polaris-logs-*/_search?pretty" -d '{"size":0,"aggs":{
    "has_logger":{"filter":{"exists":{"field":"loggerName"}}},
    "has_raw_log":{"filter":{"exists":{"field":"log"}}}}}'
```
PASS = documents indexed **after** the restart carry `loggerName` and no `log`. Restrict the query
by `@timestamp` to after the rollout or the 5,030 existing raw docs will mask the result — that
masking is exactly how this fault survived the step-2 and step-3 gates.

Then re-run the notebook and `step4-report-readout.sh`: **stdout `access_seen` should equal the
file's for matched windows.** That is the §3 measurement, and it still expires with the shipper.

---

## Fault B — `#18`, `Id_Key sequence` drops every record it was meant to dedup

`[output:opensearch:opensearch.0] the value of sequence is not string` -> `skipping record with
missing or unsafe Id_Key value`, continuously. Polaris emits `sequence` as a JSON integer; the
plugin requires a string. OUTPUT 1 indexes nothing; records survive only because OUTPUT 2
(`Match kube.*`, `Generate_ID On`) catches the same tag. So upsert-by-sequence has never operated
and a retried chunk yields duplicates.

**Options, in preference order.** (1) Delete OUTPUT 1 and let OUTPUT 2 own the tag — honest, since
that is the de facto behaviour today; loses an intended dedup that has never worked. (2) Keep
OUTPUT 1 and coerce `sequence` to a string for that path only. **Not** by adding `sequence` to a
`type_int_key`-style list — that forces the opposite type. Needs a Lua or `modify` step, i.e. new
config on tier 1, which the cutover deliberately avoided.

**Recommendation: decide, do not default.** This is a design question about whether tier 1 wants
dedup at all, and it is not blocking the cutover. Answering it inside this plan would be guessing
at intent.

---

## Fault C — `#19`, tier 1 is discarding chunks right now

```
[warn ] [http_client] cannot increase buffer: current=512000 requested=544768 max=512000
[warn ] [output:opensearch:opensearch.1] http_do=-1 URI=/_bulk
[error] [engine] chunk '...' cannot be retried
```
Four chunks unretryable in ~90 s. The `_bulk` **response** exceeds the plugin's read buffer, the
flush fails, `Retry_Limit 3` exhausts, the chunk is dropped. Unacknowledged loss, invisible to
document-count gates because most chunks still succeed.

### The change

```diff
     [OUTPUT]
         Name                opensearch
         Match               kube.*
         ...
+        Buffer_Size         False
```
`False` removes the cap on the response buffer. Apply to OUTPUT 2 first — it is the one erroring.
OUTPUT 1 and the tier 2/3 outputs can take it in the same edit; the setting bounds a read buffer,
not memory the pipeline holds.

**Blast radius: tier 1's node-wide sink.** This is the release's highest-volume path and the one
the cutover promised not to disturb, so it deserves its own rollout and its own gate.

### Gate
`kubectl -n datahub-hynix logs ds/benchmarks-fluent-bit --since=10m | grep -cE 'cannot increase buffer|cannot be retried'`
must be **0** over a window that previously produced them. Record the pre-change count first —
a gate with no baseline cannot fail.

---

## Sequencing

1. **A alone**, its own commit and rollout. It is the cutover blocker and its gate is unambiguous.
2. **C next**, separately — different subsystem, different gate, and mixing it with A makes a
   crashloop ambiguous.
3. **B last**, and only after Kade decides what tier 1 dedup should do.
4. Only then the cutover's remaining steps: the `access_seen` equality re-measurement, then
   step 7, then the 1800/30 revert as the final gate.

**Standing: `fb-polaris-shipper` stays installed throughout.** Until A is fixed and the
re-measurement passes, the file path is the only one that recognises an access-log line.

## Not verifiable from a Cowork session
No `helm lint`, no `--dry-run`, no cluster reach. Every figure here is Kade's pasted output. The
DoD render gate has to run on his host before any of this is applied.
