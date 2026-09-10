# Active Service Testing State

**Index, not the record.** Current state below; everything else is a link into
[`.memory/`](.memory/README.md). If you are picking this up cold, read the
handoff named in *Now* — it is standalone.

## Now — 2026-09-10 (session 11)

**PRISM IS REMOVED. NOTHING NOW CHECKS A REQUEST WITHOUT DRIVING IT.** `--spec-check`,
`src/spec_check.py` and `test_spec_check.py` are gone: **65 of 286 cells (23%) were the mock
talking about the document, not about a request**, and `planTableScan` could not be judged by it
at all. Two tiers remain — `--dry-run` (builds 286, contacts nothing, prints the 400-cell split)
and `--profile` (drives, MUTATES). **`log-coverage/spec/` STAYS: it is the denominator.** Gone
with it: any request check without a cluster, and the per-API controls. `.memory/active-issues.md`.

**THE GRID MALFORMS BY WRONG TYPE where it cannot malform by omission** — **16 omit / 11
wrong-type / 0 unbreakable**, denominator still 286, and the 16 send byte-identical bodies to
every earlier run. **It is 10 verified, 1 UNVERIFIABLE — never quote 11:** `planTableScan`'s 400
cell cannot be seen, because Prism returned identical violation lists for a malformed and a valid
body, with no `request` entry at all.

**TWO THINGS COMMITTED IN `05616df` WERE WRONG AND ARE NOW FIXED.** `has_required_fields` had
**six tests at `7cb12c2` and zero after** — a test file rewritten rather than extended, with the
count stable at 58 both sides, so the suite stayed green. And `_typed_properties` crashes on a
schema with one combinator key (`list + tuple`), found by chasing a mutant that SURVIVED. **Diff
test NAMES, not counts, after any move. A surviving mutant is a finding.**

**`pytest` AND `black` RUN IN A COWORK SESSION NOW** — the Linux VM has egress; `black` is
**26.5.1**, the pin. Gate: **911 passed, 45 skipped** (960 − 62 + 13). Build the venv OUTSIDE the
mount (`UV_PROJECT_ENVIRONMENT=$HOME/venv-linux`) or `uv sync` destroys the macOS `.venv`.
**The cluster is NOT reachable** from the VM, so handoff steps 0-1 stay Kade's. A 403 from a
Polaris URL was the **egress allowlist**, not Polaris.

**FIRST EVER `drive()` RUN — `1789031469`, smoke, and it found a coverage figure that cannot
fail.** `_row_from` stamps `verdict: "covered"` unconditionally, bypassing `adjudicate`: six of
eight teardown rows contradicted their target (409/400/404) and all counted covered. **True
coverage 12/20, reported 18/20** — and the same helper builds the gate2/gate4 rows. **UNFIXED.**
Teardown also leaked: `apimatrix1789031469_cat` and `probe_ns` are still on the cluster.
`echo_ok` was 20/20 and `claims` is correctly empty for smoke.

**`index.lock`: `mv` works where `rm` does not** (delete permission was granted this session, so
`rm` works too). **Never `GIT_INDEX_FILE`** — it commits against a stale index.

**NEXT SESSION STARTS FROM
[`log-coverage/HANDOFF-split-logging-test-2026-09-10.md`](log-coverage/HANDOFF-split-logging-test-2026-09-10.md)**
— steps 3-4 need BOTH folders. Step 2 DONE. Report schema **v3 on the DaemonSet, v2 on the
Deployment**; `min_record_time` is mapped **text** and only an index template fixes it.

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
