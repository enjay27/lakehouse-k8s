# 2026-09-18 — the v4 schema checks ran, and the PASS was narrower than it read

Cowork session. **No cluster, Docker or psql reach** (CLAUDE.md). Kade ran every command that
touched the image or the repo's `/tmp`; this session read the output, found a gap in what it
proved, and edited files.

## What Kade brought in

The verifier, run with the **shipped** v3 as its baseline:

```
v3 10   v4 21   migration 11
declared version -- v3 3, v4 4, migration 4
shared objects: 10, of which differing: 0
objects v4 adds over v3: 11
PASS
```

Then, on request, two more commands: the step 2c baseline `diff`, and a grep of the shipped v4
for every statement the verifier does not inspect.

## Three results

1. **The baseline claim is true, and had never been tested.** `CLAUDE.md` has called
   `postgresql/schema/schema_v3.sql` "the ASF-shipped file and the authority" since August.
   Diffed against `/tmp/schema-v3.shipped.sql`: **indentation only** (the repo copy is
   IDE-reformatted with deep column alignment), plus a missing trailing newline. No column,
   type, constraint, index or version value differs. So the whole delta analysis — computed
   against that file — was standing on solid ground after all.
2. **The transcription is faithful.** 11 added objects, 11 in our script, no extras, 10 shared
   objects identical. `ce72bde`'s circularity is closed: additive-only is now measured against
   the distribution, not against our own copy of it.
3. **The PASS covered less than it claimed, and the gap was occupied.** Both claims only match
   `CREATE TABLE/INDEX/SCHEMA/VIEW`. Running the verifier's own parser over the repo's v3
   showed **26 of 36 statements are none of those**. The grep of shipped v4 found two
   `COMMENT ON TABLE` statements our migration omitted — lines 226 and 295, on
   `scan_metrics_report` and `commit_metrics_report`. It also found, reassuringly, **no**
   `CREATE FUNCTION`/`SEQUENCE`/`TYPE`/`TRIGGER`, **no** `GRANT`, **no** `ALTER`, and one
   `INSERT` (the version row) — additive-only survives the wider look.

## What changed

- `postgresql/schema/migrate_v3_to_v4.sql` — the two `COMMENT ON TABLE` statements, verbatim,
  inside the existing transaction, before the version write. Upstream comments only those two
  tables; `idempotency_records` has none, and matching the shipped file beats being tidy.
- `postgresql/schema/verify_v4_transcription.py` — **CLAIM 3**. Every statement the object
  claims cannot see is compared too: a v4-added function, grant, alter or seed insert the
  migration omits now FAILS; an omitted `COMMENT ON` is a NOTE, since the database ends up
  functionally identical. Excluded as legitimately delta-vs-full-schema differences: the
  transaction wrapper, `SET search_path`, psql meta-commands, our `DO` guard, and the version
  row write (already covered by `declared_version`).
- Its header and the runbook's step 2c — the PASS, the diff result, and what the PASS does not
  mean. The migration's `PROVENANCE` block had survived `eddeea5` still telling the reader to
  run `kubectl exec deploy/benchmarks-polaris -- unzip -p /deployments/*.jar`: the command that
  hung, against a 1.3.0 pod that does not ship `schema-v4.sql`, on a path a Quarkus thin jar
  does not use. The runbook was corrected that day and the SQL file was not.
- `MEMORY.md` — the *Now* section had grown to 68 lines against its own ~40-line rule, and the
  Polaris paragraph was a 23-line digest of findings already filed in `active-issues.md`, which
  is the exact thing the file's rules forbid. Condensed to 7 lines of links and the facts that
  would be *false* if stale. 68 → 56. Every fact removed was grepped for in `.memory/` and the
  runbook first; none was only here. It also carried a live contradiction — "Step 1 reframed:
  never a blocker" and, four lines later, "1.6.0 rejects entity names … screen first" — dropped.

## Self-test, because the repo's own standard demands one

A verifier's new check is not evidence until it has failed on a known-bad input. Built a
synthetic v4 (repo v3, version bumped, plus the migration's 11 objects via the verifier's own
parser, plus the two comments):

- round trip against the migration **as committed** → PASS with exactly the two NOTEs, which
  reproduces what Kade's real run would print. After the fix: PASS, no notes.
- synthetic v4 + `CREATE OR REPLACE FUNCTION` → **CLAIM 3 trips**.
- synthetic v4 + `GRANT SELECT` → **CLAIM 3 trips**.

First attempt at building the synthetic file split the migration on `;` and got 8 CREATEs
instead of 11 — comment banners preceding a statement defeat a `^\s*CREATE` match, and the `DO`
block's inner semicolons fragment it. Used `split_statements` + `OBJ` from the module under
test instead. Worth noting the circularity that leaves: the round trip exercises the claim
logic, not the parser, since the same parser builds the input.

## Decided: do not vendor the shipped files

Proposed committing `schema-v3.shipped.sql` and `schema-v4.shipped.sql` into
`postgresql/schema/` to end their perishability. Withdrawn once the diff came back clean:
`schema_v3.sql` *is* the shipped v3, so the repo gains a duplicate and no authority, and this
repo's duplicate-file problem is already in `repository-map.md`. The v4 file is three commands
from the image.

## Open, unchanged by this session

**`2b`, the metastore dump, has not been run**, and it is the rollback for step 2 — the next
thing to do. Re-confirm pg-1 is the primary before `2e`. The HPA may undo `2d`'s scale-to-0
(`#8`).

NOT VERIFIED: no cluster, Docker or psql command was run from this session. The verifier was
re-run here only against synthetic inputs; the run against the real shipped files was Kade's,
before these edits, and it should be repeated after them if the files are still in `/tmp`.

## Later the same day — step 2 ran

Kade ran all of step 2. `2f` returned `version | 4` and nine tables in `polaris_schema`: the
six from v3 plus `idempotency_records`, `scan_metrics_report`, `commit_metrics_report`.

Two observations about that readback, recorded because the first is a design feature worth
reusing and the second is a hole in the step as written:

* **The `4` implies the indexes.** The migration is one transaction and the version write is
  its last statement before `COMMIT`, so a `version_value` of 4 means everything ahead of it
  committed — the 8 indexes included. That ordering was deliberate (it was written so a failure
  leaves the row at 3) and it pays off twice: as a rollback property and as a proof obligation
  discharged for free.
* **`\dt` lists tables only.** Step 2f asked for `\dt polaris_schema.*` and called it
  verification, so the 8 indexes were never actually listed, and neither were the two table
  comments `935c7ed` added. The inference above covers the indexes; the comments depend on
  *which* script ran, since step 2c deliberately sanctioned both ours and the shipped file, and
  ours only acquired the comments in `935c7ed`. Added a `pg_indexes` + `obj_description` query
  to the runbook that settles both, plus the two standalone `COMMENT ON` statements to apply if
  they are missing — re-running the migration is not an option, the guard now refuses v4, which
  is correct.

**New open issue `#35`: the metastore is v4 and the server is still 1.3.0.** Additive-only
means nothing 1.3.0 reads has moved, so this is not expected to bite; whether 1.3.0 *asserts*
`version_value = 3` at bootstrap is undocumented. Upstream's relational-JDBC page covers only
the reverse direction (a newer server finding an older schema, the v5 placeholder case).
Because `2d` scaled to 0, the current pod state answers it for free — and step 4 destroys the
reading, so it is perishable in the same way step 0's captures were. Direction is forward.

NOT VERIFIED: this session ran no cluster command. The step 2 output above is Kade's.

## The three confirmations, and a fourth thing nobody was looking for

`pg_indexes` + `obj_description` + `get deploy,hpa,pods`, all Kade's:

1. **21 indexes**, containing all 8 new ones, v3's three, nine primary keys, and
   `constraint_name` — a `CONSTRAINT constraint_name UNIQUE` on `entities`, an upstream naming
   wart present in the shipped file too. The transaction inference is now a direct measurement.
2. **Both new table comments present**, so the script that ran was post-`935c7ed` or the
   shipped file.
3. **`deployment 0/0`, HPA `REPLICAS 0`.** The clean case.

**On (3), a warning in three documents turned out to be false rather than lucky.** Step 2d,
step 4 and `#8`'s mid-upgrade note all said the HPA might undo the scale-to-0 because
`minReplicas: 1`. **An HPA does not scale a workload up from 0 replicas** — scaling to zero is
the documented way to take a workload out of an autoscaler's hands, and scaling back from zero
needs the alpha `HPAScaleToZero` gate. So `2d` is a safe reversible hold, and the "scale back up
if the HPA hasn't" line in step 4 is not a fallback but the required step. Deleted the warning
rather than hedging it. `cpu: <unknown>` is "no pods to measure", not the 09-09 regression.

Also worth stating plainly: the window `#35` described is **empty, not survived**. No 1.3.0 pod
met the v4 metastore, so nothing was learned about whether 1.3.0 asserts `version_value = 3`,
and "no incident" must not be recorded as "tested". The consequence is for the rollback path:
`helm rollback` alone would leave that untested combination running, so assume the `2b` dump
goes back with it.

## The fourth thing: v3's table comments are missing from the live database

`obj_description` showed the two new tables commented and **all four tables v3 comments —
`version`, `entities`, `grant_records`, `principal_authentication_data` — blank.** Exactly that
set; `events` and `policy_mapping_record` are correctly blank, v3 never comments them.

Chased it in the repo. `postgresql/schema/schema.sql` declares the **same 10 objects** as
`schema_v3.sql`, **0 differing**, both version 3, and differs only by those **24 `COMMENT ON`
statements** — it has none. `bootstrap.sql` has none and declares no version. So `schema.sql`
is *exactly* v3-minus-comments, which is *exactly* the live shape.

**No structural risk, which is worth saying before the speculation:** the live database is
complete v3 — all v3 objects and indexes present — so the migration went onto a correct
baseline and `#34` is unaffected.

Two candidate provenances, neither settled: the database was bootstrapped from `schema.sql` by
hand, or Polaris 1.3.0's own jar shipped a v3 without comments that upstream added by 1.6.0 —
and the file diffed in `#34` came from the **1.6.0** jar, so it cannot speak to 1.3.0.
`RESET-AND-CLEAN-INSTALL.md` favours the second: it bootstraps via `bootstrapCredentials` and
`persistence.relationalJdbc` and never applies a repo SQL file, and no template, values file or
script in the repo references any of the three. But the shape match favours the first.

Filed as `#36` with a three-command discriminator for the next time the 1.3.0 image is pulled
(count `COMMENT ON` in its `postgres/schema-v3.sql`). **Not a gate on step 3**, and the live
database should not be "fixed" by adding the four comments — they are the evidence.

NOT VERIFIED: this session ran no cluster command; all three outputs above are Kade's.

## Step 3 — the render passes, and reading it found the step-4 blocker

All four assertions pass: `console.level=INFO`, **zero** category lines at DEBUG,
`event-listener.types` plural with `PT5S`/`1000` intact, `apache/polaris:1.6.0` at render line
7433. `helm lint` output was never shown, so that half of the DoD gate is on Kade's word.

**The diff against the 0c capture is the useful artifact.** It shows exactly two kinds of
change and nothing else: the listener key `type` → `types`, and **13** category lines
DEBUG → INFO. Two notes on that 13. First, this repo has been saying "ten" in two places in the
runbook — an estimate that was never counted; corrected. Second, the 13 change the ConfigMap
and not the console output, because `console.level` was already INFO at revision 5 (`#33`); the
diff is what turns that from an inference into a measurement, since anything else that had
moved would appear in these forty-odd lines.

A red herring worth recording: `grep -nE '^ *image:'` returned bare `image:` at render lines
117 and 422. Those are `--debug`'s USER-SUPPLIED VALUES and COMPUTED VALUES dumps, where
`image:` is a mapping key with `repository`/`tag` beneath it — not an empty image in a manifest.
The chart has exactly two image references and both render as real containers.

## #37 — the pre-upgrade hook is the likeliest way step 4 fails

Chasing the *other* image reference is what found it. `secret-rsa-key-hook.yaml` registers four
`pre-install,pre-upgrade` objects, the last being a Job on **`bitnami/kubectl:latest`** that
creates the RSA key-pair secret, `backoffLimit: 3`. It runs *before* step 4 touches Polaris.

Two things compound. The Job sets **no `imagePullPolicy`** and the tag is `:latest`, so
Kubernetes defaults to `Always` — a live registry pull on every upgrade, node cache irrelevant.
And Bitnami retired its public Docker Hub catalog to `bitnamilegacy/` on 2025-08-28, leaving
community users a reduced set of hardened images under `latest` only; `bitnami/kubectl` went
away, came back, and upstream left its future availability unresolved
(bitnami/containers#86977).

The failure would be safe — nothing changed — but misleading: `ImagePullBackOff` on a Job named
`benchmarks-polaris-rsa-keygen`, which does not read as a Polaris problem. Hence the one-command
pre-check, and a `--no-hooks` fallback that is safe *only* because the Job self-skips when the
secret exists. Pinning the image is a separate task; changing the chart mid-upgrade is not.

## #38 — the file log handler is off, and two env vars configure it anyway

The diff shows `quarkus.log.file.enabled=false` **unchanged** between live and render, and no
`QUARKUS_LOG_FILE_ENABLED` variable exists to override it. So Quarkus writes no log file, while
`extraEnv` sets `QUARKUS_LOG_FILE_JSON_ENABLED=true` and `QUARKUS_LOG_FILE_JSON_PRETTY_PRINT=false`
to format a handler that is switched off.

That is the **third** instance of this pattern in one chart — after `logging.console.json`/
`format` being inert because the env var wins, and `topologySpreadConstraints` selecting a label
nothing carries. Three is no longer a coincidence; it is the repo's signature fault and worth
counting in one place.

Two consequences left as checks rather than conclusions: nothing writes
`/deployments/logs/polaris.log` even though the PVC is mounted there, and `#8`'s
interleaved-write hazard may be inert with it. **`#8` is not closed on this** — the PVC may hold
content from when file logging was on, and none of it speaks to the 1 → 3 scaling itself. It
also suggests `fb-polaris-shipper` may have been tailing an empty file all along, which is worth
knowing before assuming it ever delivered anything.

NOT VERIFIED: no cluster command from this session. Step 3's outputs are Kade's; `helm lint` was
not shown; the `#37` pre-check and the `#38` directory listing are both outstanding.

## The hook gate is green, and step 4's own ordering was wrong

`docker pull bitnami/kubectl:latest` → `Status: Image is up to date`, digest
`sha256:b29d8c1665b70817259ceecaea16ab27aab6368b48daf485d19436c809067492`. The registry serves
it, which is exactly what `imagePullPolicy: Always` needs, so step 4 runs with hooks.

**Captured that digest into `#37` as the known-good pin.** It cost nothing to record and it is
the thing the eventual fix should point at — taken while `:latest` still resolved to a working
image, which is the only window in which it is obtainable. `#37` stays open regardless: the
hook re-pulls on every future upgrade, so today's green says nothing about next month's.

**Checking the chart to write that up found a worse problem in step 4 than the one being
checked.** `deployment.yaml` emits `replicas:` only when `autoscaling.enabled` is false
(lines 31-32), and it is true here. So:

* `helm upgrade` does **not** set replicas — the deployment stays at the 0 that `2d` left.
* The HPA cannot lift it off 0 (established earlier today).
* **`kubectl rollout status` on a deployment with `spec.replicas: 0` reports "successfully
  rolled out" immediately**, with no pods and no image pull attempted.

Step 4 as written ran `helm upgrade` then `rollout status`, with "if the HPA has not restored
it, scale back up before waiting on the rollout" as a conditional afterthought underneath. Run
in that order it would have printed a successful rollout of 1.6.0 while nothing was running —
a false green of exactly the kind this repo keeps finding, and this one was in the runbook's
own happy path. Reordered so `scale --replicas=1` sits between the two, unconditionally.

Also noted while there: `#20`'s "a helm upgrade can change a ConfigMap without restarting the
pod, so restart it" caveat **does not apply to this upgrade** — the pod is created from zero and
reads the new ConfigMap by construction. It applies to any later values-only change made while
a pod is already running.

NOT VERIFIED: no cluster command from this session. The pull output is Kade's; step 4 has not
been run.

## Step 4 ran, and #8 fired within minutes

Confirmed from running objects: the loaded ConfigMap is the 1.6.0 one (plural
`event-listener.types` with `PT5S`/`1000`, every category INFO or OFF with no DEBUG,
`console.level=INFO`, `file.enabled=false`), and the metastore reads `version_value = 4`. `#35`
closes — as **never exercised**, not as survived.

Then the HPA:

```
benchmarks-polaris   cpu: 2%/80%   memory: 88%/80%   MINPODS 1  MAXPODS 3  REPLICAS 3
```

**`#8` has fired, and the arithmetic says it had to.** HPA memory utilisation is measured
against the **request** (`1Gi`), while `-XX:InitialRAMPercentage=50.0` sizes the initial heap
from the **limit** (`2Gi`) — so the JVM commits `1Gi`, the entire request, before serving one
API call, then adds metaspace, code cache, stacks and direct buffers. The 80% target is
exceeded **at idle**, which is why it scaled at `cpu: 2%`. And utilisation cannot fall below
80% of a `1Gi` request while a `1Gi` initial heap is held, so this does not come back down:
three pods is the steady state, and the HPA sits pegged at `maxReplicas` with its target still
unmet, carrying no headroom for a real load event. Filed as `#39` with the three fix options,
none applied — *Polaris is not to be changed*, and this needs its own plan.

Three things worth separating out:

* **`#8`'s prediction was right and its mechanism was wrong.** It called the scale-up; its
  hazard was three pods appending one `ReadWriteOnce` log file, and `#38` establishes the file
  handler is off, so there are no writes to interleave. What three pods actually costs is
  elsewhere.
* **`#15` hypothesis C is alive again**, six hours after step 0b killed it on a one-pod
  reading. The entry had even named the risk — "if a future ladder run pushes Polaris past the
  target, C comes back" — and got the trigger wrong: it was the JVM's startup footprint, not a
  ladder. Its recommended mitigation was never applied. Anything reading "hypothesis C is dead"
  is now stale, MEMORY.md included; fixed.
* **`replicaCount: 1` is in `values.yaml` and means nothing here**, since `deployment.yaml`
  emits `replicas:` only when autoscaling is off. Correct chart behaviour — but it is why
  "replicaCount is 1" must never be read as "there is one pod".

## The events reading was pre-upgrade, and step 5 asked the wrong question

`count(*), max(timestamp_ms)` returned `2528 | 1789574562296`. That timestamp is
**2026-09-16T16:02:42Z** — two days old, and it matches the 09-16 traffic window that verified
report schema v6. Polaris then sat at 0 replicas through the migration and nothing has called
it since the upgrade.

So the number proves the table survived and says **nothing** about whether the listener writes
on 1.6.0 — yet step 5 labelled it "the events table is still being written — the listener
survived the upgrade". A high-water mark from before the change cannot answer a question about
after it. Corrected: generate one API call, `sleep 10` for the `PT5S` buffer, then re-read and
require the count to **rise**. If it stays flat, the plural `event-listener.types` rename is
the first suspect, being the only listener config that moved.

Added a `restartCount` / `lastState.terminated.reason` check while there: max heap `1.33Gi`
inside a `2Gi` limit leaves ~`0.67Gi` for non-heap, and there are now three JVMs on one node.

NOT VERIFIED: no cluster command from this session. Step 5 is **partial** — the console-JSON
check, pod image and phase, restart counts, `/q/health`, the log-directory listing and the real
listener check are all still outstanding.

## The event listener works on 1.6.0 — the one assertion a flat count would have muddied

```
before:  2528 | 1789574562296  = 2026-09-16T16:02:42Z   (pre-upgrade high-water mark)
after:   2536 | 1789710542265  = 2026-09-18T05:49:02Z   (14:49 KST)
```

+8 rows and the timestamp moved to now. Worth being explicit about why this was the assertion
to get right: `polaris.event-listener.types` is a **renamed** key. The singular
`event-listener.type` this cluster ran under 1.3.0 has been deprecated since 1.5.0, and if
1.6.0 had ignored the plural form, the buffer settings would still be present and nothing would
be subscribed — `events` would stop growing with no error logged anywhere. That is the same
failure shape as the console-JSON risk: **quiet, not wrong.** It is also exactly the case the
earlier version of this check could not have distinguished, because it read a pre-upgrade
high-water mark and called it proof.

Also noted: 8 rows from a couple of calls, so the listener emits more than one event per
request and the count is not a request counter.

NOT VERIFIED: no cluster command from this session. Still outstanding from step 5 — the
console-JSON check, pod image/phase, restart counts, `/q/health`, and `#38`'s
`/deployments/logs/` listing.

## The last three checks: one clean pass, and two of my own claims refuted

**Console is still JSON.** Every line a JSON object with `timestamp`, `level`, `message`, `mdc`,
`hostName`. `QUARKUS_LOG_CONSOLE_JSON_ENABLED` survives the upgrade, so the tier-2 Lua and
report schema v6 keep parsing. That was the last silent-failure risk in the upgrade and it is
clear. (`threadName`/`threadId`/`ndc` are present at the source, as expected — `#30` trims them
in Fluent Bit FILTER 4, not upstream.)

**Both pods on `apache/polaris:1.6.0`, both `Running`. And `…-5vpmc` has `restartCount 3`.**
The reason was not captured — the jsonpath's `lastState.terminated.reason` field came back
empty — so the OOMKill question is open, and with max heap 1.33Gi inside a 2Gi limit it is the
first suspect.

### I was wrong about #39: it does scale back down

`kubectl logs` reported "Found 2 pods" and the pod list showed two. So `REPLICAS` went 3 → 2
within the hour, and the "it cannot come back down" argument was too strong. The mechanism I
missed: **ZGC uncommits unused heap by default**, so `InitialRAMPercentage` sizes the heap at
start without pinning the resident set there permanently. The memory metric is not monotonic.

What replaces the ratchet is not better, only different: the metric still tracks heap behaviour
rather than load, so the HPA **flaps** — up on warm-up, down after ZGC returns pages, at 2% CPU
throughout. For `#15` that is worse than a stuck maximum, because a ladder run can straddle a
scale event and hypothesis C is intermittently rather than continuously live.

### I was wrong about #38: the PVC is full of logs

Predicted an empty directory. Got an active `polaris.log` (9594 bytes, mtime **Sep 18 01:35**)
and ~130 rotated `polaris.log.<date>.N.gz` files back to **Aug 21**, 27 MB total. The file
handler has been writing for at least a month.

The mtimes do carry the forward-looking half: `polaris.log` last touched 01:35, the 1.6.0 pods
started 05:41, traffic at 05:47–05:49, nothing written. So the handler is off *now*, which
`file.enabled=false` predicts — the writing stopped today.

**And that produces a contradiction worth chasing.** The step 3 diff showed
`quarkus.log.file.enabled=false` in the **R5 ConfigMap as well as** the render, unchanged. Yet
the R5 pod was writing. `#20` explains it: a `helm upgrade` can change a ConfigMap without
restarting the pod, and Polaris reads `application.properties` only at start — so R5 likely
turned file logging off while the running pod carried on with the older config for days, until
`2d`'s scale-to-0 killed it. If so, **this upgrade did not disable file logging; it delivered a
change that had been sitting inert in the ConfigMap.** That is the repo's signature fault
arriving from the opposite direction: not config that never executed, but config that executed
only when something unrelated restarted the pod.

Two consequences I had stated backwards: `fb-polaris-shipper` has **not** been tailing an empty
file — it had real content until today. And `#8`'s log-interleave mechanism was **live for the
entire month it was filed as hypothetical**, which is what `#40` now asks about: rotation
suffixes reach `.14` against `maxBackupIndex: 5`, with clusters of same-size rotations minutes
apart. That is either inert rotation config or multiple writers, and one `zcat | grep hostName`
over a rotated file distinguishes them. Left explicitly unestablished — `#8`'s own 09-09 note
says the HPA had no metrics then and could not scale, which argues for one busy writer.

NOT VERIFIED: no cluster command from this session; all readings are Kade's. Outstanding: the
restart reason, `/q/health`, and `#38`'s two commands.
