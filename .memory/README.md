# The memory tree — which file takes what

`../MEMORY.md` is the index: under ~40 lines, its *Now* section says what is next and what is
written but not running. Everything with more detail lives here.

| file | takes |
|---|---|
| [`environments.md`](environments.md) | **read before running anything** — the one cluster, the three suite environments, ports, PVCs, secrets |
| [`goal.md`](goal.md) | the standing objective and what is actually deployed |
| [`active-issues/platform.md`](active-issues/platform.md) | cluster, charts, Fluent Bit, OpenSearch, PostgreSQL. Numbered `#1`–`#53`; *Open* first, then *Resolved, kept because they recur*, then *Standing constraints*. Configuration written but never applied lives here |
| [`active-issues/catalog.md`](active-issues/catalog.md) | the suite: coverage denominators, harness gaps, notebook defects. Unnumbered; a bare `#N` always means platform |
| [`active-issues/merge.md`](active-issues/merge.md) | what the 2026-09-21 merge deferred, and what has since closed |
| [`roadmap/platform.md`](roadmap/platform.md) · [`roadmap/catalog.md`](roadmap/catalog.md) | facts with numbers, milestones, and the verification assertions to run after a change |
| [`completed.md`](completed.md) | finished structural work |
| [`sessions/`](sessions/) | `YYYY-MM-DD-topic.md`, one per session, flat and chronological across both halves — the blow-by-blow, **including the wrong turns** |

## Rules

- **A fact with a number goes in `roadmap/`; the story goes in `sessions/`.** The wrong turns do not
  survive summarising, and they are the part most likely to be repeated.
- **Written is not live.** Anything not verified against the running cluster belongs in
  `active-issues/`, not `roadmap/`.
- **Check a number's denominator before quoting it.** The coverage denominator moved from 63
  operations / 286 cells to 65 / 297 when the 1.6.0 documents were vendored on 2026-09-21;
  `assert_denominator` hard-fails on drift. Re-record deliberately, never to turn a red run green.
- **A HANDOFF or PLAN is not memory.** It lives beside the code it describes, for someone starting
  cold. Link it; do not copy it.
- Session records name paths as they were. Documents deleted in the 2026-09-29 cleanup are indexed
  in [`../docs/DELETED-2026-09-29.md`](../docs/DELETED-2026-09-29.md).
