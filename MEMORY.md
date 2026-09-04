# Active Infrastructure State

**Index, not the record.** Only what would be *false* the moment it goes stale lives here;
everything else is a link into [`.memory/`](.memory/README.md).

## Now — 2026-09-04

**Next:** `helm upgrade` the shipper to policy v2 —
[`shipper-v2-upgrade-runbook.md`](shipper-v2-upgrade-runbook.md) is the whole procedure. Note
the correction it carries: the Fluent Bit counters reset when the pod is replaced, so the
pre-upgrade metrics sample is a **rate baseline, not a subtrahend**. Then re-run
`polaris-learning/log-coverage` — its characterization test is built to fail on a policy
change, so read the diff and update it and `doc-log-coverage-results.md` together.

**Written and NOT running:** `logging/fb-values.yaml` carries policy v2 and the flush report,
one `helm upgrade` away; the cap on the principal-keyed dedup table is still Kade's to decide.
The repo's recurring failure mode, entered knowingly this time — the account, the measurements
and what was deferred are [`active-issues.md`](.memory/active-issues.md) **#14**.

**Standing, and both outrank inference.** Polaris is not to be changed — it works and ships
continuously (Kade's observation, over the reasoning in #11). And **verify against the running
object, never an intent artifact**: `helm get values` is one too, showing *inputs*; a `_stream`
is not a field list; a histogram bucket is not a clock.

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
