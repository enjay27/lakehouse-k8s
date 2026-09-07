# Active Infrastructure State

**Index, not the record.** Only what would be *false* the moment it goes stale lives here;
everything else is a link into [`.memory/`](.memory/README.md).

## Now — 2026-09-07

**Report schema v2 is written and NOT running.** `fb-values.yaml` carries `SCHEMA_VERSION = 2`:
`distinct_resources`/`_principals` count only rows with `requests > 0` (v1 counted zero-carry
rows, so an idle window reported resources it never saw — remainder now in `carried_rows`);
`counted_get` -> `counted_read`, it had always counted HEAD. Added `errors_4xx`/`errors_5xx`/
`auth_denied`, `bytes_total`, `resources_other_distinct`, `windows_skipped`. **60/60** in
`logging/scripts/test-polaris-filters.py`; its suite 4 fails if a numeric field is missing from
`type_int_key`. `helm lint`/`--dry-run` NOT run — no cluster reach from Cowork. Decisions:
[`sessions/2026-09-07-report-schema-v2.md`](.memory/sessions/2026-09-07-report-schema-v2.md);
proposal: [`HANDOFF-report-schema-v2`](logging/HANDOFF-report-schema-v2-2026-09-07.md).

**Also written and NOT running:** the temporary **30s window** (`Interval_Sec 5`), kept on
purpose for one fast coverage run against v2 — **revert both to 1800/30 in a second upgrade
after it** (#14d: a late tick makes counts unattributable; ~60x report volume).
[`shipper-v3-upgrade-runbook.md`](shipper-v3-upgrade-runbook.md) is the procedure.

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
