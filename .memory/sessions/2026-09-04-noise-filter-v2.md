# 2026-09-04 — the policy runs, and it turns out to govern 4.5% of the volume

Input: two documents from `polaris-learning/log-coverage` — the second coverage run
(`doc-log-coverage-results.md`, run `1788498536`) and the project README. Task: prepare an
enhancement to the Fluent Bit filter. Plan-first per `.claude/skills/workflow-control`;
P0 approved, P1/P2 deferred.

## What the run actually said, which is not what its own summary said

The report's headline is the coverage matrix. Reading the matrix instead of the prose:

```
access-log records stored   90
application lines stored  1928
                          ----
                          2018   (the report says 2,026 stored; the rest is uncorrelated)
```

Rules 1 and 2 keep every application line untouched. So the entire policy — five rules, two
Lua state machines, thirty test cases — decides the fate of **90 records in 2,018**, and its
34 drops removed **1.7%** of the volume. That is the finding. It does not make the policy
wrong; it makes it an *audit-fidelity* control that was being discussed as a storage control.
`active-issues.md` #5b had already named the real storage lever (DEBUG SQL records, ~1.5KB
each, to be **routed** not turned down) and it was not connected to this until the columns
were added up.

**A second thing the report is inconsistent about, left open on purpose.** Question 5 says
"34 of 122 calls produce no record at all", but those 34 calls carry 628 application lines in
the matrix, and `90 + 1,928 ≈ 2,026` says that column is read from VictoriaLogs. If it is,
a dropped `create_principal` is not invisible — it loses its access-log line (method, path,
status, principal) and keeps thirteen correlated records. That changes how the drop should be
described, not whether it should be fixed. Filed in #14a rather than resolved by argument.

## What changed (policy v2, `logging/fb-values.yaml`)

Four changes, all inside `polaris_noise_filter` and the `[FILTER]` blocks. None of them is
running: this is #13's shape again, entered knowingly, one `helm upgrade` away.

**1. Rule 5 inverted.** It was a keep-list — POST on the table/view API kept, every other
successful POST dropped — and *its own comment said the drop was aimed at the OAuth token
endpoint*. The blast radius was never bounded to it, and the run measured the bill: eight
endpoints with no access-log record, including `reset_principal_credentials`. A credential
reset leaving no trace is the exact opposite of what this pipeline is for. Now every POST is
kept except `ONCE_PER_DAY_POST_PATTERNS`, currently `/oauth/tokens$` alone — and *that* is
kept once per principal per KST day rather than dropped outright, so "who authenticated
today" is answerable while per-connect traffic stays bounded. Kade's call, from three options.

**2. The dedup key carries the principal.** It was `method .. " " .. path`. The second
principal to read a table today was therefore invisible. On an authorization catalog, "who
read what" is the question the access log exists to answer, and the policy was discarding it
to save a record.

**3. The dedup key drops the query string.** `probe_tbl`, `?snapshots=refs` and
`?snapshots=all` were three keys for one table in one day, and Iceberg clients vary that
parameter constantly. `test-polaris-filters.py:90` asserted this as KEEP — a deliberate
decision, now reversed with the run behind it. `api_path` itself is untouched: it stays the
raw path, which is what you read when a parse looks wrong.

**4. `Alias` on all four filters.** Question 6 of the report reads
`fluentbit_filter_drop_records_total` delta **unknown** — two `lua` filters are
indistinguishable in Fluent Bit's metrics without one. Zero behavioural change, and it turns
the notebook's own unanswerable question into a number.

## What was deliberately not done

Everything in the P1/P2 table in `active-issues.md` #14, each with a measurement behind it:
collection listings are not deduplicated at all (20 identical `GET .../tables` → 20 records),
repeated 4xx have no cap (20 identical 404s → 20 records), `report_metrics` is the one POST
kept unbounded, and `%D` / stack traces are Polaris-side where **Polaris is not to be
changed** (#11).

**And one decision was passed back rather than made.** Keying on the principal multiplies the
dedup table by distinct principals per day, in the shipper's 512Mi, and nothing bounds it —
before or now. A placeholder `DEDUP_MAX_KEYS = 50000` fail-open guard stands in: above it the
filter stops deduplicating and keeps everything. Fail-open can only store more records, never
lose one, so it cannot surprise anyone while the real policy is decided. It is marked
PLACEHOLDER in the source. Replacing it is the next small task.

## Verification

`python3 logging/scripts/test-polaris-filters.py` — **46/46** (was 30/30), run on the device.
It extracts the Lua out of `fb-values.yaml` and executes it, so the suite cannot drift from
what ships. Fourteen new cases: the eight mutations that used to vanish, three token cases
across two principals, and five that pin the principal-and-no-query dedup key.

`helm lint` and `--dry-run` were **not** run: a Cowork session has no cluster reach. The YAML
parses and `luaScripts` still renders one key, which is all this session can assert.

## Two things for whoever runs the upgrade

- Sample `fluentbit_filter_drop_records_total{name="polaris_noise_filter"}` **before** it, or
  the first delta has nothing to compare against.
- The tail DB is still on an `emptyDir` (#5b), so the upgrade replaces the pod,
  `Read_from_Head true` replays the file, and the dedup buckets start empty. Expect a burst.
- Then re-run `polaris-learning/log-coverage`. Its characterization test is **built to fail**
  on a policy change; read the diff, confirm the change was intended, and update the test and
  `doc-log-coverage-results.md` together.
