# 2026-09-03 — the rebuild was done outside the runbook, and the task is closed

**What happened:** Kade reset and rebuilt the whole OrbStack cluster himself, including the
K8s services, and asked to close the rebuild task. He did **not** follow
`RESET-AND-CLEAN-INSTALL.md` — the 12-step order, the pre-flight image gate and the
verification block were all bypassed. The four config blockers were resolved during the
install; the details were not recorded.

Also confirmed, and worth having in writing because both were guesses until now:

- **OpenSearch runs in Docker**, outside the cluster and outside this repo. That settles the
  open question from the morning session: the old `MEMORY.md` line about a Docker Compose
  OpenSearch was *right about the container* and only stale about the rest. No compose file
  is versioned here because the thing it describes is not part of this repo.
- **Fluent Bit runs as a K8s DaemonSet and works.**

## What I did not write down, and why

The temptation was to close every issue and leave the tree clean. That would have been the
tidy summary rather than the honest one, so two things stay open:

1. **The repo has not been reconciled against the live cluster.** The blockers are fixed in
   the running releases; whether they are fixed in the `values.yaml` files here is unknown,
   and nobody has diffed them. This is #F1's exact shape — a gap between what a file says and
   what a cluster does — reopened by the rebuild rather than closed by it. `helm get values`
   per release is the whole job.
2. **The plaintext MinIO key at `spark/values.yaml:30`.** Kade resolved the credential
   conflict in the cluster, which does not un-leak a key that is in git history. Rotating it
   is a separate action from fixing the deployment, and it is easy to think the first happened
   because the second did.

The verification assertions were deliberately not run — Kade's call, to be run if a
PostgreSQL setting needs changing. They stay in `roadmap.md` as a reference rather than as a
pending step, because a checklist nobody intends to run is noise in a roadmap.

## Status of the runbooks

`RESET-AND-CLEAN-INSTALL.md` and `local-k8s-HANDOFF.md` are now **historical**. They are the
best account of why the rebuild was needed (#F1, #F2) and their install order still holds for
any future reinstall, but nothing should be executed from them as written. Both are still
untracked in git.
