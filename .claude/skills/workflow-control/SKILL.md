# Skill: Strict 6-Step Workflow Execution

Merged 2026-09-21 from the two source repos' copies, which shared these six
steps and differed only in the guard at step 1 and the verification at step 4.
Both variants are preserved below as per-tree clauses.

## Activation
- Activated immediately upon session initialization.
- Governs all feature requests, refactoring tasks, notebook updates, chart
  edits, Kubernetes topology updates and Helm values changes.

## The six steps

1. **Plan Phase.** Read the developer's request. Output a markdown impact
   analysis naming *exactly* which files, cells, charts or values files will be
   touched and what logic will change. **Halt and wait for permission.**
   - *Under `charts/`, `releases/`, `logging/`, `schema/`, `runbooks/`:* first
     confirm the runtime context maps to the `datahub-hynix` namespace **and**
     that the active `kubectl` context is exactly `orbstack` (CLAUDE.md's
     Cluster-Context Guard). In a Cowork session there is no cluster reach at
     all -- say so rather than reporting a check you could not run.
2. **Review Checkpoint.** Do not write to files or run changes until the
   developer submits explicit approval.
3. **Execution Phase.** Modify configuration, modules or notebooks directly on
   disk. Edit files in place; never re-type a file's contents from earlier tool
   output, which may have been truncated.
4. **Verification & Error Recovery.** Parse any traceback, attempt
   auto-correction at most **2** times, then halt for manual feedback.
   - *Platform trees:* `helm lint` **and**
     `helm upgrade --install ... --dry-run=client --debug`; then query the
     running object, never the values file.
   - *Suite trees (`src/`, `tests/`, `notebooks/`, `diagnostics/`):*
     `pytest`, then `black . && isort .`.
5. **Handoff Phase.** Record the outcome in the memory tree: the *Now* section
   of `MEMORY.md` and nothing else there; detail into `.memory/`.
6. **Token Reset Hygiene.** Long layout cycles trigger heavy auto-compaction
   token drain. When a milestone wraps up, prompt the developer to close the
   task block and open a fresh Cowork session.
