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

**Open: `polaris-logs-*` is empty.** Not "wait a window" — the report arrived through the same
filter instance and the same credential. Either Polaris is idle (it only logs on requests) or
stdout does not carry what the file carries. **The report answers it itself**: `access_seen`
counts what the filter SAW, before any keep/drop.
`logging/scripts/step4-report-readout.sh` reads it and says which.

**The next action is a notebook run in `polaris-learning`, handed off in
[`HANDOFF-notebook-run`](logging/HANDOFF-notebook-run-2026-09-09.md) — run it UNCHANGED; porting
it to `_search` is step 7 and doing it first destroys the measurement below.**

**Do this before uninstalling `fb-polaris-shipper` — it cannot be measured afterwards.** Both
releases are running the same filter over the same traffic from two sources: the shipper from the
log FILE into VictoriaLogs, the DaemonSet from STDOUT into OpenSearch. Equal `access_seen` for one
window is the proof that stdout carries the same access-log set as the file — the question every
earlier revision of this plan had to leave open.

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
