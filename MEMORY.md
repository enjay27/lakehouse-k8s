# Active Infrastructure State

**Index, not the record.** Only what would be *false* the moment it goes stale lives here;
everything else is a link into [`.memory/`](.memory/README.md).

## Now — 2026-09-09

**TIER 2 IS FIXED AND §3 IS ANSWERED.** Root cause: **`multiline.parser cri` alone** on the tier 2
tail; `docker, cri` works. Post-fix documents in `polaris-logs-*`: **4,403/4,403 carry
`loggerName`, 0 carry `log`**. Health check for this chain is the `unwrap -> rename` byte delta —
**12.00 B/rec = failing, 5.00-7.00 = working**, now 6.97. Mechanism unknown; measurement
unambiguous.

**Stdout carries the same access-log set as the file: `access_seen` 265 == 265, `access_kept`
126 == 126** on matched windows, one burst, both releases running. Per-window diffs sum to zero —
boundary assignment, not loss. **The earlier "file 270, stdout 0" is VOID**: it was measured
through a filter that was not parsing. Detail:
[`sessions/2026-09-09-stdout-not-equivalent`](.memory/sessions/2026-09-09-stdout-not-equivalent.md).

**Next, in order.** (1) Remove the five heartbeat probes — scaffolding; probe 5 duplicates tier 2's
tail exactly. (2) `#18` `Id_Key sequence` drops every record it should dedup; `#19` `_bulk`
responses exceed the output buffer and chunks are discarded — both live, both tier 1, neither
caused by the cutover. (3) Step 7, the `fb-polaris-shipper` uninstall — **now unblocked but
`helm uninstall` needs authorisation at the moment of execution**, and it destroys the ability to
repeat the 265==265 measurement. (4) The **30s window revert to 1800/30** stays the cutover's last
step and final gate (§4.1); tier 3's long ISM policy is blocked on it.

**Deploying is three facts, not one.** `helm upgrade` updates the ConfigMap; a DaemonSet does
**not** roll on a ConfigMap change; `rollout restart` alone restarts the OLD config. Both halves
report success either way. Use `logging/scripts/step5-probe-apply-verify.sh --apply`, which
verifies the ConfigMap *and* the running process. See `#20`.

**Standing.** Polaris is not to be changed. **Verify against the running object, never an intent
artifact.** And **an instrument that reads correctly while idle can still misread under load** —
this week produced four: `grep -c` over a one-line Lua, a ratio gate that inverted its own verdict,
a summary window that shrank exactly when traffic arrived, and a published PASS threshold that was
simple arithmetic done wrong.

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
