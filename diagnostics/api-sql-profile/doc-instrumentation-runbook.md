# Instrumentation Runbook

Enable the three capture streams before running `01_api_access_map.ipynb`, and **revert them
afterwards**. Every command here targets the local OrbStack cluster only.

> **Do not run any of this against the company DEV or PROD clusters.** `log_statement='all'` on a
> shared PostgreSQL is both a performance problem and a confidentiality problem — bound parameters
> land in the server log, and some of them are secret material.

## 0. Resource names

Confirmed against `kubectl get all` on this cluster (2026-08-18):

```bash
export NS=datahub-hynix
export POLARIS=deploy/benchmarks-polaris
export PGPOOL=deploy/benchmarks-postgresql-postgresql-ha-pgpool
export PGSTS=statefulset/benchmarks-postgresql-postgresql-ha-postgresql   # 3 replicas
export MINIO=deploy/benchmarks-minio
```

Endpoints (all LoadBalancer on `192.168.139.2`):

| Service | Address | Notes |
|---|---|---|
| `benchmarks-polaris` | `192.168.139.2:8181` | the catalog API |
| `benchmarks-polaris-mgmt` | `192.168.139.2:8182` | **management port — `/q/metrics` lives here**, not 8282 as the upstream docs default suggests |
| `benchmarks-postgresql-...-pgpool` | `192.168.139.2:5432` | the pooler — this is what `PG_HOST` reaches |
| `benchmarks-minio` | `192.168.139.2:9000` | |

`check_sql_logging.py` derives the Polaris deployment name from `polaris_container_name` in
`common.yaml`; override the namespace with `--namespace`.

### Two corrections worth carrying forward

**The pooler is Pgpool-II, not PgBouncer.** The Bitnami `postgresql-ha` chart ships Pgpool-II
(`...-ha-pgpool`), and `CLAUDE.md` describing it as PgBouncer is inaccurate. It runs with
`load_balance_mode = on`, `statement_level_load_balance = off` and
`disableLoadBalancingOnWrite: always`, which means:

- a session that has issued **no** write load-balances its SELECTs across all three replicas;
- once a session performs a write, **every** subsequent read in that session is pinned to the
  primary for the life of that session.

Polaris holds pooled connections for up to `QUARKUS_DATASOURCE_JDBC_MAX_LIFETIME=PT10M`, so a
connection that ever wrote stays on the primary until it is recycled. The distribution is therefore
skewed toward the primary but **not exclusive to it** — a PG server log tailed from one pod still
silently misses statements. Tail all three, or port-forward the primary and bypass the pooler.

**Direct-to-Postgres needs a port-forward.** Decision #6 assumed direct access; in fact only the
pgpool service is a LoadBalancer. The `...-ha-postgresql` service is ClusterIP-only, so bypassing the
pooler means:

```bash
# -0 is usually the repmgr primary, but confirm rather than assume:
kubectl -n $NS exec $PGSTS-0 -- bash -c 'repmgr -f /opt/bitnami/repmgr/conf/repmgr.conf node check'
kubectl -n $NS port-forward pod/benchmarks-postgresql-postgresql-ha-postgresql-0 5433:5432 &
# then point the notebook's psycopg2 connection at localhost:5433
```

Worth doing for the SQL-mapping and index-audit runs, since it removes both the load-balancing
ambiguity and the pooler's session-attribution problem. Leave it *out* of any later latency run —
production traffic goes through the pooler, so the pooler's cost belongs in the honest number.

## 0.5 The one setting that blocks everything (CONFIRMED 2026-08-18)

Polaris's Helm `values.yaml` pins the SQL logger to INFO under "Noise suppression":

```yaml
logging:
  categories:
    org.apache.polaris.persistence.relational.jdbc.DatasourceOperations: INFO
```

Logger resolution is **most-specific-wins**, so setting the *package*
(`org.apache.polaris.persistence.relational.jdbc`) to DEBUG has no effect — the class-level `INFO`
overrides it. The symptom is DEBUG lines from other `org.apache.polaris.*` categories and never a
single `query:` line, which looks exactly like "persistence isn't running".

**Fix (preferred) — one line in the Polaris values, then `helm upgrade`:**

```yaml
org.apache.polaris.persistence.relational.jdbc.DatasourceOperations: DEBUG
```

**Fix (no chart change) — the env var must name the CLASS, not the package:**

```bash
kubectl -n $NS set env $POLARIS \
  QUARKUS_LOG_CATEGORY__ORG_APACHE_POLARIS_PERSISTENCE_RELATIONAL_JDBC_DATASOURCEOPERATIONS__LEVEL=DEBUG
```

It is suppressed for a good reason — one log line per statement, on every request. Enable it for the
profiling run and revert afterwards (§5).

Persistence on this cluster is confirmed `relational-jdbc` with the jdbcUrl pointing at pgpool, so
no metastore change is needed.

## 0.6 Shared memory — check before seeding

The PostgreSQL values set **no `/dev/shm` volume**, so the containers get Kubernetes' 64 MB default.
That is the exact condition reproduced in `diagnostics/doc-shm-exhaustion-test-plan.md`: parallel-query
DSM allocation fails, and clients see 08001/08003/08006. Those would surface mid-seed as scattered API
failures that look like Polaris defects.

```bash
kubectl -n $NS exec benchmarks-postgresql-postgresql-ha-postgresql-0 -- df -h /dev/shm
```

Fix in the postgresql-ha values (the chart has no `shmVolume` key — use the extra-volume hooks):

```yaml
postgresql:
  extraVolumes:
    - name: dshm
      emptyDir:
        medium: Memory
        sizeLimit: 1Gi
  extraVolumeMounts:
    - name: dshm
      mountPath: /dev/shm
```

This also closes the OrbStack K8s leg of S5 in that test plan, which was still open.

---

---

## 1. Polaris — SQL DEBUG log (required)

Polaris 1.3.0 logs every statement from
`org.apache.polaris.persistence.relational.jdbc.DatasourceOperations` at DEBUG, as
`query: <sql> <params>`. This is the primary stream: it is emitted in-process, so it attributes
statements to the request that caused them — something the PostgreSQL log cannot do behind a pooler.

```bash
# Kubernetes
kubectl -n $NS set env $POLARIS \
  QUARKUS_LOG_CATEGORY__ORG_APACHE_POLARIS_PERSISTENCE_RELATIONAL_JDBC_DATASOURCEOPERATIONS__LEVEL=DEBUG \
  QUARKUS_HTTP_ACCESS_LOG_ENABLED=true

kubectl -n $NS rollout status $POLARIS
```

```bash
# plain Docker
docker rm -f benchmarks-polaris
docker run -d --name benchmarks-polaris \
  -e QUARKUS_LOG_CATEGORY__ORG_APACHE_POLARIS_PERSISTENCE_RELATIONAL_JDBC__LEVEL=DEBUG \
  -e QUARKUS_HTTP_ACCESS_LOG_ENABLED=true \
  ... <your existing flags> ...
```

### Facts confirmed against the 1.3.0 distribution defaults

Checked in `runtime/defaults/src/main/resources/application.properties`, so these are not guesses:

- **`quarkus.log.min-level` is NOT set by Polaris**, so Quarkus's default of `DEBUG` applies. The
  build-time gate that would make a runtime category override silently useless **is not a problem
  here** — a runtime `DEBUG` category setting genuinely works.
- `quarkus.log.level=INFO` is the *root* level. A category override to `DEBUG` still takes effect;
  the root level does not suppress it.
- **Polaris also logs to a file**: `quarkus.log.file.enable=true`,
  `quarkus.log.file.path=./logs/polaris.log`, rotating at 10 MB. If console logging is ever turned
  off, tail that file instead of container stdout.
- The shipped console/file format is

  ```
  %d{yyyy-MM-dd HH:mm:ss,SSS} %-5p [%c{3.}] [%X{requestId},%X{realmId}] \
      [%X{traceId},%X{parentId},%X{spanId},%X{sampled}] (%t) %s%e%n
  ```

  `%c{3.}` abbreviates each *package* segment to three characters but keeps the class name in full,
  so lines read `[org.apa.pol.per.rel.jdb.DatasourceOperations]` — which is why grepping for
  `DatasourceOperations` is the right check.

  Note the MDC is **positional** (`[requestId,realmId] [traceId,parentId,spanId,sampled]`), not
  `key=value`. `api_trace.parse_mdc` handles both, positional first.

### Prefer the JSON log format

```bash
kubectl -n $NS set env $POLARIS QUARKUS_LOG_CONSOLE_JSON_ENABLED=true
```

Not cosmetic — it is the format the parser is happiest with, for two concrete reasons:

- `DatasourceOperations.logQuery()` renders parameters **newline-separated and four-space indented**,
  not bracketed. In the plain-text formatter a single statement therefore spans several physical log
  lines and cannot be parsed line-by-line at all. JSON keeps the whole message in one string.
- The JSON form carries `mdc.requestId` as a first-class field, and Polaris increments it per request
  (`<uuid>_0000000000000000002`). That gives **exact** per-request attribution — strictly better than
  the timestamp window `api_trace` otherwise falls back to.

`api_trace.parse_polaris_log` auto-detects the format per line, so both work. With JSON on, the
`grep -c DatasourceOperations` check still works too, because `loggerName` carries the full class name.

### If `grep -c DatasourceOperations capture/polaris.log` returns 0

Run the diagnostic rather than guessing — it generates its own traffic and reports which rung of the
ladder actually broke:

```bash
python diagnostics/api-sql-profile/check_sql_logging.py
```

The most common cause is the most benign: **no API traffic has reached Polaris since the tail
started**, so there is simply nothing to log yet. The next most common is that `kubectl set env`
triggered a rollout and the tail is still following the old, now-dead pod.

If the env var genuinely is not taking effect, note the **double underscores** — they encode the
quote characters in `quarkus.log.category."…".level`, and a single underscore silently does nothing:

```
QUARKUS_LOG_CATEGORY__ORG_APACHE_POLARIS_PERSISTENCE_RELATIONAL_JDBC__LEVEL=DEBUG
```

Sidestep the mangling entirely if it stays stubborn:

```bash
JAVA_OPTS_APPEND='-Dquarkus.log.category."org.apache.polaris.persistence.relational.jdbc".level=DEBUG'
```

Tail into the capture directory (from the notebook's own directory):

```bash
mkdir -p capture
kubectl -n $NS logs -f $POLARIS > capture/polaris.log &
# or: docker logs -f benchmarks-polaris > capture/polaris.log 2>&1 &
```

Confirm it is producing SQL:

```bash
grep -c "DatasourceOperations" capture/polaris.log
```

---

## 2. PostgreSQL — statement log (optional, adds server-side timings)

Gives the real `duration: N ms` per statement and catches transaction/pooler chatter Polaris never
logs. Skip it and the mapping still works; only the timing columns go empty.

Apply on **each** of the three PostgreSQL replicas — `ALTER SYSTEM` is per-node, and with Pgpool
load-balancing reads, statements land on all of them:

```sql
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_min_duration_statement = 0;
ALTER SYSTEM SET log_line_prefix = '%m [%p] db=%d,user=%u,app=%a,xid=%x ';
SELECT pg_reload_conf();          -- no restart needed for these three
```

Tail it:

```bash
# Pgpool load-balances SELECTs across all three replicas, so ONE pod is not enough:
for i in 0 1 2; do
  kubectl -n $NS logs -f benchmarks-postgresql-postgresql-ha-postgresql-$i \
    >> capture/pg.log &
done
# or, if PostgreSQL logs to a file inside the container:
# Simpler alternative: port-forward the primary (§0) and skip the pooler entirely.
```

### Connection budget — check before the seed

The numbers do not add up under load, and the seed is the heaviest write workload this cluster has seen:

| Setting | Value |
|---|---|
| PostgreSQL `max_connections` | **200** (per node) |
| `max_wal_senders` | 10 |
| Pgpool `numInitChildren` x `maxPool` | 64 x 4 |
| Polaris `QUARKUS_DATASOURCE_JDBC_MAX_SIZE` | **300** per pod, HPA up to 3 pods |

Polaris alone is willing to open 300 connections against a backend that accepts 200, and Pgpool's
client slots sit between them. Under the seed this is likely to produce PostgreSQL's
`FATAL: sorry, too many clients already` — which is exactly the string the Case B work in
`error-cases/` identified as the real DB-pool-exhaustion signal, and what Monitor 7 was built to
alert on.

Before a full seed, either lower `QUARKUS_DATASOURCE_JDBC_MAX_SIZE` to something below the backend's
capacity (~150), or raise `max_connections` — and treat any `too many clients` errors during the run
as infrastructure, not as a Polaris defect.

### `pg_stat_statements` (decision #2 — included)

> ### ⚠ DO NOT run a bare `ALTER SYSTEM SET shared_preload_libraries`
>
> An earlier revision of this runbook said:
>
> ```sql
> ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';   -- DESTRUCTIVE HERE
> ```
>
> That is **wrong on this cluster.** `ALTER SYSTEM` writes `postgresql.auto.conf`, which overrides
> `postgresql.conf` — so it does not *append*, it **replaces**. The Bitnami `postgresql-ha` chart
> ships `postgresql.sharedPreloadLibraries: "pgaudit, repmgr"`, and running that statement would
> drop `repmgr`, leaving repmgrd unable to attach to its shared-memory segment. Since repmgrd is
> what promotes a standby when the primary fails, that silently disables automatic failover on a
> 3-node cluster.
>
> This is a hazard to avoid, not a diagnosis of any observed incident — `repmgrd` also logs
> `[<ts>] [ERROR] unable to write to shared memory` transiently **during pod rollout**, before
> PostgreSQL has finished starting, which is unrelated and expected. To tell them apart:
>
> ```sql
> SELECT name, setting, source, sourcefile
> FROM pg_settings WHERE name = 'shared_preload_libraries';
> ```
>
> `source = configuration file` pointing at `postgresql.auto.conf` means an override is in force.
> Otherwise the message was startup noise. Confirm the cluster either way:
>
> ```bash
> kubectl -n $NS exec benchmarks-postgresql-postgresql-ha-postgresql-0 -- \
>   repmgr -f /opt/bitnami/repmgr/conf/repmgr.conf cluster show
> ```

**The correct way** is through the chart, so the value stays a complete list and survives pod
re-creation:

```yaml
postgresql:
  sharedPreloadLibraries: "pgaudit, repmgr, pg_stat_statements"
  extendedConf: |
    pg_stat_statements.track = all
    pg_stat_statements.max = 10000
```

then `helm upgrade` and restart. Afterwards:

```sql
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
SHOW shared_preload_libraries;          -- must still list repmgr
SELECT count(*) FROM pg_stat_statements;
```

If you would rather not restart a healthy HA cluster at all, **skip `pg_stat_statements`**. It only
adds rows-scanned and buffer statistics; the API→table mapping and the index audit both work without
it.

---

## 3. MinIO — object trace (optional, needed for the storage half)

Without this the "which directory in MinIO" question cannot be answered.

```bash
mc alias set localminio http://<MINIO_HOST>:9000 "$MINIO_ACCESS_KEY" "$MINIO_SECRET_KEY"
mc admin trace --json --path '/data-catalog-bucket/*' localminio > capture/minio.json &
```

`--json` matters: one JSON object per line is far more robust to parse than the human-readable
default, and `api_trace.parse_minio_trace` expects it.

Never put the keys on the command line — read them from the environment, as
`diagnostics/probe_auth_mode.py` already does.

---

## 4. Preflight

The notebook checks all three itself, but to verify by hand:

```bash
grep -c DatasourceOperations capture/polaris.log   # must be > 0
wc -l capture/pg.log capture/minio.json            # warn only if empty
```

---

## 5. REVERT — do not skip

Leaving `log_statement='all'` on will fill the disk and slow every later run.

```sql
ALTER SYSTEM RESET log_statement;
ALTER SYSTEM RESET log_min_duration_statement;
ALTER SYSTEM RESET log_line_prefix;
SELECT pg_reload_conf();
```

```bash
# Polaris back to default logging
kubectl -n $NS set env $POLARIS \
  QUARKUS_LOG_CATEGORY__ORG_APACHE_POLARIS_PERSISTENCE_RELATIONAL_JDBC_DATASOURCEOPERATIONS__LEVEL- \
  QUARKUS_HTTP_ACCESS_LOG_ENABLED-

# stop the tails and the MinIO trace
kill %1 %2 %3 2>/dev/null

# pg_stat_statements: revert via the CHART (postgresql.sharedPreloadLibraries),
# never with a bare ALTER SYSTEM — see the warning in §2.
```

Also confirm the seed fixture is gone — `TEARDOWN_SEED = True` in the notebook's final section, or:

```python
from polaris_seed import teardown
teardown(pc, ledger_path="capture/seed_ledger.json")
```

---

## 6. Capture hygiene

`capture/` is gitignored by the notebook on first run, and it must stay that way.

Raw captures contain **bound parameters**, and statements against `principal_authentication_data`
carry `main_secret_hash`, `secondary_secret_hash` and `secret_salt`. `api_trace` redacts these before
they reach any record or generated document — `redact_params()` replaces *every* parameter of any
statement touching that table, on the principle that positional parameters cannot be reliably mapped
back to columns — but **the raw log files themselves are not safe to commit**.

Delete them when finished:

```bash
rm -rf capture/
```

---

## Appendix — the OpenTelemetry alternative

Polaris ships Quarkus OTel, and its MDC already carries `requestId`, `realmId`, `traceId`,
`parentId`, `spanId`. Enabling it replaces the timestamp-window correlation with an exact span tree:

```properties
quarkus.otel.sdk.disabled=false
quarkus.otel.exporter.otlp.traces.endpoint=http://<collector>:4317
quarkus.datasource.jdbc.telemetry=true    # one span per JDBC statement, with db.statement
```

One Jaeger container then gives, per HTTP request: request → auth/resolution → each SQL statement
(text and duration) → each S3 call. That would let **section 2 of this runbook be dropped entirely** —
no `log_statement='all'`, which is the heaviest and riskiest step here.

Deferred pending a decision on running Jaeger locally; `api_trace` is structured so that swapping the
source of `SqlStatement` records is the only change it would require.
