# The memory tree — which file takes what

Merged 2026-09-21 from two repos. Where a file existed in both, the two are kept side by side
with a `-platform` / `-catalog` suffix rather than blended: `active-issues` alone is 183 KB +
111 KB, and a 289 KB lookup file is not a lookup file. **Reconciling them is a tracked
follow-up** (`active-issues/merge.md`), not something the merge commit attempted.

- **platform** = the cluster and what ships to it — `charts/ releases/ logging/ schema/ runbooks/`
  (was the `local-k8s` repo).
- **catalog** = the suite that measures it — `src/ tests/ notebooks/ diagnostics/`
  (was the `polaris-learning` repo).

| file | takes |
|---|---|
| `../MEMORY.md` | the <40-line index. *Now*: what is next, and what is written but not running |
| `active-issues/platform.md` · `catalog.md` | anything you should not trust yet — a value, a number, a tool, a runbook. Configuration written but never applied lives here |
| `active-issues/merge.md` | the follow-ups the 2026-09-21 merge deliberately deferred |
| `roadmap/platform.md` · `catalog.md` | facts with numbers; milestones; the verification assertions |
| `sessions/` | the blow-by-blow, **including the wrong turns** — the part most likely to be repeated if lost. 37 files, flat, chronological across both halves |
| `environments-platform.md` · `-catalog.md` | contexts, namespaces, ports, and what must never run where. **Read before running anything** |
| `goal-platform.md` · `-catalog.md` | the standing objective and structural model of each half |
| `repository-map-platform.md` · `-catalog.md` | **pre-merge maps.** Paths in them are stale; `CLAUDE.md` has the current layout |
| `completed-platform.md` · `-catalog.md` | finished structural work |

**A fact with a number goes in `roadmap/`; the story goes in `sessions/`.** Neither goes in
`MEMORY.md`, which is an index and nothing else.
