# RUNBOOK — Polaris 1.3.0-incubating → 1.6.0

**2026-09-18. Status: PREPARED, NOT EXECUTED.** The values/chart change and the schema
migration script are committed. No cluster command has been run — this was prepared in a
Cowork session, which has no `kubectl`, `helm` or `psql` reach (CLAUDE.md, *Cowork sessions
have no cluster reach*). Everything below is for Kade to run, in order.

Supersedes the ordering in [`HANDOFF-upgrade-1.6.0-2026-09-17.md`](HANDOFF-upgrade-1.6.0-2026-09-17.md),
which stays as the record of why the upgrade goes before `#15`. **Three of that document's
assumptions turned out to be wrong — see [What changed](#what-changed-since-the-2026-09-17-handoff).**

---

## What is already committed

| file | change |
|---|---|
| `polaris/values.yaml` | `image.tag` `1.3.0-incubating` → **`1.6.0`**; console threshold **INFO** (Kade's decision); all 13 DEBUG log categories → INFO; version-pinned doc links → 1.6.0 |
| `polaris/Chart.yaml` | `version` and `appVersion` → **`1.6.0`** |
| `polaris/templates/configmap.yaml` | emits `polaris.event-listener.types` (plural list) instead of the singular key, deprecated upstream since 1.5.0 |
| `postgresql/schema/migrate_v3_to_v4.sql` | the v3 → v4 migration, additive only |

**Nothing about Polaris's runtime shape was touched** — `replicaCount`, `autoscaling`,
persistence, auth, realms, the event listener type and the log PVC are all unchanged. The
standing rule *Polaris is not to be changed* is intact; this is a version bump plus one
logging decision.

---

## Step 0 — the perishable capture. Before the first mutating command.

Unchanged from the handoff, and still the thing that cannot be recovered afterwards.

```bash
kubectl config current-context        # must equal orbstack -- halt if not

# 0a. THE ONE THAT CANNOT BE RECOVERED. Closes or narrows #5.
helm -n datahub-hynix get values benchmarks-polaris > /tmp/polaris-values-1.3.0.yaml
helm -n datahub-hynix history benchmarks-polaris

# 0b. Ten seconds, and it settles #15 hypothesis C (round-robin across replicas).
#     NOTE the selector: the chart's name IS `benchmarks-polaris`, so `polaris.name` renders
#     `benchmarks-polaris` and the label is app.kubernetes.io/name=benchmarks-polaris.
#     `=polaris` matches nothing. (Corrected 2026-09-18 after it returned empty.)
kubectl -n datahub-hynix get deploy,hpa,pods -l app.kubernetes.io/name=benchmarks-polaris

# 0c. DONE 2026-09-18 -- the live metastore is at schema version 3. CONFIRMED, not inferred.
#     Exec the PRIMARY pod directly, not pgpool: a read through pgpool can be load-balanced
#     onto a standby, and PGPASSWORD must be passed or psql prompts and the exec hangs.
kubectl -n datahub-hynix exec benchmarks-postgresql-postgresql-ha-postgresql-1 -- \
  env PGPASSWORD=polaris psql -U polaris -d polaris -tAc "SELECT * FROM polaris_schema.version"
#   -> version|3     (pg-1 is the primary as of 2026-09-17; re-confirm before the migration)

# 0d. Optional but cheap: the #15 baseline ladder on 1.3.0.
#     polaris-learning/diagnostics/polaris_replica_staleness.ipynb, sections 8 and 10.
```

**Also capture the config that is about to change**, so the logging decision is measurable
rather than asserted:

```bash
kubectl -n datahub-hynix get cm benchmarks-polaris -o jsonpath='{.data.application\.properties}' \
  | grep -E 'quarkus\.log|event-listener' > /tmp/polaris-log-config-1.3.0.properties
```

**`0c` is done: the metastore reports `version|3`.** Step 2's v3 → v4 migration is therefore
the right migration, and the script's own guard will agree. `0a` and `0b` are still outstanding
and `0a` is the perishable one.

---

## Step 1 — pre-flight: entity names. NEW, and it can block the upgrade.

**1.6.0 tightened entity-name validation.** Upstream's own guidance: entities whose names
contain control characters, dots, backslashes, colons and similar special characters *must be
renamed before upgrading*. This platform's catalogs and namespaces were created by test
ladders, so this is a real risk, not a formality.

Screen the metastore first — read-only:

```sql
-- against the primary (pg-1 as of 2026-09-17; confirm, do not assume pg-0). Wrapper:
--   kubectl -n datahub-hynix exec benchmarks-postgresql-postgresql-ha-postgresql-1 -- \
--     env PGPASSWORD=polaris psql -U polaris -d polaris -c "<the query>"
SELECT realm_id, catalog_id, id, type_code, sub_type_code, name
FROM polaris_schema.entities
WHERE drop_timestamp = 0
  AND (name ~ '[\x00-\x1F\x7F]'   -- control characters
    OR name LIKE '%.%'
    OR name LIKE '%\%'
    OR name LIKE '%:%'
    OR name ~ '[/\\<>"|?*]')
ORDER BY realm_id, catalog_id, id;
```

**This query is a screen, not the rule.** It was written from upstream's prose description,
not from 1.6.0's validation code. If it returns rows, confirm the actual rejected character
set against the 1.6.0 validation source before renaming anything — and rename on **1.3.0**,
while the old validation still lets you.

If it returns zero rows, record that: "entity-name screen clean, N entities, <date>".

---

## Step 2 — the metastore migration. v3 → v4.

**1.6.0 requires schema v4.** Not v5 — see [What changed](#what-changed-since-the-2026-09-17-handoff).

The delta is **additive only**: three indexes on existing tables, plus
`idempotency_records`, `scan_metrics_report`, `commit_metrics_report` and their indexes. No
`ALTER`, no column type change, no data rewrite. `events` is byte-for-byte the same table it
is on v3.

```bash
# 2a. Commit the tree first -- this is the risky step CLAUDE.md's rule is about. (Done: see above.)

# 2b. Dump the metastore. Non-negotiable; this is the rollback.
kubectl -n datahub-hynix exec benchmarks-postgresql-postgresql-ha-postgresql-1 -- \
  env PGPASSWORD=polaris pg_dump -U polaris -d polaris -Fc > /tmp/polaris-metastore-pre-v4.dump
ls -l /tmp/polaris-metastore-pre-v4.dump   # a 0-byte dump is the classic silent failure here

# 2c. Diff the committed script against the v4 script the 1.6.0 image actually ships.
#     If the shipped file is available, PREFER RUNNING IT DIRECTLY -- every statement in v4
#     is IF NOT EXISTS, so applying the full v4 script to a v3 database *is* the migration.
kubectl -n datahub-hynix exec deploy/benchmarks-polaris -- \
  sh -c 'unzip -l /deployments/*.jar | grep schema-v'
# (run this while 1.3.0 is still up only to learn the path; the v4 resource lives in the
#  1.6.0 image, so the authoritative copy needs a 1.6.0 container -- see note below)

# 2d. Scale Polaris to 0. The events table is written on every API call.
kubectl -n datahub-hynix scale deploy/benchmarks-polaris --replicas=0
# NOTE: autoscaling.enabled is true with maxReplicas 3. Check whether the HPA scales it back
# up (kubectl -n datahub-hynix get hpa) before assuming replicas stays at 0.

# 2e. Migrate, against the PRIMARY, not through pgpool's load balancer.
kubectl -n datahub-hynix port-forward pod/benchmarks-postgresql-postgresql-ha-postgresql-1 5433:5432
psql -h localhost -p 5433 -U polaris -d polaris -v ON_ERROR_STOP=1 \
  -f postgresql/schema/migrate_v3_to_v4.sql

# 2f. Read it back from the database, not from the script's exit code.
psql -h localhost -p 5433 -U polaris -d polaris -c "SELECT * FROM polaris_schema.version;"
psql -h localhost -p 5433 -U polaris -d polaris -c "\dt polaris_schema.*"
```

Expect `version_value = 4` and the three new tables present. The script wraps everything in
one transaction and writes the version row **last**, so a failure leaves the database at 3.

---

## Step 3 — render the chart. The gate, before the upgrade.

```bash
helm lint ./polaris
helm upgrade --install benchmarks-polaris ./polaris -f polaris/values.yaml \
  -n datahub-hynix --dry-run=client --debug > /tmp/polaris-1.6.0.render.txt
```

`helm lint` is not a render — both are required (CLAUDE.md). Then read the render, do not
just check the exit code:

```bash
grep -E 'quarkus\.log\.(level|console|file)|quarkus\.log\.category|event-listener' \
  /tmp/polaris-1.6.0.render.txt
diff <(sort /tmp/polaris-log-config-1.3.0.properties) <(...)   # against the 0c capture
```

**Three things to confirm in the render:**

1. `quarkus.log.console.level=INFO` — and note the upstream **chart default is `ALL`**, so
   INFO is a genuine narrowing, not a value that happens to match a default. This is the one
   assertion that discriminates (Configuration Policy).
2. `quarkus.log.category."…".level=DEBUG` appears **nowhere**.
3. `polaris.event-listener.types=persistence-in-memory-buffer`, with `buffer-time=PT5S` and
   `max-buffer-size=1000` still present.

Helm 4 defaults to server-side apply and the existing release already reports
`previous_release_apply_method=ssa`, so watch for field-manager conflicts on the upgrade —
a failure mode Helm 3 did not have.

---

## Step 4 — upgrade.

```bash
kubectl config current-context        # again
helm upgrade --install benchmarks-polaris ./polaris -f polaris/values.yaml -n datahub-hynix
kubectl -n datahub-hynix rollout status deploy/benchmarks-polaris
```

If step 2d scaled to 0 and the HPA has not restored it, scale back up before waiting on the
rollout.

A `helm upgrade` can change a ConfigMap **without restarting the pod** (`#20`). Polaris reads
`application.properties` at start, so if the pod did not restart, restart it:

```bash
kubectl -n datahub-hynix rollout restart deploy/benchmarks-polaris
```

---

## Step 5 — verify from the running object. Never from the values file.

```bash
# The image that is actually running.
kubectl -n datahub-hynix get pods -l app.kubernetes.io/name=benchmarks-polaris \
  -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[0].image}{"\n"}{end}'
# expect apache/polaris:1.6.0

# The log config that is actually loaded.
kubectl -n datahub-hynix get cm benchmarks-polaris -o jsonpath='{.data.application\.properties}' \
  | grep -E 'quarkus\.log|event-listener'

# The management port is 8182 here, not the 8282 upstream docs use.
kubectl -n datahub-hynix port-forward deploy/benchmarks-polaris 8182:8182
curl -s localhost:8182/q/health

# Schema version, from the database.
psql ... -c "SELECT * FROM polaris_schema.version;"        # 4

# The events table is still being written -- the listener survived the upgrade.
psql ... -c "SELECT count(*), max(timestamp_ms) FROM polaris_schema.events;"
```

Then confirm the logging change did what it was for: one window of `polaris-logs-*` after
the upgrade should be materially smaller than one before. Use `step10` / `step11`, not Dev
Tools copies (MEMORY.md).

---

## Step 6 — what the upgrade invalidates downstream

Nothing here is optional; each one is a number that silently becomes wrong.

- **`polaris-learning/log-coverage/spec/`** is the vendored 1.3.0 OpenAPI and it is the
  coverage run's *denominator* — `load_spec` builds the 63 operations and 286 cells from it.
  Every coverage number is invalid until `log-coverage/fetch_specs.sh` is re-run.
- **`polaris-learning/src/config/local.yaml`** carries `polaris_version: "1.3.0"` and flags
  derived from it. `purge_deletes_files: false` is annotated *"issue #379 present locally"* —
  re-test on 1.6.0 rather than assume.
- **The Lua retention policy and report schema v6** key on Polaris log *shapes*. The console
  format string is unchanged, but the DEBUG categories are gone, so the mix of lines the Lua
  sees changes. Compare one window against a v6 baseline before trusting the counters.
- **`#24`** (four operations answer 500 to a malformed request) and **`#15`** were both
  characterised with DEBUG categories on. Re-running either now needs the `--set` override
  recorded in `polaris/values.yaml`'s categories comment.

---

## Step 7 — then, and only then, the `#15` experiment

Re-run the identical ladder from `polaris-learning/diagnostics/polaris_replica_staleness.ipynb`
§8 and §10. The reading table in the 2026-09-17 handoff still applies and is not repeated here.

**Run the ladder with the DEBUG override**, not on the committed INFO config — the NPE stack
trace itself is logged at ERROR and survives INFO, but the persistence and storage DEBUG lines
that made the NPE legible do not. The override is one `helm upgrade --set` away and is written
out in the `categories:` comment in `polaris/values.yaml`.

Note also: the notebook's ladder runs as `root`, and this project has already learned once
that root is the least representative identity. Re-run as a seeded non-root principal before
drawing a line.

---

## Rollback

| what failed | rollback |
|---|---|
| render or lint (step 3) | nothing to undo; the tree is committed, fix forward |
| migration (step 2e) | the script is one transaction and writes the version row last — a failure leaves v3; if it partially applied anyway, restore `/tmp/polaris-metastore-pre-v4.dump` |
| upgrade (step 4) | `helm -n datahub-hynix rollback benchmarks-polaris <rev>` back to the 1.3.0 revision. **The metastore does not roll back with it** — v4 is a superset of v3 and 1.3.0 reads a v4 database's shared tables fine, but 1.3.0 will report an unexpected schema version. Decide before migrating whether that is acceptable, or plan to restore the dump too. |
| pod will not start on 1.6.0 | read `kubectl logs` for a config error first — an unknown property is logged, not fatal; a rejected entity name is (step 1) |

---

## What changed since the 2026-09-17 handoff

Three corrections. Each was established by reading upstream at tag `apache-polaris-1.6.0`,
not from the cluster — the cluster half is still unverified.

1. **1.6.0 requires schema v4, not v5.** `DatabaseType.java` at that tag declares latest
   schema version **4** for Postgres, CockroachDB and H2. The handoff's main stated risk —
   "the documented v5 step alters `events.catalog_id`, the table the audit event listener
   writes" — is a **1.7.0** concern. On 1.6.0 `events.catalog_id` stays `TEXT NOT NULL`.
   Upstream notes the `__realm__` placeholder that v5 cleans up "only ever existed in 1.6.0
   release candidates", which is consistent.
2. **The v3 → v4 migration is additive only**, so the main risk of this upgrade is much
   smaller than the handoff assumed. Object-by-object, v3 and v4 share identical definitions
   for `entities`, `grant_records`, `principal_authentication_data`,
   `policy_mapping_record` and `events`.
3. **The handoff said the working tree already carried `maxReplicas 3 → 1` uncommitted. It
   did not.** The only uncommitted change in `polaris/values.yaml` on 2026-09-18 was the
   console threshold `DEBUG → INFO`. `autoscaling.maxReplicas` is still **3** and
   `autoscaling.enabled` is still **true**, so `#8` (three pods appending to one shared log
   PVC) is still open and still armed. **Not changed here** — Polaris's runtime shape is out
   of scope for this commit. Decide it separately.

And one thing the handoff did not mention at all: the **entity-name validation tightening**
in step 1, which is the only part of this upgrade that can require changing data before you
can proceed.

---

## Verified vs open

**Verified** — read from upstream at tag `apache-polaris-1.6.0` and from upstream docs,
2026-09-18:

- 1.6.0's relational-JDBC latest schema version is **4**; the v3 → v4 delta is additive only.
- The v5 `events.catalog_id` `DROP NOT NULL` migration belongs to 1.7.0.
- The 1.6.0 image tag is **`1.6.0`** — no `-incubating`; Polaris graduated after 1.3.0.
- `polaris.event-listener.type` is **deprecated since 1.5.0**; 1.6.0 reads
  `polaris.event-listener.types` (list). `buffer-time` and `max-buffer-size` are unchanged.
- `polaris.authentication.*` property names are **unchanged** in 1.6.0 — upstream's
  `polaris.authenticationOptions` helper emits the same set this chart inlines.
- Upstream's chart default for `logging.console.threshold` is **`ALL`**; ours is INFO, so the
  setting discriminates against the default.
- 1.6.0 breaking change: the request's CDI context is no longer propagated to event
  listeners. `persistence-in-memory-buffer` is built-in, so this should not bite — but it is
  the listener that writes the `events` table, so confirm rows still arrive (step 5).
- Upstream's 1.6.0 chart has **no `eventListener` and no `opa` section** — both are local
  additions to this fork, so neither can drift with the upstream chart.
- `rateLimiter.type` is `no-op` here, so the `token-bucket.window` key that vanished from the
  upstream 1.6.0 chart is never emitted. Non-issue.

**Measured on the cluster 2026-09-18** (by Kade, not this session): the live metastore is at
**schema version 3** — `SELECT * FROM polaris_schema.version` → `version|3`, read from the
primary pg-1. So the v3 → v4 migration applies, and `#F1`'s mistake (inferring the version
from the file in this repo) has been avoided: the file and the database happen to agree, but
that is now a fact rather than an assumption.

**Open — everything else that needs the cluster.** In particular: `helm get values
benchmarks-polaris` has *still* never been run, so the live replica count, the live logging
config and the degree of divergence from `polaris/values.yaml` (`#5`) remain unknown; the
live `polaris_schema.version` has not been read; the entity-name screen has not been run;
`helm lint` and `--dry-run=client` have not been run against the edited chart.

**Also open, and not investigated here:** this repo emits `quarkus.log.console.enabled`
while upstream's 1.3.0 chart emitted `quarkus.log.console.enable`. Both default to on, so
nothing observable turned on this — but if the console handler ever needs to be *disabled*,
check which spelling 1.6.0 actually reads first.
