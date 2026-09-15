# Active Infrastructure State

**Index, not the record.** Only what would be *false* the moment it goes stale lives here;
everything else is a link into [`.memory/`](.memory/README.md).

## Now — 2026-09-14

**THREE OF RUN `1789370776`'s GATES WERE READ ONE ROW OFF, AND THE RUN SAID SO WRONG (`#26`).**
Report rows are stamped by a tick that fires **3.673s late**, constant (σ<2ms, 11 rows) and
undriftable because `Interval_Sec 5` **divides** `WINDOW_SECONDS 30`; the matrix fires every phase
**0.5s after the boundary**, so each burst lands in the previous row. The run called this an
inconsistent offset that *"no single offset can correct"* — **withdrawn**: `{-30: 5, 0: 1}` is one
skew measured against the label twice, the `0` being the only burst that did not start on a
boundary. Verified against the log index: `access_kept` == real-window access docs, **7/7**,
343==343. **Cheapest fix is in the notebook — start each phase ~5s past the boundary.**

**Gate 2 — `last_write_bytes`, which IS the feature — is STILL unanswered**, second run running.
Gate 4's two FAILs and Gate 2's VOID are all `#26`: the 403 did **not** fall to `__errors__`.

**Written and NOT running (`#25`), unchanged.** `fluent-bit/values.yaml` omits `min/max_record_time`
when nil; `logging/opensearch/polaris-report-template.json` types them `date`. **Both or neither,
Lua first** — with the template applied a `""` is rejected per item inside a `_bulk` that returns
HTTP 200. Apply with `logging/scripts/step9-report-index-template.sh`; not retroactive. The run's
"index mapping" item is this issue, not new work, and its nine-digits cause is still **asserted** —
a 3-call `_analyze`/probe-index test settles it without waiting a day.

**Next, in order.** (1) **`#26`'s cause is in the NOTEBOOK, not the pipeline** — every phase calls
`seconds_to_boundary(lag=0.5)` and fires into the tick's blind spot. Two edits, no cluster change:
[`logging/HANDOFF-notebook-window-attribution-2026-09-15.md`](logging/HANDOFF-notebook-window-attribution-2026-09-15.md).
(2) Re-drive Gate 2 in a named window. (3) Roll the Lua, then the template. (4) `#24` reproduced across two runs;
`exception.frames` is what is missing before it goes upstream. (5) `#18` `Id_Key sequence` indexes
nothing. (6) The **30s revert to 1800/30** is the cutover's last step — it also changes `#26`'s
arithmetic, so re-check the tick divides the window.

**Standing.** Polaris is not to be changed. **Verify against the running object, never an intent
artifact** — and a model that fits every count can still be wrong by an order of magnitude
(`sessions/2026-09-14-window-skew-review.md` §6).

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
