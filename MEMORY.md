# Active Service Testing State

**Index, not the record.** Current state below; everything else is a link into
[`.memory/`](.memory/README.md). If you are picking this up cold, read the
handoff named in *Now* — it is standalone.

## Now — 2026-09-04

**Read [`log-coverage/PLAN-log-coverage.md`](log-coverage/PLAN-log-coverage.md) first — standalone.**

Handed over from `local-k8s` roadmap step 2: drive every Polaris API, then report what the
Fluent Bit → VictoriaLogs pipeline stored and what it discarded. **Built, not yet run** —
`log-coverage/polaris_log_coverage.ipynb` cells 0–10, new `src/vlogs.py` + `src/log_coverage.py`,
and `extra_headers` on `PolarisREST`/`IcebergREST` for per-call `Polaris-Request-Id`.

**MEASURED offline against the deployed Lua** (`fb-values.yaml` sha256 `b56c135b87d6281b…`,
under `luatex --luaonly`): **10 mutations produce no record at all** — 8 of the 43 driven
operations plus the fixture's `POST /v1/catalogs` and the token exchange. The source plan names
one (principals created invisibly, deleted visibly); the two it misses matter more —
**`POST /v1/principals/{p}/reset`, so a credential reset leaves no trace**, and both rename
endpoints, whose paths carry no `/namespaces/{ns}/tables` segment. Rule 5's drop was aimed at
the OAuth endpoint and its blast radius was never bounded to it.

The expected column is not a table anyone typed — `log_coverage.Policy` runs the filter out of
the values file, with **no Python re-implementation to fall back on**. 111 tests green under a
stand-in runner; **`pytest`/`black`/`isort` could not be run — no package index from Cowork.**

Still true from the API→SQL matrix, and it is the same endpoint twice over: **1 refused =
`reset_principal_credentials`, so admin is NOT a superset** — and that call is also one of the
ten this pipeline does not record. Detail in
[`HANDOFF-api-index-matrix.md`](diagnostics/api-sql-profile/HANDOFF-api-index-matrix.md).

**Open:** the notebook has never touched the cluster; whether `mdc.requestId` round-trips is
still `[assumed]`, and is cell 1's first question.

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
