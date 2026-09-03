# Active Infrastructure State

**Index, not the record.** Current state below; everything else is a link into
[`.memory/`](.memory/README.md).

## Now — 2026-09-03

**Live thread: the Polaris → VictoriaLogs pipeline**, built against
`logging/polaris-logging-architecture-spec.md`. Next steps in
[`roadmap.md`](.memory/roadmap.md); the audit and its four corrections in
[`sessions/2026-09-03-polaris-vlogs-audit.md`](.memory/sessions/2026-09-03-polaris-vlogs-audit.md).

**The repo does describe this cluster — there was no hidden config.** ConfigMap, pod env,
live release values and `polaris/values.yaml` all agree: `quarkus.log.file.enabled=false`.
The divergence story that ran through five readings was wrong at every level (#10). **And it
inverts Kade's belief that the chart's `logging.file` block is inert: it is the switch holding
the pipeline off**, rendered straight into the ConfigMap. `QUARKUS_LOG_FILE_JSON_*` sets
formatting on a disabled handler.

**Polaris is not to be changed** — it works and ships continuously (Kade's observation;
#11 is left unexplained rather than acted on, since this session's inferences about this
pipeline were wrong four times and his observation wins). #12 withdrawn.

**Then** (#5b, #8, #9): the tail has no `DB` with `Read_from_Head true` and
`Skip_Long_Lines Off`, both confirmed live; per-record waste; no `%D`, so §7's P99 panels
cannot exist. **#8 — HPA can scale Polaris to 3 pods appending to one log file**; RWO does
not stop that on one node. Plaintext credentials now in three places (#3, #4, #9).

**The rule, at its fourth setting this session:** verify against the running object, never an
intent artifact — and `helm get values` is one too, showing *inputs*. Nor is a rendered view
the object: a `_stream` is not a field list, a histogram bucket is not a clock. And a claim
about "the repo" needs evidence about the repo, not one file in it.

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
