# Active Infrastructure State

**Index, not the record.** Only what would be *false* the moment it goes stale lives here;
everything else is a link into [`.memory/`](.memory/README.md).

## Now — 2026-09-18 (Polaris 1.6.0 written, NOT applied; the cluster still runs 1.3.0)

**Start here next session:** [`logging/HANDOFF-pipeline-next-2026-09-16.md`](logging/HANDOFF-pipeline-next-2026-09-16.md) — state, rules, ordered tasks. Docs index: [`logging/README.md`](logging/README.md).

**Running:** `benchmarks-fluent-bit` pod `62klp`, policy v5 / **report schema 6** (`#32`): field `message`, trim before the one Lua
filter, tier-1 `Id_Key` output / self-log / parsers gone. Verified on traffic 16:02:30Z — counts equal to v5, detail 200/22/78,
report rows −31 % bytes. Query strings via `.keyword`. **`WINDOW_SECONDS` is still 30.**

**Rules:** Lua only → `apply-lua.sh`; values only → step2 → `helm upgrade` → step3; both → `apply-lua.sh --no-restart` → step2 →
`helm upgrade`, no restart between. Readouts: `step10` + `step11`, not Dev Tools copies.

**Next:** (1) 1800 s window (`apply-lua.sh`) → (2) delete 30 s report indices (explicit OK) → phase 3. P5 undecided; shipper: Kade uninstalls.
**ISM / retention: Monitoring team, not ours.** `#29` dropped.

**PostgreSQL (2026-09-17):** issue 1 first — `#15` create-namespace 500s are an NPE, not a settled read-after-write;
`SELECT pg_wal_replay_pause()` on the standbys settles it in one command. The primary-unavailable harness is **planned, not built**:
[`postgresql/HANDOFF-toxiproxy-failover-2026-09-17.md`](postgresql/HANDOFF-toxiproxy-failover-2026-09-17.md).

**POLARIS 1.6.0 (2026-09-18): committed, NOTHING RUN.** Ordered steps:
[`polaris/RUNBOOK-upgrade-1.6.0.md`](polaris/RUNBOOK-upgrade-1.6.0.md) — supersedes the 09-17 handoff's ordering (`#33`).
Tag/Chart 1.6.0, plural `event-listener.types`, console **INFO** + all 13 DEBUG categories demoted. Not rendered, not applied —
**the running Polaris is 1.3.0 with DEBUG output; do not read the level off the file.** Step 0's capture still goes first (`#5`).
**STEP 0 COMPLETE (Kade ran it).** Metastore **v3**. **One Polaris pod** (HPA 1/3, idle 1% cpu) → **`#15` hypothesis C dead**,
**`#8` re-armed**. **`#5` RESOLVED — REFUTED:** the working tree matched live R5 on **all 210 keys** bar `afc88e2`'s 14, and
`--all` added nothing, so no chart default was in play; the DEBUG-console scare was one uncommitted edit already applied at R5.
`afc88e2`'s logging half reconciles the file, does **not** change the cluster → **the upgrade will not reduce `polaris-logs-*`
volume.** **The console emits JSON** (`QUARKUS_LOG_CONSOLE_JSON_ENABLED=true`, ordinal 300 > properties 250), so
`logging.console.json:false` + `format` are **inert** — that, not the threshold, is the real dead config, and the tier-2 Lua
depends on the env var. `topologySpreadConstraints` selects `name: polaris` → **0 pods, inert since install** (`#8`'s "spreading"
is not in effect). JVM: `-XX:+ZGenerational` safe on 1.6.0's **JDK 21** image, removed in JDK 25. **Next: step 1 entity-name
screen** — the only pre-flight that can still block.
Corrections: **1.6.0 needs schema v4, not v5** (the `events.catalog_id` ALTER is 1.7.0) and **v3→v4 is additive only**
(`postgresql/schema/migrate_v3_to_v4.sql` — transcribed; diff against the shipped file first). "`maxReplicas 3 → 1` already in
the tree" was **false** — `#8` still armed. New: **1.6.0 rejects entity names with dots/colons/backslashes — screen first**
(step 1). INFO gates categories, so `#15`/`#24` re-runs need the `--set` override in the `categories:` comment. 1.7.0:
`OPTIMIZED_SIBLING_CHECK` 403s every nested namespace (apache/polaris#5521) — 1.6.0 is clear.

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
