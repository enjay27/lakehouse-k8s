# Active Infrastructure State

**Index, not the record.** Only what would be *false* the moment it goes stale lives here;
everything else is a link into [`.memory/`](.memory/README.md).

## Now — 2026-09-16 late (refactored v5 live: one Lua filter, thread fields gone)

**Start here next session:** [`logging/HANDOFF-audit-log-next-2026-09-16.md`](logging/HANDOFF-audit-log-next-2026-09-16.md) — tasks C–K still apply; B done (rev 18 = hot-reload removal), A dropped (`#29`, Kade).

**Running:** `benchmarks-fluent-bit` pod `qr4br`, policy/report schema **v5**, Lua = refactor `#31` (sha `2fbcfa47c513f5a0`, parser merged into
FILTER 3, start-up records counted) + `#30` (no threadName/threadId/ndc in `polaris-logs-*`, rev 19). Verified on traffic 15:01Z: every
report count equal to the pre-refactor windows, detail 200/22/78. **`WINDOW_SECONDS` is still the verification value 30.**

**Rules:** a Lua-only change is `bash fluent-bit/apply-lua.sh`; Lua + values together is `apply-lua.sh --no-restart` → step2 → `helm upgrade`
→ step3. Never `kubectl apply -k` alone, never `--set-file`. Dev Tools response panel is not JSON — `devtools-json-fix.py` or curl.

**Next, in order:** (C) ISM policies (2.8). (D) 1800 s window via `apply-lua.sh` (2.5). (E) delete 30 s report indices — destructive, explicit OK (2.7).
(F) apply ISM (2.9). Then phase 3 (3.1 load test also measures `#31`'s C-side saving).

**Standing.** Polaris is not to be changed. **Verify against the running object, never an intent artifact.**

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
