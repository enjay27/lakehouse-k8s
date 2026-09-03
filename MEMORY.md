# Active Infrastructure State

**Index, not the record.** Current state below; everything else is a link into
[`.memory/`](.memory/README.md).

## Now — 2026-09-03

**Live thread: the Polaris → VictoriaLogs pipeline.** VictoriaLogs and a Fluent Bit file
shipper are deployed (`logging/`) against Kade's design, filed at
`logging/polaris-logging-architecture-spec.md`. Order of work:
[`roadmap.md`](.memory/roadmap.md) *Next*; the audit behind it,
[`sessions/2026-09-03-polaris-vlogs-audit.md`](.memory/sessions/2026-09-03-polaris-vlogs-audit.md).

**That half carries nothing today — written-but-inert, not broken** ([`active-issues.md`](.memory/active-issues.md) #5).
Three switches are off: `logging.file.enabled: false` renders `quarkus.log.file.enabled=false`,
so no `polaris.log` is written; the same flag gates the log PVC, so `polaris-shared-logs-pvc`
— named by both Polaris and the shipper — **is created by nothing in this repo**; and
`quarkus.http.access-log.enabled` is set nowhere, so the access log the spec's dedup filter
consumes does not exist. Everything that reaches OpenSearch does so by the **console** path
via the DaemonSet — which answers the old open question: **two Fluent Bit releases, not
one** (#2). Also new: a committed plaintext OpenSearch password (#4); a PVC cannot cross
namespaces, so the file shipper must live in `datahub-hynix` (#6); VictoriaLogs sized from
the doc's 140M/day column, no disk cap, unauthenticated `LoadBalancer` on 9428 (#7).

**Still the rule:** verify against the **subchart default**, never against the values file —
and the repo has not been reconciled against the rebuilt cluster (#1).

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
