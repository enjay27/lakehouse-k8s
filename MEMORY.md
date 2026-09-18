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

**`#8` FIRED: `REPLICAS 3`, on `memory: 88%/80%` at `cpu: 2%`.** Not load — the HPA measures memory against the **1Gi request**
while `-XX:InitialRAMPercentage=50` commits **1Gi** (50% of the 2Gi limit) before the first call, so the target is exceeded at
idle and **cannot fall back**. Three pods is the steady state until fixed (`#39`, with the options; *Polaris is not to be
changed* — needs its own plan). **`#15` hypothesis C is ALIVE again** — step 0b killed it on one pod this morning and `#39`
revived it: **pin `replicaCount` / disable autoscaling before any ladder run**, or it cannot separate C from A. `#8`'s predicted
mechanism (three pods, one log file) is **inert** — the file handler is off (`#38`). Watch `restartCount`: max heap 1.33Gi in a
2Gi limit, three JVMs on one node.

**Step 5 is PARTIAL. Outstanding, silent-failure first:** (1) console still emits **JSON** — if it reverted to text the tier-2
pipeline goes *quiet, not wrong*; (2) pod image/phase; (3) `restartCount`; (4) `/q/health` on **8182**; (5)
`ls /deployments/logs/` (`#38` predicts empty); (6) **the listener check — today's `events` reading was PRE-upgrade**
(`max(timestamp_ms)` = 2026-09-16T16:02:42Z, two days stale, because Polaris sat at 0 replicas). Needs traffic, then re-read.
Also open, no structural risk: `#36`, `#37` (hook pulls `bitnami/kubectl:latest` on **every** upgrade; known-good digest filed),
`#38`. Detail in [`.memory/active-issues.md`](.memory/active-issues.md) `#33`–`#39`, not here.

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
