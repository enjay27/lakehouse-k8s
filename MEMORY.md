# Active Infrastructure State

**Index, not the record.** Only what would be *false* the moment it goes stale lives here;
everything else is a link into [`.memory/`](.memory/README.md).

## Now — 2026-09-10

**v3 IS DEPLOYED AND STILL UNPROVEN.** The API matrix (run `1789026666`: 63 operations, 286 cells,
0 transport errors) drove the whole API surface for the first time, and **Gate 2 —
`last_write_bytes`, which IS the feature — came back VOID**, on a window of zero-carry rows. The Lua
sets the field: **58/58** in `logging/scripts/test-schema-v3.lua` under a real `lua5.4` against
today's values file. Next step is to drive ONE commit and query THAT window, not to touch the filter.

**Written and NOT running (`#25`).** `fluent-bit/values.yaml` omits `min/max_record_time` when nil;
`logging/opensearch/polaris-report-template.json` types them `date`. **Both or neither, Lua first** —
with the template applied a `""` is rejected per item inside a `_bulk` that returns HTTP 200. Apply
with `logging/scripts/step9-report-index-template.sh`; not retroactive, so `polaris-report-2026.09.10`
and earlier stay `text` and take no date maths. Also unrolled: the heartbeat-probe removal.

**A gate that matches nothing PASSES.** Three of the guide's gates used `{"term": {"<text field>":
…}}` — matched against the analyser's output, so `POST` looks for `post` and can never match. Fixed
with `.keyword` throughout, plus: **row-level gates pin `window_start`**, because zero-carry rows
make the newest documents for a key its zeros. Third instrument this fortnight that read correctly
while idle and lied under load. `errors_5xx` is meanwhile **drivable through the API alone** (`#24`).

**Next, in order.** (1) Roll the Lua, then apply the template — that order. (2) Re-drive Gate 2 in a
named window. (3) `#18` `Id_Key sequence` indexes nothing, so tier 1 has no dedup at all — a design
call, not a bug to fix blind. (4) `#23`, two raw `log` docs in 4,576, low. (5) The
`fb-polaris-shipper` uninstall needs authorisation at the moment of execution and destroys the
ability to repeat the 265==265 measurement. (6) The **30s revert to 1800/30** is the cutover's last
step and final gate (§4.1); tier 3's long ISM policy is blocked on it.

**Standing.** Polaris is not to be changed. **Verify against the running object, never an intent
artifact** — and deploying is three facts, not one (`#20`): use
`logging/scripts/step5-probe-apply-verify.sh --apply`.

## Where the detail is

| read | when |
|---|---|
| [`.memory/environments.md`](.memory/environments.md) | **before running anything** — context, namespaces, ports, and the no-cluster-reach constraint on Cowork sessions |
| [`.memory/active-issues.md`](.memory/active-issues.md) | before trusting a value or a runbook |
| [`.memory/roadmap.md`](.memory/roadmap.md) | what is next, and the PostgreSQL verification assertions |
| [`.memory/repository-map.md`](.memory/repository-map.md) | looking for where something lives, or which duplicate values file is current |
| [`.memory/goal.md`](.memory/goal.md) | the standing objective and the structural model |
| [`.memory/sessions/`](.memory/sessions/) | why a decision was made, including the wrong turns |
| [`.memory/completed.md`](.memory/completed.md) | finished structural work |
| `logging/polaris-logging-architecture-spec.md` | the design the log pipeline is being built against, and its §7 LogsQL recipes |

## Rules for keeping this file useful

- **Under ~40 lines.** It reached 80 by accumulating,each session, a digest of findings
  already filed in `.memory/`. **A paragraph summarising a file that exists does not belong
  here.** *Now* carries what is next and what is written but not running; nothing else.
- **Update *Now* every session**, even when the answer is "unchanged".
- **A fact with a number goes in `.memory/roadmap.md`; the story goes in
  `.memory/sessions/`.** Configuration that is written but not applied goes in
  `.memory/active-issues.md` — in this repo that distinction is the whole game.
