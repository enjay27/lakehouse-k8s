> **HISTORICAL (banner added 2026-09-16).** This 2026-09-03 design (Polaris log PVC → Fluent Bit Deployment → VictoriaLogs) is not what was built. The running pipeline is the Fluent Bit DaemonSet → OpenSearch described in `SPEC-polaris-audit-logging.ko.md`; see `README.md` for the current set.

# Polaris Log Analytics Pipeline: Comprehensive Architecture & Integration Specification

---

## 1. Executive Summary & Context

* **Project Objective:** Build a dedicated, isolated, and scalable logging pipeline for Apache Polaris (running on Quarkus / JDK 21 in Kubernetes) to handle daily log surges from **10M up to 140M records/day** with **30-day retention (~300M to 4.2B records)**.
* **Core SLA Requirement:** Sub-second to 2-second query performance across arbitrary structured JSON fields (e.g., `mdc.requestId`, `loggerName`, `http_status`, exception stack traces) without JVM memory thrashing or high maintenance overhead.
* **Storage Reduction Strategy:** High-frequency, low-variance polling traffic (e.g., `GET .../tables/...` accounting for ~11M hits/day) is deduplicated at the shipper tier via stateful Lua scripting, slashing redundant access log volume by >99% before ingestion.
* **Selected Technology Stack:**
  * **Application Log Storage & Search Engine:** **VictoriaLogs (Single-Server Edition)**
  * **Dedicated In-Cluster Shipper:** **Fluent Bit** (running as a single replica Deployment)
  * **Log Volume Sharing Mechanism:** Kubernetes Shared `PersistentVolumeClaim` (`ReadWriteOnce` or `ReadWriteMany`) mounting `/logs/polaris.log`
  * **Exploration & Visualization:** Native **VMUI** and **Grafana** (`victoriametrics-logs-datasource`)

---

## 2. End-to-End Pipeline Architecture

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                   Kubernetes Cluster                                   │
│                                                                                        │
│  ┌───────────────────────────┐                                                         │
│  │   Polaris Application     │                                                         │
│  │   (Quarkus 3.x / JDK 21)  │                                                         │
│  └─────────────┬─────────────┘                                                         │
│                │ Non-blocking Append (OS Page Cache)                                   │
│                ▼                                                                       │
│  ┌───────────────────────────────────────────────────────────────────────────────┐     │
│  │   Shared PVC: polaris-shared-logs-pvc (Mount: /logs/polaris.log)               │     │
│  └──────────────────────────────────────┬────────────────────────────────────────┘     │
│                                         │ Inotify File Tail                            │
│                                         ▼                                              │
│  ┌───────────────────────────────────────────────────────────────────────────────┐     │
│  │   Fluent Bit Shipper Pod (Dedicated Deployment, replicaCount: 1)              │     │
│  │                                                                               │     │
│  │   ├── [INPUT]      Tail /logs/polaris.log (JSON parser)                       │     │
│  │   ├── [PARSER]     Quarkus Access Log Regex:                                  │     │
│  │   │                Extracts client_ip, user, http_method, api_path,           │     │
│  │   │                http_status (int), response_size (int)                     │     │
│  │   ├── [FILTER:LUA] Stateful Window Deduplication (11M GET table calls/day)    │     │
│  │   │                Drops duplicate GET /tables/{tbl} logs within 24h          │     │
│  │   └── [FILTER:MOD] Standardize _time, _msg, and app tags                      │     │
│  └──────────────────────────────────────┬────────────────────────────────────────┘     │
│                                         │ HTTP Ingest: NDJSON Stream                   │
│                                         │ /insert/jsonline?_stream_fields=...          │
│                                         ▼                                              │
│  ┌───────────────────────────────────────────────────────────────────────────────┐     │
│  │   VictoriaLogs Single-Server (StatefulSet)                                    │     │
│  │                                                                               │     │
│  │   ├── Storage Engine: Columnar block store with Bloom filters & 15x compress  │     │
│  │   ├── Streams: {app="polaris", level="...", loggerName="...", realmId="..."}  │     │
│  │   ├── Retention: 30 days automatic partition pruning                          │     │
│  │   └── Endpoints: Web UI (/select/vmui), LogsQL HTTP API, Health probes        │     │
│  └───────────────────┬───────────────────────────────────┬───────────────────────┘     │
│                      │                                   │                             │
│                      ▼                                   ▼                             │
│       ┌──────────────────────────────┐   ┌──────────────────────────────┐              │
│       │ VMUI (Native Explorer)       │   │ Grafana Dashboard            │              │
│       │ - Ad-hoc debugging           │   │ - 5xx Spike Panels           │              │
│       │ - Live Tail streaming        │   │ - P99 Endpoint Latencies     │              │
│       │ - Exact word/error search    │   │ - Throughput Breakdown       │              │
│       └──────────────────────────────┘   └──────────────────────────────┘              │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Application Changes: Apache Polaris Configuration

To maximize ingestion efficiency, eliminate thread blocking, and avoid interfering with cluster-wide console log forwarders (e.g., existing Elastic/OpenSearch daemons), Polaris writes strictly formatted NDJSON to a dedicated shared volume.

### 3.1 Polaris `application.properties` / Quarkus Logging Configuration
```properties
# 1. Disable or isolate Console JSON if cluster daemons collect it
quarkus.log.console.enable=true
quarkus.log.console.format=%d{yyyy-MM-dd HH:mm:ss,SSS} %-5p [%c{3.}] (%t) %s%e%n

# 2. Enable File Logging to Shared Volume
quarkus.log.file.enable=true
quarkus.log.file.path=/logs/polaris.log
quarkus.log.file.format=%m%n
quarkus.log.file.rotation.max-file-size=500M
quarkus.log.file.rotation.max-backup-index=5
quarkus.log.file.rotation.rotate-on-boot=true

# 3. Enable Structured JSON Logging on File Handler
quarkus.log.file.json=true
quarkus.log.file.json.pretty-print=false
quarkus.log.file.json.record-delimiter=\n

# 4. Quarkus HTTP Access Log (Produces the access log string)
quarkus.http.access-log.enabled=true
quarkus.http.access-log.pattern="%h %u %t \"%r\" %s %b"
quarkus.http.access-log.category=io.quarkus.http.access-log

# 5. MDC Context propagation for multi-tenancy
quarkus.log.file.json.additional-field."app".value=polaris
```

### 3.2 Polaris Deployment Volume Mount (Kubernetes Pod Spec)
Attach the shared volume claim to the Polaris container:

```yaml
spec:
  containers:
    - name: polaris
      volumeMounts:
        - name: polaris-shared-logs
          mountPath: /logs
  volumes:
    - name: polaris-shared-logs
      persistentVolumeClaim:
        claimName: polaris-shared-logs-pvc
```

---

## 4. Shipper Implementation: Fluent Bit Specification

Fluent Bit is deployed as a single-replica `Deployment` mounting `polaris-shared-logs-pvc` as `readOnly: true`.

### 4.1 Access Log Regex Parser
Access log messages from Quarkus follow the format:
```text
192.168.194.1 - root [21/Aug/2026:21:24:33 +0000] "PUT /api/management/v1/... HTTP/1.1" 500 454
```
The parser extracts these into first-class numerical and string fields while preserving non-access logs (exceptions, application logs) seamlessly via `Reserve_Data On`.

### 4.2 State-Driven Table Request Deduplication (Lua Filter)
Polaris clients frequently poll table metadata (`GET /api/management/v1/realms/{realm}/catalogs/{cat}/namespaces/{ns}/tables/{tableName}`). In production workloads, this generates **~11M requests/day** for a largely static set of tables.
* The embedded Lua filter maintains an in-memory map of `{ table_name: last_seen_unix_epoch }`.
* If a table lookup has already been logged within the deduplication window (e.g., 24 hours / 86,400 seconds), subsequent logs are dropped (`return -1, 0, 0`).
* Non-GET requests (`PUT`, `POST`, `DELETE`), errors (`5xx`), and application traces bypass the deduplicator and are always forwarded.

### 4.3 Complete Helm Values: `fluent-bit-file-shipper.yaml`
```yaml
kind: Deployment
replicaCount: 1

resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 512Mi

extraVolumes:
  - name: polaris-logs
    persistentVolumeClaim:
      claimName: polaris-shared-logs-pvc

extraVolumeMounts:
  - name: polaris-logs
    mountPath: /logs
    readOnly: true

config:
  service: |
    [SERVICE]
        Flush         1
        Log_Level     info
        Parsers_File  parsers.conf
        Parsers_File  custom_parsers.conf
        HTTP_Server   On
        HTTP_Listen   0.0.0.0
        HTTP_Port     2020

  customParsers: |
    [PARSER]
        Name        quarkus_access_log
        Format      regex
        Regex       ^(?<client_ip>[^ ]+) - (?<user_principal_name>[^ ]+) \[[^\]]+\] "(?<http_method>[A-Z]+) (?<api_path>[^ ]+) [^"]+" (?<http_status>\d+) (?<response_size>\d+)
        Types       http_status:integer response_size:integer

  inputs: |
    [INPUT]
        Name              tail
        Path              /logs/polaris.log
        Tag               polaris.vlogs
        Read_from_Head    true
        Parser            json
        Buffer_Max_Size   10MB
        Skip_Long_Lines   Off

  filters: |
    # 1. Parse Quarkus access log into typed fields (IP, Method, Path, Status, Size)
    [FILTER]
        Name          parser
        Match         polaris.vlogs
        Key_Name      message
        Parser        quarkus_access_log
        Reserve_Data  On

    # 2. Stateful 24-Hour Deduplication of GET Table Access Logs
    [FILTER]
        Name    lua
        Match   polaris.vlogs
        Inline  |
            seen_tables = seen_tables or {}
            WINDOW_SECONDS = 86400

            function filter_table_dedup(tag, timestamp, record)
                local method = record["http_method"]
                local path = record["api_path"] or ""

                if method == "GET" and string.find(path, "/tables/") then
                    local table_name = string.match(path, "/tables/([^/?]+)")
                    if table_name then
                        local now = os.time()
                        local last_seen = seen_tables[table_name]

                        if last_seen and (now - last_seen) < WINDOW_SECONDS then
                            return -1, 0, 0
                        end
                        seen_tables[table_name] = now
                    end
                end

                -- Periodically clean up expired entries
                if math.random(1, 1000) == 1 then
                    local now = os.time()
                    for tbl, t in pairs(seen_tables) do
                        if (now - t) > WINDOW_SECONDS then
                            seen_tables[tbl] = nil
                        end
                    end
                end

                return 0, timestamp, record
            end
        Call    filter_table_dedup

    # 3. Standardize metadata keys for VictoriaLogs
    [FILTER]
        Name          modify
        Match         polaris.vlogs
        Add           app polaris
        Rename        message _msg
        Rename        timestamp _time

  outputs: |
    # Native VictoriaLogs HTTP JSONLine endpoint with dynamic stream partitioning
    [OUTPUT]
        Name          http
        Match         polaris.vlogs
        Host          vlsingle-victoria-logs-single-server.logging.svc.cluster.local
        Port          9428
        URI           /insert/jsonline?_msg_field=_msg&_time_field=_time&_stream_fields=app,level,loggerName,mdc.realmId
        Format        json_lines
        Header        Content-Type application/json
```

---

## 5. Storage & Search Backend: VictoriaLogs Specification

VictoriaLogs serves as the unified storage and query engine. It automatically indexes words and JSON properties inside data blocks without maintaining memory-heavy inverted index structures.

### 5.1 Storage & Sizing Parameters (30-Day Retention)

| Metric | Normal Workload (Post-Dedup / Filter) | Peak Workload (Raw Unfiltered) |
| :--- | :--- | :--- |
| **Ingested Records / Day** | ~10,000,000 logs/day | ~140,000,000 logs/day |
| **Raw Uncompressed Data** | ~8 GB / day (~240 GB / month) | ~112 GB / day (~3.36 TB / month) |
| **VictoriaLogs Footprint** | **~15–25 GB / month** (10–15x compression) | **~220–350 GB / month** |
| **Allocated PV Size** | **50 GiB** (gp3 / local-path) | **500 GiB** |

### 5.2 Complete Helm Values: `vl-values.yaml`
```yaml
server:
  enabled: true

  # Automatic retention pruning (30 days)
  retentionPeriod: "30d"

  # Dynamic PVC provisioning via default StorageClass (e.g., gp3, local-path)
  persistentVolume:
    enabled: true
    size: 50Gi
    accessModes:
      - ReadWriteOnce
    # storageClassName: "gp3"

  # Resource bounds designed for sub-2s queries across 300M+ records
  resources:
    requests:
      cpu: "500m"
      memory: "1Gi"
    limits:
      cpu: "2000m"
      memory: "4Gi"

  # Service exposing Web UI and Ingestion API
  service:
    enabled: true
    type: LoadBalancer
    servicePort: 9428

  # Performance and graceful termination flags
  extraArgs:
    memory.allowedPercent: "60"
    http.maxGracefulShutdownDuration: "15s"

  livenessProbe:
    initialDelaySeconds: 15
    periodSeconds: 10
    timeoutSeconds: 5
    failureThreshold: 3
  readinessProbe:
    initialDelaySeconds: 5
    periodSeconds: 5
    timeoutSeconds: 5
    failureThreshold: 3

  ingress:
    enabled: false
```

---

## 6. Architectural Comparisons & Strategic Insights

### 6.1 Why Shipper vs. Direct Appender vs. Search Engine Parsers?

| Factor | Appender Direct Ingestion (Logback HTTP) | Engine File Parsers (Elastic Agent) | Dedicated Shipper (Fluent Bit) **[Chosen]** |
| :--- | :--- | :--- | :--- |
| **App Performance Impact** | High risk of blocking I/O on logging threads | None (Reads file asynchronously) | None (Reads local file from OS Page Cache) |
| **System Coupling** | High (App code directly coupled to backend) | High (Requires engine-specific agent pod) | Zero (Clean separation via standardized NDJSON) |
| **Spike Resilience** | Network timeouts drop logs or crash JVM | Moderate file-lag during spikes | Buffer queuing handles 140M daily spikes safely |
| **Transformation Power** | Inflexible (Java code changes required) | Tied to search engine ingest pipelines | Full Lua/Regex edge transformations before network |

### 6.2 Search Engine Evaluation: Why Non-Indexed Engines Fail the SLA

* **VictoriaLogs (Selected):** Leverages block-level metadata, stream pruning, and Bloom filters. It searches across 300M records in **0.2s–0.8s** using only **2–4 GB RAM**.
* **OpenSearch / Elasticsearch:** Can meet the 2s SLA, but requires **16–32 GB RAM**, JVM garbage collection tuning, index lifecycle management (ILM), and consumes **>300 GB disk** due to inverted index expansion.
* **Grafana Loki (Non-Indexed Text):** Chunks logs and indexes stream labels only. Searching for an unindexed `requestId`, stack trace substring, or arbitrary JSON field across 30 days of data requires decompressing hundreds of gigabytes of raw chunks on the fly. Queries routinely take **5 to 30+ seconds**, failing the operational SLA.
* **S3 Select / Athena / CloudWatch Grep:** Requires sequential byte scanning without indexing. Queries take **tens of seconds to minutes** with high per-query scanning costs.

---

## 7. LogsQL Production Query Recipes

Once logs are stored in VictoriaLogs, team members can query structured fields directly using LogsQL in VMUI or Grafana:

* **Find All Unhandled Server Exceptions in the Last 24 Hours:**
  ```text
  _time:1d AND _stream:{app="polaris", level="ERROR"} AND exception.exceptionType:*
  ```

* **Inspect HTTP 5xx Server Errors by Endpoint and Caller:**
  ```text
  _stream:{app="polaris"} AND http_status:>=500 
  | stats count(*) as err_count by (api_path, user_principal_name, http_status) 
  | sort by (err_count desc)
  ```

* **Trace a Specific Transaction End-to-End via MDC Request ID:**
  ```text
  mdc.requestId:"d67b7857-4263-4ae4-b94c-c05d7730c92e_0000000000000000006"
  ```

* **Filter Slow Responses (> 10KB response payload on GET requests):**
  ```text
  http_method:"GET" AND response_size:>10240
  ```

* **Sample 1 Unique Stack Trace per Error Type (On-Demand Deduplication):**
  ```text
  level:ERROR | uniq by (_msg, loggerName)
  ```

---

## 8. Post-Processing, Metrics Extraction & Webhooks

To extend the pipeline beyond interactive debugging without burdening the application:

1. **Immediate Webhook Triggering (Shipper Level):**
   Use Fluent Bit's `rewrite_tag` filter on `Rule $level ^(ERROR|FATAL)$` to route critical exceptions directly to a Slack or PagerDuty webhook URL via an auxiliary HTTP output plugin.
2. **Threshold Alerting (`vmalert`):**
   Deploy `vmalert` to query VictoriaLogs every minute (e.g., `http_status:>=500 | count() > 100`). Alerts are routed to Prometheus Alertmanager.
3. **Log-to-Metric Downsampling:**
   Use `vmalert` recording rules to extract numeric time-series (e.g., requests/second by endpoint, error rates) and store them in VictoriaMetrics. This enables multi-year trend analysis without needing to store raw log files indefinitely.
