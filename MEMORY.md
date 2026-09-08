# Active Infrastructure State

**Index, not the record.** Only what would be *false* the moment it goes stale lives here;
everything else is a link into [`.memory/`](.memory/README.md).

## Now — 2026-09-08

**Next is the sink, not the harness** — the harness bugs are in code that queries the sink.
VictoriaLogs is being retired for the existing Docker OpenSearch as a **three-tier retention
ladder**: `k8s-logs` 5d unfiltered (**untouched**), `polaris-logs-*` 30d policy-v3 filtered,
`polaris-report-*` 365d schema-v2 rows.
Plan, gates and traps: [`PLAN-opensearch-cutover`](logging/PLAN-opensearch-cutover-2026-09-08.md).

**It is NOT a one-line output swap**, and both reasons fail silently. The tail INPUT has never
parsed Polaris' `timestamp`, so `Logstash_Format` would date every document on arrival; and
`Id_Key sequence` is **data loss, not dedup** — a per-JVM counter that resets on restart, with
`doc_as_upsert` field-unioning the collision. Plan §10 lists ten v1 claims that were wrong, five
of which returned a plausible number rather than an error.

**Still written and NOT running:** the temporary **30s window** (`Interval_Sec 5`) — now a
**prerequisite**, not cleanup. Tier 3 is long-retention, so 30s density (~138k docs/day vs ~2.3k)
would be baked in for a year. Revert to 1800/30 (#14d) **before** tier 3 gets its ISM policy,
riding `resources_other`/`_distinct` into the summary `_msg`.
[`shipper-v3-upgrade-runbook.md`](shipper-v3-upgrade-runbook.md) is the procedure.

**Standing, and all three outrank inference.** Polaris is not to be changed. **Verify against the
running object, never an intent artifact.** And **a gate that cannot fail is not a gate** — plan
§7 replaces one that was built to pass.

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
