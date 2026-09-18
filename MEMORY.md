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

**POLARIS 1.6.0 (2026-09-18): committed, NOTHING APPLIED.** Ordered steps:
[`polaris/RUNBOOK-upgrade-1.6.0.md`](polaris/RUNBOOK-upgrade-1.6.0.md) (supersedes the 09-17 handoff's ordering, `#33`).
**The metastore is at schema v4 (migrated 2026-09-18, read back as `version|4`, 9 tables) while the running Polaris is still
1.3.0** — a combination nothing has characterised, and upstream documents no behaviour for a server older than its schema.
**Step 3 next, then 4, promptly.** Check whether the HPA restored a 1.3.0 pod after `2d`'s scale-to-0 (`#8`) and whether it is
healthy — that reading is perishable, it disappears at step 4. Console is at **INFO** and emits **JSON**, live since R5 and not
readable off the values file. **Steps 0, 1 and 2 are DONE** (step 1's corrected screen still to re-run before the ladder).
Findings — `#5` refuted, the dead config is the JSON env var not the threshold, the inert topology selector, the schema-check
PASS and the two comments it missed — are in [`.memory/active-issues.md`](.memory/active-issues.md) `#33`/`#34`. Not here.

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
