# HANDOFF — simulating primary-node loss with Toxiproxy (active-issues #2 scenario)

**2026-09-17. Status: PLANNED AND NOT BUILT.** No manifest exists, `postgresql/values.yaml` is
unchanged by this document, nothing was applied to the cluster. This is the design plus the
reasoning that produced it, written to be picked up cold.

**Sequencing: Kade is doing issue 1 (the create-namespace 500s) first.** That is deliberate —
see *Do issue 1 first* below, because its outcome can change whether this harness is worth
building at all.

---

## The question this answers

> What happens when the PostgreSQL primary becomes unavailable?

and the sub-question that makes it hard here: **there is exactly one node.** A personal OrbStack
single node, with `podAntiAffinityPreset: soft` on both postgresql and pgpool because it has to
be. Losing the node takes all three Postgres replicas, pgpool, Polaris and everything downstream
with it — that is a total outage, not a failover test, and nothing survives to fail over *to*.

So the testable scenario is narrower and is the useful half: **the primary is unreachable to
everyone else while still running.** That isolates the detection-and-promotion path from the
restart-and-storage path, and it is the thing nobody here has ever measured.

Real node-level failover needs a multi-node cluster. This repo has one cluster, it is personal,
and per CLAUDE.md no other cluster may ever be targeted from it. Out of scope, permanently.

## Read first

- `.memory/active-issues.md` #8 (HPA vs the shared log file), #9, #15 (the 500s — issue 1)
- `.memory/roadmap.md` → *PostgreSQL verification assertions*
- `postgresql/values.yaml` — the `extendedConf`, `pgpool.configuration` and pg_hba comments are
  the accumulated scar tissue and are worth reading before touching anything
- `.memory/active-issues.md` #F1 and #F2 — both failure modes below are versions of these

---

## Two designs that were rejected, and why

Recorded so the next session does not re-propose them. Both are reasonable-sounding and both
fail for the same underlying reason.

### Rejected: per-pod Kubernetes Services, then delete one

The idea was to give each Postgres pod its own Service, route everything through that layer, and
delete a Service to simulate the node vanishing. It fails three ways:

1. **The per-pod service layer already exists.** The chart addresses every pod through the
   headless service and *both* consumers already use it:
   `PGPOOL_BACKEND_NODES = 0:<fullname>-0.<headless>.<ns>.svc.cluster.local:5432,...`,
   `REPMGR_PARTNER_NODES` and `REPMGR_NODE_NETWORK_NAME` likewise. A new layer would be a
   *second* one that only pgpool could be moved onto.
2. **Established connections do not notice.** Removing a Service changes DNS and endpoints, both
   of which only matter at connect time. With `useConnectionCache: true` (chart default) plus
   `connection_life_time = 0` and `client_idle_limit = 0` in our `pgpool.configuration`, pgpool's
   cached backend connections **never expire** — the "failure" stays invisible until something
   reconnects, possibly never during a short test.
3. **It bypasses the timers the test exists to measure.** A deleted Service gives NXDOMAIN — an
   immediate, explicit resolution failure. A dead node gives *silence*: packets dropped,
   connections hanging. NXDOMAIN short-circuits `repmgrConnectTimeout: 5` and pgpool's
   `health_check_timeout = 20`, so the test would report detection far faster than reality.

### Rejected: an nginx container in Docker as an extra layer

Same fatal flaw plus new ones. `docker stop`/`docker kill` closes sockets, so the client gets an
immediate **connection reset** — fast-fail again, not silence. Open-source nginx `stream` is a
dumb TCP pipe: it can forward or not forward, but it cannot black-hole packets while holding the
connection open, which is the one behaviour needed. It is also protocol-blind for Postgres, so it
can take over none of pgpool's job, and its own `proxy_connect_timeout` (60s) and `proxy_timeout`
(10m) would sit in front of everything being measured. Finally it would add a **second**
ungoverned out-of-cluster Docker dependency — OpenSearch is already one, and CLAUDE.md flags that
as a wart — this time in the critical path between Polaris and its metastore, inside a dependency
order (`MinIO -> PostgreSQL -> Polaris`) that git would not know about.

### The flaw both share, which Toxiproxy alone does NOT fix

**repmgr routes around a proxy that is only in pgpool's path.** repmgrd reaches its peers on
`REPMGR_PARTNER_NODES` / `REPMGR_NODE_NETWORK_NAME`, generated per-ordinal from `$(MY_POD_NAME)`
inside the StatefulSet template. Break only pgpool's path and repmgr still sees three healthy
nodes and **will not promote**: pgpool degenerates the primary, no new primary appears, writes
simply fail. That is not node-unavailable — it is pgpool and repmgr holding different views.

Switching proxy software does not fix this. The design below fixes it with `hostAliases`.

---

## The design

Toxiproxy was chosen over a NetworkPolicy or `iptables ... -j DROP` because it gives **both
failure shapes from one tool** — silent black-hole *and* fast reset — and its latency toxic is
reusable for issue 1. A NetworkPolicy remains the simpler fallback (see *Caveats*).

One Toxiproxy Deployment hosting three listeners, fronted by **three ClusterIP Services** that
each map port 5432 to a different listener. `hostAliases` on the Postgres and pgpool pods then
point each pod's headless FQDN at the matching Service IP:

```
pg-0 FQDN -> toxiproxy-pg0 (ClusterIP:5432) -> :15432 -> real pg-0:5432
pg-1 FQDN -> toxiproxy-pg1 (ClusterIP:5432) -> :15433 -> real pg-1:5432
pg-2 FQDN -> toxiproxy-pg2 (ClusterIP:5432) -> :15434 -> real pg-2:5432
```

Three proxies, not one, so the test is repeatable: after a failover the primary moves, and you
inject on whichever pod is primary *now*. The Toxiproxy pod itself carries no aliases, so it
resolves the real headless DNS normally and forwards to the true pod IP.

This puts **repmgrd peer traffic, walreceiver replication, and pgpool's backends** all through
the proxy — which is what makes it a genuine failover test rather than the split-view non-test
described above.

`postgresql.hostAliases` and `pgpool.hostAliases` are both exposed by postgresql-ha 16.3.2
(`templates/postgresql/statefulset.yaml` L46, `templates/pgpool/deployment.yaml` L47), so **no
chart fork is required.**

### Names in this cluster

```
fullname : benchmarks-postgresql-postgresql-ha-postgresql
headless : benchmarks-postgresql-postgresql-ha-postgresql-headless
pg-0 FQDN: benchmarks-postgresql-postgresql-ha-postgresql-0.benchmarks-postgresql-postgresql-ha-postgresql-headless.datahub-hynix.svc.cluster.local
pgpool   : benchmarks-postgresql-postgresql-ha-pgpool
```

---

## Impact analysis

| file | change | risk |
|---|---|---|
| `postgresql/toxiproxy/` (**new**) | Deployment + 3 Services + seed config | new, isolated |
| `postgresql/values.yaml` | add `postgresql.hostAliases` and `pgpool.hostAliases` | **must nest under `postgresql-ha:`** — this is #F1 exactly |
| `polaris/values.yaml` | none | — |
| `.memory/`, `MEMORY.md` | issue entry + session note per DoD | — |

**Blast radius, stated plainly:** while the aliases are installed, every Postgres connection in
the platform traverses a single Toxiproxy pod. That is a new SPOF and added latency in the
metastore path for `MinIO -> PostgreSQL -> Polaris -> everything`. This is a harness, not a
topology. **Step 7 removes it. Do not leave it installed.**

Applying the aliases needs a `helm upgrade`, which **rolling-restarts all three Postgres pods**.
That is disruptive on its own and must be a deliberate act, not a side effect of something else.

## Blocker to clear before any `helm upgrade`

As of 2026-09-17 the working tree carried **uncommitted edits made by Kade, not by Claude**:

```
polaris/values.yaml      autoscaling.maxReplicas    3 -> 1
polaris/values.yaml      logging.console.threshold  DEBUG -> INFO
```

`postgresql/values.yaml` is clean as of this writing — a `pgpool.replicaCount 3 -> 1` edit was
present earlier the same day and was **reverted back to 3** before this document was committed.
So the values file no longer diverges from HEAD, and a `helm upgrade` for this test would push
only the hostAliases block.

That does not make the check skippable. **Run `git status` before any `helm upgrade` and read
what it says rather than trusting this paragraph** — this is the second time in one day that the
tree changed underneath an analysis. The Polaris edits above are still uncommitted and would ride
along with any `helm upgrade` of *that* chart.

---

## Steps

### 1 — Baseline, verified against running objects

```bash
kubectl config current-context                     # must equal orbstack
kubectl -n datahub-hynix exec <pg-0> -- \
  repmgr -f /opt/bitnami/repmgr/conf/repmgr.conf cluster show
kubectl -n datahub-hynix exec <pgpool> -- psql -U postgres -c "show pool_nodes;"
curl -s localhost:8182/q/health                    # Polaris green
```

Record which pod is primary. Everything below assumes pg-0; substitute if not.

### 2 — Deploy Toxiproxy

`kubectl apply`, not a Helm release. Image pinned explicitly to a chosen
`ghcr.io/shopify/toxiproxy:<version>` and the version written down — active-issues #2 is about
charts that pin nothing, and this must not add to it. Seed the three proxies from a JSON config
so they exist at startup rather than being created by hand.

### 3 — Read the three ClusterIPs

`hostAliases` takes literal IPs, not names:

```bash
kubectl -n datahub-hynix get svc toxiproxy-pg0 toxiproxy-pg1 toxiproxy-pg2 \
  -o custom-columns=NAME:.metadata.name,IP:.spec.clusterIP
```

**Operational gotcha:** delete and recreate those Services and the IPs change, silently
invalidating every alias. If the harness ever behaves strangely, check this first.

### 4 — Add hostAliases, dry-run, upgrade

```yaml
postgresql-ha:
  postgresql:
    hostAliases:
      - ip: "<toxiproxy-pg0 ClusterIP>"
        hostnames:
          - "benchmarks-postgresql-postgresql-ha-postgresql-0.benchmarks-postgresql-postgresql-ha-postgresql-headless.datahub-hynix.svc.cluster.local"
          - "benchmarks-postgresql-postgresql-ha-postgresql-0.benchmarks-postgresql-postgresql-ha-postgresql-headless.datahub-hynix.svc"
      # ... pg1, pg2
  pgpool:
    hostAliases:
      # the same three entries
```

Gate: `helm lint ./postgresql` -> `helm upgrade --install benchmarks-postgresql ./postgresql
-n datahub-hynix --dry-run=client --debug` -> upgrade.

### 5 — Prove the path is live before trusting any result

Verify from the running object, never from the values file:

```bash
kubectl -n datahub-hynix get pod <pg-1> -o jsonpath='{.spec.hostAliases}'
kubectl -n datahub-hynix exec <pg-1> -- getent hosts <pg-0 FQDN>   # must be the Toxiproxy ClusterIP
kubectl -n datahub-hynix exec <toxiproxy> -- /toxiproxy-cli list
```

Then re-run step 1 in full. **If the baseline does not come back clean through the proxy, stop —
the harness is broken, not the cluster.** A green-looking result from a harness that is not in
the path is exactly the #F1 failure wearing a new costume.

### 6 — Inject, and timestamp everything

Black hole — connections accepted, never answered, never closed. This is the shape a dead node
actually has, and the reason for the whole design:

```bash
/toxiproxy-cli toxic add pg0 -t timeout -a timeout=0 -n blackhole_down
/toxiproxy-cli toxic add pg0 -t timeout -a timeout=0 --upstream -n blackhole_up
```

Fast-fail variant, as a **second, separate run**: `/toxiproxy-cli toggle pg0` — closes
connections and refuses new ones (RST semantics). Running both is the point of choosing
Toxiproxy; do not conflate their results.

Capture, with timestamps:

| mark | event | prediction from config |
|---|---|---|
| T0 | toxic applied | — |
| T1 | repmgrd logs primary failure | ~11s (`repmgrConnectTimeout 5` + 2 x `repmgrReconnectInterval 3`) |
| T2 | `repmgr cluster show` reports the new primary | T1 + promotion |
| T3 | `show pool_nodes` shows node 0 down and the new primary | 30-70s (`health_check_period 10`, `timeout 20`, `max_retries 3`) |
| T4 | first successful Polaris write after the break | the number that actually matters |

**T3 - T2 is the interesting one** — the window where repmgr has promoted but pgpool has not yet
noticed, during which writes fail against a healthy cluster. These predictions exist to be
falsified; replace them with measurements.

Also record:

- whether Polaris answers 500 or 503 during the window (the values carry **no retry**, so 500 is
  expected, and that is itself a finding for #15's neighbours);
- whether any transaction that returned 200 before T0 is missing after promotion.
  `syncReplication: false` means committed-but-unreplicated writes are lost on promotion, and
  confirming that is part of the test, not an accident.

### 7 — Recovery, then remove the harness

Remove the toxics and watch the old primary rejoin. Expect friction: pg-0 still believes it is
primary, and with `usePgRewind: false` (chart default, not overridden) the rejoin is a **full
`pg_basebackup` clone, not a rewind** — minutes, and watch headroom on the 10Gi PVC. Record
whether it self-heals or needs a manual `repmgr node rejoin`.

Then remove `hostAliases`, `helm upgrade`, delete the Toxiproxy manifests, and re-verify step 1.

---

## Caveats

- **pg-0 aliases its own name.** A StatefulSet applies one pod spec to all replicas, so pg-0's
  own FQDN also resolves to the proxy, and during the black hole its self-connections by that
  name will hang. There is no per-ordinal override through values. Probably acceptable and
  arguably realistic, but it is the most likely source of a surprising result. **If it distorts
  the test, fall back to a NetworkPolicy on pg-0**, which needs no aliases at all — but first
  confirm OrbStack's CNI actually enforces NetworkPolicy, because many local clusters accept one
  through the API server and silently never apply it.
- **Node-level remains out of reach**, as above. This measures *primary unreachable*, not *node
  gone*.
- **No cluster reach from a Cowork session.** Every command here is Kade's to run. Anything
  Claude commits about this carries `NOT VERIFIED`.

## Do issue 1 first

Issue 1 is `.memory/active-issues.md` #15 — create-namespace/view returning 500, which is a
`NullPointerException` and **not** the settled "PG-HA read-after-write signature" it was once
labelled as. The decisive test is one command, needs none of this harness, and should be run
before deciding whether to build it:

```sql
-- on each standby
SELECT pg_wal_replay_pause();
-- run the three-brand-new-catalog ladder, then:
SELECT pg_wal_replay_resume();
```

Replay stops instantly, the standbys are guaranteed stale, WAL keeps arriving but is not applied.
If the 500 rate jumps, stale reads through pgpool are confirmed. If it is unchanged, that
hypothesis is dead and the cause is Polaris's own resolver — and CLAUDE.md says Polaris is not to
be changed, so the answer becomes a client-side retry.

**Why this changes the value of the harness:** if issue 1 turns out to be a Polaris resolver bug,
the remaining reason to build this is measuring failover latency for its own sake — still
worthwhile, but no longer urgent, and a NetworkPolicy would probably do.

Related and separate, from the same 2026-09-17 review, both still OPEN and neither acted on:

- `database_redirect_preference_list = 'polaris:primary'` in `pgpool.configuration` would pin all
  of Polaris's sessions to the primary. Use the `primary` keyword, **not** a node id — node 0 is
  not permanently the primary, and after a failover an id would pin reads to a demoted standby.
- `delay_threshold` is set nowhere in the chart, the templates or our values, so it sits at the
  pgpool default of 0: **replication lag is never checked** before a read is load-balanced.
- One `.memory/roadmap.md` PostgreSQL assertion does not discriminate: `postgresql.replicaCount:
  3` is also the subchart default, so observing 3 proves nothing about whether the nested block is
  live. "pgpool pod count 3, not default 1" **is** valid while the values say 3 — but it inverts
  silently if that value is ever set to 1 again, so re-read the file before trusting it. Still
  sound: `persistence.size` 10Gi vs 8Gi, `max_connections` 200 vs 100, `/dev/shm` 1G vs 64M.
- With pgpool back at 3 replicas, the connection ceiling is the one its own comment states:
  `numInitChildren 64 x maxPool 4 x 3 = 768` against `max_connections = 200` per node, and Polaris
  may open `QUARKUS_DATASOURCE_JDBC_MAX_SIZE=300` per pod. Pgpool queues rather than overruns, but
  a post-failover reconnect storm is exactly when that queue matters. Unmeasured.
- `postgresql/secret/polaris-persistence-secret.yaml` is the stale manifest #4 refers to without
  naming: its `jdbcUrl` is `jdbc:postgresql://postgres-postgresql:5432/polaris`, a host that does
  not exist in this deployment. Applying it breaks Polaris's metastore path.

## Verified vs open

**Verified** (read from the chart and the values, 2026-09-17): `hostAliases` is exposed for both
postgresql and pgpool in postgresql-ha 16.3.2; `PGPOOL_BACKEND_NODES`, `REPMGR_PARTNER_NODES` and
`REPMGR_NODE_NETWORK_NAME` all use headless per-pod DNS; `syncReplication` and `usePgRewind` are
both unset and therefore false; `useLoadBalancing` is unset and therefore true.

**Open — every runtime claim.** No `kubectl`, `helm` or `docker` command in this document has
been run. The timings in step 6 are arithmetic on config values, not measurements. Which pod is
primary, whether the HPA still allows 3 Polaris pods, and whether the live release matches these
files are all unconfirmed — `helm -n datahub-hynix get values benchmarks-polaris` has still never
been run, which is also what blocks active-issues #5.
