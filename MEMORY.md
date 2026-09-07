# Active Service Testing State

**Index, not the record.** Current state below; everything else is a link into
[`.memory/`](.memory/README.md). If you are picking this up cold, read the
handoff named in *Now* — it is standalone.

## Now — 2026-09-07 (session 8)

**Read [`log-coverage/HANDOFF-500-coverage-2026-09-07.md`](log-coverage/HANDOFF-500-coverage-2026-09-07.md)
first — standalone, written for a session starting cold.** Then
[`PLAN-log-coverage-schema-v2.md`](log-coverage/PLAN-log-coverage-schema-v2.md) and
[`PLAN-log-coverage-v3.md`](log-coverage/PLAN-log-coverage-v3.md).

**THE ORACLE READS SCHEMA v2, and the drift that caused the gate abort cannot recur silently.**
The filter shipped v2 while `SCHEMA_VERSION` stayed 1, and cell 0b printed eight "unexpected
fields" per stored row — correct rows rendered as pipeline drift, with nothing naming the cause.
`Policy.schema_version` now reads the deployed script and the gate compares the two.
**`merge_windows` no longer sums a hardcoded list**: it derives the summable fields from the row,
because the old list added `errors` and silently not `errors_4xx` **in the same row** — the third
instance of that shape here. `check_invariants` carries v2's cardinality rule, the error-split
inequalities and all six reconciled margins.

**COVERAGE: 500 ERROR RAN, AND EVERY ROUTE TO A 500 IS NOW A CLOSED ONE.** Run `1788759324`,
157 calls, clean linear run. All four rungs answered by a **4xx**: a broken storage endpoint is
**422** whether it is refused (`127.0.0.1:1`) or unresolvable (`.svc.invalid`), a missing bucket
is **400**, a stale `entityVersion` is **409**. `IcebergExceptionMapper` (50 records) catches and
maps them, so **storage misconfiguration is a CLIENT error on this build and never reaches
`errors_5xx`** — measured, not assumed. §5c printed NOT PROVOKED, which is the contract working.
**The only 500 anyone has seen here is still the PG-HA read-after-write signature**, which
cannot be provoked on demand. **Stack traces survive and are richer than recorded: 7 of 7, under
FOUR names** — `exception.exceptionType`, `.frames`, `.message`, `.refId` — and 48 records in the
run carried one, so traces accompany handled 4xx too.

**Fast-run settings still live and TEMPORARY** (sha `d58b9203a8304030`): `WINDOW_SECONDS` 30,
`Interval_Sec` 5. **Revert together** when the run of record is done.

**Next:** the blocker is that **nothing provokes an UNHANDLED exception**. Best candidate is
inducing PG replica lag on purpose (`pg_wal_replay_pause()` on a standby, then
`create_namespace`) — a `local-k8s` action, since it needs psql. If that is not feasible, close
the question honestly as *opportunistic and not repeatable* rather than leaving it open. Then the
run of record, then revert the fast-run settings.

**Gate: the oracle tests RUN FROM COWORK now — 115 passed, 0 skipped**, against the deployed
filter (`lua5.4` in the cloud container + `FB_VALUES_PATH` at a staged `fb-values.yaml`). 37 tests
that had never executed from this side found three real bugs on their first run. Device suite:
708 passed / 1 pre-existing `test_privilege_scan` drift.

## Where the detail is

| read | when |
|---|---|
| [`.memory/roadmap.md`](.memory/roadmap.md) | what is done, what is next |
| [`.memory/active-issues.md`](.memory/active-issues.md) | before trusting a number or a tool (13 open, 5 resolved-but-instructive) |
| [`.memory/environments.md`](.memory/environments.md) | **before running anything** — local / dev / prod, and what must never run where |
| [`.memory/repository-map.md`](.memory/repository-map.md) | looking for where something lives |
| [`.memory/goal.md`](.memory/goal.md) | the standing objective and structural model |
| [`.memory/sessions/`](.memory/sessions/) | why a decision was made, including the wrong turns |
| [`.memory/completed.md`](.memory/completed.md) | finished structural work |

Task-specific handoffs live beside the code they describe, in
`diagnostics/api-sql-profile/HANDOFF-*.md`. They are written for someone
starting cold and are the right first read for a task; this file is the right
first read for the *project*.

## Rules for keeping this file useful

- **This file stays under ~40 lines.** Growth belongs in `.memory/`, not here.
  It was 198 lines against its own 150-line limit once, and a tracking document
  nobody finishes reading tracks nothing.
- **Update *Now* every session**, even when the answer is "unchanged".
- **A finding with a number goes in `.memory/roadmap.md`; the story goes in
  `.memory/sessions/`.** The wrong turns do not survive summarising and are the
  part most likely to be repeated.
