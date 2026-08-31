# Active Service Testing State

**Index, not the record.** Current state below; everything else is a link into
[`.memory/`](.memory/README.md). If you are picking this up cold, read the
handoff named in *Now* — it is standalone.

## Now — 2026-08-31

The privilege-query index audit is at its analysis step — see
**[`diagnostics/api-sql-profile/HANDOFF-index-contrast.md`](diagnostics/api-sql-profile/HANDOFF-index-contrast.md)**
first; it is standalone. Three identity tiers x two index states, all driven at
a measured **60,782 `grant_records`**, 0 non-2xx everywhere. **Nothing is
EXPLAINed yet at that volume**, so the Seq→Index contrast is banked but unread.
NEXT: correlate + EXPLAIN all six (`profile_queries.py --index-state
{present|absent} --explain --report`), toggling the index once between the
halves, then one combined report. No drives needed. Older handoffs
(`HANDOFF-privilege-scan.md`, `HANDOFF.md`, `HANDOFF-20260820.md`) are
superseded for the measurement; their Phase 3 is this task.

## Where the detail is

| read | when |
|---|---|
| [`.memory/roadmap.md`](.memory/roadmap.md) | what is done, what is next |
| [`.memory/active-issues.md`](.memory/active-issues.md) | before trusting a number or a tool (13 open, 5 resolved-but-instructive) |
| [`.memory/environments.md`](.memory/environments.md) | **before running anything** — local / dev / prod, and what must never run where |
| [`.memory/repository-map.md`](.memory/repository-map.md) | looking for where something lives |
| [`.memory/goal.md`](.memory/goal.md) | the standing objective and structural model |
| [`.memory/sessions/`](.memory/sessions/) | why a decision was made, including the wrong turns |
| [`.memory/completed.md`](.memory/completed.md) | finished structural work |

Task-specific handoffs live beside the code they describe, in
`diagnostics/api-sql-profile/HANDOFF-*.md`. They are written for someone
starting cold and are the right first read for a task; this file is the right
first read for the *project*.

## Rules for keeping this file useful

- **This file stays under ~40 lines.** Growth belongs in `.memory/`, not here.
  It was 198 lines against its own 150-line limit once, and a tracking document
  nobody finishes reading tracks nothing.
- **Update *Now* every session**, even when the answer is "unchanged".
- **A finding with a number goes in `.memory/roadmap.md`; the story goes in
  `.memory/sessions/`.** The wrong turns do not survive summarising and are the
  part most likely to be repeated.
