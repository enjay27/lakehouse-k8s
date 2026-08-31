# Active Service Testing State

**Index, not the record.** Current state below; everything else is a link into
[`.memory/`](.memory/README.md). If you are picking this up cold, read the
handoff named in *Now* — it is standalone.

## Now — 2026-08-31

**Read [`HANDOFF-pass-b.md`](diagnostics/api-sql-profile/HANDOFF-pass-b.md) first — it is standalone.**

Done — the index contrast, reported in [`doc-grant-index-contrast-20260831.md`](diagnostics/api-sql-profile/doc-grant-index-contrast-20260831.md):
at 60,784 `grant_records` the grantee lookup **Seq-Scans 572 pages, discarding 60,783
rows to return 1**; with `idx_grant_records_grantee`, an **Index Scan of 3 pages**
discarding none. Three fixtures agree, 29 of 29 read ops affected, a 403 pays the same
7-statement prelude in both states. A page-access ratio, **not** latency — logging was on.

Next — Pass B (latency, logging off), **blocked** on one unexplained thing: the
index-absent passes issued *more statements*, not just slower ones (122,010 vs 109,010 on
`user`), and ran first, so a naive Pass B would report `index + warmth` as the index. The
handoff's step 1 settles it offline from the banked captures, no cluster.
`HANDOFF-index-contrast.md` is complete and superseded.

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
