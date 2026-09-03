# Active Infrastructure State

**Index, not the record.** Current state below; everything else is a link into
[`.memory/`](.memory/README.md).

## Now — 2026-09-03

**Live thread: the Polaris → VictoriaLogs pipeline**, built against Kade's design doc, filed
at `logging/polaris-logging-architecture-spec.md`. What to do next:
[`roadmap.md`](.memory/roadmap.md). The audit and its three corrections:
[`sessions/2026-09-03-polaris-vlogs-audit.md`](.memory/sessions/2026-09-03-polaris-vlogs-audit.md).

**It runs, and the repo half-describes it.** `logging/fb-values.yaml` is **reconciled** —
it matched live revision 10 of `fb-polaris-shipper` bar one line. **`polaris/values.yaml` is
not**: it says file logging and the access log are off, and carries `logging.mdc: {}`, while
the file is written, access-log lines arrive and `mdc.requestId` / `mdc.realmId` are on every
record. Run `helm -n datahub-hynix get values benchmarks-polaris` **before editing it**, or
the edit reverts what is running. `polaris-shared-logs-pvc` is mounted by both releases and
created by no manifest here. ([`active-issues.md`](.memory/active-issues.md) #5.)

**Built:** access-log field extraction — a Lua filter inline in `fb-values.yaml` (no `--set`;
the values file is the definition), gated on `loggerName`, emitting the spec's §7 field
names. `logging/scripts/test-access-log-parser.py` reads the Lua *out of the values file*, so
tests cannot drift from what ships. 6/6.

**Next faults, all confirmed live** (#5b): tail has no `DB` with `Read_from_Head true`
(restart replays from byte 0) and `Skip_Long_Lines Off` (a long line stops the tail);
per-record waste (`date` duplicates `_time`, `processName` on every line); no `%D`, so §7's
P99 panels cannot exist. DEBUG SQL volume is closed — Kade is disabling DEBUG in production.
Also open: a committed plaintext OpenSearch password (#4); VictoriaLogs sized from the doc's
140M/day column, no disk cap, unauthenticated `LoadBalancer` on 9428 (#7).

**The rule, and it cuts both ways:** verify against the running object, never the values file
— when *reading* as much as writing. A rendered view is not the object (**a `_stream` is not
a field list, a histogram bucket is not a clock**), and a claim about "the repo" needs
evidence about the repo, not about one file in it.

## Where the detail is

| read | when |
|---|---|
| [`.memory/environments.md`](.memory/environments.md) | **before running anything** — context, namespaces, ports, and the no-cluster-reach constraint on Cowork sessions |
| [`.memory/active-issues.md`](.memory/active-issues.md) | before trusting a value or a runbook (6 open, 2 resolved-but-instructive) |
| [`.memory/roadmap.md`](.memory/roadmap.md) | what is next, and the PostgreSQL verification assertions |
| [`.memory/repository-map.md`](.memory/repository-map.md) | looking for where something lives, or which duplicate values file is current |
| [`.memory/goal.md`](.memory/goal.md) | the standing objective and the structural model |
| [`.memory/sessions/`](.memory/sessions/) | why a decision was made, including the wrong turns |
| [`.memory/completed.md`](.memory/completed.md) | finished structural work |

## Rules for keeping this file useful

- **This file stays under ~40 lines.** Growth belongs in `.memory/`, not here. A
  tracking document nobody finishes reading tracks nothing.
- **Update *Now* every session**, even when the answer is "unchanged".
- **A fact with a number goes in `.memory/roadmap.md`; the story goes in
  `.memory/sessions/`.** Configuration that is written but not applied goes in
  `.memory/active-issues.md` — in this repo that distinction is the whole game.
