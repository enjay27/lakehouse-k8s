# HANDOFF — the capture dies when the notebook starts it, not when a terminal does

Written 2026-09-01, **diagnosis corrected 2026-09-02**. Standalone. Companion to
`PLAN-api-index-matrix.md` (design) and `RUNBOOK-api-index-matrix.md` (commands).
Read this one first.

The 2026-09-01 version of §0–§1 blamed a Polaris startup burst and a too-short
`settle_s`. Both were wrong, and the wrong fix (§1.4) would have passed its own
assertion. §1.2 lists what has been falsified by measurement so nobody re-tests it.

---

## 0. Where this stands, in one paragraph

Three identity drives completed cleanly and captured no SQL, and the cause is now
located: **the capture tail dies when the capture is started from notebook `03`,
and does not die when it is started from a terminal.** A CLI drive taken
2026-09-02 into a terminal-started capture recorded **859 log lines with the tail
alive**; every one of the seven notebook-started captures holds exactly **25
lines**. The runner, the parser, the streams and the log volume are all sound.
Drive from the CLI (§1.6) and the task proceeds today; the notebook defect is
separate and still open.

---

## 1. THE BLOCKER — located 2026-09-02, and every earlier theory was wrong

### 1.1 What the broken captures actually contain

Each of the seven `capture-*/polaris.log` written on 2026-09-01 holds **25 lines**
spanning under one second:

| line | content |
|---|---|
| 0–7 | root OAuth exchange, `POST /v1/oauth/tokens` → 200 |
| 2–22 | **19 real `DatasourceOperations query:` lines** — `entities`, `principal_authentication_data`, `grant_records` |
| 23 | **1,292,023 bytes** — `PolarisServiceImpl` logging `listCatalogs returning:` at INFO |
| 24 | the `GET /api/management/v1/catalogs` access-log line |

That is exactly the liveness probe in cell 9b (`_pc.list_catalogs()`), and nothing
after it. **The "1,311,11x bytes in all four runs" constant is that one oversized
line, not a startup burst** — the previous version of this section said startup
burst and was wrong. The parser is fine: 19 statements parsed, matched 1:1 by 19
`execute <unnamed>:` lines in `pg-*.log`.

By contrast the 2026-08-31 captures hold **2,371** and **2,170** lines (1,676 /
1,556 statements). The pipeline has worked; it stopped working on 2026-09-01.

### 1.2 Falsified, each by a measurement — do not re-test these

| theory | probe | result |
|---|---|---|
| the 1.29 MB line kills `kubectl logs -f` | capture, one `list_catalogs`, then 10 calls | tail alive, **+112 lines** |
| a rollout leaves the tail following the dead pod | restart, rotate, same probe | tail alive, **106 lines** |
| `settle_s` too short / logs buffering behind a burst | — | 19 statements parsed from a 0.25 s window |
| `parse_polaris_log(require_logger=True)` rejects abbreviated logger names | — | the lines parse; they are simply absent |
| `MultiStream` / `FileStream` position | — | pre-probe content is retained; the file stops growing |
| **the runner kills its own capture** | terminal `capture.sh rotate` + `drive_api_surface.py --drive --case admin --capture <dir>` | **859 lines, tail alive** |

The 859-line drive is the decisive one. Same runner, same `--capture` argument
cell 9c passes, same cluster, and it worked — including two oversized
`listCatalogs` dumps mid-sweep (548 KB → 1.88 MB → 2.46 MB) that the tail sailed
straight through.

### 1.3 What is left, and it is one difference

Cell 19 starts the tail through the notebook's `sh()` helper —
`subprocess.run(cmd, shell=True, capture_output=True)` from the Jupyter kernel.
The working run started it from an interactive shell. Nothing in Python kills
anything (`pkill|killpg|.kill()|terminate()|SIGKILL|os.kill` across `src/` and
this directory returns nothing), and the only `capture.sh stop` is at the top of
cell 19, *before* the start. So the tail is started under a different parent and
stops within a second of the gate's own probe.

**The probe that closes it, and it needs no drive and no restart:** run cell 19,
then run NOTHING and poll `polaris.log` and the tail PID for 60 s. If the tail
dies while idle, the fault is in how `sh()` backgrounds it, and the fix is to
detach the tails (`setsid` / `nohup`, or `start_new_session=True`) rather than to
change anything about the drive.

### 1.4 The previous §1.1 was NOT the fix

It proposed asserting `rec.sql_count > 0` on a preflight `list_catalogs`. That
call is precisely the one that still works in every broken capture — it is line
23 of all seven. The assertion would have passed and the drive would still have
produced 43 empty rows. Worth adding as a general guard; useless against this
fault.

### 1.5 The gate that WOULD have caught it

Liveness must be re-checked **per operation**, not once before the sweep.
`_TraceContext.__exit__` already reads the stream; a 2xx operation that yields
zero new bytes is an assertable condition and would have failed on operation 2
rather than after the 43rd. Add a `.pids` reap check (`kill -0` on each recorded
PID) at drive end too — it would have flagged all seven runs.

### 1.6 Unblocked path — drive from the CLI

Proven working 2026-09-02. Per case, from a terminal:

```bash
restart_polaris                              # RUNBOOK §4
./capture.sh pgon                            # rotate alone does NOT enable it
./capture.sh rotate capture-<case>-$(date +%H%M%S)
CAP=$(ls -td capture-<case>-* | head -1)
uv run python drive_api_surface.py --drive --case <case> --capture $CAP
```

**Pass `--capture` explicitly.** `find_capture_dir()` selects the `capture*`
directory whose `polaris.log` has the newest mtime and requires it non-empty, so a
freshly-started capture is not a candidate until something writes to it — it can
silently choose a stale directory from a previous run. There are 15 such
directories here.

### 1.7 A separate defect in `capture.sh`, found on the way

`do_stop` reaps strays with `pgrep -f "kubectl.*-n $NS.*logs.*-f"`, which matches
**every** such tail on the machine, not only the ones this capture started. A
`stop` or `rotate` for one case kills a live capture belonging to another. Real,
independent of the bug above, and worth fixing in the same change.

## 2. What the reports must contain when this is fixed

Kade's requirement, verbatim in shape:

```
### `iceberg.get_config`

- `GET /v1/config` → **200**
- wall 94 ms · 0 statements · 0 object ops · entity access: N/A
- tables: —
- QUERY (select from table ...)
```

Two additions per API:

**(a) The QUERY.** `api_report.render_statements` ALREADY emits this — full SQL
in a fenced block plus its `params:` line, per statement. It emitted nothing
because `rec.sql` was empty. **No renderer change is needed for the QUERY; fix
§1 and it appears.** Confirm with `test_api_report.py`, whose round-trip test
covers exactly this path.

**(b) The EXPLAIN result, per API.** This is new. `explain_api_matrix.py`
produces `runs/apiexplain-<case>-<stamp>.json` holding, per (SQL, params) pair:
`scans`, `seq_scanned`, `indexes_used`, and the full plan. The renderer must
join those onto the statements it prints — the pair is the key, and
`query_profile.parse_api_statements` already keys on it. Suggested per-statement
block:

```
**[3]** `grant_records` · SELECT · no timing

```sql
SELECT ... WHERE grantee_id = ? AND realm_id = ? AND grantee_catalog_id = ?
```
params: `1002, POLARIS, 0`

EXPLAIN (index present) — Index Scan using idx_grant_records_grantee, 3 buffers
EXPLAIN (index absent)  — Seq Scan on grant_records, 572 buffers, 60,783 rows removed
```

Both index states on the same statement is the point; that contrast is the
finding. Add a per-API rollup line too (`per_api` in the run JSON already has
`seq_scanned` / `indexes_used` / `uses_index_only`).

---

## 3. Measured facts — carry these into the report

### 3.1 The identities, and what they actually exercised

| case | identity | token scope | footprint | permitted / refused / other |
|---|---|---|---:|---|
| unauthorized | `zerograve_principal` | own role | **1** | 2 / 22 / 19 |
| authorized | `authz1_principal` | own role | **78** | 28 / 5 / 10 |
| admin | `admin1_principal` | **`service_admin`** | 3,377 (ceiling) | see §3.4 |

**Footprint is not what the token carries.** `--footprint` walks EVERY role a
principal holds; a token is scoped to ONE. 3,377 is admin's ceiling, not what its
grantee lookup resolves. Say which in the report.

**`authz1` is an outlier in its own tier** — 78 against the other 99 identities'
52, because `--authorize` granted it rights on the shared probe catalog. Quote
the authorized case at 78.

### 3.2 The authorization boundary, measured

Authorized (catalog-scoped) is refused **exactly** the five service-scoped
operations: `mgmt.create_principal`, `create_principal_role`, `list_catalogs`,
`list_principal_roles`, `list_principals`. Every catalog-scoped `mgmt.*`
succeeded. Independently reproduces the 2026-08-24 probe's finding through a
different fixture and identity.

Admin is **not** a superset: `mgmt.reset_principal_credentials` → **403**.
`service_admin` reads every management API and is refused credential vending;
the catalog-scoped owner is the reverse. Neither tier contains the other, and
that is the headline the three-identity design exists to produce.

### 3.3 Statuses that are not authorization outcomes

- **404 is usually SECOND-ORDER.** A refused `create_*` leaves every dependent
  operation addressing an entity that does not exist. 19 in the unauthorized
  case, 10 in authorized, and they collapse as authority rises. They still issue
  SQL — entity-lookup-miss paths — and their statements belong in the report,
  labelled as such and never as denials.
- **500 on `create_view` and `create_namespace` is a WRITE THAT SUCCEEDED.**
  Kade: a database sync error. Corroborated independently — `load_view`,
  `head_view`, `rename_view` and `drop_view` all answered 2xx in the same run,
  which is impossible unless the create committed. Known PG-HA read-after-write
  signature; `_attempt` exists because of it.
- **Two operations succeed for a ZERO-grant principal**: `iceberg.get_config`
  (200) and `iceberg.report_metrics` (204). `get_config` is plausible;
  `report_metrics` accepting a write-shaped call from an identity with no rights
  is worth verifying against the source before it is called a finding.

### 3.4 Re-drive admin

The admin run in `reports/` was taken with the token scoped to
`admin1_principal_role` instead of `service_admin`, and is a copy of the
unauthorized case. `resolve_identity` is fixed (2026-09-01) but **the report on
disk is from before the fix** — the 2026-09-01 15:41 file shows the corrected
run. Verify the scope line reads `PRINCIPAL_ROLE:service_admin` before trusting
any admin report.

### 3.5 Volume at drive time

`entities` 9,634 · `grant_records` 60,819 · `policy_mapping_record` **0** ·
`principal_authentication_data` 1,108.

`policy_mapping_record` is empty and stays empty: a mapping row is written when a
policy is ATTACHED to a target, not when one is created (12 policy entities
exist). Its **2 statement texts are NOT MEASURABLE at this fixture** — report
them as that, never as a plan, because every plan against an empty table looks
identical.

---

## 4. The sweep, once statements exist

Unchanged from the plan. Per case, both index states:

```bash
uv run python explain_api_matrix.py --case <case> --index-state present \
    --matrix reports/doc-api-sql-matrix-<case>-<stamp>.md
# then drop_grantee_index.py + ANALYZE, repeat with --index-state absent, then restore
```

`--index-state` is checked against live `pg_indexes` and refuses on a mismatch.
`analyze=False` throughout: plain EXPLAIN never executes, which is what makes the
write half askable and leaves no clock to misquote.

Expect ~115 (SQL, params) pairs per case from a full matrix; 112 of 115 replay
in the archived root matrix, the other 3 being redacted secret-table parameters
that never will.

---

## 5. Guards — every one cost something this session

- **Compare distributions ACROSS runs.** Three separate faults were caught only
  this way, and none from a single run's output: two runs matching exactly is a
  fixture fault, not a finding. Each individual run looked perfect — 43/43,
  zero errors, healthy capture.
- **Bytes are not evidence, and neither is content right after a restart.** §1.
- **A summary that prints only the buckets you thought of hides the rest.**
  `permitted 2 refused 22` omitted 19 operations. `DriveResult.other` and
  `.distribution` now exist because of it.
- **Errors are not refusals.** 43 `IsADirectoryError` reported as errors; had
  they been collapsed into refusals it would have read as a flawless
  unauthorized pass.
- **A token is scoped to ONE principal-role.** An identity holding two gets the
  one it asked for. Never `PRINCIPAL_ROLE:ALL` for a non-root principal — 200
  with no effective role, then 403 everywhere.
- **A catalog-scoped principal cannot act on a catalog it does not own.** Grant
  it with `--authorize` first, or it reads as unauthorized.
- **Never write a secret into `os.environ`** — it persists for the kernel and
  the next case authenticates as the wrong identity. `sh(env=...)` overlays
  per-call. Never print one into a tracked notebook's output either.
- **`capture.sh rotate` does not enable statement logging.** `pgon` is separate.
  `PGDUR=1` adds durations.
- **`--footprint` said "uniform" for `[52, 78]`.** Fixed. A false green light is
  worse than a false alarm: nobody investigates it.

---

## 6. Definition of done

- A tracer-level preflight proving SQL is read, in the runner and cell 9b.
- Three reports where every API lists its statements with full SQL and params —
  the QUERY Kade asked for.
- Six `apiexplain-*.json` (3 cases × 2 index states), each recording the live
  `pg_indexes` state it was taken in.
- Reports carrying the EXPLAIN result per statement, both index states, plus a
  per-API rollup.
- `policy_mapping_record`'s 2 texts marked not-measurable; INSERT texts accounted
  for, not planned (`INSERT … VALUES` plans to a Result node — no scan, no index
  to detect).
- §3's measured facts stated, including that admin is not a superset.
- `black` (last), `isort`, `pytest` green — 183 across five suites.
- `MEMORY.md` *Now* + `.memory/` updated; one commit, message stating the finding.
