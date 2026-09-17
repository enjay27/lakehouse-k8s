# HANDOFF — Polaris 1.3.0 → 1.6.0, and what the upgrade costs `#15`

**2026-09-17. Status: NOTHING DONE.** No values changed, no chart touched, no cluster command run.
Written for the session that will perform the upgrade, and written to be read cold.

**Kade's decision: the upgrade goes first**, before the `#15` investigation. This document is
organised around that order. It says once, below, what that costs, and then gets out of the way.

---

## Read this first — the 1.3.0 evidence is perishable

`.memory/active-issues.md` **#15** (create-namespace / create-view returning 500) has never been
characterised on this version. The moment Polaris is upgraded, it never can be: the 500s either
vanish or change shape, and the question becomes unanswerable rather than answered.

**There is a 15-minute capture that preserves it.** Run it before the first mutating command of
the upgrade session. Nothing in it changes anything.

```bash
kubectl config current-context                       # must equal orbstack

# 1. THE ONE THAT CANNOT BE RECOVERED LATER.
#    This is the evidence for #5's "the values file does not describe the running Polaris"
#    claim. After the upgrade there is nothing left to diff it against.
helm -n datahub-hynix get values benchmarks-polaris > /tmp/polaris-values-1.3.0.yaml
helm -n datahub-hynix get values benchmarks-polaris --revision $(helm -n datahub-hynix history benchmarks-polaris | tail -2 | head -1 | awk '{print $1}')

# 2. Ten seconds, and it can reorder the whole #15 investigation (hypothesis C below).
kubectl -n datahub-hynix get deploy,hpa,pods -l app.kubernetes.io/name=polaris

# 3. The live schema version -- needed for the upgrade anyway, see below.
kubectl -n datahub-hynix exec <pgpool> -- \
  psql -U polaris -d polaris -tAc "SELECT * FROM polaris_schema.version;"

# 4. The #15 baseline itself: run the ladder on 1.3.0 and keep the output.
#    polaris-learning/diagnostics/polaris_replica_staleness.ipynb, sections 8 and 10.
```

Step 4 is optional if time is short; **steps 1-3 are not**. Step 1 in particular takes five
seconds and closes a question that has been open since 2026-09-03.

---

## What `#15` is, and which parts of it the upgrade can erase

Every stored 500 is a `java.lang.NullPointerException` from
`org.apache.polaris.service.exception.IcebergExceptionMapper`, in three signatures — six
`…getPassthroughResolvedPath(Object)" is null` on `POST …/namespaces`, one `grantee_not_found`
for `catalog_admin` on catalog create, one `metadata` on view create. **3 of 3 brand-new catalogs
500 on the first namespace created in them**, and the namespace is usable afterwards. Consistent
with a write that committed and a resolution that then dereferenced null.

It was once labelled a "PG-HA read-after-write signature". **That was asserted and never
established.** Three hypotheses are live:

| | hypothesis | survives the upgrade? |
|---|---|---|
| **A** | stale reads through Pgpool — a write on one Agroal connection is invisible to a read on another | **yes**, it is a database-layer fact |
| **B** | Polaris 1.3.0's own resolver / entity cache mishandles a freshly created parent | **possibly erased by the upgrade** |
| **C** | the namespace request lands on a *different* Polaris pod than the catalog create, whose cache never saw it | **yes**, it is a deployment-shape fact |

**C deserves more weight than it has had.** Round-robin across replicas is deterministic in a way
replication lag is not, which fits 3-of-3 far better. `#8` records `maxReplicas: 3` in the live
release with `REPLICAS 1` and no metrics as of 2026-09-09 — unverified since. Capture step 2
settles it.

**Do not invest in B before the upgrade.** Upstream issue search, filing a bug, building a
client-side retry — all of it is aimed at a version being abandoned. The upgrade is itself the
better experiment: run the identical ladder before and after and the version-dependence answers
itself, for free.

---

## The upgrade

### The metastore schema migration is the main risk, and it is manual

From the Polaris docs for the relational JDBC metastore:

> Polaris does not run automated schema migrations. Bootstrapping applies a full `schema-vN.sql`
> script and records the schema version in the `polaris_schema.version` table; upgrading an
> existing database to a newer schema version is a manual, operator-driven step.

This repo carries `postgresql/schema/schema_v3.sql` as the ASF-shipped authority, so this install
is on **schema v3**. The 1.7.0 docs document up to **v5**. Therefore:

1. **Read `polaris_schema.version` off the live metastore** (capture step 3). Do not infer the
   version from the file in this repo — that is the same mistake as `#F1`.
2. **Find 1.6.0's required schema version** and whether v3 → that version needs a migration.
3. **Do NOT re-bootstrap an existing metastore expecting it to migrate.** Bootstrap applies a
   *full* schema script; it is an initialisation path, not an upgrade path.

**One documented migration step touches a table this platform actively writes.** The v5 migration
alters `events.catalog_id` from NOT NULL to nullable — and `polaris/values.yaml` configures an
event listener (`type: persistence-in-memory-buffer`) that records every API operation into that
`events` table. Treat it as load-bearing, not incidental.

**Commit before this step, not after.** A schema migration is exactly the risky operation
CLAUDE.md's *commit before a risky step* rule exists for.

### The chart, not just the image tag

`polaris/values.yaml` pins `image.tag: "1.3.0-incubating"` and this repo's `polaris/` is a **local
chart** whose templates were written against 1.3.0. Bumping the tag alone may not be enough — the
upstream 1.6.0 chart may have moved or renamed values keys, and a key this chart no longer reads
fails silently, which is `#F1`'s failure mode again. Diff the local chart against the upstream
1.6.0 chart before assuming a tag bump suffices.

Gate, per CLAUDE.md: `helm lint ./polaris` → `helm upgrade --install … --dry-run=client --debug`
→ upgrade → verify **from the running object**, never from the values file.

### Downstream invalidations, in the other repo

The upgrade reaches into `polaris-learning`:

- `src/config/local.yaml` carries `polaris_version: "1.3.0"` and flags derived from it.
  `purge_deletes_files: false` is annotated *"issue #379 present locally"* — re-test rather than
  assume it still holds on 1.6.0.
- **`log-coverage/spec/` is the vendored 1.3.0 OpenAPI, and it is the coverage run's denominator**
  — `load_spec` builds the 63 operations and 286 cells from it. The upgrade invalidates every
  coverage number until the specs are re-fetched (`log-coverage/fetch_specs.sh`).
- The Lua retention policy and report schema v6 key on Polaris log shapes. Compare one window
  after the upgrade rather than assuming they hold.

---

## After the upgrade — the `#15` experiment

Re-run the identical ladder from
`polaris-learning/diagnostics/polaris_replica_staleness.ipynb` (§8 and §10: three brand-new
catalogs, first namespace in each, once with WAL replay paused and once against healthy
replication).

| result on 1.6.0 | reading |
|---|---|
| 500s gone | **B** was a 1.3.0 bug, fixed upstream. `#15` closes — record the version that fixed it |
| 500s persist, `paused` > `healthy` | **A** is contributing; apply the pgpool remedy below and re-measure |
| 500s persist, `paused` == `healthy`, >1 Polaris pod | **C**; pin replicas and re-measure |
| 500s persist, one pod, no standby serves reads | a current-version Polaris bug with a clean repro — **now worth reporting upstream** |

**If the ladder produces no 500s in either phase**, do not conclude "unreproducible" yet. `#15`'s
evidence came from a differently-seeded cluster (run `1788760757`), and the notebook's ladder runs
as `root`. This project has already learned once that *"the sweep was measuring root, and root is
the least representative identity"* — re-run as a seeded non-root principal before drawing a line.

---

## Two remedies worth applying regardless of which hypothesis wins

Both sit outside Polaris, so neither is affected by the upgrade and neither violates the standing
"Polaris is not to be changed" rule.

**A — pin Polaris's reads to the primary.** One line into the existing `pgpool.configuration`
block in `postgresql/values.yaml`:

```
database_redirect_preference_list = 'polaris:primary'
```

Use the **`primary` keyword, never a node id** — node 0 is not permanently the primary, and after a
failover an id would pin reads to a demoted standby. Then: `helm lint` → `--dry-run=client
--debug` → upgrade → **rollout restart pgpool** (`#20`: an upgrade can change the ConfigMap without
restarting the pod) → confirm from the running `pgpool.conf`.

Context for why this is not already covered: `disable_load_balance_on_write = always` pins only
*within* one session, and **`delay_threshold` is set nowhere** — not in the chart, its templates or
our values — so it sits at the pgpool default of 0 and replication lag is never checked before a
read is balanced onto a standby.

**C — pin Polaris to one replica.** `replicaCount: 1`, `autoscaling.enabled: false`. The working
tree already carries `maxReplicas 3 → 1` uncommitted. **This also closes `#8`**, the
three-pods-appending-to-one-log-file hazard, open since August.

---

## Next month: 1.7.0 has a trap

[apache/polaris#5521](https://github.com/apache/polaris/issues/5521) — `OPTIMIZED_SIBLING_CHECK`
rejects **every** namespace and table created under an existing namespace with a **403**, across
in-memory, PostgreSQL and NoSQL backends. It affects **1.7.0 and later; 1.6.0 is clear.** PR #5520
exists and may land before the release.

Given phase J drives a nested namespace deliberately, this would bite immediately. Before
upgrading to 1.7.0: confirm whether #5520 shipped, and keep `OPTIMIZED_SIBLING_CHECK` off until it
has.

---

## Record items still open, none of which need the cluster

1. `postgresql/secret/polaris-persistence-secret.yaml` — `jdbcUrl` is
   `jdbc:postgresql://postgres-postgresql:5432/polaris`, a host that does not exist here. This is
   the stale manifest `#4` refers to without naming. Applying it breaks the metastore path.
2. **Three** `.memory/roadmap.md` PostgreSQL assertions no longer discriminate:
   `postgresql.replicaCount: 3` is the subchart default; "pgpool pod count 3" inverts silently if
   that value is ever set to 1 again; and `persistence.size` 10Gi **cannot be checked with `df`** —
   measured 2026-09-17, `/bitnami/postgresql` reports 203G because OrbStack's local-path
   provisioner does not enforce the request. Check the PVC spec instead.
3. `#5` closes or narrows once capture step 1 has been run.
4. `polaris-learning/CLAUDE.md` claims the git lock blocker was fixed 2026-08-31. It was not, in a
   Cowork session on 2026-09-17; delete permission had to be re-granted.

---

## Verified vs open

**Verified** (read from the chart, the values and upstream docs, 2026-09-17): Polaris does not
auto-migrate its metastore schema; this repo carries `schema_v3.sql`; `#5521` affects 1.7.0+ and
returns 403, so it is **not** the 1.3.0 NPE; `delay_threshold` appears nowhere in chart, templates
or values; `hostAliases` is exposed for both postgresql and pgpool. Measured live 2026-09-17:
**pg-1 is the PostgreSQL primary**, pg-0 and pg-2 standbys; 2 replication slots;
`/bitnami/postgresql` is 203G.

**Open — everything about Polaris's runtime.** `helm get values benchmarks-polaris` has still never
been run, so the live replica count, the live logging configuration and the degree of divergence
from `polaris/values.yaml` are all unknown. 1.6.0's required schema version has not been looked up.
A general web search surfaces no upstream issue matching the `getPassthroughResolvedPath` NPE,
which means unreported or wrong search terms — not absent; a proper `gh issue list -R apache/polaris`
search has not been run.

**Related:** `postgresql/HANDOFF-toxiproxy-failover-2026-09-17.md` (the primary-unavailable harness,
deferred), `polaris-learning/diagnostics/polaris_replica_staleness.ipynb` (the ladder and the
staleness probe), `polaris-learning/.memory/sessions/2026-09-17-replica-staleness-probe.md`.
