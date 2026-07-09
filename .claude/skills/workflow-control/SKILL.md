# Skill: Infrastructure Workflow Execution

## When to Use This Skill
- Instantly activated upon session initialization.
- Governs all dual-runtime edits, Kubernetes topology updates, Docker Compose configurations, and Helm chart variations.

## The Protocol
1. **Plan Phase:** Read the developer's request. Scan local config structures (both Compose specs and Helm chart variables). Verify your runtime context maps explicitly to the `datahub-hynix` namespace **and confirm the active `kubectl` context matches the expected local cluster** (see CLAUDE.md's Cluster-Context Guard) before considering any change. Output a clean markdown impact analysis detailing exactly which running engines, charts, or values files will be altered. **Halt execution and wait for permission.**
2. **Review Checkpoint:** Do not proceed to run any changes or write to files until the developer submits explicit approval.
3. **Execution Phase:** Modify local configurations, update targeted `values.yaml` fields, or update Docker Compose declarations directly on disk.
4. **Verification & Error Recovery:** Run local verification hooks (e.g., `docker-compose ps` and `helm list -n datahub-hynix`). If a dependency collision, runtime exception, or connection timeout occurs, parse the stdout traceback, attempt auto-correction up to 2 times, and halt if the failure persists.
5. **Topology Handoff:** Log final engine properties, exposed container/cluster network ports, and active deployment flags directly into the root `MEMORY.md`.
6. **Token Reset Hygiene:** Because long layout cycles trigger heavy auto-compaction token drains, monitor the task length. Explicitly prompt the user to close this task block and open a fresh Cowork task session to clear the history cache when a milestone wraps up.