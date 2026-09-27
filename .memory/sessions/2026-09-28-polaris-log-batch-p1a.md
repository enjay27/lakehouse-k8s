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
