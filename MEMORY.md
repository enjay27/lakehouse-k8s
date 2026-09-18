# Active Infrastructure State

**Index, not the record.** Only what would be *false* the moment it goes stale lives here;
everything else is a link into [`.memory/`](.memory/README.md).

## Now — 2026-09-18 (Polaris 1.6.0 live; thread fields ROLLED and VERIFIED; retention WRITTEN, not applied)

**THE POLARIS LOG PVC IS BEING REMOVED (2026-09-18, Kade).** `polaris/values.yaml` no longer mounts
`polaris-shared-logs-pvc` (`extraVolumes`/`extraVolumeMounts` now `[]`, the dead `QUARKUS_LOG_FILE_JSON_*` vars deleted,
`maxBackupIndex` 45 → **5** because with no PVC `logsDir` is the node's own disk). **The cluster still mounts it** — the
ordered teardown (shipper → VictoriaLogs → Polaris upgrade → PVC delete, with the finalizer trap) is
[`logging/RUNBOOK-log-pvc-removal-2026-09-18.md`](logging/RUNBOOK-log-pvc-removal-2026-09-18.md) and **step 3 is DONE** (2026-09-18: gate PASS with its positive control, applied, and the pod
confirms `ls /deployments/logs` → *No such file or directory* — the mount is gone from the running container, not merely
empty). **Polaris has released the claim; `fb-polaris-shipper` is the last mounter.** Steps 1, 2 and 4 have NOT run —
the shipper and VictoriaLogs are still installed and the PVC still exists with its 27 MB.
Step 4 destroys the 27 MB archive; Kade chose no copy. **`#8` is CLOSED as of step 3** (not step 4 — the hazard was the
mount, not the claim), and a never-fired duplicate-mountPath trap at `/deployments/logs` went with it. The OpenSearch tiers read stdout and are untouched.

**RETENTION IS WRITTEN AND NOTHING IS APPLIED (2026-09-18, `#44`).** ISM is **ours locally** now, not the Monitoring team's
(production still theirs): `logging/opensearch/ism-*.json` — `polaris-logs-*` 3d, `polaris-report-*` **30d (a rehearsal
figure: that stream is the only record of successful reads)**, `k8s-logs-*` 3d. Run `logging/scripts/step13-ism-apply.sh`
dry first; `--apply` also deletes the 30 s-window report indices. PVC side: **Quarkus has no age TTL** (`#44`) — which is
why the PVC is going instead. All of it inert while `logging.file.enabled: false` (`#38`).

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
**`#38`:** the file handler is off, so nothing writes the log PVC and **`fb-polaris-shipper` (still installed) now tails a dead
file**. Also open: `#36`, `#37`, `#40` (**`#44` answers its question 1: the bound is per-day**), and a **plaintext OpenSearch
password in `fluent-bit/values.yaml`** against CLAUDE.md.

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
