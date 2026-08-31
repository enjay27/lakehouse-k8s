# .memory

`MEMORY.md` at the repo root is the **index**: current state in one paragraph,
plus links to here. This directory is the detail.

The split exists because `MEMORY.md` grew to 198 lines against its own 150-line
limit, and a tracking document nobody finishes reading tracks nothing. A task
that only needs to know *where things stand* reads the index and stops; a task
that needs to know *why* follows one link.

| file | what it holds |
|---|---|
| `goal.md` | the standing objective and structural model |
| `repository-map.md` | where things live, current inventory |
| `environments.md` | local / dev / prod, and what must never run where |
| `roadmap.md` | what is done and what is next, newest first |
| `active-issues.md` | open faults, plus struck-through ones whose reasoning still matters |
| `sessions/` | per-session narrative, including the wrong turns |
| `completed.md` | finished structural work, kept out of the roadmap |

## Keeping it usable

- **`MEMORY.md` stays under ~40 lines.** If it grows, the growth belongs in a
  file here, not in the index.
- **One session, one file in `sessions/`.** Named `YYYY-MM-DD-topic.md`.
  Summarise it in `roadmap.md` as a single entry that links back.
- **Detail is not the same as narrative.** A finding with a number goes in
  `roadmap.md`; the story of how it was found — the wrong turns especially —
  goes in `sessions/`. The wrong turns are the part a summary destroys and the
  part most likely to be repeated.
- **A standalone HANDOFF is not memory.** `HANDOFF-*.md` lives beside the code
  it describes and is written for someone starting cold. Link it; do not copy it.
