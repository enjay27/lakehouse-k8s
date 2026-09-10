# Active Service Testing State

**Index, not the record.** Current state below; everything else is a link into
[`.memory/`](.memory/README.md). If you are picking this up cold, read the
handoff named in *Now* — it is standalone.

## Now — 2026-09-10 (session 9)

**EVERY API, EVERY REACHABLE STATUS — planned, not started.**
[`log-coverage/PLAN-api-status-matrix.md`](log-coverage/PLAN-api-status-matrix.md) is the
read; it needs sign-off before code. Measured: today's harness drives **40 of the 63**
operations the vendored specs name, and the 24 with no driver include every endpoint the
classifier has never seen (`/credentials`, `/plan`, `/tasks`, `/register`,
`/transactions/commit`) — so **Gate 6 of the schema-v3 guide has never had anything to find**.
The run targets **OpenSearch** (`polaris-report-*` / `polaris-logs-*`), not VictoriaLogs, in a
new `polaris_log_coverage_v2.ipynb`; v1 stays the run of record.

**BUILT AND UNRUN: `polaris_log_coverage_v2.ipynb` (43 cells), `src/os_report.py` (the
OpenSearch query layer, 52 tests) and `src/api_status_matrix.py` (the 286-cell grid + executor,
48 tests).** 100 tests, no cluster needed, all negative-tested. **The notebook has never been
executed** -- the first run tests the notebook as much as the pipeline. It writes two documents:
`doc-api-status-matrix-results.md` (this repo) and `REPORT-for-local-k8s.md` (the work list for
the pipeline repo). Wiring it found two harness bugs worth remembering: the happy sweep would
have **deleted its own fixture and rotated the runner's secret** mid-run (fixed by
`REBIND` + a `doomed_*` family), and `mdc.requestId` was missing from `STRING_FIELDS`, so the
correlation join would have matched nothing -- the same `.keyword` defect this repo had just
written up against the guide's Gate 5.

**REPORT SCHEMA v3 IS LIVE, and the two shippers now disagree.** `benchmarks-fluent-bit`
(DaemonSet → OpenSearch, helm rev 11, pod 00:55:24Z) runs `SCHEMA_VERSION 3`;
`fb-polaris-shipper` (Deployment → VictoriaLogs, pod 2026-09-07) still runs **2**. So the
oracle must be told WHICH pipeline it is measuring — `load_policy(FB_VALUES_PATH)` would hand
a v2 oracle to a v3 run. Preflight (`log-coverage/preflight_os_report.sh`, read-only) also
found: the access log DOES reach OpenSearch (884 records with `http_status`; 500/422/405 all
reachable, 304/406/419/429/502/503/504 absent across all 884), `min_record_time` is **already
mapped as text** in today's report index, and **55 report rows are unaccounted for** between
`_cat/indices` and the aggregation — settle that before driving anything.

## Then — 2026-09-07 (session 8)

**Read [`log-coverage/HANDOFF-500-coverage-2026-09-07.md`](log-coverage/HANDOFF-500-coverage-2026-09-07.md)
first if you are picking that up cold** — standalone. In one paragraph: the oracle reads schema
v2 and the drift that caused the gate abort cannot recur silently (`Policy.schema_version`
reads the deployed script; `merge_windows` derives summable fields from the row). **Every route
to a 500 is a closed one** — run `1788759324`, 157 calls: a broken storage endpoint is **422**,
a missing bucket **400**, a stale `entityVersion` **409**, all mapped by
`IcebergExceptionMapper`, so storage misconfiguration is a CLIENT error on this build. The only
500 seen here remains the PG-HA read-after-write signature, which cannot be provoked on demand;
§5c printed NOT PROVOKED, which is the contract working. Stack traces survive, 7 of 7, under
four `exception.*` names. **Still open:** nothing provokes an UNHANDLED exception — best
candidate is inducing PG replica lag (`pg_wal_replay_pause()`, a `local-k8s` action); if that is
not feasible, close it as *opportunistic and not repeatable*. Detail:
[`PLAN-log-coverage-v3.md`](log-coverage/PLAN-log-coverage-v3.md), `.memory/roadmap.md`.

**Fast-run settings are live and TEMPORARY** (`WINDOW_SECONDS` 30, `Interval_Sec` 5). **Revert
together** when the run of record is done — the api-status-matrix phase schedule depends on 30s
windows, so revert AFTER it, not before.

**Side task 2026-09-08 — the api-sql-profile workbooks have a Korean reading guide**
(`diagnostics/api-sql-profile/doc-api-sql-profile-guide-ko.md` + `-results-ko.md`;
figures recomputed by `_check_guide_figures.py`). `pytest` could not be run at all
that session — see `.memory/active-issues.md`.

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
