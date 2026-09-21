# Merge follow-ups — deferred by the 2026-09-21 Big Merge, none done

The merge commit relocated files and changed no content. Everything below is a known,
deliberate seam left for a follow-up commit of its own.

| # | what | where | why it was deferred |
|---|---|---|---|
| M1 | Notebook `sys.path` bootstrap depth is wrong | all 66 notebooks under `notebooks/` and `diagnostics/` | notebooks moved one level deeper (`notebooks/<domain>/`), so `cwd().parent / "src"` no longer resolves. Mechanical but touches every notebook, and notebook diffs are unreviewable inside a 500-file commit |
| M2 | Absolute cross-repo paths still point at the old repo | `diagnostics/ladders/api-sql-profile/reset_realm.sh:37-38`, `src/config/local.example.yaml:33`, `src/log_coverage.py:170` | they resolve today because the old repo still exists on disk. They must become repo-relative before the old directories are removed |
| M3 | `fb_values_path` points at a dead release | `src/config/*.example.yaml`, `src/log_coverage.py:185`, `tests/test_log_coverage.py:162` | `logging/fb-values.yaml` describes the shipper uninstalled 2026-09-18. The live policy is `releases/fluent-bit/polaris_access_log.lua` + `values.yaml`. **Whether the suite has been validating against the wrong file is an open question, not a settled finding** — it needs tracing, which is a task, not a move |
| M4 | The two `.memory` halves are namespaced, not merged | `.memory/active-issues/`, `.memory/roadmap/`, `.memory/*-platform.md` / `*-catalog.md` | 183 KB + 111 KB and 33 KB + 124 KB. Blending them is content work with real judgement in it |
| M5 | Issue numbers collide across halves | `.memory/active-issues/` | platform `#24` and catalog `#24` are different issues. Renumbering needs M4 done first |
| M6 | Jupytext pairing not set up | `notebooks/` | agreed as a follow-up. Pairing 66 notebooks generates 66 new `.py` files and changes the diff workflow — its own commit, its own verification |
| M7 | `repository-map-*.md` describe the pre-merge layout | `.memory/` | kept as historical record. `CLAUDE.md` carries the current layout |
| M8 | Neither DoD gate has been run against this tree | — | a Cowork session has no `helm`, no `kubectl`, no cluster. `pytest` has not been run either. **Treat the tree as unverified until Kade runs both gates locally** |
