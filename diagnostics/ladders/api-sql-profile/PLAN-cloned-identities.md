# Plan — authenticable identities by SQL, and the grant-set-size curve

Status: **confirmed empirically, ready to build.** Kade verified the credential
clone against the live cluster (2026-08-24).

---

## 1. What was confirmed

The claim in `PLAN-api-latency-sweep.md` §2a — long asserted, never run — is now
tested against the running server, not reasoned from a comment:

1. create a principal over the API, keep its `client_id` and `secret`;
2. `INSERT` a new principal row into `entities`;
3. `INSERT` a row into `principal_authentication_data` with the **same
   `main_secret_hash` and `secret_salt`** as the API-made principal, under a new
   `principal_id` and `principal_client_id`;
4. give it privileges (Kade did this over the API; step 5 below argues DML does
   it too);
5. **the new client_id authenticated with the original secret — 200, not 403.**

This matches what the 1.3.0 source said it would: on the `relational-jdbc`
backend `loadPrincipalSecrets` is a plain `SELECT` on `principal_authentication_
data` per token request (no secrets cache in this path), and `matchesSecret` is
`sha256Hex(secret + ":" + salt)` compared to the stored hash — it binds to the
secret and salt and to **nothing else**, not `client_id`, not `principal_id`.

**One control still worth running once**, because a pass alone cannot tell "the
hash ignores identity" from "auth isn't checking the secret at all":
`probe_cloned_credentials.py` clones the row AND tries the clone's client_id
with a *wrong* secret, requiring refusal. Run it to bank the negative result
next to the positive one; the manual test proved the positive half.

## 2. Why this matters — the axis it unlocks

02c can already measure latency *as* a chosen principal (`bind_identity`,
`SWEEP_IDENTITIES`). What it could not do was vary that principal's **grant-set
size** across many identities, because each authenticable principal cost one
REST `create` + one `reset_credentials`. At a few dozen that is fine; at the
scale needed to draw a *curve* it is not.

The curve is the point. Established this session, from `find_scan_crossover.py`:

- an **unindexed** grantee lookup is a Seq Scan whose cost is **constant in the
  grantee's own grant count** — `filtered` was the whole table at every volume
  from 5k to 640k;
- an **indexed** lookup's cost tracks **rows returned**, i.e. the grant-set
  size.

So the index's benefit is *large* for a small grantee and *small* for a big one
— which is exactly 02's headline ("~100x for a typical principal, single digits
for an admin holding a thousand grants"), a finding no root-only sweep can
reproduce because root holds two grants. Cloning gives us principals at 2, 25,
50, 200, 1000 grants on demand, and turns that headline into a measured line.

## 3. The build

Extend `entity_replay` — the machinery is already there and name-scoped.

### 3a. Clone the credential row alongside the entity

`entity_replay` clones `entities` and `grant_records` today. Add
`principal_authentication_data` to the set, copying `main_secret_hash`,
`secondary_secret_hash` and `secret_salt` verbatim and rewriting only
`principal_id` and `principal_client_id`. Every clone then authenticates with
**one shared secret** — the source principal's — which is exactly what a fixture
wants and must be disclosed as such (see §6).

One source principal, minted once over the API, is enough: its hash+salt seed
the whole fleet.

### 3b. Give each identity a grant set of a chosen SIZE

This is the new part, and it is what makes the axis a curve rather than a
repeat. Two ways, and the second is preferred for the same reason cloning beat
API calls everywhere else:

- **API (what Kade tested):** for each clone, `create_principal_role` →
  `assign_principal_role_to_principal` → `create_catalog_role` →
  `assign_catalog_role_to_principal_role` → N × `grant_privilege`. Correct,
  proven, and ~(4+N) calls per identity. Fine for tens of identities.
- **DML (preferred at scale):** clone the source principal's whole grant chain
  — principal-role, catalog-role, and the grant_records linking them — remapping
  ids, exactly as clone_rows already does for catalogs. To vary **size**, clone
  a *prefix* of the source's privilege grants: the first K of its catalog-scoped
  privileges, K ∈ {2, 25, 50, 200, …}. `catalog_privileges(n)` already slices
  the privilege list in a superset order, so K grants for one identity is a
  subset of K′>K for another — clean, monotone, comparable.

**Gate before trusting DML for step 4:** Kade assigned privileges over the API
and it worked. DML-cloned grants have never been authorized against. So the
smoke check must confirm a DML-granted identity not only authenticates but
**authorizes** — issues a token AND resolves its grants (`GET /catalogs`
succeeds, a scoped op it should be allowed returns 2xx, one it should not
returns 403). A token that mints but resolves nothing is a trap: the sweep would
time error paths as latency.

### 3c. Restart, then measure

Credentials, entities and grants written by SQL are all behind Polaris's back.
`InMemoryEntityCache` holds entities with their grants; the secrets path reads
the table directly but the *authorization* path uses the cache. So **restart
Polaris after cloning**, via `reset_realm.sh`'s enforced-restart path or a bare
`kubectl rollout restart` + wait-for-token. This is the step that cost three
failures this session; do not hand-run it.

## 4. Wiring into 02c

`SWEEP_IDENTITIES` already accepts a comma list. Extend preflight to accept
identities by **grant-set size** rather than by name:

    SWEEP_IDENTITY_SIZES=2,25,50,200

Preflight clones one authenticable principal per size, records each one's
**measured** footprint via `identity_grant_footprint` (never the requested K —
this repo has been wrong about assumed constants three times), mints nothing per
identity because the clone already carries credentials, and binds each into the
op set with `bind_identity`. The report then has a real x-axis: latency vs
grant-set size, at each volume, index on and off. The index-benefit curve falls
straight out of the index-present-minus-absent delta plotted against footprint.

## 5. Order of operations

1. `reset_realm.sh --seed 50` → clean realm, restarted, verified, seeded.
2. `find_scan_crossover.py` → the crossover and cache-eviction lines (already
   measured once: Seq Scan below 5k, parallel 80–160k, cache falls out 320–640k;
   re-confirm on the fresh realm).
3. `probe_cloned_credentials.py` → bank the negative control beside Kade's
   positive result.
4. Build 3a/3b in `entity_replay`, tests first, DML-authorizes-something gate in
   the smoke check.
5. Sweep with `SWEEP_IDENTITY_SIZES` at volumes chosen from step 2 —
   one below the crossover (index moot), one or two above — `SWEEP_PIN_
   PARALLELISM=1` on any cell past ~160k.

## 6. Risks and disclosures

| risk | handling |
|---|---|
| These are REAL working credentials made by SQL | A genuine finding, not just a test trick: on a shared or production realm, DB-write access would let anyone mint an authenticable principal without an audit trail. Worth reporting upstream **separately** from the index. On this isolated OrbStack cluster it is a fixture. |
| All clones share one secret | Fine for a read-only latency fixture; stated next to every number derived from them, as with every other synthetic row in this repo. |
| Clones have no MinIO objects | Read-only APIs only. Anything vending credentials or touching storage fails; the smoke check must not include such an op. |
| DML-granted authorization unproven | §3b gate: a cloned identity must *authorize*, not merely authenticate, before any measurement. |
| Cleanup | Name-scoped on a dedicated prefix, never an id range — the 201-real-entities rule. Removal deletes `principal_authentication_data`, `grant_records` and `entities` for the prefix, verified by count. |
| Cache/DB disagreement | Restart after cloning, enforced by `reset_realm.sh`. |

## 7. Open

- **Second-secret column.** `matchesSecret` also accepts `secondary_secret_hash`.
  The clone copies both; no action needed, but worth noting a rotation on the
  source would not propagate to clones (they are snapshots).
- **How high does the identity count need to go?** A curve needs ~5–6 distinct
  sizes, not thousands of identities. Thousands would only be needed to move
  `grant_records` volume — and filler already does that far more cheaply. So the
  identity fleet stays small and diverse, not large and uniform.
