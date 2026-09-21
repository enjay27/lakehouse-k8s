# HANDOFF — a traffic notebook that ends in OpenSearch, for the **polaris-logging** project

**Written to be read cold, from a session in the Polaris project. Nothing here assumes you have seen
`local-k8s`.** Everything about the pipeline you are testing is restated below rather than linked.

**Why this is a handoff and not code.** The notebook belongs in the Polaris project: it is a *client* of
the pipeline, and `local-k8s` owns the pipeline itself. A draft was written here on 2026-09-21 and the
commit was removed for that reason — but the design survived the deletion, so it is written out below in
full, including the two defects the draft already hit. Build it there; don't rediscover these.

**Status markers.** **[verified]** = observed in a real record or a running object. **[from values]** =
read out of a values file. **[assumed]** = reasoning that has *not* been checked, and is the first thing
the notebook should settle. That distinction matters here more than usual: this repo's most expensive
failure was configuration that was written and never applied.

---

## 1. What the notebook is for

Generate traffic at Polaris in a deliberately chosen shape, then **read the result back out of OpenSearch
and show what the pipeline kept, what it only counted, and whether that matches what the policy says
should have happened.**

The second half is the point. Generating traffic is easy and has been done many times by hand; the part
that keeps getting redone differently each run is the reconciliation. The notebook should print **one row
per call**: what was sent, what the policy predicted, what the index actually holds.

It is **not** a functional test of Polaris. It is a log-generating harness, and its output is a statement
about observability: *if this endpoint broke tomorrow, would there be a record?* For several endpoints the
honest answer is "no, by design" — and showing that is half the value.

---

## 2. The system under test, as of 2026-09-21

| | | |
|---|---|---|
| cluster | `orbstack` | single-node OrbStack Kubernetes on a MacBook |
| namespace | `datahub-hynix` | everything. The old `logging` namespace is empty **[verified]** |
| Polaris | `benchmarks-polaris` | **1.6.0**, deployed 2026-09-18 **[verified]** |
| Polaris ports | **8181** app · 8182 Quarkus management | **[from values]** — 8182 has `/q/health`, it is **not** where the API lives. A notebook aimed at 8182 is a wasted afternoon |
| pipeline | `benchmarks-fluent-bit` | DaemonSet, tails `/var/log/containers/*.log`. **There is no second pipeline** — the PVC → VictoriaLogs shipper was removed 2026-09-18 **[verified]** |
| detail index | `polaris-logs-*` | selected Polaris records, policy v5 |
| report index | `polaris-report-*` | window summaries, schema v6 |
| OpenSearch | `https://192.168.194.1:9200` | runs in **Docker on the Mac**, outside the cluster. Self-signed: TLS verify off **[from values]** |
| window | `WINDOW_SECONDS` **30** running, **3600** is the decided operational value | see §8 |

Polaris writes **no log file**. Everything goes to stdout and reaches OpenSearch through the DaemonSet.

### Auth **[assumed — settle this first]**

- Realm header name: **`Polaris-Realm`** is assumed, never verified. Realms are `[POLARIS, DATACORP-PROD]`
  with `requireHeader: true` **[from values]**, so a wrong header name fails *everything*, and the reason
  surfaces late.
- Token: `POST /api/catalog/v1/oauth/tokens`, **form-encoded** (not JSON),
  `grant_type=client_credentials`, `scope=PRINCIPAL_ROLE:ALL`.
- Bootstrap credentials: secret `polaris-persistence-secret`, key `bootstrapCredentials`, format
  `REALM,client_id,client_secret` **[from values]**.
- **Credentials come from the environment, never from a committed file.**

---

## 3. The policy the notebook is testing

Policy v5. A record is either **kept** (stored as its own document in `polaris-logs-*`) or **counted**
(it exists only as a number in the report). "Not stored ⇒ counted" is the invariant the whole design
exists to protect.

| rule | what | outcome |
|---|---|---|
| 1 | `level` ERROR or WARN | **kept**, regardless of the app allowlist |
| 2 | app log whose `loggerName` is in `APP_ALLOW` (`IcebergExceptionMapper`, `PolarisServiceImpl`) | **kept**, held until its access line resolves |
| 3 | HTTP ≥ 400, or an unparsable access line | **kept**, all of them, no cap |
| 3' | **404** | **counted only** (`counted_404`), and the app logs of that request are dropped too (`app_dropped_404`) |
| 4 | PUT / DELETE / PATCH | **kept** |
| 5 | POST under `/api/management/` | **kept** — POST is the *create* verb, and counting it would make principals visible on deletion but not creation |
| 5' | POST on any other path (catalog data plane) | **counted only** |
| 6 | GET / HEAD with 2xx | **counted only** |

---

## 4. Preflight — and the one cell that matters

Check five things and **stop** if any fails: Polaris reachable; realm header accepted; token obtainable;
OpenSearch reachable; and the **live `window_seconds`, read off a report row rather than out of a file.**

Then do this, before generating any real traffic:

```python
# Provoke one deliberate 401. Rule 3 says a 401 MUST be stored, so if this document
# never arrives, the chain is broken -- and it is almost always the header name.
probe_rid = f"{TAG}-0002-preflightProbe-401"
requests.get(f"{POLARIS_BASE}/api/management/v1/principals",
             headers={REALM_HEADER: REALM, RID_HEADER: probe_rid,
                      "Authorization": "Bearer not-a-real-token"}, verify=False)

for waited in range(0, 61, 5):
    if waited: time.sleep(5)
    res = os_search("polaris-logs-*", {"size": 1,
          "query": {"term": {"mdc.requestId.keyword": probe_rid}}})
    if res["hits"]["total"]["value"]:
        break
else:
    raise SystemExit("chain is broken: check POLARIS_REQUEST_ID_HEADER (default X-Request-Id)")
```

**Ten seconds to prove notebook → Polaris → Fluent Bit → OpenSearch end to end**, instead of sending four
hundred requests and discovering afterwards that none of them can be found. Whether Polaris populates
`mdc.requestId` from `X-Request-Id` is **[assumed]** — this cell is what settles it.

---

## 5. The traffic

Every call carries `requestId = nb-<run>-<seq>-<op>-<expected status>`. Putting the expectation **in the
id** is what let the 2026-09-21 run find `#24` by eye: four ids ending `-400` had returned 500.

One call per branch, small and idempotent-ish, named after a run timestamp so reruns never collide:

| seq | call | rule | prediction |
|---|---|---|---|
| 1001–1003 | `POST /api/management/v1/catalogs`, ×2 `principals` | 5 | keep |
| 2001–2003 | `GET` catalogs, catalog, principals (2xx) | 6 | **count** |
| 3001 | `PUT` catalog | 4 | keep |
| 4001–4010 | `GET`/`DELETE` on names that do not exist (404 ×4) | 3' | **count**, and **0 documents** |
| 5001–5002 | no token / bad token (401 ×2) | 3 | keep |
| 6001–6002 | `POST`/`GET` catalog namespaces | 5'/6 | **count** |
| 9001–9004 | the DELETEs that clean up | 4 | keep |

---

## 6. The verification half

```python
# every document this run produced
res = os_search("polaris-logs-*", {"size": 1000,
      "query": {"prefix": {"mdc.requestId.keyword": TAG + "-"}}})

# one row per call: sent / predicted / actually stored
for c in CALLS:
    n = len([d for d in by_rid.get(c["rid"], []) if d.get("http_status") is not None])
    ok = (n > 0) == (c["expect"] == "keep")
```

A mismatch means **either the prediction is wrong (fix the docs) or the pipeline is wrong (open an
issue)**. The notebook must not guess which — print it and stop.

Then the window's report rows (`window_start.keyword:"<W>"`) and these assertions, all of which held on
2026-09-21:

```
access_kept == access_seen - access_counted
counted_404 <= errors_4xx
summary.errors_4xx  == sum(resource rows .errors_4xx)
summary.errors_5xx  == sum(resource rows .errors_5xx)
summary.bytes_total == sum(resource rows .response_bytes)      # note the field name differs!
0 documents with http_status 404
every document carries threadName and threadId, none carries ndc
```

⚠ **`bytes_total` on the summary is `response_bytes` on a resource row.** Joining them by the same name
produces a mismatch that looks like a pipeline fault and is not — it cost time on 2026-09-21.

⚠ **Query strings through `.keyword`, always.** `threadName.keyword`, `loggerName.keyword`,
`mdc.requestId.keyword`. Undeclared strings are `text` with `index: false` plus a `.keyword` sub-field, so
a `term` or `exists` on the bare name returns **zero, silently**.

---

## 7. Two defects the draft already hit

1. **A dead `POST /oauth/tokens` with no body** fired a real request before the form-encoded one, putting
   an unintended 4xx into the traffic on a `requestId` the real call then reused. `oauth/tokens` is the
   one call that is not JSON.
2. **Every catalog-scoped call assumed `createCatalog` had succeeded.** On this MinIO the
   `storageConfigInfo` can be rejected; the later calls then 404 — and **a 404 that means "setup failed"
   is indistinguishable in the index from a 404 that means "rule 3' suppressed this"**. Guard the
   catalog-scoped calls behind the create's status and *skip* them with an explanation rather than send
   them.

---

## 8. The window, and why it decides your feedback loop

`WINDOW_SECONDS` lives in the Lua filter. **Running value: 30 s. Decided operational value: 3600 s (one
hour)**, set 2026-09-21, retunable during monitoring with 1 h and 2 h as candidates.

- **Read `window_seconds` off a report row. Never assume it.** The notebook must work at both.
- The detail index is visible within seconds. **Report rows only exist once the window closes** — at
  3600 s that is up to an hour, so the notebook should say so and leave the summary half to be re-run,
  rather than blocking.
- Test while the window is still 30 s if you can. The round trip is about a minute.

---

## 9. What already exists here, worth reading before writing anything

| file (in `local-k8s`) | why |
|---|---|
| `logging/SPEC-polaris-audit-logging.ko.md` | the whole policy, indices, retention, known limits. Korean |
| `logging/GUIDE-sample-data-2026-09-21.ko.md` | **real sample documents of every type**, generated from an export. The shapes your queries must match |
| `logging/SCHEMA-report.md` | every report field, per schema version |
| `logging/scripts/step10-v4-window-readout.sh` · `step11-replay-window.py` | the existing readout and replay for one window — do not reimplement these |
| `logging/scripts/step14-sample-doc.py` | how to turn a Dev Tools export into documentation |
| `logging/scripts/devtools-json-fix.py` | Dev Tools panel copies are `"""`-quoted and are not valid JSON |
| `.memory/active-issues.md` | `#24`, `#42`, `#45`, `#46`, `#47` below |

## 10. Polaris-side traps that will show up in your results

- **`#24`** — four operations answer **500 to a malformed request**: `getToken`, `createNamespace`,
  `renameTable`, `renameView`. All NPEs, **all four reproduced on 1.6.0** on 2026-09-21. So `errors_5xx`
  is drivable by any client and is not a health signal on its own.
- **`#46`** — an errored request **cannot create a resource row** (deliberate key-space defence). If no
  successful request to that path came first *in the same window*, its 5xx lands in the `__errors__` row.
  Counts survive; attribution does not. To see a 5xx on its own resource row, send one 2xx to that path
  first.
- **`#45`** — `PolarisEventListeners` throws an NPE delivering `BEFORE_RENAME_TABLE`/`_VIEW` on 1.6.0.
  It is stored by rule 1, not by the allowlist.
- **`#42`** — `threadName`/`threadId` were removed on 09-16 and **restored on 09-18**. Query
  `threadName.keyword`.

## 11. Definition of done

1. Preflight passes, including the 401 chain proof.
2. Every call's prediction matches the index, or the mismatch is written up as an issue.
3. The invariants in §6 pass on the window the traffic fell in.
4. No credential in any committed file.
5. The run's `requestId` prefix and `window_start` are printed at the end, so the run can be found in
   Dashboards later.
