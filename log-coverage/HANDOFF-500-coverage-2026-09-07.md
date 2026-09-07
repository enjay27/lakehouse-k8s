# HANDOFF — 500 coverage and report schema v2

**Written 2026-09-07 to be read cold, at the start of a new `polaris-learning` session.**
Read this first; it is standalone. `MEMORY.md` is the right first read for the *project*, this
file for *this task*.

Everything described here is committed. `git log --oneline -4` should show:

```
de611e9  A broken storage config is a 422 here, not a 500 -- four routes measured, four closed
86eaf71  A handled 500 carries no stack trace, and reporting that as a lost one would ...
f3b2807  The gate said "unexpected fields" eight times and meant one constant ...
c1e0bcd  The 500 probe reported a pass by returning 200, and the ERROR path was never driven
```

---

## 1. Where this stands in one paragraph

The log-coverage notebook drives the Polaris API, reads what the Fluent Bit → VictoriaLogs
pipeline stored, and compares it against an oracle that runs the **deployed** Lua filter. Two
things happened this session. **The oracle was migrated from report schema v1 to v2** (it was a
version behind the filter, which aborted a run). **A deliberate 500 probe was built** — section
5c's provoker ladder and section 11c's assertions — because the ERROR path had never been driven
on purpose. The ladder ran and **provoked nothing**: on this build every route to a 500 that this
repo could think of returns a 4xx instead. That is a measurement, and it is the main open item.

---

## 2. Read order

1. This file.
2. `doc-500-coverage-scenario.md` — the 500 scenario in full: the ladder, every assertion, why
   each comparison is `==` or `>=`, and what each outcome means.
3. `PLAN-log-coverage-schema-v2.md` — the report schema and the harness work it asked for.
4. `PLAN-log-coverage-v3.md` — the retention policy. Unchanged by any of this.
5. `doc-log-coverage-results.md` — the last run's numbers (`1788759324`).

---

## 3. Settled — do not re-derive these

| | |
|---|---|
| **A broken storage config is a CLIENT error here** | endpoint refused → **422**; endpoint unresolvable → **422**; bucket missing → **400**; stale `entityVersion` → **409**. `IcebergExceptionMapper` catches and maps them (50 records in run `1788759324`). None reaches `errors_5xx` |
| **Polaris does not validate storage at catalog create** | `POST /catalogs` returns **201** with a nonsense endpoint. The failure appears at the first storage-touching call, which is why every rung creates the catalog *then* a table |
| **Wrong MinIO credentials are not client-reachable** | `storageConfigInfo` carries none; Polaris uses static server-side creds shared by every catalog. Changing them breaks every catalog and needs a restart, which voids a run |
| **`neg.500_null_pointer` is retired** | `create_catalog_no_endpoint` omits `endpointInternal` only, and this build falls back to `endpoint`. It returned 200 for three runs. `error-cases/09` is stale the same way and is untouched |
| **Stack traces survive, under four names** | `exception.exceptionType`, `exception.frames`, `exception.message`, `exception.refId` — 7 of 7 ERROR records. **VictoriaLogs flattens nested objects**, so query `exception.*`, never `exception` |
| **Traces accompany handled 4xx too** | 48 records in that run carried an exception field. An unhandled 500 is not the only source |
| **Schema v2 is validated against stored data** | 3 windows, per-window invariants OK on each, merged OK, zero-carry 19/19, decay clean, one summary per (host, window) across 152 consecutive windows with no gaps, `errors_5xx` numeric |

---

## 4. Open — in priority order

### 4.1 No known way to provoke an UNHANDLED exception  ← the blocker

Storage misconfiguration is exhausted. The only 500 ever seen on this cluster is the **PG-HA
read-after-write signature** on `create_namespace` / `create_view` — and it is a write that
**committed**, so it is not evidence about the unhandled path either. It cannot be driven.

Consequences, both real:

- `errors_5xx` has never been exercised by anything deliberate.
- `lc.trace_verdict`'s `handled` / `unhandled` / `absent` split is unit-tested and **has never
  had a real driven record to judge**.

Two candidates, neither tried:

1. **Induce replica lag deliberately** — pause WAL replay on a standby
   (`SELECT pg_wal_replay_pause();`), drive `create_namespace`, resume. This provokes the one
   500 signature this cluster is known to produce, on purpose. **Needs psql/kubectl, so it is a
   `local-k8s` action, not a notebook one.** Highest value: it turns an accident into a probe.
2. **Corrupt a table's `metadata.json` in MinIO** so the Iceberg parser throws somewhere
   `IcebergExceptionMapper` does not map. Speculative — it may well come back 4xx like
   everything else.

If neither works, the honest close is `PLAN-log-coverage-schema-v2` §4 option 3: state in the
results that ERROR-path coverage is **opportunistic and not repeatable**, and assert `errors_5xx`
only when a 500 happens to occur.

### 4.2 The fast-run settings are still live and TEMPORARY

`WINDOW_SECONDS: 30`, `Interval_Sec: 5` in `local-k8s/logging/fb-values.yaml`
(sha `d58b9203a8304030`). **Revert them together** when the run of record is taken — at the
deployed 1800 a full run is ~90 minutes, which is why they were lowered. Every assertion works
unchanged at either value; nothing hardcodes 30.

### 4.3 `resources_other` / `resources_other_distinct` appear in no `_msg`

Known, from the `local-k8s` side. The fix is a format string and it rides with the fast-run
revert, so the repo file stays byte-identical to the deployed ConfigMap until then.

---

## 5. What comes back from the `local-k8s` session

Kade is running `local-k8s` (results and coverage) before starting the new session here. Three
things from there change what this repo should do:

1. **Whether §4.1's replica-lag probe is feasible**, and if so the exact commands — they belong
   in a new rung in `lc.provokers_500`, or in `error-cases/` if they need kubectl.
2. **Whether the fast-run settings were reverted.** If yes, every timing in the notebook still
   holds but a full run costs ~90 minutes; take the run of record accordingly.
3. **Any change to `fb-values.yaml`.** Cell 0b compares `POLICY.schema_version` against
   `lc.SCHEMA_VERSION` and aborts on a mismatch — that is deliberate, and the abort message tells
   you to do `PLAN-log-coverage-schema-v2` §1.1 first.

---

## 6. Next actions, in order

1. **Read the `local-k8s` result** for §5's three questions.
2. **If replica-lag provocation is feasible, add it as a rung** in `lc.provokers_500` and re-run
   sections 5c / 11c. That single change closes §4.1.
3. **If it is not**, write the opportunistic-coverage statement into
   `doc-500-coverage-scenario.md` §8 and `doc-log-coverage-results.md`, and stop pretending the
   question is open.
4. **Take the run of record**, then **revert the fast-run settings**.
5. `error-cases/09_500_null_pointer` is still stale. Retire it the way `neg.500_null_pointer` was
   retired, in its own commit.

---

## 7. Gotchas that already cost time — do not rediscover them

- **Absent is not zero.** A missing field read as `0` reports PASS for a measurement nobody took.
  `check_500_window` returns `None` (VOID) rather than a pass when the error split is absent.
  This is the same shape as the `0 of 0 records carried an exception object` that was quoted as a
  pipeline property for three runs.
- **Never sum a hardcoded field list.** `merge_windows` did, and would have added `errors` and
  silently not `errors_4xx` **in the same row**. It derives from the row now. Third instance of
  this shape in this pipeline (`type_int_key`, the Prometheus timestamp parser, the merge).
- **Read `build_report`, not the error message.** Two harness bugs came from assuming a field
  name: the summary has **`errors_kept`, not `errors`**, and `distinct_resources` counts rows
  with traffic, not rows emitted.
- **The burst is only pure if the ladder fires.** When it does not, its own 4xx land in the
  window the checks call "pure-500". `lc.driven_status_mix` counts what was actually driven.
- **Correlation must be split by disposition.** A COUNTED call is findable only through whatever
  application lines it happened to emit; three probes reported as "not recovered" were correctly
  invisible. Only the KEPT half is an assertion.
- **A warm repeat of a successful read is invisible end to end** — no access line (rule 6) and no
  application line either. Cache warmth decides. The first `load_table` emitted one application
  line; the repeats emitted none.

---

## 8. How to run, and how to verify without a cluster

**The notebook** needs two port-forwards:

```bash
kubectl -n logging       port-forward svc/vlsingle-victoria-logs-single-server 9428:9428
kubectl -n datahub-hynix port-forward deploy/fb-polaris-shipper 2020:2020
```

Then `Restart & Run All`. Cell 0b aborts on any gate failure; that is the design.

**The tests, from a Cowork session** — this is new and worth keeping. The repo `.venv` is a macOS
build the bridge cannot execute, and the oracle tests used to skip for want of a Lua binary and
`fb-values.yaml`, so "37 skipped" was the normal result and a skip was indistinguishable from a
pass. Both are solved:

```bash
# on the device, for everything but the oracle tests
uv run --no-project --with pytest --with requests --with pandas --with numpy \
       --with openpyxl --with matplotlib pytest -q

# in the cloud container, for the ORACLE tests against the deployed filter
apt-get install -y lua5.4
# stage src/*.py, test_log_coverage.py, test_vlogs.py and local-k8s/logging/fb-values.yaml
FB_VALUES_PATH=<staged fb-values.yaml> python3 -m pytest test_log_coverage.py test_vlogs.py -q
```

Last green: **120 passed, 0 skipped** on the oracle suite; **710 passed / 1 failed** on the
device, the failure being the pre-existing `test_privilege_scan` renderer drift that `MEMORY.md`
already records.

`log-coverage/` needs read access to `~/hynix/local-k8s/logging/` for the oracle. In Cowork that
is a folder-access request; `FB_VALUES_PATH` overrides the search if the checkout is elsewhere.
