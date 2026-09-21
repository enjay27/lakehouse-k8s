# Active Infrastructure State

**Index, not the record.** Only what would be *false* the moment it goes stale lives here;
everything else is a link into [`.memory/`](.memory/README.md).

## Now — 2026-09-21 (docs realigned to the running state; pipeline re-verified on changed traffic)

**The documentation caught up with the cluster today; nothing deployed changed.** `logging/` had thirty
files, sixteen of them finished — those are now [`logging/archive/`](logging/archive/README.md), renamed
`YYYY-MM-DD-<name>` by creation date. `PROPOSAL-polaris-audit-log-retention.ko.md` is
[`logging/SPEC-polaris-audit-logging.ko.md`](logging/SPEC-polaris-audit-logging.ko.md): it stopped being a
proposal when it rolled on 09-16. The sample guide is **generated** now
(`logging/scripts/step14-sample-doc.py` → `GUIDE-sample-data-2026-09-21.ko.md`) because the hand-written
09-16 edition still told new engineers that `threadName`/`threadId` did not exist. `fluent-bit/` has a
README. CLAUDE.md said Polaris `v1.3.0-incubating`; it is **1.6.0**.

**Pipeline re-verified on 2026-09-21 traffic — all seven invariants pass.** 391 detail docs / 122 report
rows, pod `benchmarks-fluent-bit-pdr2h`, schema v6, `391/391` carry `threadName`+`threadId` and none carry
`ndc`. Numbers: [`.memory/roadmap.md`](.memory/roadmap.md) § 2026-09-21. **Query `threadName.keyword`,
never the bare field.**

**Three findings from Kade's changed traffic.** `#24`'s four malformed-request 500s **reproduce on 1.6.0**
(all NPEs) — so `errors_5xx` is still not a health signal on its own. **`#46`:** a 5xx whose path saw no
earlier success in that window lands in `__errors__`, not its resource row — counts survive, attribution
does not; the three deliberate black-hole probes did exactly this. **`#45`:** `PolarisEventListeners`
throws on the null-rename path (new in 1.6.0) and is stored only because rule 1 keeps ERROR/WARN
regardless of `APP_ALLOW` — which also flagged `LocalIcebergCatalog`, 42 dropped lines in 25 s, for an
allowlist review.

**Unchanged and still open:** `WINDOW_SECONDS` is **30**, five days after it was set "temporarily" (28 of
30 windows in the 09-21 export were empty summary rows). The **plaintext OpenSearch password in
`fluent-bit/values.yaml`** tier 1 is documented in three more places today and fixed in none — it needs a
Secret plus a `k8s-logs-*` write-permission check, because a wrong user stops node-wide collection.
`#41` (the 1.6.0 pod that crashed 3× at rollout) is **perishable** and still unread. `#39`, `#36`, `#37`
unchanged. ISM is live and evaluating since 09-18; first deletion happened 09-20 08:42Z.

**Start here next session:** [`.memory/sessions/2026-09-21-fb-docs-and-traffic-review.md`](.memory/sessions/2026-09-21-fb-docs-and-traffic-review.md)
for what moved and why, then `.memory/active-issues.md` `#45`/`#46`. Docs index:
[`logging/README.md`](logging/README.md).

**Standing.** Polaris is not to be changed. **Verify against the running object, never an intent artifact.**

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
| `logging/README.md` | which `logging/` document is current (the 09-03 architecture spec is historical) |

## Rules for keeping this file useful

- **Under ~40 lines.** It reached 80 by accumulating,each session, a digest of findings
  already filed in `.memory/`. **A paragraph summarising a file that exists does not belong
  here.** *Now* carries what is next and what is written but not running; nothing else.
- **Update *Now* every session**, even when the answer is "unchanged".
- **A fact with a number goes in `.memory/roadmap.md`; the story goes in
  `.memory/sessions/`.** Configuration that is written but not applied goes in
  `.memory/active-issues.md` — in this repo that distinction is the whole game.
