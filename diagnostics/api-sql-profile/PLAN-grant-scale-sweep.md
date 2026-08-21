# Plan — production-shaped grant volume and the index scaling sweep

Phase 1 stage 3. Supersedes the single-point index measurement in
`02_index_audit.ipynb` without invalidating it.

Status: **Phase A is SUPERSEDED and built. Phases B and C stand, not built.**

- Phase A was replanned and replaced by `PLAN-seeding-production-shape.md`, which
  is signed off and implemented — its premise here (below) was wrong. Read that
  document instead of §"Phase A" in this one.
- The sweep notebook is **`02b_grant_scale_sweep.ipynb`** (decided 2026-08-21;
  see §"Open naming decision", now closed).

## Why this is worth doing before Phase 2

`doc-index-measurement-latest.md` reports 188x for the median grantee. That number is
true and reproducible, and it is measured at the **most favourable corner** of a
two-dimensional space that the report never separates:

| variable | what it drives | current fixture |
|---|---|---:|
| total rows in `grant_records` | Seq Scan cost — it reads every row | 30,009 |
| rows returned for one grantee | Index Only Scan cost | 1 (p50) |

An upstream reviewer will ask what happens in a realm shaped like theirs, and today
there is no answer. Worse, a reviewer who seeds their own realm and gets a different
ratio has grounds to dismiss the whole finding.

**The likely outcome is that production shape strengthens the case.** Seq Scan is
O(total rows); the index scan is O(rows returned). A realm of 10,000 users holding
50 grants each is ~500,000 rows — the Seq Scan gets ~16x slower while the index scan
barely moves. The present fixture *understates* the problem. That is a far better
argument than a single ratio, and only a trend can demonstrate it.

## Two corrections to the current write-up

**`p50 = 1` is not a seed artifact.** Every principal is the grantee of exactly one
record — its role assignment — and so is every principal-role. Roughly half the
grantees in *any* Polaris realm hold exactly one row. The reports currently call this
an artifact of the seed and promise production will differ. It will not. What
production changes is the number of *fat* grantees and, decisively, total table size.

~~**Polaris has only 25 catalog-scoped privileges.** `FULL_CATALOG_PRIVILEGES` is
already the complete set and the seed already grants all of them. "50 privileges on
one catalog role" is therefore only reachable across **multiple securables** —
namespace- and table-scoped grants held by the same role.~~

**RETRACTED 2026-08-21 — this was wrong, and it drove the whole of Phase A.**
`CatalogPrivilege` at tag `apache-polaris-1.3.0-incubating` carries ~51 values.
`FULL_CATALOG_PRIVILEGES` (now `CORE_CATALOG_PRIVILEGES`) stops at
`VIEW_FULL_METADATA`, which is exactly where the enum ended before the policy API
landed; it was missing the 8 `POLICY_*`/`CATALOG_*_POLICY` names and the 18
fine-grained `TABLE_*` names. 50 grants per role is reachable **at catalog scope
alone**, and because the existing 25 are precisely the first 25 of the spec's own
order, the upgrade is purely additive.

So the securable-scoped work this section justified is not needed, and neither is
the `skip_if_present`-must-compare-the-securable bug it warned would "silently
halve the fixture" — that bug cannot occur if no namespace grant is ever emitted.
What is given up is securable diversity: all 50 rows of a role point at the same
catalog. That does not change what the sweep measures, because the grantee lookup
constrains `(realm_id, grantee_catalog_id, grantee_id)` and never touches the
securable columns.

## Design decisions taken (2026-08-20)

1. **Hybrid seeding** — REST for shape, SQL for volume.
2. ~~**Role shape** — 25 catalog privileges + namespace-scoped privileges on each of
   2 namespaces, reaching ~50 per role.~~ **Revised 2026-08-21: 50 privileges, all
   catalog-scoped** (`CATALOG_PRIVILEGES[:50]`), per the retraction above.
3. **Both index states at every grid cell** — drop and rebuild per cell so each point
   carries its own before/after and cannot be contaminated by a stale index.
4. **Added 2026-08-21 — the flow, and what 02b owes 03.** Order is: seed to 50 →
   re-run 01 with the index **dropped** (stock Polaris at production volume, so
   the hypotheses read CONFIRMED rather than REMEDIED against our own patch) →
   run 02b → 03. **02b replaces 02 as the manifest producer for 03**, so no plain
   02 re-run happens in between; it must therefore write the core manifest keys
   03 checks and end with the index present and valid. Note 02's section-5 guard
   asserts the index is ABSENT once at the top — 02b drops and rebuilds per cell,
   so it needs that guard per cell instead, or it cannot run at all.

## Phase A — SUPERSEDED, and built

Replaced in full by **`PLAN-seeding-production-shape.md`** (2026-08-21), because the
premise above was wrong. What was actually built, and is now in `src/`:

- `polaris_seed.CATALOG_PRIVILEGES` — the real ~51-name enum in spec order, with
  `catalog_privileges(n)` slicing it so every larger n is a superset of every
  smaller one. `FULL_CATALOG_PRIVILEGES` renamed to `CORE_CATALOG_PRIVILEGES`,
  alias kept because existing ledgers record the old name.
- `upgrade_grants()` — additive, resumable, local-only. **One `list_grants` GET per
  role**, diff, then PUT only what is missing with `skip_if_present=False`. The
  plan's own proposal (turn `skip_if_present` off wholesale) was right about the
  24,000 wasted GETs and wrong about the consequence: it also removes the
  idempotence a resumable pass needs, so a resumed run would pay the measured ~5 s
  duplicate-key retry on every already-granted row. Diffing per role gets both.
- `revert_grants()` + `polaris_rest.revoke_privilege()` — the restore step, so the
  risk table's "optionally revert the extra grants" is a real path. Note revoke is
  **POST** to the grants URL with `?cascade=`, not DELETE.
- `probe_privileges()` / `--probe-privileges` — the spec is the source, the deployed
  build is the authority. Run it before the bulk pass.
- `expected_counts()` now projects `grant_records` in two parts, granted vs
  Polaris-written, and `verify_counts` names an unexplained residual instead of
  printing "Row counts match the spec" off a `>=` comparison.

Simulated at full scale against the fake: **1,000 GETs + 25,000 PUTs, 30,009 →
55,009 rows.** 233 tests green, `black` clean.

## Phase B — the scaling sweep

### B1. Volume via bulk SQL, disclosed as such

REST cannot reach production table sizes in a session — 10,000 users x 50 grants is
~1,000,000 API calls. Filler rows are inserted directly:

- grantee ids from a reserved high range (`>= 1_000_000_000`) that **matches no
  entity**, so the rows are inert for authorization but entirely real to a Seq Scan,
  which is the only thing being measured;
- shaped realistically — ~50 rows per synthetic grantee, not one fat grantee;
- removable precisely with `DELETE ... WHERE grantee_id >= 1000000000`.

**Pre-flight, before relying on any of this:** confirm `grant_records` carries no
foreign key to `entities`. Polaris's `QueryGenerator` emits no JOINs at all, which
strongly suggests none exists, but that is an inference from query shape and must be
checked against `pg_constraint` before inserting a single row.

**`ANALYZE grant_records` after every size change.** Without it the planner works from
stale `reltuples` and may choose a plan the data no longer justifies — which would
look exactly like a finding. Record both `reltuples` and exact `count(*)` per cell so
the drift between them is visible rather than assumed.

### B2. The grid

Three table sizes x four grantee probes, each measured in both index states:

| table size | source |
|---|---|
| ~55,000 | REST fixture alone (Phase A) |
| ~150,000 | + filler |
| ~500,000 | + filler |

Grantee probes per size: **1 row** (a principal — structurally the commonest), **~50
rows** (a production-shaped catalog role), **~500 rows**, and the **fattest** grantee.

Protocol per cell, unchanged from 02 because it is already trustworthy: statement
logging OFF, `/*NO LOAD BALANCE*/` on every statement, `pg_is_in_recovery()` asserted
False, `explain_n(k=11)` with the first discarded, medians reported with min/max.

Capture per cell the clock-independent evidence too — plan shape, Total Cost, shared
buffers, rows returned vs rows discarded by filter. Those were identical across every
run to date and are what carries an upstream report.

### B3. What the sweep should show, stated in advance

So that a null result is still informative:

- **Seq Scan time grows linearly with total rows** and is flat across grantee probes
  within a size.
- **Index Only Scan time is flat across total rows** and grows only with rows
  returned.
- Therefore **speedup grows with realm size and shrinks with grantee fatness**, and
  the current 188x is a point on that surface rather than a property of Polaris.

If Seq Scan does *not* grow linearly, something is wrong with the fixture (most
likely a missing ANALYZE or filler rows the planner is treating differently) and the
result should not be published until it is explained.

## Phase C — production point estimate

At the production-shaped cell, re-run 02's wall-clock probes: `GET /catalogs/{name}`,
`GET /principal-roles`, `GET /catalogs` (payload-dominated), and
`POST /oauth/tokens` as the **control that must not move**. Medians of 15, first 2
discarded. The control moving the wrong way is what made 02's table credible; keep it.

## Outputs

- `runs/<run_id>.json` extended with the grid, so a later notebook can re-check it
  against the live cluster the same way 03 does.
- `reports/doc-grant-scale-sweep-<run_id>.md` plus a `-latest` copy.
- Two plots — Seq Scan vs table size, Index Only Scan vs rows returned. The trend is
  the argument; a table of twelve cells is not persuasive on its own.

## Risks and how each is handled

| risk | handling |
|---|---|
| Filler rows misread as real evidence | Reported in a labelled section; every table states which rows are REST-created and which are synthetic. Never quote a filler-derived number upstream without that caveat. |
| Fixture change breaks the 02 -> 03 handoff | Row counts move, so 02's manifest must be rewritten afterwards. Sequence: sweep -> restore -> re-run 02 -> then 03. |
| A hidden FK makes filler rows impossible | Checked in B1 before any insert. If one exists, fall back to pure-REST at a lower ceiling (~110k rows) and say so. |
| PG-HA lag on ~25,000 grant PUTs | `call_with_lag_retry` already absorbs 5xx/403/404; the additive pass is idempotent and resumable. |
| `CREATE INDEX CONCURRENTLY` slows at 500k | Expected and worth recording — index build time is part of the cost being proposed upstream. |
| Leaving the cluster in an unknown state | Explicit restore step: delete filler, optionally revert the extra grants, `ANALYZE`, then re-run 02. |

## Definition of done

1. Clean linear `Restart & Run All`, monotonic execution counts, zero errors.
2. `black . && isort .` (black last — see the toolchain note), `pytest` green.
3. Sandbox static verification before the live run, per the established harness.
4. `MEMORY.md` and the README Result section updated with the measured surface.
5. The upstream-facing claim restated as a **range with its shape**, never a single
   number.

## Open naming decision — CLOSED (2026-08-21)

**`02b_grant_scale_sweep.ipynb`.** It continues the index investigation, depends on
02's work, and leaves `03_read_cache_profile.ipynb` free — the name used throughout
`MEMORY.md` and the handoffs. 03 is downstream of 02b's result.
