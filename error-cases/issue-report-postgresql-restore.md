# Incident Report — PostgreSQL Restore Cache Mismatch

**Date:** Monday  
**Severity:** P1 — Service Degraded  
**Duration:** Until manual Polaris pod restart  
**Root Cause:** PostgreSQL restored from 6-hour-old backup → entity_version mismatch with Polaris in-memory state  

---

## Timeline

```
T-0    PostgreSQL failure occurs
         → Polaris connection pool: all connections broken
         → Requests fail: 500 Internal Server Error
         → Error: "connection refused" / "broken pipe"

T+Xh   PostgreSQL restored from backup (6 hours prior)
         → Same pod, same connection info
         → Data rolled back 6 hours

T+Xh   Polaris NOT restarted
         → JVM heap still has:
           - In-memory event buffer (PT5S, up to 1000 events)
           - JDBC connection pool (stale connections)
           - Cached entity_version values from before outage

T+Xh   Polaris reconnects to PostgreSQL (pool auto-recovery)
         → New connections established to restored DB
         → DB has entity_versions from 6 hours ago
         → Polaris in-memory state has entity_versions from NOW

T+Xh   Engineers notice errors continue after PostgreSQL restore
         → Not connection errors anymore
         → New errors: entity_version conflicts, 500s
         → Root cause not immediately obvious

T+Xh   Manual Polaris pod restart
         → JVM heap flushed
         → All caches cleared
         → entity_version re-read from PostgreSQL
         → Service restored ✅
```

---

## Root Cause Analysis

### Primary: PostgreSQL connection pool (Phase 1)
```
Polaris JDBC pool (Agroal):
  max-size: 300
  max-lifetime: PT30M
  idle-removal-interval: PT2M

During outage:
  All 300 connections → TCP reset / timeout
  Pool marks connections as invalid
  Requests: 503 (pool exhausted) or 500 (SQL error)

After restore:
  Pool auto-creates new connections ✅
  Connection errors stop ✅
```

### Secondary: entity_version cache mismatch (Phase 2 — real issue)
```
Polaris optimistic locking:
  Every entity has entity_version (integer)
  On UPDATE: WHERE entity_version = :expected
  If mismatch → EntityVersionMismatchException → 500

Before outage (live DB):
  catalog "analytics": entity_version = 47
  namespace "bronze":  entity_version = 23
  ...

After restore (backup from 6h ago):
  catalog "analytics": entity_version = 31  ← rolled back
  namespace "bronze":  entity_version = 15  ← rolled back

Polaris in-memory event buffer:
  Contains events referencing entity_version 32-47
  Tries to flush → UPDATE WHERE entity_version = 47
  DB has entity_version = 31
  → Mismatch → EntityVersionMismatchException → 500

Result:
  Every write operation fails until pod restart
  Read operations may also fail (principal lookup version check)
  Engineers see 500 errors but PostgreSQL appears healthy
```

### Why it was hard to diagnose
```
After PostgreSQL restore:
  ✅ PostgreSQL health check: UP
  ✅ Polaris /q/health: UP (health only checks connection, not entity_version)
  ✅ Polaris logs: "Database connections health check UP"
  ❌ But actual requests: 500 EntityVersionMismatchException

Without observability:
  Engineers check PostgreSQL → looks fine
  Engineers check Polaris health → UP
  → Confusion: both healthy but service broken
  → Root cause found only after manual investigation
```

---

## What Observability Should Have Detected

```
Signal 1: Connection error spike (T-0)
  → io.agroal: WARN "Connection is not valid"
  → io.quarkus.http.access-log: 500 spike
  → Alert: "Polaris 500 error rate > 10% for 1 minute"

Signal 2: entity_version mismatch after restore (T+Xh)
  → org.apache.polaris.core.persistence: ERROR
    "EntityVersionMismatchException"
  → Pattern: 500 errors continue AFTER connection restored
  → Alert: "EntityVersionMismatchException detected"
  → Suggested action: "Restart Polaris pod to flush entity cache"

Signal 3: Event buffer flush failure (T+Xh)
  → org.apache.polaris.service.events: ERROR
    "Failed to flush event buffer"
  → Alert: "Event flush failures detected"
```

---

## Fix Applied
```
Manual restart of Polaris pod:
  kubectl rollout restart deployment/benchmarks-polaris -n datahub-hynix

Effect:
  JVM heap cleared → all cached entity_versions gone
  Fresh DB read on next request → entity_version = 31 (from restore)
  All subsequent operations use correct version ✅
```

---

## Prevention Recommendations

### 1. Add connection validation (immediate)
```yaml
# values.yaml extraEnv
- name: QUARKUS_DATASOURCE_JDBC_BACKGROUND_VALIDATION_INTERVAL
  value: "PT30S"    # validate connections every 30s
- name: QUARKUS_DATASOURCE_JDBC_VALIDATE_ON_BORROW
  value: "true"     # validate before handing to Polaris
- name: QUARKUS_DATASOURCE_JDBC_NEW_CONNECTION_SQL
  value: "SELECT 1" # validation query
```

### 2. Add entity_version alert (immediate)
```
OpenSearch alert:
  Monitor: EntityVersionMismatchException in last 1 minute
  Trigger: count > 0
  Action: SMS + "Restart Polaris pod: kubectl rollout restart"
```

### 3. Add Polaris restart runbook to alert message
```
Alert message:
  "⚠️ Polaris entity_version mismatch detected
   Likely cause: PostgreSQL restored from backup
   Action: kubectl rollout restart deployment/benchmarks-polaris -n datahub-hynix
   Verify: kubectl rollout status deployment/benchmarks-polaris -n datahub-hynix"
```

### 4. Add health check for entity consistency (future)
```
Custom health check:
  POST /api/management/v1/catalogs (read operation)
  → if 500 EntityVersionMismatch → health = DOWN
  → triggers K8s liveness probe → auto-restart
```
