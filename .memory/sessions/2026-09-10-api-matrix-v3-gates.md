# 2026-09-10 — the API matrix run, and what it actually proved

Inputs: `REPORT-for-local-k8s.md` and `doc-api-status-matrix-results.md`, both produced by
`log-coverage/polaris_log_coverage_v2.ipynb` run `1789026666` (2026-09-10 07:54Z, schema v3,
30s windows). No cluster reach from this session — everything below is read off those two
documents and off the repo.

## What was different about this run

63 operations driven from the **vendored OpenAPI documents**, 286 (operation × status) cells.
Every previous run drove a hand-picked path set. That single change is what produced the
findings: Gate 6 can only report an endpoint unclassified if something called it, and nothing
ever had.

## The report's own list, re-read

The handoff listed five FAILs and two VOIDs. Sorting them by **whose fault they are** matters more
than the count:

| item | reads as | actually |
|---|---|---|
| Gate 6, 1 path with no rule | filter gap | **real.** One rule missing, added. |
| index mapping `text` | environment | **real.** Predicted by review #2, now measured. |
| four 500s | Polaris bug | **real**, and useful — `errors_5xx` on demand. |
| Gate 5 term filter | doc bug | **real**, and it is a CLASS, not a line (below). |
| Gate 4 `writes=1 granted=3` | filter fault | **probably the query.** Per-window row vs run-total count. |
| Gate 4 `auth_denied=0` | exemption broken | **probably the query.** Read off zero-carry rows. |
| Gate 2 VOID | plumbing | **the most important item in the run**, and it was listed last. |

## The wrong turn worth recording

The first read of `auth_denied=0` was "the `ROLE_KINDS` exemption is not working" — which is what
the report says, and what the guide's own failure mode invites. Reading the Lua says otherwise: a
403 on a `catalog-role` key that is not yet known forces `create=true` under `REPORT_MAX_ROLE_KEYS`,
and `logging/scripts/test-schema-v3.lua` pins exactly that case ("denied grant keeps its role row",
`role_keys_forced` = 1). What the gate actually does is `sort @timestamp desc, size 20` — and
**zero-carry rows make the newest documents for a key its zeros**. The window that carried the 403
is further down the list.

So the gate could not have seen the denial even if everything worked. The decisive field is
`role_keys_forced` **on the summary of the window you drove into**, which the gate never reads. That
is now in the guide.

The general form is already in this repo twice ("match by `window_start`, never by position";
"absence is not zero"). It reappeared as a *third* instrument reading correctly while idle.

## The class-level defect in the guide

The report caught Gate 5's `{"term": {"resource": "__errors__"}}` matching the token `errors`. It is
not one line. On dynamic-mapped `text`:

- Gate 2: `{"term": {"http_method": "POST"}}` → `post`. **Uppercase can never match.**
- Gate 4: `{"term": {"resource_kind": "catalog-role"}}` → `catalog`, `role`. Never matches.
- Gate 6: `{"term": {"resource_kind": "other"}}` → works, **by luck of being one lowercase token**.

Three gates that cannot match, one that passes by accident. The notebook has clearly diverged from
the guide already — Gate 5 returned `requests=63 over 4 docs`, which the guide's own query cannot
do — so the guide is the stale artifact and anyone following it literally gets false passes.

## Gate 2 is the headline and was buried

`last_write_bytes` **is** v3. Gates 1, 3, 4, 5 all test machinery that worked in v2. The run reports
Gate 2 VOID with "2 table rows in the window and NONE carries `last_write_bytes`" — which is the
expected reading of a window whose table rows are carried zeros, and the matrix did drive
`createTable`, `updateTable` and `commitTransaction` to 2xx.

Verified from the other end instead: the Lua was extracted from `fluent-bit/values.yaml` and run
under `lua5.4`, **58/58 assertions PASS**, including `table last_write == the commit` (5140) and
`last_read == the LAST get` (5203). So the filter sets the field. The gate needs to name the window
the commit landed in and filter `requests > 0`.

**v3 stays unproven until that gate passes once.**

## Changes made here

- `fluent-bit/values.yaml` — `{ kind = "transaction", pattern = "^.-/transactions/commit$" }`. The
  span is the whole path either way, so the **row key does not change**; only `resource_kind` moves
  off `other`. New value in an existing field, so `SCHEMA_VERSION` stays 3.
- `fluent-bit/values.yaml` — `min/max_record_time` omitted when nil instead of `""`.
- `logging/opensearch/polaris-report-template.json` + `logging/scripts/step9-report-index-template.sh`
  — the OpenSearch side of this platform was entirely unversioned, which is how the mapping drifted
  with nothing to review. **The two changes are one change**: with `date` mapping, a `""` is rejected
  per item inside a `_bulk` that returns HTTP 200.
- `logging/GUIDE-schema-v3-testing.md` — `.keyword` throughout, window pinning, `role_keys_forced`
  as Gate 4's direct evidence, Gate 2 told that carried rows are not evidence.
- `logging/scripts/test-schema-v3.lua` — 46 → **58** assertions.
- `logging/SCHEMA-report.md` — review #2 closed; `resource_kind` list corrected (`management` has
  not been a value since v3; `transaction` added).

## Not verified from here

`helm lint` and `--dry-run` were not run — no cluster reach from a Cowork session. The Lua test WAS
run for real, under `lua5.4` in the cloud container, against the values file as edited today. Both
new behaviours are **written and not rolled**: `#25`.
