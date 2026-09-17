# 2026-09-17 — a notebook for the read-after-write question, and the two bugs that wasted a run

**Built:** `diagnostics/polaris_replica_staleness.ipynb`. **Not executed** — it needs the
cluster, and this was a Cowork session with no `kubectl`, no venv and no cluster reach.

## What it is for

`local-k8s` `.memory/active-issues.md` **#15** — create-namespace and create-view answering 500 —
was once labelled a "PG-HA read-after-write signature". That label was asserted and never
established. Every stored 500 is a `java.lang.NullPointerException` from
`IcebergExceptionMapper`, and the trigger looks like a **fresh parent entity, not load**: 3 of 3
brand-new catalogs 500 on the first namespace created in them.

Two hypotheses survive, and they need separating:

- **A — stale read through Pgpool.** Every link is in the config and was read out of the chart
  this session: `syncReplication` unset (async), `useLoadBalancing` unset (on),
  `statement_level_load_balance = off` (backend fixed per session),
  `disableLoadBalancingOnWrite: always` (pins only *within* a session), and **`delay_threshold`
  set nowhere at all** — chart, templates, or values — so it sits at the pgpool default of 0 and
  replication lag is never checked before a read is balanced onto a replica. Polaris writes on one
  Agroal connection (min 10 / max 300, `PT10M` lifetime) and resolves on another, which is a
  different pgpool session with no write of its own.
- **B — Polaris's own resolver.** 3-of-3 is not what probabilistic lag produces. `grantee_not_found`
  for `catalog_admin` immediately after creating it is the same shape one level up.

The notebook settles **A only**, at the SQL level, without Polaris in the picture.

## Method

Pause WAL *replay* on every standby so staleness is guaranteed rather than waited for, write one
row through Pgpool, then read from 12 brand-new pooled sessions. Each read returns
`pg_is_in_recovery()` in the same statement, so **which node served the session** and **what it
could see** are measured together. `pool_sql()` opens and closes one connection per call —
deliberately unpooled, because with `statement_level_load_balance = off` a reused connection asks
the same backend every time and measures nothing.

## The wrong turns, which are the point of this note

A hand-run bash version was tried first and produced **no result at all**, twice over:

1. **Wrong database.** The helper connected `-U postgres` with no `-d`, which lands in the
   `postgres` database; the read half connected `-d polaris`. Twelve identical
   `relation "rw_probe" does not exist` errors. The notebook creates the probe **through Pgpool**
   as the `polaris` user in the `polaris` database, so there is only one database in play and this
   cannot recur.
2. **Hardcoded standby ordinals.** The script said `for i in 1 2` after telling the operator to
   detect the primary. **The primary is pg-1**, so it tried to pause the primary (`ERROR: recovery
   is not in progress`) and paused only pg-2 — leaving pg-0, also a standby, live and serving
   fresh reads, which would have masked the effect even if the table had existed. The notebook
   derives roles from `pg_is_in_recovery()` and asserts exactly one primary.

**What that run did establish**, and it is worth keeping: the topology is **pg-1 primary, pg-0 and
pg-2 standbys**; both standbys are `streaming`; and pausing pg-2 produced a measured
`replay_lag` of **00:01:43.96**, with pg-0 at zero. So staleness is inducible on demand and
measurable — and under normal load the natural lag is ~zero, which matters when interpreting how
much of the real 500 rate hypothesis A could possibly explain.

## Safety, and why it is heavier than the other diagnostics notebooks

This is the only notebook in `diagnostics/` that changes server state. `require_not_prod()` only
blocks `prod`, and `dev` is a **shared company cluster** where pausing replay would degrade other
people's reads — so there is also a hard `ENV == "local"` assertion with no override, plus a
`kubectl config current-context == orbstack` guard.

Pausing stops replay, not receipt, so WAL accumulates. The pre-flight cell prints which regime
applies: with replication slots the primary retains WAL **without bound**; without them retention
is capped at `wal_keep_size` and a standby that overruns it **cannot catch up on resume** and
needs a full `pg_basebackup` re-clone, because `usePgRewind` is false on this chart. A standalone
idempotent PANIC cell resumes every standby and is safe after a kernel restart.

No credential appears anywhere in the notebook: `kexec` reads the password from the file the
chart already mounts inside the pod.

## What happens next

- **CONFIRMED** (stale reads seen) → remedy is `database_redirect_preference_list =
  'polaris:primary'` in `pgpool.configuration`, using the **`primary` keyword, not a node id** —
  an id would pin reads to a demoted standby after a failover. Then re-run the #15 catalog ladder
  to measure how much of the 500 rate it actually removes, because proving the mechanism is not
  proving the diagnosis.
- **REFUTED** (every read served by the primary) → A is dead, #15 is Polaris's resolver, and since
  Polaris is not to be changed the remedy becomes a client-side retry.

Either way the denominator problem is untouched and separate: a *successful* namespace create
leaves no individual access-log record, so the 500 rate cannot be computed from the log pipeline
at all. It has to come from the driver recording its own statuses.

Deferred behind this: `local-k8s/postgresql/HANDOFF-toxiproxy-failover-2026-09-17.md`, the
primary-unavailable harness. If this comes back REFUTED, that harness stops being urgent and a
NetworkPolicy would probably do.

## Verified vs open

**Verified statically:** every code cell parses; every name the notebook takes from
`import *` (`init_env`, `require_not_prod`, `ENV`, `PG_HOST`, `PG_PORT`, `PG_DB`, `PG_USER`,
`PG_CONFIG`) exists in `polaris_test_utils`; `PG_CONFIG`'s keys are the ones
`psycopg2.connect` takes; no test globs notebooks, so `test_notebook_calls.py` (pinned to
`polaris_log_coverage_v2.ipynb`) is unaffected.

**Open:** the notebook has never been executed. `PG_HOST` is asserted in prose to be the Pgpool
LoadBalancer rather than a pod — the notebook prints it and warns, but cannot check it. And the
helpers (`kexec`, `pool_sql`) live in the notebook rather than `src/`, which this repo's own rule
says is the wrong home; promoting them to `src/pg_replica_probe.py` with a `test_` file is the
right follow-up, as its own task.

---

# Run 1, and the correction — same day

**Run 1 executed cleanly and its verdict was worthless.** All 12 cells ran, no errors, replay
resumed on both standbys, probe table dropped. The notebook printed:

> REFUTED - all 12 sessions were served by the PRIMARY, so Pgpool is not load-balancing reads here
> at all

**That verdict measured the instrument, not the cluster.** The detector was inside the measured
statement:

```sql
SELECT pg_is_in_recovery(), count(*), inet_server_addr()::text FROM rw_probe;
```

`pg_is_in_recovery()` is **VOLATILE**, and Pgpool decides read-vs-write by parsing the statement.
If it classifies a volatile system function as write-ish, the whole statement goes to the primary
— so the detector is a plausible cause of the very routing it reported. Every row would read
`primary` whatever the cluster was doing.

**And nothing proved the connection reached Pgpool at all.** `PG_HOST` is `192.168.139.2`, the
OrbStack LoadBalancer address that also fronts Polaris on 8181. If port 5432 there reached the
primary pod directly, run 1's output would be identical. The notebook printed a prose warning and
checked nothing.

Two candidate explanations for 12/12, only one of which is the printed conclusion — and it is the
least likely of the three.

## What run 1 did establish

- Topology confirmed live: **pg-1 primary**, pg-0 and pg-2 standbys, `inet_server_addr()` of the
  serving backend `192.168.194.55`.
- The pause/resume machinery works end to end; both standbys reached `paused`, and after resume
  `replay_lag` was 1.65 s / 1.96 s and closing.
- **2 replication slots exist**, so a pause retains WAL on the primary without bound. Not a risk
  here: `/bitnami/postgresql` is **203G with 165G free**.
- **`persistence.size: 10Gi` is not what the filesystem shows.** OrbStack's local-path provisioner
  does not enforce the requested capacity, so `local-k8s` `.memory/roadmap.md`'s assertion
  "`persistence.size` -> 10Gi, not 8Gi" **cannot be checked with `df`** and needs re-specifying
  against the PVC spec. Third dead assertion found in one day.

## What the correction changes

- **§2b refuses to continue unless `SHOW pool_nodes` answers**, and displays `status`, `lb_weight`,
  `role` and `load_balance_node` per backend, warning on a zero weight or a down node — either of
  which would explain "no balancing" without any read-after-write behaviour existing.
- **Routing is measured from Pgpool's own `select_cnt`**, diffed around a loop of plain
  `SELECT count(*)`. A counter outside the query cannot perturb the decision it reports.
- **§7b keeps run 1's instrumented query beside it**, purely to show the disagreement if there is
  one. If the counters say standbys served reads while that query says `primary` 12/12, the
  confound is demonstrated rather than argued.
- **§8 and §10 add the symptom**: the #15 ladder — 3 brand-new catalogs, first namespace in each —
  run once while replay is paused and once against healthy replication. Without the control, a 500
  rate while paused says nothing, because #15's 500s were seen on a cluster nobody had paused.
  This also supplies the denominator the log pipeline cannot: the driver records its own statuses.
- `kexec` connects over TCP to 127.0.0.1 instead of the Unix socket, because `inet_server_addr()`
  returns NULL on a socket connection — which is why run 1's role table had an empty `addr` column.
- Outputs cleared. Run 1's result lives in this note, not in the notebook, because keeping a
  superseded verdict beside corrected code is how a wrong number gets quoted later.

## The lesson worth keeping

The failure was not a typo. **The measurement changed what it measured, and it failed silently —
producing a clean, confident, wrong verdict with no error anywhere.** It is the same shape as this
project's window-lag finding (the notebook caused the condition it spent three runs reporting) and
as `local-k8s` #F1 (a values block inert for months because the observed value matched the
default). In all three the output looked right.

The general defence, and it is cheap: **make the instrument prove itself before trusting a
result.** §2b is that assertion. §7b is the receipt.

## Also this session

`log-coverage/polaris-logs.json` (staged but never committed) and `polaris-summary.json`
(untracked) were untracked and deleted at Kade's request — 407 KB and 61 KB of run output from the
2026-09-16 16:03 window. Neither was ever in history, so nothing was lost. They are not gitignored,
so a re-run will bring them back as untracked noise.
