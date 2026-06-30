# Skill: Strict 6-Step Workflow Execution

## When to Use This Skill
- Activated immediately upon session initialization.
- Governs all feature requests, refactoring tasks, notebook updates, and infrastructure configurations.

## The Protocol
1. **Plan Phase:** Read the user's request. Output a markdown list detailing *exactly* which files, cells, or manifests will be touched and what logic will change. Stop execution and wait for user input.
2. **Review Checkpoint:** Wait for explicit developer confirmation before making any changes.
3. **Execution Phase:** Write code or update configuration files directly to local disk assets. 
4. **Verification Loop:** Run local checks (e.g., test suites, container status lookups, or dry-runs). If an exception occurs, read the traceback, iterate, and fix it natively. Do not ask the user to debug basic typos or missing imports. Limit to 2 autonomous repair attempts.
5. **Handoff Phase:** Write the updated status directly into the local `MEMORY.md` file.
6. **Token Reset Hygiene:** If multiple complex execution cycles have occurred and the chat session grows long, explicitly prompt the user to close this task block and open a fresh Cowork task session to clear the history cache and avoid auto-compaction token penalties.