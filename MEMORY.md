# Active Infrastructure State

**Index, not the record.** Current state below; everything else is a link into
[`.memory/`](.memory/README.md).

## Now — 2026-09-03

**Live thread: the Polaris → VictoriaLogs pipeline**, built against
`logging/polaris-logging-architecture-spec.md`. Next steps in
[`roadmap.md`](.memory/roadmap.md); the audit and its four corrections in
[`sessions/2026-09-03-polaris-vlogs-audit.md`](.memory/sessions/2026-09-03-polaris-vlogs-audit.md).

**Built, all in `logging/fb-values.yaml`** — no `--set`, the values file is the definition:
access-log field extraction, and a retention policy (ERROR/WARN keep, 4xx/5xx keep,
PUT/DELETE keep, POST table/view keep and other POST drop, GET/HEAD on a table or view once
per **KST** day). **Errors outrank dedup deliberately** — a 404 on a table GET is both, and a
client hammering a missing table has to stay visible. The day comes from the record's own
`_time`, not wall-clock, so a shipper replay is safe. Plus the shipper's silent faults: tail
`DB`, `Skip_Long_Lines On` (it was `Off`, which **stops the tail** rather than skipping the
line), `Rotate_Wait`, filesystem buffering, `json_date_key false`, per-record `Remove_key`.
`logging/scripts/test-polaris-filters.py` reads the Lua *out of* the values file — 30/30.

**Polaris is not to be changed** — it works and ships continuously (Kade's observation, which
outranks the inference in #11; this session's inferences about this pipeline were wrong four
times). #12 withdrawn. The repo *does* describe this cluster; there was never a hidden config
source (#10).

**Open:** tail DB is on an emptyDir, so `helm upgrade` still replays the file once — PVC block
is in the values file, commented (#5b). VictoriaLogs has no disk cap and an unauthenticated
`LoadBalancer` on 9428 (#7). HPA can scale Polaris to 3 pods appending to one log file (#8).
Plaintext credentials in three places (#3, #4, #9). Parked on Polaris changes: `%D` for
latency — **and slow requests should then be exempt from dedup**, since a table GET that
normally takes 8ms taking 4s is exactly what daily dedup discards — the "Deprecated Config"
exclusion (hook in place), and PUT request bodies, absent from the access log entirely.

**The rule, at its fourth setting this session:** verify against the running object, never an
intent artifact — `helm get values` is one too, showing *inputs*. Nor is a rendered view the
object: a `_stream` is not a field list, a histogram bucket is not a clock. And a claim about
"the repo" needs evidence about the repo, not one file in it.

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
