# Plan — a Jupyter notebook that exercises every Polaris API, to test what the log pipeline keeps

**Written to be read cold, from a new session in the Polaris project.** Nothing here assumes
you have seen `local-k8s`. Everything about the pipeline that this notebook is testing is
restated below rather than linked.

**Status of the facts in this document.** Anything marked **[verified]** was observed in a
real record or a running object. **[from values]** was read from a values file or a rendered
ConfigMap. **[assumed]** is reasoning that has *not* been checked and is the first thing the
notebook should settle. That distinction matters here more than usual: this repo's most
expensive failure was configuration that was written and never applied, and during the
session that produced this plan, four separate conclusions drawn from config files turned out
to be wrong about the running system.

---

## 1. What the notebook is for

Call **every API Apache Polaris 1.3.0-incubating implements**, so that the Fluent Bit →
VictoriaLogs pipeline is driven across every branch of its retention policy, and produce a
**coverage matrix**: for each endpoint, what the pipeline stored, and what it silently threw
away.

It is not an API client and not a functional test suite. It is a **log-generating harness**,
and its output is a statement about observability, not about Polaris correctness. The
question it answers is: *if something went wrong on this endpoint tomorrow, would there be a
record of it?*

Expect the answer to be "no" for several endpoints. Section 5 names the ones already known.

---

## 2. The system under test

### 2.1 Cluster

| | | |
|---|---|---|
| context | `orbstack` | single-node OrbStack Kubernetes on a MacBook |
| namespace | `datahub-hynix` | Polaris and the log shipper |
| namespace | `logging` | VictoriaLogs only |
| Polaris release | `benchmarks-polaris` | image `apache/polaris:1.3.0-incubating` **[from values]** |
| shipper release | `fb-polaris-shipper` | chart `fluent-bit-0.58.1`, app 5.1.1 **[verified]** |
| VictoriaLogs | `vlsingle-victoria-logs-single-server.logging` | port 9428, `LoadBalancer`, 30d retention |

**Ports — get this right before writing a single call.** `8181` is the application service.
`8182` is the **Quarkus management interface** (`/q/health`, `/q/metrics`) — it is *not* where
the Polaris Management API lives **[from values]**. The Polaris Management API is
`/api/management/v1/...` and the Iceberg REST API is `/api/catalog/v1/...`, and both are
**[assumed]** served on 8181. Confirm with one call before building anything on it; a whole
notebook aimed at the wrong port is a bad afternoon.

### 2.2 Auth and realms

- `authentication.type: mixed`, token broker `rsa-key-pair` **[from values]**.
- Bootstrap credentials live in the `polaris-persistence-secret` secret, key
  `bootstrapCredentials`, format `REALM,client_id,client_secret` **[from values]**.
- `realmContext.realms: [POLARIS, DATACORP-PROD]` with **`requireHeader: true`**
  **[from values]** — so **every request must carry the realm header** or it fails. The header
  name is **[assumed]** `Polaris-Realm`; verify it against the 1.3.0 source before assuming a
  400 is your bug rather than a missing header.
- Records carry `mdc.realmId: "POLARIS"` **[verified]**, so the realm is visible per record
  without any extra work.
- Token endpoint: `POST /api/catalog/v1/oauth/tokens`. **Read §5 rule 5 before relying on
  seeing those calls in VictoriaLogs — successful ones are deliberately dropped.**

Never print a token or a client secret into a notebook cell. Notebooks get committed.

### 2.3 The log path

```
Polaris (Quarkus, JDK21)
  └─ JSON per line → /deployments/logs/polaris.log        on PVC polaris-shared-logs-pvc
       └─ Fluent Bit `fb-polaris-shipper` (Deployment, 1 replica) tails it read-only
            ├─ [FILTER modify]          message→_msg, timestamp→_time, add app=polaris
            ├─ [FILTER lua]  polaris_access_log    parse the access-log line into fields
            ├─ [FILTER lua]  polaris_noise_filter  decide what is kept        ← §5
            ├─ [FILTER record_modifier] drop processName, loggerClassName, processId
            └─ [OUTPUT http] → VictoriaLogs /insert/jsonline
                              _msg_field=_msg  _time_field=_time  _stream_fields=app,level
```

There is a **second, independent** Fluent Bit — a DaemonSet shipping *container stdout* to an
OpenSearch running in Docker outside the cluster. It is not part of this test. If a log line
appears in OpenSearch but not VictoriaLogs, that is the DaemonSet, not this pipeline.

### 2.4 The shape of a stored record — **[verified]**, this is a real one

```json
{
  "_msg": "192.168.194.1 - user11_principal [03/Sep/2026:08:04:24 +0000] \"GET /api/catalog/v1/watchdog-catalog/namespaces/watchdog-ns/tables/watchdog-table HTTP/1.1\" 404 113",
  "_time": "2026-09-03T08:04:24.504420706Z",
  "_stream": "{app=\"polaris\",level=\"INFO\"}",
  "app": "polaris", "level": "INFO",
  "loggerName": "io.quarkus.http.access-log",
  "hostName": "benchmarks-polaris-585587454b-nhzdr",
  "threadName": "executor-thread-4", "threadId": "46", "sequence": "4168",
  "mdc.realmId": "POLARIS",
  "mdc.requestId": "dce356e7-539d-444f-a854-c9b17cf4a0a2_0000000000000000141",
  "client_ip": "192.168.194.1",
  "user_principal_name": "user11_principal",
  "http_method": "GET",
  "api_path": "/api/catalog/v1/watchdog-catalog/namespaces/watchdog-ns/tables/watchdog-table",
  "http_status": "404",
  "response_size": "113"
}
```

Note what is **not** there: no latency, no request body, no response body, no request headers.
Everything the notebook wants to correlate on has to come from a field in that list.

### 2.5 Access-log format

Quarkus pattern `%h %l %u %t "%r" %s %b` **[verified from the line shape]**. Two consequences
that shape the whole notebook:

- **There is no latency field.** `%D` is not in the pattern. Nothing in VictoriaLogs can tell
  you how long any request took.
- `%b` writes `-` for a zero-byte body; the parser normalises that to `0` **[verified]**.

---

## 3. The two correlation keys — design the notebook around these

The access log carries no custom fields, so tagging runs has to use something already in the
record. There are exactly two levers, and using both is what makes the coverage matrix
possible.

**`mdc.requestId` — the strong one.** Polaris is configured with
`logging.requestIdHeaderName: Polaris-Request-Id` **[from values]**, which means **the client
can supply the request id**. Send `Polaris-Request-Id: nb-<run>-<case>-<n>` on every call and
that value lands in `mdc.requestId` on the access-log record *and* on every application log
line the request produced. That is exact, per-call correlation across the whole pipeline, with
no parsing.

**Verify this first**, in the notebook's first cell: send a known id, query
`mdc.requestId:"..."` in VictoriaLogs, confirm it comes back. If Polaris ignores or rewrites
client-supplied ids, the entire correlation design changes and you want to know in minute one,
not hour three.

**`user_principal_name` — the fallback.** It is `%u` from the access log **[verified]**. Create
a principal per notebook run (`nb_<epoch>_principal`) and authenticate as it, and every record
from that run is selectable with `user_principal_name:"nb_1788417313_principal"`. Coarser than
the request id, but it survives even if the request-id header turns out not to be honoured.

---

## 4. Enumerating "ALL APIs" — make it a checklist, not a guess

Do not hand-write the endpoint list. Two OpenAPI documents define the surface; parse them and
generate the call list, so "all" is checkable:

- **Polaris Management API** — `spec/polaris-management-service.yml` in `apache/polaris` at tag
  `apache-polaris-1.3.0-incubating`.
- **Iceberg REST Catalog API** — the Iceberg `rest-catalog-open-api.yaml` vendored in the same
  tag.

Generate a table of `(method, path template, operationId)` and carry it through the notebook
as the master list. Every row ends up in the coverage matrix with one of: *called and stored*,
*called and deliberately dropped*, *called and unexpectedly absent*, *not callable* (with a
reason — needs cloud storage, needs a federated catalog, needs a feature that is off).

Several endpoints will be genuinely uncallable on this cluster. `ALLOW_OVERLAPPING_CATALOG_URLS`
is the only feature flag set **[from values]**, `rateLimiter.type: no-op` means **429 can never
be produced**, and `opa.enabled: false` means the OPA authorization paths are dead. Record
those as *not callable*, with the reason. An honest gap beats a fabricated pass.

---

## 5. The retention policy, and the limitation of each rule

This is the part the notebook exists to test. Rules are evaluated in order; **first match
wins**. Source: `logging/fb-values.yaml` in the `local-k8s` repo, function
`polaris_noise_filter`.

### Rule 1 — `level` is ERROR or WARN → **keep**

**Limitations.**
- Polaris logs very little at WARN or ERROR in normal operation. A *failed request* is usually
  not an ERROR log line at all — it is an access-log line with a 4xx status and nothing else.
  So this rule is not the safety net it looks like; **rule 3 is.**
- The intended exclusion for "Deprecated Config" **is not implemented** — there is a `TODO`
  hook in the function and nothing else. **Notebook job: capture every distinct WARN message
  the run produces, so the exclusion can be written narrowly.** A broad pattern here would
  silently discard real errors, which is the failure mode this whole exercise is against.
- **Untested: whether exception stack traces survive the pipeline.** Quarkus JSON puts a
  throwable in an `exception` object with a `stackTrace` field. No filter touches it, but no
  record with one has been observed. **Provoke a 500 and check.** If stack traces are being
  dropped or truncated, that is the single most valuable thing this notebook could find.

### Rule 2 — not an access-log record → **keep, untouched**

**Limitations.**
- Application logs pass through unfiltered, so whatever is noisy at DEBUG stays noisy. DEBUG
  is being turned off in production, after which application logs become sparse.
- Correlation to the access-log line is **via `mdc.requestId` only**, and that join is
  **[assumed]** to work — see §3. Verify it explicitly; the coverage matrix depends on it.

### Rule 3 — `http_status >= 400` → **keep**

This outranks deduplication deliberately: a 404 on a table GET is both "a table read" and "an
error", and errors win, so a client hammering a missing table stays visible.

**Limitations.**
- **Blind to anything that never produces a status.** The access log is written when the
  response is, so a request that hangs, times out, or has its connection dropped leaves *no
  line at all*. A Polaris hang is invisible to this pipeline. **The notebook should try to
  produce one** (a client-side timeout on a slow call) and confirm the absence, so the blind
  spot is documented rather than assumed.
- **Blind to slow-but-successful.** With no `%D`, a request that took 4 seconds and returned
  200 is indistinguishable from one that took 8ms.
- **429 is unreachable** — the rate limiter is `no-op`.
- A 500 that Quarkus turns into a 200 with an error body (if any endpoint does this) is
  invisible. Worth probing.

### Rule 4 — PUT / DELETE / PATCH → **keep**

**Limitations.**
- **The request body is not in the access log.** A PUT that changes a role's privileges is
  recorded as *"a PUT happened to this path, and it returned 200"*. **What changed is not
  recorded anywhere in this pipeline.** For an audit trail of grants, that is the whole point
  and it is missing.
- **Follow this up in the notebook**: perform a grant change, then search VictoriaLogs for
  *any* record carrying the granted privilege name. If nothing has it, the pipeline cannot
  answer "who granted what". Two candidate sources to investigate:
  - `org.apache.polaris.service.admin` at DEBUG — may log the body.
  - **The `eventListener` writes audit events to a PostgreSQL table**
    (`type: persistence-in-memory-buffer`, 5s flush, 1000-event buffer **[from values]**).
    That is a **second audit channel that does not go through VictoriaLogs at all.** It may
    well be the real source of "what changed", and if so the notebook should say so plainly —
    it changes where you would go during an incident.

### Rule 5 — POST on the table/view API → keep; **every other successful POST → DROP**

Kept paths are `/namespaces/{ns}/tables...` and `/namespaces/{ns}/views...`. Everything else
that POSTs and returns 2xx is discarded.

**Limitations — read this one carefully, it is the largest known gap.**
- **Management-API creates are POSTs, and they are being dropped.**
  `POST /api/management/v1/catalogs`, `.../principals`, `.../principal-roles`,
  `.../catalog-roles` all create objects and all return 2xx, and none of them match the kept
  patterns. Meanwhile `DELETE /api/management/v1/principals/{p}` **is** kept (rule 4).
  **The result is an asymmetric audit trail: you can see principals being deleted but not
  created.** This is almost certainly not intended, and the notebook should demonstrate it
  concretely — create a principal, delete it, then show that only the delete is in
  VictoriaLogs. That single before/after is the most persuasive output this notebook can
  produce.
- **Successful authentication is not recorded.** `POST /api/catalog/v1/oauth/tokens` returning
  200 is dropped by design. Failed auth (401) is kept by rule 3. So "who authenticated and
  when" is unanswerable; only "who failed" is.
- Namespace creation (`POST .../namespaces`) is dropped — it does not match
  `/namespaces/[^/]+/tables`.

### Rule 6 — GET / HEAD on a table or view → **first per KST day, rest dropped**

Day boundary is KST (UTC+9), derived from the record's own `_time`. Key is
`method + " " + api_path`, including any query string. State is two day-buckets in the
shipper's memory.

**Limitations.**
- **Access frequency is unrecoverable.** A table read once and a table read a million times
  produce the same one record. Total suppression is available from Fluent Bit's
  `fluentbit_filter_drop_records_total` at `/api/v1/metrics`, but there is **no per-table
  breakdown anywhere.**
- **Timing is unrecoverable.** Only the first read of the day is timestamped; you cannot tell
  whether the traffic was a morning burst or spread evenly.
- **Query strings split the key.** `/tables/t1` and `/tables/t1?snapshots=all` deduplicate
  separately. A client that varies query parameters defeats the rule entirely — worth testing,
  since Iceberg clients do send `?snapshots=`.
- **Sub-resources are separate keys.** `/tables/t1` and `/tables/t1/metrics` do not collapse
  into each other. Defensible, but know it.
- **`GET .../namespaces/{ns}/tables` (the LIST call) is not deduplicated at all** — the pattern
  requires a table name after `/tables/`. List calls can be just as noisy as reads. Currently
  every one is stored.
- **State is per-pod and in memory.** A shipper restart re-logs the first hit per table for the
  rest of that day. Accepted deliberately, but it means the notebook must not treat "exactly
  one record" as an invariant across a restart.
- **HEAD and GET are different keys**, so an Iceberg client doing `tableExists` then `loadTable`
  stores two records rather than one.

### Rule 7 — everything else → **keep**

**Limitations.** `GET /api/catalog/v1/config` is polled by every Iceberg client on connect and
is stored every single time. Namespace listings likewise. This rule is where the next round of
noise reduction will happen, and the notebook's volume numbers are what should decide it.

---

## 6. Pipeline-level limitations, independent of any rule

| limitation | consequence for the notebook |
|---|---|
| **No `%D`** — no latency anywhere | cannot test slow-request detection; measure client-side and report the gap |
| **Tail DB is on an `emptyDir`** | a `helm upgrade` of the shipper replays the whole log file once. **Records can legitimately appear twice.** Deduplicate by `mdc.requestId` when counting |
| **Dedup state lost on shipper restart** | "exactly one per day" is not an invariant across restarts |
| **HPA: Polaris can scale to 3 replicas at 80% CPU**, all appending to one shared log file | **do not drive enough load to trigger it.** Interleaved writers and independent rotation would corrupt the file and invalidate the run. Check `kubectl get hpa -n datahub-hynix` before and after |
| `Read_from_Head true` on the tail | on a fresh shipper pod the whole file is re-read |
| VictoriaLogs has **no disk cap** and 30d retention | a very large run can fill the PV; a full PV wedges the pod |
| ingest is asynchronous | allow a few seconds between the call and the LogsQL query; poll, do not sleep-and-hope |
| `_stream_fields=app,level` | all records live in ~2 streams; every other field is searchable but not a stream selector |

---

## 7. Notebook structure

**0 — Preflight.** Cluster context is `orbstack`; Polaris pods `Running`; `kubectl get hpa`
recorded; shipper pod name and start time recorded (so a restart mid-run is detectable);
VictoriaLogs reachable. Abort loudly on any failure rather than producing a misleading matrix.

**1 — Config and auth.** Base URLs, realm header, token. Create the run's principal.
**Verify the `Polaris-Request-Id` round-trip before anything else** (§3).

**2 — Endpoint inventory.** Parse both OpenAPI specs → master list (§4).

**3 — Happy path, in dependency order.** catalog → principal → roles → grants → namespace →
table → view → commit → read → list → delete. Every call tagged with its own request id.

**4 — Negative cases.** 404 (missing table), 401 (bad token), 403 (insufficient privilege),
409 (concurrent commit conflict — two writers on one table), 400 (malformed body), 405, and an
attempted timeout. These drive rule 3, which is the pipeline's real safety net.

**5 — Policy probes.** Deliberate tests of the rules themselves:
- same table GET ×20 → expect **1** stored
- same table GET with and without `?snapshots=all` → expect **2**
- GET a *missing* table ×20 → expect **20** (errors outrank dedup)
- HEAD then GET the same table → expect **2**
- create a principal, then delete it → expect the delete only, **demonstrating §5 rule 5**
- successful token request → expect **0** stored
- a table LIST ×20 → expect **20** (not deduplicated)

**6 — Collection.** Wait for ingest, then pull every record for the run from VictoriaLogs by
`user_principal_name`, and per-call by `mdc.requestId`.

**7 — The coverage matrix.** One row per endpoint from §4: called? status? stored? expected to
be stored? **discrepancy?** Plus a list of every distinct WARN/ERROR message seen, and whether
any record carried an `exception` object.

**8 — Findings.** Written for someone who was not there.

---

## 8. What this notebook should send back

Concrete answers to open questions, each of which is currently blocking a change:

1. **Every distinct WARN message** → so the "Deprecated Config" exclusion can be written
   narrowly instead of broadly.
2. **Where a PUT's request body is logged, if anywhere** — and whether the PostgreSQL
   `events` table is the real audit channel for "what changed".
3. **Whether `exception` / stack traces survive the pipeline.**
4. **Whether `mdc.requestId` reliably joins application logs to their access-log line.**
5. **A demonstrated count** of the create/delete audit asymmetry in §5 rule 5.
6. **Volume numbers** — records per API call, and `fluentbit_filter_drop_records_total` before
   and after — to decide whether rule 7 needs narrowing.
7. **A latency measurement taken client-side**, as the evidence for adding `%D`.

---

## 9. Ground rules

- **Do not change Polaris configuration.** It works and ships continuously. There is an
  unexplained discrepancy — the running config reads `quarkus.log.file.enabled=false` while a
  file is demonstrably being written and tailed — which is recorded in `local-k8s`
  `.memory/active-issues.md` #11 as *unexplained, not pursued*. **Do not act on that reasoning
  alone**, and do not "fix" it as a side effect of this work.
- **Verify against the running object, not against a values file.** In the session that
  produced this plan, four conclusions drawn from configuration files were wrong about the
  running system. `helm get values` is also an intent artifact — it shows *inputs*. The
  ConfigMap, the pod environment and an actual stored record are the truth.
- **Never print tokens or secrets into a cell.** Notebooks get committed.
- **Clean up what you create.** Catalogs, principals, roles, namespaces, tables. A failed run
  should still leave the cluster usable — and note that the cleanup DELETEs are themselves
  part of the test.
