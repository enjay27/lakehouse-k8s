# HANDOFF — six captures banked, the EXPLAIN sweep is what remains

Written 2026-08-31. Standalone: everything needed to run the next task is here.

Supersedes the measurement half of `HANDOFF-privilege-scan.md`. That document's
Phase 1 and Phase 2 are done; its Phase 3 (the report) is the next task, at a
volume and surface it did not anticipate.

---

## 0. Where this stands in one paragraph

The privilege-query index audit now has **six captures — three identity tiers ×
two index states — every one driven at the same measured volume of 60,782
`grant_records`.** Nothing has been EXPLAINed yet at that volume, so the
Seq→Index contrast the whole audit exists for is **banked but not yet read**.
The next task is a pure analysis pass: correlate each capture, replay each
distinct statement under `EXPLAIN (ANALYZE, BUFFERS)` on the primary, and write
the report. No drives are needed. The expensive part is done.

---

## 1. The fixtures

Three tiers, all seeded by API, all real. Credentials were set by Kade's manual
`principal_authentication_data` UPDATE (the seeder still discards secrets —
Active Issue, unchanged).

| prefix | n | privileges | entities | grant footprint |
|---|---:|---|---|---:|
| `user` | 1000 | 50 | 2 namespaces, no tables | **52** |
| `authz` | 100 | 50 | 2 ns, 5 tables, 2 views, 1 policy, 1 generic table | **52** |
| `admin` | 5 | 50 + `service_admin` | 2 ns, 5 tables, 2 views | not measured (~1,100 by construction) |

**The `user` and `authz` footprints are identical and uniform** — n=100,
min=p50=p95=max=52, measured with `--footprint`. So those two tiers sit at the
same point on the Seq-vs-index curve and their numbers ARE comparable. 52 = 50
granted + 2 held by the identity's own chain (the principal as grantee of its
principal-role assignment, the principal-role as grantee of its catalog-role
assignment). The other 3 of the seeder's `grant_overhead_per_user = 5` belong to
`catalog_admin` and `service_admin` — different grantees, so they never appear
in this identity's lookup.

`admin` is **not** footprint-comparable and its profile says so
(`footprint_must_match=None`). `service_admin` gains one grant per catalog, so
its grant set grows with the REALM rather than with its own privileges.

Ledgers are per-prefix: `capture/seed_ledger.json` (user, unsuffixed for
backward compatibility), `seed_ledger-authz.json`, `seed_ledger-admin.json`.

---

## 2. The six captures — this is the table to work from

All at **60,782 `grant_records`** (counted, not projected).

| tier | index | capture dir | run id | ops | requests | elapsed |
|---|---|---|---|---:|---:|---:|
| user | absent | `capture-user-noindex-2` | `privscan-20260831-110305` | 7 + 6 refused | 15,000 | 148.9 s |
| user | present | `capture-user-index` | `privscan-20260831-111114` | 7 + 6 refused | 15,000 | 87.0 s |
| authz | absent | `capture-authz-noindex` | `privscan-20260831-105310` | 21 | 2,700 | 27.7 s |
| authz | present | `capture-authz-index` | `privscan-20260831-111200` | 21 | 2,700 | 19.7 s |
| admin | absent | `capture-admin-noindex` | `privscan-20260831-105456` | 26 | 160 | 2.6 s |
| admin | present | `capture-admin-index` | `privscan-20260831-111255` | 26 | 160 | 1.7 s |

Every run: 0 non-2xx, 0 auth failures, 0 skipped.

**`privscan-20260831-105120` is a SUPERSEDED authz no-index run** (2,700 req,
33.7 s). `capture-authz-noindex` was proven live for `105310`, not for it.
Correlating the wrong one is a live foot-gun; the pairings above are the ones.

**`privscan-20260824-123408` / `capture-scan-noindex-2` is the OLD user
no-index pass at 55,004 rows.** Keep it — it is the evidence behind the
7.27-statement prelude and the 403 finding, both volume-independent — but do NOT
use it for the index contrast. The realm has grown ~10% since.

### The clock, and why it is not the finding

Elapsed dropped on all three tiers when the index appeared: 148.9→87.0 (−41%),
27.7→19.7 (−29%), 2.6→1.7 (−35%). Consistent direction across three independent
fixtures.

**Do not put this in the report as a result.** Every one of these passes ran
with statement logging ON, a measured 4.6× inflation, and this repo has watched
the same plan measure a 4.6× clock spread. It is a HINT that the EXPLAIN sweep
should confirm with buffers and rows-filtered, which are identical across runs.
Real latency is Pass B, logging off, and has not been run.

---

## 3. What is measured, and what is not

### Measured

- **7.27 statements per authenticated request**, across 15,002 requests. The
  "7-statement authorization prelude" was asserted from source until then.
- **A 403 pays the FULL prelude.** 6,000 refusals issue the same five statement
  shapes as a permitted request, including 1.00 `grant_records` grantee lookup.
  Authorization cost is paid BEFORE the authorization decision, so a caller
  hammering endpoints it has no rights to costs what real work costs.
- **The GET surface is 29 GET/HEAD operations**, and the suite reaches **29 of
  29** across tiers (`scan_privileges.py --union`).
- **Neither admin tier is a superset of the ordinary one.** `service_admin`
  reads every management API and is REFUSED credential vending; its own 403
  names what it activated: `activated grants via '[service_admin,
  catalog_admin]'`. The catalog-scoped `owner_principal` is the reverse.
  Administrative authority and DATA authority are separate in Polaris.
- **Polaris has no service-level grant API.** `GrantResource` is
  catalog / namespace / table / view / policy; `SERVICE_MANAGE_ACCESS` is in
  none of them. Membership in the bootstrapped `service_admin` role is the only
  route.

### NOT established — do not imply otherwise

- **The Seq→Index contrast at 60,782.** This is the headline and it is exactly
  what the next task produces. No valid index-absent EXPLAIN exists at any
  volume: the only attempt (`qprofile-20260824-123408`) errored on 7 of 8
  statements from the `?`-placeholder and normalized-SQL bugs, and was at
  55,004.
- **Latency.** Pass B (logging off) has not been run.
- **Write paths.** Read-only by construction; four write statements remain
  `NO_PARAMS` and unmeasured.
- **`admin`'s footprint.** Assumed ~1,100 from `service_admin`'s
  one-grant-per-catalog property. Never measured. Run `--footprint --profile
  service-admin` before quoting it.

---

## 4. THE NEXT TASK

Correlate all six, EXPLAIN each, write the report. **No cluster writes except
the two index toggles.**

### 4.1 Reconcile first — free, and it needs no database

```bash
cd diagnostics/api-sql-profile
python3 profile_queries.py --capture capture-user-index --run privscan-20260831-111114
```

Read the reconciliation before spending an EXPLAIN sweep. A capture that
disagrees with its run JSON is describing a subset, and every figure downstream
inherits that. `+2` is expected and named (`assert_capture_live`'s own token
call and `get_catalog`); harness-preparation labels (`[ns-resolve]`,
`[entity-resolve]`) fold onto their base op and the fold is printed.

### 4.2 EXPLAIN the index-PRESENT half — the database is in that state NOW

```bash
python3 profile_queries.py --capture capture-user-index  --run privscan-20260831-111114 \
    --index-state present --explain --report
python3 profile_queries.py --capture capture-authz-index --run privscan-20260831-111200 \
    --index-state present --explain --report
python3 profile_queries.py --capture capture-admin-index --run privscan-20260831-111255 \
    --index-state present --explain --report
```

`--index-state` is REQUIRED with `--explain` and is checked against live
`pg_indexes`. **EXPLAIN replays against the database as it is, not as it was** —
without the check, EXPLAINing a no-index capture today would staple Index Scan
plans onto a Seq Scan drive, with the statement counts from one cluster state
and the plans from another.

### 4.3 Flip the database, take the other half

```bash
python3 drop_grantee_index.py
#   then on the PRIMARY: ANALYZE polaris_schema.grant_records;

python3 profile_queries.py --capture capture-user-noindex-2 --run privscan-20260831-110305 \
    --index-state absent --explain --report
python3 profile_queries.py --capture capture-authz-noindex --run privscan-20260831-105310 \
    --index-state absent --explain --report
python3 profile_queries.py --capture capture-admin-noindex --run privscan-20260831-105456 \
    --index-state absent --explain --report

#   then restore:
#   CREATE INDEX CONCURRENTLY idx_grant_records_grantee
#       ON polaris_schema.grant_records (realm_id, grantee_catalog_id, grantee_id);
#   ANALYZE polaris_schema.grant_records;
```

`ANALYZE` after each toggle is not optional: a planner working from stale
`reltuples` will choose a path for a table size that no longer exists.

### 4.4 The report

Six `runs/qprofile-*.json` and six Markdown reports come out of the above. The
deliverable is **one document** that puts them together:

1. **The grantee lookup, absent vs present, at 60,782** — plan shape, shared
   buffers, rows removed by filter, rows returned. This is the headline and the
   only part that must be exactly right. Buffers and rows-filtered are identical
   across reruns; the milliseconds are not, and this pass's clock is discarded.
2. **Per-API index usage across 29 operations**, from the authz and admin
   passes. Everything on `entities` is expected to be an index scan already
   (`idx_entities` / `constraint_name`); the value is confirming that and
   catching whatever is not.
3. **The prelude on the denial path** — 6,000 refusals, same shapes, at both
   index states.
4. **What it does not establish** — §3's second list, verbatim.

State the volume as **60,782 everywhere**, measured. Provenance is entirely
real: API-seeded principals, no synthetic rows, nothing to disclose.

---

## 5. Guards, each one a scar from this session

- **EXPLAIN replays against the CURRENT database.** §4.2. The `--index-state`
  flag exists because this was one command away from producing a mislabelled
  report.
- **A capture's name is not its content.** `capture-scan-noindex-2` is honestly
  named; resolve by content anyway. One capture in this repo's history held 410
  bytes and one line, `Apache Polaris Server stopped`, after a clean 9,000-request
  pass.
- **A wrong JSON key reads as an empty collection.** `resolve_entities` looked
  for `policies`; `ListPoliciesResponse` uses `identifiers`. A full namespace
  reported "namespace holds none", and that nearly cost a TRUNCATE of the realm.
  A missing key now says `this is a PARSING fault, not an empty namespace`.
- **Lag is not a disabled feature.** 403/404/5xx are PG-HA read-after-write lag
  signatures. `_try_extension` made one attempt and marked a whole entity kind
  off on any non-2xx, so one unlucky user disabled policies for a 100-user run,
  silently. It now retries the transient class and only a definitive refusal
  disables the kind.
- **The seed ledger records THAT a user was built, never WHAT.** Ledgers are
  per-prefix now, and a foreign ledger is refused; a run that creates nothing no
  longer prints a cheerful "Next: ...".
- **A token is scoped to ONE principal-role.** An identity holding two gets the
  grants of the one it asked for. `PRINCIPAL_ROLE:ALL` is root's scope and hands
  a non-root principal a token with no effective role.
- **A 400 is not an authorization outcome.** `GET /v1/config` answered 400 for a
  missing `warehouse` parameter and was filed as `refused`, which read as a
  claim about Polaris. There is a `malformed` verdict now.
- **Batching edits into one script is how a later assertion discards earlier
  writes.** One edit, one write, one verification.
- ~~**Claude cannot run git here**~~ — **RESOLVED 2026-08-31.** The mount could
  create files under `.git/` but not unlink them, so every git invocation left a
  stale `index.lock`. The cause was the mount's delete permission, not git; with
  deletion granted on the repo folder, commits complete cleanly. Claude now
  commits every completed task automatically (CLAUDE.md, *Version Control*).

---

## 6. Definition of done

- Six `qprofile-*.json`, each recording the live `pg_indexes` state it was taken
  in, and each reconciling against its run JSON with 0 unexplained.
- The grantee-lookup contrast rendered at 60,782: plan shape, buffers,
  rows-filtered, both index states.
- Per-API index usage across all 29 operations.
- One combined Markdown report; volume stated as measured; timings labelled
  inflated and never quoted as latency.
- `black` (last) and `pytest` green — 116 tests across `test_full_surface.py`,
  `test_query_profile.py`, `test_runner_smoke.py`.
- `MEMORY.md` updated; one commit for the task, message in the style
  `git log` already uses (the finding, not the file list).
