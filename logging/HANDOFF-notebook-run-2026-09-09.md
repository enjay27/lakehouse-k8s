# HANDOFF — run the log-coverage notebook UNCHANGED. It is the last chance to prove stdout carries what the file carries.

**Written 2026-09-09 from `local-k8s`, for whoever runs `polaris-learning/log-coverage`.**
Read §2 before you touch the notebook and §5 before you touch the cluster.

---

## 1. What changed under you, in sixty seconds

Yesterday there was one Polaris log pipeline. **Today there are two, running the same policy over
the same traffic from two different sources.**

| | source | filter | sink |
|---|---|---|---|
| `fb-polaris-shipper` (Deployment) | the log **file** on `polaris-shared-logs-pvc` | policy v3 | VictoriaLogs |
| `benchmarks-fluent-bit` (DaemonSet) | Polaris **stdout**, `/var/log/containers/*benchmarks-polaris*.log` | **the same policy v3, byte-identical Lua** | OpenSearch `polaris-logs-*` / `polaris-report-*` |

The DaemonSet was upgraded 2026-09-09 04:21 UTC: Fluent Bit **3.2.2 → 5.1.1**, chart 0.57.6 (no
chart bump). Rollout clean, 0 restarts, deployed Lua sha `aa180e90b9f69bda` — identical to the
shipper's. `k8s-logs` kept flowing at ~23k docs/10m, so node-wide collection survived the bump.

**`fb-polaris-shipper` was not touched and is still installed.** That is deliberate and it is the
whole point of this handoff.

Design and gates: [`PLAN-opensearch-cutover`](PLAN-opensearch-cutover-2026-09-08.md), §4.2 for
this run specifically.

---

## 2. Do NOT port the notebook to OpenSearch. Run it exactly as it is.

Everything it touches still exists and still works:

- **VictoriaLogs** — the shipper still writes to it.
- **`fb-polaris-shipper`'s ConfigMap** — cell 0 hashes `logging/fb-values.yaml` and compares it
  against the deployed script. That file was never edited; the gate will pass.
- **that release's metrics port** — `FB_METRICS_URL`, see §4.

Porting the collection layer to `_search` is **step 7** of the cutover plan, and doing it first
would be actively harmful: it throws away the second source that makes §3 possible. Port it after
the shipper is uninstalled, not before.

---

## 3. The measurement — this is the reason you are running it, and it expires

**The open question.** Tier 2 is now sourced from stdout instead of the log file. Nobody has ever
shown that stdout carries the *same* access-log set the file does. Kade's earlier query proved
stdout carries **some** access-log records; it did not prove it carries all of them.

**Why it could not be answered before.** Under a single release, a dual-write sends the *same
post-filter records* to both outputs, so the two figures agree by construction and a partial source
is undetectable. Two releases reading two different sources break that symmetry.

**Why it cannot be answered later.** After `fb-polaris-shipper` is uninstalled the file-sourced
figure stops existing.

**Why it cannot be answered right now.** Polaris is idle. As of 04:41Z both sides report
`access_seen 0` in every window, and `polaris-logs-*` does not exist at all — nothing has ever been
written to it. **`0 == 0` proves nothing.** The notebook is the traffic.

### Do this immediately after the run, while both sinks still hold the windows

```bash
export OS_URL=https://192.168.194.1:9200 OS_USER=admin OS_PASSWORD='...'
export VL_URL=http://192.168.139.2:9428
bash ~/hynix/local-k8s/logging/scripts/step4-report-readout.sh
```

| stdout `access_seen` | file `access_seen` | verdict |
|---|---|---|
| **equal, both > 0** | | **stdout carries the same set as the file.** Question closed; `polaris-logs-*` should now exist |
| **0** | **> 0** | stdout is not reaching the filter. First suspect: the **CRI unwrap** — if `log` is not the payload key, records arrive with no `loggerName`, are never recognised as access-log lines, and `access_seen` stays 0 **while every health check stays green** |
| **> 0 but lower** | **> 0** | stdout is a **partial** view. Keep the PVC path — the fallback is fully specified in git at `fb91949` |
| equal and > 0, but `polaris-logs-*` still empty | | the fault is *after* the filter: a 401 from an unexpanded `${OS_PASSWORD}`, or a per-item rejection inside a bulk that returned HTTP 200. Both appear **only** in the DaemonSet's pod log, via `Trace_Error On` |

---

## 4. What the notebook's own instruments mean now that there are two Fluent Bits

- **`FB_METRICS_URL` must point at the SHIPPER.** Both releases serve metrics on 2020. Forward
  `deploy/fb-polaris-shipper`, not `ds/benchmarks-fluent-bit`, or the drop counters describe the
  wrong pipeline:
  `kubectl -n datahub-hynix port-forward deploy/fb-polaris-shipper 2020:2020`
- **Every drop/keep number the notebook produces is about the shipper**, because it reads
  VictoriaLogs. That is fine and expected — the DaemonSet's side is §3's job, not the matrix's.
- **The policy gate is still meaningful.** Same Lua, same sha, both releases. A PASS there says
  policy v3 is what is running in both.
- **Windows are 30 seconds right now** (`WINDOW_SECONDS 30`, `Interval_Sec 5`), so a run crosses
  boundaries in ~2 minutes instead of ~90. `Policy.window_seconds` is read from the file, so the
  notebook already knows.

---

## 5. Guards — the first two are the notebook's own, the rest are new

- **Do not trip the HPA.** Polaris scales to 3 replicas at 80% CPU, all appending to one log file
  (#8). A replica-count change invalidates the run. Record it before and after.
- **Watch the shipper pod.** A restart mid-run breaks its per-pod dedup invariants.
- **Do not change Polaris configuration** (#11/#12): it works and ships continuously.
- **Do NOT revert the 30s window.** The revert to 1800/30 is the cutover's **last** step and its
  final gate (plan §4.1) — everything else has to be finished first, and tier 3's long ISM policy
  is blocked on it.
- **Do NOT uninstall `fb-polaris-shipper`** until §3 has produced a number with traffic in it.
  That uninstall is destructive of the measurement, not just of the release.
- **Do not edit `logging/fb-values.yaml`.** It must stay byte-identical to the DaemonSet's Lua for
  the two reports to be comparable.

---

## 6. What to send back

1. **`access_seen` from both sides for at least one window that had traffic** — the §3 table.
2. **Whether `polaris-logs-*` now exists**, and its doc count.
   `curl -sk -u ... "$OS_URL/_cat/indices/polaris-*?v"`
3. **The notebook's own coverage matrix outcome**, as usual.
4. Anything in the **DaemonSet's** pod log:
   `kubectl -n datahub-hynix logs ds/benchmarks-fluent-bit --tail=200 | grep -iE '\[error\]|trace|reject'`

Record the outcome in `local-k8s`: a number in `.memory/roadmap.md`, anything not yet trustworthy
in `.memory/active-issues.md`, the blow-by-blow in `.memory/sessions/2026-09-09-<slug>.md`, and
update `MEMORY.md`'s *Now* — index only, under ~40 lines.

---

## 7. One thing this pipeline keeps teaching, worth carrying into the run

Every expensive failure here has been **a plausible wrong number rather than an error**:
`type_int_key` storing `404.0`, #13's filter disabled while everything looked healthy, the harness
merge not summing fields it did not know about. This week added three more — a verification gate
built so it could only pass, two gates that fire on a *correct* config, and several that count
something `grep -c` cannot count, because the whole Lua renders as one line.

So when a number comes back clean, ask what it would have looked like if the thing it measures were
broken. **If the answer is "the same", it is not a measurement.** That is precisely the trap in §3:
both pipelines currently agree perfectly, at zero, and that agreement means nothing at all.
