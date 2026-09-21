# PLAN — 50 grants per principal, then the privilege-query index scan

Written 2026-08-24, after reading `CLAUDE.md`, `MEMORY.md` and
`HANDOFF-privilege-scan.md`. **Nothing has been modified** — `CLAUDE.md`'s
Strict Plan-First rule applies, so this is the strategy and the exact diff,
awaiting sign-off.

---

## 0. What the cluster actually holds (confirmed with Kade)

1,000 users are seeded **at 25 grants per role**. Verify with
`python3 seed_polaris.py --verify`. The ledger agrees:
`capture/seed_ledger.json` records `spec.privileges` = 25 names,
`users` = 1..1000, and **no `grant_upgrades` record at all**.

So the fixture is at **30,002 `grant_records`** today
(25,000 granted + 5×1,000 + 2 realm), not 55K.

### Consequence that decides the whole change

`seed()` skips any user the ledger marks done, and the ledger records only
*that* a user was built — never how many grants it got. **A plain re-seed with
50 privileges against this ledger writes nothing** and reports 1,000 skipped.
It would look like a successful 50-grant seed and produce a 25-grant fixture,
short by 25,000 rows in exactly the table under audit.

Therefore the change has two halves, and only the second one moves today's
cluster:

- **(A)** make 50 the default for a *future* seed, so a fresh fixture is one
  pass instead of two;
- **(B)** reach 50 on *this* fixture through the additive upgrade path, and add
  a guard so the trap above can never be walked into silently.

---

## 1. The change to `seed_polaris.py`

Scope chosen: **CLI default only.** `src/polaris_seed.py`'s `SeedSpec.privileges`
default stays at the 25-name `CORE_CATALOG_PRIVILEGES`, so `expected_counts()`,
`verify_counts`, notebooks 01/02/02b/02c and the 233 green tests are untouched.
One small *additive* function goes into `src` (§1.3) purely so it can be tested
where the tests live.

### 1.1 — one default, not two (lines 215–220)

```diff
-    # One flag, two defaults: the spec keeps today's 25-grant shape unless
-    # asked otherwise, while the upgrade pass targets 50. Resolving both from
-    # `None` here means --verify --grants-per-role 50 checks the upgraded
-    # fixture, instead of reporting a 25,000-row shortfall that is not real.
-    spec_privileges = (
-        catalog_privileges(args.grants_per_role)
-        if args.grants_per_role
-        else list(CORE_CATALOG_PRIVILEGES)
-    )
-    upgrade_target = args.grants_per_role or 50
+    # ONE default for every path. 50 grants per role is the production shape
+    # (MEMORY, 2026-08-21); the old split default -- 25 for a seed, 50 for an
+    # upgrade -- made the documented flow permanently two passes: write 25,000
+    # rows, then PUT 25,000 more into the same table. A fresh seed now writes
+    # 50 in one pass.
+    #
+    # `catalog_privileges(n)` slices the spec-ordered enum, so 50 is a strict
+    # SUPERSET of the 25 an existing fixture holds (there is a test pinning
+    # that). The upgrade path stays additive and --revert-grants still returns
+    # to the 25-name CORE baseline, which is what the ledger's older records
+    # and every prior report mean by "baseline".
+    GRANTS_PER_ROLE_DEFAULT = 50
+    target = args.grants_per_role or GRANTS_PER_ROLE_DEFAULT
+    spec_privileges = catalog_privileges(target)
+    upgrade_target = target
```

`CORE_CATALOG_PRIVILEGES` stays imported — `--revert-grants`' help text and the
guard message both use `len(...)` on it.

### 1.2 — help text and module docstring

`--grants-per-role`'s help still says it "defaults to the 25-name baseline
everywhere else". That becomes: *defaults to 50 for every path; pass a smaller
n for a thin fixture.* The `USAGE` and `PRODUCTION GRANT VOLUME` blocks in the
module docstring change from a seed-then-upgrade recipe to:

```
    python3 seed_polaris.py                              # 1000 users x 50 grants, one pass
    python3 seed_polaris.py --verify                     # counts, per user, from PostgreSQL
    python3 seed_polaris.py --upgrade-grants             # raise an EXISTING 25-grant fixture
```

and keep the `ANALYZE grant_records` warning, which now applies to the seed too.

### 1.3 — the guard: a ledger that cannot deliver the target

New pure function in `src/polaris_seed.py` (additive, changes no default):

```python
def ledger_shortfall(ledger_path, target):
    """Grants-per-role the ledger's finished users are short of `target`.

    Returns (done_users, recorded_per_role) when a resume would silently
    under-deliver, else None.

    WHY. `seed()` skips any user in `Ledger.done_users`, and a ledger records
    only THAT a user was built -- not how many grants it got. So a 50-grant
    seed resumed against a ledger written by a 25-grant pass writes nothing at
    all and reports 1,000 skipped: a fixture 25,000 rows short of what was
    asked for, short in the one table the audit is about, and indistinguishable
    from success in the output.

    This is the same rule `Ledger.upgraded_users` already applies to the
    upgrade target -- a changed target invalidates the record -- applied to the
    seed path, which never had it.
    """
```

`seed_polaris.py` calls it just before `seed()` and exits 2 with the fix spelled
out, rather than running:

```
ledger at capture/seed_ledger.json records 1000 finished users at 25 grants
per role, but this run targets 50. Those users would be SKIPPED and the
fixture would end up 25,000 rows short of the target.

  raise the existing fixture:  python3 seed_polaris.py --upgrade-grants --grants-per-role 50
  build a new one:             mv capture/seed_ledger.json capture/seed_ledger.25.json
```

Tests, in `test_polaris_seed.py` beside the existing ledger cases: shortfall
detected / equal target passes / larger recorded target passes / empty ledger
passes / absent ledger passes.

### 1.4 — Definition of Done for this change

`black . && isort .` **with black last** (no `[tool.isort] profile`, Active
Issues), then `pytest`. Expect 233 + 5 green. `test_iceberg_rest.py` is already
black-dirty in the repo and will be reformatted — pre-existing, not from this
change.

---

## 2. Getting *this* fixture to 50 (Kade runs these)

```bash
python3 seed_polaris.py --probe-privileges                    # ~51 calls, one throwaway catalog
python3 seed_polaris.py --upgrade-grants --grants-per-role 50 --dry-run
python3 seed_polaris.py --upgrade-grants --grants-per-role 50 # 1,000 GETs + 25,000 PUTs, ~20 min
# then, on the PRIMARY:
ANALYZE polaris_schema.grant_records;
python3 seed_polaris.py --verify --grants-per-role 50
```

`--probe-privileges` first is not ceremony: `CATALOG_PRIVILEGES` is transcribed
from the 1.3.0 spec, and the 25-privilege retraction is what happens when a
transcribed constant is trusted. A rejected name costs 1,000 rows and the
shortfall reads as a Polaris behaviour.

**No Polaris restart.** The upgrade goes through the API, so
`InMemoryEntityCache` is written the normal way. The restart discipline is only
for behind-the-back writes.

### The number to expect, and a discrepancy worth settling now

`SeedSpec` currently carries `grant_overhead_per_user = 5` and
`grant_overhead_realm = 2` (re-measured after the hand-written re-bootstrap),
which projects:

```
50,000 granted + 5,000 + 2 = 55,002
```

The handoff says **55,009** — that carries the *old* realm constant of 9, from
the admin-tool bootstrap. Seven rows either way changes nothing about the plan,
but the report must state the **measured** count, and `--verify` will name any
residue as UNEXPLAINED. Settle it from `--verify` output before the report
quotes a figure.

---

## 3. Phase 2 preparation — what exists, and the three gaps

### 3.1 Already built and reusable

- `api_sweep.read_operations(fx)` — 13 GET ops bound to a real fixture
  (5 mgmt principal/role, 4 catalog, 4 Iceberg namespace/table/view).
- `api_sweep.bind_identity(label, client, ops)` — re-binds an op set to a
  specific authenticated client, and labels whose it is. This is the piece that
  makes a per-principal sweep possible at all.
- `api_sweep.assert_ok` / `measure_warm` / `measure_control`, `api_trace`'s
  `timeit` / `explain_n` / `find_capture_dir` / `NO_LOAD_BALANCE`.
- `capture.sh` (+ `rotate`, `pgoff`), `drop_grantee_index.py`, `triage_realm.py`.

### 3.2 GAP 1 — nobody knows the 1,000 principals' client_ids

`polaris_seed.py` never records credentials. `create_principal`'s response
carries `clientId` + `clientSecret` and the seeder **discards both**; the
ledger holds only `spec` and `users`. So:

- The client_ids are **Polaris-generated**, not `userN_client`. The handoff's
  `userN_client` format is an assumption about names that do not exist yet —
  it only becomes true if Kade's UPDATE rewrites `principal_client_id` as well
  as the secret (the PK `(realm_id, principal_client_id)` permits it).
- Either way, **the scan harness must LOAD each principal's client_id by
  joining `principal_authentication_data` to its `entities` row, never
  construct it from a format string.** Same lesson as `CLONE_ID_BASE` and the
  25-privilege list: a constant inferred rather than asked for is a hypothesis.

Also worth knowing before the UPDATE: `matchesSecret` accepts **main or
secondary**. Setting `main_secret_hash` alone leaves each principal's original
secret working through the secondary slot. Harmless for a read-only scan, but
it means "one secret authenticates all 1,000" is true while "only that secret
does" is not — do not assert the second.

### 3.3 GAP 2 — the authorized GET surface for a non-root principal is unmeasured

A `userN_principal` holds `owner_principal` on **its own catalog only**. The
service-level reads in `read_operations` — `GET /principals`,
`GET /principal-roles`, `GET /catalogs` — plausibly 403 for it, and `assert_ok`
**refuses to time a non-2xx** (correctly: a 403 has a latency, and putting it
in a column headed "ms" reports an error path as a performance characteristic).

So the per-principal op set is probably the catalog-scoped subset:

```
GET /catalogs/{name}            GET /namespaces
GET /catalogs/{c}/catalog-roles GET /namespaces/{ns}
GET /catalog-roles/{r}/grants   GET /namespaces/{ns}/tables
                                GET /namespaces/{ns}/views
```

**Do not assume it.** First action of the harness is a **one-principal probe**:
authenticate user1, issue all 13 ops, record status per op, print the table.
Thirteen calls settle empirically what would otherwise be a guess baked into
9,000 requests × 2 passes.

### 3.4 GAP 3 — no driver for "every principal, every GET"

Proposed new module `src/privilege_scan.py` (new file, no existing module
changed), thin because the parts exist:

- `load_identities(conn, schema, realm, prefix="user")` → per-principal
  `{index, principal, client_id, catalog, namespace, catalog_role}`, read from
  the metastore (GAP 1).
- `authorized_ops(pc_user, fx)` → the probe from §3.3, returning the surviving
  op set plus the status table for the report.
- `drive_all(identities, ops, secret, on_progress)` → token per identity, then
  its ops, single-threaded (upstream #761), resumable by index, recording
  `(identity, op, status, request_id)` — `mdc.requestId` is what Pass A
  correlates on.
- `scan_report(...)` → the per-API index-usage table.

Tests mirror `test_api_sweep.py`'s style: mocked HTTP, no live cluster.

---

## 4. The measurement itself, in order

Numbers first: **1,000 identities × ~7 authorized GETs ≈ 7,000 requests per
pass**, plus 1,000 token calls. Two Pass-A runs and one Pass-B run ≈ 24,000
requests. Reads, so minutes — but Pass A's capture is large: every request pays
the 7-statement authorization prelude, so **≥ 56,000 statements per Pass-A run**
in the Polaris DEBUG log *and* in each replica's PostgreSQL log.

```
0.  --verify --grants-per-role 50   fixture is 50/role and complete
    ANALYZE grant_records            planner is not working from stale reltuples
    triage_realm.py                  bootstrap privilege codes are 1/4, not 11/12

1.  ./capture.sh rotate capture-scan-noindex     ROTATE, never restart in place
    drop_grantee_index.py ; ANALYZE
    PASS A (index ABSENT)  -> EXPLAIN (ANALYZE, BUFFERS) on the PRIMARY
                              /*NO LOAD BALANCE*/, pg_is_in_recovery()=False

2.  CREATE INDEX CONCURRENTLY idx_grant_records_grantee ... ; ANALYZE
    ./capture.sh rotate capture-scan-index
    PASS A (index PRESENT) -> same EXPLAIN sweep

3.  ./capture.sh pgoff
    PASS B  timeit(k=15, warmup=2), EXPLAIN_N=11 first discarded,
            control POST /oauth/tokens in every cell
```

Guards carried forward, each one a scar in `MEMORY.md`:

- **Rotate the capture.** The 178 MB seeded capture was lost to an in-place
  restart.
- **Resolve the capture dir by content** — newest `capture*` with a *non-empty*
  log, never by name.
- **EXPLAIN on the primary**, detected not hardcoded (it is `postgresql-1`
  today, and it moves).
- **Pass A's clock is discarded** (logging inflates 4.6x); **Pass B's SQL shapes
  are not trusted** (logging is off). Neither pass can do the other's job.
- **Restart the kernel after any `src/` edit** — a stale import cost two
  ConnectionErrors last session.
- Fix `grant_scale.resolve_probes` before any SQL-path tool runs again. Not on
  this path (no clones), but it is a live wrong-label bug.

At 55K the grantee lookup is a **serial Seq Scan** — above the ~5K crossover,
below the ~160K parallel escalation — so the index contrast is clean and free
of the parallel-timing noise that wrecked 02b.

---

## 5. Definition of done (from the handoff, unchanged)

- Pass A capture, index absent **and** present, correlated on `mdc.requestId`;
  every GET statement's index usage rendered; the grantee-lookup Seq→Index
  contrast shown at the measured volume.
- Pass B latency with the moving control, logging off.
- Markdown report: volume stated as ~55K throughout, **all-real provenance, no
  synthetic disclosure needed**, buffers and rows-filtered as the headline with
  milliseconds as the footnote.
- `black`/`isort`/`pytest` green on new `src`/harness code — **black last**.

---

## Decisions needed before I touch anything

1. **Sign off §1** (the diff), or redirect the scope.
2. **§1.3 guard** — refuse (proposed), warn-only, or none.
3. **Who runs §2** — you, presumably; this sandbox is blocked from
   `192.168.139.2` by the network allowlist, so I can read the repo but cannot
   reach Polaris or PostgreSQL.
4. **§3.2** — are you rewriting `principal_client_id` to `userN_client`, or
   keeping Polaris's generated ids? Either works; the harness reads them from
   the metastore regardless, but the report should name what they are.
