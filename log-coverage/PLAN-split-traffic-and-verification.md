# PLAN — split the run: `polaris-learning` makes traffic, `local-k8s` verifies

**Status: PROPOSED.** Plan-first; no code until sign-off.

Kade, 2026-09-10: *"Polaris project's notebook just makes traffic, and verification should be
the role of the local-k8s project."*

Agreed, and this session is the argument for it. Four of the five worst defects came from the
seam between the two repos, not from either side of it:

| defect | where the truth lived | where the code lived |
|---|---|---|
| the oracle was a schema version behind the filter | `local-k8s` ConfigMap | here |
| `window_start.keyword` does not exist | the OpenSearch index | here |
| Gate 7 needs `test-schema-v3.lua` | `local-k8s` | here |
| the gates are written against `GUIDE-schema-v3-testing.md` | `local-k8s` | here |

Each cost a whole run. Verification code that lives away from the thing it verifies drifts
**silently** — the failure mode is never an error, it is a gate that passes without looking.

---

## 1. The line, stated once

> **`polaris-learning` knows Polaris. `local-k8s` knows the pipeline. Neither needs to know the
> other's subject, and the manifest is the only thing that crosses.**

`polaris-learning` owns the API surface, the vendored spec, identities, fixtures, payload
shapes, and the 286-cell grid. It answers **"what does this build return?"**

`local-k8s` owns the Lua, the ConfigMap, the index templates, the mappings and the report
schema. It answers **"did the pipeline record what that traffic should have produced?"**

The manifest is a **contract, not a log.** It carries what was driven *and the claims the
pipeline is expected to satisfy* — so the verifier needs no Polaris knowledge at all. That is
the difference between a split that holds and one that grows a second seam.

---

## 2. Cell-by-cell: where the current 43 cells go

| cells | today | after |
|---|---|---|
| 0–1 | title, preflight header | **split** — each side gets its own |
| 2 | preflight: Polaris + OpenSearch + indices | **split.** Polaris reachability, realm, `require_not_prod` → traffic. OpenSearch ping, `_cat/indices`, mapping probes → verify |
| 3–4 | **Gate 7**, the Lua unit test | **verify.** It already needs a `local-k8s` checkout and a `lua5.4`; it is the one gate that never belonged here |
| 5–6 | the policy that is RUNNING, both shippers | **verify** |
| 7–8 | **Gate 0**, mappings, field-name resolution | **verify** |
| 9–10 | identities: admin, denied | **traffic** |
| 11–12 | fixture, election, the `doomed_` family | **traffic** |
| 13–14 | the grid, the dry run, `run_phase` | **traffic** |
| 15–30 | **phases B–I**, including the 500 ladder and cleanup | **traffic** — this is the whole point |
| 31–32 | collection: settle, correlate by request id | **verify** |
| 33–34 | the matrix | **split.** target vs actual vs verdict → traffic. `stored` / correlation → verify |
| 35–36 | **Gates 1–6** | **verify** |
| 37–38 | the schema's invariants | **verify** |
| 39–40 | findings + the two reports | **split**, see §5 |
| 41–42 | teardown | **traffic** |

Roughly: **21 code cells become ~11 traffic + ~12 verify.** The phases are untouched; they are
already a clean traffic block.

---

## 3. The manifest

`log-coverage/runs/matrix-<run>.json`, written by the traffic notebook's last cell, and
`runs/latest.json` symlinked to it. `src/run_manifest.py` already states the principle this
rests on and it holds one repo boundary further out:

> *the manifest carries **values** — what was driven, when, against what fixture. The live
> cluster carries **truth**. Never one without the other.*

```jsonc
{
  "manifest_version": 1,          // refuse an unknown MAJOR on read, loudly
  "run": "1789008899",
  "driven_at": "2026-09-10T02:58:00Z",
  "env": "local",
  "polaris": {"url": "...", "realm": "POLARIS", "version": "1.3.0"},
  "fixture": {"catalog": "...", "namespace": "...", "table": "...", "view": "..."},
  "identities": {"admin": "root", "runner": "mx_..._runner", "denied": "mx_..._denied"},
  "window_seconds": 30,           // OBSERVED from the deployed ConfigMap, not assumed
  "windows": {"first": "...Z", "last": "...Z", "distinct": 7},
  "phases": [{"name": "B", "start": "...Z", "end": "...Z", "straddled": false, "cells": 63}],
  "calls": [                      // one per cell, 286 of them
    {"request_id": "nb-1789008899-2001-loadTable-2", "op_id": "loadTable",
     "method": "GET", "path": "/api/catalog/v1/.../tables/probe_tbl",
     "api": "catalog", "target": 2, "status": 200, "principal": "runner",
     "phase": "B", "window": "2026-09-10T02:55:30Z", "issued_at": 1789008900.12,
     "response_bytes": 1733, "verdict": "covered"}
  ],
  "claims": [                     // WHAT THE PIPELINE MUST SHOW. The verifier needs no
                                  // Polaris knowledge to check these.
    {"claim": "last_write_bytes", "window": "...Z", "resource_kind": "table",
     "resource_hint": "probe_tbl", "equals": 1733,
     "because": "exactly one 2xx POST to that table in that window"},
    {"claim": "last_write_absent", "window": "...Z", "resource_hint": "mx_..._droponly",
     "because": "the only write in that window was a DELETE (204, empty)"},
    {"claim": "role_writes", "window": "...Z", "resource_hint": ".../catalog-roles/mx_..._crole",
     "equals": 3, "because": "three privileges granted, all 201"},
    {"claim": "auth_denied", "window": "...Z", "resource_hint": ".../catalog-roles/mx_..._crole",
     "at_least": 1, "because": "a 403 on that role in that window, no prior success"},
    {"claim": "errors_kept", "request_ids": ["..."], "because": "rule 3 keeps every 4xx"}
  ]
}
```

**Why `claims` rather than letting the verifier work it out.** Gates 2 and 4 are the two that
matter most and the two that need to know *what the traffic meant*: which commit was last, how
many privileges were granted, that a window's only write was a DELETE. Today the notebook knows
that because it did it. A verifier reconstructing it from `polaris-logs-*` would be
re-implementing Polaris semantics in the pipeline repo — a second seam, and the one most likely
to rot.

**Validation on read is not optional.** `manifest_version` mismatched, `windows.first` after
`windows.last`, a claim naming a window outside the run's range, an empty `calls` — each is a
loud refusal, not a warning. A verifier that runs against a half-written manifest reports
pipeline faults that are file faults.

---

## 4. What moves as code

| file | from | to | why |
|---|---|---|---|
| `src/os_report.py` (+ 59 tests) | here | `local-k8s` | it speaks to the index and to the report schema — neither is this repo's subject |
| the gate bodies (cells 4, 6, 8, 32, 36, 38) | notebook | `local-k8s`, as a module | gates belong beside the Lua they test, with their own `pytest` |
| `src/api_status_matrix.py` (+ 49 tests) | — | stays | the spec, the grid, the payloads: pure Polaris |
| `test_notebook_calls.py` | — | stays, retargeted | it checks the traffic notebook's calls |
| `src/log_coverage.py` | — | **stays, and is the awkward one** | see below |

**`log_coverage.py` is 127 KB and straddles the line.** `provokers_500`, `drive_500`,
`elect_drive_identity`, `call_once` are traffic; `check_invariants`, `merge_windows`,
`diff_reports`, `report_mismatches`, `summable_fields` are verification. Splitting it is a
bigger change than this plan, and doing it *inside* this plan would put two risky refactors in
one step. **Proposal: leave it here, and have the verifier own its own invariant code** — it is
the report schema's own rules, and `local-k8s` is where the schema is defined. The v1 notebook
keeps using `log_coverage` unchanged. Revisit once the split has run twice.

---

## 5. Two reports, and today's is conflating them

| finding | belongs to |
|---|---|
| `createNamespace` / `createView` answer **500** | **polaris-learning** — a fact about the build |
| `reportMetrics` answers 204 for a denied principal and for a missing table | polaris-learning |
| `getConfig` answers 200 unauthorised | polaris-learning |
| `planTableScan` / `fetchPlanningResult` / `cancelPlanning` / `fetchScanTasks` are not routed | polaris-learning |
| `/transactions/commit` has no `RESOURCE_PATTERNS` rule | **local-k8s** |
| `min_record_time` mapped as `text`; no index template | local-k8s |
| `writes=1` after three grants; `auth_denied=0` after a 403 | local-k8s |
| Gate 5 / Gate 2 filter on analysed fields as the guide writes them | local-k8s (the guide) |

`REPORT-for-local-k8s.md` currently mixes the first four in with the rest. After the split each
side writes only what it owns, which is most of the value of doing this at all.

---

## 6. What the split costs, and what pays for it

- **Two steps instead of one.** Mitigated by the manifest recording window bounds: the verifier
  settles on ingest itself and can run minutes or hours later, against a run it did not watch.
- **A new seam: the manifest format.** Real. Paid for by versioning it, validating on read, and
  keeping a golden manifest in `local-k8s`'s tests so a format change breaks there loudly.
- **`git log` no longer tells one story.** Two commits per finding, in two repos. Worth naming
  the run id in both.
- **What it buys:** a gate can no longer drift from the thing it tests without someone editing
  the same repo. Every defect in the table at the top of this plan becomes structurally
  impossible.

---

## 7. Migration, in order, each step independently committable

**Do not delete anything until the replacement reproduces its output.**

1. **Fix Gate 2 and Gate 4's diagnostics here, first.** Both currently print one number where
   they need to print the row: Gate 2 cannot tell "no table row" from "a row without the field",
   and Gate 4 reads `_mine[0]` without showing what else was in scope. Moving a blind gate just
   relocates the blindness. *(Small. Do it regardless of whether the rest is approved.)*
2. **Settle the `trace_verdict: absent` question.** All eight 500s report no application line,
   which rule 2 forbids — and v1 measured 7 of 7 traces present on 2026-09-07. One query decides
   whether that is a serious pipeline finding or `error_record_pair` looking in the wrong place.
   It must be answered before the code moves, or the answer moves with the ambiguity.
3. **Write the manifest here** (`src/matrix_manifest.py`, schema + validator + tests). The
   notebook gains one cell and loses nothing. Verification still runs in place.
4. **Stand the verifier up in `local-k8s`**, reading the manifest, and **prove equivalence**: it
   must reproduce run 1789008899's eleven verdicts exactly, from the same manifest and the same
   index. That is the gate on the whole plan.
5. **Only then** cut the verification cells out of the notebook here and rename it
   `polaris_api_traffic.ipynb`.
6. **Update both memory trees**, and `CLAUDE.md` here to say where verification lives now.

---

## 8. Blocker, and what I need

`local-k8s` **is not mounted in this session** — only `polaris-learning` is. Steps 4–6 need
either folder access to `~/hynix/local-k8s`, or a session started with both folders connected.
Steps 1–3 can proceed here today.

## 9. Sign-off

1. The line in §1 — traffic here, verification there, manifest between — as stated?
2. `claims` in the manifest, or should the verifier reconstruct intent from `polaris-logs-*`?
   (I recommend `claims`: the alternative re-implements Polaris semantics in the pipeline repo.)
3. `log_coverage.py` stays whole for now (§4)?
4. Verifier shape in `local-k8s`: a module + CLI under `logging/verify/`, with a thin notebook
   for reading — or a notebook only?
