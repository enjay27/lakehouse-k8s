# Active Infrastructure State

**Index, not the record.** Only what would be *false* the moment it goes stale lives here;
everything else is a link into [`.memory/`](.memory/README.md).

## Now — 2026-09-18 (Polaris 1.6.0 live; the log-file leg REMOVED; OpenSearch retention written, NOT applied)

**THE POLARIS LOG FILE LEG IS GONE (2026-09-18, done).** `fb-polaris-shipper` and VictoriaLogs uninstalled,
`polaris-shared-logs-pvc` deleted, Polaris mounts nothing — `logging/RUNBOOK-log-pvc-removal-2026-09-18.md` is a **record, not
a to-do**. Polaris writes no log file; stdout → DaemonSet → OpenSearch is the only path. Closed: `#8` (at the mount, not the
claim), `#38`, `#40` (**unanswered** — step 4 destroyed the evidence), `REVIEW-pipeline` P10. `logging/fb-values.yaml` and
`victoria-values.yaml` are history, bannered. **Step 3 carries its own output; steps 1/2/4 are Kade's report.**
**Unconfirmed: VictoriaLogs' own 50 Gi PVC in `logging`** — `helm uninstall` does not remove it (`kubectl -n logging get pvc`).

**OPENSEARCH RETENTION IS LIVE (2026-09-18).** Three ISM policies stored, five indices managed:
`polaris-logs-*` **3d**, `polaris-report-*` **30d (a rehearsal figure — that stream is the only record of successful reads;
do not carry it to production)**, `k8s-logs-*` **3d**. Verified by `GET _plugins/_ism/policies` and `_ism/explain`. The first
`--apply` succeeded and only its *reporting* crashed, which read as a failure for two rounds (`#44`). Deletion happens on the
ISM sweep (30–60 min), not on apply. Dev Tools equivalents: [`logging/opensearch/devtools-ism.console`](logging/opensearch/devtools-ism.console).

**Still open, and I had it wrong twice: `handoff task E is NOT subsumed`** — at 30d the 30 s-window `polaris-report-*` indices
survive thirty days, so deleting them is still a manual, by-name, destructive step (console file §D). Also open: VictoriaLogs'
**50 Gi** PVC in `logging`.

**Start here next session:** `.memory/active-issues.md` `#42` — the thread-field task is **DONE**, and `#42` carries both the
outcome and the four things that were never read. [`logging/HANDOFF-thread-fields-2026-09-18.md`](logging/HANDOFF-thread-fields-2026-09-18.md)
is now a **completed-task record**, not a to-do; read it for *why*, not *what next*. What 1.6.0 changed under the pipeline is in
its Context section. Docs index: [`logging/README.md`](logging/README.md).

**POLARIS 1.6.0 IS LIVE AND VERIFIED (2026-09-18).** Image `apache/polaris:1.6.0`, metastore **schema v4** (9 tables, 21
indexes), plural `event-listener.types` **working** (`events` 2528 → 2536, timestamp moved), **console still JSON** so tier-2
keeps parsing. `#35` closed — 1.3.0 never met v4, so that pairing is *untested, not survived*. Steps 0–5 done; step 1's
corrected name screen still to re-run before any ladder.

**`#42` DONE — `threadName`/`threadId` restored, ROLLED and VERIFIED (2026-09-18, pod 07:23:34Z).** step3 after traffic
**367/367 carry `message`, `threadName.keyword`, `threadId`; 0 carry `ndc`** — the inverse of `#30`. Values-only (Lua sha
unchanged), tier-2 `ok=367 errors=0`, Lua drop 57.5 % (policy unchanged). Cost accepted, **not measured** (+47 B/doc): the
before/after was **withdrawn** as undeliverable. **Query `threadName.keyword`, never bare.**

**`step12` + `step9` PASS (11/11, 42/42) — and they revealed NEITHER v6 template had ever been stored**, only ever in this repo
from 09-16 to 09-18 (`client_ip=text`; `report_type` at OpenSearch's default `ignore_above: 256`). **Indices created 09-17/09-18
keep pre-v6 mappings for life; from 09-19 both families are v6.** No data lost, no repo query changes shape (all use `.keyword`).
**Never read on this roll:** helm revision (expect 21), `step10`/`step11` — so `#32`/`#31`'s equalities were not re-established.
**`#43`:** step3's presence checks now self-arm (`huh` never set `FAIL`); `bash -n` only.

**Pipeline running:** `benchmarks-fluent-bit` policy v5 / **report schema 6** (`#32`): field `message`, trim before the one Lua
filter. **`WINDOW_SECONDS` is still 30** (1800 s is a *Lua* change — combining it with the above needs
`apply-lua.sh --no-restart` → step2 → `helm upgrade`, no restart between; prefer landing them separately). Readouts: `step10` +
`step11`, not Dev Tools copies. **ISM / retention: ours locally since 09-18 (`step13`), Monitoring team's in production.**

**`#41` is the live loose end:** a 1.6.0 pod crashed 3× at rollout — `Reason: Error`, exit 1, dead in **4 s**, **not** an
OOMKill. `kubectl logs <pod> --previous`, or the `k8s-logs-*` Dev Tools query in the runbook. **Perishable** — `#39` recycles
pods. **`#39`:** the HPA flaps on **memory at 2% CPU** (`0→1→3→2→1` in an hour; resting 1) because it measures against the `1Gi`
request while the JVM commits `1Gi` — so **`#15` hypothesis C is intermittently live: pin `replicaCount` before any ladder run**.
**`#38` and `#40` are CLOSED** by the leg removal above (`#40` unanswered). Still open: `#36`, `#37`, and a **plaintext
OpenSearch password in `fluent-bit/values.yaml`** against CLAUDE.md.

**PostgreSQL (2026-09-17):** `#15` create-namespace 500s are an NPE, not a settled read-after-write; `SELECT
pg_wal_replay_pause()` on the standbys settles it in one command. The primary-unavailable harness is **planned, not built**:
[`postgresql/HANDOFF-toxiproxy-failover-2026-09-17.md`](postgresql/HANDOFF-toxiproxy-failover-2026-09-17.md).

Detail for every `#n` above: [`.memory/active-issues.md`](.memory/active-issues.md) `#33`–`#44`. Do not re-summarise it here.

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
