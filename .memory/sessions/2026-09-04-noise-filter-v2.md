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

---

# Second pass, same day — the flush report

Kade's proposal, and it is the right one: when Fluent Bit flushes, ship a **state report** to
VictoriaLogs — token request count, suppressed-read count, and a per-table request count so an
engineer can see hot and cold tables. Explicitly *not* per principal per table: "just per
Table". Windows on the wall clock at :00 and :30.

## Why it is worth more than the records it saves

Suppression that leaves no number behind is erasure. That is exactly why the three P1 items
above are deferred: capping repeated 404s or deduplicating collection listings would make real
volume invisible. **With a count in the report, capping stops hiding anything**, so this is the
prerequisite for the deferred work rather than a parallel feature. It is also roadmap step 7
(`log→metric downsampling`) arriving through the sink that already exists — there is no
VictoriaMetrics in this cluster, so the purpose-built `log_to_metrics` route needs a component
that does not exist.

## The mechanism, and the two things that make it work

A Lua filter cannot emit on a timer. Two facts, both checked before writing anything:

1. **The Lua filter's `record` return can be an array.** The manual: *"This value can be an
   array of tables ... and in that case the input record is effectively split into multiple
   records."* So one trigger yields the summary plus one record per table and per principal.
2. **Lua state is per filter instance.** So the trigger has to pass through *this* filter. A
   `dummy` INPUT tagged `polaris.report` does it, with `Match` widened to `polaris.*` on the
   noise filter and the OUTPUT only — `modify` and the access-log parser stay on
   `polaris.vlogs`, which is what keeps the report out of Polaris's own logging entirely.

**The tick rate is not the report period.** The filter emits only when
`floor(now/1800)` changes and drops every other tick, so over-ticking is harmless, the window
stays aligned to :00/:30 across a restart, and a 30s tick just bounds the edge skew at 30s.
Records arriving between a boundary and the tick that notices it land in the window just
closed — a summary, not a ledger, and said so in the source.

## Two margins, not the cross product

`table -> count` and `principal -> count`, never `(principal, table) -> count`. State is
|tables| + |principals|. Kade's call and the right one, but the consequence is written into
the source because it will otherwise be misread: **the report can never answer "who read which
table."** It answers which tables are hot and who is generating load. "Who read what" is
answered by the stored records — rule 6 keeps one per principal per object per KST day, which
is precisely what its key is for. The two changes are complements, not alternatives.

Table names are client-controlled — the coverage run hammered a table called `nope` twenty
times — so the per-table map is capped at 500 with an `__other__` bucket. Totals stay exact;
only the per-table detail is capped. That is the difference between this cap and the dedup cap:
overflow here loses detail, not truth, which is why this one could be decided unilaterally.

## What lands in VictoriaLogs

Its own stream, `{app="polaris-shipper-report", level="REPORT"}`, so `app:polaris` queries are
untouched. Three record types per window, tagged `report_type`:

```
app:polaris-shipper-report report_type:table     | stats by (table_path) sum(reads)
app:polaris-shipper-report report_type:principal | stats by (principal) sum(requests)
app:polaris-shipper-report report_type:summary   | fields window_start access_seen access_suppressed dedup_keys
```

`type_int_key` on the filter is not optional: without it every count ships as `482.0` and
numeric LogsQL misses it — the same trap as `http_status` on filter 2.

**And the summary carries `dedup_keys`**, the live size of the principal-keyed dedup table.
The cap policy that was passed back is now answerable from a week of data instead of a guess,
which is a better outcome than deciding it today would have been.

## Verification

56/56 (was 46/46). The report suite drives window boundaries through a `_now_override` test
hook — inert in the deployed pipeline, since the dummy INPUT never sets it — so the tests are
deterministic and nothing sleeps. Six requests in one window are asserted down to the field:
`access_seen 6, access_kept 4, read_suppressed 1, token_seen 2, token_suppressed 1,
distinct_tables 2, distinct_principals 2`, five records emitted, and the next window reports
zeros rather than repeating the last one.

Still NOT VERIFIED, and it is the one thing a test cannot reach: **that Fluent Bit 5.1.1 emits
an array return as separate records in this build, and that the `dummy` input's tag reaches the
filter.** Both are documented; neither has run here. First thing to check after the upgrade:

```
kubectl -n datahub-hynix logs deploy/fb-polaris-shipper | head
# then, 30 minutes later:
#   app:polaris-shipper-report | stats count()      -- expect >= 1 summary
```

If the array return does not split, the symptom is one record carrying a numeric-keyed blob
rather than N records; fall back to a single summary record with top-K tables inline.
