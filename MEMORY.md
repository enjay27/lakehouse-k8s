# Active Infrastructure State

**Index, not the record.** Only what would be *false* the moment it goes stale lives here;
everything else is a link into [`.memory/`](.memory/README.md).

## Now — 2026-09-18 (Polaris 1.6.0 APPLIED; HPA at 3 pods, step 5 partial)

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

**POLARIS 1.6.0 IS APPLIED (2026-09-18).** ConfigMap confirms plural `event-listener.types`, all categories INFO/OFF, console
INFO, `file.enabled=false`; metastore reads `version_value 4`. `#35` closed — 1.3.0 never ran against v4, so that pairing is
**untested, not survived**.

**`#8` FIRED: `REPLICAS 3` after step 4, then 2 within the hour.** It scales on **memory at `cpu: 2%`** — JVM heap behaviour,
not load: the HPA measures against the **1Gi request** while `-XX:InitialRAMPercentage=50` commits **1Gi** at start. It **flaps**
(ZGC uncommits), so replica count moves on its own; an earlier claim here that it sticks at 3 was wrong (`#39`). **`#15`
hypothesis C is therefore intermittently live — pin `replicaCount` / disable autoscaling before any ladder run**, or a run can
straddle a scale event. Fix options in `#39`; *Polaris is not to be changed*, so it needs its own plan.

**Console is still JSON** (verified from `kubectl logs`) and **the event listener works** (`events` 2528 → 2536, timestamp moved)
— so the plural `event-listener.types` key is read and the tier-2 pipeline keeps parsing. Those were the two silent-failure
risks; both are clear.

**`#38` REFUTED, and it matters.** `/deployments/logs/` is **not** empty: active `polaris.log` (mtime **01:35** today) plus ~130
rotated `.gz` back to **Aug 21**. The 1.6.0 pods started 05:41 and have written nothing, so the handler is off *now* — but it ran
for a month, probably because R5 turned it off in the ConfigMap while the pod kept the older config until `2d` killed it (`#20`).
So `#8`'s log-interleave mechanism was **live** the whole time it was filed as hypothetical. **New `#40`:** rotation suffixes
reach `.14` against `maxBackupIndex: 5`, with same-size bursts minutes apart — either inert config or multiple writers; one
`zcat | grep hostName` settles it.

**`#41`, NEW AND THE ONE LIVE LOOSE END:** `…-5vpmc` crashed **3×** at rollout — `Reason: Error`, **exit 1**, dead **4 s** after
start. **Not** an OOMKill (that is `OOMKilled`/137), so my memory-pressure guess was wrong. Four seconds is too fast for a JDBC
timeout, too slow for a rejected VM option — likeliest a start-up race between the three simultaneous pods against the metastore.
**Run `kubectl logs …-5vpmc --previous` before that pod is replaced** — `--previous` keeps only the last terminated container and
`#39`'s flapping recycles pods on its own. Replica sequence today: `0 → 1 → 3 → 2 → 1`; resting state is 1.
**`#38` settled:** the container has no `QUARKUS_LOG_FILE_ENABLED`, so the file handler is genuinely off and the two
`FILE_JSON` vars are inert; `#20` is now the only explanation left for the month of archive. Still open: `#36`, `#37`, `#40`
(no `zcat` in the image — `exec -- cat *.gz` out and decompress on the Mac), `/q/health` on 8182. Detail in
[`.memory/active-issues.md`](.memory/active-issues.md) `#33`–`#41`, not here.

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
