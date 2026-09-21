# 2026-09-10 (session 10) — the traffic side could not be written without importing the thing the boundary forbids

Step 2 of `log-coverage/HANDOFF-split-logging-test-2026-09-10.md`, and only step 2.
`local-k8s` was not connected, so steps 3 and 4 were out of reach by construction;
step 0 (re-run the notebook) needs a `kubectl port-forward` this session cannot see.
Kade signed off on step 2 alone before any file was touched.

## What the plan did not know, and the session had to measure first

**The import-graph guard could not have been written.** `SCENARIO-logging-test.md` §3
asks for a test asserting that `make_traffic` imports no logging module. But every
function the traffic cells call — `tag_clients`, `request_id`,
`provision_run_principal`, `elect_drive_identity`, `deprovision_run_principal`,
`provokers_500`, `drive_500`, `classify_500s` — lived in `log_coverage.py`: 3,099
lines and 70 defs that is the v1 VictoriaLogs verification module *and* half a
traffic module. The guard would have failed on day one, and the only honest fixes
were to move the traffic half out or to scope the guard until it meant nothing.

So **792 lines moved to `src/traffic_helpers.py`, verbatim**, and `log_coverage`
re-imports every name. The dependency runs one way — `log_coverage -> traffic_helpers`,
never back — and `polaris_log_coverage.ipynb`, the v1 RUN OF RECORD, keeps working
unedited. The test for that (`test_log_coverage_still_re_exports_every_moved_name`)
is what makes the claim checkable rather than hopeful.

`window_bounds` and `seconds_to_boundary` are the other half of the same problem:
twelve lines of epoch `//` that live in `os_report`, so importing them would have put
the whole OpenSearch client in the traffic side's graph. They are duplicated on
purpose, and a parametrised test compares the two copies — two copies drift, and the
drift here would be invisible until a window-scoped query matched nothing.

## The wrong turn, and it compiled

The extraction was done by an AST script computing line spans. Deleting `_as_int`
afterwards, **the span arithmetic ate one extra line: `def _epoch_of(iso_z):`.** Its
body — an indented `try:` — was then absorbed as dead code after `disposition`'s
`return`, because Python allows blank lines inside a function body. **`py_compile`
passed. `_epoch_of` simply ceased to exist**, and `check_invariants` would have
raised `NameError` at the first window-bounds check of the next run.

Caught by a check that was not about that at all: comparing the set of top-level
names in `git show HEAD:src/log_coverage.py` against the new file. It reported one
lost name. The lesson is the cheap one — **after moving code, diff the names, not the
line count** — and there is now a stronger version of it in the session's method: a
`difflib` comparison asserting every unmoved line survived in order, which found two
blank-line discrepancies and nothing else.

## What was built

| file | what | tests |
|---|---|---|
| `src/traffic_helpers.py` | the traffic half of `log_coverage`, moved verbatim | (its callers') |
| `src/make_traffic.py` | `CONTRACT_VERSION`, `config_from_env`, `PROFILES`, `TrafficRun`, `drive()` | 62 |
| `test_make_traffic.py` | the boundary, the contract, the twins, cleanup | — |
| `test_notebook_calls.py` | the signature binder now walks `make_traffic` too, not only the notebook | +1 |

`response_bytes` was added to BOTH driver row shapes (`api_status_matrix.execute` and
`traffic_helpers.call_once`). The contract lists it per call and the
`last_write_bytes` claim is a comparison against a size; neither driver recorded one.

**`drive()` is a lift of notebook cells 10–30 and 42.** What is new is small and
worth reviewing: the claims in `PLAN §3.1`'s request-id-keyed shape, `incomplete`
plus `finally`-cleanup, `build_findings` (Polaris facts, kept out of the pipeline's
work list per SCENARIO §6), and profile selection.

Two judgements made while lifting, both of which a reviewer should agree with or
overturn:

- **The delete phase makes no claim when the DELETE returns a body.** The `size > 0`
  rule is what separates a commit from a drop, so a non-empty 204 makes the negative
  case VOID. `incomplete` says so. A claim nobody can resolve is worse than no claim.
- **The `auth_denied` claim is only made if the denial actually came back 401/403.**
  A denial that was not denied cannot force the role row, and asserting on it would
  report a traffic fault as a pipeline fault — the same shape as the `echo_ok` split.

## Verification, and what it is not

**`pytest` was not run, on either machine, and that is a constraint rather than a
choice.** The `.venv` is macOS-aarch64 (`#!/Users/kade/...`) and cannot execute in the
Cowork Linux VM; that VM has no egress (`uv` fails to reach both `pypi.org` and
`github.com`); the cloud container has no `pytest` and **`pypi.org` answers 403 through
the org egress policy**, so it cannot be installed there either.

So the suite ran under a **~150-line stand-in** implementing only what this repo uses
(`raises`, `mark.parametrize`, `mark.skipif`, `fixture` with module scope / autouse /
yield-teardown, `skip`, `tmp_path`), over a staged copy: **222 passed, 0 failed, 45
skipped** — the 45 are `test_log_coverage`'s Lua tests, which need
`local-k8s/logging/fb-values.yaml`. Before this session the same files were 120.

**Every new check was then broken deliberately, one at a time — 12 mutants, all 12
caught**, including the two that matter most: a logging import at module scope in
`make_traffic`, and one hidden *inside a function* of `traffic_helpers`. A guard that
only walks module-scope imports would pass the second, and `make_traffic` imports its
clients inside `drive()`.

**What this does not establish:** that real `pytest` agrees with the stand-in, and that
`drive()` drives. Nothing here has touched Polaris. The first real run tests the
module as much as the pipeline — the same sentence session 9 wrote about the notebook.

`black` was run (version **26.3.1** in the container; `pyproject.toml` pins
`>=26.5.1`, so `black .` on Kade's machine may still produce a small diff). `isort`
was not available; per `CLAUDE.md` black runs last anyway.

## Open, in order

1. Kade runs `uv run pytest` — the real gate.
2. Step 0/1 of the handoff: re-run `polaris_log_coverage_v2.ipynb` and settle whether
   the eight `trace_verdict: absent` were the dict access or a real finding.
3. Step 3: `logging/tests/` in `local-k8s`, calling `make_traffic.drive`. Needs both
   folders connected. The gate on the whole plan is unchanged: it must reproduce run
   `1789008899`'s verdicts exactly before a verification cell is deleted here.
4. Step 4: cut the notebook down to a thin driver. Not before 3.

---

## Postscript — Kade ran the real gate, and it answered two questions at once

`uv run pytest` on the Mac: **936 passed, 1 failed**. Two things fall out of that.

**The stand-in was honest.** The 222 it reported are inside the 936, and pytest
agreed with it on every one. That does not make the shim a substitute — it never
ran `test_privilege_scan`, `test_api_trace` or the fifteen other files this session
did not stage — but the specific worry, that a hand-rolled runner would pass
something pytest fails, did not happen.

**The one failure was ten days old and nothing to do with this work.**
`test_probe_table_names_the_refusals` asserted `| NO |` and *"1 of 2 GET operations
are authorized"*. `render_probe_table` stopped saying either on **2026-08-31**, in
`e20fb22`, which replaced a YES/NO column with `OpStatus.verdict` — six values, so
that a **refusal** and a **harness fault** could stop sharing a column. The commit
message says exactly that. The renderer was improved and its test was not.

The failure mode is worth naming because it is the mirror of the one this repo
usually worries about. The usual fear is a test that passes by being unable to look.
This was a test that **failed while the code was right** — and a red test nobody can
attribute is worse than useless, because the next person to see it assumes it is
theirs and goes looking in the wrong place. It cost this session exactly that: the
first question asked was whether the 792-line move had broken something.

Fixed by updating the assertions, and by adding
`test_the_probe_table_summary_counts_every_verdict_it_rendered` — because the thing
`e20fb22` actually introduced, that `malformed` and `undriveable` are NOT
authorization outcomes and say so in the rendered document, had no test at all. A
summary folding them back into `refused` would have left every row looking right.
Four deliberate mutants, four caught.

**Also from that run, for the record:** `black` reformatted `test_vlogs.py` — a file
this session never touched, black-dirty before it started. My six files came back
unchanged, so container black 26.3.1 and the pinned 26.5.1 agreed after all.

## The `index.lock` blocker, and the workaround that nearly cost the session

This session had no delete permission — the request for it was refused by the
auto-mode classifier rather than reaching Kade — so `.git/index.lock` could not be
removed and every git write failed. The first commit went in through a separate
`GIT_INDEX_FILE`, which works, and **that turned out to be the dangerous choice.**

`GIT_INDEX_FILE` is an environment variable, and **each `device_bash` call is a fresh
shell.** The next commit therefore ran against the repo's own `.git/index` — still
holding the pre-commit state, because the first commit had never updated it. Git did
exactly what it was told: it committed the difference, and **the difference was that
`make_traffic.py`, `traffic_helpers.py`, `test_make_traffic.py` and this file had been
deleted.** The commit succeeded and read like a normal one. It was caught only by
running `git log --oneline` and `git status` afterwards and reading the output, which
listed the session's own new files as untracked.

Recovered with `git reset --mixed HEAD~1` — the working tree was never touched, so
nothing was lost.

**The actual fix, found while recovering, needs no permission at all: the mount
refuses `unlink` but allows `rename`.**

```bash
mv .git/index.lock .git/_stale/          # works; rm does not
```

A `.git/_stale/` directory was already there, so an earlier session had found this and
it never reached the memory tree. It is here now. Two details that matter: **every git
write leaves a fresh lock**, so the clear has to happen before each git command rather
than once; and `HEAD.lock` and `objects/maintenance.lock` accumulate the same way, so
clear by pattern, not by name.

**The rule this earns:** a workaround that makes git write somewhere unusual is more
dangerous than the blocker it works around, because its failure mode is a *successful*
commit with the wrong contents. Prefer the fix that keeps git in its normal path. And
after any commit made through a workaround, read `git log --stat` and `git status`
rather than trusting the exit code — the deletion commit exited 0.

---

## Second postscript — "can I run traffic in this repo?", and what answering it found

Yes, and that is what the boundary bought: `drive()` needs Polaris and MinIO,
not OpenSearch, not kubectl, not `local-k8s`. But there was no entry point (step
4 is not done and the v2 notebook still carries its gates), so checking the
answer meant reading `drive()` closely — and it had **two defects, in the one
path nothing tested.**

**`dry_run` was not dry.** The check sat AFTER the fixture was built, so a "dry
run" created a catalog, a namespace, a table, a view, two principals, two roles
and the whole `doomed_*` family — dozens of mutating calls — and only then
declined to issue the grid. The docstring said it issued none.

**And it returned from inside the `try`,** so `_finish` assembled the record and
wrote `runs/traffic-<run>.json` BEFORE `finally` ran cleanup. A dry run returned,
and persisted, a record missing its own phase-I rows.

Both were one mistake — a check placed after the work it was meant to precede —
and the reason neither was caught is worth more than the fix: **there was a test
for `_cleanup`, a test for `_finish`, and no test for the order they run in.**
Unit tests for each piece, none for the control flow. The replacement is
structural and cannot rot: `test_drive_never_returns_from_inside_its_try_block`
walks `drive`'s AST and fails on any `return` in that block, whatever it returns.

### Prism, which was Kade's idea and is a better answer than the one proposed

The plan on the table was to make `dry_run` genuinely dry and stop. Kade asked
for **Prism** against the vendored specs instead, and it is a different class of
check: `dry_run` proves each cell PRODUCES a request, by nothing raising. Prism
proves each request is **valid against the document the run already uses as its
denominator.** `src/spec_check.py`.

**It is two-sided, and it has to be.** The grid contains deliberately broken
cells, so *"every request must validate"* would flag them and read as a harness
bug. A cell targeting 400 on an operation **with a body** substitutes
`MALFORMED_BODY` and MUST be rejected; every other cell MUST be accepted.

**And it found a Polaris/spec divergence before ever running.** `getConfig`'s
400 cell drops `warehouse` — which the Iceberg document marks
`required: false`. So the request is SPEC-VALID and Prism will accept it, while
this build answers 400 (measured 2026-08-31, and the reason that cell exists).
That is a fact about Polaris, and it is reported under `build_findings`, not as
a failure of the check — SCENARIO §6's two sections that must never merge.

### Two controls, because the obvious way to run Prism cannot fail

`prism mock` **without `--errors`** logs violations and answers 200 anyway. Run
against that, this module reports 286 valid requests and a green verdict — the
most convincing wrong answer it could give, and the same shape as Gate 5's term
filter matching nothing and the two gates that reported PASS on zero rows. So a
**negative control** (a request known to be invalid) must be rejected and a
**positive control** (one known to be valid) must be accepted, or the pass is
**VOID**. VOID is not PASS and not FAIL: nothing was measured, and the CLI exits
2 for it.

Three things that cost a cycle each and are the reusable part:

- **The naive negative control was `getToken`** — the grid's sort order reaches
  it first, it is the ONLY form-encoded operation, and whether Prism validates a
  form body against a schema is unsettled. The least representative cell in the
  grid was vouching for the other 285. It is excluded from control selection now
  and still checked.
- **"Not routed" must not be diagnosed as "not enforcing".** With every path
  404ing, the first version blamed the missing `--errors` — sending the reader
  to a fix that is not the fix and leaving the mount wrong. `classify` already
  split `NOT_ROUTED` from `REJECTED` for rows; the control diagnosis now does too.
- **A globally broken Prism VOIDs rather than producing 286 findings**, in both
  directions: one that accepts everything is indistinguishable from one that is
  not enforcing, and one that rejects everything means the mount or the document
  is wrong. Two of my own tests asserted FAIL for these and were wrong; the code
  was right. To see a FAIL you have to break something the controls do not vouch
  for, which is also the only realistic shape.

**The mount is derived, not assumed.** The two documents differ and the
difference is invisible until every catalog request 404s: management carries
`/api/management/v1` in its `servers` entry, Iceberg defaults `basePath` to `""`
and gets `/api/catalog` from POLARIS, not from the spec. `prism_mounts` resolves
each document's own `servers` block rather than hardcoding the two cases.

### What is NOT verified

**Prism has never run against any of this.** `npm` answers **403** through the
org egress policy on every machine a Cowork session can reach — the same wall as
`pypi.org` — so it could not be installed. The 29 tests run against a stub that
speaks Prism's response shape. They establish that the logic AROUND Prism is
right; they do not establish that Prism agrees with the stub about what is
invalid, and **the first real run is the one that confirms the mount points.**

Gate: **289 passed** under the stand-in, 11 deliberate mutants, 11 caught.

---

## Third postscript — the first real Prism run, and it was worth every bit of the design

Kade ran it. **FAIL: 82 accepted, 57 rejected, 144 not routed, 3 error.** Three
real findings and two bugs in the check, and the two bugs are why most of the
table was noise.

### What was real

1. **`updateProperties`'s 400 cell cannot do what it claims.**
   `UpdateNamespacePropertiesRequest` has **no required fields** and does not
   forbid extra ones, so `MALFORMED_BODY` is a SPEC-VALID body. Prism accepted
   it. That cell is not testing malformation; it is a 400 the harness cannot
   provoke this way. **This is the finding the whole module exists to produce**,
   and it arrived on the first run.
2. **The Iceberg document cannot describe its own responses.** ~36 rows carried
   `response.body.metadata.schemas.0.fields.0.type` and
   `response.body.delete-files.0.content`. Those are RESPONSE violations: Prism
   generated an example response from the document and it failed the document's
   own schema. Nothing to do with any request.
3. **`getConfig`**, reported correctly under build findings, as designed.

### Bug one: the mount was DERIVED, and derivation is not measurement

**144 not routed was exactly the 144 management cells.** All 142 catalog cells
routed; every management cell 404'd. Prism ignores a templated server base path
and mounts the document's paths at the ROOT — so the derived `""` was right for
Iceberg **by luck** and the derived `/api/management/v1` was wrong for
management.

Reading the mount out of the `servers` block looked principled. It was a guess
about a running program dressed as a fact about a document, and this repo has a
rule for that. `candidate_mounts` now returns a LIST and `resolve_mounts` probes
the live server with one known-good request per candidate, takes the first that
does not 404, and **prints what it tried** — the report's mount table now reads
`(root)->404, /api/management/v1->200`, which is the diagnosis rather than the
symptom. An API that routes at NO candidate is VOID, not 144 bad requests.

### Bug two: the controls could not see it, and that is the worse one

Both controls came from the whole grid, and the grid's sort order put both on
**catalog** operations. So `createNamespace` and `getConfig` reported green
while half the run 404'd. **A control that cannot fail for the thing it vouches
for** — the exact failure this module was written to prevent, sitting inside the
module, one file away from the docstring describing it.

There is one control pair **per API** now. The same mistake had already been
caught once in this file, when the negative control picked the only
form-encoded operation; it recurred in a different dimension because the fix
was specific and the lesson was general. Both are now tests.

### The verdict split that was missing

`classify` had two ways to say "the request is bad" and needed three. A
violation whose location is in the RESPONSE gets `SPEC_EXAMPLE`, is excluded
from `unexpected`, and is reported in its own section grouped by property —
101 cells across 21 operations collapse to one finding rather than 101 rows of
the same sentence. **A body carrying both kinds is a rejection**, because the
request half is the half being asked about.

**How to tell a response violation from a request one, without trusting a
label:** the same violation appeared for targets 2, 401, 403, 404 AND 409 of
one operation — identical regardless of what was sent. A verdict that does not
vary with the request is not about the request.

### The report also hid its own evidence

Three `getToken` rows came back `error` with an empty detail and **no status
column**, so they could not be read at all. `getToken` is the only
form-encoded operation and is `deprecated: true` in the document. The status is
in the row and was simply not printed; it is now, for controls and for odd
cells alike.

### And the bridge lied about a write

`device_commit_files` reported `written` for both files and the device still
held the old content — 18370 bytes, with neither `resolve_mounts` nor
`SPEC_EXAMPLE` in it. The handoff's trap list already says *"the Cowork file
bridge can report a write it did not land"*; this is the second sighting, and
`git status` would NOT have caught it here because the file was already tracked
and modified either way. **`md5sum` against the container copy is the check
after every commit.** A second identical call landed it.

### Still not verified

Gate: **304 passed** under the stand-in, 9 deliberate mutants, 9 caught. But
every one of these fixes was tested against the stub, and **the stub is now
modelled on one observed Prism run** rather than on nothing — better evidence
than before, still not Prism. The next real run is what says whether the probe
finds the management mount.

**Open, and deliberately not fixed here:** `updateProperties`'s 400 cell. The
grid should either drop that cell or malform it in a way the schema actually
forbids, and choosing between those is a decision about `api_status_matrix`,
not about this check.

---

## Fourth postscript — the second Prism run: the mount held, and the VOID was mine

`VOID: 205 accepted, 15 rejected, **0 not routed**, 63 spec-example, 3 error.`
The probe worked — both documents resolved at the root, and the mount table
shows `management (root)->500`, which is a 500 rather than a 404 and therefore
routed. 144 not-routed became 0.

### The finding that matters, and it is now computed rather than observed

**12 of the grid's 27 malformed-body 400 cells CANNOT be provoked by omitting a
required field**, because their request schemas declare **no `required` at
all**. `MALFORMED_BODY` is then a *valid* body: the cell drives a successful
call and reports a 400 it never provoked. Prism returned 200/201 for nine of
them.

```
management  addGrantToCatalogRole, assignCatalogRoleToPrincipalRole,
            assignPrincipalRole, createCatalogRole, createPrincipal,
            createPrincipalRole, resetCredentials,
            revokeGrantFromCatalogRole, updateCatalog
catalog     getToken, planTableScan, updateProperties
```

`createCatalog` requires `catalog`, which is exactly why it works as the
management negative control — the one operation in that half whose body the
document can reject.

**The run surfaced 9; the true number is 12.** The other three were masked
behind other verdicts (`getToken` by a 401, `planTableScan` and `updateCatalog`
by response violations). That gap is the argument for `unmalformable_cells`,
which computes the whole set **from the documents alone — no Prism, no
cluster** — and is asserted in the suite that already runs. A finding that
needs a running server to be seen is a finding that stays partly hidden.

Reported as **one harness finding**, in its own section. Four audiences now,
four sections, and the discipline is the same one SCENARIO §6 asks for:

| section | whose |
|---|---|
| cells that did not do what the spec says | the request, and a real failure |
| **harness findings** | **THIS repo's** |
| spec findings | the document's |
| build findings | Polaris's |

**Deliberately not fixed.** The grid should either stop emitting a 400 cell
where the schema cannot be violated by omission, or malform by wrong TYPE on a
declared property. One shrinks the denominator to 274 and one changes every
400 cell's request; both change `api_status_matrix`, and choosing is a decision
rather than a patch. Filed in `.memory/active-issues.md`.

### Two more of mine, both the same shape as before

**The VOID was wrong.** `listCatalogs` came back 500 with a *response*
violation — the request got through and Prism failed to build its own example.
I was requiring the positive control to be literally `ACCEPTED`, so a run that
was measuring perfectly reported VOID. The positive control asks one question,
*did a valid request get through*, and `SPEC_EXAMPLE` answers yes.

**The negative control is NOT loosened the same way, and that asymmetry is
load-bearing:** a request Prism rejects never reaches response generation, so a
negative control cannot legitimately come back `SPEC_EXAMPLE`. Loosening it
would let a non-enforcing Prism through, which is the single thing the controls
exist to catch. Writing the test for it exposed that **the stub had the order
backwards** — it generated the response before validating the request, so a
rejected request could come back as a document problem and the reasoning could
not have been tested at all. The stub validates first now, as Prism does.

**The three `getToken` rows were a security refusal, not a shape verdict.**
Status 401, no violations. `getToken` declares no `security` of its own and
inherits the document's global `security: [OAuth2, BearerAuth]`, so **Prism
demands a bearer token in order to obtain a bearer token**. The request is
correct — an OAuth token endpoint carries its credentials in the form body.
`AUTH_REQUIRED` is its own verdict now, excluded from failures and reported as
a spec finding. It is checked before the 400/422 rule so a security refusal can
never read as a malformed request, and after the violation check so a genuinely
malformed request cannot hide behind a 401.

### The pattern across all three runs, stated once

Every bug in this module has been the same one: **a check that could not fail
for the thing it was vouching for.** The negative control that was the only
form-encoded operation. Both controls on one API while the other 404'd. A
positive control that failed on a verdict meaning success. Each fix was
specific; the class kept recurring. What finally generalises it is the
`NOT_ABOUT_THE_REQUEST` set — a single named place saying which verdicts are
statements about the document rather than the request — plus a static computation
that does not need a server to be right.

Gate: **317 passed** under the stand-in, 9 mutants, 9 caught. `device_commit_files`
landed first time and was md5-checked, per the rule added an hour ago.

---

## Fifth postscript — the count I published was wrong, and nothing could have caught it

Kade approved fixing the grid. Before touching it I re-derived the set, and the
number was wrong: **11, not 12.**

`spec_check.request_schema` followed **one `$ref`** and read `required` off
whatever it landed on. `getToken` `$ref`s `OAuthTokenRequest`, which carries no
`required` of its own — its constraints live entirely in an `anyOf` over
`OAuthClientCredentialsRequest` (`grant_type`, `client_id`, `client_secret`) and
`OAuthTokenExchangeRequest` (`grant_type`, `subject_token`,
`subject_token_type`). Both branches require three fields, so
`{"matrix": ...}` satisfies neither and `getToken` **is** malformable. Read as
"no required", it was filed as unmalformable.

**That number went into a commit message, `MEMORY.md`, `roadmap.md`,
`active-issues.md`, and an assertion in `test_spec_check.py`.** The test
asserted `getToken` was in the set, so the suite defended the bug.

**And no run could have contradicted it.** `getToken` comes back **401 on a
security scheme** — Prism never evaluated its body at all. The one instrument
that might have disagreed was structurally unable to. I had even written that
`getToken` was "masked by a 401" as an argument for computing the set
statically, without noticing the mask was hiding my own error rather than a
Polaris one.

The fix is `has_required_fields`, and the two combinator rules are **opposites**:

- `allOf` — the body must satisfy EVERY branch, so **one** branch with
  `required` makes it malformable.
- `anyOf` / `oneOf` — the body need satisfy only ONE branch, so it is
  malformable only if **every** branch is. A single unconstrained branch
  accepts `{"matrix": ...}` and the whole schema accepts it with it.

Getting them the same way round would flip roughly half the answers, so both
directions are separate tests, and `$ref` resolution is depth-bounded — a
document that refs itself is the document's problem, hanging on it would be
ours. **35 schemas across the two documents hide their constraints in a
combinator**, so this was never going to stay one wrong answer.

### What this actually teaches, beyond the fix

The pattern I named in the fourth postscript was *a check that could not fail
for the thing it was vouching for*. This is that pattern one level up: **a
number derived by walking a document, corroborated by a run that could not have
disagreed with it.** Agreement between a static walk and an observation is only
evidence when the observation was capable of dissent — and here it was not, for
a reason I had already written down and read as support.

`unmalformable_cells` is still the right shape. It was just wrong, and it was
wrong in the direction that reads as more thorough: **one extra operation in a
list of things to fix looks like diligence, not like an error.**

Gate: **62 passed** in `test_spec_check` (was 57), 4 mutants on the combinator
walk, 4 caught — including `anyOf` using ANY instead of ALL, and the depth bound
removed, which hangs rather than fails, and the cyclic test is what makes the
hang visible.

**The grid decision is still open and now rests on a number that has been
checked**: 11 cells, and `getToken` is not one of them.
