# 2026-09-10 (session 11) — the grid malforms by wrong type where it cannot malform by omission, and one cell still cannot be seen

Session 10 left the fix **written, unverified and uncommitted**. This session's
job was to land it. What it actually produced is a third instance of the same
pattern the last three sessions kept naming.

## What was already on disk

`git status` showed `src/api_status_matrix.py`, `src/spec_check.py` and
`test_spec_check.py` modified against `7cb12c2`, implementing the option Kade
approved: **malform by wrong TYPE on a declared property** where the schema
declares no `required`. Nothing was committed, `MEMORY.md` and
`active-issues.md` still called the decision OPEN, and no gate had been run.
The code was not re-derived; it was verified and landed.

The shape it takes:

- `Operation.malform`, decided **at parse time** from the document: `MALFORM_OMIT`
  where `required` exists, else `{"property", "value", "type"}`, else `None`.
- `malformed_body(op)` reads that strategy. **Omission is tried first, and that
  ordering is the whole point:** 16 of the 27 body-carrying 400 cells send a
  byte-identical body to every run before this change, so those cells stay
  comparable across runs. Only the 11 that were driving *successful* calls
  change shape, and they had nothing to lose.
- `spec_check` stopped carrying its own copy of the walker and **imports it**
  from `api_status_matrix`. Two copies would drift, and the drift would be
  invisible until a 400 cell sent a body the grid thought was broken and the
  checker thought was fine.
- `malform_strategies()` reports `{omit, wrong_type, none}` so a reader can see
  which cells changed shape and when.

## The count is 16 / 11 / 0, and the 11 are the named 11

Computed from the documents alone, no Prism, no cluster:

```
catalog     planTableScan               case-sensitive='not-a-boolean'   (boolean)
catalog     updateProperties            removals='not-an-array'          (array)
management  addGrantToCatalogRole       grant='not-an-object'            (object)
management  assignCatalogRoleToPrincipalRole catalogRole='not-an-object' (object)
management  assignPrincipalRole         principalRole='not-an-object'    (object)
management  createCatalogRole           catalogRole='not-an-object'      (object)
management  createPrincipal             credentialRotationRequired='not-a-boolean' (boolean)
management  createPrincipalRole         principalRole='not-an-object'    (object)
management  resetCredentials            clientId=['not-a-string']        (string)
management  revokeGrantFromCatalogRole  grant='not-an-object'            (object)
management  updateCatalog               currentEntityVersion='not-an-integer' (integer)
```

`unmalformable_cells()` is now **empty** against these documents, and an empty
finding is the right thing for it to report. `harness_findings` renders nothing.

## THE FINDING: ten of the eleven are verified. `planTableScan` is not, and could not be.

The spec-check PASSes — 196 accepted, 25 rejected, 0 not routed, 62
spec-example, 3 auth-required, 0 error — and the arithmetic against the last
run reconciles exactly: **9 cells moved accepted->rejected** (the nine Prism had
answered 200/201) and **1 moved spec_example->rejected** (`updateCatalog`, which
had been masked by a response violation). That is 10.

**The eleventh did not move.** `planTableScan`'s 400 cell is still
`spec_example`, status 500. So it was probed directly, and the result is
unambiguous:

```
POST .../plan  {"case-sensitive":"not-a-boolean"}  -> 500, 53 validations
POST .../plan  {}                                  -> 500, 53 validations
```

**Byte-identical violation lists, and not one entry is a `request` violation.**
Every entry is `['response','body',...]`. All five of its cells — targets 2,
401, 403, 404 and 400 — return the same 53. Prism's response generation for
that operation fails against the document's own schema before any request
verdict is reportable, so **a malformed request and a valid one are
indistinguishable on that endpoint**.

`updateCatalog` was masked the same way and came unmasked, because its response
violation is recoverable; `planTableScan`'s is not.

### Why this matters more than the one cell

The last three sessions each ended by naming *a check that could not fail for
the thing it was vouching for*. This is that again, one level further out:
**the instrument used to verify the fix is blind on one of the cells the fix
was for** — and it is blind in the direction that reads as success, because
`spec_example` is excluded from the failure count by design and correctly so.
`planTableScan` was ALSO one of the two cells the original run under-counted,
for this identical reason. The same blind spot has now produced a wrong count
once and an unverifiable fix once.

Recorded, not fixed. The honest statement is **10 of 11 verified through Prism,
1 unverifiable through Prism**, and `planTableScan` is separately recorded as
**not routed on this build** (404 to every cell), so the live run cannot settle
it either.

## The gate, and the environment finding underneath it

**960 passed, 45 skipped in 77.8s under REAL `pytest`** — in the Cowork Linux
VM, not a stand-in, and after `black` reformatted two of the three files.
Kade's macOS `uv run pytest` reported **1005 passed** on the same tree; 960 + 45
= 1005, so the two runs collected the same suite and the 45 skips are
Linux-side.

**This is the first Cowork session in which the DoD gate was actually
runnable**, and the reason is that `.memory/active-issues.md` was stale:

- `pypi.org`, `files.pythonhosted.org`, `registry.npmjs.org` and `github.com`
  all answer **200** through the VM's proxy. The entry saying the VM has *"no
  egress at all"* is no longer true.
- `uv`, `node` and `npx` are installed in the VM. `black` resolves at
  **26.5.1**, the exact pin — the 26.3.1 mismatch noted last session is gone.
- **Prism runs locally in the VM**, so `--spec-check` needs no cluster and no
  Mac. The whole tier-2 check is now a Cowork-session capability.
- The venv must be built **outside the mount**
  (`UV_PROJECT_ENVIRONMENT=$HOME/venv-linux`). A bare `uv sync` at the repo root
  would overwrite the macOS-aarch64 `.venv` and break Kade's Jupyter.

**The cluster is still unreachable and no credential changes that.** `local.yaml`
reads fine, but raw TCP to `192.168.139.2:8181/:9200/:5432` is *Network is
unreachable* and `localhost:9200` is refused — the VM is not on the Mac's
network and its loopback is its own. Handoff steps 0-1 stay Kade's.

**A trap worth the line:** the first probe of Polaris returned **403**, which on
this project reads as a Polaris authorization verdict. It was not. The header
said `X-Proxy-Error: blocked-by-allowlist`. An allowlist 403 and a Polaris 403
are indistinguishable by status alone, and this repo's entire grid is built on
reading status codes.

## Also true, and not this session's to fix

`log-coverage/doc-api-status-matrix-results.md` in the working tree is a live
drive Kade ran at **07:54Z, run 1789026666** — 286 calls, 228 covered,
correlation 235/235, 4 stray 500s. It is his run, it is not part of this change,
and it was deliberately left out of this commit along with the other 14 dirty
files.
