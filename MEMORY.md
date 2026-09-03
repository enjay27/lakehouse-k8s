# Active Infrastructure State

**Index, not the record.** Current state below; everything else is a link into
[`.memory/`](.memory/README.md). If you are picking this up cold, read the runbook
named in *Now* — it is standalone.

## Now — 2026-09-03

**Read [`RESET-AND-CLEAN-INSTALL.md`](RESET-AND-CLEAN-INSTALL.md) first — standalone**
(the *how*); [`local-k8s-HANDOFF.md`](local-k8s-HANDOFF.md) is the *why*.

Task: full OrbStack Kubernetes reset + clean install of every chart in this repo into
namespace `datahub-hynix`. **Status: PLAN ONLY — nothing torn down, nothing installed,
no cluster command run.** Blocked at step 0 on three developer decisions, not on work:
the Polaris root secret, one agreed MinIO credential set, and the stale
`polaris-persistence-secret.yaml` ([`active-issues.md`](.memory/active-issues.md) #1, #3, #4).

Written but **never proved against a running cluster**, so do not treat as done:
the 12 new `minio/` templates, the whole `postgresql/values.yaml` rewrite
(`postgresql-ha:` nesting, 10Gi, 1G `/dev/shm`, dual-family `pg_hba`), and the
uncommitted Fluent Bit → VictoriaLogs switch. `persistence.size` is **now-or-never** —
a fresh install is the only chance to set 10Gi.

The lesson the rebuild rests on: **an entire values block was inert for months** at the
top level of an umbrella chart, and the cluster ran on subchart defaults (`max_connections`
100 not 200, `/dev/shm` 64M not 1G). Helm does not warn. Verify against the **subchart
default**, never against the values file.

Uncommitted work in the tree is Kade's, not this convention's: `logging/fb-values.yaml`,
`postgresql/schema/bootstrap.sql` (+ `bootstrap_2.sql` deleted).

## Where the detail is

| read | when |
|---|---|
| [`.memory/environments.md`](.memory/environments.md) | **before running anything** — context, namespaces, ports, and the no-cluster-reach constraint on Cowork sessions |
| [`.memory/active-issues.md`](.memory/active-issues.md) | before trusting a value or a runbook (4 open, 3 unverified, 2 resolved-but-instructive) |
| [`.memory/roadmap.md`](.memory/roadmap.md) | what is done, what is next, and the verification assertions |
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
