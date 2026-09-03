# Active Infrastructure State

**Index, not the record.** Current state below; everything else is a link into
[`.memory/`](.memory/README.md).

## Now — 2026-09-03

**Live thread: the Polaris → VictoriaLogs pipeline**, built against Kade's design doc, now
filed at `logging/polaris-logging-architecture-spec.md`. Order of work:
[`roadmap.md`](.memory/roadmap.md) *Next*; the audit and its correction,
[`sessions/2026-09-03-polaris-vlogs-audit.md`](.memory/sessions/2026-09-03-polaris-vlogs-audit.md).

**It runs — and the repo says it cannot.** VMUI shows 1,636 records in 30 minutes, streams
`{app, level}`, with Polaris DEBUG SQL and Quarkus access-log lines. Meanwhile
`polaris/values.yaml` still carries `logging.file.enabled: false`, sets
`quarkus.http.access-log.enabled` nowhere, and mounts a `polaris-shared-logs-pvc` that
nothing in this repo creates. The live release was configured outside these files. **Diff
`helm get values` before editing `polaris/values.yaml`, or the edit reverts what is
deployed** ([`active-issues.md`](.memory/active-issues.md) #5 — which is #1 caught in the act).

**What is actually wrong** (#5b, from raw records — two earlier readings off the *rendered*
VMUI were both wrong): `_time` and `loggerName` are **fine**, as are `mdc.requestId` /
`mdc.realmId`, which make the spec's §7 trace query work today. The real faults are
per-record waste (`date` duplicating `_time`, `processName` on every line) and above all the
**DEBUG SQL from `DatasourceOperations` — ~1.5KB a record, nearly every row, bound parameter
values included.** That is the volume lever here; the spec's Lua dedup targets poll traffic
this cluster does not have. Access log needs `%D`, and its parser needs `[\d-]+` because
`%b` emits `-`. Also open: a committed plaintext OpenSearch password (#4), a PVC that cannot
cross namespaces (#6), VictoriaLogs sized from the doc's 140M/day column (#7).

**Still the rule, and it cuts both ways:** verify against the running object, never against
the values file — when *reading* it as much as when writing it. And a rendered view is not
the object: **a `_stream` is not a field list, a histogram bucket is not a clock.** Read the
record. The repo has not been reconciled against the rebuilt cluster (#1).

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
