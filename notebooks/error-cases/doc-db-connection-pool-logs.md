# Database Connection Pool Unavailable — Log & Alert Reference

Reference doc for the P0 "DB Connection Pool Unavailable" monitor
(`error-cases/opensearch-monitor-alert-guide.md`, Monitor 7). Covers the two
known root causes, what actually shows up in the logs for each, how the
OpenSearch monitor finds it, how to fix it, and what gets sent when it fires
and when it clears. Scope is deliberately narrow — connection-pool
availability only, per 2026-07-02 request (other error types are out of
scope here; see `error-cases/opensearch-alerts.md` /
`opensearch-monitor-alert-guide.md` for those).

**Revised 2026-07-03** after the first live runs against real NB15/NB27
output surfaced three problems with the first version: (1) the query was
broad enough to catch unrelated logs, (2) there was no "resolved" message —
these are infra-owned failures, not something a Polaris engineer fixes in
app code, so whoever gets paged needs an explicit all-clear, and (3) a
Vert.x concurrency warning was being lumped in with real DB-unavailable
signal even though the client already sees that failure and can retry on
its own. All three are addressed below.

Both cases share: index `k8s-logs-*`, container
`kubernetes.container_name.keyword: benchmarks-polaris`, logger
`loggerName.keyword: io.agroal.pool` (now a **mandatory** clause, not one
should-option among several — see "Query strategy").

---

## Case A — PostgreSQL / pgpool Down Entirely

Root cause: the `pgpool` (or `postgresql`) pod is unreachable — scaled down,
crashed, network partition, etc. Reproduced live in
`error-cases/15_FATAL_connection_pool_error.ipynb` by scaling
`benchmarks-postgresql-postgresql-ha-pgpool` to 0 replicas. Run twice live
(2026-06 and 2026-07-03) with consistent results.

### Actual logs from Polaris (live-captured)

**Signal 1 — Agroal detects the outage proactively**, before any API request
hits it (background connection validation). From the 2026-07-03 run, 10
consecutive WARNs about a second apart:

```
[2026-07-03T04:44:09.934Z] WARN
  logger  : io.agroal.pool
  message : Datasource '<default>': Connection to
            benchmarks-postgresql-postgresql-ha-pgpool:5432 refused. Check
            that the hostname and port are correct and that the postmaster
            is accepting TCP/IP connections.

[2026-07-03T04:44:08.911Z] WARN   (same message, repeats every ~1s)
[2026-07-03T04:44:07.883Z] WARN   (same message)
[2026-07-03T04:44:06.860Z] WARN   (same message)
[2026-07-03T04:44:05.836Z] WARN   (same message)
[2026-07-03T04:44:04.811Z] WARN   (same message)
[2026-07-03T04:44:03.787Z] WARN   (same message)
[2026-07-03T04:44:02.764Z] WARN   (same message)

[2026-07-03T04:44:01.745Z] WARN
  logger  : io.agroal.pool
  message : Datasource '<default>': Closing connection in incorrect state
            VALIDATION
```

This is the key operational fact: **Agroal's background validation thread
logs the failure on its own schedule, independent of traffic.** The monitor
can catch this before a single user request fails.

Note on the last line above (`Closing connection in incorrect state
VALIDATION`): this one is **deliberately not matched** by the tightened
query — see "Query strategy" below. It's ambiguous on its own (routine pool
churn can produce similar-looking messages); the tightened query only fires
on the unambiguous `connection refused` phrase.

**Signal 2 — repeating cycle while the outage persists** (health check +
Agroal, repeats roughly every 10s, consistent across both live runs):

```
[2026-07-03T04:45:39.018Z] WARN  io.agroal.pool
  Datasource '<default>': Connection to
  benchmarks-postgresql-postgresql-ha-pgpool:5432 refused. ...

[2026-07-03T04:45:35.951Z] INFO  io.smallrye.health
  SRHCK01001: Reporting health down status: {"status":"DOWN","checks":
  [{"name":"Database connections health check","status":"DOWN",
  "data":{"<default>":"Unable to execute the validation check for the
  default DataSource..."}}]}
```

**Client-side symptom** (what a caller sees, not a k8s pod log). Varies by
how deep into the outage the request lands:
```
Early in the outage: 401 (token/principal lookup itself needs a DB read)
Once fully down:     ConnectionError: HTTPConnectionPool(host='192.168.139.2',
                      port=8181): Max retries exceeded with url: ...
```

**Caveat (why the query was tightened):** the original broad query's should
-clauses (bare `loggerName: io.agroal.pool` as one of several OR'd options,
plus generic terms like `SQLException`) returned unrelated app-level noise
in testing — e.g. `IcebergExceptionMapper` messages about a leftover
non-empty test catalog from the harness's own cleanup step, nothing to do
with the DB pool. Fixed 2026-07-03 (see "Query strategy").

### Query strategy (OpenSearch monitor)

**Tightened 2026-07-03.** `loggerName: io.agroal.pool` moved from a
should-option into a mandatory `must` clause, and message matching switched
from `match` to `match_phrase` on only proven substrings. The query also
now computes a `current` (now-1m..now) and `previous` (now-2m..now-1m)
`date_range` aggregation instead of a plain hit count, so the same query
backs both the ALERT and RESOLVED triggers (see below):

```json
{
  "query": {
    "bool": {
      "must": [
        {"range": {"@timestamp": {"gte": "now-2m"}}},
        {"bool": {
          "must": [
            {"term": {"kubernetes.container_name.keyword": "benchmarks-polaris"}},
            {"term": {"loggerName.keyword": "io.agroal.pool"}},
            {"bool": {
              "should": [
                {"match_phrase": {"message": "connection refused"}},
                {"match_phrase": {"message": "too many clients already"}},
                {"match_phrase": {"message": "broken pipe"}}
              ],
              "minimum_should_match": 1
            }}
          ]
        }}
      ]
    }
  },
  "aggs": {
    "current":  {"filter": {"range": {"@timestamp": {"gte": "now-1m"}}}},
    "previous": {"filter": {"range": {"@timestamp": {"gte": "now-2m", "lt": "now-1m"}}}}
  }
}
```

For Case A specifically, the clause that fires is `connection refused`.
`broken pipe` is kept for a related-but-distinct scenario this test doesn't
exercise (an already-open connection getting killed mid-request, vs. a
brand-new connection attempt being refused) — documented, not yet observed
live. Dropped from the original version: bare `loggerName` as a should
-option (too broad on its own), and `SQLException` / `pool exhausted` /
`Unable to acquire` / `postmaster is accepting` (never actually appeared in
either live run — they were guesses).

**Explicitly excluded:** Vert.x `BlockedThreadChecker` "has been blocked"
warnings. These genuinely appeared in the live NB15 run:
```
[2026-07-03T04:43:55.073Z] WARN  io.vertx.core.impl.BlockedThreadChecker
  Thread Thread[vert.x-eventloop-thread-1,5,main] has been blocked for
  3563 ms, time limit is 2000 ms
```
Per 2026-07-03 direction, this is **not** treated as a "database
unavailable" signal on its own: a blocked event-loop thread can have causes
other than a dead DB connection, and when a request fails this way the
caller already gets a failed response and can retry the job itself — it
doesn't need to page anyone. `src/opensearch_alert_provisioner.py`'s
`matches_db_pool_signal()` gives a pure-Python check confirming this line
(logger `io.vertx.core.impl.BlockedThreadChecker`) does not satisfy the
monitor's must-clauses. Still available via
`polaris_test_utils.search_blocked_thread_errors()` as a manual diagnostic.

### Remediation

```
1. Confirm: kubectl get pods -n datahub-hynix | grep postgresql
2. If pgpool/postgresql pod down: restore it
     kubectl scale deployment benchmarks-postgresql-postgresql-ha-pgpool \
       --replicas=1 -n datahub-hynix
3. Polaris auto-recovers once the same DB is reachable again (Agroal
   re-creates connections) — confirmed live in NB15: GET /catalogs went
   500/ConnectionError -> 200 within 3 poll attempts (~9s) after restore.
4. If errors continue AFTER restore but look like entity_version mismatches
   instead of connection errors: PostgreSQL was likely restored from an old
   backup, not just restarted — that's a different failure mode, see
   error-cases/16 and error-cases/issue-report-postgresql-restore.md
   (requires a Polaris pod restart, not just a DB restore).
```

Longer-term prevention (from `issue-report-postgresql-restore.md`):
`QUARKUS_DATASOURCE_JDBC_BACKGROUND_VALIDATION_INTERVAL=PT30S` and
`QUARKUS_DATASOURCE_JDBC_VALIDATE_ON_BORROW=true` so broken connections are
caught and replaced before Polaris hands them to a request.

### Alert / notification sent

Covered once for both cases — see "Alert & resolved notification" after
Case B (identical for both; full definitions in the guide).

### Reproduce / test notebook

`error-cases/15_FATAL_connection_pool_error.ipynb`:
- Cell 1.5 — provisions Monitor 7, both triggers (idempotent)
- Cells 2–4 — scale pgpool to 0, confirm Agroal/health-check logs appear
- Cell 4.5 — force-runs Monitor 7 (`dryrun=True`) and checks
  `trigger_fired(result, ALERT_TRIGGER_NAME)` — not just that a log line
  exists, that the registered trigger's condition actually evaluated true
- Cells 5–6 — restore pgpool, confirm Polaris auto-recovers
- Cell 7 — re-runs the monitor and checks
  `trigger_fired(result, RESOLVED_TRIGGER_NAME)` — confirms the all-clear
  notification would have fired
- Cell 7.5 — `matches_db_pool_signal()` sanity check that the captured
  blocked-thread warning does NOT satisfy the query (exclusion proof)

---

## Case B — PostgreSQL Reachable, Pool Exhausted (max_connections)

Root cause: PostgreSQL itself is healthy, but connections are saturated —
`max_connections` reached. Reproduced live in
`error-cases/27_503_postgresql_max_connections.ipynb` via a 50-request
concurrent hammer against `/catalogs`, run live for the first time on
2026-07-03.

### Actual logs from Polaris (live-captured 2026-07-03)

The real signal turned out to be **different from what was originally
guessed** in the first version of this doc (which speculated a generic
Agroal timeout message like "Unable to acquire connection from the pool").
What Agroal actually logs is the **raw PostgreSQL FATAL error, relayed
verbatim**, and it appears directly in the `benchmarks-polaris` container
logs (not a separate `pgpool`/`postgresql` container line, as originally
assumed) — 10 identical WARNs in the same second:

```
[2026-07-03T04:47:14.902Z] WARN
  logger  : io.agroal.pool
  message : Datasource '<default>': FATAL: Sorry, too many clients already

(repeats 10x at the same timestamp, one per exhausted connection attempt)
```

Config at the time of the test, confirmed via `pg_query`:
```
PostgreSQL max_connections: 100
Active connections before test: 23 (77 available)
50 concurrent requests -> 49 succeeded, 1 client-side exception
  (response body wasn't JSON — the pool-exhaustion error page)
```

This is a much more precise, and much more specific, signal than the
original guess — `"too many clients already"` is PostgreSQL's own fixed
error string, unlikely to appear for any other reason.

### Query strategy (OpenSearch monitor)

Same Monitor 7, same shared query as Case A (see the full query in Case A's
"Query strategy" section) — the clause that specifically fires for this
case is `too many clients already`. Dropped from the original version:
`Unable to acquire`, `pool exhausted`, `SQLException`,
`postmaster is accepting` — none of these appeared in the live run; they
were guesses that made the query broader than the real signal warranted.

`search_blocked_thread_errors()` remains a useful manual diagnostic for this
case (pool exhaustion can manifest as requests queuing/blocking), but per
the 2026-07-03 exclusion decision it is **not** wired into the monitor
itself — see the exclusion note under Case A.

### Remediation

From NB27's own fix-recommendation cell:

```
Rule: pool_size <= (max_connections - reserved) / num_polaris_pods
Example:
  PostgreSQL max_connections: 200
  Reserved for admin/repmgr:  20
  Available:                   180
  Polaris pods (HPA max):      3
  Pool size per pod:           180/3 = 60 (not 300!)

Fix 1 — reduce Polaris pool size (values.yaml):
  QUARKUS_DATASOURCE_JDBC_MAX_SIZE: "60"        # was 300
  QUARKUS_DATASOURCE_JDBC_MIN_SIZE: "5"
  QUARKUS_DATASOURCE_JDBC_ACQUISITION_TIMEOUT: "PT5S"   # fail fast

Fix 2 — increase PostgreSQL max_connections:
  kubectl exec -n datahub-hynix benchmarks-postgresql-postgresql-ha-postgresql-0 -- \
    psql -U postgres -c "ALTER SYSTEM SET max_connections=500;"

Fix 3 (production-recommended) — add PgBouncer:
  Polaris -> PgBouncer -> PostgreSQL, multiplexing 300 Polaris connections
  down to ~50 real PostgreSQL connections.
```

Confirmed live in the 2026-07-03 run: `QUARKUS_DATASOURCE_JDBC_MAX_SIZE=300`
against a real PostgreSQL `max_connections=100` — Polaris alone can exceed
the DB's limit before any other service even connects. This is not a
hypothetical risk, it's the actual configuration in this environment.

### Reproduce / test notebook

`error-cases/27_503_postgresql_max_connections.ipynb`:
- Cell 1.5 — provisions Monitor 7, both triggers (idempotent — no-op if
  NB15 already ran)
- Cells 2–4 — check current PostgreSQL connection stats, hammer `/catalogs`
  with 50 concurrent requests, search for exhaustion logs
- Cell 4.5 — force-runs Monitor 7 (`dryrun=True`) and checks
  `trigger_fired(result, ALERT_TRIGGER_NAME)`
- Cells 5–6 — pool-sizing analysis + the three fixes above

---

## Alert & resolved notification

Shared by both cases — one monitor, two triggers.

### ALERT (fires while the pool is unavailable)

`value_schema_id: 225` payload to the "Polaris SMS Webhook" custom-webhook
destination, which the company Kafka REST proxy fans out to SMS +
Messenger. Severity 1, 30-minute throttle:

```json
{
  "value_schema_id": "225",
  "records": [{
    "value": {
      "noti_phone": "01012345678",
      "noti_title": "[POLARIS] 🔴 DB Connection Pool Unavailable",
      "noti_content": "{{ctx.results.0.aggregations.current.doc_count}} DB connection pool errors in last 1 min. Detected: {{ctx.results.0.hits.hits.0._source.message}} (logger: {{ctx.results.0.hits.hits.0._source.loggerName}}). Check: kubectl get pods -n datahub-hynix | grep postgresql",
      "dt": "{{ctx.periodStart}}"
    }
  }]
}
```

**Includes the actual matched log line** (2026-07-03) — not just a count.
`{{ctx.results.0.hits.hits.0._source.message}}` puts the real Agroal
message (e.g. `Connection to ...:5432 refused` or
`FATAL: Sorry, too many clients already`) directly in the SMS/Messenger
text, so the engineer knows which case it is on sight, no OpenSearch lookup
needed. Safe here (unlike the general "don't reference `hits.hits.0`
without checking for empty results" caution in the guide's Step 2) because
`current`/`previous` are filter-aggregations over the same top-level hits,
not a separate query — the trigger condition being true already guarantees
a matching hit exists.

### RESOLVED (fires once, right after recovery) — new 2026-07-03

Per direction: this is a PostgreSQL/infra-owned failure, not something a
Polaris engineer fixes by changing application code, so whoever got paged
needs an explicit all-clear rather than just silence. Severity 3
(informational, not a page), 5-minute throttle:

```json
{
  "value_schema_id": "225",
  "records": [{
    "value": {
      "noti_phone": "01012345678",
      "noti_title": "[POLARIS] ✅ DB Connection Pool Unavailable — RESOLVED",
      "noti_content": "DB connection pool errors cleared. {{ctx.results.0.aggregations.previous.doc_count}} errors in the prior minute, 0 in the last minute. Last error before recovery: {{ctx.results.0.hits.hits.0._source.message}}",
      "dt": "{{ctx.periodStart}}"
    }
  }]
}
```

**Why two triggers instead of a native "resolved" feature:** OpenSearch
Alerting has no built-in de-escalation/resolved action for query-level
monitors (confirmed against the OpenSearch 1.3/latest Alerting docs —
actions fire on every execution where the trigger condition is true,
throttle only rate-limits repeats; only bucket-level monitors get
DEDUPED/NEW per-alert scoping, and this isn't a bucket-level problem). A
naive second trigger with the literal negated condition (`hits == 0`) would
fire on *every* healthy execution — spam, not a one-time all-clear. The fix
is the `current`/`previous` sliding-window aggregation in the query above:
RESOLVED's condition (`current.doc_count == 0 && previous.doc_count > 0`)
is true for exactly one execution — the first clean minute right after a
bad one — then false again the next minute since `previous` is clean too.
No flip-flop, no persisted state needed.

Both triggers registered together via
`src/opensearch_alert_provisioner.py`'s
`provision_db_connection_pool_monitor()` (idempotent). It does **not**
create the destination itself — that's the internal-network Kafka webhook,
created manually per the guide's Step 1; the first live run against a real
cluster confirmed the provisioner correctly detects a missing destination
and skips with a clear message rather than failing silently. Actual
SMS/Messenger delivery is unconfirmed from this sandbox (no route to the
internal endpoint) — verify manually once the real webhook URL is set.

---

## Summary

| | Case A — PG/pgpool down | Case B — pool exhausted |
|---|---|---|
| Trigger message phrase | `connection refused` | `too many clients already` |
| Live-captured? | Yes (NB15, 2 runs) | Yes (NB27, 2026-07-03 run) |
| Client symptom | 401 (early) / `ConnectionError` / 500 / 503 | 500, non-JSON error body |
| Primary fix | Restore pgpool/postgresql pod | Resize pool vs `max_connections`, or add PgBouncer |
| Excluded signal | Vert.x blocked-thread warning (client can retry) | same |
| Monitor | Monitor 7 (shared, 2 triggers: ALERT + RESOLVED) | Monitor 7 (shared) |
| Notebook | `error-cases/15` | `error-cases/27` |
