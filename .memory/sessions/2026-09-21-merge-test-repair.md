# 2026-09-21 — repairing the suite gate the merge broke

Follows `2026-09-21-the-merge` (see `docs/MERGE-2026-09-21.md`). First task after the
merge landed.

## What was wrong

Moving the 21 `test_*.py` modules from the repo root into `tests/` broke every one of
them that resolved `src/` relative to its own file:

```python
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))   # -> tests/src
```

`pytest --co` reported **50 tests collected, 20 errors** — 20 of 21 files failed to
import at all. The suite's half of the Definition of Done was unrunnable, and
`docs/MERGE-2026-09-21.md` did not list this among its eight deferred seams. It was
not deferred; it was missed.

## The wrong turns, in order

1. **"12 of 21 are broken."** The first count came from a regex matching only the
   `Path(__file__)` form. Two more forms existed — `pathlib.Path(__file__)` and a
   `ROOT` indirection — and the real number was **20**. Counting a blast radius with a
   pattern narrower than the thing you are counting gives an answer that looks precise
   and is not.

2. **"M1 is 66 notebooks, blanket `parent` -> `parent.parent`."** The depth shift is
   **not** uniform. 61 notebooks moved one level deeper; **5 in `diagnostics/` did not
   move at all** and are already correct. A blanket sweep would have silently broken
   those five. There are also four distinct bootstrap forms in use, not one — 43 via
   `_SRC`, 9 raw `cwd()`, 7 `sys.path.insert(0, '.')`, 3 via `REPO`. M1 remains open;
   this is the note for whoever does it.

3. **"62 failures, so the merge damaged something."** After the import fix, collection
   went to 996 tests but the run reported 13 failed / 49 errors. Every one traced to a
   single cause: `SpecUnavailable: no OpenAPI document in .../spec -- run
   fetch_specs.sh`. The vendored OpenAPI documents are **gitignored downloads**, so they
   were never in `HEAD` and the merge — which snapshotted `HEAD` — correctly did not
   carry them. A fresh clone of the *old* repo would fail identically. Copying the two
   documents from the old working tree took the run to **996 passed, 0 failed**.
   The failure was environmental, not structural, and the only way to know that was to
   restore the missing input rather than start editing tests.

## The fix

One anchored setting in `pyproject.toml` replaces twenty per-file path hacks:

```toml
[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

The twenty `sys.path.insert` lines were deleted. Ten further path constructions had
moved *structurally*, not just by depth, and were rewritten explicitly:
`log-coverage/spec` -> `diagnostics/ladders/log-coverage/spec`,
`diagnostics/api-sql-profile` -> `diagnostics/ladders/api-sql-profile`,
and `.../api-sql-profile/reports/` -> `diagnostics/outputs/banked/reports/`.

**Four of those sat behind `skipif(not X.exists())` guards.** Had they not been fixed,
they would have reported *skipped*, not failed — the suite would have gone green while
silently testing less. That is the same shape as `test_log_coverage.py:162`, which still
skips on an unreachable `fb-values.yaml` (M3).

## Numbers

| | before | after |
|---|---|---|
| collection | 50 collected, **20 errors** | 996 collected, 0 errors |
| run | not runnable | **996 passed, 0 failed** (49.3 s) |
| files touched | — | 20 tests + `pyproject.toml` |

## Still open

- **The platform gate has never run** against this tree. No `helm`, no `kubectl`, no
  cluster from a Cowork session. Unchanged from the merge commit.
- A fresh clone needs `fetch_specs.sh` before the suite can pass. Worth stating in the
  README that does not yet exist.
- M1 (61 notebooks, not 66), M2, M3, M4/M5, M6 — see `.memory/active-issues/merge.md`.
