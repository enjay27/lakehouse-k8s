# Active issues — check here before trusting a value or a runbook

Status vocabulary: **OPEN** (will bite you), **OPEN QUESTION** (unknown, cheap to
settle), **RESOLVED-INSTRUCTIVE** (fixed, kept because the failure mode recurs).

## Open

**#33 — Polaris 1.6.0 is committed to the chart and NOT applied. The cluster still runs 1.3.0-incubating.** 2026-09-18.

`polaris/values.yaml` now pins `image.tag: "1.6.0"`, `polaris/Chart.yaml` says
`version`/`appVersion` 1.6.0, `polaris/templates/configmap.yaml` emits the plural
`polaris.event-listener.types`, all 13 DEBUG log categories are INFO and console threshold is
INFO (Kade's decision). **None of it has been rendered, linted or applied** — prepared in a
Cowork session with no `kubectl`/`helm`/`psql` reach. This is written-not-running
configuration, which in this repo is the whole game. Until step 3–5 of
[`polaris/RUNBOOK-upgrade-1.6.0.md`](../polaris/RUNBOOK-upgrade-1.6.0.md) have been run and
read back from the running object, **the running Polaris is 1.3.0 with DEBUG console output**
and the values file describes something else. Do not answer "what log level is Polaris at"
from the file.

**RETRACTION, same day.** The block below called the console-threshold discrepancy "`#5`
caught in the act". **It is not.** `helm get values` has since been run and the working tree
matched the live release on all 210 keys; the committed file lagged by one uncommitted edit
Kade had already applied at R5. See `#5`, now RESOLVED and refuted. What survives below is
correct and still matters: the threshold was already INFO, so `afc88e2`'s logging half does
not change the cluster, and the DEBUG categories were measurably inert.

**THE CONSOLE THRESHOLD WAS ALREADY INFO IN THE RUNNING RELEASE. The logging half of
`afc88e2` changes the FILE, not the cluster.** 2026-09-18, read from the live ConfigMap
`benchmarks-polaris` (revision 5, deployed 2026-09-15 17:34):

```
quarkus.log.console.level=INFO          <-- already INFO, while the committed file said DEBUG
quarkus.log.level=INFO
quarkus.log.console.enabled=true
quarkus.log.file.enabled=false
```

So the repo's `threshold: DEBUG` had not described the running Polaris since at least
revision 5. **This is `#5` caught in the act** — not a nesting error this time, just a values
file that drifted from a release nobody diffed. `afc88e2`'s logging change is a
**reconciliation of the file to reality**, not a change of behaviour, and it should be
described that way.

**And the inference about the DEBUG categories is now CONFIRMED from the running object, not
argued.** The same ConfigMap carries all ten `…level=DEBUG` category lines live —
`org.apache.polaris.service.auth`, `.service.context`, `.service.catalog`,
`.service.catalog.IcebergRestCatalogAdapter`, `.service.admin`, `core.persistence`,
`core.storage`, `.service.storage`, `DatasourceOperations`, plus `io.polaris{,.core,.service}`
— *underneath* `quarkus.log.console.level=INFO`. Quarkus takes the stricter of the two, so
**every one of them has been emitting nothing for at least three days.** Thirteen lines of
configuration, live, doing nothing.

**Consequence that must not be missed: the upgrade will NOT reduce `polaris-logs-*` volume.**
Stdout has been INFO-only since revision 5, so there is no DEBUG traffic left to remove.
Runbook step 5 originally said to expect a materially smaller window after the upgrade —
**that expectation was wrong and has been corrected.** If a window *does* shrink, something
else changed and it needs explaining, not celebrating.

**Also confirmed live, and matching the values file exactly:**
`polaris.event-listener.type=persistence-in-memory-buffer`, `buffer-time=PT5S`,
`max-buffer-size=1000`. So the plural-`types` rename in `afc88e2` is a **real** change to the
rendered config, unlike the logging half. And `quarkus.log.file.enabled=false` is live again,
which is `#11` (file logging reads as off and ships anyway) still unexplained.

**Release history:** 5 revisions, not the "ten upgrades of configuration" `#5` refers to.
R1 install 2026-08-19, R5 `deployed` 2026-09-15 17:34, chart `benchmarks-polaris-1.3.0`
throughout. The pod is 39m old against a 30d deployment with `RESTARTS 0`, so it was
**recreated** recently without a Helm revision — the running config was loaded from R5's
ConfigMap 39 minutes before the capture, not in September. Worth knowing before concluding
that a config change did or did not take (`#20`).

**THE CONSOLE IS EMITTING JSON, AND `values.yaml` SAYS IT IS NOT.** This is the inert-config
finding the threshold scare was mistaken for, and it is real. `extraEnv` carries:

```
QUARKUS_LOG_CONSOLE_JSON_ENABLED=true      # "JSON logging for Fluent Bit (Quarkus 3.29.4 new key)"
QUARKUS_LOG_FILE_JSON_ENABLED=true
QUARKUS_LOG_FILE_JSON_PRETTY_PRINT=false
```

Environment variables sit at SmallRye Config ordinal **300**; `application.properties` sits at
**250**. So the env var wins, and **`logging.console.json: false` plus the entire
`logging.console.format` string are dead configuration** — the ConfigMap dutifully renders
`quarkus.log.console.format=%d{...} %-5p [%c{2.}] (%t) [%X{requestId}] %s%e%n` and the running
Polaris ignores it. The tier-2 Lua and report schema v6 parse JSON, so the pipeline depends on
the env var, not on the two values-file keys that appear to govern it. **Anyone editing
`logging.console.format` is editing nothing.**

*Good news for the upgrade, and it is checked rather than hoped:* upstream's own 1.6.0 chart
emits `quarkus.log.console.json.enabled`, which is exactly the property
`QUARKUS_LOG_CONSOLE_JSON_ENABLED` maps to, and 1.6.0 pins **Quarkus 3.36.3** — later than the
3.29.4 the repo comment cites, same key family. So JSON console output survives 1.6.0. Confirm
from the running pod anyway; if it ever silently reverts to plain text, the entire tier-2
pipeline breaks and the report counters go quiet rather than wrong.

**THE `topologySpreadConstraints` SELECTOR MATCHES NOTHING.** In both the file and the live
release:

```
topologySpreadConstraints:
  - labelSelector:
      matchLabels:
        app.kubernetes.io/name: polaris      # <-- the label is `benchmarks-polaris`
```

The chart labels its pods `app.kubernetes.io/name: benchmarks-polaris` (`polaris.name` =
`default .Chart.Name`). So this constraint has selected zero pods for its entire life and has
never influenced scheduling. **This matters to `#8`**, whose text reasons about "a single-node
cluster with `ScheduleAnyway` spreading" — the spreading it invokes is not in effect. Same bug
class as the `=polaris` runbook selector fixed in `82525c3`; the pattern is that
`app.kubernetes.io/name` here is the *chart* name, and nothing errors when it matches nothing.
**Not changed in `afc88e2`** — it is Polaris runtime shape, and fixing it would arm a
constraint that has never run, which CLAUDE.md's Configuration Policy says to review line by
line first.

**JVM FLAGS: CHECKED, AND NOT A RISK FOR 1.6.0.** `extraEnv` sets
`GC_CONTAINER_OPTIONS=-XX:+UseZGC -XX:+ZGenerational`. `-XX:+ZGenerational` was introduced in
JDK 21, deprecated in 23, obsolete in 24 and **removed in 25** — on a JDK 25 image it is an
unrecognized VM option and the JVM refuses to start, which would present as CrashLoopBackOff
with nothing useful in the Polaris log. Polaris 1.6.0's image is
`registry.access.redhat.com/ubi9/openjdk-21-runtime` (`Dockerfile.jvm` at tag
`apache-polaris-1.6.0`), the same JDK 21 family as 1.3.0, so the flag stays valid. **Forward
watch item:** any future Polaris release that moves its base image to JDK 25 turns this env
var into a hard startup failure.

**`bootstrapCredentials` RENDERS EMPTY.** `polaris/values.yaml` has `bootstrapCredentials`
commented out while `persistence.relationalJdbc.createSecret: true`, so the rendered Secret
carries the key with no value (`bootstrapCredentials:` in the manifest) and
`POLARIS_BOOTSTRAP_CREDENTIALS` resolves to an empty string. Harmless while the metastore is
already bootstrapped; **relevant if the v3 → v4 migration ever goes wrong badly enough to
want a re-bootstrap**, because the credentials would have to be supplied at that moment. The
same manifest confirms `#9` — `password: "polaris"` in plaintext in the rendered Secret.

**`QUARKUS_DATASOURCE_JDBC_MAX_SIZE=300` per pod, MIN_SIZE 10 — this strengthens `#15`
hypothesis A.** With up to 300 Agroal connections, a write and the read that immediately
follows it are almost certainly on *different* connections, and pgpool's
`disable_load_balance_on_write = always` pins only *within* one session. So the one mechanism
that would have protected the create-then-resolve path does not cover it, and with
`delay_threshold` unset (pgpool default 0, checked nowhere) lag is never consulted before a
read is balanced onto a standby. The handoff's remedy A —
`database_redirect_preference_list = 'polaris:primary'` — addresses exactly this.

**The v4 diff is now mechanical: `postgresql/schema/verify_v4_transcription.py`.** 2026-09-18.

A plain `diff` of the shipped `schema-v4.sql` against our `migrate_v3_to_v4.sql` is useless —
the shipped file is a full schema, ours is a delta plus a guard, so they differ almost
everywhere while agreeing on everything that matters. The script checks the two claims the
transcription rests on: **(1) additive-only** — every object v3 and v4 share is declared
identically; **(2) faithful** — every object v4 adds appears in ours, normalised-identical. It
also rejects wrong declared versions, any `ALTER TABLE`, a missing transaction, and any object
ours creates that is in neither file.

**Self-tested, and the self-test mattered.** Round trip (synthetic v4 = v3 + the migration's
additive statements) → PASS; column type changed in a new table → claim 2 trips; column type
changed in a *shared* table → claim 1 trips. The first version of the script parsed **zero**
statements out of the migration: an apostrophe inside a `--` comment ("1.6.0's backend") opened
a bogus string literal and swallowed every following semicolon. It printed eleven CLAIM 2
failures, which reads exactly like a bad transcription rather than a bad parser. **A verifier
not shown to fail on a known-bad input is not evidence** — that is the lesson, and it is the
same shape as the entity-name screen whose clean result came from a broken predicate.

A PASS means three text files agree. It does not run SQL and does not predict the migration
will succeed; step 2f still reads `version_value` back from the database.

**STEP 2c ASKED A 1.3.0 POD FOR A 1.6.0 FILE.** 2026-09-18, found by Kade running it.

`kubectl exec deploy/benchmarks-polaris -- sh -c 'unzip -l /deployments/*.jar | grep schema-v'`
hung past 30s and was abandoned, correctly, under CLAUDE.md's *Timeout & Hang Guard*. **The
hang is the lesser fault.** The command could not have answered its question if it had
returned: the running pod is 1.3.0 and `schema-v4.sql` is a **1.6.0** resource. I wrote that
caveat into a parenthetical *below* the command and left the command first — which is exactly
how a step that cannot work gets run anyway. Two further faults: `unzip` is not guaranteed in a
UBI9 runtime image, and `/deployments/*.jar` is the Quarkus thin jar, with resources under
`/deployments/lib/`, so the glob is the wrong target even on a 1.6.0 pod.

Replaced with a Docker route against the 1.6.0 image — `docker create` + `docker cp
/deployments`, then `unzip` on the Mac, which has it. It reads the right image, needs nothing
installed in the container, touches no cluster object, and **pre-pulls the image the upgrade is
about to need**, which removes a cold-pull stall from step 4. OrbStack supplies the daemon.

Standing note: **do not retry the exec form.** If Docker is unavailable, skip the verification,
run the transcribed script (guarded, additive, refuses on a non-v3 database) and diff the
shipped file after the upgrade from a 1.6.0 pod, looking in `/deployments/lib/`.

**STEP 2's SQL INVOCATION WAS WRONG, AND IT BROKE A CLAUDE.md RULE.** 2026-09-18, found by
Kade running it.

The runbook's step 2e said:

```
kubectl -n datahub-hynix port-forward pod/...postgresql-1 5433:5432
psql -h localhost -p 5433 -U polaris -d polaris -f postgresql/schema/migrate_v3_to_v4.sql
```

Three faults. **`port-forward` is a blocking command** — CLAUDE.md's *Persistent Server Block*
prohibits exactly this, and in a runbook it turns a paste-able sequence into one that stops dead
at that line with no error. **It assumes a `psql` on the Mac**, of unknown version. And it was
inconsistent with the `kubectl exec -i … env PGPASSWORD=polaris psql` pattern that had already
been proven to work in step 0c and step 1 — I had the working pattern in front of me and wrote a
different one for the step that mutates the database.

Every SQL step in the runbook and the migration script's own header now use
`kubectl exec -i …` with the statements on stdin. **`-i`, never `-it`:** a TTY adds carriage
returns and can corrupt piped SQL. `PGPASSWORD` must be passed or psql prompts and the exec
hangs with no output. Step 5's `curl` health check had the same port-forward fault and is now an
`exec`, with the note that a pod reporting `READY 1/1` has already passed its readiness probe.

Note CLAUDE.md's *Direct PostgreSQL* line does give `port-forward` — that is for an interactive
session a human drives, not for scripted runbook steps. The rule and the example are not in
conflict; I read the example as licence and skipped the rule.

**STEP 1 CORRECTED: the entity-name tightening is NOT an upgrade blocker, and the first screen
asked the wrong question.** 2026-09-18.

The runbook's step 1 said 1.6.0's stricter name validation "can block the upgrade", taken from
the Snowflake 1.6 blog's *"you'll need to rename them before upgrading"*. Upstream's entities
doc is narrower and wins: **"These constraints apply to create, register, and rename operations
only. Entities predating this validation are unaffected by read or update operations."** So
existing entities do not gate the upgrade. What they break is future create/register/rename —
which still matters, because the post-upgrade `#15` ladder creates catalogs and namespaces and
`polaris-learning` phase J drives a nested namespace.

**The rule, from the doc.** A valid name: not empty; not `.` or `..` (the *whole* name); no ISO
control characters (U+0000-U+001F or U+007F-U+009F); none of `/ : * ? " < > | # +`; no leading
or trailing whitespace. Policy names stricter still: letters, digits, `-`, `_` only. **A
backslash is not forbidden** — the blog's character list is an escaping artifact.

**The screen returned 0 rows, and the screen was wrong in both directions.** Kade ran it; the
result is real for what it tested and is reassuring. But:

- `name LIKE '%.%'` flagged any name *containing* a dot, far broader than `.`/`..`. 0 rows
  there is stronger than needed, not wrong.
- `name LIKE '%\%'` was a **bug**: backslash is LIKE's default escape character, so it matched
  names ending in a literal `%`, not names containing a backslash. Backslash was covered
  anyway by the regex clause — and is not forbidden, so it never mattered.
- **`#`, `+`, the C1 range U+0080-U+009F and edge whitespace were never tested at all.**

Corrected query in the runbook's step 1, using `[[:cntrl:]]` and a `chr(128)`/`chr(159)` range
rather than backslash-u escapes. **Re-run it before the ladder.** Two lessons worth keeping:
a screen written from prose instead of the spec tests the prose, and a 0-row result is only as
good as the predicate.

**Watch backslash-u escapes in this repo's markdown.** Writing `[\u0000-\u001F]` into the
runbook produced *real* NUL / 0x1F / 0x7F / 0x9F bytes in the file, which silently killed two
edit attempts before the cause was found. Any SQL or Lua pattern committed here should use
POSIX classes or `chr()` instead.

**Step 0 progress, 2026-09-18 (Kade ran these; this session cannot):**
`0c` **DONE — the live metastore is at schema version 3**, read from primary pg-1:
`SELECT * FROM polaris_schema.version` → `version|3`. The repo's `schema_v3.sql` and the
database agree, which is now measured rather than assumed (`#F1`'s mistake avoided). So the
v3 → v4 migration is the correct one. `0b` **DONE** — one pod, `REPLICAS 1`, HPA idle at `cpu: 1%/80%, memory: 30%/80%`,
`MAXPODS 3`. This kills `#15` hypothesis C and re-arms `#8`; see both entries.
`0d` **DONE** — the live log/event-listener config, above.
**`0a` DONE — all three captures.** `helm get values` (plain and `--all`) and
`helm get manifest`, plus `helm history` (5 revisions). This closes `#5` (refuted, see above)
and is where the JSON-console, topology-selector, ZGC and pool-size findings came from.
**Step 0 is now complete.** Next is step 1, the entity-name screen — the only remaining
pre-flight that can block the upgrade.

**Two command corrections, both mine, both worth keeping:**

* The label selector is **`app.kubernetes.io/name=benchmarks-polaris`**, not `=polaris`.
  `_helpers.tpl`'s `polaris.name` is `default .Chart.Name`, and this chart's `Chart.yaml`
  `name:` is `benchmarks-polaris` — so the label follows the chart name, not the upstream
  project name. `=polaris` returns empty, silently. Fixed everywhere in the runbook and the
  roadmap assertions.
* Read the metastore by **exec'ing the primary pod directly with `env PGPASSWORD=...`**, not
  through pgpool. Through pgpool the read can be load-balanced onto a standby (the whole
  subject of `#15` hypothesis A), and without `PGPASSWORD` psql prompts and the exec hangs.

Three corrections to `polaris/HANDOFF-upgrade-1.6.0-2026-09-17.md`, all established by
reading upstream at tag `apache-polaris-1.6.0` (not from the cluster):

1. **1.6.0 requires schema v4, not v5.** `DatabaseType.java` declares latest schema version 4
   for Postgres/CockroachDB/H2. The v5 step that alters `events.catalog_id` is a **1.7.0**
   concern; on 1.6.0 that column stays `TEXT NOT NULL`. The handoff's headline risk does not
   apply to this upgrade.
2. **The v3 → v4 delta is additive only** — 3 indexes on existing tables, plus
   `idempotency_records`, `scan_metrics_report`, `commit_metrics_report` and their indexes.
   No `ALTER`, no column change, no data rewrite; `entities`, `grant_records`,
   `principal_authentication_data`, `policy_mapping_record` and `events` are byte-identical
   between our `schema_v3.sql` and upstream `schema-v4.sql`. Script:
   `postgresql/schema/migrate_v3_to_v4.sql` — **transcribed from upstream, not the shipped
   file; diff it against the v4 resource in the 1.6.0 image before running it.**
3. **The handoff claimed the working tree already carried `maxReplicas 3 → 1` uncommitted. It
   did not.** The only uncommitted change on 2026-09-18 was the console threshold. So `#8`
   (HPA can scale Polaris to 3 pods sharing one log PVC) is **still open and still armed**:
   `autoscaling.enabled: true`, `maxReplicas: 3`, unchanged. This also matters mid-upgrade —
   scaling the deployment to 0 for the migration may be undone by the HPA.

**New, and absent from the handoff: 1.6.0 tightened entity-name validation.** Upstream says
entities whose names contain control characters, dots, backslashes, colons and similar must be
**renamed before upgrading**. The catalogs and namespaces here were made by test ladders, so
this can block the upgrade. Screen query in the runbook, step 1 — and it is a screen written
from prose, not from 1.6.0's validation code; confirm the real character set before renaming.

**Consequence of the INFO decision, recorded so it is not rediscovered:** Quarkus applies the
stricter of category level and handler level, so while `console.threshold: INFO` no category
can emit DEBUG. `#15` and `#24` were both characterised with those DEBUG categories on.
Re-running either needs the `--set` override written out in the `categories:` comment in
`polaris/values.yaml`. The NPE stack trace itself is ERROR and survives INFO.

---

**#32 — Schema v6 + pipeline review P1/P2/P3/P4/P6/P7/P8/P11/P12: ROLLED 2026-09-16 (~16:01Z) and VERIFIED on traffic (tier 2/3).** 2026-09-16.
- **Verified from Kade's exports of window 16:02:30Z** (pod `benchmarks-fluent-bit-62klp`, report seq 4; `.scratch/readout-2026-09-16T160230Z/`):
  67 report rows, all `schema_version` 6, same row keys as the v5 window 15:01Z and **every count field equal** (access 355 / kept 200 /
  counted 155, 404 counted 100, app_dropped_404 110, errors 247 / 4, denied 104, commit_count per row). No row carries `app`, `level`,
  `_msg`; `message` only on the summary. Detail (386 docs, 16:02:07–16:02:42Z): field set exactly `@timestamp _time api_path client_ip
  exception hostName http_method http_status level loggerName mdc message response_size sequence user_principal_name` — no `_msg`,
  `app`, `stream`, `flb_tag`, thread/process fields; in-window 200 / 22 / 78; 0 stored 404, 0 parse errors, all 243 access docs with
  every parsed field and `message`, `http_status` integer. JSON doc size vs 15:01Z: access 705 → 649 B (−8 %), app 799 → 743 B (−7 %),
  report row 755 → 518 B (−31 %).
- **Not read:** P4 gate count, step2/step3/step9/step12 output, helm revision, any `k8s-logs` doc after the roll (P2/P3/P4 effects).
Original record:
Decisions (Kade, 2026-09-16): apply P1 P2 P3 P4 P6/7 P8 P11/12; keep the raw access line but **rename `_msg` → `message`**; drop `app`.
M2 measured by Kade: ~1,800 Fluent Bit self-log docs per traffic notebook run. M3: tier-1 docs with a `log` field exist. M4: shipper
exists, Kade uninstalls manually. M5/tier 1 sizing out of scope.
- **Lua** (`fluent-bit/polaris_access_log.lua`, schema **6**): reads `message`; report rows lose `app`/`level`; sentence only on summary,
  as `message`. Policy unchanged.
- **values**: tier 2 = parser → modify(Rename timestamp _time only) → **record_modifier trim (+`stream`) BEFORE the Lua** → Lua; no
  `Add app`, no `Rename message _msg`, no `Include_Tag_Key` on the tier-2 output. Tier 1: **OUTPUT 1 (`Id_Key sequence`) deleted**,
  **`Exclude_Path /var/log/containers/benchmarks-fluent-bit-*.log`**, parser filters and definitions `polaris_json` / `polaris_text` /
  `datahub_json` deleted.
- **templates** (v6 mappings): undeclared strings `text` `index:false` + `.keyword`; `message`, `exception.message` text; `client_ip` ip;
  report `message` text. step9/step12 now also compare `dynamic_templates`.
- step2: new block (trim-before-Lua order, no rename/app, one `Include_Tag_Key`, no `Id_Key`, `Exclude_Path`, no tier-1 parsers,
  3 outputs, schema constant 6). step3: absence of `threadName threadId ndc processName stream flb_tag app _msg` in `polaris-logs-*`,
  of `app level _msg` in `polaris-report-*`, no row with `message`, no `k8s-logs` doc from the Fluent Bit pod — all since pod start.
- P11: 8 scripts `git mv` to `logging/scripts/attic/`. P12: `logging/NOTE-monitoring-team-handover-2026-09-16.md`.
- **Verified off-cluster (Cowork):** LuaJIT tests v3/v4/v5/v6 + first-tick ALL PASS (the loop from `apply-lua.sh`); step11 PASS 67×34 with
  detail 200/22/78 on `084100Z` and `144400Z`; `diff-v5-v6.lua` 0 diffs on real + 200k fuzz after normalising only the intended changes
  (and 24 diffs when `schema_version` is not normalised — the harness sees reports); step2 on a stand-in render built from the values
  blocks: all PASS; step9/step12 comparers PASS against the template files; YAML/JSON valid.
- **NOT verified:** no helm render; OpenSearch acceptance of the v6 mappings (step9/step12 on the cluster); anything on traffic.
- **Gate before the roll, for P4's Polaris text parser only** (the two JSON parsers repeat Merge_Log's JSON decode and cannot succeed
  where it failed): if `k8s-logs` holds Polaris docs with the regex's capture field `logger`, that parser did work — then restore its
  filter + definition before rolling:
  `curl -sk -u "$OS_USER:$OS_PASSWORD" "$OS_URL/k8s-logs-*/_count" -H 'Content-Type: application/json' -d '{"query":{"bool":{"filter":[{"exists":{"field":"logger"}},{"wildcard":{"kubernetes.pod_name.keyword":"benchmarks-polaris-*"}}]}}}'` → expect `"count":0`.
- **Roll (one restart):** gate → `bash fluent-bit/apply-lua.sh --no-restart` → step2 on a fresh render → `helm upgrade` → step3 →
  traffic notebook → step3 again (field checks need docs) → `step12` + `step9` (v6 mappings; shape tomorrow's indices) →
  `step10 <window_start>` → `step11`. Expect the report counts of `144400Z`/`15:01Z` (355/200/155, 404 100/110) and detail 200/22/78.
  Dashboards/queries reading `_msg`, `app`, `level` or bare string fields need the new names.

**#31 — Lua refactor (R1–R6) and the pre-first-tick counting gap: ROLLED 2026-09-16 (~15:00Z) and VERIFIED on traffic.** 2026-09-16.
- **Rolled (Kade):** `apply-lua.sh --no-restart` → step2 → `helm upgrade` → step3 (their outputs were not pasted; helm revision not
  recorded, expected 20). New pod `benchmarks-fluent-bit-qr4br`.
- **Verified from Kade's exports of window 15:01:00Z (report seq 4 on qr4br):** summary 355 / 200 / 155, `counted_404` 100,
  `app_dropped_404` 110, errors 247 / 4, denied 104, 57 resources, 4 principals, 5 app_dropped rows, schema 5 — **every count equal to the
  14:44Z (old script) and 08:41Z windows; same 67 row keys.** The only field differences vs 14:44Z are run-to-run timing and name
  lengths (`commit_ms_*`, `response_bytes` / `last_read_bytes` of listings that embed the run id), not pipeline behaviour.
  `polaris-logs-*` (386 docs, 15:00:34–15:01:13Z): in-window detail 200 / 22 / 78 (access / PolarisServiceImpl / IcebergExceptionMapper)
  = the replay prediction; all 243 access docs carry every parsed field (so the merged parser is what runs — old Lua + new config would
  have stored parse errors, new Lua + old config would have stopped the pipeline); `access_log_parse_error` 0, 404 docs 0,
  `held_orphan` 0; `http_status` is a JSON integer on all 243 (the moved `type_int_key` works, including access lines released in arrays
  with held app logs); no `threadName` / `threadId` / `ndc`.
- **Not observed:** R4 itself (the first window after the restart was not exported); step11 on this window (no tier-1 export); pod CPU.
- **Promoted (Kade's go, 2026-09-16):** candidate → `fluent-bit/polaris_access_log.lua` (sha `2fbcfa47c513f5a0`), values FILTER 2 removed +
  `http_status response_size` in FILTER 3's int list, step2 expectations, `test-first-tick.lua` in `apply-lua.sh`. Re-checked on the
  promoted file (Cowork): apply-lua.sh's test loop ALL PASS (v3/v4/v5/first-tick); step11 PASS on `084100Z` and `144400Z` (with detail);
  differential vs the pre-refactor script 0 diffs; step2's Lua and filter-block counts on the files (script 1, call 0, int-list lines 1,
  trims present).
Review: `logging/REVIEW-lua-refactor-2026-09-16.md`. Candidate: `logging/candidates/polaris_access_log.refactor.lua`.
- **The live v5 script has a real counting gap (R4):** `counts` is nil until the first report tick, so after every pod start up
  to `Interval_Sec` (5 s) of successful GETs, catalog POSTs and 404s are dropped **and** in no counter
  (`test-r4-first-tick.lua`: current script reports `access_seen` 0 for 3 lines). Every Lua change is a restart. Fixed in the
  candidate by opening the window on the first record (decision: Kade; that window stays `partial_window: "true"`).
- **R1 (Kade: merge):** the parser moves into `polaris_noise_filter`; FILTER 2 goes away (`logging/candidates/r1-values-step2.patch`).
  **Promotion order is load-bearing:** new Lua + old config = FILTER 2 fails init and all inputs stop (tier 1 too); old Lua + new
  config = every access line becomes a stored parse error. Only `apply-lua.sh --no-restart` → `helm upgrade` (one restart) is safe.
- R2 classify guard + per-window cache, R3 allocations, R5/R6 dead conditions.
- **Verified off-cluster (Cowork, LuaJIT 2.1):** tests v3/v4/v5 ALL PASS on both scripts, now fed raw `_msg` lines
  (`test-raw-access-shim.lua`). Differential current vs candidate: 0 diffs on 2,136 real tier-1 records and 300k fuzz records.
  5 mutants are all caught. step11 on `084100Z` PASS for both. Lua CPU ~5.8 → ~2.1 µs/record.
- **NOT verified:** no helm render of the patch; the C-side marshalling saving of R1 (phase 3.1); cache hit rate at 1800 s.

**#30 — `threadName` / `threadId` / `ndc` removed from `polaris-logs-*`: ROLLED as REVISION 19 (2026-09-16 23:38:14 KST) and VERIFIED on traffic.** 2026-09-16.
- **Rolled (Kade):** `helm upgrade` from the committed values (`5315e0d`) → **rev 19**, 23:38:14 KST = 14:38:14Z (`helm history`:
  17 17:35:46 v5 with reloader, **18 18:07:08 = the hot-reload removal** (closes handoff task B), 19 = this). Pod `benchmarks-fluent-bit-4bxsn`.
  The Lua was NOT changed (apply-lua.sh: ConfigMap unchanged). step3: `RESULT: post-upgrade checks passed` (only the RESULT line recorded).
  **step12: PASS** — template stored and simulated 7/7 fields (no `threadId`); applies from tomorrow's index.
- **Traffic run 14:44:00Z window (readout `.scratch/readout-2026-09-16T144400Z/`, cut by Claude from Kade's Dev Tools export):**
  summary seq 13, schema 5, access 355 / kept 200 / counted 155, `counted_404` 100, `app_dropped_404` 110, errors 247/4, denied 104 —
  **identical to the 08:41Z window.** step11 on the 720 tier-1 records in the window: **PASS 67×34 for the live script AND the
  refactor candidate (`#31`).** No detail export, so the by-logger detail check did not run.
- **VERIFIED from `polaris-logs-*` (Kade's second export, 386 docs, 14:43:35–14:44:13Z, all `polaris-logs-2026.09.16`):**
  `threadName` 0, `threadId` 0, `ndc` 0 — and the earlier trims still hold (`processName`, `loggerClassName`, `processId`, `logtag`,
  `time` all 0). Remaining fields: `@timestamp _msg _time api_path app client_ip exception flb_tag hostName http_method http_status level
  loggerName mdc response_size sequence stream user_principal_name`. No 404 access doc stored. (The first export, `k8s-logs`, is tier 1
  where the fields stay by design: 870/870 carry them.)
- **step11 with detail, 14:44:00Z window:** detail 200 / 22 / 78 (access / PolarisServiceImpl / IcebergExceptionMapper) stored ==
  replay-emitted, for the live script **and** the `#31` candidate; 67×34 rows PASS for both.
Decision (Kade): thread name and id carry no tracing value; `ndc` was `""` on all 300 detail docs of readout
`084100Z`. Scope **tier 2 only** — tier 1 `k8s-logs` and the VictoriaLogs shipper keep them.
- `fluent-bit/values.yaml` FILTER 4 `polaris_field_trim`: three `Remove_key` lines (C filter, after the Lua, so
  held/orphan records are trimmed too; removing in Lua would force return code 2 on every stored record).
- `polaris-logs-template.json`: `threadId: long` dropped (re-PUT with step12; not retroactive).
- step2: three render checks. step3 section 5: `exists` count of each field on docs newer than the container
  start must be 0 (older docs in the same daily index still carry them).
- Originally written with no render; the roll above supersedes that. The R1 filter merge (`#31`) is a separate, later upgrade.

**#16 — RESOLVED-INSTRUCTIVE 2026-09-09: the double write DOES NOT HAPPEN. The reasoning was
sound and the conclusion was wrong.**

Measured: 13,796 documents carrying `sequence` over 13,797 distinct values in 30 minutes, ratio
**1.000**, and the *busiest* `sequence` buckets each hold exactly one document — a duplicate would
sort above them. `logging/scripts/step7-dedup-check.sh`.

**Why the config reasoning failed.** It was right that Fluent Bit routes a record to every matching
output, and right that both outputs match Polaris. What it could not see is that **OUTPUT 1 never
indexes anything**: Polaris emits `sequence` as a JSON integer, the OpenSearch plugin requires the
`Id_Key` value to be a *string*, and it drops the record instead (#18). So the second copy is
discarded before it reaches the index, and everything downstream of the "twice" claim goes with it:

- **counts over `k8s-logs` are NOT ~2x inflated**, and the dedup instruction this issue placed on
  `PLAN-opensearch-cutover` §7 is **void** — deduping there would have halved a count that was
  never doubled. The plan is corrected.
- the `doc_as_upsert` field-union hazard cannot occur, because no upsert is ever sent;
- `sequence`'s per-JVM reset does not matter for dedup, because nothing dedups.

**What remains true and is now `#18`'s problem:** tier 1 has no dedup at all, and never had. A
retried chunk produces duplicates via OUTPUT 2's `Generate_ID On`. The gain `Id_Key sequence` was
sold on has never once been delivered.

*Original entry follows, kept because the failure mode is the instructive part — a claim derived
correctly from configuration, never checked against the data, and cited as fact in a plan for a
month.*

**#16 (original) — The DaemonSet writes every Polaris console line to `k8s-logs` TWICE, and its
dedup key cannot dedup. OPEN (accepted for now).**

**Update 2026-09-08:** this issue got more load-bearing, not less. The cutover plan now sources
**tier 2 from stdout as well**, so `k8s-logs` is the denominator for proving tier 2 is a subset of
tier 1 — and an undeduplicated denominator is ~2x wrong. Every comparison against tier 1
deduplicates on `sequence` first.

`fluent-bit/values.yaml:155` OUTPUT 1 matches `kube.*benchmarks-polaris*`; `:179` OUTPUT 2
matches `kube.*`. **Fluent Bit routes a record to every matching output** and both target
`k8s-logs` — one copy keyed `Id_Key sequence` + `Write_Operation upsert`, one with
`Generate_ID On`. So every Polaris stdout line exists twice.

**Consequence for measurement, which is why this is filed rather than just fixed:** any count
over `k8s-logs` is **~2x inflated**, so it must be deduplicated on `sequence` before it is
compared with anything — including the tier-1 vs tier-2 comparison in
[`PLAN-opensearch-cutover`](../logging/PLAN-opensearch-cutover-2026-09-08.md) §7.

**And `sequence` cannot carry that load either.** It is the JBoss per-`ExtLogRecord` counter,
**per JVM from JVM start** (2026-09-03 audit: 3723/3724 = ~3.7k records since JVM start). It
resets on every Polaris restart, and #8's three HPA replicas would each run their own. Worse,
`upsert` sends `doc_as_upsert`, so a collision does not overwrite — it produces a **field-union
of two unrelated log lines**, an access record's `http_status` stapled onto an application
record's `exception.*`. Plausible, fictional, no error.

**Kade's call 2026-09-08: leave tier 1's config alone.** Defensible at 5-day retention and
unfiltered. **It must not become the precedent** — the plan gives tiers 2 and 3 a composed
`_doc_id` instead. Testable prediction if it ever matters: `k8s-logs`' Polaris count for a day
spanning a Polaris restart should be near `max(sequence)`, not the true line count. Nobody has
run it.

**#15 — Polaris 500s on create-then-resolve, and it is a NullPointerException, not a
"PG-HA read-after-write signature". OPEN.**

Every 500 this cluster has stored is a `java.lang.NullPointerException` logged by
`org.apache.polaris.service.exception.IcebergExceptionMapper`. Eight of them in run
`1788760757`, `05:59:20Z .. 05:59:33Z`, in three signatures:

| exception.message | n | on |
|---|---|---|
| `…getPassthroughResolvedPath(Object)" is null` | 6 | `POST …/{catalog}/namespaces` |
| `grantee_not_found: grantee={}, [… name='catalog_admin' …]` | 1 | `POST /api/management/v1/catalogs` |
| `metadata` | 1 | `POST …/namespaces/probe_ns/views` |

*2026-09-18 — HYPOTHESIS C IS DEAD for the current cluster.* The handoff gave hypothesis C
(the namespace request lands on a *different* Polaris pod than the catalog create, whose
entity cache never saw it) more weight than A or B, on the grounds that round-robin across
replicas is deterministic in a way replication lag is not, which fits 3-of-3. Runbook step 0b
settles it: **there is exactly one Polaris pod**, `REPLICAS 1` with the HPA idle at 1% CPU,
and the deployment reports `1/1`. With one pod there is no second cache to diverge from. C
cannot be the mechanism here.

Two caveats before this is treated as closed. `#15`'s evidence came from a differently-seeded
cluster (run `1788760757`), so what is settled is that C is not the mechanism *now*, not that
it never was. And the HPA is live again (`#8`, 2026-09-18) — if a future ladder run pushes
Polaris past the target, C comes back. **Pin `replicaCount` / disable autoscaling before the
post-upgrade ladder run if you want C held dead for the duration.**

That leaves **A** (stale reads through Pgpool — the `database_redirect_preference_list`
remedy in the handoff addresses it) and **B** (a 1.3.0 resolver/entity-cache bug, which the
1.6.0 upgrade is itself the experiment for).
**The trigger is a fresh parent entity, not load.** Three of the six namespace NPEs are the
`polaris-learning` 500-ladder's *setup* step — one per rung, `nb1788760757bh`, `…dns`,
`…nobkt`, **3 of 3 brand-new catalogs**, each 500ing on the first namespace created in it.
The catalog-create NPE is the same shape one level up: the `catalog_admin` role is created
and immediately looked up as a grantee, and the lookup returns nothing.

**Read-after-write against a standby remains the plausible mechanism** — an entity written
on the primary and resolved microseconds later — but that label had been treated as settled
and it never was. What the log carries is an unresolved entity and an NPE. Do not write
"PG-HA read-after-write" into a document again without the replication evidence beside it.

**The denominator cannot be read from this pipeline, by construction.** Scoped to the window,
`POST …/namespaces` stored **6 x 500** — 3 on the fixture catalog, 1 each on `nb1788760757bh`,
`…dns`, `…nobkt` — **and 1 x 409, and nothing else**. No 2xx, at any scope: that path is not
under `/api/management/`, so rule 5 does not keep it and a **successful namespace create leaves
no individual record**. Rule 3 keeps the failures. So `stats by (http_status)` over stored
access records for this path can only ever return errors, and its zero is the policy working,
not a measurement. The per-resource `writes` counter cannot supply it either: two of the three
fixture 500s were charged to `__other__` because the key did not exist yet, so the key's own
`writes` is 2 for 4 error POSTs.

**It exists in the driver.** The notebook knows every call it made and its status; the ladder
simply throws its setup statuses away. That single omission is why the three 500s were
invisible AND why the rate is unmeasurable — one fix closes both.

**What is established:** 3 of 3 brand-new catalogs 500 on the first namespace created in them,
and the namespace is usable afterwards — each rung went on to `create_table` and got a 4xx from
the storage layer, which requires the namespace to exist. Consistent with a write that
committed and a resolution that then dereferenced null.

**Two consequences, both real.** For the platform: writes 500 at roughly 3% (8 of 275
requests in 60s) on a single-node cluster, and nothing was watching. For
`polaris-learning`: this is the **repeatable provoker** `HANDOFF-500-coverage` §4.1 says does
not exist — API-only, no `kubectl`, no `pg_wal_replay_pause()`. Detail in
[`sessions/2026-09-07-500-coverage-review.md`](sessions/2026-09-07-500-coverage-review.md).

**#14 — The noise filter governs 4.5% of the volume, and policy v2 is not running yet. OPEN.**

Two things, from the second coverage run (`polaris-learning/log-coverage`, 2026-09-04, run
`1788498536`, against `fb-values.yaml` sha256 `b56c135b87d6281b`).

**a. The measurement.** 122 calls stored 2,026 records. Counting the coverage matrix rather
than its summary: **90 access-log records and 1,928 application lines.** The filter can only
act on the first group — rules 1 and 2 keep every application line untouched — so dropping 34
of them removed **1.7%** of what would otherwise be stored. Rules 3–7 are an *audit-fidelity*
control. Anyone tuning them for storage is tuning the wrong 4.5%; the volume lever is the
DEBUG SQL records in #5b, and #5b already says **route them, do not turn them down**.
Settle where the 1,928 come from with one `stats by (loggerName)` before designing that.

**One number in that report does not agree with itself.** Question 5 says "34 of 122 calls
produce no record at all", but those same 34 calls carry **628 application lines**, and
`90 + 1,928 ≈ 2,026` implies the `app_lines` column is counted from VictoriaLogs. If it is,
a dropped `create_principal` still leaves 13 correlated records and only the access-log line
— method, path, status, principal — is lost. Real, but not "invisible". Settle which source
that column reads before repeating the stronger claim.

**b. Policy v3, written 2026-09-04, NOT RUNNING.** Deliberately, and it is #13's shape again,
so treat the upgrade as a change: `shipper-v3-upgrade-runbook.md`. **v2 was never deployed** —
it was superseded before installation, so there is no v2 baseline in the cluster and no reason
to look for one.

```
1. ERROR / WARN ........................ keep      (no deprecated exclusion — see below)
2. not an access-log record ............ keep
--- every access-log record is COUNTED here ---
3. status >= 400, or unparseable ....... keep, ALL of them, no cap
4. PUT / DELETE / PATCH ................ keep, all
5. POST under /api/management/ ......... keep, all
   POST anywhere else ..................  counted only
6. GET / HEAD, 2xx .....................  counted only
7. anything else ....................... keep
```

**What it preserves, and this is the point of the shape:** 100% of authorization failures —
every 401 and 403 is a full record via rule 3 — and 100% of identity and grant mutations.
What becomes a count is traffic that succeeded routinely.

**Rule 5 is split, not simplified, because in Polaris POST is the CREATE verb.**
`create_principal`, `create_principal_role`, `create_catalog_role` and
`reset_principal_credentials` are all POSTs; PUT covers only assignment and grants, DELETE only
removal. Summarising POST wholesale — the obvious simplification — would make a principal
invisibly created and visibly deleted, which is the asymmetry this pipeline exists to expose.
Catalog POSTs (`create_table`, `commit_table`, both renames, `report_metrics`, `oauth/tokens`)
are data-plane volume and are counted.

**Rule 1 has no "deprecated config" exclusion and needs none.** `polaris/values.yaml:315` sets
`io.quarkus.config: "OFF"`, so those warnings are never written; the coverage run independently
saw zero across 122 calls. The values file alone would not be evidence here (#5) — the run
agreeing with it is. The TODO is deleted, not deferred.

**The dedup cap question is gone, not answered.** v2 kept one read per principal per object per
KST day and needed a per-key table to do it, which is what `DEDUP_MAX_KEYS` was placeholding
for. v3 never stores a successful read individually, so there is no key to remember. The civil-
day arithmetic, both day buckets, `seen_before` and the cap are all deleted — about 90 lines.

**The flush report, schema v1.** A `dummy` INPUT tagged `polaris.report` ticks and reaches the
*same* Lua filter instance (state is per-instance, so `Match` is `polaris.*`); on a
`WINDOW_SECONDS` boundary the filter returns an **array** of records instead of the tick and
resets the counters. Steady state is a 30-minute window on the :00/:30 wall-clock boundary with
a 30s tick — **but the deployed values file is on the temporary fast-run setting right now, see
d. below before reading a report.** Array return is documented behaviour — "this value can be an array of tables... the
input record is effectively split into multiple records" — but has never run here (#14c).
Lands on `{app="polaris-shipper-report", level="REPORT"}`, its own stream.

Three record types on one envelope (`schema_version`, `report_type`, `report_seq`, `hostname`,
`window_start`/`window_end`/`window_seconds`, `_time` = window end):

| type | carries |
|---|---|
| `summary` | `access_seen` / `access_kept` / `access_counted` (**kept + counted == seen**), `counted_get`, `counted_post`, `errors_kept`, `parse_errors`, `distinct_resources`, `distinct_principals`, `resources_other`, `principals_other`, `min_record_time`, `max_record_time`, `partial_window` |
| `resource` | `resource`, `resource_kind`, `requests`, `reads`, `writes`, `errors`, `response_bytes` |
| `principal` | `user_principal_name`, `requests`, `reads`, `writes`, `errors`, `response_bytes` |

**Two margins, never the cross product** — `resource -> count` and `principal -> count`, so
state is |resources| + |principals| rather than their product. The consequence is in the source
because it will otherwise be misread as an audit trail: the report says *which resources are
hot* and *who is generating load*, and **cannot** say *who read which resource*. Under v3 that
question has no record behind it at all — a deliberate trade, taken knowingly.

Four things worth knowing about the schema:

- **`sum(resource.requests) == sum(principal.requests) == access_seen - parse_errors.** The two
  margins must agree. It is asserted in the test suite and it is Phase 4's last check — a
  dashboard that verifies it knows whether to trust a trend before drawing one.
- **The resource key is the resource, not the URL.** `/tables/t/metrics` counts under
  `/tables/t`. v2 emitted two rows for one table — measured, not supposed — and a trend
  computed on a key that splits is simply wrong.
- **Errors increment an existing resource key but never create one**, so a client walking
  invented table names cannot fill the key space. Their counts are not lost: they land in
  `__other__`, which keeps the margin totals exact, and every one is stored in full by rule 3.
- **Zero-carry, exactly one window.** A resource falling from 100k reads to none emits an
  explicit `0` rather than vanishing from the output, then decays. The fall is the direction
  you most want to see and a missing row cannot express it.

`user_principal_name` deliberately reuses the access-log field name, so one filter spans a
principal's stored 403s and their per-window counts. `resource` is a new name because it is a
normalized identity, not a request path.

**c. What is still unverified, and no test can reach it:** that this Fluent Bit build splits an
array return into separate records, and that the dummy input's tag reaches the filter instance.
Both documented, neither run. Runbook Phase 4 distinguishes them and names the fallback.

**d. TEMPORARY: the report window is 30 seconds, not 30 minutes.** Set 2026-09-04 at Kade's
request so a coverage run crosses three window boundaries in ~2 minutes instead of ~90 — the
handoff's §4 needs three, for `report_seq`, zero-carry and carry decay. In
`logging/fb-values.yaml`: `WINDOW_SECONDS = 30` (was 1800) and the dummy INPUT's
`Interval_Sec 5` (was 30).

**Revert both together.** The tick has to stay well under the window: `report_tick` reports
whatever `counts` holds under the index it was *opened* with, and records accumulate into the
open window regardless of their own timestamps, so if the tick period reaches the window period
ordinary jitter lets a boundary pass unnoticed — the skipped window never opens and its records
are folded into the previous window's index. At 1800/30 the margin is 60×; at 30/30 there is
none. That is why the tick moved too, and it is not cosmetic.

Two consequences while it is set:

- **Report volume is ~60× steady state.** Zero-carry emits every non-zero key once more as an
  explicit `0`, so even an idle pipeline ships a summary plus carried rows every 30s.
- **The first window after the `helm upgrade` is a replay, not traffic.** The tail DB is on an
  `emptyDir` with `Read_from_Head true` and VictoriaLogs does not deduplicate on ingest, so the
  upgrade replays the whole log file — and at 30s the entire replay lands in *one* window as a
  spike. A window whose `min_record_time`/`max_record_time` span far exceeds `window_seconds`
  is a replay. Do not trust it.

Nothing else reads the constant. `logging/scripts/test-polaris-filters.py` now parses
`WINDOW_SECONDS` off the deployed Lua and expresses every tick offset as a multiple of it
(it hardcoded 1800, so `T0 + 900` — "a tick inside the window" — would have become a tick 30
windows later and failed for the wrong reason). 48/48 at 30s. The runbook, roadmap #7 and
`POLARIS-LOG-COVERAGE-V3-HANDOFF.md` still describe the 30-minute steady state on purpose.

**Decided by this policy, and therefore no longer open:** the 4xx cap (there is none — all
errors kept), collection listings (counted, like every other successful read), `report_metrics`
(counted, as a catalog POST), and the dedup cap (deleted with the dedup).

**Still deferred, each with a number behind it:**

| | evidence | why deferred |
|---|---|---|
| the 95.5% — routing the DEBUG SQL records | 1,928 of 2,018 stored records are application lines | needs the `loggerName` distribution first; #5b already fixes the direction — route, never turn down |
| no `%D` — no request duration is recorded anywhere | the access-log pattern carries no latency token | Polaris-side, and **Polaris is not to be changed** (#11). The *no stack traces* half of this row is **CLOSED** — see immediately below |
| retention for the report stream | reads now live only as counts | VictoriaLogs single has one global retention and no disk cap (#7); the counts eventually want a TSDB, roadmap 7 |
| `neg.client_timeout` "EXPECTED DROPPED, PRESENT" | the run's only matrix discrepancy | oracle artefact — a call with no client-side status is not predictable and should not be scored `drop`. Harness fix, in `polaris-learning` |

**CLOSED 2026-09-07 — stack traces DO survive, and the `0 of 5` was a mis-named search.**
Run `1788760757`: **8 of 8** WARN/ERROR records carry an exception payload, stored flattened as
`exception.exceptionType`, `exception.frames`, `exception.message`, `exception.refId`.
VictoriaLogs flattens nested objects, so a query for `exception` matches nothing and a
`grep -c stackTrace` finds nothing — **two searches for a name this build does not emit,
agreeing with each other**, which is what the `0 of 5` was. Query `exception.*`, never
`exception`. The fact with its numbers is in [`roadmap.md`](roadmap.md), *Handing back*; the
review that re-proved it is
[`sessions/2026-09-07-500-coverage-review.md`](sessions/2026-09-07-500-coverage-review.md).
Only the `%D` half of that row is still open, and it is Polaris-side.

**READING THE REPORT STREAM — three false findings came from not doing this.** Every query
against `app:polaris-shipper-report` must carry **`schema_version:2`**, and anything about
sequence continuity must also carry **`hostname:"…"`**.

- **The stream holds v1 AND v2 records side by side.** The shipper pod was replaced at
  `2026-09-07T04:21:30Z` (`…68b4959db4-4f7tf` v1 -> `…55b7bf586d-5kt5l` v2). A `sum(errors_4xx)`
  over any range spanning that instant silently under-counts: the v1 records have no such field,
  and an absent field behaves like a zero inside a sum. Cell 0b gates the POLICY's schema
  version; nothing gates the QUERY's.
- **`report_seq` is per pod and resets to 1 on restart.** `min`/`max`/`count` across two
  generations manufactures a phantom gap — it read as "50 reports lost", then as "a backlog
  draining", and it was neither. The schema's own claim is *one summary per **(host, window)***;
  the host is not decoration.
- **`sum()` over an empty group returns `NaN` in LogsQL; `count()` returns 0.** A v1 summary has
  no `carried_rows`, so summing it yields NaN, which a naive comparison reads as a mismatch.
- **`_time` on a report record is the window END**, not its start. Seq 196 (`window_start
  05:59:00`) appears at `05:59:30`.
- **Every count must carry its denominator.** Ask `stats count()` for the scope first. Three
  times in one session a number arrived with no scope and read like an answer — 25 vs 6 on an
  unfiltered `_time`, a 5-row UI truncation read as a full result, and the cross-pod seq range.
  Each was caught only because an independent number disagreed.

**#1 — The repo has not been reconciled against the live cluster. OPEN.**
Kade reset and rebuilt the cluster on 2026-09-03 without following
`RESET-AND-CLEAN-INSTALL.md`, and resolved the four config blockers during the
install. Those fixes are in the running releases; whether they are also in the
`values.yaml` files here is **unknown**. Until someone diffs them, nothing on disk
is evidence of what is deployed:

```bash
helm -n datahub-hynix list
helm -n datahub-hynix get values <release> > /tmp/<release>-live.yaml   # then diff
```

The four blockers this closes out — Polaris `bootstrapCredentials` rendering `""`,
three conflicting MinIO credential sets (one of them plaintext at
`spark/values.yaml:30`), the stale `polaris-persistence-secret.yaml`, and the
unpinned images in `kafka/` / `schema-registry/` / `datahub/` — are **resolved in
the cluster**. Two of them are worth checking on disk regardless: a plaintext
secret key stays a leaked secret even after the cluster stops using it, and an
unpinned image is still unpinned for the next install.

**#2 — Which sink does Fluent Bit ship to? SETTLED — both halves, as of 2026-09-08.**
Not one shipper choosing a sink — **two releases**. Confirmed from `helm list` on
2026-09-03: **`fb-polaris-shipper`**, namespace **`datahub-hynix`**, chart
`fluent-bit-0.58.1` / app **5.1.1**, **revision 10**, deployed 2026-08-22 — the Deployment
that tails the Polaris log PVC into VictoriaLogs (`logging/fb-values.yaml`). The DaemonSet
release (`fluent-bit/values.yaml`) ships container logs to OpenSearch in Docker. **Its name is
`benchmarks-fluent-bit`, in `datahub-hynix`** — quoted 2026-09-08 from `kubectl get ds -A`, the
half of this issue that had been open since 2026-09-03. **`hostNetwork` is unset**, so it is an
ordinary pod on the cluster network: reaching `192.168.194.1:9200` is not a host-network
privilege, and any pod in the namespace has the same egress. `CLAUDE.md`'s tech stack now says so.

Two things that follow. The shipper is in `datahub-hynix`, which is the only namespace it
could be in — #6 was a real constraint and is already satisfied. And **revision 10** on a
file that has never matched the cluster is the shape of #5: ten upgrades of configuration
this repo cannot account for.

**#3 — `minio/values.yaml` defeats its own chart's credential guard. OPEN (low).**
`minio/templates/secret.yaml` refuses to render when `auth.rootPassword` is empty —
CLAUDE.md's Zero Hardcoded Credentials rule, enforced at install time, which is the
right place for it. But the committed values carry `rootUser: "minio"` /
`rootPassword: "minio"` as defaults, so the guard never fires and an install with no
`--set-string` quietly comes up with a publicly known password. Either blank the
defaults so the guard does its job, or accept that this cluster's object store has a
guessable root credential. Cheap either way; just pick one deliberately.

**#4 — `fluent-bit/values.yaml` carries a plaintext OpenSearch password. OPEN.**
`HTTP_Passwd Str0ngP@ssw0rd123!` appears twice, in a **committed** file — the Zero
Hardcoded Credentials rule broken in tracked history. Rewriting the file does not unleak
it; the credential has to be rotated on the OpenSearch side as well. The fix in the values
is a Secret plus `${VAR}` expansion in the Fluent Bit config, not a different literal.
`polaris/values.yaml:408-409` (`minioadmin`/`minioadmin`) is the same class of problem and
should go the same way.

**#5 — RESOLVED 2026-09-18, AND THE CLAIM IS REFUTED. `polaris/values.yaml` DOES describe the
running Polaris.**

`helm get values benchmarks-polaris` was finally run — the command this issue waited on since
2026-09-03. Flattened and diffed key by key against the working tree:

| comparison | result |
|---|---|
| repo working tree vs live R5 user-supplied | **identical on all 210 keys** except the 14 `afc88e2` changed |
| live user-supplied vs live computed (`--all`) | **209 of 210 identical**; the only difference is `revisionHistoryLimit: null` present in supplied and absent from computed, which is Helm coalescing a null |

Two conclusions, and the second is the structural one:

1. **The file matched the release.** The 14 differing keys are exactly `image.tag` plus the 13
   log categories from `afc88e2` — i.e. the changes made *after* the capture. Nothing else
   diverged. `logging.console.threshold` does **not** appear in the diff: the working tree said
   INFO and so did the release.
2. **There is no chart-default layer hiding anything.** `--all` adding nothing over the supplied
   values means the release was installed with the whole file, so no setting is being served
   quietly from a chart default. This is the structural fear behind `#F1` and the `postgresql:`
   nesting, and for Polaris it is now measured as absent.

**What the DEBUG-console confusion actually was.** The *committed* file said
`threshold: DEBUG` while the release ran INFO — but the *working tree* said INFO, uncommitted.
So the drift was one uncommitted edit Kade had already applied at revision 5 (2026-09-15) and
not committed, not a file describing something else. An earlier session note in `#33` called
this "`#5` caught in the act"; **that was wrong and is retracted** — it inferred file/cluster
divergence from a ConfigMap reading before the values comparison existed to check it against.

*Historical, kept because the reasoning is instructive:* filed first as "the VictoriaLogs path
has no input" (wrong — it runs), then rewritten as "the repo and the cluster disagree", which
over-reached: it said *the repo*, on evidence about *one file*. Every file it named has now
reconciled. The lesson is not "the repo is fine"; it is that **"the file is probably wrong" is
itself a claim needing evidence**, and three times running it has failed to find any.

Filed first as "the VictoriaLogs path has no input" (wrong — it runs), then rewritten as
"the repo and the cluster disagree", which over-reached: it said *the repo*, on evidence
about *one file*. The `helm get values fb-polaris-shipper` diff on 2026-09-03 settles that
half and it went the other way.

**`fluent-bit/values.yaml` is RECONCILED too, 2026-09-09.** `helm get values
benchmarks-fluent-bit` diffed key by key against the file: **zero differing keys, none present on
one side only**, and the DaemonSet's running container is
`cr.fluentbit.io/fluent/fluent-bit:3.2.2` — exactly what the file pins. So the OpenSearch outputs,
the parsers and the `kube.*` filter chain in that file are all genuinely in effect, which is what
licenses editing it. (Note `helm get metadata` reports `APP_VERSION 5.0.6`; that is the *chart's*
appVersion, not the image.) **Both Fluent Bit values files now match their releases**, and
CLAUDE.md's "neither values file matches its live release" has been corrected.

**`logging/fb-values.yaml` is RECONCILED.** Live revision 10 matched it line for line apart
from `helm`'s alphabetical key ordering and **one** real difference: the live output streams
on `_stream_fields=app,level` where the file asked for `app,level,loggerName`. The file now
says `app,level`. Nothing else about the shipper was ever divergent — the tail with no `DB`,
`Read_from_Head true` and `Skip_Long_Lines Off` are all genuinely deployed, so #5b's
open questions about them are answered: they are live, and they are still worth changing.

What remains open is narrower and still real:

- **`polaris/values.yaml`** says `logging.file.enabled: false`, sets
  `quarkus.http.access-log.enabled` nowhere, and carries `logging.mdc: {}` — yet the file is
  written, access-log lines arrive, and `mdc.requestId` / `mdc.realmId` are on every record.
  That configuration is somewhere else. `helm -n datahub-hynix get values benchmarks-polaris`
  has not been run. **Do it before editing that file.**
- **`polaris-shared-logs-pvc`** is mounted by both releases and created by no manifest here.
  It exists in the cluster; the repo cannot rebuild it.

The generalisable part: a claim about "the repo" needed evidence about the repo. One file
diffing clean is exactly the outcome that a broad claim could not have predicted.

**#8 — HPA can scale Polaris to 3 pods sharing one log file. OPEN.**
`autoscaling.enabled: true`, `maxReplicas: 3` at 80% CPU — and every replica mounts
`polaris-shared-logs-pvc` and appends to the same `/deployments/logs/polaris.log`.
`ReadWriteOnce` does **not** prevent this: RWO allows many pods on the *same node*, and this
is a single-node cluster with `ScheduleAnyway` spreading. Two JBoss file handlers with
independent descriptors and independent rotation state on one file means interleaved records,
and a rotation by one pod pulling the file out from under the other and from under the
shipper's inode. Unbitten only because nothing has pushed Polaris past 80% CPU. Fix: pin
`replicaCount` and disable autoscaling while the shared-file design stands, or give each pod
its own filename and let the shipper glob.

*2026-09-09:* the HPA currently reports `cpu: <unknown>/80%, memory: <unknown>/80%` at
`REPLICAS 1`, age 21d — **no metrics, so it cannot scale at all**. That removes the hazard
from the notebook run in progress, and it is not a fix: the autoscaler has been inert for an
unknown span, and the interleaved-write hazard returns the moment metrics come back. Still OPEN.

*2026-09-18 — THE METRICS ARE BACK, so the hazard is armed again.* Measured:
`cpu: 1%/80%, memory: 30%/80%`, `MINPODS 1  MAXPODS 3  REPLICAS 1`, age 30d, one pod
(`benchmarks-polaris-777c948595-c2zzg`). The 2026-09-09 reading is superseded: the autoscaler
can scale now, it simply has no reason to — 1% CPU against an 80% target is enormous
headroom, and memory at 30% is the closer of the two. So `#8` is **armed but not firing**,
and it is not "removed by lack of metrics" any more. Unchanged in the 1.6.0 commit
(`afc88e2`) by choice: `autoscaling.enabled: true`, `maxReplicas: 3`. **This also bites
mid-upgrade** — runbook step 2d scales the deployment to 0 for the migration and the HPA
`minReplicas: 1` may scale it straight back up. Check after scaling, do not assume.

**#9 — A plaintext database password in the live release. OPEN.**
`persistence.relationalJdbc.secret.password: polaris` in `helm get values` output. Same class
as #3 and #4. Separately, `minio.accessKeyId`/`secretAccessKey: minioadmin` sit beside
`minio.existingSecret: benchmarks-minio-credentials` — two credential sources for one client,
which is how #1's "three conflicting MinIO credential sets" began.

**#10 — RESOLVED-INSTRUCTIVE: there was never a hidden config source.**
The ConfigMap and pod env, read directly, say `quarkus.log.file.enabled=false` — matching the
live release values *and* `polaris/values.yaml` on disk. Everything agrees. The divergence
story that ran through five readings of this pipeline was wrong at every level; **the repo
does describe this cluster.**

**And the belief it rested on is backwards.** Kade's read was that the chart's
`logging.console` / `logging.file` blocks "are not applied at all, just extraEnv applied".
His own ConfigMap disproves it: `quarkus.log.file.enabled=false` is rendered by
`templates/configmap.yaml:132-147` *from* `logging.file.enabled: false`. The block is not
inert — **it is the switch holding the pipeline off.** It reads as inert precisely because
the only value it has ever written is the one with no visible effect. `QUARKUS_LOG_FILE_JSON_*`
is real but orthogonal: JSON formatting for a handler that is disabled.

**#11 — Unexplained, NOT pursued: file logging reads as off, and ships anyway.**
The running config says `quarkus.log.file.enabled=false`, and Polaris is nonetheless writing
a file that the shipper tails — **Kade confirms the pipeline works and ships continuously**,
which is an observation, where the prediction that it would break at the next restart was an
inference. This session's inferences about this pipeline were wrong four times; his
observation wins. **Polaris config is not to be changed.**

Left here because it is genuinely unexplained, not because it needs action. Whoever picks it
up: `ls -l --full-time /deployments/logs/` twice, thirty seconds apart, says whether the file
is live or stale, and the Polaris pod's start time against the ConfigMap's last write says
whether the JVM predates it. Do not turn it into a change on the strength of the reasoning
alone.

**#12 — WITHDRAWN.** Proposed flipping `logging.file.enabled: true` and deleting the
`extraVolumes` pair. Kade's call: Polaris works, leave it. The reasoning behind it is in the
session file if the situation ever changes; the mount-path collision it warns about
(`logging.file.enabled: true` makes the chart mount `logs-storage` at `logsDir`, colliding
with the existing `extraVolumeMounts` on the same path) stays true and would bite anyone who
enables that flag without removing the pair.

**#5b — What is actually wrong in the shipped records. OPEN.**
Established from two raw records off the VMUI JSON tab, after two earlier readings of the
same pipeline from a *rendered* view were both wrong. `_time` is **not** an ingest stamp —
it is the record's own Quarkus time (`...13.911654221Z`), 178µs *earlier* than Fluent Bit's
own `date` (`...13.911832Z`), which an ingest stamp cannot be; the nanoseconds are the JBoss
JSON formatter printing the full `Instant`. And every record **does** carry `loggerName` —
the stream-fields panel was showing the *stream* (`{app, level}`), not the field list.
**A `_stream` is not a field list and a histogram bucket is not a clock. Read the record.**

Working, and not to be "fixed": Quarkus JSON file logging, `_time`, `_msg`, `_stream` on
`{app, level}` (low-cardinality, the right choice), and **`mdc.requestId` + `mdc.realmId`,
which make the spec's §7 end-to-end trace query work today**. Note `polaris/values.yaml` has
`logging.mdc: {}` and `_stream_fields=app,level,loggerName` — the cluster is right and the
repo is wrong on both, which is #5 again.

Actually wrong:

| what | evidence | fix |
|---|---|---|
| `date` duplicates `_time` on every record | `"date": "1788417313.911832"` beside `_time` | `json_date_key false` on the HTTP output |
| `processName` is a 60-byte JVM path on every record; `loggerClassName`, `processId` near-valueless | in every record | `record_modifier` `Remove_key` |
| **DEBUG SQL records are ~1.5KB each** — full statement, every bound parameter, an embedded JSON blob escaped four deep — and are nearly every row | the sample `_msg` | **Do NOT just set `DatasourceOperations` to INFO.** `polaris-learning` depends on that logger being at DEBUG (`roadmap.md`, *Handing back*: `check_sql_logging.py` must print *SQL DEBUG logging is WORKING*). Turning it down to save space breaks the only consumer this platform exists for. Route it instead — its own stream, or leave it to the console→OpenSearch path and keep VictoriaLogs for the rest. |
| bound parameter values are written to the log | S3 paths and internal properties in the sample | same fix; worth knowing before this pattern reaches anything with real data in it |
| `response_size` is `-` for zero-byte responses | `"... 200 -"` | regex `[\d-]+`, not `\d+` |
| no latency token in the access-log pattern | the access-log `_msg` | add `%D`; the spec's own P99 panels need it |

The tail `DB`, `Skip_Long_Lines Off` and the absent buffering are now **confirmed live** by
the revision-10 diff, not merely suspected. Unchanged as faults: a restart replays the file
from byte 0, and a line over `Buffer_Max_Size` stops the tail rather than being skipped.

**#6 — A shared PVC cannot cross namespaces. OPEN (design constraint, decide before building).**
PVCs are namespaced. Polaris runs in `datahub-hynix`, so the file-tailing shipper must run
in `datahub-hynix` too — only VictoriaLogs stays in `logging`, which is what
`environments.md` already says that namespace is for. `ReadWriteOnce` is survivable only
because OrbStack is one node; it stops being survivable the moment anything is scheduled
elsewhere. The alternative that avoids the PVC entirely is to add a second OUTPUT to the
existing DaemonSet and drop the Deployment — at the cost of the access-log field extraction
and the dedup filter, which need the file path to be worth building.

**#7 — `logging/victoria-values.yaml` is sized for the spec's peak, not for this laptop. OPEN (low).**
50Gi PV and a 4Gi memory limit come from the 140M-records/day column of the design doc, on
the single OrbStack node that already needs >7GB for the full platform set. Two specific
gaps rather than just the sizing: there is **no `retention.maxDiskSpaceUsageBytes`**, so
30-day retention alone does not stop the PV filling and wedging the pod; and
`service.type: LoadBalancer` on 9428 publishes an **unauthenticated ingest *and* query**
endpoint onto the Mac, since VictoriaLogs single has no auth. **`persistence.size` is
now-or-never** — if the PVC is already bound at 50Gi, that is what this cluster has.


**#26 — Report rows are stamped by a tick that fires 3.673s late, and the matrix fires every phase
on the boundary. OPEN, LIVE, and it is the reason three gates in run `1789370776` did not mean what
they said.** 2026-09-14. Measured from the OpenSearch report + log exports, not from config:

- **The skew is constant, not erratic.** All 11 rows (`seq` 184..194) emitted at
  `window_end + 3.673s`, σ < 2ms. It cannot drift: `Interval_Sec 5` **divides** `WINDOW_SECONDS 30`,
  so the tick phase against the window grid is fixed for the life of the process. Row `[W, W+30)`
  really covers about `[W+3.7, W+33.7)`. Bounded independently to **+1.55s..+3.67s** for `seq=186`
  by its own emit timestamp — a 30s shift is arithmetically excluded.
- **The notebook lands every burst inside that dead zone.** Traffic starts 0.52–0.61s after each
  boundary and finishes within ~1s, so 100% of a phase is attributed to the previous row.
- **`{-30: 5, 0: 1}` is one rule, not two.** `lead_s` measures distance to the *label*, so it reads
  −30 for a boundary-aligned burst and ≈0 for a mid-window one. The single `0` row is `seq=185`,
  the setup burst at 07:26:16.9 — the only traffic in the run that did not start on a boundary.
  **The report's "no single offset can correct it, do not quote window-scoped gates" is withdrawn.**
- **Confirmed against the other pipeline:** `access_kept` equals the access docs in the real window
  in **7 of 7** windows, 343 == 343 total.
- **Consequences already visible:** Gate 4 `writes=1 granted=3` is two adjacent rows (3 grants at
  07:29:00.55–.61; the teardown DELETE at 07:29:31.35). Gate 4 `auth_denied=0` is **not** the
  ROLE_KINDS exemption and the 403 did **not** fall to `__errors__` — it is on the role row in the
  neighbouring report row (`auth_denied=1`). Gate 2's VOID is the same class.
- **Cheapest fix is in the notebook, not the pipeline:** start each phase ~5s past the boundary
  (> `Interval_Sec`). Re-typing the window from record times is a *design change* — the Lua refuses
  it deliberately, so a replayed record is not re-dated — and must be argued as one.

Full derivation, including the wrong turn that nearly filed this as a constant 30s shift, in
[`sessions/2026-09-14-window-skew-review.md`](sessions/2026-09-14-window-skew-review.md).

**2026-09-15 — FIX CONFIRMED by run `1789460891`; two corrections.** Bursts started +11.5s and
+6.6s past the boundary; errors per row 2 / 251 == detail docs, by label, no shift. (a) **The tick
does drift**: same pod, `seq` unbroken 440→854, offset 3.673s → 2.77s — divisibility fixes the grid,
not the timer. The `Interval_Sec + 1.5` lag is immune; a hardcoded 3.673 is not. (b) The run put
**every phase in one window**, so per-phase window gates (Gate 4's grant count on a busy role) read
the whole matrix. Downgrade to MONITOR once phases are one-per-window again.
[`sessions/2026-09-15-rerun-1789460891-review.md`](sessions/2026-09-15-rerun-1789460891-review.md).

**#27 — Policy v4 / report schema v4. CLOSED: rolled 2026-09-15, superseded by v5 (`#28`, rev 17) and the refactor (`#31`).** 2026-09-15.
*(Header corrected 2026-09-16; the body below is the original record, "WRITTEN AND NOT ROLLED" as of 2026-09-15.)*
`fluent-bit/polaris_access_log.lua` carries it (split out of `values.yaml`'s `luaScripts` the same day;
**every `helm upgrade` needs `--set-file 'luaScripts.polaris_access_log\.lua=fluent-bit/polaris_access_log.lua'`**,
or the Lua filters lose their script and the pod CrashLoops). The running pod is v3.
**2026-09-15 09:14 UTC — that happened.** The first v4 roll ran without `--set-file`:
`helm get values` showed `luaScripts: {}`, the pod logged `cannot access script
'/fluent-bit/scripts/polaris_access_log.lua'` → `filter initialization failed`, and every input
paused — **tier 1 (`k8s-logs`) stopped with it**, not only Polaris. step2 was not run on that
render; its APP_ALLOW check would have failed. Fix is the full command with the flag.
**Rolled correctly the same day (pod `benchmarks-fluent-bit-rvm49`). First run `1789463971`, exports
`…-7` (598 polaris-logs docs) / `…-8` (report `seq` 3–4 only):**
- detail is exactly the replay's prediction: 598 docs = 343 access + 180 IcebergExceptionMapper (4 ERROR)
  + 75 PolarisServiceImpl; **no dropped logger present**; `clientSecret` all `*`.
- `schema_version 4`; `app_dropped` rows present (seq 4: 7+4+4+4+2 = `app_dropped_total` 21).
- seq 3 / 4: `access_kept` 6 / 39 == detail docs between tick emits (18:19:01.765–31.765–01.769 KST);
  errors 2 / 0 match; resource == principal == access lines (8, 76); management writes 39 == 39 docs;
  `catalog_admin` + `_shared` writes 1 + 25 == 26 `Adding grant` lines. No zero rows without commits.
- Commit-only rows (3 in seq 4) are **creates** (`POST …/tables`, `…/views` keys to the collection, the
  commit to the table) — plan gate G7 corrected; not a fault.
- New pod, new tick phase **1.765s**; the setup burst started +1.57s, so 6 lines went to seq 3.
- **NOT checked:** seq 5 (the matrix window: 298 access lines, 251 errors) was not in the export, and
  `commit_*` / `dropped` were not export columns, so their `long` mapping is unseen.
**2026-09-16 — the matrix window (seq 5) checked: ALL PASS.** Replaying its 696 raw tier-1 docs through the
repo Lua reproduces all 64 report rows with 0 mismatches over 30 fields; G1–G6, G8 and **Gate 2** pass
(`probe_tbl` 1941 == last 2xx write). v4 integers map `long`. #27 stays open only for template (#25), the
1800 revert and ISM. **2026-09-16 later: template applied (37/37), nested-namespace key PASS (run 1789535345,
one row, commit_count 2) — #27 open only for the 1800 revert and ISM.** [`sessions/2026-09-16-v4-phase0-matrix-window.md`](sessions/2026-09-16-v4-phase0-matrix-window.md). What changes when it rolls:
app-log allow-list (`IcebergExceptionMapper`, `PolarisServiceImpl`; WARN/ERROR exempt), dropped lines
counted as `report_type: app_dropped`, `commit_count/commit_ms_*` on table/view rows, zero-carry
deleted (`carried_rows` gone), clientSecret guard. `WINDOW_SECONDS` stays **30** — the 1800 revert is
still its own last step.

- **Verified off-cluster only:** v3 tests + v4 tests pass on LuaJIT and Lua 5.1 against the extracted
  script; a replay of run `1789460891`'s export keeps 598 / drops 158 exactly by logger, errors per
  window 2 / 251 as the real report, commit keys equal the real report's resource keys; every numeric
  field the Lua emits is in `type_int_key`.
- **NOT verified:** no `helm lint` / `--dry-run` render (no helm in the Cowork session);
  `step2-render-gate.sh` updated for v4 but never run against a real render. Nested-namespace `%1F`
  key never seen in real traffic. Deployed ConfigMap sha must read **`f364c89653dfe481`**
  (`step3-postupgrade.sh`).
- **Order:** roll the Lua, THEN apply `polaris-report-template.json` (#25) — it now also types the
  v4 integers as `long`.
- **After rolling, the plan's gates G1–G8** (`logging/PLAN-audit-allowlist-2026-09-15.md` §5).
  Any v3 dashboard reading `carried_rows` or counting zero rows breaks by design; filter `schema_version`.

## Resolved, kept because they recur

**#29 — Tier 1 OUTPUT 2 (`opensearch.1`, `kube.*` → k8s-logs) still discards chunks under traffic, on 5.1.1. DROPPED by Kade 2026-09-16 — not diagnosed, not fixed.** 2026-09-16.
**Dropped (Kade, 2026-09-16 late: "drop #29, since task done"):** no further diagnosis is planned. The fault was never read: the
diagnosis commands' output directory `.scratch/issue29-1356Z/` came out empty, so the cause (mapping reject / 429 / buffer) is unknown
and nothing was changed. It concerns tier 1 only; the Polaris tier-2/3 pipeline was intact in every checked window. If it matters
again (e.g. phase 3.1's load test shows more drops), restart from the commands in `logging/HANDOFF-audit-log-next-2026-09-16.md` §3 A.
Original record:
One chunk per traffic run, twice today, **before and after the v5 roll**, so not caused by v5:
- `1-1789535377` (05:09:37 UTC, v4 pod `rvm49`, traffic window readout `050930Z`): warn 05:09:46, 05:10:07, `cannot be retried` 05:10:45.
- `1-1789548067` (08:41:07 UTC, v5 pod, step-7 traffic window `084100Z`): warn 08:41:19, 08:41:38, `cannot be retried` 08:41:52.
`Retry_Limit 3` exhausts and the chunk is dropped. **It is not `#19`'s signature as far as step3 shows:** step3's
grep matches `cannot`, and no `cannot increase buffer` line appeared — but step3 does not print the lines that say
*why* a flush failed (`[output:opensearch:opensearch.1] http_do=… / HTTP status=…`), and OUTPUT 2 has no `Trace_Error`,
so per-item `_bulk` rejections are invisible. Candidates, none measured: a per-item mapping rejection (deterministic,
so every retry fails — fits "one chunk, all retries fail"), OpenSearch 429 under the burst, or `Buffer_Size False`
behaving differently on 5.1.1 than on 3.2.2 where `#19`'s 7 → 0 gate was taken.
**What it did not hit (measured from `.scratch/readout-2026-09-16T084100Z/tier1.json`):** the 720 Polaris tier-1 docs
in the step-7 interval have 720 distinct `sequence`, 0 duplicates, and step11 replays them to the pipeline's exact
rows — so no Polaris record in that window was lost or duplicated. Fluent Bit chunks are per tag (= per container log
file), so the dropped chunk is most likely another container's. Which one is unknown. Still real tier-1 loss.

**#28 — Policy v5 (404 counted, not stored) + Lua as its own ConfigMap: ROLLED 2026-09-16 (rev 17) and verified. Hot reload REMOVED and ROLLED the same day.** 2026-09-16.
Decisions (Kade): 404 access lines count into `errors_4xx`/`counted_404` and are not stored; the allow-listed
app lines of a 404 request are dropped too, **matched by `mdc.requestId`** (hold until the access line, 30 s
orphan timeout → stored with `held_orphan: true`). Lua ships as ConfigMap `polaris-fluent-bit-lua`
(`fluent-bit/kustomization.yaml`), mounted via `extraVolumes`, reloaded by the chart's `hotReload` sidecar;
**no `--set-file`**. Also: `/namespaces/{ns}/register` → kind `collection`.
- **Verified off-cluster only:** v3/v4/v5 Lua tests ALL PASS on LuaJIT and Lua 5.1; `kustomize build` (v5.4.3)
  output byte-identical to the file (sha `80119adc…` before the header-title fix — step3 recomputes); step2
  run against a **simulated** render built from chart 0.57.6 templates + values.yaml: all PASS. step11 replay
  of the 2026-09-16 window predicts detail 300/32/178 → 200/22/78 (access / ServiceImpl / ExceptionMapper).
- **Pre-roll re-check (2nd Cowork session, 2026-09-16), still off-cluster:** v3/v4/v5 ALL PASS again on LuaJIT
  2.1 against the committed script (sha256 `bfff86db220036c2`). Chart **source** for 0.57.6 read from
  `fluent/helm-charts` tag `fluent-bit-0.57.6` (`79fa0f4`): every v5-wiring expectation in step2 is what the
  templates emit — `--enable-hot-reload` appended to the default args, one `reloader` container
  (`ghcr.io/jimmidyson/configmap-reload:v0.15.0`, must be pullable on OrbStack) posting to
  `localhost:2020/api/v2/reload` (values' `HTTP_Server On` / `HTTP_Port 2020` satisfy it), `-volume-dir=/watch/extra-0`
  mounting `polaris-lua`, `checksum/*` annotations omitted, an empty `-luascripts` CM mounted at `/fluent-bit/scripts`.
  The reloader also watches `/watch/config`, so a Helm config change reloads rather than restarts. Still **no real
  render**: get.helm.sh, fluent.github.io and proxy.golang.org are all blocked from Cowork, so helm cannot be
  obtained or built; step2 on Kade's real render remains the first real run.
- **step3 run by Kade, 2026-09-16 (~17:2x KST): the DaemonSet is NOT on v5.** `ds/benchmarks-fluent-bit` has no
  `reloader` container and no `--enable-hot-reload` — per the 0.57.6 template source both are unconditional under
  `hotReload.enabled: true`, so the live pod template was not rendered from the committed values. ConfigMap
  `polaris-fluent-bit-lua` IS applied (sha `bfff86db220036c2` == repo). restartCount 0, and the pod log still holds
  engine lines from 05:09 UTC (before v5 was written), so the pod was not replaced either. The in-pod script sha
  (`8c1fb607…`) is unexplained — not any committed version of the Lua; possibly an exec error string (5.1.1 image
  may lack `cat`). **Cause established the same afternoon: step 5 (`helm upgrade`) was never run.** `helm history`
  tops out at **rev 16, 2026-09-15 18:18 KST, deployed, SSA** (no failed revision, so no SSA conflict);
  `get values` still has `luaScripts:`; DS volumes are `config luascripts varlog varlibdockercontainers
  etcmachineid` (no `polaris-lua`); generation 25 == observed; pod `benchmarks-fluent-bit-rvm49`, 23h, 0 restarts.
  So the running pod is v4 and the in-pod sha was of a path that does not exist (step3 mislabels that as "not synced"). Tier 1 alive (k8s-logs 22874/10m); report 20 docs/10m.
  Separately: a tier-1 chunk (tail.0 → opensearch.1, k8s-logs `kube.*`) was dropped after retries at 05:10:45 UTC.
- **ROLLED, 2026-09-16 ~17:35 KST (08:35 UTC pod start).** step2 on the **first real helm render**: all PASS
  (41 checks, including every v5-wiring expectation written against the simulated render). `helm upgrade` →
  rev 17. step3: rollout complete; containers `fluent-bit` (5.1.1) + `reloader` (configmap-reload v0.15.0), 0/0
  restarts; `--enable-hot-reload` present; ConfigMap sha `bfff86db220036c2` == repo; no error/lua/parser lines in
  the pod log; **tier 1 alive (k8s-logs 23012 docs/10m)**; polaris-report 20 docs/10m (may include pre-restart
  windows — `schema_version` 5 not yet read); polaris-logs 0/10m (idle Polaris, expected); `hot_reload_count` 0.
  The one FAIL (image) and the `????` (in-pod sha) were **step3 bugs**, fixed in the same commit: the image
  check read both containers' images; the in-pod check hashed the runtime's "cat not found" message
  (`8c1fb607ef937f3a`, identical on the v4 pod where the path did not exist) — the image is distroless. Also
  fixed: section 6 had printed "could not parse metrics" on every run ever — backslashes inside f-string
  braces are a SyntaxError before Python 3.12. **Re-run with the fixed step3: `post-upgrade checks passed`. step9:
  `PASS -- template stored and every field simulates as declared` (41 fields).**
  **step7 (Kade): step11 `PASS: 0 field mismatch(es) over 67 rows x 34 fields`** — 34 = v4's 30 + the four v5
  fields; PASS also requires the row sets and the detail-docs-by-logger counts to be equal, so the running
  pipeline reproduces the repo v5 Lua exactly on its own raw tier-1 input. **`polaris-logs-*` docs with
  `http_status: 404` since 08:36 UTC: 0.** Read by Claude from `.scratch/readout-2026-09-16T084100Z/`: window
  **08:41:00Z** (17:41 KST), `schema_version` **5**, `report_seq` 12, access_seen 355 / kept 200 / counted 155,
  errors_4xx 247, **`counted_404` 100, `app_dropped_404` 110**, app_dropped_total 155, held_orphans 0,
  held_pending 0; record span 08:41:06.56–08:41:15.14 (8.6 s ≤ 30). Detail docs: **200 / 22 / 78** (access /
  PolarisServiceImpl / IcebergExceptionMapper) — **exactly the replay prediction made before the roll**; no 404
  among detail statuses (401 59, 403 45, 204 27, 400 26, 201 17, 409 11, 422 6, 200 5, 500 4); 0 held_orphan docs.
  **So the 404 policy and the request-id drop are verified on live traffic; step 7 PASS.**
- **HOT RELOAD REMOVED — ROLLED 2026-09-16 (Kade): step3 `RESULT: post-upgrade checks passed`** — with the new
  checks that means one container (no reloader), no `--enable-hot-reload`, container start ≥ ConfigMap change,
  CM sha == repo, tier 1 receiving. Only the RESULT line was pasted: step2's output and the new revision
  number (expected 18) are not recorded. `apply-lua.sh` has still never run for real. Decision record follows.
- **Re-verified on the no-reload pod `benchmarks-fluent-bit-fjdjb` from Discover exports (`…-3.csv` detail, `…-4.csv`
  report), run `1789549828`, 18:10–18:11:30 KST, report seq 7/8/9:** seq 9 (09:11:00Z) is **identical** to the 08:41Z
  window — 355 seen / 200 kept / 155 counted (100 × 404), 247 4xx, 4 5xx, 104 denied, 57 resources, 4 principals,
  155 app lines dropped, 1,035,369 bytes; detail 200 / 22 / 78 (access / ServiceImpl / ExceptionMapper), 0 × 404
  stored. In every window: detail access docs == `access_kept` (35 / 8 / 200); resource totals == principal totals
  == access lines, bytes included (21,643 / 183,509 / 1,035,369); `app_dropped` rows sum to the summary; all 143 app
  docs join an access doc by `mdc.requestId`, no duplicate request ids. The run spans three windows (seq 7–8 are
  setup: 201s and grants). Not checkable from these CSVs: `counted_404` / `app_dropped_404` / `held_*` columns were
  not selected in Discover, and numbers export with thousands separators (`1,898`).
- **Same run from Dev Tools JSON (`polaris-summary.json` = request 2 for 09:11:00Z, 67 rows; `polaris-log.json` = 386
  polaris-logs docs 09:10:28–09:11:12Z)** — the fields the CSV lacked: `counted_404` 100, `app_dropped_404` 110,
  `held_orphans` 0, `held_pending` 0, `partial_window` `"false"` (a string), `role_keys_forced` 4, span 09:11:06.57–12.92.
  Identities hold: `access_kept` 200 = 355 − 155; `access_counted` 155 = 100 (404) + 31 read + 24 POST;
  `errors_kept` 151 = 247 + 4 − 100 (404s not kept); `app_dropped_404` outside `app_dropped_total`. Commit fields on 5
  table/view rows, incl. `probe_ns%1Fnested/…/mx_1789549828_deep` commit_count 2 (TODO 1.5 shape again). Detail: all
  numerics typed int; no duplicate `_id`; every app doc joins an access doc; `exception` is an object with a
  `frames` array of {class, method, line}; `clientSecret: *` (Polaris' own mask) on 4 docs, `secret_redacted` never
  set; held PolarisServiceImpl lines carry `@timestamp` up to 21 ms after `_time` (v5's documented behaviour).
  **Found: the Dev Tools response panel is not JSON** — multi-line strings print as triple-quoted blocks with
  re-indented continuation lines (300 `_msg` + 4 `exception.message`; 53 messages differ in whitespace, identical
  after normalising). `devtools-export.console` now says so; `logging/scripts/devtools-json-fix.py` repairs a panel copy.
- *(as written, Kade's decision 2026-09-16)* Wanted: no reloader, Lua and
  config read at start only, simple config. Choice among two: *Helm `--set-file`* (one command, chart checksum
  restarts; the 09-15 outage risk) vs **separate ConfigMap + restart** — **chosen**. Changes:
  `values.yaml` drops the `hotReload` block (chart default false → no `reloader`, no `--enable-hot-reload`, no
  empty `-luascripts` CM/mount, `checksum/config` back on the pod template — chart 0.57.6 source);
  new **`fluent-bit/apply-lua.sh`** = context guard → LuaJIT tests v3–v5 → `kubectl diff -k` (unchanged + pod
  newer than CM → nothing to do) → `apply -k` → `rollout restart` → `rollout status` → Lua load errors in the
  new pod's log → CM sha == repo (`--no-restart` for a change that also needs `helm upgrade`; `--restart` to
  force). step2 flipped (flag 0, reloader 0, `configmap-reload` 0, `luascripts` 0, `checksum/config` 1);
  step3 drops reloader/args/reload-counter checks and the meaningless in-pod file check, and adds **fluent-bit
  container `startedAt` ≥ the ConfigMap's last `managedFields` time** — the only outside evidence the process
  loaded the current script. apply-lua.sh's control flow was exercised with a mocked kubectl/luajit only.
  Runbook B/C dropped (never run, nothing measured); D becomes "tier-1 gaps across a restart".
  **Roll (Kade):** step2 on a fresh render → `helm upgrade` (no `--set-file`) → pod restarts once, 1 container
  → step3. Rollback: `helm rollback benchmarks-fluent-bit 17`. Leaves ConfigMap `polaris-fluent-bit-lua` as is.
- **NOT verified (as originally written; hot-reload items moot since its removal):** any real `helm` render (no helm in Cowork); hot reload itself; **what 5.1.1 does when a
  reloaded script is invalid** (runbook C — may stop tier 1 like #27); reload loss (runbook D); whether
  Polaris assigns `requestId` without a client header (production question — if not, 404 app lines are kept).
- **Order:** tests → `kubectl kustomize` + helm dry-run → step2 (two args) → **`kubectl apply -k fluent-bit/`
  BEFORE `helm upgrade`** (missing ConfigMap = ContainerCreating) → step3 → step9 re-apply (41 fields) →
  traffic → step10/11 → runbook B/C/D. [`logging/RUNBOOK-lua-hot-reload-2026-09-16.md`](../logging/RUNBOOK-lua-hot-reload-2026-09-16.md).
- **Until it rolls, #27's rule stands:** the running release is v4 and any `helm upgrade` of the *old* values
  still needs `--set-file`. After v5 is rolled, `--set-file` must NOT be used (it would re-add a luascripts key
  nobody reads, harmless, but a sign the wrong runbook is being followed).

**#13 — RESOLVED. `polaris_noise_filter` was written and not running; it runs now.**
Measured absent on 2026-09-04 (0 of 34 expected drops dropped; twenty identical
`GET .../tables/probe_tbl` stored twenty records). The filter entered `fb-values.yaml` in
**2120ed9, 08:26:18Z 2026-09-03**; the shipper pod had run since **08:04:06Z** from
**60b94d9**, which carries the parser and no filter. `helm upgrade` had never been run.
It was run: the shipper pod dates from **04:57:36Z 2026-09-04**, the second coverage run
reports *retention policy deployed? True — the running ConfigMap carries this exact script*,
and **34 of 34 expected drops dropped.**

**Kept because the pattern is the repo's whole failure mode.** This was #F1 in a different
file: configuration written correctly, five documents describing it as built, and nothing
warning that none of it was the running object. What caught it was not a review — it was a
harness that ran the *deployed* Lua and compared it against what the pipeline actually
stored. **#14b is the same state again**, entered knowingly.

**#F1 — An entire values block was inert for months. RESOLVED-INSTRUCTIVE.**
`postgresql/` is an umbrella chart. Helm passes values to a subchart only when
nested under the subchart's name — everything at the top level was silently
ignored, and the cluster ran on subchart defaults:

| intended | actually in effect |
|---|---|
| `max_connections = 200` | **100** |
| `shared_buffers = 384MB` | 128MB |
| `log_min_duration_statement = 1000` | -1 (off) |
| `persistence.size: 10Gi` | 8Gi |
| explicit 2Gi resources | `resourcesPreset: micro` |
| `disableLoadBalancingOnWrite: always` | `transaction` |
| `/dev/shm` emptyDir | not mounted (64MB default) |

Detected by comparing a value against the **subchart default**, not against the
values file: `pgpool.replicaCount: 3` with one pgpool pod running proved the block
was dead. `postgresql.replicaCount: 3` matched only because 3 is also the default —
a coincidence, not evidence. **Verify against defaults, never against intent.**
This is also why #1 above matters: the rebuild is exactly the moment that gap
reopens.

**#F2 — `0.0.0.0/0` does not match IPv6. RESOLVED-INSTRUCTIVE.**
The custom `pgHbaConfiguration` was IPv4-only; OrbStack's pod network is IPv6
(`fd00::/8`), so repmgr's pod-to-pod connection was rejected and a standby went
into CrashLoopBackOff. It never bit while #F1 was in force, because Bitnami's
*default* pg_hba includes `::/0`. **Un-inerting configuration that has never
executed is a change, not a fix** — review it line by line against the defaults it
replaces.

## Standing constraints

- **`persistence.size` is now-or-never.** A PVC cannot be grown in place after
  install. Whatever the rebuild set is what this cluster has.
- **Resource footprint.** The full set (DataHub + prerequisites + Kafka + Spark +
  Airflow) needs >7GB RAM on the daemon node.
- **`ALTER SYSTEM SET shared_preload_libraries` replaces, it does not append.**
  Running it bare drops `repmgr` and silently disables automatic failover.
  `postgresql.auto.conf` lives on each pod's PVC and does not replicate.
- **`git status` hygiene.** `.gitignore` covers `.idea`, `node_modules`,
  `postgresql-ha-*.tgz` and `.DS_Store`. Still check `git status` **before**
  `git add -A`, never after — chart tarballs and `helm get values` exports are not
  covered by any pattern.

**#21 — RESOLVED 2026-09-09 (REVISION 7).** *(filed as #16 by mistake — #16 was taken; renumbered.)* Cause: `multiline.parser cri` alone on the tier 2
tail; `docker, cri` fixes it. Verified on post-fix documents — 4,403/4,403 with `loggerName`, 0
with `log` — and by the `unwrap -> rename` delta moving 12.00 -> 6.97 B/rec. The ~29,800 raw
documents already in `polaris-logs-*` predate the fix, are not rewritten, and age out under the
30d policy. Mechanism unknown; measurement unambiguous. Original entry follows.

**#21 (original) — Policy v3 is INERT on tier 2: `polaris-logs-*` is storing unfiltered stdout. OPEN, LIVE.**
Measured 2026-09-09. The notebook run put **4,718 docs / 2.7 MB** into `polaris-logs-2026.09.09`
for roughly 270 requests, while the DaemonSet's own report said `access_seen 0` for the same
windows. Both are true: records traverse the chain and index fine, but **none is recognised as an
access-log line** (`loggerName ~= "io.quarkus.http.access-log"`), so every record takes the keep
path and no retention rule applies. The tier advertised as "30d, policy-v3 filtered" is currently
a firehose with a 30d retention on it, and it looks healthy — no errors, no restarts, no drop
counters. Storage grows with traffic until fixed. **Not a values-file fault**: the
`polaris_cri_unwrap` filter, `Parsers_File custom_parsers.conf` and `Time_Keep On` were each
checked and are present. **ROOT CAUSE FOUND 2026-09-09:** `polaris_stdout_json` carried
`Time_Key timestamp` / `Time_Format %Y-%m-%dT%H:%M:%S.%L%z` / `Time_Keep On` and its parse failed
on every record — measured at the filter, `records 5030 / drop 0 / add 0`, byte delta 12.00 B per
record. Those three lines are now **removed from `fluent-bit/values.yaml`, and NOT YET DEPLOYED**.
Until `helm upgrade` runs and §A's gate passes, this issue is live exactly as described.
Evidence: `sessions/2026-09-09-stdout-not-equivalent.md`; change and gate:
`logging/PLAN-tier2-parse-fault-2026-09-09.md`.

**#22 — RESOLVED 2026-09-09, AND THE ORIGINAL FINDING WAS WRONG.** *(filed as #17; renumbered with #21.)* Re-measured after the
`multiline.parser` fix, one burst, matched windows: **`access_seen` 265 (stdout) == 265 (file)**
and **`access_kept` 126 == 126**. Per-window differences (+15, -17, +2) sum to zero — records fall
in adjacent 30s buckets, none is lost. Stdout carries the same access-log set as the file AND
policy v3 decides identically on both. The original "file 270, stdout 0" was taken while the CRI
unwrap was silently not parsing, so the stdout side could not count anything: **the disproof was
an artefact of `#21`, not a property of stdout.** Cutover step 7 is unblocked; `helm uninstall` of
the shipper still needs authorisation at the moment of execution and destroys the ability to
repeat this. Original entry follows.

**#22 (original, SUPERSEDED) —**
The cutover assumed Polaris stdout carries the same access-log set as the log file. Measured on
matched windows 2026-09-09: file 226 + 44 = **270**, stdout **0**. Until #16 is resolved,
`fb-polaris-shipper` and `polaris-shared-logs-pvc` are the ONLY path that recognises an access-log
record. Uninstalling the shipper — cutover step 7 — would destroy the capability, not just the
duplicate. Fallback specified in git at `fb91949`.

**#18 — `Id_Key sequence` skips every record it was meant to dedup. CLOSED 2026-09-16: the output was deleted (review P2, schema v6
roll `#32`); tier 1 keeps no dedup (option B of `PLAN-tier1-dedup`). Original: OPEN, LIVE, and it defeats
the dedup it exists for.** Pod log, 2026-09-09 05:07:
`[output:opensearch:opensearch.0] the value of sequence is not string` followed by
`skipping record with missing or unsafe Id_Key value`, repeating continuously.
`opensearch.0` is OUTPUT 1 (`Match kube.*benchmarks-polaris*`, `Id_Key sequence`,
`Write_Operation upsert`). Polaris emits `sequence` as a JSON **integer** (`"sequence":49687`);
the OpenSearch plugin requires the `Id_Key` value to be a **string** and drops the record
otherwise. So OUTPUT 1 has been indexing **nothing** — and the records survive only because
OUTPUT 2 (`Match kube.*`, `Generate_ID On`) matches the same records and indexes them with a
generated id. Net effect: the upsert-by-sequence dedup has never once operated, and a retried
chunk produces **duplicates** instead of upserts. `repository-map`/roadmap's "sequence in
particular makes a gap in ingestion visible" describes a mechanism that is not running.
Fix is `type_int_key`-style coercion to string, or `Id_Key` on a string field, or drop OUTPUT 1
and let OUTPUT 2 own the tag.

**SETTLED 2026-09-09: `#18` IS RIGHT, `#16` IS NOT.** Ratio 1.000 over 13,796 documents; the
busiest `sequence` buckets hold one document each. OUTPUT 1 indexes nothing, so the record really
is dropped rather than merely losing its `_id`, and `#16`'s double-write claim is disproved. The
contradiction as it stood is kept below.

**THIS CONTRADICTS `#16`, AND ONE OF THEM IS WRONG.** `#16` states every Polaris stdout line
exists in `k8s-logs` **twice** — both outputs match the tag — and instructs every comparison
against tier 1 to deduplicate on `sequence` first, calling an undeduplicated count "~2x wrong".
But if OUTPUT 1 skips each record for an unusable `Id_Key`, **only OUTPUT 2 ever indexes it and
there is no second copy.** `#16` was reasoned from the config; `#18` is read from the pod log.
Neither has been measured against the index, and `#18`'s "skips the record" is my reading of the
message text, not a proven drop.

**One query settles both**, and until it is run neither number should be used in a measurement:
```bash
curl -sk -u "$OS_USER:$OS_PASSWORD" -H 'Content-Type: application/json' \
  "$OS_URL/k8s-logs-*/_search?pretty" -d '{"size":0,"query":{"exists":{"field":"sequence"}},
   "aggs":{"per_seq":{"terms":{"field":"sequence","size":5},
     "aggs":{"n":{"value_count":{"field":"sequence"}}}}}}'
```
2 docs per `sequence` -> `#16` is right, `#18`'s drop reading is wrong. 1 doc -> `#18` is right and
`#16`'s 2x-inflation warning is void, along with the dedup instruction in
`PLAN-opensearch-cutover` §7.

**#19 — RESOLVED 2026-09-09 (REVISION 10).** `Buffer_Size False` on all four OpenSearch outputs.
**Gate passed against a real baseline: 7 -> 0** occurrences of
`cannot increase buffer|cannot be retried` in a 10-minute window, both windows containing a
notebook run so the load is comparable. A zero measured while idle would have proved nothing;
the 7 is what made this a gate.

**One thing this DID NOT settle, and cannot any more.** Whether the historical failures lost
records or duplicated them is now unanswerable: the fix removed the failures, so the window that
was both *loaded* and *failing* no longer exists. The dedup ratio measured after the fix, under
load — 13,737 documents over 13,737 distinct `sequence`, ratio **1.000**, busiest buckets one
document each — says the steady state is clean, which is what matters going forward. It says
nothing about what happened during the four dropped chunks on 2026-09-09. Do not cite it as
evidence those chunks did not duplicate.

*Original entry follows.*

**#19 (original) — Tier 1 is LOSING CHUNKS: the OpenSearch response exceeds the output's buffer.**
```
[warn ] [http_client] cannot increase buffer: current=512000 requested=544768 max=512000
[warn ] [output:opensearch:opensearch.1] http_do=-1 URI=/_bulk
[error] [engine] chunk '1-1788930438.635329228.flb' cannot be retried: task_id=11,
        input=tail.0 > output=opensearch.1
```
Four distinct chunks unretryable in ~90 seconds on 2026-09-09. `opensearch.1` is OUTPUT 2, the
node-wide k8s-logs sink. The `_bulk` **response** is larger than the plugin's 512000-byte read
buffer, the flush fails with `http_do=-1`, `Retry_Limit 3` exhausts, and the chunk is
**discarded**. This is unacknowledged data loss on tier 1, happening now, and it is invisible to
every gate used so far: `k8s-logs` doc counts keep rising because most chunks still succeed.
**FIX APPLIED 2026-09-09, NOT DEPLOYED:** `Buffer_Size False` on all four OpenSearch outputs.
Plan, mechanism and gate: `logging/PLAN-bulk-response-buffer-2026-09-09.md`. Not a bulk-size
reduction — that treats the symptom. Not a cutover regression by evidence; no before/after
measurement exists.

**BASELINE RECORDED 2026-09-09, under load, BEFORE the fix: `7`** occurrences of
`cannot increase buffer|cannot be retried` in a 10-minute window containing a notebook run. The
fix is deployed as **REVISION 10** (ConfigMap and running process both confirmed). **The AFTER
number is not taken yet** — it requires a second notebook run so the load is comparable. Until
then `#19` is fixed-but-unverified, not fixed.

**`#18` AND `#19` COMPOSE, and it changes what `#19` costs.** The plugin cannot read the reply, so
it does not know whether the batch was indexed. If it *was*, each retry writes it again — and tier
1 has **no dedup at all** (`#18`: `Id_Key sequence` drops every record, so only OUTPUT 2 stores
anything and `Generate_ID On` mints a fresh `_id` per attempt), giving up to 3 duplicate copies per
failing chunk. If it *was not*, the records are lost when the chunk is discarded. Nothing
distinguishes the two afterwards. So `#19` is not simply data loss: it is **an unbounded mixture of
loss and duplication, under load, with no signal either way** — the duplicate-generating machine
`#16` feared, reached by a route `#16` did not propose.

**This is also why the `sequence` ratio of 1.000 does not clear it.** That window was quiet, and
these failures only occur under load. A duplicate-ratio measured while idle cannot see `#19`.
Re-measure `step7-dedup-check.sh` immediately after a notebook run, before the fix is deployed, if
a number is wanted for the record.

**#20 — A `helm upgrade` may update the ConfigMap without restarting the pod, so committed config
is not running config. SUSPECTED, not yet confirmed.** 2026-09-09: after `6dfa0d0` the filter map
shows `hb_parse_probe: null` and `_cat/indices/fb-heartbeat-*` is empty — the heartbeat blocks are
not in the running instance. Meanwhile `polaris_cri_unwrap`'s cumulative record counter went
**5,030 -> 5,009**, and cumulative counters only decrease across a process restart, so the pod
*has* restarted at some point. The fluent-bit chart does not necessarily stamp a
`checksum/config` pod annotation, and **a DaemonSet does not roll on a ConfigMap change by
itself** — so `helm upgrade` can report success while every pod keeps serving the previous config
until something else restarts it.

If true this is not a new fault, it is the explanation for an existing one: **Fault A's gate
failure (`has_logger 0` after `4788294`) would mean the fix was never running when it was
measured.** That must be settled before the fix is judged.

Split it with:
```bash
helm -n datahub-hynix history benchmarks-fluent-bit | tail -3
kubectl -n datahub-hynix get cm benchmarks-fluent-bit -o json \
  | jq -r '.data["fluent-bit.conf"]' | grep -c heartbeat
kubectl -n datahub-hynix get pods -l app.kubernetes.io/name=fluent-bit \
  -o custom-columns=NAME:.metadata.name,START:.status.startTime,RESTARTS:.status.containerStatuses[0].restartCount
```
- ConfigMap **contains** `heartbeat`, pod does not -> config deployed, pods never rolled.
  `kubectl -n datahub-hynix rollout restart ds/benchmarks-fluent-bit`.
- ConfigMap **lacks** it -> the upgrade did not run.

Durable fix either way: a `checksum/config` pod annotation so a values change always rolls the
pods, instead of "deployed" and "running" being two different facts nobody checks.

**#23 — Two documents in a post-fix window still carry a raw `log`. OPEN (low), unexplained.**
2026-09-09, `polaris-logs-*` split by time: the newest bucket is 3,575/3,575 parsed with **0** raw,
but the bucket before it holds **2 raw documents out of 4,576 — 0.04%**. Not a failure of the
`multiline.parser` fix, which is working on everything else in the same window, and far too rare to
be a parser regression.

Most likely a Polaris stdout line that **is not JSON** — a JVM or container message, or a
stack-trace fragment the multiline parser did not join — which `polaris_stdout_json` correctly
declines, leaving `log` intact via `Reserve_Data On`. That would be right behaviour, not a bug.
**Unverified**; nobody has looked at the two documents.

*A `now-30m` window does NOT find them* — tried 2026-09-09 and it returned far too many, because
30 minutes reaches back past the roll into the 29,803 pre-fix raw documents that share the index.
Do not filter by a window at all. **Sort by time descending and take the newest raw documents**,
which answers "when" and "what" at once:

```bash
curl -sk -u "$OS_USER:$OS_PASSWORD" -H 'Content-Type: application/json' \
  "$OS_URL/polaris-logs-*/_search?pretty" -d '{"size":3,
    "query":{"exists":{"field":"log"}},
    "sort":[{"@timestamp":"desc"}],
    "_source":["@timestamp","log","stream","flb_tag"]}'
```
If the newest raw document predates the roll, there are no post-fix ones and this closes itself.
If it postdates the roll, its `log` value says immediately whether it is a non-JSON line — which
would be `polaris_stdout_json` correctly declining, and right behaviour.
Worth knowing because if they are NOT stray non-JSON lines, the tier 2 parse has a rare failure
mode and the 0.04% is the only place it shows.
**#24 — Four Polaris operations answer 500 to a malformed request. OPEN, and it makes `errors_5xx`
drivable on demand.** API matrix run `1789026666`, 2026-09-10: `getToken`, `createNamespace`,
`renameTable` and `renameView` each returned **500 where the matrix targeted 400**, trace verdict
`unhandled` on all four — a throwable survived to the transport. 4 five-hundreds in 286 cells, 0
transport errors.

Two consequences, and the second is the useful one:

- **It widens `#15`.** That issue says Polaris 500s on the create path and reads as an NPE on
  create-then-resolve. Three of these four are not creates and one (`getToken`) is not even a
  catalog operation, so "the create path" is not the shape of the fault. What the four share is
  **malformed input on an operation whose 400 handler does not cover it**.
- **`errors_5xx` can now be exercised without cluster surgery**, which is the standing question in
  `roadmap.md` — no scaling, no HPA movement, no `503` route that invalidates the run. Four named
  operations, reachable through the API alone.

Not chased, deliberately: the run's job was coverage, and Polaris is not to be changed (`MEMORY.md`
standing). What is missing before anyone files this upstream is the **stack trace per operation**,
which `polaris-logs-*` holds in full by rule 3 (`http_status >= 400` over the run's windows, field
`exception.frames` — not `exception`).
**Stack traces now in hand (2026-09-16, run `1789549828`, window 09:11:00Z, Discover export
`opensearch_export_2026-09-16-3.csv`).** Reproduced a third time: the same four operations, 4 × 500, each with one
ERROR `IcebergExceptionMapper` "Unhandled exception returning INTERNAL_SERVER_ERROR" joined by `mdc.requestId`, all
`java.lang.NullPointerException`, top frames:
- `POST …/tables/rename` and `POST …/views/rename`: *"identifier" is null* —
  `PolarisCatalogHelpers.tableIdentifierToList:38` ← `CatalogHandler.authorizeRenameTableLikeOperationOrThrow:339`
  ← `IcebergCatalogHandler.renameTable:956` / `renameView:1135` (58 frames). A null source/destination reaches
  authorization before validation.
- `POST …/namespaces` (createNamespace): *"namespace" is null* — `IcebergCatalogHandler.createNamespace:284` (56 frames).
- `POST /api/catalog/v1/oauth/tokens` (getToken): *"o" is null* — `ImmutableCollections$Set12.contains:817` ←
  `JWTBroker.supportsGrantType:169` (42 frames): a request without `grant_type`.
Polaris 1.3.0-incubating. Enough to file upstream; not filed (Polaris is not to be changed from here).

**#25 — The report index template and the `""`-free Lua. CLOSED 2026-09-16: template applied (step9 PASS), Lua rolled.** 2026-09-10.
*(Header corrected 2026-09-16; the body keeps the original "WRITTEN AND NOT APPLIED" record and the APPLIED note.)* `logging/opensearch/polaris-report-template.json` exists in the
repo; nothing has PUT it to OpenSearch. `fluent-bit/values.yaml` no longer writes `""` for
`min/max_record_time`; the running pod still does. Until both land:
**2026-09-16 — APPLIED.** `PUT _index_template/polaris-report` acknowledged; a simulated new index maps
`min/max_record_time` as `date`. Existing indices as expected: 09.09 / 09.10 / 09.14 `text` for life; 09.15 / 09.16
already `date` by dynamic mapping (the Lua has omitted `""` since 09-10). step9's read-back was a `grep | head -20`
that showed 19 of 35 `long` fields — rewritten to compare all 37 fields. **Rerun PASS: 37/37 stored and simulated.** #25 is closed for new indices; 09.09/09.10/09.14 stay text.

- `polaris-report-2026.09.10` and every earlier index keep `min_record_time` as **`text`** — no
  range query, no date histogram, for the life of those indices. The invariant
  `max - min <= window_seconds` is still checkable client-side, because RFC3339 parses.
- **Order is load-bearing.** The Lua must be rolled *before or with* the template. With the fields
  typed `date`, a document carrying `""` is rejected **per item inside a `_bulk` that returns HTTP
  200** — the silent failure mode this pipeline has already produced twice. `ignore_malformed: true`
  is set on both fields as the backstop; it costs the field, never the document.
- Applying the template is `bash logging/scripts/step9-report-index-template.sh`, and it is **not
  retroactive** — the first correctly-mapped index is the next day's.
