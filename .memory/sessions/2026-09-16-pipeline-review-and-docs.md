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

## Decisions and implementation (same night)
- Kade: apply P1 P2 P3 P4 P6/7 P8 P11/12. M1 unknown, M2 ~1,800 docs per notebook run, M3 yes, M4 yes (manual uninstall later), M5 not a
  concern (tier 2/3 only). Asked in-session: raw access line → keep, **renamed `message`**; `app` → drop.
- Chose to rename the report summary sentence `_msg` → `message` as well, for one name across both indices (flagged to Kade).
- Rename implemented by **not renaming** (Polaris' own key) instead of a second rename — one less operation, and the Lua reads `message`.
- P4 with M3 = yes: the JSON parser filters are redundant by construction (same decode as Merge_Log); the Polaris text regex is not
  provably dead, so `#32` carries a pre-roll count on its capture field `logger`.
- P8 first draft made report `message` `index: false`; changed to indexed text because step3's `exists` check on it would error on
  new indices. The `.keyword`-only design uses `text` + `index:false` so every existing `.keyword` query path survives across old and new
  daily indices; caveat recorded (bare-name queries find nothing on new indices).
- `json.dump` reformatted `polaris-report-template.json` (blank-line grouping lost) — content diff is the `_meta.v6`, `dynamic_templates`
  and `message` entries only.

## Roll result and final docs (same night)
- Kade rolled v6 and exported window 16:02:30Z (report + detail). Read: counts equal to v5 field by field over the same 67 row keys;
  detail field set exactly as designed; sizes −8 % / −7 % / −31 %. Not supplied: gate, step2/3/9/12 output, helm revision, tier 1.
- Docs brought to the rolled state: HANDOFF rewritten as the final start point (next: 1800 s), `#32` ROLLED, CLAUDE.md, MEMORY.md,
  README, review status, SCHEMA-report, proposal (ko) status/history/§10.1 6c, plan note, roadmap numbers, values header comment.
