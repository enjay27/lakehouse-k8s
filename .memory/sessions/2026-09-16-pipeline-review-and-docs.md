# 2026-09-16 (late) — whole-pipeline review, ISM handed over, docs brought current (Cowork)

Asked by Kade: "ISM is not needed in this task, Monitoring team will make it themselves. Time to review entire process and
source files. Check inefficiency, and provide better way and compare with current way. This should include all flow,
including core flow inside Fluent Bit. And need to up to date docs. After review is done, prepare update documents."

## What was done
- `logging/REVIEW-pipeline-2026-09-16.md` (commit `3c13fb0`): flow map of all three inputs through filters and router, P1–P12
  ranked, current-vs-proposed tables, a "kept on purpose" section, read-only measurements M1–M5. No config change.
- Docs: new handoff, `logging/README.md` index, proposal (ko) status/ISM/filter diagram/§9.1 order/§10–11, SCHEMA-report
  refactor section, CLAUDE.md Fluent Bit/OpenSearch bullets, values.yaml and kustomization.yaml **top-level comments only**,
  plan-todo (2.8/2.9 handed over), roadmap "current" block, repository-map, goal, environments, `#25`/`#27` headers,
  historical banners on the 09-03 spec and the 09-07 guide.

## How the numbers were obtained, and their limits
- Record shape at FILTER 3 was reconstructed from the tier-1 export (870 docs): tier-1 fields minus `kubernetes`,
  `environment`, `cluster`, `flb_tag`, `@timestamp`, renamed as FILTER 1 does. 16 keys / ~717 B; 7 keys removed by FILTER 4.
  This is JSON bytes, not msgpack, and not CPU.
- Detail/report shares are `_source` JSON bytes from the 15:01Z exports, not on-disk size (mappings + compression). Every storage
  proposal is gated on M5 (`_cat/indices`).
- No Fluent Bit binary could be obtained in Cowork (packages.fluentbit.io, cr.fluentbit.io, GitHub all 403), so no pipeline
  benchmark was run. CPU claims are deferred to phase 3.1.

## Wrong turns / things checked and dropped
- Considered merging the two tails of the Polaris file with `rewrite_tag` (one read, one decode). Rejected in the review: a
  tier-1 backlog would pause the shared tail and stall the audit stream.
- Considered flagging `Skip_Long_Lines On` as silent loss of long stack traces. Downgraded: the runtime splits lines at 16 KB
  before the tail's 32 KB buffer sees them; largest Polaris line in the export was 6.8 KB.
- A first draft claimed application lines are ~95 % of Polaris output (a 09-04 VictoriaLogs-era figure with DEBUG SQL).
  Replaced with the current window's number: 365 of 720.
- The proposal's own header still said "v4 applied, v5 not" while its status row said v5 verified. Both fixed.
