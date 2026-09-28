# 2026-09-29 — the log batch, built, installed and run on the cluster

First session on Kade's Mac rather than in Cowork, so `kubectl` / `helm` 4.1.4 / Docker 29.4 all
reached the cluster (context `orbstack`, Kubernetes 1.35.6). Everything the 09-28 handoff marked
"NEEDS KADE" was done here, in its order.

## Preconditions (01:48 KST, read-only)
- One Polaris pod, `54c794779c-q6pz6`, Running 25 h. Labels `instance`/`name` = `benchmarks-polaris`,
  `fsGroup` 10001, `runAsUser` 10000, claim `polaris-logs-pvc` — the batch chart's `polaris:` block
  matches. Polaris does **not** set `runAsGroup`; the batch sets 10001. Harmless: files land 10000:10001
  either way (setgid directory + fsGroup).
- Files named `polaris-benchmarks-polaris-*`; no `polaris-sizetest-*` being written, so step15's test
  settings are not live. No `movetest/`.
- No CronJob / Role / ConfigMap from `9ec82a4` (the batch inside the Polaris chart) — it was never applied.
- 40 batch tests green; `helm lint` + `--dry-run=client --debug` clean. Job pod labels carry
  `polaris-log-batch`, never Polaris's selector.

## The one change: memory limit 1Gi -> 2Gi
Before running anything on the PVC, copied its 17 files (130,393,487 bytes) into a scratchpad with
`kubectl exec … cat`, restored their mtimes from `stat -c %Y` in the pod (the quiet/deferred logic reads
mtime), and ran `polaris_log_batch.py --no-pod-list --dry-run` under `/usr/bin/time -l`:
**peak RSS 838 MB, 2.5 s**, 27 hours, invariant held on all 27, 0 malformed. 838 MB is 82 % of the
1Gi limit — an OOMKill on the first run was a live risk, driven entirely by step15's two ~64 MB files
(hour `20260927-23`, 18,872 lines, ~6.9 KB/line). Kade chose 2Gi. Steady-state hours are tiny; revisit
when sizing for production.

Measured on macOS with Python 3.12, the image runs 3.11-slim: comparable, not identical. The in-cluster
peak was not measured (the Job pod was gone before anything could sample it; no metrics-server check made).

## Build, install, manual run (01:51–01:52)
- `docker build -t polaris-log-batch:0.1.0` -> `6cbd52db993f`. `.dockerignore` kept the stray
  `__pycache__` out.
- `helm upgrade --install polaris-log-batch … -f charts/polaris-log-batch/values.yaml` -> revision 1.
  `auth can-i list pods` as the SA: **yes**. CronJob: `3 * * * *`, `Asia/Seoul`, limit 2Gi.
- `log-batch-manual-1`: **Complete in 9 s**. 27 `published` events, `20260927-22` .. `20260929-00`.
  **Every counted field identical to the local rehearsal** (lines_in, processed, dropped, malformed,
  access_*, errors_kept, distinct_*). `lines_in == processed + dropped + malformed` on all 27;
  `pod_list_error: null` on all 27.

| hour | lines_in | processed | dropped | malformed |
|---|---|---|---|---|
| 20260927-22 | 1,669 | 782 | 887 | 0 |
| 20260927-23 | 18,872 | 9,391 | 9,481 | 0 |
| 20260928-00 | 47 | 0 | 47 | 0 |
| 20260928-01 .. 20260929-00 | 0 | 0 | 0 | 0 (24 empty hours, published as empty files) |

PVC afterwards: `processed-logs/` 27 files (`20260927-23.jsonl` 124.5 MB / 9,391 lines),
`aggregated-logs/` 27, `malformed/` empty; the two `-22.gz` rolls and **14 orphan `.log` files** in
`done/20260927/` and `done/20260928/` (names `…log.<hour>.orphan`, including `2tklb` and step15's
two 64 MB files). Untouched as required: the live `q6pz6` file (reported under `idle_log_files`),
`legacy-shared/`, `sizetest/`. Checkpoint `last_published: 20260929-00`.

## First scheduled run
`polaris-log-batch-29843583`, pod started **2026-09-28T17:03:00Z = 02:03:00 KST** (the `timeZone` field
works), Complete in 4 s. Published **exactly one hour**, `20260929-01`: 0 lines (no traffic), `pod_list_error`
null, nothing moved, `q6pz6` reported idle (last line `20260928-00`). Checkpoint `last_published: 20260929-01`,
28 files in `processed-logs/`. Handoff step 4 passes.

## Not done
- Step 5 of the handoff (step16 Lua parity on real per-pod files). The only real hours on disk are the
  step15 load test's; the next real traffic is a better input.
- Parallel run against Fluent Bit tiers 2/3 and the count reconciliation.
- `processed-logs/20260927-23.jsonl` is 124.5 MB of step15 load on a 5Gi PVC. Retention is by mtime
  (SPEC §보존): the outputs go ~2026-10-02 01:52 KST (3 days after publication), but the moved raw files
  in `done/` keep their **original** mtime, so `done/20260927/` goes ~09-30 23:20 — 1.9 days after
  publication, not the 3 PLAN D5 says. The SPEC documents this; PLAN D5's wording is the looser one.

## Test phase: every 2 minutes (release rev 2, 02:12)
Kade asked for the Job to run every 2 minutes during testing. The script's unit is the closed KST hour
(`HOUR`, `last_ready = floor_hour(now - grace) - 1h`), so a schedule change alone does not give output
every 2 minutes — asked; Kade chose **schedule only** over making the window configurable (a code change
whose test output would no longer match the hourly production contract). Values: `*/2 * * * *`,
`activeDeadlineSeconds` 3000 -> 110 (a run must end before the next start; runs take 4–9 s),
`startingDeadlineSeconds` 600 -> 60. Read back from the running CronJob. Production values are kept in a
comment in `values.yaml`: restore them when the test phase ends.
Verified: `polaris-log-batch-29843594` started 02:14:00 KST and `-29843596` 02:16:00 KST, Complete in 4 s
and 5 s. **An idle run prints nothing** (hour `20260929-02` is not ready until 03:01) — an empty Job log
with status Complete is the normal case in this phase, not a fault.

## Handoff step 5 — parity on real traffic (02:17–02:40)
Traffic, local only (`run_traffic.py --env local`): `smoke` run `1790615875` (27 calls, 25 covered; the
`deleteCatalog -> 400` is the known undroppable fixture catalog) then `full` run `1790615924` (327 calls,
278 covered, 8 windows 02:19:00–02:22:30 KST; 7 responses of 500). All inside hour `20260929-02`.

**A late roll of an already-published hour.** The first write after 26 idle hours (02:17) rolled the pod's
09-28 00:17 startup lines into `q6pz6.log.2026-09-28-00.gz` — an hour published at 01:52 from the `.log`.
Not double-counted: its lines are timestamped hour 00 and hour 02 selects by timestamp. Not leaked:
`housekeep_after` moves every roll named <= the hour just published, so it goes to `done/20260928/` with
hour 02. (Checked in code; the real move is still to be seen on the PVC.)

**Simulated the 03:02 run instead of waiting (Kade's call).** Copied the live `.log`, the late `.gz` and
the real `.state/checkpoint.json` (`last_published 20260929-01`) out with mtimes restored, ran
`--dry-run --no-pod-list --now 2026-09-29T03:02:00+09:00`: exactly one hour, `20260929-02` — 1,012 in /
495 processed / 517 dropped / 0 malformed, invariant holds, `errors_5xx` 7 (= the 7 driven 500s),
83 resources, 5 principals, peak RSS 35 MB.

**step16 parity on those files: 22 diffs, every one the documented kind (SPEC §9.1).** 7 error requests
that precede their resource's first success in the hour — 2 × GET 404 on `apimatrix1790615875_cat`,
2 × GET 404 on `apimatrix1790615924_cat`, 3 × POST 500 on `bh_ns/tables` — sit in `__errors__` in the Lua
and in the resource row in the batch. Exactly conserved: +7 requests / +1,068 bytes on the resource rows,
−7 / −1,068 on `__errors__`, and the same for reads, writes, 4xx, 5xx. Errors *after* a success (DELETE 400,
401, 403) agree. **Every summary counter identical.** Synthetic seed 7 identical in the same run.

Wrong turns:
- `P="kubectl … --"; $P cat …` — zsh does not word-split, the same trap the cleanup session recorded.
  Write the command out.
- **lupa 2.8 on macOS arm64 ships lua51–lua55 but no `luajit21`**, so step16 cannot run on the Mac.
  Ran it unchanged in `docker run --rm --platform linux/amd64 python:3.11-slim` with the repo mounted
  read-only, where `lupa.luajit21` imports. Swapping in `lua51` would have tested a runtime Fluent Bit
  does not use.

Still open: the real 03:02 publish (compare it to the simulation above); the in-cluster memory peak.
