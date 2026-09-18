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

**STEP 0 IS DONE as of 2026-09-18.** Kept in full for the record and for the next upgrade.

```bash
kubectl config current-context        # must equal orbstack -- halt if not

# 0a. THE ONE THAT CANNOT BE RECOVERED. DONE -- and it CLOSED #5: the working tree matched
#     the live release on all 210 keys, and `--all` added nothing over the supplied values,
#     so no setting was being served from a chart default. Take all three: the two
#     `get values` forms answer different questions (supplied vs in effect) and the manifest
#     is the before-state of every rendered object.
helm -n datahub-hynix get values benchmarks-polaris       > /tmp/polaris-values-1.3.0.yaml
helm -n datahub-hynix get values benchmarks-polaris --all > /tmp/polaris-values-1.3.0-all.yaml
helm -n datahub-hynix get manifest benchmarks-polaris     > /tmp/polaris-manifest-1.3.0.yaml
helm -n datahub-hynix history benchmarks-polaris          # 5 revisions; R5 deployed 2026-09-15

# 0b. Ten seconds, and it settles #15 hypothesis C (round-robin across replicas).
#     NOTE the selector: the chart's name IS `benchmarks-polaris`, so `polaris.name` renders
#     `benchmarks-polaris` and the label is app.kubernetes.io/name=benchmarks-polaris.
#     `=polaris` matches nothing. (Corrected 2026-09-18 after it returned empty.)
kubectl -n datahub-hynix get deploy,hpa,pods -l app.kubernetes.io/name=benchmarks-polaris
#   -> DONE 2026-09-18: deployment 1/1, ONE pod, HPA MINPODS 1 MAXPODS 3 REPLICAS 1,
#      cpu: 1%/80%, memory: 30%/80%. #15 hypothesis C is DEAD (no second pod's cache to
#      diverge from). #8 is RE-ARMED though -- the metrics that were <unknown> on 2026-09-09
#      are back, so the autoscaler can scale; it just has no reason to at 1% CPU.

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

**DONE 2026-09-18, and it found the thing this capture existed to find:**
`quarkus.log.console.level=INFO` **was already live** (revision 5, 2026-09-15), while the
committed `polaris/values.yaml` said `DEBUG`. The logging half of `afc88e2` therefore
reconciles the file to the release; it does not change the cluster. All ten DEBUG category
lines are live *underneath* that INFO handler, so they have been emitting nothing for days —
the inference is now measured, not argued. `polaris.event-listener.type` and its two buffer
settings match the values file exactly, so the plural-`types` rename **is** a real change.
See `active-issues.md` `#33`.

**`0c` is done: the metastore reports `version|3`.** Step 2's v3 → v4 migration is therefore
the right migration, and the script's own guard will agree. `0a` and `0b` are still outstanding
and `0a` is the perishable one.

---

## Step 1 - entity names. A forward-compatibility screen, NOT an upgrade blocker.

**Corrected 2026-09-18.** The first version of this step said 1.6.0's stricter entity-name
validation "can block the upgrade", following the Snowflake 1.6 blog's *"if you have existing
entities with these characters, you'll need to rename them before upgrading"*. **Upstream's own
docs are narrower, and they win:**

> These constraints apply to create, register, and rename operations only. Entities predating
> this validation are unaffected by read or update operations.

So existing entities do **not** stop the upgrade and do not need renaming to perform it. What
they break is *future* create / register / rename on those names. That still matters here --
the post-upgrade `#15` ladder creates catalogs and namespaces, and `polaris-learning` phase J
drives a nested namespace deliberately -- but it is a step 7 concern, not a step 2 gate.

**The actual rule** (upstream entities doc). A valid name:

- is not empty
- is not `.` or `..` -- the *whole* name, not "contains a dot"
- does not contain ISO control characters (**U+0000-U+001F or U+007F-U+009F**)
- does not contain any of: `/ : * ? " < > | # +`
- does not start or end with whitespace

Policy names are stricter still: letters, digits, `-` and `_` only.

Note what is **not** on that list: a backslash, and a dot anywhere but as the entire name. The
blog's rendering of the character set is an escaping artifact of `:*?"<>|#+`.

### The corrected screen

The control-character test uses `[[:cntrl:]]` plus an explicit C1 range built with `chr()`,
deliberately avoiding backslash-u escapes: those are a hazard in their own right, having
already been turned into real control bytes once while this file was being edited.

```bash
kubectl -n datahub-hynix exec -i benchmarks-postgresql-postgresql-ha-postgresql-1 -- \
  env PGPASSWORD=polaris psql -U polaris -d polaris <<'SQL'
SELECT count(*) AS live_entities FROM polaris_schema.entities WHERE drop_timestamp = 0;

SELECT realm_id, catalog_id, id, type_code, sub_type_code, name,
       CASE
         WHEN name = ''                       THEN 'empty'
         WHEN name IN ('.', '..')             THEN 'dot-name'
         WHEN name ~ '[[:cntrl:]]'            THEN 'control-char-c0'
         WHEN name ~ ('[' || chr(128) || '-' || chr(159) || ']') THEN 'control-char-c1'
         WHEN name ~ '[/:*?"<>|#+]'           THEN 'forbidden-char'
         WHEN name ~ '^[[:space:]]|[[:space:]]$' THEN 'edge-whitespace'
       END AS why
FROM polaris_schema.entities
WHERE drop_timestamp = 0
  AND ( name = ''
     OR name IN ('.', '..')
     OR name ~ '[[:cntrl:]]'
     OR name ~ ('[' || chr(128) || '-' || chr(159) || ']')
     OR name ~ '[/:*?"<>|#+]'
     OR name ~ '^[[:space:]]|[[:space:]]$' )
ORDER BY realm_id, catalog_id, id;
SQL
```

Heredoc with `exec -i`, not `-c`: the pattern contains both quote characters.

### Why the first screen's clean result did not settle it

The 2026-09-18 run of the *original* query returned 0 rows, but that query was wrong in both
directions and its clean result was partly luck:

| original clause | what it actually did |
|---|---|
| `name LIKE '%.%'` | flagged **any** name containing a dot -- far broader than the real `.`/`..` rule. 0 rows means no name contains a dot at all: stronger than needed, not wrong. |
| `name LIKE '%\%'` | **bug.** Backslash is LIKE's default escape character, so this matched names ending in a literal `%`, not names containing a backslash. |
| the `~` character class | covered `/ < > " \| ? *` and, via the doubled backslash, a literal backslash -- which is not actually forbidden |
| -- | **missed `#` and `+`**, missed the C1 control range **U+0080-U+009F**, and missed leading/trailing whitespace entirely |

So `#`, `+`, the C1 range and edge-whitespace have **not** been screened. Re-run the corrected
query above before the ladder, and record the result as
"entity-name screen clean, N live entities, <date>" -- with N, so the next reader knows the
screen ran against a populated metastore rather than an empty one.

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

# 2c. Get the AUTHORITATIVE schema-v4.sql, from the 1.6.0 image, via Docker -- NOT from the
#     running pod. See "Why 2c is not a kubectl exec" below. This also pre-pulls the image,
#     which stops the step-4 rollout stalling on a cold pull.
docker pull apache/polaris:1.6.0
cid=$(docker create apache/polaris:1.6.0)
docker cp "$cid":/deployments /tmp/polaris-1.6.0-deployments
docker rm "$cid"

# Find the jar carrying the resource (macOS has unzip; the image may not).
for j in $(find /tmp/polaris-1.6.0-deployments -name '*.jar'); do
  unzip -l "$j" 2>/dev/null | grep -q 'schema-v4\.sql' && echo "FOUND: $j"
done

# The jar, found 2026-09-18 (NOTE: if /tmp/polaris-1.6.0-deployments already existed,
# `docker cp` nests a second identical copy under .../deployments/lib/main/ -- either works):
JAR=/tmp/polaris-1.6.0-deployments/lib/main/org.apache.polaris.polaris-relational-jdbc-1.6.0.jar
unzip -l "$JAR" | grep schema-v          # every schema version the jar carries

# Extract v4 AND v3. Extracting v3 is not belt-and-braces -- it closes a real gap, below.
unzip -p "$JAR" postgres/schema-v4.sql > /tmp/schema-v4.shipped.sql
unzip -p "$JAR" postgres/schema-v3.sql > /tmp/schema-v3.shipped.sql
wc -l /tmp/schema-v*.shipped.sql          # 0 lines = wrong inner path; re-read the listing

# CROSS-CHECK THE BASELINE. Everything concluded about this migration was computed against
# THIS REPO's schema_v3.sql, on CLAUDE.md's claim that it is "the ASF-shipped file and the
# authority". If that is false, claim 1 was checked against the wrong baseline and the
# additive-only finding does not hold. This is the first chance anyone has had to test it.
diff /tmp/schema-v3.shipped.sql postgresql/schema/schema_v3.sql \
  && echo "BASELINE OK: repo schema_v3.sql is byte-identical to the shipped v3"
# Whitespace/indentation differences are fine -- the repo copy was reformatted at some point.
# A difference in any column, type, constraint, index or the version value is NOT: stop.
#
# Check it MECHANICALLY, not by eye -- a plain diff is useless here, because the shipped file
# is a FULL schema and ours is a delta plus a guard, so they differ almost everywhere while
# still agreeing on everything that matters:
python3 postgresql/schema/verify_v4_transcription.py \
    --v3        /tmp/schema-v3.shipped.sql \
    --v4        /tmp/schema-v4.shipped.sql \
    --migration postgresql/schema/migrate_v3_to_v4.sql
# Baseline is the SHIPPED v3, not the repo copy -- see the note under the script's description.
# PASS -> either script is safe in 2e. FAIL -> run the SHIPPED file, not ours, and read why.
#
# IF THE SHIPPED FILE IS IN HAND, PREFER RUNNING IT DIRECTLY in 2e -- every statement in v4
# is IF NOT EXISTS, so applying the full v4 script to a v3 database *is* the migration, from
# the authoritative source. Our transcribed script is the fallback. The one thing the shipped
# file does NOT do is refuse to run on a non-v3 database; ours guards that.

# 2d. Scale Polaris to 0. The events table is written on every API call.
kubectl -n datahub-hynix scale deploy/benchmarks-polaris --replicas=0
# NOTE: autoscaling.enabled is true with maxReplicas 3. Check whether the HPA scales it back
# up (kubectl -n datahub-hynix get hpa) before assuming replicas stays at 0.

# 2e. Migrate, against the PRIMARY, not through pgpool's load balancer.
#     `exec -i` with the script on stdin. NOT port-forward + a local psql: port-forward is a
#     blocking command (CLAUDE.md, Persistent Server Block) and it assumes a psql on the Mac.
kubectl -n datahub-hynix exec -i benchmarks-postgresql-postgresql-ha-postgresql-1 -- \
  env PGPASSWORD=polaris psql -U polaris -d polaris -v ON_ERROR_STOP=1 \
  < postgresql/schema/migrate_v3_to_v4.sql

# 2f. Read it back from the database, not from the script's exit code.
kubectl -n datahub-hynix exec -i benchmarks-postgresql-postgresql-ha-postgresql-1 -- \
  env PGPASSWORD=polaris psql -U polaris -d polaris <<'SQL'
SELECT * FROM polaris_schema.version;
\dt polaris_schema.*
SQL
```

Expect `version_value = 4` and the three new tables present. The script wraps everything in
one transaction and writes the version row **last**, so a failure leaves the database at 3.

### 2c IS DONE — 2026-09-18. Both checks ran, and one of them found something.

Kade extracted both files from
`/tmp/polaris-1.6.0-deployments/lib/main/org.apache.polaris.polaris-relational-jdbc-1.6.0.jar`
and ran the verifier with the **shipped** v3 as the baseline.

**The verifier PASSED.** v3 10 objects, v4 21, v4 adds 11, the migration has 11 and no extras;
the 10 objects v3 and v4 share are declared identically. Declared versions 3 / 4 / 4. So the
delta is additive-only *measured against the distribution*, not against our own copy of it —
which is the circularity `ce72bde` existed to remove, and it came out in the runbook's favour.

**The baseline diff came back clean too.** `/tmp/schema-v3.shipped.sql` against
`postgresql/schema/schema_v3.sql`: **indentation only**, plus a missing trailing newline on the
repo copy. Every column, type, constraint, index and the version value are identical. The repo
copy is a reformatted shipped v3 — `CLAUDE.md`'s "ASF-shipped file and the authority" claim was
never tested before today, and it holds. `#F1`'s mistake is not sitting in the baseline.

**So do NOT vendor the two shipped files into the repo.** That was on the table; the diff
result removes the reason for it. `schema_v3.sql` *is* the shipped v3, and this repo already
has a duplicate-files problem (`.memory/repository-map.md`). If you want the v4 file kept, keep
it outside the repo — it is reproducible from the image in three commands.

**What the PASS did NOT cover, and what that cost.** The verifier's two original claims only
ever looked at `CREATE TABLE/INDEX/SCHEMA/VIEW`. In the shipped v3, **26 of 36 statements are
neither** — so "the transcription agrees with the shipped schema" was a statement about DDL
objects, not about the file. Grepping the shipped v4 for everything else found:

- **no** `CREATE FUNCTION` / `SEQUENCE` / `TYPE` / `TRIGGER`, **no** `GRANT`, **no** `ALTER`,
  and exactly one `INSERT` (the version row). The additive-only finding is intact.
- **two `COMMENT ON TABLE` statements the migration omitted** — shipped v4 lines 226 and 295,
  on `scan_metrics_report` and `commit_metrics_report`. Now added to
  `postgresql/schema/migrate_v3_to_v4.sql`. (Upstream comments only those two;
  `idempotency_records` carries none.)

Two table comments are harmless, which is precisely what makes them worth the fix: the blind
spot that hid them would equally have hidden a `CREATE FUNCTION`. The verifier now has a
**CLAIM 3** that compares residual statements — failing on a v4-added function, grant, alter
or seed insert the migration omits, and noting an omitted `COMMENT ON` rather than blocking on
it. Self-tested 2026-09-18: a round trip against a synthetic v4 reproduces the real run's
output exactly (PASS, and before the fix, the two notes), and two negative controls — v4 plus a
`CREATE FUNCTION`, v4 plus a `GRANT` — both trip CLAIM 3.

**Either script is now safe in 2e**, and the shipped file remains the preferable one; ours is
the fallback that guards the version. **2b, the dump, has still not been run** and is the
rollback for this step — it is the next thing to do, before 2d. Re-confirm pg-1 is still the
primary while you are there (`0c`'s note).

### Why 2c is not a `kubectl exec` into the running pod

The first version of this step was:

```
kubectl -n datahub-hynix exec deploy/benchmarks-polaris -- sh -c 'unzip -l /deployments/*.jar | grep schema-v'
```

It hung past 30s when run on 2026-09-18 and was abandoned — correctly, per CLAUDE.md's
*Timeout & Hang Guard*. But the hang is the less interesting fault. **That command could not
have answered the question even if it had returned:** the running pod is **1.3.0**, and
`schema-v4.sql` is a resource of the **1.6.0** distribution. 1.3.0 ships v3 at best. The
original text admitted as much in a parenthetical *underneath the command* and still put the
command first, which is how a step that cannot work gets run anyway.

Two smaller faults in it, worth remembering: `unzip` is not guaranteed in a UBI9 runtime image,
and `/deployments/*.jar` is a Quarkus thin jar (`quarkus-run.jar`) whose classes and resources
live under `/deployments/lib/`, so even on a 1.6.0 pod that glob is the wrong target.

The Docker route above avoids all of it: it reads the 1.6.0 image directly, needs nothing
installed in the image, touches no cluster object, and pre-pulls the image the upgrade is about
to need. OrbStack provides the Docker daemon — the same one OpenSearch runs under.

**Do not retry the exec form.** If Docker is unavailable for some reason, the fallback is to
skip verification, run the transcribed script (it is guarded and additive), and check the
shipped file after the upgrade from a 1.6.0 pod — at which point `/deployments/lib/` is the
place to look, not `/deployments/*.jar`.

### `verify_v4_transcription.py` — what it checks, and what a PASS does not mean

`postgresql/schema/verify_v4_transcription.py` compares three text files and exits non-zero if
any of the three claims behind the transcribed migration fails:

- **Claim 1, additive-only:** every object v3 and v4 share is declared *identically*, so no
  `ALTER` and no data rewrite is needed. A violation here means the migration is wrong in
  principle, not just in detail.
- **Claim 2, faithful transcription:** every object v4 adds over v3 appears in our migration,
  normalised-identical (comments, whitespace, case and `IF NOT EXISTS` folded out).

- **Claim 3, added 2026-09-18, nothing is invisible:** claims 1 and 2 only see
  `CREATE TABLE/INDEX/SCHEMA/VIEW`. Claim 3 takes every *other* statement — `COMMENT ON`,
  `GRANT`, `CREATE FUNCTION`/`SEQUENCE`/`TYPE`/`TRIGGER`, seed `INSERT`s — and fails if v4
  adds one the migration omits, except for an annotation (`COMMENT ON`), which is reported as
  a note. The transaction wrapper, `SET search_path`, psql meta-commands and the version-row
  write are excluded: their shape legitimately differs between a full schema and a delta, and
  `declared_version` already covers the last of them. **This claim exists because the first
  real run of this script passed without it while the migration was two statements short.**

It also refuses a v3 file not declaring 3, a v4 file not declaring 4, a migration not setting
4, any `ALTER TABLE` in the migration, a missing transaction, and any object our script creates
that is in neither v3 nor v4.

**Self-tested 2026-09-18** with a round trip (synthetic v4 = v3 + the migration's additive
statements → PASS) and two negative controls (a column type changed in a new table → claim 2
trips; a column type changed in a *shared* table → claim 1 trips). That self-test earned its
keep: the first version of the script read **zero** statements from the migration, because an
apostrophe inside a `--` comment opened a bogus string literal and swallowed every following
semicolon. It reported eleven CLAIM 2 failures — which reads exactly like a bad transcription
rather than a bad parser. **A verifier that has not been shown to fail on a known-bad input is
not evidence.**

**Pass the SHIPPED v3 as `--v3`, not the repo copy.** Every conclusion in this runbook about
the v3 → v4 delta was computed against `postgresql/schema/schema_v3.sql`, trusting CLAUDE.md's
claim that it is the ASF-shipped authority. Feeding that same file back as the baseline would
check the transcription against its own assumption. The jar ships v3 too, so use it — and
`diff` the two while you are there: if they differ in substance, `#F1`'s mistake has been
sitting in the baseline all along and the additive-only finding needs redoing.

**A PASS is not a green light for the migration.** It says three files agree. It does not run
SQL, does not connect to anything, and does not predict that the migration will succeed. Step
2f still reads `version_value` back out of the database.

**Every SQL step in this runbook uses `kubectl exec -i … env PGPASSWORD=polaris psql`**, with
the statements on stdin via heredoc or `<`. That is the pattern proven to work here on
2026-09-18. Three reasons it is the only one used:

- **`port-forward` blocks.** It holds the terminal until interrupted, which CLAUDE.md's
  *Persistent Server Block* prohibits, and in a runbook it silently turns a paste-able sequence
  into one that stops dead at that line. The original step 2e did exactly that.
- **`psql` on the Mac is not a given**, and its version need not match the server's.
- **`exec` on `…-postgresql-1` reaches the primary directly.** Through pgpool the read can be
  balanced onto a standby — the mechanism `#15` hypothesis A is about — so a version check
  through pgpool would beg the question it is asked to settle.

`PGPASSWORD` must be passed or psql prompts and the exec hangs with no output. The pod
defaults to the `postgresql` container, which is the right one; the `Defaulted container`
notice is normal. Note CLAUDE.md's *Direct PostgreSQL* line still gives `port-forward` — that
is for an interactive session you drive yourself, not for scripted steps.

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

1. `quarkus.log.console.level=INFO`. Read this one carefully, because it discriminates
   against two things and not against a third. It differs from the upstream **chart default
   `ALL`**, so the block is not silently un-applied. It differs from what the committed file
   said before `afc88e2` (`DEBUG`). It does **not** differ from the live release — step 0d
   measured `INFO` already running at revision 5. So seeing INFO here confirms the values
   are being read; it does **not** confirm that anything changed.
2. `quarkus.log.category."…".level=DEBUG` appears **nowhere**.
3. `polaris.event-listener.types=persistence-in-memory-buffer`, with `buffer-time=PT5S` and
   `max-buffer-size=1000` still present.

**Do not assert on `quarkus.log.console.format`.** It is dead config: `extraEnv` sets
`QUARKUS_LOG_CONSOLE_JSON_ENABLED=true`, environment variables sit at SmallRye ordinal 300
against `application.properties`' 250, so the console emits **JSON** and the format string in
`values.yaml` is ignored. The tier-2 Lua and report schema v6 parse that JSON, so the env var
— not `logging.console.json` — is what the pipeline depends on. 1.6.0 pins **Quarkus 3.36.3**
and upstream's own 1.6.0 chart emits `quarkus.log.console.json.enabled`, the property that env
var maps to, so JSON survives the upgrade. Confirm from the running pod in step 5 regardless:
if console output silently reverts to plain text, the tier-2 pipeline goes **quiet rather than
wrong**, which is harder to notice.

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

# THE CONSOLE IS STILL JSON. This is the one that breaks the tier-2 pipeline silently.
kubectl -n datahub-hynix logs deploy/benchmarks-polaris --tail=5
#   -> every line must be a JSON object. Plain `2026-.. INFO [..]` text means
#      QUARKUS_LOG_CONSOLE_JSON_ENABLED stopped being honoured; stop and fix before trusting
#      any polaris-logs-* window or report counter.

# The JVM accepted the GC flags. -XX:+ZGenerational is valid on JDK 21 and REMOVED in JDK 25;
# 1.6.0's image is ubi9/openjdk-21-runtime so this should be clean -- but an unrecognized VM
# option presents as CrashLoopBackOff with nothing useful in the Polaris log, so check.
kubectl -n datahub-hynix logs deploy/benchmarks-polaris | grep -i 'Unrecognized VM option' \
  || echo "GC flags OK"

# The management port is 8182 here, not the 8282 upstream docs use. exec, not port-forward --
# port-forward blocks the terminal (CLAUDE.md, Persistent Server Block).
kubectl -n datahub-hynix exec deploy/benchmarks-polaris -- \
  curl -sf http://localhost:8182/q/health
# If curl is absent from the image, the readiness probe already answers this: a pod reporting
# READY 1/1 has passed it. Do not reach for port-forward to find out.

# Schema version, from the database.
kubectl -n datahub-hynix exec benchmarks-postgresql-postgresql-ha-postgresql-1 -- \
  env PGPASSWORD=polaris psql -U polaris -d polaris -tAc \
  "SELECT * FROM polaris_schema.version"                   # expect version|4

# The events table is still being written -- the listener survived the upgrade.
kubectl -n datahub-hynix exec benchmarks-postgresql-postgresql-ha-postgresql-1 -- \
  env PGPASSWORD=polaris psql -U polaris -d polaris -tAc \
  "SELECT count(*), max(timestamp_ms) FROM polaris_schema.events"
```

**Do not expect the log volume to drop.** The original version of this runbook said one
`polaris-logs-*` window after the upgrade should be materially smaller than one before. That
was wrong, and step 0d is why: stdout has been INFO-only since revision 5, so there is no
DEBUG traffic left for the INFO threshold to remove. The right assertion is the opposite —
**one window after should be comparable to one before**, allowing for whatever 1.6.0's own
logging changes add or remove. Use `step10` / `step11`, not Dev Tools copies (MEMORY.md).

If a window *does* shrink materially, that is an unexplained change, not a success: something
other than the threshold moved, and it needs a cause before the report schema v6 counters are
trusted again.

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
§8 and §10. The reading table in the 2026-09-17 handoff still applies **minus its hypothesis
C row**: step 0b measured one Polaris pod, so cross-pod cache divergence is not the mechanism
on this cluster. That leaves **A** (stale reads through Pgpool) and **B** (a 1.3.0
resolver/entity-cache bug — and this upgrade is the experiment for B, for free).

**The ladder's own names must satisfy 1.6.0's validation** (step 1). It creates catalogs and
namespaces, so any probe name carrying `/ : * ? " < > | # +`, a leading/trailing space, or a
bare `.`/`..` will now be rejected at create time — a 400 where 1.3.0 gave a 200, which would
look like a new failure rather than a renamed rule. Check the notebook's probe names before
reading anything into the result.

Before the ladder run, decide whether to hold C dead for its duration: the HPA is live again
with `maxReplicas: 3`, so a ladder that loads Polaris past the target can reintroduce a
second pod mid-experiment and contaminate the result. `replicaCount: 1` with
`autoscaling.enabled: false` is the handoff's remedy C and also closes `#8`.

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

**Measured on the cluster 2026-09-18** (by Kade; this session has no cluster reach):

- **Metastore schema version 3** — `SELECT * FROM polaris_schema.version` → `version|3`, read
  from primary pg-1. The v3 → v4 migration applies. `#F1`'s mistake avoided: the file and the
  database agree, and that is now a fact rather than an assumption.
- **One Polaris pod.** Deployment `1/1`, HPA `MINPODS 1 MAXPODS 3 REPLICAS 1` at `cpu: 1%/80%,
  memory: 30%/80%`, age 30d. Kills `#15` hypothesis C; re-arms `#8` (the metrics that were
  `<unknown>` on 2026-09-09 are back).
- **`quarkus.log.console.level=INFO` was already live** at revision 5 (2026-09-15) while the
  committed file said `DEBUG`. The logging half of `afc88e2` reconciles the file to the
  release rather than changing it — and all ten DEBUG categories were live underneath that
  INFO handler, emitting nothing. `#5`, caught in the act.
- **The event listener matches the file exactly** — `type=persistence-in-memory-buffer`,
  `buffer-time=PT5S`, `max-buffer-size=1000`. The plural-`types` rename is a real change.
- **5 release revisions**, R1 2026-08-19 → R5 `deployed` 2026-09-15 17:34, chart
  `benchmarks-polaris-1.3.0` throughout. The pod is 39m old against a 30d deployment with
  `RESTARTS 0` — recreated without a Helm revision, so R5's ConfigMap was loaded 39 minutes
  before the capture, not in September (`#20`).
- **`#5` IS CLOSED, REFUTED.** `polaris/values.yaml` (working tree) matched the live release on
  **all 210 keys** bar the 14 `afc88e2` changed, and `--all` added nothing over the supplied
  values — so nothing was being served from a chart default either. The file *did* describe the
  running Polaris. The DEBUG-console scare was one uncommitted edit already applied at R5, and
  calling it "`#5` caught in the act" was wrong; retracted in `#33`.
- **The console emits JSON and `values.yaml` says it does not.**
  `QUARKUS_LOG_CONSOLE_JSON_ENABLED=true` in `extraEnv` (ordinal 300) beats
  `application.properties` (250), so `logging.console.json: false` and the whole
  `logging.console.format` string are inert. This is the genuine inert-config finding of the
  capture. Survives 1.6.0 (Quarkus 3.36.3; upstream's 1.6.0 chart emits the same
  `quarkus.log.console.json.enabled`).
- **`topologySpreadConstraints` selects `app.kubernetes.io/name: polaris` — zero pods.** The
  constraint has never influenced scheduling, in the file or the release. `#8`'s reasoning
  invokes `ScheduleAnyway` spreading that is not in effect. Left unchanged deliberately.
- **JVM flags safe.** `-XX:+UseZGC -XX:+ZGenerational` is valid on JDK 21 and 1.6.0's image is
  `ubi9/openjdk-21-runtime`. The flag is **removed in JDK 25** — watch it on any later release.
- **`bootstrapCredentials` renders empty**, so `POLARIS_BOOTSTRAP_CREDENTIALS` is an empty
  string. Fine while bootstrapped; supply it if the migration ever needs a re-bootstrap. The
  same manifest confirms `#9` — `password: "polaris"` plaintext in the rendered Secret.
- **`QUARKUS_DATASOURCE_JDBC_MAX_SIZE=300` per pod** — a write and its follow-up read almost
  certainly use different Agroal connections, so pgpool's `disable_load_balance_on_write`
  (session-scoped) cannot cover the create-then-resolve path. Strengthens `#15` hypothesis A
  and the case for the handoff's remedy A.

**Entity-name screen, 2026-09-18: 0 rows — but on the WRONG query.** The screen as first
written over-tested dots, had a LIKE-escape bug in its backslash clause, and never tested `#`,
`+`, the C1 control range or edge whitespace. 0 rows is real for what it did test and is
reassuring, not conclusive. Corrected query in step 1; re-run before the ladder. And the
framing was wrong in a more useful way: upstream's docs say the new validation applies to
create/register/rename only and **entities predating it are unaffected by read or update**, so
this was never an upgrade blocker.

**Open — everything else that needs the cluster.** In particular: `helm get values
benchmarks-polaris` has *still* never been run, so the live replica count, the live logging
config and the degree of divergence from `polaris/values.yaml` (`#5`) remain unknown; the
live `polaris_schema.version` has not been read; the entity-name screen has not been run;
`helm lint` and `--dry-run=client` have not been run against the edited chart.

**Also open, and not investigated here:** this repo emits `quarkus.log.console.enabled`
while upstream's 1.3.0 chart emitted `quarkus.log.console.enable`. Both default to on, so
nothing observable turned on this — but if the console handler ever needs to be *disabled*,
check which spelling 1.6.0 actually reads first.
