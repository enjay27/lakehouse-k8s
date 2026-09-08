# Active Infrastructure State

**Index, not the record.** Only what would be *false* the moment it goes stale lives here;
everything else is a link into [`.memory/`](.memory/README.md).

## Now — 2026-09-08

**The task is the Fluent Bit config, and only that** (Kade, scoped 2026-09-08). `fb-polaris-shipper`
stops tailing the Polaris log PVC and tails the **container log** instead — stdout carries the
access-log records, confirmed from `k8s-logs` — and its VictoriaLogs `http` output is replaced by
two `opensearch` outputs: `polaris-logs-*` and `polaris-report-*`. The DaemonSet is untouched, and
**`polaris_access_log.lua` is byte-identical**: no Lua edit anywhere in this change.
Blocks, gates and render greps: [`PLAN-opensearch-cutover`](logging/PLAN-opensearch-cutover-2026-09-08.md).

**Duplicates, mappings, ISM and the query layer are handed off** (plan §6) — but note the one
sequencing item that is still ours: revert the **30s window** to 1800/30 **before** the long
retention policy is applied, or ~138k report docs/day against ~2.3k is baked in for a year.

**Five of the eight traps in that config fail silently** — `customParsers` is written and never
loaded; without `Time_Keep On` the parser eats `timestamp`, `_time` never exists and filter 3's
replay detector skips without erroring; renaming the tag without the INPUT that *defines* it drops
the whole log stream while reports keep flowing; a second `@timestamp` is rejected per-item inside
an HTTP 200; an undefined `${OS_USER}` expands to empty and 401s past every render grep. Plan §3.

**Standing, and all three outrank inference.** Polaris is not to be changed. **Verify against the
running object, never an intent artifact.** And **a gate that cannot fail is not a gate.**

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
