# PLAN — `#19`: the `_bulk` **response** overflows the read buffer, and the chunk is discarded

**Applied to `fluent-bit/values.yaml`, NOT deployed.** Roll with
`logging/scripts/step5-probe-apply-verify.sh --apply`.

## What is happening

Fluent Bit batches records into a chunk and POSTs them to `_bulk`. OpenSearch replies with **one
status entry per record**, so the reply grows with the batch. Fluent Bit reads that reply into a
buffer capped by the output's `Buffer_Size`, which the plugin defaults to 512 KB.

```
[warn ] [http_client] cannot increase buffer: current=512000 requested=544768 max=512000
[warn ] [output:opensearch:opensearch.1] http_do=-1 URI=/_bulk
[error] [engine] chunk '1-1788930438.635329228.flb' cannot be retried
```

544,768 bytes against a 512,000 cap. Unable to read the reply, the plugin reports the call failed —
**even though OpenSearch may have indexed every record**. It cannot tell; it never read the answer.

It then retries. Same batch, same reply size, same failure: **deterministic, so retrying cannot
help.** After `Retry_Limit 3` the chunk is discarded. Four chunks in ~90 seconds on 2026-09-09.

**It is the response that is too large, not the request.** That is why nothing about the request
path looks wrong.

## What it costs — and it is not simply "loss"

- If OpenSearch **did** index the batch, the retries wrote it **again**. Tier 1 has **no dedup at
  all** (`#18`, measured — `Id_Key sequence` drops every record, so only OUTPUT 2 stores anything
  and `Generate_ID On` mints a fresh `_id` per attempt). Up to 3 duplicate copies per failing chunk.
- If it **did not**, the records are gone when the chunk is dropped.

Nothing distinguishes the two after the fact. **`#18` and `#19` compose:** a retry storm in a
pipeline with no idempotency is exactly the duplicate-generating machine `#16` feared, arriving by
a different route than `#16` proposed.

**Only under load.** Small batches produce small replies. This is why `k8s-logs` doc counts kept
rising, why no gate caught it, and why the 2026-09-09 `sequence` ratio came back a clean 1.000 —
that window was quiet. **A ratio measured while idle cannot see this.**

## The change

`Buffer_Size False` on **all four** OpenSearch outputs, placed with `Retry_Limit`:

```diff
         Retry_Limit         3
+        # Caps the buffer used to read the _bulk RESPONSE, not the request. The
+        # response carries one status entry per record, so it grows with the batch;
+        # the plugin default of 512 KB was being exceeded under load (#19).
+        # False = unlimited, bounded in practice by the chunk size.
+        Buffer_Size         False
```

**Why all four rather than only the one that erred.** `opensearch.1` (OUTPUT 2) is where the
overflow was observed, but the cap is a plugin default that applies identically everywhere, and
tier 2 now carries real volume — 4,403 documents in one burst. Fixing only the output that has
failed *so far* leaves the same landmine on the paths that have not yet been pushed. The setting
bounds a read buffer, not pipeline memory, and the reply is bounded by the chunk size regardless.

**Not** a bulk-size reduction: that would keep replies under the cap by making batches smaller,
treating the symptom and costing throughput.

## Blast radius

Tier 1's node-wide sink is the release's highest-volume path and the one the cutover promised not
to disturb. This is a one-line-per-output addition with no effect on routing, formatting or
retention. The pod also does node-wide collection, so a render error crashloops tier 1 — dry-run
first, which `step5` does before it will upgrade.

## Gate — and it needs a baseline or it cannot fail

**Record the failure count BEFORE, under comparable load.** The errors only appear under load, so a
zero taken while idle proves nothing and would pass on a completely unfixed release.

```bash
# BEFORE: run the notebook, then
kubectl -n datahub-hynix logs ds/benchmarks-fluent-bit --since=10m \
  | grep -cE 'cannot increase buffer|cannot be retried'
```

Apply, roll, then repeat **with the notebook run again** so the load is comparable. PASS = the
count drops to 0 over a window that previously produced a non-zero count. A zero against an
unrecorded or idle baseline is not a pass.

Second, cheaper check — the plugin's own retry counters should stop climbing:

```bash
curl -s localhost:2021/api/v1/metrics | jq '.output'
```

## Not verifiable from a Cowork session
No `helm lint`, no `--dry-run`, no cluster reach. `step5-probe-apply-verify.sh --apply` runs the
render gate, confirms the ConfigMap, rolls, and confirms the process.
