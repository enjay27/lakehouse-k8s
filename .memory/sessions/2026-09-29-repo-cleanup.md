# 2026-09-29 — repo cleanup: dead code, stale docs, the memory tree

Kade asked for a refactoring plan that brings every document and the codebase up to date and
keeps only the docs that are needed. Plan approved with four decisions: archive the current state
on an `archive/*` ref and **delete** (including `archive/`); keep useful tests and docs; delete
`releases/datahub/VALUES_REFERENCE.md`; keep every session record.

Before-state: branch `archive/pre-cleanup-2026-09-29` + tag `v-archive/pre-cleanup-2026-09-29` at
`cf6eae8`. Work on branch `refactor/2026-09-29-cleanup`, one commit per phase. Baseline: pytest
1101 passed; `helm lint` 4/4; client dry-run minio, polaris, polaris-log-batch.

## What the cleanup found (the part worth more than the deletions)

1. **`apply-lua.sh` had refused to run since the merge** (platform `#52`). The merge moved
   `fluent-bit/` → `releases/fluent-bit/` but not the paths *inside* the scripts. The script cds to
   the repo root and then exits `FATAL: run inside the local-k8s repo`. Same for `step3` and
   `step11`. Nobody noticed for 8 days because no Lua change was rolled. Fixed; the read-only half
   was run: `kubectl diff` = 0, step3 §3 sha `f92bb6d4dbbfc346` == repo.
2. **The 44 policy tests passed only because the old checkout still existed.**
   `resolve_fb_values()` never found the in-repo `logging/fb-values.yaml`; it resolved
   `~/hynix/local-k8s/logging/fb-values.yaml`. Deleting the old directory would have turned them
   into silent skips. The file is now `tests/fixtures/fb-values-shipper.yaml`.
3. **Every API→SQL matrix report since 09-18 says "Polaris 1.3.0-incubating"**: the version was a
   default argument that the only live caller never overrode.
4. **Fluent Bit dropped two chunks to OpenSearch on 09-27** (`#49`), seen in step3 §2 while
   verifying finding 1. Same symptom class as `#19` / `#29`.
5. **`charts/minio` would bring MinIO up empty** (`#53`). Release rev 1 is a Deployment + kept PVC;
   the chart renders a StatefulSet with `volumeClaimTemplates`. It was found only because the
   environments file was rewritten from `kubectl get` instead of from the old file.

## Wrong turns

- **zsh does not word-split `$var`.** Two loops over a space-separated list ran once with the whole
  string as one argument (`release name is invalid: benchmarks-minio minio`; a perl rewrite that
  touched 0 files). Use `while read` or arrays.
- **A directory-scoped `git add -A diagnostics …` committed Kade's uncommitted edits** to
  `polaris_api_traffic_v1.ipynb` (884 lines) into the phase-5 commit. Caught from the `--stat` right
  after; rebuilt the commit without it (reset --soft, restore --staged). The working tree was
  untouched. Rule since: stage explicit paths, read `git diff --cached --stat` *before* committing.
- **A redaction regex failed and printed a committed principal secret** from `03_api_index_matrix`
  into the session output. It was already in git history, so nothing new leaked; it is now
  recorded in `active-issues/catalog.md` with "rotate, then strip".
- **`doc-privilege-matrix-plan.md` was deleted and restored**: it looked like a finished plan, but it
  is the only definition of the outcome taxonomy that the results doc reports in.
- Phase 1's commit message first said "~60 policy tests"; counted, it is 44. Amended.
- A sentence in `#49` guessed the drops coincided with the Polaris restarts that evening. The log
  times are probably UTC, which would make it after midnight KST. Removed; the timezone is listed
  as unknown.

## Rules that decided what stayed

- A PLAN/HANDOFF that is the **cited design of code still in use** stays, finished or not
  (`PLAN-grant-scale-sweep`, `SCENARIO-logging-test`, …). A dated doc cited only by other dated
  docs goes.
- Anything open in a doc was checked against `active-issues/` before deleting; two untracked
  items were carried (`#50` review P5, `#51` non-discriminating roadmap assertions).
- Session records and `docs/MERGE-2026-09-21.md` keep naming deleted paths; they are dated
  records. `docs/DELETED-2026-09-29.md` resolves every such name.
