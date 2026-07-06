# Polaris Observability — OpenSearch Monitor & Alert Setup Guide

## Architecture

```
OpenSearch Monitor (scheduled query)
  → detects error pattern in k8s-logs-*
  → Trigger fires (threshold condition met)
  → Action sends POST to notification channel
  → Webhook server → Company Kafka REST Proxy → SMS
```

---

## Step 1 — Create Notification Channel

```
Alerting → Notifications → Create channel

Name:    Polaris SMS Webhook
Type:    Custom webhook
Method:  POST
URL:     http://<webhook-server-host>:<port>/sms

Headers:
  Key:    Content-Type
  Value:  application/vnd.kafka.avro.v2+json

  Key:    Accept
  Value:  application/vnd.kafka.v2+json

→ Save
```

Note: test button sends plain text — expected to show warning.
Real alerts will send proper JSON.

---

## Step 2 — Message Body Template

Used in all monitor trigger actions:

```json
{
  "value_schema_id": "225",
  "records": [{
    "value": {
      "noti_phone": "01012345678",
      "noti_title": "[POLARIS] <error title>",
      "noti_content": "{{ctx.results.0.hits.total.value}} errors detected. Monitor: {{ctx.monitor.name}}",
      "dt": "{{ctx.periodStart}}"
    }
  }]
}
```

### Safe Mustache variables (always populated)

```
{{ctx.monitor.name}}                    monitor name
{{ctx.trigger.name}}                    trigger name
{{ctx.results.0.hits.total.value}}      error count
{{ctx.periodStart}}                     period start time
{{ctx.periodEnd}}                       period end time
```

### DO NOT USE (causes Mustache error when no hits)

```
{{ctx.results.0.hits.hits.0._source.*}} → null when no results → error
```

---

## Step 3 — Create 7 Monitors

Go to: **Alerting → Monitors → Create monitor**

Common settings for all monitors:
```
Monitor type:  Per query monitor
Index:         k8s-logs-*
Time field:    @timestamp
Editor:        Extraction query editor
```

Monitor 7 (below) is **P0 — highest priority**, per manager request (2026-07-02):
Database Connection Pool is the single fault that takes Polaris fully down for
every user, so it gets registered first and is the only monitor in this guide
that also has a provisioning script — see "Automation" under Monitor 7. The
other six monitors stay manually-provisioned via the UI steps above; that
work is unchanged and out of scope here.

---

### Monitor 1 — Critical Errors (ERROR + WARN)

```
Monitor name:  Polaris Critical Errors
Schedule:      By interval → Every 1 Minutes
```

Query:
```json
{
  "size": 1,
  "query": {
    "bool": {
      "must": [
        {"range": {"@timestamp": {"gte": "now-1m"}}},
        {"term": {"kubernetes.container_name.keyword": "benchmarks-polaris"}},
        {"terms": {"level.keyword": ["ERROR", "WARN"]}}
      ]
    }
  },
  "_source": ["mdc.requestId", "level", "message", "loggerName"],
  "sort": [{"@timestamp": {"order": "desc"}}]
}
```

Trigger:
```
Trigger name:  Critical error detected
Condition:     ctx.results[0].hits.total.value > 0
Severity:      1 (Critical)
```

Action:
```
Action name:   Send SMS
Channel:       Polaris SMS Webhook
Throttle:      Every 30 minutes

Message body:
{
  "value_schema_id": "225",
  "records": [{
    "value": {
      "noti_phone": "01012345678",
      "noti_title": "[POLARIS] 🔴 Critical Error",
      "noti_content": "{{ctx.results.0.hits.total.value}} ERROR/WARN in last 1 min. Monitor: {{ctx.monitor.name}}",
      "dt": "{{ctx.periodStart}}"
    }
  }]
}
```

---

### Monitor 2 — 401 Unauthorized

```
Monitor name:  Polaris 401 Unauthorized
Schedule:      Every 1 Minutes
```

Query:
```json
{
  "size": 1,
  "query": {
    "bool": {
      "must": [
        {"range": {"@timestamp": {"gte": "now-1m"}}},
        {"term": {"kubernetes.container_name.keyword": "benchmarks-polaris"}},
        {"bool": {
          "should": [
            {"match": {"message": "\" 401"}},
            {"match": {"message": "Failed to resolve principal"}},
            {"match": {"message": "unauthorized_client"}},
            {"match": {"message": "MissingOrInvalidRealm"}}
          ],
          "minimum_should_match": 1
        }}
      ]
    }
  },
  "_source": ["mdc.requestId", "level", "message", "loggerName"],
  "sort": [{"@timestamp": {"order": "desc"}}]
}
```

Trigger:
```
Trigger name:  401 detected
Condition:     ctx.results[0].hits.total.value > 0
Severity:      1 (Critical)
```

Action:
```
Throttle: Every 30 minutes

Message body:
{
  "value_schema_id": "225",
  "records": [{
    "value": {
      "noti_phone": "01012345678",
      "noti_title": "[POLARIS] 🔴 401 Unauthorized",
      "noti_content": "{{ctx.results.0.hits.total.value}} auth failures in last 1 min. Causes: expired token / deleted principal / wrong credentials / missing realm header.",
      "dt": "{{ctx.periodStart}}"
    }
  }]
}
```

---

### Monitor 3 — 403 Forbidden

```
Monitor name:  Polaris 403 Forbidden
Schedule:      Every 1 Minutes
```

Query:
```json
{
  "size": 1,
  "query": {
    "bool": {
      "must": [
        {"range": {"@timestamp": {"gte": "now-1m"}}},
        {"term": {"kubernetes.container_name.keyword": "benchmarks-polaris"}},
        {"match": {"message": "ForbiddenException"}}
      ]
    }
  },
  "_source": ["mdc.requestId", "level", "message", "loggerName"],
  "sort": [{"@timestamp": {"order": "desc"}}]
}
```

Trigger:
```
Trigger name:  403 spike detected
Condition:     ctx.results[0].hits.total.value > 3
Severity:      2 (High)
```

Action:
```
Throttle: Every 1 hour

Message body:
{
  "value_schema_id": "225",
  "records": [{
    "value": {
      "noti_phone": "01012345678",
      "noti_title": "[POLARIS] 🟠 403 Forbidden Spike",
      "noti_content": "{{ctx.results.0.hits.total.value}} forbidden errors in last 1 min. Check RBAC configuration.",
      "dt": "{{ctx.periodStart}}"
    }
  }]
}
```

---

### Monitor 4 — 404 Not Found

```
Monitor name:  Polaris 404 Not Found
Schedule:      Every 5 Minutes
```

Query:
```json
{
  "size": 1,
  "query": {
    "bool": {
      "must": [
        {"range": {"@timestamp": {"gte": "now-5m"}}},
        {"term": {"kubernetes.container_name.keyword": "benchmarks-polaris"}},
        {"bool": {
          "should": [
            {"match": {"message": "does not exist"}},
            {"match": {"message": "NoSuch"}},
            {"match": {"message": "MissingOrInvalidRealm"}}
          ],
          "minimum_should_match": 1
        }}
      ]
    }
  },
  "_source": ["mdc.requestId", "level", "message", "loggerName"],
  "sort": [{"@timestamp": {"order": "desc"}}]
}
```

Trigger:
```
Trigger name:  404 spike detected
Condition:     ctx.results[0].hits.total.value > 5
Severity:      3 (Medium)
```

Action:
```
Throttle: Every 2 hours

Message body:
{
  "value_schema_id": "225",
  "records": [{
    "value": {
      "noti_phone": "01012345678",
      "noti_title": "[POLARIS] 🟡 404 Not Found Spike",
      "noti_content": "{{ctx.results.0.hits.total.value}} not found errors in last 5 min. Check catalog/namespace names.",
      "dt": "{{ctx.periodStart}}"
    }
  }]
}
```

---

### Monitor 5 — 409 Conflict

```
Monitor name:  Polaris 409 Conflict
Schedule:      Every 5 Minutes
```

Query:
```json
{
  "size": 1,
  "query": {
    "bool": {
      "must": [
        {"range": {"@timestamp": {"gte": "now-5m"}}},
        {"term": {"kubernetes.container_name.keyword": "benchmarks-polaris"}},
        {"bool": {
          "should": [
            {"match": {"message": "AlreadyExists"}},
            {"match": {"message": "not empty"}},
            {"match": {"message": "duplicate key"}}
          ],
          "minimum_should_match": 1
        }}
      ]
    }
  },
  "_source": ["mdc.requestId", "level", "message", "loggerName"],
  "sort": [{"@timestamp": {"order": "desc"}}]
}
```

Trigger:
```
Trigger name:  409 conflict detected
Condition:     ctx.results[0].hits.total.value > 0
Severity:      2 (High)
```

Action:
```
Throttle: Every 1 hour

Message body:
{
  "value_schema_id": "225",
  "records": [{
    "value": {
      "noti_phone": "01012345678",
      "noti_title": "[POLARIS] 🟠 409 Conflict",
      "noti_content": "{{ctx.results.0.hits.total.value}} conflict errors in last 5 min. Check for duplicate ETL runs.",
      "dt": "{{ctx.periodStart}}"
    }
  }]
}
```

---

### Monitor 6 — 400 Bad Request

```
Monitor name:  Polaris 400 Bad Request
Schedule:      Every 5 Minutes
```

Query:
```json
{
  "size": 1,
  "query": {
    "bool": {
      "must": [
        {"range": {"@timestamp": {"gte": "now-5m"}}},
        {"term": {"kubernetes.container_name.keyword": "benchmarks-polaris"}},
        {"bool": {
          "should": [
            {"match": {"message": "\" 400"}},
            {"match": {"message": "Bad Request"}},
            {"match": {"message": "Invalid schema"}},
            {"match": {"message": "IllegalArgumentException"}}
          ],
          "minimum_should_match": 1
        }}
      ]
    }
  },
  "_source": ["mdc.requestId", "level", "message", "loggerName"],
  "sort": [{"@timestamp": {"order": "desc"}}]
}
```

Trigger:
```
Trigger name:  400 spike detected
Condition:     ctx.results[0].hits.total.value > 5
Severity:      3 (Medium)
```

Action:
```
Throttle: Every 2 hours

Message body:
{
  "value_schema_id": "225",
  "records": [{
    "value": {
      "noti_phone": "01012345678",
      "noti_title": "[POLARIS] 🟡 400 Bad Request Spike",
      "noti_content": "{{ctx.results.0.hits.total.value}} bad request errors in last 5 min. Likely client bug — check API schema.",
      "dt": "{{ctx.periodStart}}"
    }
  }]
}
```

---

### Monitor 7 — Database Connection Pool Unavailable

**Priority: P0 (added 2026-07-02, per manager request). Revised 2026-07-03**
after the first live run against real NB15/NB27 output — the original query
was too broad and there was no resolved notification. Covers both known
root causes proven live in this repo's error-case notebooks:
- **Case A — PostgreSQL/pgpool down entirely** (`connection refused`,
  Agroal `io.agroal.pool` warnings) — see `error-cases/15_FATAL_connection_pool_error.ipynb`.
- **Case B — pool exhausted / max_connections exceeded** — the real captured
  Agroal message is the raw PostgreSQL error relayed verbatim:
  `FATAL: Sorry, too many clients already` — see
  `error-cases/27_503_postgresql_max_connections.ipynb`.

```
Monitor name:  Polaris DB Connection Pool Unavailable
Schedule:      Every 1 Minutes
```

**Query — tightened 2026-07-03.** The first version's `should` clauses were
too broad: a bare `loggerName: io.agroal.pool` term matched *any* Agroal log
line regardless of content, and `SQLException` / `pool exhausted` /
`Unable to acquire` never actually appeared in either live run — they were
guesses, not observed signal. Rebuilt from the real captured output:
`loggerName: io.agroal.pool` is now a mandatory `must` clause (not a
should-option), and the should-clauses use `match_phrase` (not `match`) on
only proven/documented substrings. The query also computes a `current`
(now-1m..now) and `previous` (now-2m..now-1m) `date_range` aggregation
instead of a plain hit count — both triggers below share this one query:

```json
{
  "size": 3,
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
  },
  "_source": ["mdc.requestId", "level", "message", "loggerName"],
  "sort": [{"@timestamp": {"order": "desc"}}]
}
```

**Explicitly excluded (2026-07-03 decision):** Vert.x `BlockedThreadChecker`
"has been blocked" warnings. These did appear in the live NB15 run
(event-loop thread blocked waiting on a dead connection), but a blocked
thread on its own isn't a "database unavailable" signal — it can have other
causes, and when a request fails this way the client already gets a failed
response and can retry the job itself. Not page-worthy. Still available via
`search_blocked_thread_errors()` as a manual diagnostic, just not wired into
this monitor.

**Two triggers, not one — this is how "resolved" notifications work here.**
OpenSearch Alerting has no native "notify when resolved" action for
query-level monitors (only bucket-level monitors get per-alert
DEDUPED/NEW/COMPLETED scoping); a naive second trigger with the negated
condition (`hits == 0`) would fire on *every* healthy execution, which is
spam, not a resolved notice. The `current`/`previous` aggregation above
fixes this: RESOLVED is true for exactly one execution — the first clean
minute right after a bad one — then false again on the next clean minute,
since `previous` is clean too. No flip-flop, no persisted state.

Trigger 1 (ALERT):
```
Trigger name:  DB connection pool unavailable detected
Condition:     ctx.results[0].aggregations.current.doc_count > 0
Severity:      1 (Critical)
```

Action:
```
Action name:   Send SMS + Messenger
Channel:       Polaris SMS Webhook
Throttle:      Every 30 minutes

Message body:
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

Trigger 2 (RESOLVED) — new 2026-07-03, per "not controlled by the Polaris
engineer" direction: since this is a PostgreSQL/infra-owned failure, not
something fixed by changing Polaris application code, whoever's paged needs
an explicit all-clear, not just silence:
```
Trigger name:  DB connection pool RESOLVED
Condition:     ctx.results[0].aggregations.current.doc_count == 0 &&
               ctx.results[0].aggregations.previous.doc_count > 0
Severity:      3 (Medium — informational, not a page)
```

Action:
```
Action name:   Send SMS + Messenger (resolved)
Channel:       Polaris SMS Webhook
Throttle:      Every 5 minutes

Message body:
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

**Message content includes the actual matched log line** (2026-07-03) —
`{{ctx.results.0.hits.hits.0._source.message}}` and `loggerName`, not just a
count, so the engineer sees e.g. `Connection to ...:5432 refused` vs
`FATAL: Sorry, too many clients already` directly in the SMS/Messenger body
and immediately knows which failure mode it is, without opening OpenSearch.
This looks like the pattern Step 2 above warns against ("DO NOT USE
`hits.hits.0._source.*`... null when no results → error") — but that
warning is about a query where the condition doesn't guarantee any hits.
Here it's safe: `current`/`previous` are `filter` aggregations computed over
the *same* top-level hits (not a separate query), so ALERT firing
(`current.doc_count > 0`) and RESOLVED firing (`previous.doc_count > 0`)
both guarantee `hits.hits` is non-empty whenever the action actually runs.

**Automation:** unlike Monitors 1–6, this one is also registered in code —
`src/opensearch_alert_provisioner.py` creates/updates this exact Monitor +
both Triggers via the OpenSearch Alerting REST API (idempotent), so it
doesn't have to be clicked through the Dashboards UI by hand. It looks up
the "Polaris SMS Webhook" channel from Step 1 by name and does **not**
create the destination itself — the webhook target is an internal-network
Kafka REST proxy endpoint (SMS + Messenger fan-out), so create the channel
manually first if it doesn't already exist (the first live run against a
real cluster confirmed the provisioner correctly detects this and skips
with a clear message rather than failing silently). `error-cases/15` and
`27` force-execute this monitor after simulating each fault and check
`trigger_results` by trigger name (via `trigger_fired()`) — ALERT during the
outage, RESOLVED after recovery — not just that a matching log line exists.
`matches_db_pool_signal()` gives a pure-Python check for the exclusion
decision above (e.g. proving a blocked-thread line does not match). Actual
SMS/Messenger delivery cannot be confirmed from a sandbox that can't reach
the internal endpoint; that's a manual check once the real webhook URL is
in place.

---

## Monitor Summary Table

| Monitor | Schedule | Threshold | Severity | Throttle |
|---------|----------|-----------|----------|----------|
| Critical Errors | 1 min | > 0 | 1 Critical | 30 min |
| 401 Unauthorized | 1 min | > 0 | 1 Critical | 30 min |
| 403 Forbidden | 1 min | > 3 | 2 High | 1 hour |
| 404 Not Found | 5 min | > 5 | 3 Medium | 2 hours |
| 409 Conflict | 5 min | > 0 | 2 High | 1 hour |
| 400 Bad Request | 5 min | > 5 | 3 Medium | 2 hours |
| **DB Connection Pool Unavailable (P0) — ALERT** | 1 min | current window > 0 | 1 Critical | 30 min |
| **DB Connection Pool Unavailable (P0) — RESOLVED** | 1 min | current == 0 & previous > 0 | 3 Medium | 5 min |

---

## Alert Decision Tree

```
🔴 Critical Error / 401
  → Check OpenSearch: Polaris - ERROR ALL panel
  → 401: expired token / deleted principal / wrong credentials
  → 500: check DB connection or entity_version mismatch
  → EntityVersionMismatch: kubectl rollout restart deployment/benchmarks-polaris

🔴 DB Connection Pool Unavailable
  → Check: kubectl get pods -n datahub-hynix | grep postgresql
  → If pgpool/postgresql pod down (Case A): restore the pod — Polaris
    auto-recovers once the same DB is reachable again (see error-cases/15)
  → If pods healthy but errors persist (Case B): pool exhausted — compare
    QUARKUS_DATASOURCE_JDBC_MAX_SIZE against PostgreSQL max_connections
    (see error-cases/27 for the sizing formula)
  → If errors continue AFTER DB restore and look like entity_version
    mismatches instead: PostgreSQL was likely restored from backup —
    kubectl rollout restart deployment/benchmarks-polaris (see
    error-cases/16 and error-cases/issue-report-postgresql-restore.md)
  → RESOLVED alert arrives automatically once the pool is clean for a full
    minute — this is NOT something the Polaris engineer fixes in app code,
    it confirms the infra-side fix (pod restore / pool resize) worked
  → A lone Vert.x "blocked thread" warning without a matching Agroal line is
    NOT this alert (excluded on purpose) — the caller already saw the
    failure and can retry; investigate separately if it recurs a lot

🟠 403 Forbidden
  → Check RBAC chain:
    principal role assigned to principal? GET /principals/{name}/principal-roles
    catalog role assigned to principal role? GET /principal-roles/{name}/catalog-roles
    privilege granted to catalog role? GET /catalogs/{name}/catalog-roles/{cr}/grants

🟡 404 Not Found
  → Check catalog name in ETL config — typo?
  → Check if catalog was deleted: GET /api/management/v1/catalogs/{name}
  → Check Polaris-Realm header present in all requests

🟠 409 Conflict
  → Check for duplicate ETL job runs
  → Check for duplicate grant: use safe_grant_privilege() pattern
  → Check namespace delete order: bottom-up (tables → child ns → parent ns)

🟡 400 Bad Request
  → Client-side bug — check API schema
  → namespace must be array not string: ["ns"] not "ns"
  → table create requires schema field
```

---

## Throttle Rationale

```
Severity 1 (Critical): 30 minutes
  → user-facing, needs fast re-alert if not resolved

Severity 2 (High):     1 hour
  → RBAC/conflict issues need engineer time to investigate

Severity 3 (Medium):   2 hours
  → client bugs need code fix + deployment cycle

Reference: Prometheus AlertManager default = 4 hours
Polaris uses shorter throttle — API service is user-facing
```

---

## Troubleshooting Monitors

```
Monitor shows 0 results always:
  → Preview query in extraction query editor
  → Check index pattern: k8s-logs-* has data?
  → Check time range matches schedule interval
  → Verify container name: kubernetes.container_name.keyword = benchmarks-polaris

Mustache error on test message:
  → Test button sends plain text — expected behavior
  → Do not use hits.hits._source in message body
  → Use only ctx.results.0.hits.total.value and ctx.monitor.name

Alert fires but webhook not receiving:
  → Check channel URL reachable from OpenSearch container
  → Use host.docker.internal if OpenSearch runs in Docker
  → Check Content-Type header set correctly
  → Check webhook server running: curl http://localhost:3000/

Alert fires too frequently:
  → Increase throttle duration
  → Increase trigger threshold (count > N)
  → Narrow query time range (now-1m → now-30s)
```
