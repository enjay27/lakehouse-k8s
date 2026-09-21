# 2026-09-03 — adopt `polaris-learning`'s memory + commit convention

**Ask:** make `CLAUDE.md` and `MEMORY.md` match the `polaris-learning` project's
format, and have Claude commit each change automatically the way it does there.

## Decisions

- **Full `.memory/` tree**, not just a reshuffle of the two root files. The polaris
  format only works because `MEMORY.md` has somewhere to push detail *to*; a 40-line
  cap with no tree behind it just deletes information.
- **Docs-only first commit.** The repo had in-flight work (`logging/fb-values.yaml`
  modified, `postgresql/schema/bootstrap.sql` staged with `bootstrap_2.sql` deleted,
  and several untracked runbooks). Sweeping those into a "documentation convention"
  commit would have produced exactly the kind of message the new convention forbids —
  one that describes files rather than a finding. They stay uncommitted for Kade.

## What the audit turned up while writing the tree

Writing `active-issues.md` meant re-checking each of the seven blockers from the
2026-08-18 audit against what is on disk *today*, rather than copying the old list:

- **Three are fixed on disk** — MinIO templates now exist (12 of them, untracked);
  bucket names are reconciled in `minio/values.yaml`; `postgresql/values.yaml` is
  nested with 10Gi, `/dev/shm` and dual-family `pg_hba`. None has been installed, so
  they are logged as ON DISK, UNVERIFIED, not as done.
- **Four are still open** — Polaris `bootstrapCredentials` is *still* commented out
  under `createSecret: true` (renders `""`); `spark/values.yaml` still carries a
  plaintext MinIO secret key at line 30 while Polaris uses `minioadmin/minioadmin`
  and `minio/values.yaml` uses `minio/minio`; the stale
  `polaris-persistence-secret.yaml` still points at `postgres-postgresql:5432`; and
  `kafka/` still pins no image at all.
- **One new question.** `CLAUDE.md` described a Docker Compose OpenSearch as the log
  sink, but there is **no compose file anywhere in this repo**, and the uncommitted
  `logging/fb-values.yaml` change points Fluent Bit at VictoriaLogs instead. Rather
  than carry the OpenSearch claim forward into the new `CLAUDE.md` tech stack, it is
  written as an open question in `active-issues.md` #7.

One claim written into the tree was **wrong and had to be corrected before commit**:
`server/node_modules/` was described as committed noise. It is not tracked at all —
`git ls-files server` returns four files, and `node_modules` has been in `.gitignore`
since the initial commit. Written from the size of the directory on disk rather than
from git, which is exactly the "verify against intent instead of against the system"
error the rest of this repo is about.

The OpenSearch question is the reason the audit was worth doing: the old `MEMORY.md` asserted
"OpenSearch (v1.5.0): Deployed and running stably via Docker Compose" as a completed
checkbox, and nothing in the repo supports it.

## Environment note

This session had **no cluster reach** — `device_bash` is an isolated VM with only the
repo folder mounted, so no `kubectl`, `helm` or `docker`. Everything here is a file
edit and a commit; nothing was verified against OrbStack. The DoD items that need a
live cluster are recorded as NOT VERIFIED in the commit body, per the new rule.
