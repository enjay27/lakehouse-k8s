# Active Infrastructure State

**Index, not the record.** Only what would be *false* the moment it goes stale lives here;
everything else is a link into [`.memory/`](.memory/README.md).

## Now — 2026-09-07

**Report schema v2 is DEPLOYED and measured correct** (sha `d58b9203a8304030`; the notebook
gate confirms the running ConfigMap carries it). Run `1788755035`, window `04:24:00Z`: both
request margins 158, `errors_4xx` 41/41/41, `auth_denied` 12/12/12, `bytes_total` 1,186,348 on
both sides — **the new fields carry their own margins**, where v1 had only the request one.
38 active + 4 principals + 6 carried = 48 rows; the next window carries 42 and decays.

**Next, and it is the harness, not the filter:** that run reports 34 fixture mismatches and a
violated invariant, **none of them a filter fault** — all three, with evidence, in
[`HANDOFF-harness-schema-v2`](logging/HANDOFF-harness-schema-v2-2026-09-07.md). The one that
matters: `polaris-learning`'s window merge does not sum fields it does not know, so a v2 field
reads as one window rather than the merge — **a wrong number, not an error**, the same failure
mode as `type_int_key`.

**Still written and NOT running:** the temporary **30s window** (`Interval_Sec 5`). Revert to
1800/30 (#14d) and ride one change with that single upgrade: `resources_other` /
`resources_other_distinct` into the summary `_msg` — queryable today, invisible as text. Until
then the repo file stays byte-identical to the deployed ConfigMap, which is what makes the
notebook's gate mean anything. [`shipper-v3-upgrade-runbook.md`](shipper-v3-upgrade-runbook.md).

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
