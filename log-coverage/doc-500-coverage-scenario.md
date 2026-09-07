# Coverage: 500 error — the full test scenario

**Status: written 2026-09-07, NOT YET RUN.** Every expected status below marked **[assumed]**
has never been observed on this build. The point of the run is to replace those markers.

Read `PLAN-log-coverage-v3.md` for the policy and `PLAN-log-coverage-schema-v2.md` for the
report schema. This file is only the 500 scenario: what is driven, what is asserted, and what
each possible outcome means.

---

## 1. Why this exists

`neg.500_null_pointer` returned **200 for three consecutive runs**. Its provocation
(`create_catalog_no_endpoint`) omits `endpointInternal` *only* and still sets `endpoint`, and
this build falls back to `endpoint` — so the NullPointerException it is named for cannot happen.
Nothing caught it: nothing asserted on the probe's status, and the results document rendered
*"0 of 0 WARN/ERROR records carried an exception object"*, which reads like a measurement of the
pipeline and is a measurement of a dead probe.

Every 500 this pipeline has ever stored arrived **by accident**, from the PG-HA read-after-write
failures on `create_namespace` / `create_view`. Those are writes that **committed** — on
2026-09-01 `load_view`, `head_view`, `rename_view` and `drop_view` all answered 2xx after one —
so they say nothing about the unhandled-exception path in either direction.

**Consequence: `errors_5xx` has never been exercised against the real pipeline, and whether a
stack trace survives has only ever been answered from records nobody asked for.**

---

## 2. A 500 is TWO records

This is the whole shape of the test. A check that looks at one half passes while the other is
missing.

| half | loggerName | rule | disposition | carries |
|---|---|---|---|---|
| access-log line, `http_status 500` | `io.quarkus.http.access-log` | **3** | kept **and** counted — every access-log record is counted before any keep/drop decision | `access_seen`, `errors_kept`, `errors_5xx`, the row's `errors` |
| application line | the handler's own logger | **2 → 1** | kept, counted into **nothing** | the throwable, as **flattened** `exception.frames` |

They join on `mdc.requestId`.

---

## 3. Preconditions

| # | gate | abort if |
|---|---|---|
| P1 | port-forwards up: VictoriaLogs `9428`, Fluent Bit metrics `2020` | cell 0 cannot reach either |
| P2 | running ConfigMap carries the policy under test | sha mismatch |
| P3 | `POLICY.schema_version == lc.SCHEMA_VERSION` | the oracle is a schema version behind — **this is what aborted the 2026-09-07 run** |
| P4 | the report array splits into three `report_type`s | one record with numeric-keyed fields |
| P5 | `WINDOW_SECONDS` read from the deployed script, never hardcoded | currently **30** (fast-run, temporary) |

`env`: `local` only. Every rung creates and deletes a catalog; none of it is PROD-safe and none
of it is meant to run anywhere else.

---

## 4. The provoker ladder

Tried cheapest first, **stopping at the first rung that actually returns ≥ 500**. Every rung is
API-only, creates its own catalog, and deletes it in `cleanup` with `purge=False`.

| # | rung | what is wrong | fails at | expected |
|---|---|---|---|---|
| 1 | `black_hole_endpoint` | **both** `endpoint` and `endpointInternal` point at `127.0.0.1:1` | TCP connect — `ConnectException`, refused instantly | 500 **[assumed]** |
| 2 | `unresolvable_host` | both endpoints point at `…svc.invalid:9000` | DNS — `UnknownHostException` | 500 **[assumed]** |
| 3 | `nonexistent_bucket` | catalog's bucket does not exist in MinIO | bucket lookup on first write | 500 **[assumed]** |
| 4 | `stale_entity_version` | PUT `/catalogs` with `currentEntityVersion − 5` | optimistic lock | **409, not 500** [assumed] — `update_catalog`'s own docstring says so, so this rung may be unable to fire at all |

**Rungs 1 and 2 are separate on purpose.** DNS resolution and TCP connect are different layers
and the S3 client may handle them in different code paths, so one can 500 where the other does
not. A ladder testing only one would report NOT PROVOKED with the answer sitting in the next rung.

**Why `127.0.0.1:1` and `.invalid`, and not a plausible-but-wrong host.** Both fail *fast*. A
routable-but-dead host would **hang**, and a hang leaves **no access-log line at all** — the one
failure this pipeline is structurally blind to — so the probe would be measuring the blind spot
instead of the ERROR path. `.invalid` is reserved by RFC 2606, so the lookup cannot accidentally
resolve to something real.

**Why `purge=False`.** `purgeRequested=true` asks Polaris to delete the underlying files, i.e.
to talk to the storage endpoint the rung just broke. That hangs, or provokes a second, untagged
500 during teardown. (The retired `NPE_CAT` cleanup used `purge=True`.)

### Not in the ladder, and why

| candidate | reason |
|---|---|
| **wrong MinIO credentials** | `storageConfigInfo` carries no credentials — Polaris uses **static, server-side** creds shared by every catalog (`purge/doc-purge-minio-issue-briefing.md`: *"falls back to the static MinIO creds"*). Making them wrong is a `local-k8s` deployment change that breaks **every** catalog and needs a Polaris restart — and a restart mid-run voids the run (§7). Not client-reachable, so not a rung. |
| **wrong endpoint at catalog CREATE** | Polaris does not validate storage config on `POST /catalogs` (`error-cases/23`: *"Catalog create succeeds — Polaris does not verify bucket"*). It returns **201**. That is why every rung creates the catalog, then creates a **table**. |
| **a server-side hang** | leaves no access-log line at all; cannot be provoked from a client. |
| **429** | `rateLimiter.type: no-op` — the limiter cannot produce one. |

---

## 5. The scenario, step by step

### S1 — wait for a window boundary (§5c)

`V.seconds_to_boundary(WINDOW_SECONDS, lag=0)`, then sleep. **The burst must be pure.** Driving
only 500s into a fresh window is what turns `errors_4xx == 0` and `auth_denied == 0` from
observations into **predictions**.

### S2 — walk the ladder (§5c)

Each rung: `prepare()` (create catalog + namespace — the namespace must **succeed**, so the
window has a resource key that was read cleanly) → drive **3 × `create_table`** → `cleanup()`.
Stop at the first rung returning ≥ 500.

Three calls, not one, because **rule 3 keeps errors with no cap** and one call cannot show the
absence of a cap.

### S3 — record which window, and whether the burst fits

`window_bounds(t0)` vs `window_bounds(t1)`. **A burst that straddles a boundary is a VOID
group** — detected and reported, then re-driven. Never reasoned about
(`PLAN-log-coverage-schema-v2` §2).

### S4 — the rest of the run proceeds normally

The 500 rows join `ALL_CALLS`, so they appear in the coverage matrix, the correlation count and
the volume reconciliation like any other call.

### S5 — assert, once the report windows are in (§11c)

Cells 10 and 11b must have run first; §11c only reads.

---

## 6. Assertions

### 6.1 Record level — both halves

| # | assertion | VOID when |
|---|---|---|
| A1 | a deliberate 500 was driven at all | — (this is the NOT PROVOKED gate) |
| A2 | every 500 kept its access-log line (rule 3, no cap) | nothing driven |
| A3 | the kept access line really carries `http_status 500` | nothing driven |
| A4 | every 500 left **at least one** application line (rule 2 → rule 1) | nothing driven |
| A5 | the trace survives where the 500 was **unhandled**, under its flattened name | **every 500 was handled** — see below |
| A6 | the payload is **queryable** in VictoriaLogs, not merely present | as A5 |

**A4 does not care about the level.** Rule 2 keeps every non-access-log record untouched,
whatever its level, so an INFO or WARN line satisfies it.

### 6.2 The three trace verdicts — only one accuses the pipeline

| verdict | what was seen | what it means |
|---|---|---|
| `unhandled` | application line **with** a throwable | the trace survived end to end. **The outcome this section exists to demonstrate.** |
| `handled` | application line(s), **no** throwable | Polaris **caught** the failure, mapped it to a 500, and logged it without attaching the exception. **Nothing was lost — there was never a trace to carry.** A fact about the *provocation*. |
| `absent` | **no** application line at all | rule 2 forbids this. Either the pipeline dropped it, or Polaris logged nothing for the failure. **The only one that is a pipeline finding.** |

A check that asks only *"did a trace arrive?"* collapses the first two, and their remedies are
opposite: change the probe, or fix the shipper.

### 6.3 Window level — the pure-500 burst

| # | assertion | why this comparison |
|---|---|---|
| W0 | the window carries the v2 error split | **absent is not zero.** A missing field read as `0` reports PASS for a measurement nobody took |
| W1 | `errors_5xx >= driven` | **≥**: neighbour traffic and an accidental PG-HA 500 land in the same window and can only add |
| W2 | `errors_4xx == 0` | **==**: nothing driven into a pure-500 burst can add a 4xx. An inequality here would pass a filter that charged the 500 to the wrong counter — the exact bug the split exists to catch |
| W3 | `auth_denied == 0` | as W2 |
| W4 | `auth_denied <= errors_4xx` | schema-v2 §1.2 |
| W5 | `errors_4xx + errors_5xx <= errors` | **inequality on purpose**: a record with no parsable status is an error charged to neither half, deliberately, so "client errors" does not absorb the pipeline's own failures |
| W6 | `sum(resource.errors_5xx) == sum(principal.errors_5xx)` | the margin — two independently built row sets |
| W7 | `errors_5xx:>0` matches in LogsQL | `type_int_key`. A counter stored as the string `"3.0"` renders in every count and matches no range filter, **silently** |

### 6.4 Also asserted, from the oracle side (pytest, no cluster needed)

- a 500 access record is **kept and counted**; the application ERROR line is **kept and counted
  into nothing**;
- a 500 on a resource never read successfully lands in `__other__` and **does not create a key**;
- `classify_500s` separates `deliberate` / `read_after_write` / `unknown`, and an unrecognised
  500 stays `unknown` rather than being folded into either bucket.

---

## 7. What invalidates the run

- **the burst straddled a window boundary** → the window-level assertions are VOID; re-drive.
- **the shipper pod restarted** → counters are per-process, `report_seq` restarts at 1, the
  window is flagged `partial_window`. The run is void.
- **Polaris restarted or scaled** → recorded either side; a change voids it.
- **a `helm upgrade` mid-run** → the tail DB is on an `emptyDir` with `Read_from_Head true` and
  VictoriaLogs does not deduplicate on ingest, so the whole file replays. **A window whose
  `min`/`max_record_time` span is far wider than `window_seconds` is a replay, not a spike.**
- **the MacBook slept** → the OrbStack VM suspends with it, windows never open, `windows_skipped`
  is large. Expected, not a fault — but no measurement spanning a sleep is elapsed time.

---

## 8. Possible outcomes, and what each one means

| outcome | reading |
|---|---|
| a rung fires, verdict `unhandled` | **full coverage.** `errors_5xx` exercised, trace demonstrated end to end, question 3 answered from a driven 500 |
| a rung fires, verdict `handled` | `errors_5xx` and both halves are covered; **the trace question stays open** and needs a rung that provokes an *unhandled* exception. Not a pipeline fault |
| a rung fires, verdict `absent` | **a pipeline finding.** Rule 2 says the line should be there |
| every rung returns 2xx | **NOT PROVOKED.** 500 coverage unavailable on this build; question 3 stays NOT ANSWERED. The accidental PG-HA 500s are **not** substituted. Remaining options are `PLAN-log-coverage-schema-v2` §4: add a rung, or state in the results that ERROR-path coverage is *opportunistic and not repeatable* |

---

## 9. What the run settles

1. Does **any** rung provoke a 500 on this build, and which — all four are `[assumed]`.
2. Is the 500 **handled or unhandled** — i.e. is there a throwable to carry at all.
3. Does `errors_5xx` move, and does the split charge it to the right counter.
4. Is `errors_5xx` stored as a **number**.
5. Whether `error-cases/09_500_null_pointer` can be repaired the same way, or should be retired
   like `neg.500_null_pointer` was.
