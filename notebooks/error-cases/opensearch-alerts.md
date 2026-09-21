# OpenSearch Alert Configuration — Polaris Observability

## Alert 1: PostgreSQL Connection Failure

```
Monitor name:  Polaris DB Connection Failure
Type:          Per query monitor
Index:         k8s-logs-*
Schedule:      Every 1 minute

Query:
{
  "query": {
    "bool": {
      "must": [
        {"range": {"@timestamp": {"gte": "now-1m"}}},
        {"term": {"kubernetes.container_name.keyword": "benchmarks-polaris"}}
      ],
      "should": [
        {"match": {"message": "connection refused"}},
        {"match": {"message": "broken pipe"}},
        {"match": {"message": "Unable to acquire connection"}},
        {"match": {"message": "Connection is not valid"}}
      ],
      "minimum_should_match": 1
    }
  }
}

Trigger: count > 0

Alert body (SMS format):
{
  "value_schema_id": "225",
  "records": [{
    "value": {
      "noti_phone": "01012345678",
      "noti_title": "[POLARIS] DB Connection Failure",
      "noti_content": "PostgreSQL connection error detected. Check DB health: kubectl get pods -n datahub-hynix | grep postgresql",
      "dt": "{{ctx.periodStart}}"
    }
  }]
}
```

---

## Alert 2: Entity Version Mismatch (Monday Incident)

```
Monitor name:  Polaris Entity Version Mismatch
Type:          Per query monitor
Index:         k8s-logs-*
Schedule:      Every 1 minute

Query:
{
  "query": {
    "bool": {
      "must": [
        {"range": {"@timestamp": {"gte": "now-1m"}}},
        {"term": {"kubernetes.container_name.keyword": "benchmarks-polaris"}}
      ],
      "should": [
        {"match": {"message": "EntityVersionMismatch"}},
        {"match": {"message": "entity_version"}},
        {"match": {"message": "optimistic lock"}}
      ],
      "minimum_should_match": 1
    }
  }
}

Trigger: count > 0

Alert body (SMS format):
{
  "value_schema_id": "225",
  "records": [{
    "value": {
      "noti_phone": "01012345678",
      "noti_title": "[POLARIS] Entity Version Mismatch - RESTART REQUIRED",
      "noti_content": "PostgreSQL may have been restored from backup. Action: kubectl rollout restart deployment/benchmarks-polaris -n datahub-hynix",
      "dt": "{{ctx.periodStart}}"
    }
  }]
}
```

---

## Alert 3: High Error Rate (general)

```
Monitor name:  Polaris High Error Rate
Type:          Per query monitor
Index:         k8s-logs-*
Schedule:      Every 1 minute

Query:
{
  "query": {
    "bool": {
      "must": [
        {"range": {"@timestamp": {"gte": "now-1m"}}},
        {"term": {"kubernetes.container_name.keyword": "benchmarks-polaris"}},
        {"terms": {"level.keyword": ["ERROR", "WARN"]}}
      ]
    }
  }
}

Trigger: count > 10

Alert body (SMS format):
{
  "value_schema_id": "225",
  "records": [{
    "value": {
      "noti_phone": "01012345678",
      "noti_title": "[POLARIS] High Error Rate",
      "noti_content": "{{ctx.results.0.hits.total.value}} errors in last 1 minute. Check OpenSearch dashboard.",
      "dt": "{{ctx.periodStart}}"
    }
  }]
}
```

---

## Alert 4: Event Buffer Flush Failure

```
Monitor name:  Polaris Event Buffer Flush Failure
Type:          Per query monitor
Index:         k8s-logs-*
Schedule:      Every 1 minute

Query:
{
  "query": {
    "bool": {
      "must": [
        {"range": {"@timestamp": {"gte": "now-1m"}}},
        {"term": {"kubernetes.container_name.keyword": "benchmarks-polaris"}}
      ],
      "should": [
        {"match": {"message": "Failed to flush"}},
        {"match": {"message": "event buffer"}},
        {"match": {"message": "flush error"}}
      ],
      "minimum_should_match": 1
    }
  }
}

Trigger: count > 0

Alert body (SMS format):
{
  "value_schema_id": "225",
  "records": [{
    "value": {
      "noti_phone": "01012345678",
      "noti_title": "[POLARIS] Event Buffer Flush Failure",
      "noti_content": "Audit event buffer failed to flush. Audit log gap possible. Check PostgreSQL connectivity.",
      "dt": "{{ctx.periodStart}}"
    }
  }]
}
```

---

## Decision tree when alerts fire

```
Alert: DB Connection Failure
  → Check: kubectl get pods -n datahub-hynix | grep postgresql
  → If PostgreSQL DOWN: restore PostgreSQL first
  → If PostgreSQL UP:   check pgpool logs

Alert: Entity Version Mismatch
  → PostgreSQL was likely restored from backup
  → Action: kubectl rollout restart deployment/benchmarks-polaris
  → Verify: kubectl rollout status deployment/benchmarks-polaris
  → Confirm: GET /api/management/v1/catalogs → 200

Alert: High Error Rate
  → Check what error type:
    - 401 spike → auth/token issue
    - 403 spike → RBAC misconfiguration
    - 500 spike → check DB connection or entity_version
    - Connection errors → PostgreSQL issue

Alert: Event Buffer Flush Failure
  → Audit log gap (not data loss)
  → Check PostgreSQL connectivity
  → Consider pod restart if persistent
```
