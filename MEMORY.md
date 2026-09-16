# Active Infrastructure State

**Index, not the record.** Only what would be *false* the moment it goes stale lives here;
everything else is a link into [`.memory/`](.memory/README.md).

## Now — 2026-09-15

**`#26` IS FIXED — run `1789460891` agrees with the log index by label** (errors 2/251 == 2/251,
resource == principal totals). But the tick **does drift** (3.673s → 2.77s, same pod), and the run put
**all phases in one window**, so per-phase gates read the whole matrix.
[`sessions/2026-09-15-rerun-1789460891-review.md`](.memory/sessions/2026-09-15-rerun-1789460891-review.md).

**Gate 2 — on a table it cannot be answered from `polaris-logs-*`:** a 2xx catalog POST is counted,
never stored (rule 5'). `probe_tbl` says `last_write_bytes 1941`; the record to compare is in
`k8s-logs` only. 12/12 checkable (management/PUT) rows match.

**Written and NOT running (`#25`), unchanged.** `fluent-bit/values.yaml` omits `min/max_record_time`
when nil; `logging/opensearch/polaris-report-template.json` types them `date`. **Both or neither,
Lua first** — with the template applied a `""` is rejected per item inside a `_bulk` that returns
HTTP 200. Apply with `logging/scripts/step9-report-index-template.sh`; not retroactive. The run's
"index mapping" item is this issue, not new work, and its nine-digits cause is still **asserted** —
a 3-call `_analyze`/probe-index test settles it without waiting a day.

**Next, in order.** (1) Gate 2 against `k8s-logs`: last 2xx `POST …/tables/probe_tbl` in
[17:28:30, 17:29:00) KST, `response_size` == 1941? Fix the guide's query. (2) One window per phase. (3) Roll the Lua, then the template. (4) `#24` reproduced across two runs;
`exception.frames` is what is missing before it goes upstream. (5) `#18` `Id_Key sequence` indexes
nothing. (6) The **30s revert to 1800/30** is the cutover's last step — it also changes `#26`'s
arithmetic, so re-check the tick divides the window.

**Policy v4 VERIFIED 2026-09-16 (`#27`)** — matrix window replayed from the raw tier-1 copy: 64 rows × 30 fields, 0 mismatches; Gate 2 passed for the first time. Every upgrade needs `--set-file`. **Next (TODO phase 1):** apply report template (1.1), write detail template (1.2), one test phase per window (1.4).

**TODO plan (2026-09-16):** [`logging/PLAN-audit-log-todo-2026-09-16.md`](logging/PLAN-audit-log-todo-2026-09-16.md) — phase 0 verify v4 (matrix-window export, Gate 2 in `k8s-logs`), 1 templates + one phase per window, 2 next Lua bundle (404 policy, register, 1800s) + ISM, 3 load test and GitOps port.

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
