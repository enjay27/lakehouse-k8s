# `.memory/` — where the detail lives

`MEMORY.md` in the repo root is an **index, kept under ~40 lines**. It says what is
true *now* and links here. Everything that would make it grow goes in one of these
files instead.

| file | takes |
|---|---|
| [`goal.md`](goal.md) | the standing objective and the shape of the platform. Changes rarely. |
| [`environments.md`](environments.md) | **read before running anything** — cluster, context, namespaces, and what must never run where. |
| [`repository-map.md`](repository-map.md) | what lives in which directory, and which copy is authoritative. |
| [`roadmap.md`](roadmap.md) | what is done, what is next, with the numbers. |
| [`active-issues.md`](active-issues.md) | anything you should not trust yet: open blockers, config written but not proved live, values that are wrong on disk. |
| [`completed.md`](completed.md) | finished structural work, kept so it is not re-litigated. |
| [`sessions/`](sessions/) | `<date>-<slug>.md` — one session's blow-by-blow, **including the wrong turns**. |

## Rules

- **A fact with a number goes in `roadmap.md`; the story goes in `sessions/`.**
  The wrong turns do not survive summarising and are the part most likely to be
  repeated.
- **Written is not live.** Anything not verified against a running cluster belongs
  in `active-issues.md`, not `roadmap.md`. This repo's most expensive failure was
  configuration that was written correctly and never applied — an entire
  `postgresql:` block sat inert under the wrong nesting level for months, and
  nothing warned.
- **Task runbooks stay in the repo root**, beside the thing they describe
  (`RESET-AND-CLEAN-INSTALL.md`, `local-k8s-HANDOFF.md`,
  `shm-exhaustion-orbstack-leg-runbook.md`). They are written for someone starting
  cold and are the right first read for a *task*; `MEMORY.md` is the right first
  read for the *repo*.
