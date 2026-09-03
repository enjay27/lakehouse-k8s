# Active Infrastructure State

**Index, not the record.** Current state below; everything else is a link into
[`.memory/`](.memory/README.md).

## Now — 2026-09-03

**The cluster rebuild is DONE and the task is closed.** Kade reset and rebuilt the whole
OrbStack cluster himself, **without following** `RESET-AND-CLEAN-INSTALL.md`. That runbook
and `local-k8s-HANDOFF.md` are now **historical** — keep them for the two faults they
diagnose (`.memory/active-issues.md` #F1, #F2), not as a procedure to run. All four config
blockers were resolved by Kade during the install; how, is not recorded here.

Confirmed by Kade: **Fluent Bit runs as a K8s DaemonSet and works.** **OpenSearch runs in
Docker** — outside the cluster, and outside this repo, which is why no compose file is here.

The one thing to know before trusting anything on disk: **the repo has not been reconciled
against the live cluster.** The blockers were fixed during the install, not necessarily in
these files, and the verification assertions were not run — so no values file here is
currently evidence of what is deployed. `helm -n datahub-hynix get values <release>` is the
authority ([`active-issues.md`](.memory/active-issues.md) #1).

The lesson the rebuild rested on, still the rule: **an entire values block was inert for
months** at the top level of an umbrella chart, and the cluster ran on subchart defaults
(`max_connections` 100 not 200, `/dev/shm` 64M not 1G). Helm does not warn. Verify against
the **subchart default**, never against the values file.

Uncommitted work in the tree is Kade's: `logging/fb-values.yaml`,
`postgresql/schema/bootstrap.sql` (+ `bootstrap_2.sql` deleted). The root runbooks are still
untracked.

## Where the detail is

| read | when |
|---|---|
| [`.memory/environments.md`](.memory/environments.md) | **before running anything** — context, namespaces, ports, and the no-cluster-reach constraint on Cowork sessions |
| [`.memory/active-issues.md`](.memory/active-issues.md) | before trusting a value or a runbook (2 open, 1 open question, 2 resolved-but-instructive) |
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
