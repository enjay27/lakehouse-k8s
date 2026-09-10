# Active Service Testing State

**Index, not the record.** Current state below; everything else is a link into
[`.memory/`](.memory/README.md). If you are picking this up cold, read the
handoff named in *Now* — it is standalone.

## Now — 2026-09-10 (session 11)

**THE GRID DECISION IS LANDED: it malforms by WRONG TYPE where it cannot malform by omission,
so the denominator stays 286.** `Operation.malform` is decided at parse time; omission is tried
FIRST, so the **16** cells that could always be malformed send a byte-identical body to every
previous run and stay comparable, and only the **11** that were driving *successful* calls change
shape. Split **16 omit / 11 wrong-type / 0 unbreakable**; `unmalformable_cells()` is now empty.

**But it is 10 verified, 1 UNVERIFIABLE — never quote 11.** `planTableScan`'s 400 cell cannot be
seen: `{"case-sensitive":"not-a-boolean"}` and `{}` return byte-identical 53-entry violation lists
with **no `request` entry at all**, because Prism's response generation for that operation fails
first. **The instrument is blind on one of the cells the fix was for, and blind toward green** —
the same blind spot that made the original count wrong. `.memory/active-issues.md`.

**`pytest` AND PRISM NOW RUN IN A COWORK SESSION.** The Linux VM has egress (pypi/npm/github all
200) and `uv`/`node`/`npx`; `black` is **26.5.1**, the exact pin. Gate: **960 passed, 45 skipped**
under real `pytest`, agreeing with Kade's macOS **1005 passed**. Build the venv OUTSIDE the mount
(`UV_PROJECT_ENVIRONMENT=$HOME/venv-linux`) or `uv sync` destroys the macOS `.venv`. The stand-in
is retired. **The cluster is still unreachable** — the OrbStack node IP is *Network is
unreachable* from the VM — so handoff steps 0-1 stay Kade's. A 403 from a Polaris URL was the
**egress allowlist**, not Polaris.

**`index.lock`: the mount refuses `unlink` but allows `rename`.** `mv .git/index.lock .git/_stale/`
works where `rm` does not, and every git write leaves a fresh lock, so clear before each command.
**Never `GIT_INDEX_FILE`** — it commits against a stale index and records new files as deleted.

**THE WORK IS SPLIT IN TWO, AND THE NEXT SESSION STARTS FROM
[`log-coverage/HANDOFF-split-logging-test-2026-09-10.md`](log-coverage/HANDOFF-split-logging-test-2026-09-10.md)**
— standalone; steps 3-4 need BOTH folders connected. Step 2 is DONE. Traffic runs from this repo
alone: `log-coverage/run_traffic.py --dry-run` / `--spec-check` (Prism, **`--errors` is not
optional** or the check is VOID) / `--profile smoke` (drives, and MUTATES).

**Still true from session 9:** the matrix harness report schema **v3 is on the DaemonSet and v2 on
the Deployment**, so the oracle must be told which pipeline it measures; `min_record_time` is
mapped **text** and only an index template fixes it.

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
