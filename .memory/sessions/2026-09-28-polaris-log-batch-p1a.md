# 2026-09-28 — the batch job, P1a (framework, passthrough policy)

What was built: `charts/polaris/files/log-batch/polaris_log_batch.py` (stdlib only; Python 3.10 in the
Cowork VM, 3.11 in the job image) and `tests/test_polaris_log_batch.py` (26 tests, all green in the VM).

## The design as Kade settled it (same day, in order)
1. One file per pod — measured, `#48`.
2. Select lines by `timestamp` in `[H, H+1)` from every pod's rolls AND current `.log`; no sort.
3. Orphaned `.log` files move to `done/` after their hour is published.
4. Orphan = the pod is gone from the Kubernetes API (CronJob lists pods, read-only Role) AND the
   file is complete. I kept the completeness half: the pod list alone misreads a pod started between the
   API call and the scan.

## Decisions made while building, not asked
- Candidates for H: files with mtime ≥ H:00. A file last written before H cannot hold an H line.
- First run (no checkpoint) starts at the earliest valid line on disk, by a full read. The first
  version used roll names and a test caught it: a roll of 11 can open with a 10:59:59.9 line.
- A malformed line is booked to the hour of the nearest valid line before it in the same file, so it
  lands in exactly one hour's `malformed/` file.
- An empty hour is published as an empty file with a zero summary — "done, nothing" is distinguishable
  from "not done".
- Corrupt `.gz`: defer while < 120 s old, quarantine after (the plan said "retry 3 runs"; no state needed).
- `event_id` = sha1 of the raw line; `log_hour` added to every processed line.

## Housekeeping in the mount
isort cannot format in place on this mount (it writes `<file>.isorted` and cannot delete it); formatted
a copy and wrote it back. The two `.isorted` leftovers and a pytest `__pycache__` from the chart dir are in
`_to_delete/` (gitignored) for Kade to remove. Run pytest with `PYTHONDONTWRITEBYTECODE=1` so no
`__pycache__` lands inside `charts/polaris/files/`, which Helm would package.

## Not done
Full suite not run (the VM lacks pandas etc.); only this module's tests. No CronJob, Role or ConfigMap
yet (P3). Policy port (P1b).

## P1b — the Lua policy, same day
`AuditPolicy` ports `polaris_access_log.lua` (policy v5). Batch-driven changes, all written down in
`logging/SPEC-polaris-log-batch.ko.md` §9.1 as report schema 7: one KST hour for all pods (`pods`
replaces `hostname`/`report_seq`; no `windows_skipped`/`partial_window`/`held_pending`); the request-id
pair is found by looking ±30 s (so it crosses the hour); an error request joins its resource row if
the resource succeeded anywhere in the hour (the Lua could only see the rows existing at that instant);
evaluation in timestamp order.

Parity: `logging/scripts/step16-batch-lua-parity.py` loads the real Lua in LuaJIT (`pip install lupa`)
and feeds both sides the same records. First run: 8 diffs, all one bug of mine -- principal rows
carried `last_*_bytes`, which the Lua only puts on resource rows. After the fix: identical on seeds
7, 1, 2, 3, 11 (~5,300 lines each). Sensitivity: a first "break rule 4" probe showed 0 diffs because
rule 7 keeps a DELETE anyway -- the probe was wrong, not the harness; breaking rule 6 (HEAD) produced
the expected diffs. Asserts in the job became explicit raises (python -O strips asserts).
