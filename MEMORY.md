# Active Infrastructure State

**Index, not the record.** Only what would be *false* the moment it goes stale lives here;
everything else is a link into [`.memory/`](.memory/README.md).

## Now — 2026-09-09

**The cutover is DEPLOYED and tier 1 survived it.** `benchmarks-fluent-bit` now runs all three
tiers on Fluent Bit **5.1.1** (chart 0.57.6, no chart bump): `k8s-logs` 5d unfiltered,
`polaris-logs-*` 30d policy-v3 filtered from **stdout**, `polaris-report-*` 365d schema-v2 rows.
Rollout clean, 0 restarts, no filter complaints, deployed Lua sha `aa180e90b9f69bda` matches the
repo, **`k8s-logs` still taking ~23k docs/10m**, and `polaris-report-*` is receiving — which alone
proves the tick, the noise-filter Lua, the report output and `${OS_PASSWORD}` expansion.
Plan and gates: [`PLAN-opensearch-cutover`](logging/PLAN-opensearch-cutover-2026-09-08.md).

**§3 IS ANSWERED, AND THE ANSWER IS NO. Do not uninstall `fb-polaris-shipper`.** Notebook run
2026-09-09 ~05:07Z, the same two windows on both sides: file-sourced (shipper -> VictoriaLogs)
**`05:07:00Z` seen 226 / kept 99, `05:07:30Z` seen 44 / kept 33**; stdout-sourced (DaemonSet ->
OpenSearch) **0 in both**. 270 access-log lines to 0. The measurement is valid — same
`window_start`, one side non-zero — and it stops existing the moment the shipper goes.

**But the naive reading of that is wrong**, and this is the finding: `polaris-logs-2026.09.09`
now exists with **4,718 docs / 2.7 MB**, created during the very run that reported `access_seen 0`.
Records reach the chain and the output fine. **Not one of ~4,718 was recognised as an access-log
line**, i.e. `loggerName ~= "io.quarkus.http.access-log"` on the stdout path. So policy v3 is
**inert on tier 2**: the 30d "filtered" tier is currently storing the raw firehose — 4,718 docs
for ~270 requests — and it looks healthy doing it. **Cause is NOT in the values file**: the
`polaris_cri_unwrap` filter, `Parsers_File custom_parsers.conf` and `Time_Keep On` are all
present and were each checked. Only the running object can say. Diagnosis and the decisive
queries: [`sessions/2026-09-09-stdout-not-equivalent`](.memory/sessions/2026-09-09-stdout-not-equivalent.md).

**ROOT CAUSE FOUND: `multiline.parser cri` alone. `docker, cri` works.** Probe 5 tailed the SAME
FILES with the SAME parser filter and only that line different: **4,314 of 4,314 records parsed**
(`loggerName` a field, `log` consumed) while the real chain sat at the failing 12.00 B/rec delta —
same process, same moment. Tier 1 has always used `docker, cri`, which is why `Merge_Log` worked
there for months. **Mechanism unknown; measurement unambiguous.** Fix applied to the tier 2 input,
**not yet deployed**. Gate: `unwrap -> rename = 9.00 B/rec`.

**Superseded (kept so it is not re-derived):** `polaris_cri_unwrap` processed all
5,030 records, dropped 0, transformed 0 — the byte delta to the next filter is exactly
**12.00 B/record**, the cost of `Add app polaris` alone, so both renames found nothing and the
JSON was never unpacked. `Time_Key`/`Time_Format`/`Time_Keep` are now **removed** from
`polaris_stdout_json` (the only parser here that had to resolve a time key, and the only one
failing). **The next action is `helm upgrade` + the gate**, both in
[`PLAN-tier2-parse-fault`](logging/PLAN-tier2-parse-fault-2026-09-09.md) §A — and the gate query
**must be restricted to docs indexed after the rollout**, or 5,030 existing raw docs mask it.

**The gate FAILED on first read — `has_logger 0`, `has_raw_log 4994` — but it is NOT known
whether the upgrade had run**, so that is not yet evidence against the fix. Next flow is a
**heartbeat probe** ([`PLAN-heartbeat-probe`](logging/PLAN-heartbeat-probe-2026-09-09.md), written
into the values file, not deployed): two dummy ticks every 30s on `heartbeat.*`, one flat control
and one feeding `polaris_stdout_json` a CRI-shaped record. It splits "parser filter is broken"
from "the real records do not look like we think" **without Polaris in the path**, and it retests
Fault A without waiting for traffic. Prefer its filter-metrics gate — byte delta on
`hb_parse_probe` — over doc counts, which old records mask.

**Cutover step 7 and the shipper uninstall stay BLOCKED** until the re-measured `access_seen`
matches. The PVC path stays; the fallback is specified at `fb91949`. Two more live tier 1 faults
found in the same pod log and NOT touched — `#18` `Id_Key sequence` drops every record it should
dedup, `#19` `_bulk` responses exceed the output buffer and chunks are discarded.

**Still written and NOT running:** the temporary **30s window** (`Interval_Sec 5`). It stays until
everything else is done; the revert to 1800/30 is the plan's **last step and its final gate**
(§4.1), and tier 3's long ISM policy is blocked on it.

**Standing, and all three outrank inference.** Polaris is not to be changed. **Verify against the
running object, never an intent artifact.** And **a gate that cannot fail is not a gate** — this
week that cut both ways: one gate was built so it could only pass, two more fire on a *correct*
config, and several count something `grep -c` cannot count (the whole Lua renders as ONE line).

## Where the detail is

| read | when |
|---|---|
| [`.memory/environments.md`](.memory/environments.md) | **before running anything** — context, namespaces, ports, and the no-cluster-reach constraint on Cowork sessions |
| [`.memory/active-issues.md`](.memory/active-issues.md) | before trusting a value or a runbook |
| [`.memory/roadmap.md`](.memory/roadmap.md) | what is next, and the PostgreSQL verification assertions |
| [`.memory/repository-map.md`](.memory/repository-map.md) | looking for where something lives, or which duplicate values file is current |
| [`.memory/goal.md`](.memory/goal.md) | the standing objective and the structural model |
| [`.memory/sessions/`](.memory/sessions/) | why a decision was made, including the wrong turns |
| [`.memory/completed.md`](.memory/completed.md) | finished structural work |
| `logging/polaris-logging-architecture-spec.md` | the design the log pipeline is being built against, and its §7 LogsQL recipes |

## Rules for keeping this file useful

- **Under ~40 lines.** It reached 80 by accumulating,each session, a digest of findings
  already filed in `.memory/`. **A paragraph summarising a file that exists does not belong
  here.** *Now* carries what is next and what is written but not running; nothing else.
- **Update *Now* every session**, even when the answer is "unchanged".
- **A fact with a number goes in `.memory/roadmap.md`; the story goes in
  `.memory/sessions/`.** Configuration that is written but not applied goes in
  `.memory/active-issues.md` — in this repo that distinction is the whole game.
