# Active Infrastructure State

**Index, not the record.** Current state below; everything else is a link into
[`.memory/`](.memory/README.md).

## Now — 2026-09-03

**Live thread: the Polaris → VictoriaLogs pipeline**, built against
`logging/polaris-logging-architecture-spec.md`. Steps in [`roadmap.md`](.memory/roadmap.md);
the audit and its four corrections in
[`sessions/2026-09-03-polaris-vlogs-audit.md`](.memory/sessions/2026-09-03-polaris-vlogs-audit.md).

**Next, and it moves to the Polaris project:** `POLARIS-API-LOG-COVERAGE-NOTEBOOK.md` — a
notebook calling every Polaris API so the pipeline is driven across every policy branch,
producing a matrix of what was stored vs discarded. Written to be read cold. It answers the
parked questions, and should demonstrate the gap found while writing it: **successful
management-API creates are POSTs and are being dropped** — a principal is visibly deleted and
invisibly created (roadmap 4b).

**Built, all in `logging/fb-values.yaml`** — no `--set`, the values file is the definition:
access-log field extraction, and a retention policy (ERROR/WARN keep, 4xx/5xx keep,
PUT/DELETE keep, POST table/view keep and other POST drop, GET/HEAD on a table or view once
per **KST** day). **Errors outrank dedup deliberately.** The day comes from the record's own
`_time`, not wall-clock, so a shipper replay is safe. Plus the shipper's silent faults: tail
`DB`, `Skip_Long_Lines On` (it was `Off`, which **stops the tail** rather than skipping the
line), `Rotate_Wait`, filesystem buffering, `json_date_key false`, per-record `Remove_key`.
`logging/scripts/test-polaris-filters.py` reads the Lua *out of* the values file — 30/30.

**Polaris is not to be changed** — it works and ships continuously (Kade's observation, which
outranks the inference in #11). #12 withdrawn; the repo *does* describe this cluster and there
was never a hidden config source (#10).

**#13, and it is now the top of the list: the retention policy is written and NOT RUNNING.**
Measured 2026-09-04 by the Polaris-project notebook — 0 of 34 expected drops dropped, 20
identical table GETs stored 20 records. The filter went into `fb-values.yaml` in `2120ed9` at
08:26:18Z; the shipper pod has run since 08:04:06Z from `60b94d9`, which has the parser and no
filter. **`helm upgrade` was never run** — and it is a change, not a fix, so read #13 first.
Also settled there: **`Polaris-Request-Id` round-trips**, so the spec's §7 trace query works.

**Open:** tail DB on an emptyDir, so `helm upgrade` replays the file once — PVC block is in
the values file, commented (#5b). No latency field at all until `%D` is added Polaris-side,
**and slow requests should then be exempt from dedup**. VictoriaLogs has no disk cap and an
unauthenticated `LoadBalancer` on 9428 (#7). HPA can scale Polaris to 3 pods appending to one
log file (#8). Plaintext credentials in three places (#3, #4, #9).

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
