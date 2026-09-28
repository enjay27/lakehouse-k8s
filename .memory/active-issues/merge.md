# Merge follow-ups — deferred by the 2026-09-21 merge

**Open: M3, M6, M10. Everything else is closed** (M1, M8-suite and M9 on 2026-09-21; the rest in the
2026-09-29 cleanup on branch `refactor/2026-09-29-cleanup`).

| # | what | state |
|---|---|---|
| M1 | Notebook `sys.path` bootstrap depth | **DONE 2026-09-21** — walk-up root, gated by `tests/test_notebook_bootstrap.py` |
| M2 | Absolute paths into the old `~/hynix/local-k8s` checkout | **DONE 2026-09-29.** `reset_realm.sh` now uses repo-relative `schema/`; `log_coverage.resolve_fb_values` uses `tests/fixtures/`; `local.example.yaml` drops `fb_values_path`. The 44 policy tests had passed only because the old checkout still existed. The same class of bug was in `releases/fluent-bit/apply-lua.sh` and two `logging/scripts/`: `fluent-bit/` instead of `releases/fluent-bit/` (platform `#52`) |
| M3 | The oracle reads the uninstalled shipper's Lua | **OPEN.** The file is now `tests/fixtures/fb-values-shipper.yaml` (policy v2/v3); the live DaemonSet runs `releases/fluent-bit/polaris_access_log.lua` (v6). Moving the oracle onto the live Lua is a change with its own verification, not a path swap |
| M4 | The two `.memory` halves namespaced, not merged | **DONE 2026-09-29.** `goal`, `environments`, `completed` merged into single files; the pre-merge READMEs and indexes deleted. `active-issues/` and `roadmap/` stay split by *domain* (platform / catalog), and the platform file's *Open* section now holds only open entries |
| M5 | Issue numbers collide across halves | **CLOSED 2026-09-29, no collision.** `active-issues/catalog.md` numbers nothing (its one `#N` is upstream `#379`). Convention: a bare `#N` is a platform issue |
| M6 | Jupytext pairing | **OPEN** — its own commit, its own verification |
| M7 | `repository-map-*.md` describe the pre-merge layout | **DONE 2026-09-29** — deleted; `CLAUDE.md` carries the layout |
| M8 | Neither DoD gate had run | **DONE 2026-09-29.** Suite: pytest green (1069). Platform: `helm lint` all four local charts; `--dry-run=client` minio, polaris, polaris-log-batch and fluent-bit. **postgresql still not dry-run** — its `postgresql-ha` subchart is not downloaded (`helm dependency build` first) |
| M9 | 20 of 21 test modules failed to import | **FIXED 2026-09-21** |
| M10 | A clone cannot pass the suite until `fetch_specs.sh` runs | **OPEN** until the root `README.md` says so |
